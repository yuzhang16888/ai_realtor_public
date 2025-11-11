# kb.py
import glob, os

def load_notes(max_chars: int = 6000) -> str:
    """
    Reads kb/*.md and kb/*.txt, concatenates, trims to max_chars.
    """
    parts = []
    for path in glob.glob("kb/*.md") + glob.glob("kb/*.txt"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                parts.append(f"\n[NOTE: {os.path.basename(path)}]\n" + f.read())
        except Exception:
            pass
    joined = "\n".join(parts)
    return joined[:max_chars]

def build_system_prompt(extra_notes: str = "") -> str:
    from gpt_client import SYSTEM_PROMPT_BASE
    if extra_notes:
        return SYSTEM_PROMPT_BASE + "\n\nUse these internal notes when helpful:\n" + extra_notes
    return SYSTEM_PROMPT_BASE

if __name__ == "__main__":
    notes = load_notes()
    print("Loaded notes:\n")
    print(notes)
