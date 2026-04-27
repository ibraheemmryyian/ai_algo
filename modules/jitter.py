# modules/jitter.py
# Module C: Semantic Jitter and Punctuation Friction
#
# Anti-detection post-processing layer. Two independent transforms:
#
# 1. Log-Prob Swap (prime-indexed targeting):
#    - Score the generated text using the model's logprobs to find
#      "AI-certain" tokens (log_prob > -1.0, i.e. P > 0.37).
#    - At positions following a prime-cycle (7, 11, 7, 11...) AND only
#      where the token is high-certainty, request the 4th or 5th most
#      likely alternative. This specifically targets the "clustering effect"
#      of AI text without touching appropriately uncertain words.
#    - Using primes (7, 11) avoids predictable modular cycles.
#
# 2. Bernoulli Punctuation Trial (P=0.15):
#    - Each sentence ending has a 15% chance of structural transformation:
#      em-dash, colon introduction, or parenthetical aside.

import re
import random
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Alternating prime positions for word targeting (cycles: 7, 11, 7, 11...)
_PRIME_CYCLE = [7, 11]

# Log-prob threshold: tokens with log_prob above this are "AI-certain"
# log_prob > -1.0  =>  P > ~0.37 (model is at least 37% confident)
# We consider these "clustered" AI choices worth swapping.
_HIGH_PROB_THRESHOLD = -1.0

_PUNCT_BREAKS = ["em_dash", "colon", "parenthetical"]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on sentence-ending punctuation + whitespace."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s.strip()]


def _score_text_logprobs(
    client: OpenAI,
    text: str,
    model: str = "gpt-4o-mini",
) -> list[dict]:
    """
    Get per-token log probabilities for a given text by asking the model to
    repeat it verbatim with temperature=0 and logprobs=True.

    Returns a list of dicts: {token, log_prob, top_logprobs, char_offset}
    where top_logprobs is a list of (token, log_prob) tuples for top-5 alternatives.
    """
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Repeat the following text verbatim. Do not change a single word or character.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0,
            logprobs=True,
            top_logprobs=5,
            max_tokens=len(text.split()) * 4,
        )
        content_logprobs = resp.choices[0].logprobs.content
        if not content_logprobs:
            return []

        result = []
        for token_info in content_logprobs:
            top_alts = []
            if token_info.top_logprobs:
                for alt in token_info.top_logprobs:
                    top_alts.append((alt.token, alt.logprob))
            result.append({
                "token": token_info.token,
                "log_prob": token_info.logprob,
                "top_logprobs": top_alts,
            })
        return result

    except Exception as e:
        logger.warning("Logprob scoring failed: %s", str(e)[:200])
        return []


def _tokens_to_word_map(token_data: list[dict]) -> list[dict]:
    """
    Group sub-word tokens into words, accumulating their log_probs and top_logprobs.
    Returns a list of dicts: {word, avg_log_prob, top_logprobs_by_token, word_idx}

    Log-prob aggregation: use the minimum log_prob among constituent tokens
    (the most "certain" token dominates the word's certainty score).
    """
    words = []
    current_word_tokens = []

    for td in token_data:
        tok = td["token"]
        # A new word starts when the token begins with a space or is punctuation-only
        if tok.startswith(" ") or (not current_word_tokens) or re.match(r'^[^\w]', tok):
            if current_word_tokens:
                word_text = "".join(t["token"] for t in current_word_tokens).strip()
                if word_text:
                    min_lp = min(t["log_prob"] for t in current_word_tokens)
                    # Collect all top alternatives from constituent tokens
                    all_alts = []
                    for t in current_word_tokens:
                        all_alts.extend(t["top_logprobs"])
                    words.append({
                        "word": word_text,
                        "avg_log_prob": min_lp,
                        "top_logprobs": all_alts,
                        "word_idx": len(words),
                    })
                current_word_tokens = [td]
            else:
                current_word_tokens = [td]
        else:
            current_word_tokens.append(td)

    # flush last word
    if current_word_tokens:
        word_text = "".join(t["token"] for t in current_word_tokens).strip()
        if word_text:
            min_lp = min(t["log_prob"] for t in current_word_tokens)
            all_alts = []
            for t in current_word_tokens:
                all_alts.extend(t["top_logprobs"])
            words.append({
                "word": word_text,
                "avg_log_prob": min_lp,
                "top_logprobs": all_alts,
                "word_idx": len(words),
            })

    return words


def _select_prime_targets(
    word_map: list[dict],
    high_prob_threshold: float = _HIGH_PROB_THRESHOLD,
) -> list[int]:
    """
    Walk through words using alternating prime-cycle positions (7, 11, 7, 11...).
    At each prime-cycle position, check if the word is "AI-certain" (log_prob above threshold).
    Return the list of word indices that are both prime-targeted AND high-certainty.

    This double filter ensures we only swap words that are:
    1. At a prime-cycle position (breaks pattern detection)
    2. Actually high-probability AI choices (breaks clustering)
    """
    targets = []
    prime_idx = 0
    next_target = _PRIME_CYCLE[0] - 1  # 0-indexed: first check is at word[6] (7th word)

    for word_data in word_map:
        idx = word_data["word_idx"]
        if idx == next_target:
            # Only target if the word is AI-certain
            if word_data["avg_log_prob"] >= high_prob_threshold:
                targets.append(idx)
            # Advance to next prime position
            prime_idx = (prime_idx + 1) % len(_PRIME_CYCLE)
            next_target += _PRIME_CYCLE[prime_idx]

    return targets


def _apply_logprob_swap(
    client: OpenAI,
    text: str,
    word_map: list[dict],
    target_indices: list[int],
    model: str = "gpt-4o-mini",
) -> str:
    """
    For each target word index, request the 4th or 5th most likely alternative
    (not the 1st, 2nd, or 3rd — those are still AI-clustered choices).

    First tries to pull alternatives from the already-scored top_logprobs.
    Falls back to an LLM batch call for words where top_logprobs didn't cover rank 4-5.
    """
    if not target_indices:
        return text

    original_words = text.split()
    new_words = list(original_words)

    # Build a set of target positions for O(1) lookup
    target_set = set(target_indices)

    # Try to use the already-scored alternatives first
    needs_llm_fallback = []
    idx_to_word_data = {wd["word_idx"]: wd for wd in word_map}

    for word_idx in target_indices:
        if word_idx >= len(new_words):
            continue

        wd = idx_to_word_data.get(word_idx)
        if not wd:
            needs_llm_fallback.append(word_idx)
            continue

        alts = wd.get("top_logprobs", [])
        # Filter out the word itself and punctuation-only tokens
        orig_lower = new_words[word_idx].lower().strip(".,!?;:")
        clean_alts = [
            (tok.strip(), lp)
            for tok, lp in alts
            if tok.strip().lower() not in ("", orig_lower)
            and re.match(r'\w', tok.strip())
        ]

        # Sort by log_prob descending (most likely first) and pick rank 4 or 5
        clean_alts.sort(key=lambda x: x[1], reverse=True)

        target_rank = random.choice([3, 4])  # 0-indexed: rank 4 = index 3, rank 5 = index 4
        if len(clean_alts) > target_rank:
            replacement = clean_alts[target_rank][0].strip()
            # Preserve capitalization
            if new_words[word_idx][0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            new_words[word_idx] = replacement
            logger.debug(
                "LogProb swap [word_idx=%d]: '%s' -> '%s' (rank %d alt, log_prob was %.3f)",
                word_idx, wd["word"], replacement, target_rank + 1, wd["avg_log_prob"]
            )
        else:
            needs_llm_fallback.append(word_idx)

    # LLM fallback for words where top_logprobs didn't have enough alternatives
    if needs_llm_fallback:
        context_snippet = text[:400]
        target_str = "\n".join(
            f"{i}: \"{new_words[wi]}\"" for i, wi in enumerate(needs_llm_fallback)
            if wi < len(new_words)
        )

        system_msg = (
            "You are a lexical frequency expert. For each word below, list exactly 5 "
            "synonyms in order from most to least common in everyday writing. "
            "Reply ONLY with lines: INDEX: word1, word2, word3, word4, word5\n"
            "All synonyms must fit the context perfectly."
        )
        user_msg = f"Context:\n{context_snippet}\n\nWords:\n{target_str}"

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=len(needs_llm_fallback) * 30 + 50,
            )
            reply = resp.choices[0].message.content.strip()
            for line in reply.splitlines():
                parts = line.split(":", 1)
                if len(parts) != 2:
                    continue
                try:
                    batch_i = int(parts[0].strip())
                    syns = [s.strip() for s in parts[1].split(",")]
                    target_rank = random.choice([3, 4])  # pick 4th or 5th
                    if len(syns) > target_rank and batch_i < len(needs_llm_fallback):
                        wi = needs_llm_fallback[batch_i]
                        if wi < len(new_words):
                            replacement = syns[target_rank]
                            if new_words[wi] and new_words[wi][0].isupper():
                                replacement = replacement[0].upper() + replacement[1:]
                            new_words[wi] = replacement
                except (ValueError, IndexError):
                    continue
        except Exception as e:
            logger.warning("LLM fallback for logprob swap failed: %s", str(e)[:200])

    return " ".join(new_words)


def _apply_punctuation_friction(
    client: OpenAI,
    sentences: list[str],
    punct_p: float,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """
    Bernoulli punctuation trial: each sentence has punct_p chance of being
    transformed into a structural break (em-dash, colon, or parenthetical).
    Batches all triggered sentences in one LLM call.
    """
    triggered = []
    for i, sentence in enumerate(sentences):
        if random.random() < punct_p:
            break_type = random.choice(_PUNCT_BREAKS)
            triggered.append((i, sentence, break_type))

    if not triggered:
        return sentences

    lines = [f"{i}|{btype}|{sent}" for i, (_, sent, btype) in enumerate(triggered)]

    system_msg = (
        "You are a structural editor. Transform each sentence using its break type:\n"
        "- em_dash: Insert an em-dash (--) at a natural pause. Keep as one sentence.\n"
        "  Example: 'The waste problem -- and it is a real problem -- costs them six figures.'\n"
        "- colon: Rewrite to use a colon leading into a specific detail.\n"
        "  Example: 'Three things drove the decision: timing, cash, and a competitor move.'\n"
        "- parenthetical: Add a brief parenthetical aside that adds texture.\n"
        "  Example: 'The match rate (across 40k listings) jumped 23% in month one.'\n\n"
        "Reply ONLY with: INDEX|transformed_sentence\n"
        "Preserve meaning. Keep approximate length. Use -- for em-dash (not Unicode)."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": "\n".join(lines)},
            ],
            temperature=0.5,
            max_tokens=sum(len(s) for _, s, _ in triggered) * 2 + 200,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Punctuation friction LLM call failed: %s", str(e)[:200])
        return sentences

    result = list(sentences)
    for line in reply.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            batch_idx = int(parts[0].strip())
            if 0 <= batch_idx < len(triggered):
                orig_idx = triggered[batch_idx][0]
                result[orig_idx] = parts[1].strip()
        except ValueError:
            continue

    return result


# ---------------------------------------------------------------------------
# C-4: The "And" Embargo (Coordination Break)
# ---------------------------------------------------------------------------

_COORD_CONJ = {"and", "but", "or", "nor", "for", "yet", "so"}
_DEFAULT_EMBARGO_THRESHOLD = 25   # words


def _apply_and_embargo(
    client: OpenAI,
    sentences: list[str],
    embargo_threshold: int = _DEFAULT_EMBARGO_THRESHOLD,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """
    C-4: If a sentence exceeds embargo_threshold words, it may contain at most
    one coordinating conjunction. Extras are replaced with em-dash or semicolon
    via a targeted LLM rewrite.
    """
    to_rewrite = []

    for i, sent in enumerate(sentences):
        words = sent.split()
        if len(words) <= embargo_threshold:
            continue
        conj_count = sum(
            1 for w in words if w.lower().strip(".,;:\"'") in _COORD_CONJ
        )
        if conj_count > 1:
            to_rewrite.append((i, sent, conj_count))

    if not to_rewrite:
        return sentences

    lines = [f"{b}|{sent}" for b, (_, sent, _) in enumerate(to_rewrite)]

    system_msg = (
        "You are a structural editor enforcing coordination discipline. "
        "Each sentence below uses too many coordinating conjunctions (and/but/or/nor/for/yet/so). "
        "Rewrite each sentence so it uses at most ONE coordinating conjunction. "
        "Replace extras with an em-dash (--) or a semicolon. "
        "Keep all information. Keep approximately the same length.\n\n"
        "Rules:\n"
        "- Do not use Unicode em-dash. Use -- instead.\n"
        "- Do not change meaning.\n"
        "- Do not split into two separate sentences.\n\n"
        "Reply ONLY with: BATCH_INDEX|rewritten_sentence"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": "\n".join(lines)},
            ],
            temperature=0.4,
            max_tokens=sum(len(s) for _, s, _ in to_rewrite) * 2 + 100,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("And Embargo LLM call failed: %s", str(e)[:200])
        return sentences

    result = list(sentences)
    for line in reply.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            batch_idx = int(parts[0].strip())
            if 0 <= batch_idx < len(to_rewrite):
                orig_idx = to_rewrite[batch_idx][0]
                result[orig_idx] = parts[1].strip()
                logger.debug("And Embargo: rewrote sentence %d", orig_idx)
        except ValueError:
            continue

    return result


# ---------------------------------------------------------------------------
# C-5: Temporal Interjection (Parenthetical Jitter)
# ---------------------------------------------------------------------------

# Action verbs that signal character movement/interaction — interjection candidates
_ACTION_VERBS = {
    "opened", "closed", "walked", "ran", "turned", "looked", "typed", "called",
    "picked", "placed", "pushed", "pulled", "sat", "stood", "entered", "left",
    "reached", "grabbed", "clicked", "read", "wrote", "signed", "dialed",
    "checked", "reviewed", "printed", "handed", "dropped", "stepped", "leaned",
}

_INTERJECTION_TYPES = ["environmental_detail", "time_marker", "sensory_aside"]


def _find_action_sentence(sentences: list[str], start: int, end: int) -> int:
    """Return index of first sentence in [start, end) that contains an action verb."""
    for i in range(start, min(end, len(sentences))):
        words = {w.lower().strip(".,;:\"'") for w in sentences[i].split()}
        if words & _ACTION_VERBS:
            return i
    return -1


def _apply_temporal_interjection(
    client: OpenAI,
    sentences: list[str],
    word_window: int = 300,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """
    C-5: Every word_window words, find the nearest action-verb sentence and
    inject a parenthetical observation about the environment or time.
    """
    # Build cumulative word counts to find 300-word window boundaries
    cum_words = []
    total = 0
    for s in sentences:
        total += len(s.split())
        cum_words.append(total)

    if total < word_window:
        return sentences  # text too short to warrant interjection

    to_inject = []
    window_start_idx = 0
    next_boundary = word_window

    while next_boundary <= total + word_window:
        # Find sentence index where cumulative words crosses next_boundary
        boundary_sent_idx = len(sentences) - 1
        for i, cw in enumerate(cum_words):
            if cw >= next_boundary:
                boundary_sent_idx = i
                break

        action_idx = _find_action_sentence(sentences, window_start_idx, boundary_sent_idx + 1)
        if action_idx >= 0 and action_idx not in {t[0] for t in to_inject}:
            inject_type = random.choice(_INTERJECTION_TYPES)
            to_inject.append((action_idx, sentences[action_idx], inject_type))

        window_start_idx = boundary_sent_idx + 1
        next_boundary += word_window

        if window_start_idx >= len(sentences):
            break

    if not to_inject:
        return sentences

    lines = [f"{b}|{itype}|{sent}" for b, (_, sent, itype) in enumerate(to_inject)]

    system_msg = (
        "You are a narrative editor adding sensory texture to prose. "
        "For each sentence, insert a brief parenthetical observation using the specified type.\n\n"
        "Types:\n"
        "- environmental_detail: something about the physical space "
        "(e.g. 'the hinges creaked', 'the fluorescent light buzzed', 'rain against the window')\n"
        "- time_marker: reference to time passing or the hour "
        "(e.g. 'it was already past six', 'three weeks and counting', "
        "'the morning light had gone flat')\n"
        "- sensory_aside: a brief sensory detail the character notices "
        "(e.g. 'the room smelled of old coffee and printer toner', "
        "'her hands were still cold from outside')\n\n"
        "Rules:\n"
        "- The parenthetical goes BEFORE the second clause of the sentence, not at the start.\n"
        "- Use regular parentheses: (detail here)\n"
        "- Keep the rest of the sentence intact.\n"
        "- The parenthetical should be 5-12 words inside the brackets.\n\n"
        "Reply ONLY with: BATCH_INDEX|modified_sentence"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": "\n".join(lines)},
            ],
            temperature=0.6,
            max_tokens=sum(len(s) for _, s, _ in to_inject) * 3 + 200,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Temporal Interjection LLM call failed: %s", str(e)[:200])
        return sentences

    result = list(sentences)
    for line in reply.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            batch_idx = int(parts[0].strip())
            if 0 <= batch_idx < len(to_inject):
                orig_idx = to_inject[batch_idx][0]
                result[orig_idx] = parts[1].strip()
                logger.debug("Temporal Interjection: inserted into sentence %d", orig_idx)
        except ValueError:
            continue

    return result


# ---------------------------------------------------------------------------
# C-6: Starting-Fragment Bias
# ---------------------------------------------------------------------------

_PREPOSITIONS = {
    "at", "by", "in", "on", "under", "above", "across", "through", "against",
    "beyond", "within", "among", "between", "beside", "behind", "before",
    "after", "during", "without", "throughout", "alongside",
}

_ADVERBS = {
    "slowly", "quickly", "carefully", "suddenly", "quietly", "deeply", "high",
    "already", "still", "never", "rarely", "often", "always", "early", "late",
    "perhaps", "barely", "almost", "finally", "now",
}


def _has_fragment_opener(sentence: str, allow_adverbs: bool = True) -> bool:
    """Return True if a sentence opens with a preposition or adverb."""
    if not sentence.strip():
        return False
    first_word = sentence.strip().split()[0].lower().rstrip(".,;:")
    if first_word in _PREPOSITIONS:
        return True
    if allow_adverbs and first_word in _ADVERBS:
        return True
    return False


def _apply_fragment_bias(
    client: OpenAI,
    sentences: list[str],
    block_size: int = 5,
    allow_adverbs: bool = True,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """
    C-6: Walk sentences in blocks of block_size. If no sentence in the block
    starts with a preposition or adverb, rewrite the longest sentence's opening.
    Only changes word order — not vocabulary — to preserve C-2 swap work.
    """
    to_rewrite = []

    for block_start in range(0, len(sentences), block_size):
        block = sentences[block_start:block_start + block_size]
        if not block:
            continue

        has_opener = any(
            _has_fragment_opener(s, allow_adverbs) for s in block
        )
        if has_opener:
            continue

        # Pick the longest sentence in the block as rewrite candidate
        # (longer sentences have more natural inversion options)
        candidate_local_idx = max(range(len(block)), key=lambda i: len(block[i].split()))
        candidate_global_idx = block_start + candidate_local_idx
        to_rewrite.append((candidate_global_idx, sentences[candidate_global_idx]))

    if not to_rewrite:
        return sentences

    opener_list = ", ".join(sorted(_PREPOSITIONS | (_ADVERBS if allow_adverbs else set())))
    lines = [f"{b}|{sent}" for b, (_, sent) in enumerate(to_rewrite)]

    system_msg = (
        "You are a syntax editor. Rewrite each sentence so it begins with a "
        "preposition or adverb rather than a subject noun or pronoun.\n\n"
        "Valid openers: " + opener_list + "\n\n"
        "Rules:\n"
        "- Change ONLY the word order. Do not substitute any vocabulary.\n"
        "- Do not change any word — only rearrange the sentence structure.\n"
        "- The rewritten sentence must be grammatically natural.\n"
        "- If the sentence cannot be naturally inverted, move a prepositional "
        "phrase from later in the sentence to the front.\n\n"
        "Reply ONLY with: BATCH_INDEX|rewritten_sentence"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": "\n".join(lines)},
            ],
            temperature=0.3,
            max_tokens=sum(len(s) for _, s in to_rewrite) * 2 + 100,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Fragment Bias LLM call failed: %s", str(e)[:200])
        return sentences

    result = list(sentences)
    for line in reply.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            batch_idx = int(parts[0].strip())
            if 0 <= batch_idx < len(to_rewrite):
                orig_idx = to_rewrite[batch_idx][0]
                result[orig_idx] = parts[1].strip()
                logger.debug("Fragment Bias: rewrote opener for sentence %d", orig_idx)
        except ValueError:
            continue

    return result


# ---------------------------------------------------------------------------
# Main orchestrator — all six Module C passes
# ---------------------------------------------------------------------------

def apply_jitter(
    client: OpenAI,
    text: str,
    mode: str,
    jitter_model: str = "gpt-4o-mini",
) -> tuple[str, dict]:
    """
    Full Module C pipeline — six sequential passes:
      C-1  Score text with logprobs (find AI-certain tokens)
      C-2  Prime-cycle log-prob swap (4th/5th rank alternatives)
      C-3  Bernoulli punctuation friction (P=0.15)
      C-4  And Embargo (coordination break on long sentences)
      C-5  Temporal Interjection (parenthetical jitter every 300 words)
      C-6  Starting-Fragment Bias (preposition/adverb openers every 5 sentences)

    Returns:
        Tuple of (jittered_text, stats_dict) where stats_dict contains counts
        of each transform applied (for UI display).
    """
    from config.modes import MODES
    cfg = MODES[mode]
    punct_p = cfg["punct_p"]
    embargo_threshold = cfg.get("embargo_threshold", _DEFAULT_EMBARGO_THRESHOLD)
    allow_adverbs = cfg.get("fragment_bias_adverbs", True)

    stats = {
        "logprob_swaps": 0,
        "punct_breaks": 0,
        "embargo_rewrites": 0,
        "temporal_injections": 0,
        "fragment_rewrites": 0,
    }

    # C-1 + C-2: Logprob scoring and prime-cycle swap
    logger.info("C-1/C-2: Logprob scoring + prime-cycle swap | model=%s", jitter_model)
    token_data = _score_text_logprobs(client, text, model=jitter_model)

    if token_data:
        word_map = _tokens_to_word_map(token_data)
        target_indices = _select_prime_targets(word_map)
        stats["logprob_swaps"] = len(target_indices)
        logger.info("C-2: %d high-certainty words targeted", len(target_indices))
        jittered = _apply_logprob_swap(client, text, word_map, target_indices, model=jitter_model)
    else:
        logger.warning("C-1: Logprob scoring returned nothing - skipping swap pass")
        jittered = text

    sentences = _split_sentences(jittered)

    # C-3: Punctuation friction
    logger.info("C-3: Bernoulli punctuation friction | P=%.2f", punct_p)
    before_count = len(sentences)
    sentences = _apply_punctuation_friction(client, sentences, punct_p, model=jitter_model)
    stats["punct_breaks"] = sum(
        1 for o, n in zip(_split_sentences(jittered), sentences) if o != n
    )

    # C-4: And Embargo
    logger.info("C-4: And Embargo | threshold=%d words", embargo_threshold)
    sentences_before = list(sentences)
    sentences = _apply_and_embargo(client, sentences, embargo_threshold, model=jitter_model)
    stats["embargo_rewrites"] = sum(1 for a, b in zip(sentences_before, sentences) if a != b)

    # C-5: Temporal Interjection
    logger.info("C-5: Temporal Interjection | every 300 words")
    sentences_before = list(sentences)
    sentences = _apply_temporal_interjection(client, sentences, model=jitter_model)
    stats["temporal_injections"] = sum(1 for a, b in zip(sentences_before, sentences) if a != b)

    # C-6: Starting-Fragment Bias
    logger.info("C-6: Starting-Fragment Bias | block_size=5 | adverbs_allowed=%s", allow_adverbs)
    sentences_before = list(sentences)
    sentences = _apply_fragment_bias(
        client, sentences, allow_adverbs=allow_adverbs, model=jitter_model
    )
    stats["fragment_rewrites"] = sum(1 for a, b in zip(sentences_before, sentences) if a != b)

    result = " ".join(sentences)
    logger.info("Module C complete: %s", stats)

    return result, stats

    """
    Full Module C pipeline:
      1. Score text with logprobs to find AI-certain tokens
      2. Apply prime-cycle log-prob swap (4th/5th rank alternatives)
      3. Apply Bernoulli punctuation friction

    Args:
        client: OpenAI client instance.
        text: Generated text to post-process.
        mode: Mode config name.
        jitter_model: Model for scoring and jitter (cheap/fast).

    Returns:
        Jittered text string.
    """
    from config.modes import MODES
    cfg = MODES[mode]
    punct_p = cfg["punct_p"]

    logger.info("Module C: Scoring text with logprobs | model=%s", jitter_model)

    # Step 1: Get logprob scores
    token_data = _score_text_logprobs(client, text, model=jitter_model)

    if token_data:
        # Step 2: Map tokens to words and find prime-cycle high-certainty targets
        word_map = _tokens_to_word_map(token_data)
        target_indices = _select_prime_targets(word_map)

        logger.info(
            "Prime-cycle targeting: %d high-certainty words identified for swap "
            "(out of %d total words)",
            len(target_indices), len(word_map)
        )

        # Step 3: Apply log-prob swap (4th/5th rank alternatives)
        jittered = _apply_logprob_swap(client, text, word_map, target_indices, model=jitter_model)
    else:
        logger.warning("Logprob scoring returned nothing - skipping swap pass")
        jittered = text

    # Step 4: Punctuation friction
    sentences = _split_sentences(jittered)
    sentences = _apply_punctuation_friction(client, sentences, punct_p, model=jitter_model)
    result = " ".join(sentences)

    return result
