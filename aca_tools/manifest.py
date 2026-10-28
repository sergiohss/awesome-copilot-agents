from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
from typing import Mapping

from .provenance import SourceBaseline
from .render import normalize_text


def build_manifest(
    package_id: str,
    files: Mapping[PurePosixPath, bytes],
    *,
    baseline: SourceBaseline,
    adaptation_version: str,
    complete: bool,
) -> bytes:
    """Build a deterministic SHA-256 inventory for one generated package."""
    entries = [
        {
            "path": path.as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
        for path, data in sorted(files.items(), key=lambda item: item[0].as_posix())
    ]
    document = {
        "schema_version": baseline.schema_version,
        "package_id": package_id,
        "adaptation_version": adaptation_version,
        "complete": complete,
        "upstream_repository": baseline.upstream_repository,
        "upstream_commit": baseline.upstream_commit,
        "license_spdx": baseline.license.spdx,
        "source_attribution": baseline.license.attribution,
        "files": entries,
    }
    rendered = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    return normalize_text(rendered, source=f"manifest {package_id}").encode("utf-8")
