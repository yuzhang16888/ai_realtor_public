import streamlit as st
import glob
from gpt_client import chat, SYSTEM_PROMPT_BASE
from kb import load_notes  # your existing loader

# -----------------------------------------------
# 🏠 PAGE SETUP
# -----------------------------------------------
st.set_page_config(page_title="🏡 AI Realtor", page_icon="🏠")

st.title("🏡 AI Realtor")
st.caption("Ask any question about San Francisco home buying — the AI agent uses your real estate notes and market rules.")

# -----------------------------------------------
# 🧠 KNOWLEDGE BASE LOADER WITH RELOAD BUTTON
# -----------------------------------------------

@st.cache_data(show_spinner=False)
def load_kb(seed: int) -> str:
    """
    Cached loader for KB files. Changing the seed busts the cache.
    """
    return load_notes()

if "kb_seed" not in st.session_state:
    st.session_state.kb_seed = 0

with st.sidebar:
    st.subheader("Knowledge Base")
    files = sorted(glob.glob("kb/*.md") + glob.glob("kb/*.txt"))
    if files:
        st.caption("Loaded files:")
        for f in files:
            st.write("•", f.split("/")[-1])
    else:
        st.info("No .md or .txt files found in /kb")

    if st.button("🔄 Reload knowledge"):
        st.session_state.kb_seed += 1
        st.cache_data.clear()
        # works in all Streamlit versions
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()



st.caption(f"📚 KB loaded: {len(files)} file(s). Click 'Reload knowledge' after editing kb/*.md.")

# -----------------------------------------------
# 💬 CHAT INTERFACE
# -----------------------------------------------

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if user_q := st.chat_input("Ask your real estate question..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_q})

    # Load KB content
    NOTES = load_kb(st.session_state.kb_seed)
    SYSTEM_PROMPT = SYSTEM_PROMPT_BASE
    if NOTES:
        SYSTEM_PROMPT += "\n\nUse these internal notes when helpful:\n" + NOTES

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply = chat(user_q, system_prompt=SYSTEM_PROMPT)
            except Exception as e:
                reply = f"⚠️ Error: {e}"
            st.markdown(reply)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})

# -----------------------------------------------
# 🪪 FOOTER
# -----------------------------------------------
st.divider()
st.caption("© 2025 AI Realtor • Not legal/financial advice • Verify with your licensed agent and local regulations.")
