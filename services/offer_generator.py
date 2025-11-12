# services/offer_generator.py
from services.llm_client import get_client
from config import settings

def generate_offer_letter(inputs: dict) -> str:
    client = get_client()

    prompt = f"""
    You are a California real-estate assistant helping a buyer draft a professional
    home purchase offer for a San Francisco property.

    Use SF customs: reference earnest money (3%), contingencies, and escrow timing.
    Format as a friendly, formal letter from buyer to seller.

    Inputs:
    {inputs}
    """

    completion = client.chat.completions.create(
        model=settings.model,
        messages=[
            {"role": "system", "content": "You are an expert real estate writer for the San Francisco market."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    return completion.choices[0].message.content.strip()
