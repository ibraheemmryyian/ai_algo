# Entropy Engine

The README you are reading right now was written to demonstrate the output of this tool. Variable sentence lengths. Deliberate punctuation breaks. No transition clichés. That is what this pipeline produces — and this document is the sample.

---

## The Problem

AI detectors do not read for meaning. They measure patterns.

The dominant pattern they exploit is the **Clustering Effect**. Every major LLM — GPT, Claude, Gemini — produces text where sentence lengths cluster around a statistical mean with very low variance. The autocorrelation of those lengths across a 500-word window is measurably non-human. Turnitin, GPTZero, and similar tools don't care what you wrote. They care that your sentences are 18, 19, 17, 20, 18 words long, over and over, in a distribution no person has ever naturally produced.

The fix is not a better prompt. Prompting is cosmetic surgery on the symptom.

The fix is to break the underlying statistical signature — before the LLM writes a single word.

---

## How It Works

Three stages. The math runs first. The LLM fills in the blanks.

```
STAGE 1 — MAP GENERATOR
  [Module A] Ornstein-Uhlenbeck Brownian Walk
             Output: length_map = [12, 4, 28, 7, 19, 3, 31, ...]

  [Module B] Strobe-Phase State Machine        <- long-form only (2000+ words)
             Swaps (mu, sigma) every 500 words

STAGE 2 — CONSTRAINED LLM CALL
  [Few-Shot Structured Prompt]
  "Write N sentences. Sentence 1 = 12 words. Sentence 2 = 4 words. Sentence 3 = 28 words..."
  The LLM fills word buckets. It never writes freely.

STAGE 3 — POST-PROCESSOR
  [Module C-1] Log-Prob Scoring
               Find AI-certain tokens: log_prob > -1.0

  [Module C-2] Prime-Cycle Swap
               At positions 7, 11, 7, 11... replace AI-certain words
               with the 4th or 5th most likely alternative

  [Module C-3] Bernoulli Punctuation Trial
               P(structural break) = 0.15 per sentence ending

  [Module C-4] "And" Embargo (Coordination Break)
               If sentence length > 25 words: max 1 coordinating conjunction
               Extras replaced with em-dash or semicolon

  [Module C-5] Temporal Interjection
               Every 300 words: insert a parenthetical environmental/time
               observation into the nearest character-action sentence

  [Module C-6] Starting-Fragment Bias
               Every 5th sentence: force opening word to be a preposition
               or adverb (not Subject + Verb)
```

---

## Module A: The Brownian Length Controller

The core formula is a discrete **Mean-Reverting Wiener Process** — specifically, the Ornstein-Uhlenbeck stochastic differential equation discretized to sentence steps:

```
W_n = W_{n-1} + N(0, sigma^2) + kappa * (mu - W_{n-1})
```

That last term — `kappa * (mu - W_{n-1})` — is everything. Pure Brownian motion drifts without bound. The O-U term pulls the walk back toward `mu` after every step, the same way a real writer orbits their natural sentence rhythm but occasionally breaks out of it.

| Variable | Role |
|----------|------|
| `W_n` | Target word count for sentence n |
| `mu` | The attractor — mean sentence length for this mode |
| `sigma` | Volatility — how wild the jumps can get |
| `kappa` | Reversion speed — high value snaps back fast, low value drifts longer |

Three modes ship by default:

| Mode | mu | sigma | kappa | Built for |
|------|----|-------|-------|-----------|
| `pulse` | 12 | 6 | 0.35 | LinkedIn posts, cold DMs |
| `scholar` | 25 | 8 | 0.20 | Technical emails, proposals |
| `narrative` | 18 | 10 | 0.25 | Founder intros, story follow-ups |

---

## Module B: The Strobe-Phase State Machine

Only fires at 2,000+ words. Here is why it exists.

A well-tuned O-U walk with fixed `(mu, sigma)` still produces a detectable global signature. Local variance looks human. Zoom out to 500-word windows and the autocorrelation pattern is flat — a statistical fingerprint that screams "generated." Turnitin's "Global Pattern" check exploits exactly this.

The state machine swaps `(mu, sigma)` every 500 cumulative words. Four states, cycling in sequence:

```
State 0 — volatile_short  (mu=10, sigma=15)   burst, punchy, sensory
State 1 — scholar_long    (mu=28, sigma=5)    dense, technical, explanatory
State 2 — staccato        (mu=7,  sigma=12)   very short. Aggressive.
State 3 — flowing         (mu=22, sigma=9)    moderate, narrative pace
```

The walk value `W` carries forward across transitions — no hard reset. The new attractor pulls it gradually, producing a natural gear shift instead of a discontinuity that would itself be detectable.

---

## Module C: Semantic Jitter and Punctuation Friction

The LLM filled the word buckets. The text is coherent. It is still, statistically, AI text — because the word choices are clustered around the model's highest-probability outputs.

This module fixes that.

### Log-Prob Scoring

The generated text is passed back through `gpt-4o-mini` with `logprobs=True, top_logprobs=5, temperature=0` — a verbatim reproduction at greedy decoding. This returns the model's probability distribution over every token it produces.

Tokens with `log_prob > -1.0` have `P > 0.37`. The model was highly confident in that choice. That confidence is the problem — it is the clustering effect at the token level.

### Prime-Cycle Targeting

Word positions are walked using an alternating prime cycle: **7, 11, 7, 11, ...**

A fixed modulo (every 7th word, always) creates its own periodic signature. Alternating two coprime values produces a non-repeating cycle with LCM = 77. At each prime-cycle position, the check runs: is this word AI-certain? If yes, it gets swapped. If no — the word is already uncertain enough. Leave it.

The replacement is always the **4th or 5th most likely alternative** from `top_logprobs`. Not the 1st, 2nd, or 3rd — those are still inside the AI's high-probability cluster. The 4th and 5th choices are plausible, contextually appropriate, and occupy the long tail of the distribution. That long tail is where human writers actually live.

### Bernoulli Punctuation Trial

Every sentence ending gets an independent coin flip: `P = 0.15`.

If it fires, the sentence is structurally transformed -- into an em-dash break, a colon introduction, or a parenthetical aside. Human prose contains these structures at roughly this frequency. Injecting them stochastically (not at fixed intervals) replicates that distribution without creating its own detectable pattern.

### C-4: The "And" Embargo (Coordination Break)

This sub-routine targets the 7% "smoothness" alarm — the score AI detectors assign when sentence rhythm is too clean. Long sentences are the primary trigger. A sentence of 25+ words joined by repeated "and" / "but" connectors is almost always machine-generated: AI defaults to compound structures because they are the highest-probability continuation at each token step.

**The rule:** If a sentence exceeds 25 words, it may contain at most one coordinating conjunction (and, but, or, nor, for, yet, so). Every additional conjunction is replaced with an em-dash or semicolon by a targeted LLM rewrite pass.

```
Before (AI): "He went to the meeting and he presented the data and the board approved it."
After:       "He went to the meeting, presented the data — the board approved it before he finished."
```

The effect is structural compression. The sentence carries the same information but the rhythm breaks where AI would have smoothed it.

### C-5: Temporal Interjection (Parenthetical Jitter)

AI explains things in a straight line. Cause follows effect. Action follows thought. No human writes this way for long — memory intrudes, the environment presses in, a detail surfaces at an inconvenient moment.

**The rule:** Every 300 words, the nearest sentence containing a character action verb (opened, walked, typed, called, entered) receives a parenthetical interjection. The parenthetical must reference the immediate environment or the passage of time — not the subject matter of the sentence.

```
Before: "She opened the laptop and logged in."
After:  "She opened the laptop (the hinges creaked, a reminder of how old the hardware was) and logged in."
```

This is not decoration. It is a structural marker of human attention. People notice things. The parenthetical inserts the evidence of that noticing.

Implementation: the algorithm scans the output in 300-word windows, identifies the first action-verb sentence in each window, and passes it to the LLM with a system instruction specifying the interjection type (environmental detail, time marker, or sensory aside). The insertion point is always before the second clause — never at the sentence's opening.

### C-6: Starting-Fragment Bias

AI almost always opens sentences with Subject + Verb. The subject is named, then it acts. This is the structurally safest pattern for an LLM to predict — and therefore the most detectable.

**The rule:** For every 5 sentences in the output, at least one must begin with a preposition or an adverb, not a subject noun or pronoun.

Valid openers: At, By, In, Under, Above, Across, Through, Slowly, High above, Deep inside, Without warning, Against the wall.

```
Before: "The results came back three weeks later."
After:  "Three weeks later, the results came back."

Before: "She pushed the door open carefully."
After:  "Carefully, she pushed the door open."
```

Implementation: the algorithm walks the output in blocks of five sentences. If none of the five starts with a preposition or adverb, it selects the sentence with the most natural inversion candidate and rewrites its opening via LLM. The rewrite instruction specifies that word order must change — not vocabulary. This preserves the log-prob swap work already done in C-2.

---

## The Few-Shot Structured Prompt

The LLM is never given a free-form instruction. It receives a word-count sequence and a constraint:

```
System:
  You are a master of human stylometry. You will receive a word-count
  sequence [L1, L2, L3...]. You MUST write coherent text where sentence i
  has exactly L_i words (+/- 1). Tone: [mode tone]. Banned phrases:
  Furthermore, Moreover, Additionally, In conclusion, [12 more]...

User:
  Example:
    Sequence: [8, 4, 15, 6]
    Output: "Industrial waste is not a problem waiting to be solved.
             It is currency.
             Every ton of red gypsum sitting in a landfill represents a missed connection.
             Someone needs what you discard."

  Your task:
    Topic: [topic]
    Sequence: [12, 4, 28, 7, 19, ...]
```

The LLM fills the buckets. The math already made the decisions.

---

## Human Error Layer (Optional)

Pass `--drafts 2` or `--drafts 3`. The pipeline generates N versions of the same word-bucket sequence in a single API call, then runs a merge pass that occasionally chooses simpler words where a draft used something complex.

A human writer revises. They write "utilize," cross it out, write "use." That pattern — choosing the accessible word over the sophisticated one — is part of what makes text read as human. Turnitin's authorship check profiles vocabulary complexity over time. This pass breaks that profile.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY to .env
```

---

## Usage

```bash
# LinkedIn cold DM
python entropy_engine.py --topic "industrial symbiosis for chemical manufacturers" --mode pulse --words 120

# Technical email with Human Error layer
python entropy_engine.py --topic "red gypsum valorization ROI" --mode scholar --words 400 --drafts 3

# Long-form (triggers state machine)
python entropy_engine.py --topic "industrial symbiosis market analysis" --mode scholar --words 2500

# JSON output with length map and stats
python entropy_engine.py --topic "..." --mode pulse --words 150 --json

# Debug: see the O-U map before generation
python entropy_engine.py --topic "..." --mode scholar --words 300 --debug

# Reproducible walk
python entropy_engine.py --topic "..." --mode pulse --words 120 --seed 42

# Pipe from stdin
echo "waste-to-resource matching for TiO2 producers" | python entropy_engine.py --mode pulse --words 120
```

---

## CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--topic` / `-t` | required | What to write about |
| `--mode` / `-m` | `pulse` | `pulse`, `scholar`, `narrative` |
| `--words` / `-w` | `150` | Target word count |
| `--context` / `-c` | `""` | Grounding context (recipient info, company facts) |
| `--drafts` / `-d` | `1` | Human Error drafts (1-3) |
| `--main-model` | `gpt-4o` | Generation model |
| `--jitter-model` | `gpt-4o-mini` | Logprob scoring + jitter model |
| `--no-jitter` | off | Skip Module C |
| `--seed` | None | RNG seed for reproducible O-U walks |
| `--debug` | off | Print length map and stats to stderr |
| `--json` | off | Output JSON with text and metadata |

---

## File Structure

```
entropy_engine.py          CLI entry point and pipeline orchestrator
config/
  modes.py                 Mode profiles: mu, sigma, kappa, jitter parameters
modules/
  brownian.py              Module A: O-U length map generator
  phase_scheduler.py       Module B: 500-word state machine for long-form
  llm_caller.py            Stage 2: Constrained few-shot call and Human Error layer
  jitter.py                Module C: Log-prob swap and punctuation friction
requirements.txt
.env.example
```
