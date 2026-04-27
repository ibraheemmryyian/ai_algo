# config/modes.py
# Mode constants for the Brownian Length Controller.
# Each mode defines the Ornstein-Uhlenbeck parameters and jitter settings
# tuned for a specific outreach context.

MODES = {
    "pulse": {
        "description": "LinkedIn posts, short punchy outreach, cold DMs",
        "mu": 12,         # target mean sentence length (words)
        "sigma": 6,       # volatility - how wild the length jumps are
        "kappa": 0.35,    # reversion speed - how fast it snaps back to mu
        "jitter_n": 5,    # replace every N-th word with a synonym
        "punct_p": 0.15,  # probability of non-standard punctuation break
        "min_words": 3,
        "max_words": 30,
        "tone": "direct, punchy, conversational. No filler words. Write like a sharp operator.",
    },
    "scholar": {
        "description": "Technical cold emails, detailed proposals, case studies",
        "mu": 25,
        "sigma": 8,
        "kappa": 0.20,
        "jitter_n": 7,
        "punct_p": 0.10,
        "min_words": 8,
        "max_words": 45,
        "tone": "authoritative, precise, data-driven. Use concrete specifics over abstractions.",
    },
    "narrative": {
        "description": "Story-driven emails, follow-ups, founder intros",
        "mu": 18,
        "sigma": 10,
        "kappa": 0.25,
        "jitter_n": 6,
        "punct_p": 0.20,
        "min_words": 3,
        "max_words": 40,
        "tone": "vivid, human, slightly informal. Use active voice. Ground claims in real scenarios.",
    },
    "academic": {
        "description": "Essays, research papers, academic submissions",
        "mu": 22,
        "sigma": 6,
        "kappa": 0.15,
        "jitter_n": 9,    # prime, longer interval for formal text
        "punct_p": 0.08,  # fewer structural breaks in academic prose
        "min_words": 8,
        "max_words": 45,
        "tone": (
            "Formal, third-person, evidence-driven. No contractions. "
            "Hedged claims using epistemic markers (suggests, indicates, appears to, may). "
            "Passive voice permitted at 25% maximum. Avoid first-person."
        ),
        # Academic mode uses stricter And Embargo threshold
        "embargo_threshold": 20,   # words (vs default 25)
        "fragment_bias_adverbs": False,  # prepositional openers only, no adverbs
    },
}

# Strobe-Phase zone overrides for long-form content (2k+ words).
# Zones are defined as (start_fraction, end_fraction, mu_override, sigma_override).
PHASE_ZONES = [
    (0.00, 0.25, 10,  15),   # Zone 1: high volatility, short punchy opener
    (0.25, 0.75, 28,  5),    # Zone 2: high mean, technical explanatory body
    (0.75, 1.00, None, None), # Zone 3: Frantic finish - handled separately
]

FRANTIC_LENGTHS = [3, 7, 35, 4, 28, 5, 33, 6, 12, 35, 3, 22]  # cyclic oscillation
LONG_FORM_THRESHOLD = 2000  # words at which phase scheduler activates

# Banned transition cliches the LLM must avoid
BANNED_PHRASES = [
    "Furthermore", "Moreover", "Additionally", "In conclusion",
    "It is worth noting", "It should be noted", "As mentioned",
    "In summary", "To summarize", "Needless to say", "Certainly",
    "Absolutely", "In today's world", "In the realm of", "Leverage",
    "Synergy", "Streamline", "Utilize", "Facilitate", "Delve",
    "It's important to", "I wanted to reach out",
]
