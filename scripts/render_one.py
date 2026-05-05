"""Render one registered crypto chart template from the command line."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.prefix).resolve() != (PROJECT_ROOT / "venv").resolve():
    try:
        import pandas  # noqa: F401
    except ModuleNotFoundError:
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

from config.templates import TEMPLATES
from templates import render_template


def parse_args() -> argparse.Namespace:
    """Parse command-line options for a single template render."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template_id", choices=sorted(TEMPLATES), help="Template id to render, e.g. t1.")
    parser.add_argument("--as-of", dest="as_of", default=None, help="Cutoff date in YYYY-MM-DD format.")
    parser.add_argument("--variant", default=None, help="Optional template variant.")
    parser.add_argument("--title", default=None, help="Optional manual chart title override.")
    return parser.parse_args()


def main() -> int:
    """Render the selected template and print the output path."""
    args = parse_args()
    output_path = render_template(
        args.template_id,
        as_of=args.as_of,
        variant=args.variant,
        title=args.title,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
