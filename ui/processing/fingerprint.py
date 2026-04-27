# ui/processing/fingerprint.py
# Stylometric fingerprint extraction for the Tone Mimic feature.
# Analyses the user's own writing samples to extract a personal style profile
# that overrides the mode's default OU parameters and enriches the few-shot prompt.

import re
import logging

logger = logging.getLogger(__name__)


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip().split()) > 2]


def _first_word(sentence: str) -> str:
    words = sentence.strip().split()
    return words[0].lower().rstrip(".,;:\"'") if words else ""


_PREPOSITIONS = {
    "at", "by", "in", "on", "under", "above", "across", "through", "against",
    "beyond", "within", "among", "between", "beside", "behind", "before",
    "after", "during", "without", "throughout",
}
_SUBJECT_PRONOUNS = {"i", "he", "she", "they", "we", "you", "it"}


def extract_fingerprint(samples: list[str]) -> dict:
    """
    Analyse a list of text samples (the user's own writing) and return
    a style fingerprint dict used to personalise the generation prompt.

    Returns:
        {
          custom_mu: float,
          custom_sigma: float,
          opener_pos_distribution: dict,  # first-word POS category frequencies
          top_openers: list[str],          # 5 most common sentence-opening phrases
          punct_style: dict,               # punctuation frequency metrics
          vocab_diversity: float,          # type-token ratio
          example_sentences: list[str],    # 5 characteristic short sentences
        }
    """
    all_sentences = []
    all_words = []
    opener_categories = {"pronoun": 0, "noun": 0, "preposition": 0, "other": 0}
    opener_phrases = {}
    comma_count = 0
    dash_count = 0
    colon_count = 0

    for sample in samples:
        sentences = _split_sentences(sample)
        all_sentences.extend(sentences)
        words = sample.lower().split()
        all_words.extend(words)

        for sent in sentences:
            fw = _first_word(sent)
            if fw in _SUBJECT_PRONOUNS:
                opener_categories["pronoun"] += 1
            elif fw in _PREPOSITIONS:
                opener_categories["preposition"] += 1
            elif fw[0].isalpha():
                opener_categories["noun"] += 1
            else:
                opener_categories["other"] += 1

            # First 3 words as opener phrase
            opener = " ".join(sent.split()[:3]).lower()
            opener_phrases[opener] = opener_phrases.get(opener, 0) + 1

        comma_count += sample.count(",")
        dash_count += sample.count("--") + sample.count("—")
        colon_count += sample.count(":")

    if not all_sentences:
        return _default_fingerprint()

    # Sentence length stats
    lengths = [len(s.split()) for s in all_sentences]
    n = len(lengths)
    custom_mu = sum(lengths) / n
    variance = sum((l - custom_mu) ** 2 for l in lengths) / n
    custom_sigma = variance ** 0.5

    # Vocabulary diversity (type-token ratio, capped at 1000 words for efficiency)
    sample_words = all_words[:1000]
    vocab_diversity = len(set(sample_words)) / len(sample_words) if sample_words else 0.5

    # Top opener phrases (by frequency, exclude very common function words alone)
    top_openers = sorted(opener_phrases.items(), key=lambda x: x[1], reverse=True)
    top_openers = [phrase for phrase, _ in top_openers[:5]]

    # Pick 5 characteristic short sentences (8-20 words) as few-shot examples
    example_sents = [
        s for s in all_sentences
        if 8 <= len(s.split()) <= 20
    ][:5]

    total_sents = max(n, 1)
    punct_style = {
        "commas_per_sentence": round(comma_count / total_sents, 2),
        "dashes_per_sentence": round(dash_count / total_sents, 2),
        "colons_per_sentence": round(colon_count / total_sents, 2),
    }

    return {
        "custom_mu": round(custom_mu, 1),
        "custom_sigma": round(custom_sigma, 1),
        "opener_distribution": opener_categories,
        "top_openers": top_openers,
        "punct_style": punct_style,
        "vocab_diversity": round(vocab_diversity, 3),
        "example_sentences": example_sents,
        "n_sentences_analysed": n,
    }


def _default_fingerprint() -> dict:
    return {
        "custom_mu": None,
        "custom_sigma": None,
        "opener_distribution": {},
        "top_openers": [],
        "punct_style": {},
        "vocab_diversity": None,
        "example_sentences": [],
        "n_sentences_analysed": 0,
    }


def fingerprint_to_prompt_block(fp: dict) -> str:
    """
    Convert a fingerprint dict into a prompt block injected into the
    few-shot system prompt for personalised generation.
    """
    if not fp.get("example_sentences"):
        return ""

    lines = [
        "PERSONAL STYLE FINGERPRINT:",
        f"  Average sentence length: {fp['custom_mu']} words",
        f"  Typical sentence std deviation: {fp['custom_sigma']} words",
        f"  Vocabulary diversity (TTR): {fp['vocab_diversity']}",
    ]

    if fp.get("top_openers"):
        lines.append(
            "  You often open sentences with: "
            + ", ".join(f'"{o}"' for o in fp["top_openers"])
        )

    if fp.get("punct_style"):
        ps = fp["punct_style"]
        lines.append(
            f"  Punctuation: {ps['commas_per_sentence']} commas/sentence, "
            f"{ps['dashes_per_sentence']} dashes/sentence"
        )

    if fp.get("example_sentences"):
        lines.append("  Example sentences from this writer's work:")
        for ex in fp["example_sentences"][:5]:
            lines.append(f'    "{ex}"')

    lines.append(
        "Match this personal style. The output should feel like this writer wrote it."
    )

    return "\n".join(lines)
