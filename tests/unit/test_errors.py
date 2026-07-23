from __future__ import annotations

from repoos.errors import ExitCode, invalid_input


def test_error_contract_is_stable() -> None:
    error = invalid_input("Bad input.", field="target")
    assert error.code is ExitCode.INVALID_INPUT
    assert error.as_dict() == {
        "ok": False,
        "error": {
            "type": "invalid_input",
            "message": "Bad input.",
            "exit_code": 2,
            "details": {"field": "target"},
        },
    }
