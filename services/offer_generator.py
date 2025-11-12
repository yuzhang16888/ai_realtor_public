# services/offer_generator.py
# Minimal, no external deps – just formats a letter string.
from datetime import date

def generate_offer_letter_stub(inputs: dict) -> str:
    """
    Very basic, deterministic offer letter for testing imports & UI wiring.
    Does NOT call any API. Safe to run on Streamlit Cloud.
    """
    addr = inputs.get("property_address", "123 Main St, San Francisco, CA")
    offer_price = inputs.get("offer_price", 1_000_000)
    earnest = inputs.get("earnest", int(offer_price * 0.03))
    buyer = inputs.get("buyer_name", "Buyer Name")
    close_days = inputs.get("close_days", 30)
    financing = inputs.get("financing", "Conventional")
    contingencies = inputs.get("contingencies", ["Inspection", "Appraisal"])
    notes = inputs.get("notes", "")

    today = date.today().strftime("%B %d, %Y")
    cont_str = ", ".join(contingencies) if contingencies else "None"

    return f"""\
{today}

Seller
{addr}

Re: Purchase Offer for {addr}

Dear Seller,

I am pleased to submit an offer to purchase the property at {addr} for ${offer_price:,.0f}.
I propose an earnest money deposit of ${earnest:,.0f}, with a target close in approximately {close_days} days.
My intended financing is: {financing}.
Requested contingencies: {cont_str}.

Additional notes:
{notes or "(none)"}

Sincerely,
{buyer}
"""

