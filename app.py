import re
from collections import Counter
from datetime import datetime
import streamlit as st

# -------------------- NLP config --------------------
STOP_WORDS = {
    "a","about","above","after","again","against","all","am","an","and","any","are","as","at",
    "be","because","been","before","being","below","between","both","but","by",
    "can","could",
    "did","do","does","doing","down","during",
    "each","else",
    "few","for","from","further",
    "had","has","have","having","he","her","here","hers","herself","him","himself","his","how",
    "i","if","in","into","is","it","its","itself",
    "just",
    "me","more","most","my","myself",
    "no","nor","not","now",
    "of","off","on","once","only","or","other","our","ours","ourselves","out","over","own",
    "same","she","should","so","some","such",
    "than","that","the","their","theirs","them","themselves","then","there","these","they",
    "this","those","through","to","too",
    "under","until","up",
    "very",
    "was","we","were","what","when","where","which","while","who","whom","why","will","with",
    "you","your","yours","yourself","yourselves"
}

def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # sentence end punctuation + whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())

def extract_keywords(text: str, k: int = 8) -> list[str]:
    words = tokenize_words(text)
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    if not filtered:
        return []
    freq = Counter(filtered)
    return [w for w, _ in freq.most_common(k)]

def summarize_extractive(text: str, num_sentences: int = 5, min_sentence_words: int = 6) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return ""

    words = tokenize_words(text)
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    if not filtered:
        picked = sentences[:min(num_sentences, len(sentences))]
        return "\n".join(f"- {s}" for s in picked)

    freq = Counter(filtered)

    scored = []
    for idx, s in enumerate(sentences):
        s_words = tokenize_words(s)
        if len(s_words) < min_sentence_words:
            continue
        score = sum(freq.get(w, 0) for w in s_words if w not in STOP_WORDS)
        scored.append((idx, s, score))

    if not scored:
        # fallback if everything is too short
        for idx, s in enumerate(sentences):
            s_words = tokenize_words(s)
            score = sum(freq.get(w, 0) for w in s_words if w not in STOP_WORDS)
            scored.append((idx, s, score))

    scored.sort(key=lambda x: x[2], reverse=True)

    picked = []
    seen = set()
    for idx, s, _ in scored:
        if s in seen:
            continue
        seen.add(s)
        picked.append((idx, s))
        if len(picked) >= num_sentences:
            break

    # Keep original order for readability
    picked.sort(key=lambda x: x[0])
    return "\n".join(f"- {s}" for _, s in picked)

def highlight_keywords_markdown(bullet_summary: str, keywords: list[str]) -> str:
    """Bold keyword matches in markdown. Keeps it simple + safe."""
    if not bullet_summary or not keywords:
        return bullet_summary
    out = bullet_summary
    for kw in keywords:
        # bold whole-word matches (case-insensitive)
        pattern = re.compile(rf"\b({re.escape(kw)})\b", re.IGNORECASE)
        out = pattern.sub(r"**\1**", out)
    return out

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Notes Summarizer", page_icon="📝", layout="centered")

# Session state
if "notes" not in st.session_state:
    st.session_state.notes = ""
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {title, ts, notes, summary, keywords}

# Minimal header
st.title("📝 Notes Summarizer")
st.caption("Built by Navraj Singh Waraich • Free • Offline")

# ----- Sidebar (pro layout) -----
with st.sidebar:
    st.header("Settings")

    title = st.text_input("Title", value="Untitled Notes", help="Name your notes (you can change this anytime).")

    num = st.slider("Summary length (sentences)", 2, 12, 5)
    min_words = st.slider("Minimum words per sentence", 3, 12, 6)

    show_keywords = st.toggle("Show keywords", value=True)
    highlight = st.toggle("Highlight keywords in summary", value=True)

    st.divider()

    example_text = (
        "Photosynthesis is the process by which plants make their own food. "
        "It occurs in chloroplasts of plant cells. "
        "Plants use sunlight, water, and carbon dioxide to produce glucose. "
        "Oxygen is released as a byproduct of photosynthesis. "
        "Photosynthesis is essential for life on Earth."
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📌 Example"):
            st.session_state.notes = example_text
    with c2:
        if st.button("🧹 Clear"):
            st.session_state.notes = ""

    st.divider()
    st.subheader("About")
    with st.expander("How it works"):
        st.write(
            "This app uses classic NLP: it filters stop-words, counts important word frequencies, "
            "scores each sentence, and extracts the highest-scoring sentences as a summary."
        )
    st.caption("Privacy: notes stay in your browser session for this free version.")

# ----- Main tabs -----
tab1, tab2, tab3 = st.tabs(["Summarize", "History", "About"])

with tab1:
    notes = st.text_area(
        "Paste your notes",
        height=240,
        value=st.session_state.notes,
        placeholder="Paste notes here…"
    )
    st.session_state.notes = notes  # keep synced

    # quick stats
    words_count = len(tokenize_words(notes))
    sent_count = len(split_sentences(notes))
    st.caption(f"Words: {words_count}  •  Sentences: {sent_count}")

    # Buttons row
    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        do_summarize = st.button("✅ Summarize", use_container_width=True)
    with b2:
        do_save = st.button("💾 Save", use_container_width=True)
    with b3:
        # This is the "Copy" option: we show it in a box users can copy
        st.button("📋 Copy", use_container_width=True, help="Copy using the box below after you summarize.")

    # Generate summary when requested OR if they press Save (save implies summarize)
    summary = ""
    keywords = []
    if do_summarize or do_save:
        if not notes.strip():
            st.warning("Paste some notes first.")
        else:
            summary = summarize_extractive(notes, num_sentences=num, min_sentence_words=min_words)
            keywords = extract_keywords(notes, k=8)

            display_summary = summary
            if highlight:
                display_summary = highlight_keywords_markdown(summary, keywords)

            st.subheader("Summary")
            st.markdown(display_summary)

            if show_keywords and keywords:
                st.caption("Top keywords: " + ", ".join(keywords))

            # Copy box (A)
            st.text_area("Copy-ready summary", value=summary, height=140)

            # Download
            st.download_button(
                "⬇️ Download summary (.txt)",
                data=summary,
                file_name=f"{title.strip() or 'summary'}.txt",
                mime="text/plain"
            )

            # Save (B)
            if do_save:
                st.session_state.history.insert(0, {
                    "title": title.strip() or "Untitled Notes",
                    "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "notes": notes,
                    "summary": summary,
                    "keywords": keywords
                })
                st.success("Saved to History ✅")

with tab2:
    st.subheader("History")

    if not st.session_state.history:
        st.info("No saved summaries yet. Use **Save** after you summarize.")
    else:
        # Actions
        a1, a2 = st.columns([1, 1])
        with a1:
            if st.button("🗑️ Clear history"):
                st.session_state.history = []
                st.success("History cleared.")
        with a2:
            # Download all history
            all_text = []
            for item in st.session_state.history:
                all_text.append(f"{item['title']} ({item['ts']})")
                all_text.append(item["summary"])
                all_text.append("")
            st.download_button(
                "⬇️ Download all summaries (.txt)",
                data="\n".join(all_text).strip(),
                file_name="all_summaries.txt",
                mime="text/plain"
            )

        st.divider()

        # List items
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"{item['title']}  •  {item['ts']}"):
                # Editable title (B: user can change title)
                new_title = st.text_input("Edit title", value=item["title"], key=f"title_edit_{i}")
                if new_title != item["title"]:
                    item["title"] = new_title

                st.caption("Summary")
                st.text(item["summary"])

                if item.get("keywords"):
                    st.caption("Keywords: " + ", ".join(item["keywords"]))

                # Load back into editor
                if st.button("↩️ Load into editor", key=f"load_{i}"):
                    st.session_state.notes = item["notes"]
                    st.success("Loaded into editor. Go to the Summarize tab.")

with tab3:
    st.subheader("About this project")
    st.write(
        "A free, minimalist notes summarizer built with Python + Streamlit. "
        "It uses classic NLP sentence scoring (no paid APIs) so it’s fast and deployable."
    )
    st.write("**Made by:** Navraj Singh Waraich")
