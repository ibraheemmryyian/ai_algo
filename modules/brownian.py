# modules/brownian.py
# Module A: Brownian Length Controller
#
# Implements a Mean-Reverting Wiener Process (Ornstein-Uhlenbeck) to generate
# a sentence-length map that mimics human burstiness.
#
# Formula: W_n = W_{n-1} + N(0, sigma^2) + kappa * (mu - W_{n-1})

import numpy as np
import math
from config.modes import MODES, FRANTIC_LENGTHS


def _ou_step(W_prev: float, mu: float, sigma: float, kappa: float) -> float:
    """Single Ornstein-Uhlenbeck step."""
    noise = np.random.normal(0.0, sigma)
    reversion = kappa * (mu - W_prev)
    return W_prev + noise + reversion


def generate_length_map(
    n_sentences: int,
    mode: str,
    mu_override: float = None,
    sigma_override: float = None,
    seed: int = None,
) -> list[int]:
    """
    Generate a list of target word counts, one per sentence.

    Args:
        n_sentences: Number of sentences to plan.
        mode: One of 'pulse', 'scholar', 'narrative'.
        mu_override: Override the mode default mu.
        sigma_override: Override the mode default sigma.
        seed: Optional RNG seed for reproducibility.

    Returns:
        List of integers (word counts per sentence), length == n_sentences.
    """
    if seed is not None:
        np.random.seed(seed)

    cfg = MODES[mode]
    mu = float(mu_override if mu_override is not None else cfg["mu"])
    sigma = float(sigma_override if sigma_override is not None else cfg["sigma"])
    kappa = float(cfg["kappa"])
    min_w = cfg["min_words"]
    max_w = cfg["max_words"]

    lengths = []
    W = mu  # start the walk at the mean

    for _ in range(n_sentences):
        W = _ou_step(W, mu, sigma, kappa)
        clamped = int(round(max(min_w, min(max_w, W))))
        lengths.append(clamped)

    return lengths


def generate_frantic_map(n_sentences: int, seed: int = None) -> list[int]:
    """
    Zone 3 (75-100%): Frantic finish - rapidly oscillating lengths between 3 and 35.
    Uses a cyclic pattern from FRANTIC_LENGTHS instead of OU so oscillations are
    guaranteed extreme rather than stochastic-convergent.
    """
    if seed is not None:
        np.random.seed(seed)

    lengths = []
    for i in range(n_sentences):
        # Cycle through the frantic pattern and add a tiny stochastic nudge
        base = FRANTIC_LENGTHS[i % len(FRANTIC_LENGTHS)]
        nudge = int(np.random.choice([-1, 0, 1]))
        val = max(3, min(35, base + nudge))
        lengths.append(val)

    return lengths


def estimate_sentence_count(target_words: int, mode: str) -> int:
    """
    Estimate how many sentences are needed to hit target_words,
    based on the mode's mean sentence length.
    """
    mu = MODES[mode]["mu"]
    # add a small buffer so we don't fall short
    return math.ceil(target_words / mu) + 1


def log_map_stats(length_map: list[int]) -> dict:
    """Return a stats dict for a length map (for debug logging)."""
    arr = np.array(length_map)
    return {
        "n_sentences": len(arr),
        "total_words_planned": int(arr.sum()),
        "mean": round(float(arr.mean()), 2),
        "std": round(float(arr.std()), 2),
        "min": int(arr.min()),
        "max": int(arr.max()),
    }
