"""Tests for the centralized template registry and render contracts."""

from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.templates import TEMPLATES


def test_all_seven_templates_are_registered() -> None:
    """Verify the long-running template registry contains T1 through T7."""
    assert tuple(sorted(TEMPLATES)) == ("t1", "t2", "t3", "t4", "t5", "t6", "t7")


def test_template_modules_expose_render_contract() -> None:
    """Verify each template exposes a compatible render contract."""
    for config in TEMPLATES.values():
        module = importlib.import_module(config.module)
        assert hasattr(module, "render")
        signature = inspect.signature(module.render)
        assert tuple(signature.parameters)[:2] == ("as_of", "variant")


def test_template_placeholders_raise_not_implemented() -> None:
    """Verify placeholder templates fail explicitly until implementation is added."""
    for config in [item for item in TEMPLATES.values() if item.template_id != "t1"]:
        module = importlib.import_module(config.module)
        try:
            module.render(as_of="2026-01-01")
        except NotImplementedError:
            continue
        raise AssertionError(f"{config.template_id} should raise NotImplementedError while scaffolded")
