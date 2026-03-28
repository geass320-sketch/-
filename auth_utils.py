"""Authentication payload utilities for Jimeng automation."""

from __future__ import annotations

from typing import Any


class AuthPayloadError(ValueError):
    """Raised when auth payload JSON cannot be normalized."""


def normalize_local_storage_payload(raw_payload: Any) -> dict[str, str]:
    """Normalize localStorage payload from multiple JSON formats.

    Supported formats:
    - Flat mapping: {"token": "abc", "uid": 123}
    - Playwright-ish storage state:
      {"origins": [{"origin": "...", "localStorage": [{"name": "k", "value": "v"}]}]}
    """
    if isinstance(raw_payload, dict) and "origins" not in raw_payload:
        return {str(k): str(v) for k, v in raw_payload.items()}

    if isinstance(raw_payload, dict) and isinstance(raw_payload.get("origins"), list):
        out: dict[str, str] = {}
        for origin_obj in raw_payload["origins"]:
            if not isinstance(origin_obj, dict):
                continue
            items = origin_obj.get("localStorage")
            if not isinstance(items, list):
                continue
            for entry in items:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                value = entry.get("value")
                if name is None or value is None:
                    continue
                out[str(name)] = str(value)
        if out:
            return out

    raise AuthPayloadError("Local storage JSON must be a key-value object or a storage_state-like origins payload")
