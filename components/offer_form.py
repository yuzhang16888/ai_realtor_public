# components/offer_form.py
import streamlit as st

def render_offer_form():
    st.subheader("🏠 Create a Purchase Offer – San Francisco")

    with st.form("offer_form"):
        property_address = st.text_input("Property address", placeholder="123 Main St, San Francisco, CA")
        listing_price = st.number_input("Listing price ($)", min_value=100_000, step=10_000)
        offer_price = st.number_input("Your offer price ($)", min_value=100_000, step=10_000)
        earnest = st.number_input("Earnest money deposit ($)", min_value=1_000, step=1_000)
        close_days = st.slider("Closing in (days)", 10, 60, 30)
        financing = st.selectbox("Financing type", ["All cash", "Conventional", "FHA", "VA", "Other"])
        contingencies = st.multiselect(
            "Contingencies", ["Inspection", "Appraisal", "Loan", "Sale of current home"], ["Inspection", "Appraisal"]
        )
        buyer_name = st.text_input("Buyer name")
        buyer_email = st.text_input("Buyer email (optional)")
        notes = st.text_area("Additional notes to seller", height=100)
        submitted = st.form_submit_button("Generate Offer Letter")

    if not submitted:
        return None

    return {
        "property_address": property_address,
        "listing_price": listing_price,
        "offer_price": offer_price,
        "earnest": earnest,
        "close_days": close_days,
        "financing": financing,
        "contingencies": contingencies,
        "buyer_name": buyer_name,
        "buyer_email": buyer_email,
        "notes": notes,
    }
