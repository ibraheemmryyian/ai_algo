"""
Entropy Engine — Streamlit Web UI
Run with: streamlit run ui/app.py
"""

import sys
import os
import re
import json
import logging
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import streamlit as st

from config.modes import MODES
from ui.processing.file_extractor import extract_text, word_count, auto_detect_mode
from ui.processing.fingerprint import extract_fingerprint, fingerprint_to_prompt_block
from ui.processing.pipeline_adapter import run_generate, run_humanize

logging.basicConfig(level=logging.INFO)

# ─────────────────────────────────────────────────────────────────────────────
# Page config and custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Entropy Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: #0d0f14;
    color: #e2e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111318;
    border-right: 1px solid #1e2330;
}

/* Header */
.ee-header {
    padding: 2rem 0 1rem 0;
    border-bottom: 1px solid #1e2330;
    margin-bottom: 2rem;
}
.ee-header h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -0.5px;
}
.ee-header p {
    color: #64748b;
    margin: 0.3rem 0 0 0;
    font-size: 0.9rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #111318;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #1e2330;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 0.5rem 1.2rem;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #1e2330 !important;
    color: #a78bfa !important;
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    background: #111318 !important;
    border: 1px solid #1e2330 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.2) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.6rem 1.8rem;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

/* Output area */
.output-box {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 1.5rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.925rem;
    line-height: 1.75;
    color: #e2e8f0;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 600px;
    overflow-y: auto;
}

/* Stats grid */
.stat-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-label {
    font-size: 0.75rem;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
}

/* Mode badge */
.mode-badge {
    display: inline-block;
    background: rgba(124, 58, 237, 0.15);
    color: #a78bfa;
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Fingerprint card */
.fp-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-left: 3px solid #7c3aed;
    border-radius: 8px;
    padding: 1rem;
    font-size: 0.85rem;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: #111318 !important;
    border: 1px solid #1e2330 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* Slider */
.stSlider > div > div > div > div {
    background: #7c3aed !important;
}

/* File uploader */
.stFileUploader {
    background: #111318;
    border: 1px dashed #2d3748;
    border-radius: 12px;
    padding: 1rem;
}

/* Warning / info */
.stAlert {
    border-radius: 8px;
}

/* Divider */
hr {
    border-color: #1e2330;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
if "fingerprint" not in st.session_state:
    st.session_state.fingerprint = None
if "fp_block" not in st.session_state:
    st.session_state.fp_block = ""
if "api_key_override" not in st.session_state:
    st.session_state.api_key_override = ""


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="ee-header">
  <h1>⚡ Entropy Engine</h1>
  <p>Break the AI signature. Ornstein-Uhlenbeck sentence control + six-pass post-processing.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — controls
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Controls")

    mode = st.selectbox(
        "Mode",
        options=list(MODES.keys()),
        format_func=lambda m: {
            "pulse":     "Pulse — LinkedIn, cold DMs",
            "scholar":   "Scholar — Technical emails, proposals",
            "narrative": "Narrative — Founder stories, follow-ups",
            "academic":  "Academic — Essays, research papers",
        }.get(m, m),
        index=0,
    )

    target_words = st.slider(
        "Target word count",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        help="Only applies to Generate mode. Humanize mode processes the full input.",
    )

    draft_count = st.select_slider(
        "Human Error drafts",
        options=[1, 2, 3],
        value=1,
        help="Generate N drafts and merge them — simulates human revision. More drafts = more tokens.",
    )

    jitter_intensity = st.select_slider(
        "Jitter intensity",
        options=["Off", "Normal", "Aggressive"],
        value="Normal",
    )
    skip_jitter = jitter_intensity == "Off"

    st.markdown("---")
    st.markdown("### Models")

    main_model = st.text_input(
        "Generation model",
        value="gpt-4o",
        help="Main model for text generation (Stage 2).",
    )
    jitter_model = st.text_input(
        "Jitter model",
        value="gpt-4o-mini",
        help="Cheaper model for logprob scoring and Module C passes.",
    )

    st.markdown("---")
    st.markdown("### Advanced")

    seed_input = st.text_input(
        "RNG seed (optional)",
        value="",
        placeholder="e.g. 42",
        help="Pin the Brownian walk for reproducible output.",
    )
    seed = int(seed_input) if seed_input.strip().isdigit() else None

    st.markdown("---")
    st.markdown("### API Key")
    api_key_input = st.text_input(
        "Override OPENAI_API_KEY",
        type="password",
        value=st.session_state.api_key_override,
        placeholder="sk-... (overrides .env)",
    )
    if api_key_input:
        st.session_state.api_key_override = api_key_input
        os.environ["OPENAI_API_KEY"] = api_key_input


# ─────────────────────────────────────────────────────────────────────────────
# Main tabs
# ─────────────────────────────────────────────────────────────────────────────

tab_generate, tab_humanize, tab_upload, tab_tone = st.tabs([
    "✦ Generate",
    "⟳ Humanize",
    "↑ Upload",
    "◈ Tone Mimic",
])


# ── TAB 1: GENERATE ──────────────────────────────────────────────────────────

with tab_generate:
    st.markdown("#### What do you want to write about?")

    topic = st.text_area(
        "Topic",
        height=100,
        placeholder="e.g. 'A cold outreach email to a chemical plant procurement manager about industrial waste valorization'",
        label_visibility="collapsed",
    )

    context = st.text_area(
        "Context (optional)",
        height=80,
        placeholder="Recipient name, company info, key facts to include, tone notes...",
        help="Extra grounding passed to the LLM. Not shown to the reader.",
    )

    if st.session_state.fp_block:
        st.info("Tone Mimic profile active — your writing style will be applied.", icon="◈")

    col_run, col_space = st.columns([1, 3])
    with col_run:
        run_gen = st.button("Run Engine", key="btn_generate", use_container_width=True)

    if run_gen:
        if not topic.strip():
            st.error("Enter a topic before running.")
        else:
            with st.spinner("Stage 1: Generating O-U length map..."):
                pass
            with st.spinner("Running pipeline — this takes 20-60 seconds..."):
                try:
                    result = run_generate(
                        topic=topic,
                        mode=mode,
                        target_words=target_words,
                        context=context,
                        draft_count=draft_count,
                        main_model=main_model,
                        jitter_model=jitter_model,
                        skip_jitter=skip_jitter,
                        seed=seed,
                        tone_fingerprint_block=st.session_state.fp_block,
                    )
                    st.session_state.result = result
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Pipeline error: {str(e)[:300]}")


# ── TAB 2: HUMANIZE (PASTE) ───────────────────────────────────────────────────

with tab_humanize:
    st.markdown("#### Paste AI-generated text to humanize")
    st.caption("Skips Stages 1 and 2 — runs Module C only on your existing text.")

    paste_text = st.text_area(
        "Input text",
        height=300,
        placeholder="Paste any AI-generated text here...",
        label_visibility="collapsed",
    )

    wc_display = word_count(paste_text) if paste_text.strip() else 0
    st.caption(f"{wc_display} words")

    col_h, col_s = st.columns([1, 3])
    with col_h:
        run_hum = st.button("Humanize", key="btn_humanize", use_container_width=True)

    if run_hum:
        if not paste_text.strip():
            st.error("Paste some text first.")
        else:
            with st.spinner("Running Module C passes..."):
                try:
                    result = run_humanize(
                        text=paste_text,
                        mode=mode,
                        jitter_model=jitter_model,
                        skip_jitter=skip_jitter,
                    )
                    st.session_state.result = result
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {str(e)[:300]}")


# ── TAB 3: UPLOAD ─────────────────────────────────────────────────────────────

with tab_upload:
    st.markdown("#### Upload a file to humanize")
    st.caption("Supports .txt, .md, .pdf, .docx — auto-detects mode from length.")

    uploaded_file = st.file_uploader(
        "Drop your file here",
        type=["txt", "md", "pdf", "docx"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        extracted = extract_text(file_bytes, uploaded_file.name)
        suggested_mode = auto_detect_mode(extracted)

        st.success(
            f"Extracted {word_count(extracted)} words from **{uploaded_file.name}**. "
            f"Suggested mode: **{suggested_mode}**"
        )

        with st.expander("Preview extracted text"):
            st.text(extracted[:1000] + ("..." if len(extracted) > 1000 else ""))

        col_u, col_s = st.columns([1, 3])
        with col_u:
            run_upload = st.button("Humanize File", key="btn_upload", use_container_width=True)

        if run_upload:
            use_mode = mode  # user can override via sidebar
            with st.spinner("Running Module C passes on uploaded content..."):
                try:
                    result = run_humanize(
                        text=extracted,
                        mode=use_mode,
                        jitter_model=jitter_model,
                        skip_jitter=skip_jitter,
                    )
                    st.session_state.result = result
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {str(e)[:300]}")


# ── TAB 4: TONE MIMIC ────────────────────────────────────────────────────────

with tab_tone:
    st.markdown("#### Tone Mimic")
    st.caption(
        "Upload 2-5 samples of your own writing. "
        "The engine extracts your stylometric fingerprint and applies it to all generation."
    )

    st.info(
        "**Privacy:** Uploaded samples are processed in memory only. "
        "Text is sent to the OpenAI API (your own key) and not stored anywhere else.",
        icon="🔒",
    )

    sample_files = st.file_uploader(
        "Upload writing samples",
        type=["txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if sample_files:
        samples_text = []
        for f in sample_files:
            text = extract_text(f.read(), f.name)
            samples_text.append(text)

        if st.button("Extract My Style", key="btn_fingerprint", use_container_width=False):
            with st.spinner("Analysing your writing style..."):
                fp = extract_fingerprint(samples_text)
                st.session_state.fingerprint = fp
                st.session_state.fp_block = fingerprint_to_prompt_block(fp)

    if st.session_state.fingerprint:
        fp = st.session_state.fingerprint
        st.markdown("**Your style fingerprint:**")
        st.markdown(f"""
<div class="fp-card">
  Sentences analysed:   {fp['n_sentences_analysed']}<br>
  Mean length:          {fp['custom_mu']} words<br>
  Std deviation:        {fp['custom_sigma']} words<br>
  Vocab diversity:      {fp['vocab_diversity']}<br>
  Common openers:       {', '.join(f'"{o}"' for o in fp['top_openers'][:3])}<br>
  Commas/sentence:      {fp['punct_style'].get('commas_per_sentence', '-')}<br>
  Dashes/sentence:      {fp['punct_style'].get('dashes_per_sentence', '-')}
</div>
""", unsafe_allow_html=True)

        if fp.get("example_sentences"):
            with st.expander("Example sentences used in prompt"):
                for ex in fp["example_sentences"]:
                    st.markdown(f"> {ex}")

        col_clear, _ = st.columns([1, 3])
        with col_clear:
            if st.button("Clear Tone Profile", key="btn_clear_fp"):
                st.session_state.fingerprint = None
                st.session_state.fp_block = ""
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Output panel — shown below all tabs when a result exists
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.result:
    result = st.session_state.result
    text = result["text"]

    st.markdown("---")
    st.markdown("### Output")

    # Mode badge + pipeline label
    pipeline_label = result.get("pipeline", "full_pipeline")
    st.markdown(
        f'<span class="mode-badge">{result["mode"]}</span> '
        f'<span style="color:#475569;font-size:0.8rem;margin-left:0.5rem;">'
        f'{result["actual_words"]} words</span>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # Text output
    st.markdown(
        f'<div class="output-box">{text}</div>',
        unsafe_allow_html=True,
    )

    # Copy / download row
    col_copy, col_dl_txt, col_dl_md, col_regen = st.columns([2, 1, 1, 1])

    with col_copy:
        # Streamlit doesn't have a native copy button — use JS via components
        st.code(text, language=None)  # user can select-all from here
        st.caption("Select all text above to copy (Ctrl+A / Cmd+A)")

    with col_dl_txt:
        st.download_button(
            "Download .txt",
            data=text.encode("utf-8"),
            file_name="entropy_output.txt",
            mime="text/plain",
        )

    with col_dl_md:
        st.download_button(
            "Download .md",
            data=text.encode("utf-8"),
            file_name="entropy_output.md",
            mime="text/markdown",
        )

    with col_regen:
        if st.button("Clear", key="btn_clear"):
            st.session_state.result = None
            st.rerun()

    # Stats panel
    with st.expander("Pipeline stats"):
        stats = result.get("stats", {})
        jstats = result.get("jitter_stats", {})

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        metrics = [
            (c1, result.get("actual_words", 0), "Words"),
            (c2, stats.get("n_sentences", 0), "Sentences"),
            (c3, f"{stats.get('std', 0):.1f}", "Length std"),
            (c4, jstats.get("logprob_swaps", 0), "Swaps"),
            (c5, jstats.get("embargo_rewrites", 0) + jstats.get("punct_breaks", 0), "Punct breaks"),
            (c6, jstats.get("fragment_rewrites", 0) + jstats.get("temporal_injections", 0), "Structure edits"),
        ]
        for col, val, label in metrics:
            with col:
                st.markdown(
                    f'<div class="stat-card">'
                    f'<div class="stat-value">{val}</div>'
                    f'<div class="stat-label">{label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if result.get("length_map"):
            st.markdown("**O-U length map:**")
            st.code(str(result["length_map"]))
