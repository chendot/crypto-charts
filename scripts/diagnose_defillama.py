"""One-off diagnostic for DefiLlama protocol stablecoin fields."""

from __future__ import annotations

import json
from numbers import Number
from typing import Any

import requests


PROTOCOLS_URL = "https://api.llama.fi/protocols"
TARGET_NAMES = ("Aave V3", "Curve", "MakerDAO")


def main() -> int:
    response = requests.get(PROTOCOLS_URL, timeout=30)
    response.raise_for_status()
    protocols = response.json()
    if not isinstance(protocols, list) or not protocols:
        print("No protocol rows returned")
        return 1

    first = protocols[0]
    print("protocols[0] fields:")
    print(", ".join(sorted(first)) if isinstance(first, dict) else type(first).__name__)

    stable_fields = _stable_fields(protocols)
    print("\nstable-related fields:")
    print(", ".join(stable_fields) if stable_fields else "(none)")
    print("\nstable-related field types and non-empty samples:")
    for field in stable_fields:
        print(f"{field}:")
        samples = [item for item in protocols if isinstance(item, dict) and item.get(field)]
        type_names = sorted({type(item.get(field)).__name__ for item in samples})
        print(f"  types: {', '.join(type_names) if type_names else '(no truthy values)'}")
        for item in samples[:5]:
            print(f"  {item.get('name')} ({item.get('slug')}): {json.dumps(item.get(field), sort_keys=True)[:500]}")

    print("\nselected protocol stable-related fields and numeric values:")
    for target_name in TARGET_NAMES:
        matches = [
            item
            for item in protocols
            if isinstance(item, dict) and target_name.lower() in str(item.get("name", "")).lower()
        ]
        print(f"\n{target_name}:")
        if not matches:
            print("  no partial name match")
            continue
        for item in matches:
            filtered = _filtered_stable_values(item)
            print(f"  {item.get('name')} ({item.get('slug')}):")
            print("  " + json.dumps(filtered, indent=2, sort_keys=True).replace("\n", "\n  "))

    field_name, top_values = _top_stable_field_values(protocols, stable_fields)
    print("\ntop 10 protocols by highest non-zero stable-related field:")
    if not field_name:
        print("  no non-zero numeric stable-related values found")
        return 0
    print(f"selected field: {field_name}")
    for item in top_values[:10]:
        print(f"  {field_name} | {item.get('name')} | {item.get(field_name)}")
    return 0


def _stable_fields(protocols: list[Any]) -> list[str]:
    fields = set()
    for item in protocols:
        if not isinstance(item, dict):
            continue
        fields.update(key for key in item if "stable" in key.lower())
    return sorted(fields)


def _filtered_stable_values(item: dict[str, Any]) -> dict[str, Any]:
    filtered: dict[str, Any] = {
        key: value
        for key, value in item.items()
        if "stable" in key.lower() or _is_numeric(value)
    }
    return filtered


def _top_stable_field_values(protocols: list[Any], stable_fields: list[str]) -> tuple[str | None, list[dict[str, Any]]]:
    best_field = None
    best_max_value = 0.0
    for field in stable_fields:
        numeric_values = [_stable_numeric_value(item.get(field)) for item in protocols if isinstance(item, dict)]
        max_value = max(numeric_values, default=0.0)
        if max_value > best_max_value:
            best_field = field
            best_max_value = max_value

    if best_field is None:
        return None, []
    top_values = [
        item
        for item in protocols
        if isinstance(item, dict) and _stable_numeric_value(item.get(best_field)) > 0
    ]
    top_values.sort(key=lambda item: _stable_numeric_value(item.get(best_field)), reverse=True)
    return best_field, top_values


def _is_numeric(value: object) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def _to_float(value: object) -> float:
    if not _is_numeric(value):
        return 0.0
    return float(value)


def _stable_numeric_value(value: object) -> float:
    if _is_numeric(value):
        return float(value)
    if isinstance(value, dict):
        nested_values = [_stable_numeric_value(nested_value) for nested_value in value.values()]
        return max(nested_values, default=0.0)
    return 0.0


if __name__ == "__main__":
    raise SystemExit(main())
