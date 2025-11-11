# gpt_client.py
import os
from openai import OpenAI

# Try to load .env locally; ignore on Cloud if package not present
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
# except Exception:
#     pass

# Streamlit Cloud stores secrets in st.secrets
# try:
#     import streamlit as st  # lightweight import
#     _KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
# except Exception:
#     _KEY = os.getenv("OPENAI_API_KEY")
# # Pull key from env or Streamlit secrets
# _KEY = os.getenv("OPENAI_API_KEY")
# try:
#     import streamlit as st  # lightweight import
#     _KEY = _KEY or st.secrets.get("OPENAI_API_KEY")
# except Exception:
#     pass

# if not _KEY or not _KEY.startswith("sk-"):
#     # Fail fast with a friendly message instead of OpenAI AuthenticationError
#     raise RuntimeError(
#         "OPENAI_API_KEY is missing or invalid. "
#         "Set it in Streamlit → Manage app → Settings → Secrets."
#     )

_KEY = os.getenv("OPENAI_API_KEY")
try:
    import streamlit as st
    _KEY = _KEY or st.secrets.get("OPENAI_API_KEY")
except Exception:
    pass

if not _KEY:
    raise RuntimeError("Missing OPENAI_API_KEY. Add it in Streamlit → Manage app → Settings → Secrets.")

client = OpenAI(api_key=_KEY)


SYSTEM_PROMPT_BASE = (
    "You are a compliant, helpful real-estate assistant working under a licensed broker. "
    "Give practical, objective guidance. Never make neighborhood-quality claims; offer objective alternatives "
    "(transit, parks, noise, zoning). Add a short disclaimer when giving price/offer advice: "
    "'Not legal/financial advice; confirm with your licensed agent and local rules.'"
)

def chat(message: str, system_prompt: str = "") -> str:
    """
    Sends a chat message to GPT and returns its reply.
    Optionally includes a system prompt.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    return completion.choices[0].message.content

