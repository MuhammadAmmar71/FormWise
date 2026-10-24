"""Catch obvious personal data before it reaches the LLM. This is a safety net for a demo, not a DLP system."""
import re

PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,4})?\b"),
    "PHONE": re.compile(r"(?<!\w)(?:\+|00)\d{1,3}[\s/-]?\d[\d\s/-]{6,}\d\b|\b0\d{2,5}[\s/-]?\d{5,}\b"),
    # Steuer-ID: 11 digits, often written 12 345 678 901.
    "TAX_ID": re.compile(r"\b\d{2} ?\d{3} ?\d{3} ?\d{3}\b"),
    # ID card / passport serials: 8-10 uppercase letters and digits, with at least one of each.
    "DOCUMENT_NO": re.compile(r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8,10}\b"),
    # A full date only counts as PII when it is said to be a birth date.
    "BIRTH_DATE": re.compile(
        r"(?i)(?:geboren|geb\.|born|birth|geburtsdatum)\D{0,20}\d{1,2}[./-]\d{1,2}[./-](?:19|20)\d{2}"
    ),
}


def redact(text: str) -> tuple[str, list[str]]:
    """Return the text with PII replaced by [REDACTED-TYPE] and the list of types found."""
    found = []
    for kind, pattern in PATTERNS.items():
        text, n = pattern.subn(f"[REDACTED-{kind}]", text)
        if n:
            found.append(kind)
    return text, found
