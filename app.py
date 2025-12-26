import re
from collections import Counter
import streamlit as st

# A stronger (but still simple) stop-word set for better summaries
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
    """Split text into sentences in a reasonably robust way."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Split on sentence-ending punctuation followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Clean + filter very short lines
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def tokenize_words(text: str) -> list[str]:
    """Extract words (letters + apostrophes) in lowercase."""
    return re.findall(r"[a-zA-Z']+", text.lower())

def summarize_extractive(text: str, num_sentences: int = 5, min_sentence_words: int = 6) -> tuple[str, list[str]]:
    """
    Extractive summarizer:
    - Scores sentences based on word frequency (excluding stop-words)
    - Selects top N by score
    - Returns them in original order (better readability)
    Also returns top keywords for optional display.
    """
    sentences = split_sentences(text)
    if not sentences:
        return "", []

    words = tokenize_words(text)
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    if not filtered:
        # If everything got filtered out, fallback to first N sentences
        picked = sentences[:min(num_sentences, len(sentences))]
        return "\n".join(f"- {s}" for s in picked), []

    freq = Counter(filtered)

    # Score each sentence
    scored = []
    for idx, s in enumerate(sentences):
        s_words = tokenize_words(s)
        # Filter out very short sentences (often titles/fragments)
        if len(s_words) < min_sentence_words:
            continue
        score = sum(freq.get(w, 0) for w in s_words if w not in STOP_WORDS)
        scored.append((idx, s, score))

    # If all got filtered out by min_sentence_words, allow shorter ones
    if not scored:
        for idx, s in enumerate(sentences):
            s_words = tokenize_words(s)
            score = sum(freq.get(w, 0) for w in s_words if w not in STOP_WORDS)
            scored.append((idx, s, score))

    # Pick top N by score (dedupe by exact sentence text)
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

    # Return in original order (so it flows)
    picked.sort(key=lambda x: x[0])
    bullet_summary = "\n".join(f"- {s}" for _, s in picked)

    # Top keywords (nice for “what it focused on”)
    top_keywords = [w for w, _ in freq.most_common(8)]
    return bullet_summary, top_keywords


# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Free Notes Summarizer", page_icon="📝", layout="centered")

st.title("📝 Free Notes Summarizer")
st.caption("Built by Navraj Singh Waraich")

example_text = (
    "Photosynthesis is the process by which plants make their own food. "
    "It occurs in chloroplasts of plant cells. "
    "Plants use sunlight, water, and carbon dioxide. "
    "Glucose is produced for energy. "
    "Oxygen is released as a byproduct. "
    "Photosynthesis is essential for life on Earth."
)

# Session state for buttons
if "notes" not in st.session_state:
    st.session_state.notes = ""

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("📌 Insert example"):
        st.session_state.notes = example_text
with col2:
    if st.button("🧹 Clear"):
        st.session_state.notes = ""
with col3:
    show_keywords = st.toggle("Show keywords", value=True)

notes = st.text_area("Paste your notes here:", height=240, value=st.session_state.notes, placeholder="Paste notes...")

num = st.slider("Summary length (sentences)", 2, 12, 5)
min_words = st.slider("Minimum words per sentence", 3, 12, 6)

# Quick stats
sentences_count = len(split_sentences(notes))
words_count = len(tokenize_words(notes))
st.caption(f"Words: {words_count}  •  Sentences: {sentences_count}")

if st.button("✅ Summarize"):
    summary, keywords = summarize_extractive(notes, num_sentences=num, min_sentence_words=min_words)
    if not summary:
        st.warning("Please paste some notes first.")
    else:
        st.subheader("Summary")
        st.code(summary, language="markdown")

        if show_keywords and keywords:
            st.caption("Top keywords: " + ", ".join(keywords))

        st.download_button(
            "⬇️ Download summary (.txt)",
            data=summary,
            file_name="summary.txt",
            mime="text/plain"
        )

st.markdown("---")
st.caption("Tip: For best results, paste full paragraphs (not just titles).")
