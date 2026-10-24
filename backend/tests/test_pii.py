from app.pii import redact


def test_redacts_common_personal_data():
    text, found = redact(
        "Meine IBAN ist DE89 3704 0044 0532 0130 00, Mail max@example.org, "
        "Tel. +49 170 1234567, Steuer-ID 12 345 678 901, geboren am 01.02.1990."
    )
    assert set(found) >= {"IBAN", "EMAIL", "PHONE", "TAX_ID", "BIRTH_DATE"}
    for leaked in ("DE89", "max@example.org", "1234567", "678 901", "1990"):
        assert leaked not in text


def test_passport_like_serial_is_redacted():
    text, found = redact("My passport number is AB1234567")
    assert "DOCUMENT_NO" in found and "AB1234567" not in text


def test_normal_questions_are_untouched():
    for q in ("How long do I have to register after moving in on 01.10.2026?",
              "Was ist eine Wohnungsgeberbestätigung nach § 19 BMG?",
              "Do I need to register if I stay 3 months?"):
        assert redact(q) == (q, [])
