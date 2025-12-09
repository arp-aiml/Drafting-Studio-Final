FORBIDDEN_KEYWORDS = [
    "backdate", "fake invoice", "hide income", "evade tax", 
    "forge signature", "fabricate", "bribery", "launder money"
]

def scan_for_safety(text: str) -> bool:
    """Returns True if safe, False if unsafe content is detected."""
    text_lower = text.lower()
    for word in FORBIDDEN_KEYWORDS:
        if word in text_lower:
            return False
    return True