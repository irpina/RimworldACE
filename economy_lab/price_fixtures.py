"""Write the regional price update's inputs and answers for the port (docs/77).

The fourth of the port's fixture sets.  This is the slice with ``exp`` in
it, which IEEE 754 does not specify to the bit, so these fixtures exist
as much to *measure* the disagreement between CPython's libm and the
runtime's as to check the transliteration.

One call to the laboratory's own ``_update_prices`` per fixture, on a
deep copy, with every region's prices before and after.

    python -m economy_lab.price_fixtures      # writes .../Fixtures/prices/
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, List

from .model import Economy
from .scenarios import (
    equilibrium,
    input_shortage,
    regional_glut,
    technique_change,
)


DEFAULT_DIR = (
    Path(__file__).resolve().parents[1]
    / "rimworld"
    / "economy_mod"
    / "Source"
    / "Fixtures"
    / "prices"
)


def _pairs(mapping: Dict[str, float]) -> List[List[object]]:
    return [[name, float(value)] for name, value in mapping.items()]


def problem(economy: Economy) -> Dict[str, object]:
    """Everything `_update_prices` reads, in the order it reads it."""
    return {
        "competitive_price_intensity": economy.competitive_price_intensity,
        "unmet_demand_price_pressure": economy.unmet_demand_price_pressure,
        "commodities": [
            {
                "name": name,
                "reference_price": commodity.reference_price,
                "target_inventory_days": commodity.target_inventory_days,
                "inventory_price_sensitivity": commodity.inventory_price_sensitivity,
                "minimum_price_factor": commodity.minimum_price_factor,
                "maximum_price_factor": commodity.maximum_price_factor,
                "price_adjustment_speed": commodity.price_adjustment_speed,
            }
            for name, commodity in economy.commodities.items()
        ],
        "regions": [
            {
                "name": region.name,
                "throughput": _pairs(economy._throughput[region.name]),
                "inventory": _pairs(region.inventory),
                "unmet_demand": _pairs(region.unmet_demand),
                "cost_ratio": _pairs(region.cost_ratio),
                "prices": _pairs(region.prices),
            }
            for region in economy.regions.values()
        ],
    }


def expected(economy: Economy) -> List[Dict[str, object]]:
    """The prices the laboratory's own call leaves behind."""
    clone = copy.deepcopy(economy)
    clone._update_prices()
    return [
        {"region": region.name, "prices": _pairs(region.prices)}
        for region in clone.regions.values()
    ]


def fixture(name: str, economy: Economy) -> Dict[str, object]:
    assert not economy.posted_prices, "this slice is the planned rule"
    return {
        "name": name,
        "day": economy.day,
        "problem": problem(economy),
        "expected": expected(economy),
    }


def build_all() -> Dict[str, Dict[str, object]]:
    """Four economies, one call each.

    `equilibrium_day60` is the sharp one: at the seed the pressure is
    exactly zero, so `exp` is called with exactly 0.0 and must return
    exactly 1.0 in any libm.  If the others disagree by an ulp, this one
    still says the *argument* is computed identically (docs/77 s5).
    """
    return {
        "equilibrium_day60": fixture("equilibrium_day60", equilibrium(days=60)),
        "regional_glut_day120": fixture(
            "regional_glut_day120", regional_glut(60)
        ),
        "input_shortage_day90": fixture(
            "input_shortage_day90", input_shortage(30)
        ),
        "technique_change_day120": fixture(
            "technique_change_day120", technique_change(days_after_entry=60)
        ),
    }


def write_all(directory: Path) -> List[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, document in build_all().items():
        path = directory / f"{name}.json"
        path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    for path in write_all(args.out):
        print(path)


if __name__ == "__main__":
    main()
