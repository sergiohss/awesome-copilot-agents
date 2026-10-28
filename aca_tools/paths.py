from __future__ import annotations

import os
from pathlib import Path


def upstream_vendor_dir(project_root: Path) -> Path:
    return project_root / "vendor/upstream/awesome-claude-agents"


def is_upstream_source_root(path: Path) -> bool:
    """True when path looks like the pinned awesome-claude-agents tree on disk."""
    if not path.is_dir():
        return False
    return (path / "agents/core/code-archaeologist.md").is_file()


def resolve_upstream_source_root(project_root: Path) -> Path:
    """Pick a local checkout used for upstream blob verification."""
    candidates: list[Path] = []
    env = os.environ.get("ACA_SOURCE_ROOT")
    if env:
        candidates.append(Path(env))
    candidates.append(upstream_vendor_dir(project_root))
    candidates.append(Path("/var/www/projetos/awesome-claude-agents"))
    for candidate in candidates:
        if is_upstream_source_root(candidate):
            return candidate.resolve()
    vendor = upstream_vendor_dir(project_root)
    raise FileNotFoundError(
        "Upstream source root not found. Clone the pinned awesome-claude-agents commit with "
        f"`python scripts/bootstrap_upstream.py` or set ACA_SOURCE_ROOT. "
        f"Expected agent files such as {vendor / 'agents/core/code-archaeologist.md'}."
    )
