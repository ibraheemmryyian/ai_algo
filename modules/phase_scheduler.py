# modules/phase_scheduler.py
# Module B: Strobe-Phase State Machine
#
# Implements a word-count-triggered state machine that swaps (mu, sigma)
# every STATE_WORD_THRESHOLD words to defeat "Global Pattern" detection.
#
# AI detectors measure variance in sentence length over a rolling window.
# A static OU walk with fixed (mu, sigma) produces a recognizable global
# signature even if local variance looks OK. Swapping the parameters every
# ~500 words breaks the global autocorrelation pattern.
#
# State transitions:
#   State 0: Volatile short  (mu=10, sigma=15) - burst opener
#   State 1: Scholar long    (mu=28, sigma=5)  - dense explanatory
#   State 2: Staccato        (mu=7,  sigma=12) - very short punchy
#   State 3: Flowing         (mu=22, sigma=9)  - moderate narrative
#   (cycles back to 0)

import math
import logging
import numpy as np
from config.modes import MODES, LONG_FORM_THRESHOLD
from modules.brownian import _ou_step

logger = logging.getLogger(__name__)

# State machine configuration: each state is (mu, sigma, label)
_STATES = [
    (10, 15, "volatile_short"),
    (28,  5, "scholar_long"),
    ( 7, 12, "staccato"),
    (22,  9, "flowing"),
]

STATE_WORD_THRESHOLD = 500  # swap state every N words


def build_phased_map(
    target_words: int,
    mode: str,
    seed: int = None,
) -> list[int]:
    """
    Build a sentence-length map using the state machine phase controller.
    Active for content >= LONG_FORM_THRESHOLD words.

    The machine walks through states, generating sentences via OU with
    that state's (mu, sigma) until the cumulative word count crosses
    STATE_WORD_THRESHOLD, then advances the state.

    Args:
        target_words: Desired total word count.
        mode: Base mode for kappa (reversion speed) and word bounds.
        seed: Optional RNG seed.

    Returns:
        List of target word counts per sentence.
    """
    if seed is not None:
        np.random.seed(seed)

    cfg = MODES[mode]
    kappa = cfg["kappa"]
    min_w = cfg["min_words"]
    max_w = cfg["max_words"]

    length_map = []
    cumulative_words = 0
    state_idx = 0
    words_in_current_state = 0

    mu, sigma, label = _STATES[state_idx]
    W = float(mu)  # start walk at current state's mean

    logger.debug(
        "State machine start | target=%d words | initial state: %s (mu=%d, sigma=%d)",
        target_words, label, mu, sigma
    )

    while cumulative_words < target_words:
        # Check if we need to advance state
        if words_in_current_state >= STATE_WORD_THRESHOLD:
            state_idx = (state_idx + 1) % len(_STATES)
            mu, sigma, label = _STATES[state_idx]
            # Don't reset W — let it revert naturally from where it landed.
            # This creates a realistic "gear shift" rather than a hard jump.
            words_in_current_state = 0
            logger.debug(
                "State transition -> %s (mu=%d, sigma=%d) at word %d",
                label, mu, sigma, cumulative_words
            )

        # OU step with current state parameters
        W = _ou_step(W, mu, sigma, kappa)
        length = int(round(max(min_w, min(max_w, W))))

        length_map.append(length)
        cumulative_words += length
        words_in_current_state += length

    return length_map


def get_state_at_word(word_idx: int) -> dict:
    """
    Return the state that would be active at a given word index.
    Useful for labeling prompt zones.
    """
    state_idx = (word_idx // STATE_WORD_THRESHOLD) % len(_STATES)
    mu, sigma, label = _STATES[state_idx]
    return {"state": state_idx, "mu": mu, "sigma": sigma, "label": label}


def get_zone_label(sentence_idx: int, total_sentences: int) -> str:
    """Return a human-readable zone label for a sentence (for prompt context)."""
    estimated_word_pos = sentence_idx * 18  # rough estimate
    state = get_state_at_word(estimated_word_pos)
    return state["label"]


def should_use_phase_scheduler(target_words: int) -> bool:
    """True when content is long enough to warrant the state machine."""
    return target_words >= LONG_FORM_THRESHOLD
