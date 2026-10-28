from __future__ import annotations

import json
from typing import Sequence
import unicodedata

from .errors import ValidationError
from .models import AgentSpec


def normalize_text(text: str, *, source: str) -> str:
    """Return portable NFC/LF text after rejecting invalid Unicode scalars."""
    for index, character in enumerate(text):
        if 0xD800 <= ord(character) <= 0xDFFF:
            raise ValidationError(
                f"{source}: surrogate code point U+{ord(character):04X} at index {index}"
            )
    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")


def render_profile(agent: AgentSpec, body: str, fragments: Sequence[str]) -> str:
    """Render one Copilot profile using the exact portable frontmatter contract."""
    description = json.dumps(agent.description, ensure_ascii=False)
    tools = ", ".join(agent.tools)
    sections = [body.strip(), *(fragment.strip() for fragment in fragments)]
    rendered = (
        f"---\nname: {agent.id}\ndescription: {description}\n"
        f"tools: [{tools}]\n---\n\n"
        + "\n\n".join(sections)
        + "\n"
    )
    return normalize_text(rendered, source=f"profile {agent.id}")
