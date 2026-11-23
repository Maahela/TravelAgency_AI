"""
Security regression tests for input handling.
"""
from database.airtable_client import formula_str
from email_handler.outlook_sender import OutlookSender


def test_formula_str_escapes_quotes():
    # A crafted hotel name must not be able to close the string literal
    payload = "x'), TRUE(), ('"
    out = formula_str(payload)
    assert out == "'x\\'), TRUE(), (\\''"
    assert out.startswith("'") and out.endswith("'")


def test_formula_str_escapes_backslashes_first():
    # A trailing backslash must not escape the closing quote
    assert formula_str("abc\\") == "'abc\\\\'"
    assert formula_str("a\\'b") == "'a\\\\\\'b'"


def test_formula_str_strips_newlines():
    assert "\n" not in formula_str("line1\nline2")


def test_rate_request_email_escapes_html():
    sender = OutlookSender()
    result = sender.generate_rate_request_email(
        "<script>alert(1)</script> Hotel", "hotel@example.com", {"season": "<b>2026</b>"}
    )
    assert "<script>" not in result["body"]
    assert "&lt;script&gt;" in result["body"]
    assert "<b>2026</b>" not in result["body"]
