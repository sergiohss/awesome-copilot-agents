from __future__ import annotations

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parents[1]

DOC_PAIRS = (
    "install-repository",
    "install-cli",
    "install-vscode",
    "agents",
    "skills",
    "compatibility",
    "troubleshooting",
)


@pytest.mark.parametrize("slug", DOC_PAIRS)
def test_bilingual_docs_exist_with_matching_headings(slug: str):
    en = PROJECT_ROOT / "docs/en" / f"{slug}.md"
    pt = PROJECT_ROOT / "docs/pt-BR" / f"{slug}.md"
    assert en.is_file() and pt.is_file()
    en_heading = en.read_text(encoding="utf-8").splitlines()[0]
    pt_heading = pt.read_text(encoding="utf-8").splitlines()[0]
    assert en_heading.startswith("# ")
    assert pt_heading.startswith("# ")
    assert "33" in en.read_text(encoding="utf-8")
    assert "33" in pt.read_text(encoding="utf-8")
    assert "21" in en.read_text(encoding="utf-8")
    assert "21" in pt.read_text(encoding="utf-8")


def test_readme_languages_reference_same_counts():
    en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    pt = (PROJECT_ROOT / "README.pt-BR.md").read_text(encoding="utf-8")
    assert "33" in en and "33" in pt
    assert "21" in en and "21" in pt
