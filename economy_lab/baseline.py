"""Compare current Stage 0 behavior with the deliberately frozen reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from .behavior import collect_behavioral_metrics


DEFAULT_REFERENCE = Path(__file__).with_name("behavior_baseline.json")


def reference_document() -> Dict[str, object]:
    return {
        "format_version": 1,
        "description": "Stage 0 behavioral reference; update deliberately.",
        "metrics": collect_behavioral_metrics(),
    }


def write_reference(path: Path) -> None:
    path.write_text(
        json.dumps(reference_document(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def print_delta_table(
    reference: Dict[str, Dict[str, object]],
    current: Dict[str, Dict[str, object]],
) -> None:
    name_width = max(48, *(len(name) for name in set(reference) | set(current)))
    print(
        f"{'metric':{name_width}} {'reference':>12} {'current':>12} "
        f"{'delta':>12} {'delta %':>10}"
    )
    print("-" * (name_width + 62))
    for name in sorted(set(reference) | set(current)):
        if name not in reference:
            print(
                f"{name:{name_width}} {'missing':>12} "
                f"{_number(float(current[name]['value'])):>12}"
            )
            continue
        if name not in current:
            print(
                f"{name:{name_width}} "
                f"{_number(float(reference[name]['value'])):>12} "
                f"{'missing':>12}"
            )
            continue
        expected = float(reference[name]["value"])
        actual = float(current[name]["value"])
        delta = actual - expected
        percent = "n/a" if expected == 0 else f"{delta / abs(expected) * 100:+.3f}%"
        print(
            f"{name:{name_width}} {_number(expected):>12} "
            f"{_number(actual):>12} "
            f"{_number(delta):>12} {percent:>10}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference",
        type=Path,
        default=DEFAULT_REFERENCE,
        help="reference JSON to read or deliberately replace",
    )
    parser.add_argument(
        "--write-reference",
        action="store_true",
        help="replace the reference JSON with current behavior",
    )
    args = parser.parse_args()

    if args.write_reference:
        write_reference(args.reference)
        print(f"Wrote behavioral reference: {args.reference}")
        return

    document = json.loads(args.reference.read_text(encoding="utf-8"))
    print_delta_table(document["metrics"], collect_behavioral_metrics())


if __name__ == "__main__":
    main()
