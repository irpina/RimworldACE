"""Write the full-state fixtures the C# port reads (docs/141 §4).

    python -m economy_lab.state_fixtures

Each is a docked economy (``wright_battery.DOCKED``) at a small size,
encoded by ``state_codec``: on the day it is built, after one day, and
after forty, on two regions; and after thirty on three, so that more than
one route exists.  ``tests/test_port_fixtures.py`` fails when the
committed files are not what the laboratory writes today.
"""
from __future__ import annotations

from pathlib import Path

from .state_codec import dumps
from .wright_battery import DOCKED, build_ours

DIRECTORY = (Path(__file__).resolve().parents[1] / "rimworld" / "economy_mod"
             / "Source" / "Fixtures" / "state")
COMMODITIES = 24

#: (file stem, seed, regions, days)
CASES = (
    ("docked_r2_day0", 0, 2, 0),
    ("docked_r2_day1", 0, 2, 1),
    ("docked_r2_day40", 0, 2, 40),
    ("docked_r3_day30", 5, 3, 30),
)


def build(seed: int, regions: int, days: int):
    economy = build_ours(seed, commodities=COMMODITIES, regions=regions, **DOCKED)
    economy.step(days)
    return economy


def texts():
    """``{file name: text}`` for every case, as the laboratory writes them now."""
    return {f"{stem}.json": dumps(build(seed, regions, days)) + "\n"
            for stem, seed, regions, days in CASES}


def main() -> None:
    from .interpreter import require_compensated_sum

    require_compensated_sum()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, text in texts().items():
        (DIRECTORY / name).write_text(text, encoding="utf-8")
        print(f"wrote {name}: {len(text):,} bytes")


if __name__ == "__main__":
    main()
