from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    parent = cfg.pop("extends", None)
    if parent:
        parent_path = Path(parent)
        if not parent_path.is_absolute():
            candidates = [
                path.parent / parent_path,
                path.parent.parent / parent_path,
                Path.cwd() / parent_path,
            ]
            parent_path = next((c for c in candidates if c.exists()), candidates[0])
        base = load_config(parent_path)
        cfg = _deep_merge(base, cfg)
    resolved = path.resolve()
    project_root = resolved.parent.parent if resolved.parent.name == "configs" else resolved.parent
    cfg["_config_path"] = str(resolved)
    cfg["_project_root"] = str(project_root)
    return cfg
