# app.py — Streamlit chat that uses your KB + GPT
import streamlit as st
from gpt_client import chat, SYSTEM_PROMPT_BASE
from kb import load_notes

# --- Build system prompt from your base rules + KB notes ---
NOTES = load_notes()  # reads kb/*.md and kb/*.txt
SYSTEM_PROMPT = SYSTEM_PROMPT_BASE
if NOTES:
    SYSTEM_PROMPT += "\n\nUse these internal notes when helpful:\n" + NOTES

# --- Page setup ---
st.set_page_config(page_title="🏠 My AI Real Estate Agent", page_icon="🏠", layout="centered")
st.title("🏠 My AI Real Estate Agent")
st.caption("Ask anything about buying a home. (Demo; not legal/financial advice.)")

# --- Chat state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Share your budget, areas (up to 3), and top 3 must-haves — or ask about 2025 commission changes."}
    ]

# --- Render chat history ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- Input box ---
user_q = st.chat_input("Type your real-estate question…")

def maybe_add_disclaimer(q: str, reply: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ["price", "offer", "negot", "comp", "cma", "dom"]):
        reply += "\n\n_Disclaimer: Not legal or financial advice. Verify with your licensed agent and local rules._"
    return reply

if user_q:
    # show user message
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.markdown(user_q)

    # call GPT with your combined system prompt
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            reply = chat(user_q, system_prompt=SYSTEM_PROMPT)
            reply = maybe_add_disclaimer(user_q, reply)
            st.markdown(reply)

    # save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
# addline 