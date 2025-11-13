# app.py — clean, working scaffold with auth + gated offer stub

# --- make local packages importable regardless of working dir ---
import sys, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import os
import streamlit as st

from services.auth import update_user_name,get_user_by_id

# --- services (hard requirements) ---
from services.auth import init_db, create_user, verify_credentials

# --- optional services (best-effort to avoid hard crashes) ---
try:
    from services.offer_generator import generate_offer_letter_stub
except Exception:
    generate_offer_letter_stub = None

# (optional search bits; keep best-effort)
try:
    from services.search_client import fast_search
except Exception:
    fast_search = None
# If you used components.* previously, you can re-import them later once repo is stable.

from services.evals import init_eval_db
init_db()
init_eval_db()

from services.evals import create_property_eval,save_uploads,list_property_evals






# ------------------------------
# App setup
# ------------------------------
st.set_page_config(page_title="AI Realtor", layout="wide")
st.title("🏠 AI Realtor — Phase 2")

# init auth DB
init_db()

# session defaults
if "user" not in st.session_state:
    st.session_state["user"] = None
if "auth_view" not in st.session_state:
    # options: "welcome", "login", "signup", "visitor", "profile"
    st.session_state["auth_view"] = "welcome"

# ------------------------------
# helper: require login
# ------------------------------
def require_login() -> bool:
    if st.session_state.get("user"):
        return True
    st.info("Please **log in** to use this feature.")
    return False

# ------------------------------
# Welcome chooser
# ------------------------------
user = st.session_state.get("user")

with st.container():
    st.markdown("### 👋 Welcome")
    if user:
        st.success(f"Signed in as **{user.get('name') or user['email']}**")
        c1, c2 = st.columns(2)
        if c1.button("👤 Profile"):
            st.session_state["auth_view"] = "profile"
        if c2.button("Log out"):
            st.session_state["user"] = None
            st.session_state["auth_view"] = "welcome"
            st.rerun()
    else:
        st.info("Choose how to continue:")
        c1, c2, c3 = st.columns(3)
        if c1.button("🔐 Log in"):
            st.session_state["auth_view"] = "login"
            st.rerun()
        if c2.button("🧭 Continue as visitor"):
            st.session_state["auth_view"] = "visitor"
            st.rerun()
        if c3.button("✨ Sign up"):
            st.session_state["auth_view"] = "signup"
            st.rerun()

# ------------------------------
# Sign Up (only when not logged in)
# ------------------------------
if not user and st.session_state["auth_view"] == "signup":
    with st.expander("👤 Create an account (Sign Up)", expanded=True):
        with st.form("signup_form", clear_on_submit=False):
            su_name = st.text_input("Full name (optional)")
            su_email = st.text_input("Email", placeholder="you@example.com")
            su_pw = st.text_input("Password", type="password")
            su_pw2 = st.text_input("Confirm password", type="password")
            su_submit = st.form_submit_button("Create account")
        if su_submit:
            if not su_email or not su_pw:
                st.error("Email and password are required.")
            elif su_pw != su_pw2:
                st.error("Passwords do not match.")
            else:
                res = create_user(email=su_email, password=su_pw, name=su_name or None)
                if res["ok"]:
                    st.success("Account created! Click **Log in** above.")
                else:
                    st.error(res["error"] or "Could not create account.")

# ------------------------------
# Log In (only when not logged in)
# ------------------------------
if not user and st.session_state["auth_view"] == "login":
    with st.expander("🔐 Log in", expanded=True):
        with st.form("login_form", clear_on_submit=False):
            li_email = st.text_input("Email", placeholder="you@example.com")
            li_pw = st.text_input("Password", type="password")
            li_submit = st.form_submit_button("Log in")
        if li_submit:
            res = verify_credentials(li_email, li_pw)
            if res["ok"] and res["user"]:
                u = res["user"]
                st.session_state["user"] = {"id": u.id, "email": u.email, "name": u.name}
                st.success("Logged in successfully.")
                st.session_state["auth_view"] = "profile"
                st.rerun()
            else:
                st.error(res["error"] or "Login failed.")

# ------------------------------
# ------------------------------
# Profile (only when logged in)
# ------------------------------
user = st.session_state.get("user")
if user and st.session_state["auth_view"] == "profile":
    with st.expander("👤 Profile", expanded=True):
        st.write(f"**Email:** {user['email']}")

        with st.form("profile_form", clear_on_submit=False):
            new_name = st.text_input("Full name", value=user.get("name") or "")
            save_profile = st.form_submit_button("Save")

        if save_profile:
            res = update_user_name(user_id=user["id"], name=new_name or None)
            if res["ok"]:
                # refresh session copy
                refreshed = get_user_by_id(user["id"])
                st.session_state["user"] = {"id": refreshed.id, "email": refreshed.email, "name": refreshed.name}
                st.success("Profile updated.")
            else:
                st.error(res["error"] or "Could not update profile.")


# ------------------------------
# Buyer Profile – stage 1 (intent-conditional UI)
# ------------------------------
if user and st.session_state["auth_view"] == "profile":
    st.markdown("### 🏡 Buyer Profile")

    # initialize once
    if "buyer_profile" not in st.session_state:
        st.session_state["buyer_profile"] = {
            "intent": "Just exploring the market",
            "budget_min": 800000,
            "budget_max": 1200000,
            "city": "San Francisco",
            "subject_property": {  # only used when evaluating a specific property
                "address1": "",
                "address2": "",
                "prop_city": "",
                "zipcode": "",
            },
        }

    profile = st.session_state["buyer_profile"]

    # 1) intent
    intent = st.radio(
        "What brings you here today?",
        ["Just exploring the market", "Evaluating a specific property"],
        index=0 if profile.get("intent") != "Evaluating a specific property" else 1,
        horizontal=True,
    )
    profile["intent"] = intent

    if intent == "Evaluating a specific property":
        # Hide budget/city. Show property address fields instead.
        st.subheader("🧰 What help do you need for this property?")

        # A) Price suggestion toggle → show contingencies if yes
        want_price = st.radio(
            "Are you looking for a price suggestion / offer advice?",
            ["No", "Yes"],
            horizontal=True,
            key="eval_want_price",
        )

        contingencies = []
        if want_price == "Yes":
            st.markdown("**If so, please input/confirm the property address below.**")
            subject = profile.get("subject_property", {}) or {}

            col1, col2 = st.columns(2)
            with col1:
                subject["address1"] = st.text_input("Address line 1", subject.get("address1", ""), key="eval_addr1_inline")
                subject["prop_city"] = st.text_input("City", subject.get("prop_city", profile.get("city","San Francisco")), key="eval_city_inline")
            with col2:
                 subject["address2"] = st.text_input("Address line 2 (unit/suite/floor, optional)", subject.get("address2", ""), key="eval_addr2_inline")
                 subject["zipcode"] = st.text_input("ZIP code", subject.get("zipcode", ""), key="eval_zip_inline")
            # save back to session so the payload uses latest edits
            profile["subject_property"] = subject
            st.session_state["buyer_profile"] = profile
            
            contingencies = st.multiselect(
                "If so, which contingencies might you waive?",
                ["Inspection", "Appraisal", "Loan", "Sale of current home"],
                default=[],
                key="eval_contingencies",
            )

        # B) Buy / Not buy reasoning
        want_buy_advice = st.radio(
            "Are you looking for a buy/not-buy suggestion (e.g., location, litigation, building condition)?",
            ["No", "Yes"],
            horizontal=True,
            key="eval_want_buy_advice",
        )

        concerns = ""
        if want_buy_advice == "Yes":
            concerns = st.text_area(
                "Tell us your concerns (optional)",
                placeholder="e.g., HOA lawsuit? soft-story retrofit? street noise? shadow impact?",
                key="eval_concerns",
            )

        # C) Upload disclosures / docs (optional)
        uploads = st.file_uploader(
            "If you have disclosures from the seller agent, upload them here (PDFs recommended).",
            type=["pdf", "jpg", "png"],
            accept_multiple_files=True,
            key="eval_uploads",
        )

        # D) Save request
        # make sure we have the subject property dict in-scope here
        subject = profile.get("subject_property", {}) or {}
        if st.button("💾 Save Evaluation Request", type="primary"):
            # Build payload to store
            payload = {
            "mode": "evaluating_specific_property",
            "subject_property": {
            "address1": subject.get("address1", ""),
            "address2": subject.get("address2", ""),
            "city":    subject.get("prop_city", ""),
            "zipcode": subject.get("zipcode", ""),
        },
         "asks": {
             "want_price": (want_price == "Yes"),
             "contingencies": contingencies,
             "want_buy_advice": (want_buy_advice == "Yes"),
             "concerns": concerns,
    },
}

            saved_paths = save_uploads(uploads) if uploads else []
            out = create_property_eval(user_id=user["id"], payload=payload, uploaded_paths=saved_paths)
            if out["ok"]:
                st.success(
                    "We’re on it! Your evaluation request was saved. If you shared disclosures, that helps us a ton. "
                    "You’ll receive our recommendations within 24 hours."
                )
            else:
                st.error(f"Could not save request: {out['error']}")
st.divider()
st.markdown("#### 🗂️ Your Property Evaluations")

if user:
    evals = list_property_evals(user_id=user["id"], limit=10)
    if not evals:
        st.caption("No saved evaluations yet.")
    else:
        for e in evals:
            with st.container(border=True):
                st.write(f"**Request #{e['id']}** — status: `{e['status']}` — created: {e['created_at']}")
                sp_payload = e["payload"].get("subject_property", {})
                st.write(
                    f"**Property:** {sp_payload.get('address1','')} {sp_payload.get('address2','')}, "
                    f"{sp_payload.get('city','')} {sp_payload.get('zipcode','')}"
                )
                asks = e["payload"].get("asks", {})
                if asks.get("want_price"):
                    st.write(f"• Price suggestion requested — contingencies: {', '.join(asks.get('contingencies', [])) or 'none'}")
                if asks.get("want_buy_advice"):
                    st.write(f"• Buy/Not-buy advice — concerns: {asks.get('concerns') or '—'}")
else:
    st.info("Log in to view your saved evaluations.")



# ------------------------------
# Offer letter generator (stub) — gated by login
# ------------------------------
with st.expander("🧾 Generate Offer Letter (stub)", expanded=True):
    if require_login():
        if not generate_offer_letter_stub:
            st.warning("Offer generator service not found. Make sure services/offer_generator.py is present.")
        else:
            st.write("Enter basic details — still offline, no GPT yet.")
            with st.form("offer_stub_form", clear_on_submit=False):
                addr = st.text_input("Property address", "850 Minnesota St #M101, San Francisco, CA")
                price = st.number_input("Offer price ($)", min_value=500000, max_value=5000000, value=1200000, step=50000)
                earnest = st.number_input("Earnest money ($)", min_value=1000, max_value=500000, value=int(price * 0.03), step=1000)
                buyer = st.text_input("Buyer name", "Jane Doe")
                close_days = st.slider("Closing in (days)", min_value=10, max_value=60, value=30)
                financing = st.selectbox("Financing type", ["Conventional", "All cash", "FHA", "VA", "Other"])
                contingencies = st.multiselect(
                    "Contingencies",
                    ["Inspection", "Appraisal", "Loan", "Sale of current home"],
                    default=["Inspection", "Appraisal"],
                )
                notes = st.text_area("Additional notes", "We love the light and Dogpatch location.")
                submitted = st.form_submit_button("Generate letter")

            if submitted:
                inputs = {
                    "property_address": addr,
                    "offer_price": price,
                    "earnest": earnest,
                    "buyer_name": buyer,
                    "close_days": close_days,
                    "financing": financing,
                    "contingencies": contingencies,
                    "notes": notes,
                }
                letter = generate_offer_letter_stub(inputs)
                st.code(letter)
                st.download_button("Download letter (txt)", letter, "offer_letter.txt")

# ------------------------------
# (Optional) Search area — keep as-is, or re-hook later
# ------------------------------
with st.expander("🔎 Search (placeholder)", expanded=False):
    if fast_search:
        st.caption("Your existing search UI can be re-inserted here.")
        # TODO: re-add your render_filters / results / chat if desired
    else:
        st.info("Search client not imported. Skip for now.")
