#!/usr/bin/env python3
# entropy_engine.py
# Main CLI entry point for the Entropy Engine pipeline.
#
# Usage:
#   python entropy_engine.py --topic "..." --mode pulse --words 150
#   python entropy_engine.py --topic "..." --mode scholar --words 2500 --drafts 3
#   echo "topic here" | python entropy_engine.py --mode narrative --words 300
#
# The pipeline:
#   1. Map Generator (Module A/B): OU Brownian walk -> sentence length map
#   2. Constrained LLM Call: Fill the map with coherent text
#   3. Post-Processor (Module C): Semantic jitter + punctuation friction

import os
import sys
import argparse
import logging
import json
from dotenv import load_dotenv
from openai import OpenAI

from config.modes import MODES
from modules.brownian import generate_length_map, estimate_sentence_count, log_map_stats
from modules.phase_scheduler import build_phased_map, should_use_phase_scheduler
from modules.llm_caller import generate_constrained_text
from modules.jitter import apply_jitter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("entropy_engine")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Entropy Engine - Brownian humanizer for AI-generated outreach text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  pulse     LinkedIn posts, short punchy outreach, cold DMs (mu=12 words/sentence)
  scholar   Technical cold emails, detailed proposals (mu=25 words/sentence)
  narrative Story-driven emails, follow-ups, founder intros (mu=18 words/sentence)

Examples:
  python entropy_engine.py --topic "industrial symbiosis platform for chemical manufacturers" --mode pulse --words 120
  python entropy_engine.py --topic "red gypsum valorization ROI pitch" --mode scholar --words 400 --drafts 3
  python entropy_engine.py --topic "why we built SymbioFlows" --mode narrative --words 250 --debug
        """,
    )
    p.add_argument("--topic", "-t", type=str, help="Topic or subject for the content")
    p.add_argument(
        "--mode", "-m",
        choices=list(MODES.keys()),
        default="pulse",
        help="Content style mode (default: pulse)",
    )
    p.add_argument(
        "--words", "-w",
        type=int,
        default=150,
        help="Target word count (default: 150)",
    )
    p.add_argument(
        "--context", "-c",
        type=str,
        default="",
        help="Optional extra context to ground the output (company info, recipient details, etc.)",
    )
    p.add_argument(
        "--drafts", "-d",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Number of drafts for Human Error composite layer (default: 1, max: 3). Costs more tokens.",
    )
    p.add_argument(
        "--main-model",
        type=str,
        default="gpt-4o",
        help="Main generation model (default: gpt-4o)",
    )
    p.add_argument(
        "--jitter-model",
        type=str,
        default="gpt-4o-mini",
        help="Jitter/post-processing model (default: gpt-4o-mini, cheaper)",
    )
    p.add_argument(
        "--no-jitter",
        action="store_true",
        help="Skip Module C (semantic jitter + punctuation friction). Faster but less humanized.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible Brownian walks",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Print the length map and stats to stderr before generating",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON with text + metadata instead of plain text",
    )
    return p


def run_pipeline(
    topic: str,
    mode: str,
    target_words: int,
    context: str,
    draft_count: int,
    main_model: str,
    jitter_model: str,
    skip_jitter: bool,
    seed: int,
    debug: bool,
) -> dict:
    """
    Full three-stage pipeline.

    Returns a dict with keys: text, length_map, stats, mode, target_words.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set. Add it to .env or export it.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ------------------------------------------------------------------ #
    # Stage 1: Map Generator
    # ------------------------------------------------------------------ #
    logger.info(
        "Stage 1: Generating Brownian length map | mode=%s | target=%d words",
        mode, target_words
    )

    if should_use_phase_scheduler(target_words):
        logger.info("Long-form detected (%d words) - activating Strobe-Phase Scheduler", target_words)
        length_map = build_phased_map(target_words, mode, seed=seed)
    else:
        n_sentences = estimate_sentence_count(target_words, mode)
        length_map = generate_length_map(n_sentences, mode, seed=seed)

    stats = log_map_stats(length_map)

    if debug:
        logger.info("Length map: %s", length_map)
        logger.info("Map stats: %s", json.dumps(stats))

    # ------------------------------------------------------------------ #
    # Stage 2: Constrained LLM Call
    # ------------------------------------------------------------------ #
    logger.info(
        "Stage 2: Generating constrained text | %d sentences | model=%s | drafts=%d",
        len(length_map), main_model, draft_count
    )

    text = generate_constrained_text(
        client=client,
        topic=topic,
        length_map=length_map,
        mode=mode,
        model=main_model,
        context=context,
        draft_count=draft_count,
    )

    logger.info("Stage 2 complete: %d words generated", len(text.split()))

    # ------------------------------------------------------------------ #
    # Stage 3: Post-Processor (Semantic Jitter)
    # ------------------------------------------------------------------ #
    if skip_jitter:
        logger.info("Stage 3: Skipped (--no-jitter)")
        final_text = text
    else:
        logger.info(
            "Stage 3: Applying semantic jitter + punctuation friction | model=%s",
            jitter_model
        )
        final_text = apply_jitter(client, text, mode, jitter_model=jitter_model)
        logger.info("Stage 3 complete")

    return {
        "text": final_text,
        "length_map": length_map,
        "stats": stats,
        "mode": mode,
        "target_words": target_words,
        "actual_words": len(final_text.split()),
        "main_model": main_model,
        "jitter_model": jitter_model if not skip_jitter else None,
        "drafts": draft_count,
    }


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Allow topic from stdin if not provided as argument
    if not args.topic:
        if not sys.stdin.isatty():
            args.topic = sys.stdin.read().strip()
        if not args.topic:
            parser.error("--topic is required (or pipe text via stdin)")

    result = run_pipeline(
        topic=args.topic,
        mode=args.mode,
        target_words=args.words,
        context=args.context,
        draft_count=args.drafts,
        main_model=args.main_model,
        jitter_model=args.jitter_model,
        skip_jitter=args.no_jitter,
        seed=args.seed,
        debug=args.debug,
    )

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["text"])


if __name__ == "__main__":
    main()
