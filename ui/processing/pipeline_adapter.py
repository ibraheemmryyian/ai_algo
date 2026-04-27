# ui/processing/pipeline_adapter.py
# Bridges UI inputs to the entropy_engine run_pipeline() function.
# Handles three UI modes: Generate (topic), Humanize (paste), Upload (file).
# Also exposes a jitter-only path for Humanize and Upload modes.

import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure the project root is on the path so we can import entropy_engine
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def run_generate(
    topic: str,
    mode: str,
    target_words: int,
    context: str,
    draft_count: int,
    main_model: str,
    jitter_model: str,
    skip_jitter: bool,
    seed: int | None,
    tone_fingerprint_block: str = "",
) -> dict:
    """
    Full three-stage pipeline: Generate from topic.
    Returns the result dict from run_pipeline() or raises on error.
    """
    from entropy_engine import run_pipeline
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your .env file or set it "
            "in the Settings tab."
        )

    # Inject tone fingerprint into context if provided
    full_context = context
    if tone_fingerprint_block:
        full_context = tone_fingerprint_block + ("\n\n" + context if context else "")

    return run_pipeline(
        topic=topic,
        mode=mode,
        target_words=target_words,
        context=full_context,
        draft_count=draft_count,
        main_model=main_model,
        jitter_model=jitter_model,
        skip_jitter=skip_jitter,
        seed=seed,
        debug=False,
    )


def run_humanize(
    text: str,
    mode: str,
    jitter_model: str,
    skip_jitter: bool,
) -> dict:
    """
    Jitter-only pipeline: takes existing text (pasted or extracted from file)
    and runs Module C without Stages 1 or 2 (no O-U map, no LLM generation).

    Returns a result dict compatible with the output panel.
    """
    import os
    from openai import OpenAI
    from modules.jitter import apply_jitter

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your .env file or set it "
            "in the Settings tab."
        )

    client = OpenAI(api_key=api_key)

    if skip_jitter:
        return {
            "text": text,
            "length_map": [],
            "stats": {},
            "jitter_stats": {},
            "mode": mode,
            "target_words": len(text.split()),
            "actual_words": len(text.split()),
            "main_model": None,
            "jitter_model": None,
            "drafts": 1,
            "pipeline": "humanize_skipped",
        }

    final_text, jitter_stats = apply_jitter(client, text, mode, jitter_model=jitter_model)

    return {
        "text": final_text,
        "length_map": [],
        "stats": {},
        "jitter_stats": jitter_stats,
        "mode": mode,
        "target_words": len(text.split()),
        "actual_words": len(final_text.split()),
        "main_model": None,
        "jitter_model": jitter_model,
        "drafts": 1,
        "pipeline": "humanize_only",
    }
