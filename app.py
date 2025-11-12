# app.py
import os
import glob
import streamlit as st
from gpt_client import chat, SYSTEM_PROMPT_BASE
from kb import load_notes  # must read all kb/*.md or kb/*.txt

# -----------------------------------------------
# 🏠 PAGE SETUP
# -----------------------------------------------
st.set_page_config(page_title="🏡 AI Realtor", page_icon="🏠", layout="centered")
st.title("🏡 AI Realtor")
st.caption("Ask anything about SF home buying. The agent uses your private notes for context. (Demo; not legal/financial advice.)")

# -----------------------------------------------
# 📚 KNOWLEDGE BASE LOADER (with reload)
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
            st.write("•", os.path.basename(f))
    else:
        st.info("No .md or .txt files found in /kb")

    if st.button("🔄 Reload knowledge"):
        st.session_state.kb_seed += 1
        st.cache_data.clear()
        # streamlit >=1.32 uses st.rerun()
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

st.caption(f"📚 KB loaded: {len(files)} file(s). Click 'Reload knowledge' after editing kb/*.md.")

# -----------------------------------------------
# 🔎 FIND LISTINGS (MVP DEEP LINKS)
# -----------------------------------------------
with st.sidebar:
    st.subheader("🔎 Find Listings (MVP)")
    neighborhood = st.text_input("Neighborhood / Area", value="Dogpatch, San Francisco, CA")
    prop_type = st.selectbox("Property type", ["Condo", "Townhouse", "Single Family"], index=0)
    min_price = st.number_input("Min price", min_value=0, step=50000, value=800000)
    max_price = st.number_input("Max price", min_value=0, step=50000, value=1500000)
    beds = st.selectbox("Beds (min)", ["Any", 1, 2, 3], index=1)
    baths = st.selectbox("Baths (min)", ["Any", 1, 2], index=0)

    def q(v):
        return "" if v in (None, "Any") else str(v)

    # —— Zillow direct-ish path (readable; may need user tweaks) ——
    z_area = neighborhood.lower().replace(",", "").replace(" ", "-")
    z_base = f"https://www.zillow.com/{z_area}/"
    if prop_type.lower() == "condo":
        z_base += "condos/"

    # Zillow via Google with filters (robust fallback)
    z_google = (
        "https://www.google.com/search?q=" +
        "+".join([
            "site:zillow.com",
            neighborhood.replace(" ", "+"),
            "condos" if prop_type.lower() == "condo" else prop_type.lower(),
            f"${min_price}-{max_price}",
            (f"{beds}+bed" if q(beds) else ""),
            (f"{baths}+bath" if q(baths) else "")
        ])
    )

    # Redfin via Google (since Redfin URLs change often)
    rf_google = (
        "https://www.google.com/search?q=" +
        "+".join([
            "site:redfin.com",
            neighborhood.replace(" ", "+"),
            "condos" if prop_type.lower() == "condo" else prop_type.lower(),
            f"${min_price}-{max_price}",
            (f"{beds}+bed" if q(beds) else ""),
            (f"{baths}+bath" if q(baths) else "")
        ])
    )

    # Realtor.com direct-ish
    r_base = "https://www.realtor.com/realestateandhomes-search/"
    r_path = neighborhood.replace(", ", "-").replace(" ", "-")
    r_type = "condo" if prop_type.lower() == "condo" else "type"
    r_link = f"{r_base}{r_path}/type-{r_type}"

    st.markdown("**Open searches:**")
    st.markdown(f"- [Zillow (direct)]({z_base})")
    st.markdown(f"- [Zillow (Google filter)]({z_google})")
    st.markdown(f"- [Redfin (Google filter)]({rf_google})")
    st.markdown(f"- [Realtor.com (direct-ish)]({r_link})")
    st.caption("These open live results. For precise filters (DOM, HOA, parking), adjust on the portal UI.")

# -----------------------------------------------
# 💬 CHAT INTERFACE
# -----------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Share your budget, areas (up to 3), and must-haves — or ask about SF offer strategy."}
    ]

# Render history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input
user_q = st.chat_input("Type your real-estate question…")

def maybe_add_disclaimer(q: str, reply: str) -> str:
    ql = q.lower()
    if any(k in ql for k in ["price", "offer", "negot", "comp", "cma", "dom", "value"]):
        reply += "\n\n*_Disclaimer: Not legal/financial advice. Verify with your licensed agent and local rules._*"
    return reply

if user_q:
    st.session_state.messages.append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.markdown(user_q)

    # Build system prompt with KB
    NOTES = load_kb(st.session_state.kb_seed)
    SYSTEM_PROMPT = SYSTEM_PROMPT_BASE
    if NOTES:
        SYSTEM_PROMPT += "\n\nUse these internal notes when helpful:\n" + NOTES

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                reply = chat(user_q, system_prompt=SYSTEM_PROMPT)
                reply = maybe_add_disclaimer(user_q, reply)
            except Exception as e:
                reply = f"⚠️ Error: {e}"
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# -----------------------------------------------
# 🪪 FOOTER
# -----------------------------------------------
st.divider()
st.caption("© 2025 AI Realtor • Demo only. Not legal/financial advice.")
