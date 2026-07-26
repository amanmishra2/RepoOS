from __future__ import annotations

from repoos.redaction import REDACTED, contains_secret_like, redact_data, redact_text


def test_redacts_common_secret_shapes() -> None:
    token_prefix = "github_" + "pat_"
    source = f"token={token_prefix}abcdefghijklmnopqrstuvwxyz123456 password=hunter2"
    result = redact_text(source)
    assert token_prefix not in result
    assert "hunter2" not in result
    assert REDACTED in result


def test_redacts_openai_key() -> None:
    value = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz"
    assert contains_secret_like(value)
    assert redact_text(value) == REDACTED


def test_recursively_redacts_data() -> None:
    value = {"nested": ["api_key=abcdefghijklmnop", {"safe": "value"}]}
    result = redact_data(value)
    assert "abcdefghijklmnop" not in str(result)
    assert result["nested"][1]["safe"] == "value"


def test_safe_text_is_unchanged() -> None:
    assert redact_text("ordinary public text", redact_home=False) == "ordinary public text"
