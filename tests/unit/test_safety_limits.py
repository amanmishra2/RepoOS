from __future__ import annotations

from repoos.planning import safety_violations


def test_every_configured_safety_limit_has_a_deterministic_violation() -> None:
    operations = [
        {
            "action": "create",
            "ownership": "managed_section",
            "target": "outside/secret.pem",
        },
        {
            "action": "delete",
            "ownership": "managed_file",
            "target": "managed/old.txt",
        },
    ]
    limits = {
        "max_files_changed": 1,
        "max_files_created": 0,
        "max_files_deleted": 0,
        "max_total_bytes_changed": 1,
        "max_lines_added": 0,
        "max_lines_removed": 0,
        "max_percentage_repository_files_touched": 1.0,
        "allowed_path_prefixes": ["managed"],
        "forbidden_path_patterns": ["*secret*", "*.pem"],
        "max_managed_sections_changed": 0,
    }
    measurements = {
        "files_changed": 2,
        "files_created": 1,
        "files_deleted": 1,
        "total_bytes_changed": 2,
        "lines_added": 1,
        "lines_removed": 1,
        "percentage_repository_files_touched": 50.0,
        "managed_sections_changed": 1,
    }
    assert safety_violations(operations, limits, measurements) == [
        "allowed_path_prefixes",
        "forbidden_path_patterns",
        "max_files_changed",
        "max_files_created",
        "max_files_deleted",
        "max_lines_added",
        "max_lines_removed",
        "max_managed_sections_changed",
        "max_percentage_repository_files_touched",
        "max_total_bytes_changed",
    ]
