import re
from collections import Counter
import streamlit as st

def summarize(text, num_sentences=5):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    sentences = re.split(r'(?<=[.!?]) +', text)

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    stop_words = {
        "the", "is", "and", "to", "of", "in", "that", "it", "for", "on",
        "with", "as", "was", "are", "by", "this", "be", "or", "an", "a"
    }
    filtered_words = [w for w in words if w not in stop_words]
    word_freq = Counter(filtered_words)

    sentence_scores = {}
    for sentence in sentences:
        sentence_words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
        score = sum(word_freq.get(word, 0) for word in sentence_words)
        sentence_scores[sentence] = score

    best_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    return "\n".join(f"- {s}" for s in best_sentences)

st.set_page_config(page_title="Free Notes Summarizer", page_icon="📝")
st.title("📝 Free Notes Summarizer")
st.caption("Built by Navraj Singh Waraich")
st.write("Paste your notes, choose summary length, and get a bullet summary.")

notes = st.text_area("Paste your notes here:", height=220, placeholder="Type or paste notes...")
num = st.slider("Summary length (sentences)", 3, 10, 5)

if st.button("Summarize"):
    summary = summarize(notes, num_sentences=num)
    if summary:
        st.subheader("✅ Summary")
        st.text(summary)
    else:
        st.warning("Please paste some notes first.")
