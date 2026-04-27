# modules/llm_caller.py
# The Constrained LLM Caller
#
# Builds the few-shot structured prompt that forces the LLM to fill
# "word buckets" from the Brownian length map, then calls the main
# generation model. Also handles the "Human Error" composite drafting pass.

import logging
import random
from openai import OpenAI
from config.modes import MODES, BANNED_PHRASES

logger = logging.getLogger(__name__)

# Few-shot examples demonstrate exactly what word-count adherence looks like.
# These are generic enough to work across topics.
_FEW_SHOT_EXAMPLES = [
    {
        "map": [8, 4, 15, 6, 10],
        "output": (
            "Industrial waste is not a problem waiting to be solved. "       # 9 words - close
            "It is currency. "                                                 # 3
            "Every ton of red gypsum sitting in a landfill represents a missed connection. "  # 14
            "Someone needs what you discard. "                                 # 5
            "The match already exists — the infrastructure to make it real does not."  # 14
        ),
    }
]


def _build_system_prompt(mode: str, zone_label: str = "") -> str:
    cfg = MODES[mode]
    tone = cfg["tone"]
    banned = ", ".join(BANNED_PHRASES[:12])  # keep prompt compact

    zone_context = f" Current zone: {zone_label}." if zone_label else ""

    return (
        "You are a master of human stylometry. Your output must be indistinguishable "
        "from a skilled human writer.\n\n"
        f"TONE: {tone}{zone_context}\n\n"
        "HARD RULES:\n"
        f"1. You will receive a word-count sequence [L1, L2, L3...]. "
        "Each number is the EXACT target word count for that sentence. "
        "Match every sentence to within +/- 1 word. Count carefully.\n"
        "2. Do NOT use these banned phrases: " + banned + "\n"
        "3. Do NOT start consecutive sentences with the same word.\n"
        "4. Do NOT use passive voice more than once per paragraph.\n"
        "5. Write coherent, flowing text - do not make length constraints obvious.\n"
        "6. Return ONLY the text. No labels, no numbering, no explanations.\n"
    )


def _build_user_prompt(topic: str, length_map: list[int], context: str = "") -> str:
    map_str = "[" + ", ".join(str(l) for l in length_map) + "]"
    ctx_line = f"\nAdditional context:\n{context}\n" if context else ""

    # Include the few-shot example
    ex = _FEW_SHOT_EXAMPLES[0]
    ex_map = "[" + ", ".join(str(l) for l in ex["map"]) + "]"

    return (
        f"EXAMPLE:\n"
        f"Word-count sequence: {ex_map}\n"
        f"Output:\n{ex['output']}\n\n"
        f"---\n"
        f"YOUR TASK:\n"
        f"Topic: {topic}\n"
        f"{ctx_line}"
        f"Word-count sequence: {map_str}\n\n"
        "Write the text now, matching each sentence to the sequence:"
    )


def _chunk_length_map(length_map: list[int], chunk_size: int = 20) -> list[list[int]]:
    """Split a long length map into chunks for separate API calls (token limit safety)."""
    return [length_map[i:i+chunk_size] for i in range(0, len(length_map), chunk_size)]


def generate_constrained_text(
    client: OpenAI,
    topic: str,
    length_map: list[int],
    mode: str,
    model: str = "gpt-4o",
    context: str = "",
    zone_label: str = "",
    draft_count: int = 1,
) -> str:
    """
    Core constrained generation call.

    If draft_count > 1 (Human Error layer), generates multiple drafts and
    creates a composite that blends them, occasionally choosing simpler words
    to simulate human revision behavior.

    Args:
        client: OpenAI client.
        topic: What to write about.
        length_map: List of target word counts per sentence.
        mode: Mode name.
        model: Main generation model.
        context: Optional extra context to ground the output.
        zone_label: Phase zone label (for long-form content).
        draft_count: Number of drafts to generate for the composite layer.

    Returns:
        Generated text string.
    """
    system_prompt = _build_system_prompt(mode, zone_label)
    chunks = _chunk_length_map(length_map)

    # For very long maps, generate chunk by chunk with context carry-over
    all_parts = []
    running_context = context

    for chunk_idx, chunk in enumerate(chunks):
        user_prompt = _build_user_prompt(topic, chunk, running_context)

        if draft_count > 1:
            drafts = _generate_multiple_drafts(
                client, system_prompt, user_prompt, model, draft_count
            )
            chunk_text = _composite_drafts(client, drafts, model)
        else:
            chunk_text = _single_generation(client, system_prompt, user_prompt, model, chunk)

        all_parts.append(chunk_text)
        # Feed last 2 sentences as context for next chunk
        sentences = chunk_text.strip().split(". ")
        running_context = ". ".join(sentences[-2:]) if len(sentences) >= 2 else chunk_text

    return " ".join(all_parts).strip()


def _single_generation(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str,
    length_map: list[int],
) -> str:
    """Single LLM generation call with retry logic."""
    max_tokens = sum(length_map) * 6  # ~6 chars per word average

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.85,
                max_tokens=min(max_tokens, 4096),
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning("Generation attempt %d failed: %s", attempt + 1, str(e)[:200])
            if attempt == 2:
                raise

    return ""


def _generate_multiple_drafts(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str,
    draft_count: int,
) -> list[str]:
    """Generate N draft versions via the n parameter (single API call)."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            n=min(draft_count, 3),  # GPT-4o supports n<=3 efficiently
            max_tokens=4096,
        )
        return [choice.message.content.strip() for choice in resp.choices]
    except Exception as e:
        logger.warning("Multi-draft generation failed: %s", str(e)[:200])
        # Fall back to single draft
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.85,
            max_tokens=4096,
        )
        return [resp.choices[0].message.content.strip()]


def _composite_drafts(
    client: OpenAI,
    drafts: list[str],
    model: str,
) -> str:
    """
    Human Error Layer: merge N drafts into a composite that simulates
    a human choosing simpler words occasionally (revision behavior).

    Uses the LLM to merge rather than naive sentence-by-sentence splice,
    so transitions stay coherent.
    """
    if len(drafts) == 1:
        return drafts[0]

    drafts_formatted = "\n\n---DRAFT {}---\n{}"
    all_drafts = "".join(
        drafts_formatted.format(i + 1, d) for i, d in enumerate(drafts)
    )

    system_msg = (
        "You are a human editor merging multiple draft versions of the same text. "
        "Create ONE final version that:\n"
        "1. Uses the best phrasing from each draft.\n"
        "2. Occasionally opts for a simpler, more natural word where a draft used "
        "something more sophisticated (simulates a human 'choosing' the right word).\n"
        "3. Maintains perfect coherence and flow throughout.\n"
        "4. Matches approximately the same length as any single draft.\n"
        "Return ONLY the final merged text."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": all_drafts},
            ],
            temperature=0.6,
            max_tokens=4096,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Composite merge failed: %s", str(e)[:200])
        return random.choice(drafts)
