#!/usr/bin/env python3
"""Fetch the OpenCode Zen model list and write docs/models.json.

Pulls https://opencode.ai/zen/v1/models (the machine-readable source of the
OpenCode Zen pricing/model catalog) and writes a small JSON file that the
GitHub Pages docs site renders. Run on a schedule via .github/workflows/models.yml
or manually with `python3 scripts/generate_models.py`.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = (
    "opencode-hacs-docs/0.1 (+https://github.com/pranjal-joshi/opencode)"
)

MODELS_URL = "https://opencode.ai/zen/v1/models"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "models.json"

# Must match custom_components/opencode/const.py
EXCLUDED_MODEL_PREFIXES = ("gpt-", "grok-", "claude-", "qwen", "gemini-")

FAMILIES = (
    ("deepseek-", "DeepSeek"),
    ("minimax-", "MiniMax"),
    ("glm-", "GLM"),
    ("kimi-", "Kimi"),
    ("qwen", "Qwen"),
    ("gpt-", "GPT"),
    ("grok-", "Grok"),
    ("claude-", "Claude"),
    ("gemini-", "Gemini"),
)


def family_of(model_id: str) -> str:
    """Map a model id to its family name."""
    for prefix, name in FAMILIES:
        if model_id.startswith(prefix):
            return name
    return "Other"


def is_openai_compatible(model_id: str) -> bool:
    """Return True if the model is served through the OpenAI-compatible endpoint."""
    return not model_id.startswith(EXCLUDED_MODEL_PREFIXES)


def is_free(model_id: str) -> bool:
    """Return True for free-tier models."""
    return model_id.endswith("-free") or model_id == "big-pickle"


def main() -> int:
    req = urllib.request.Request(MODELS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    models = []
    for item in payload["data"]:
        model_id = item["id"]
        models.append(
            {
                "id": model_id,
                "family": family_of(model_id),
                "openai_compatible": is_openai_compatible(model_id),
                "free": is_free(model_id),
            }
        )

    models.sort(key=lambda m: (m["family"], m["id"]))

    result = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": MODELS_URL,
        "count": len(models),
        "models": models,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT} with {len(models)} models")
    return 0


if __name__ == "__main__":
    sys.exit(main())
