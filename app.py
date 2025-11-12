# app.py
# app.py (very top)
# app.py (top)
import sys, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# sys.path.append(str(pathlib.Path(__file__).parent.resolve()))
import os
import glob
import streamlit as st
from gpt_client import chat, SYSTEM_PROMPT_BASE
from kb import load_notes  # must read all kb/*.md or kb/*.txt
from services.offer_generator import generate_offer_letter_stub






# -----------------------------------------------
# 🏠 PAGE SETUP
# -----------------------------------------------
st.set_page_config(page_title="🏡 AI Realtor", page_icon="🏠", layout="centered")
st.title("🏡 AI Realtor")
st.caption("Ask anything about SF home buying. The agent uses your private notes for context. (Demo; not legal/financial advice.)")

# -----------------------------------------------
# 📚 KNOWLEDGE BASE LOADER (with reload)
# -----------------------------------------------
with st.sidebar:
    st.subheader("🔎 Find Listings (MVP)")

    # remember last filters
    ss = st.session_state
    def _g(key, default): 
        if key not in ss: ss[key] = default
        return ss[key]

    neighborhood = st.text_input("Neighborhood / Area", value=_g("nbhd","Dogpatch, San Francisco, CA"))
    prop_type    = st.selectbox("Property type", ["Condo", "Townhouse", "Single Family"], index=_g("ptype_i",0))
    min_price    = st.number_input("Min price", min_value=0, step=50000, value=_g("pmin",800000))
    max_price    = st.number_input("Max price", min_value=0, step=50000, value=_g("pmax",1500000))
    beds         = st.selectbox("Beds (min)", ["Any", 1, 2, 3], index=_g("beds_i",1))
    baths        = st.selectbox("Baths (min)", ["Any", 1, 2], index=_g("baths_i",0))

    # persist choices
    ss.nbhd = neighborhood
    ss.ptype_i = ["Condo","Townhouse","Single Family"].index(prop_type)
    ss.pmin = int(min_price); ss.pmax = int(max_price)
    ss.beds_i = ["Any",1,2,3].index(beds); ss.baths_i = ["Any",1,2].index(baths)

    def q(v): 
        return "" if v in (None, "Any") else str(v)

    # build links only when user clicks "Search"
    do_search = st.button("🔍 Search")

    if do_search:
        # —— Zillow direct-ish path ——
        z_area = neighborhood.lower().replace(",", "").replace(" ", "-")
        z_base = f"https://www.zillow.com/{z_area}/"
        if prop_type.lower() == "condo":
            z_base += "condos/"

        # Google helpers (robust if portals change URL params)
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
        r_base = "https://www.realtor.com/realestateandhomes-search/"
        r_path = neighborhood.replace(", ", "-").replace(" ", "-")
        r_type = "condo" if prop_type.lower()=="condo" else "type"
        r_link = f"{r_base}{r_path}/type-{r_type}"

        st.success("Links ready—click to open in a new tab:")
        # nice clickable buttons (Streamlit 1.31+)
        st.link_button("Zillow (direct)", z_base)
        st.link_button("Zillow (Google filter)", z_google)
        st.link_button("Redfin (Google filter)", rf_google)
        st.link_button("Realtor.com (direct-ish)", r_link)

        st.caption("Tip: refine details like DOM, HOA, parking on the portal UI after opening.")

    st.divider()
    if st.button("⭐ Save as default filters"):
        st.success("Saved! These values will prefill next time.")


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




with st.expander("🧾 Generate Offer Letter (stub)", expanded=True):
    st.write("Enter basic details — still offline, no GPT yet.")
    with st.form("offer_stub_form"):
        addr = st.text_input("Property address", "850 Minnesota St #M101, San Francisco, CA")
        price = st.number_input("Offer price ($)", 500000, 5000000, 1200000, step=50000)
        buyer = st.text_input("Buyer name", "Jane Doe")
        close_days = st.slider("Closing in (days)", 10, 60, 30)
        financing = st.selectbox("Financing type", ["Conventional", "All cash", "FHA", "VA", "Other"])
        contingencies = st.multiselect(
            "Contingencies",
            ["Inspection", "Appraisal", "Loan", "Sale of current home"],
            ["Inspection", "Appraisal"],
        )
        notes = st.text_area("Additional notes", "We love the light and Dogpatch location.")
        submitted = st.form_submit_button("Generate letter")

    if submitted:
        inputs = {
            "property_address": addr,
            "offer_price": price,
            "buyer_name": buyer,
            "close_days": close_days,
            "financing": financing,
            "contingencies": contingencies,
            "notes": notes,
        }
        letter = generate_offer_letter_stub(inputs)
        st.code(letter)
        st.download_button("Download letter (txt)", letter, "offer_letter.txt")



# -----------------------------------------------
# 🪪 FOOTER
# -----------------------------------------------
st.divider()
st.caption("© 2025 AI Realtor • Demo only. Not legal/financial advice.")
