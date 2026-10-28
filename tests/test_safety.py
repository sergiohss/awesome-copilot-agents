from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[1]

SCAN_ROOTS = (
    PROJECT_ROOT / "src",
    PROJECT_ROOT / ".github",
    PROJECT_ROOT / "packages",
)

SCAN_SUFFIXES = {".md", ".yaml", ".yml"}

FORBIDDEN_BYPASS_PHRASES = (
    "captcha solving",
    "stealth plugin",
    "fingerprint spoofing",
    "access-control bypass",
    "bot-detection evasion",
    "credential theft",
)

FORBIDDEN_VENDOR_TOKENS = (
    "@agent-",
    "~/.claude",
    "model: opus",
    "WriteFile",
    "WebFetch",
    "Context7",
)


def _iter_scanned_files():
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SCAN_SUFFIXES:
                yield path


@pytest.fixture(scope="module")
def scanned_file_texts() -> dict[Path, str]:
    return {path: path.read_text(encoding="utf-8") for path in _iter_scanned_files()}


def test_canonical_and_generated_files_avoid_forbidden_bypass_phrases(scanned_file_texts):
    violations: list[str] = []
    for path, text in scanned_file_texts.items():
        lowered = text.lower()
        for phrase in FORBIDDEN_BYPASS_PHRASES:
            if phrase in lowered:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}: {phrase}")
    assert not violations, "\n".join(violations)


def test_canonical_and_generated_files_avoid_forbidden_vendor_tokens(scanned_file_texts):
    violations: list[str] = []
    for path, text in scanned_file_texts.items():
        for token in FORBIDDEN_VENDOR_TOKENS:
            if token.lower() in text.lower():
                violations.append(f"{path.relative_to(PROJECT_ROOT)}: {token}")
    assert not violations, "\n".join(violations)


def test_acquisition_profile_refuses_unauthorized_work_without_bypass_lexicon():
    text = (
        PROJECT_ROOT / "src/profiles/python-web-scraping-expert.md"
    ).read_text(encoding="utf-8").lower()
    assert "needs-approval" in text
    assert "authorization" in text
    for phrase in FORBIDDEN_BYPASS_PHRASES:
        assert phrase not in text
