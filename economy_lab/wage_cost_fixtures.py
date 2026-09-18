"""Write the wage-cost refresh's inputs and answers for the port (docs/79).

The fifth and last of the planned model's arithmetic slices.  This is the
wage's only reach into what a producer's output costs, and the first
ported rule that walks the **process graph**: the labor a unit bears is
the process's direct labor apportioned across its joint outputs by mass,
which is the same apportionment the value solve uses and is shared with
it rather than written twice.

One call to the laboratory's own ``_update_wage_costs`` per region, on a
deep copy.

    python -m economy_lab.wage_cost_fixtures   # writes .../Fixtures/wage_costs/
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, List

from .model import Economy, Region
from .scenarios import capital_goods, equilibrium, technique_change


DEFAULT_DIR = (
    Path(__file__).resolve().parents[1]
    / "rimworld"
    / "economy_mod"
    / "Source"
    / "Fixtures"
    / "wage_costs"
)


def _pairs(mapping: Dict[str, float]) -> List[List[object]]:
    return [[name, float(value)] for name, value in mapping.items()]


def _process(process) -> Dict[str, object]:
    """The fields the labor share reads, in the model's order."""
    return {
        "name": process.name,
        "outputs": _pairs(process.outputs),
        "direct_labor": process.direct_labor,
        "apportionment": process.apportionment,
    }


def region_problem(economy: Economy, region: Region) -> Dict[str, object]:
    return {
        "region": region.name,
        "has_basket": bool(region.subsistence_basket),
        "wage_rate": region.wage_rate(),
        "ticks_per_worker_day": region.ticks_per_worker_day,
        "commodity_mass": [
            [name, commodity.mass_per_unit]
            for name, commodity in economy.commodities.items()
        ],
        "producers": [
            {
                "name": producer.name,
                "commodity": producer.commodity,
                "active": producer.active,
                "process": _process(producer.process),
                "wage_cost_per_unit": producer.wage_cost_per_unit,
            }
            for producer in region.producers
        ],
    }


def expected(economy: Economy, region_name: str) -> Dict[str, object]:
    """What the laboratory's own call leaves on each producer."""
    clone = copy.deepcopy(economy)
    region = clone.regions[region_name]
    clone._update_wage_costs(region)
    return {
        "region": region_name,
        "wage_cost_per_unit": [
            [producer.name, producer.wage_cost_per_unit]
            for producer in region.producers
        ],
    }


def fixture(name: str, economy: Economy) -> Dict[str, object]:
    return {
        "name": name,
        "day": economy.day,
        "problem": {
            "regions": [
                region_problem(economy, region)
                for region in economy.regions.values()
            ]
        },
        "expected": [expected(economy, name_) for name_ in economy.regions],
    }


def build_all() -> Dict[str, Dict[str, object]]:
    """Three economies.

    `capital_goods_day60` is the one that matters for the apportionment:
    nine commodities, and Department I's processes carry joint outputs
    whose masses differ, so `share_of_cost` returns something other than
    1.0 and the labor per unit is not simply `direct_labor / units`.
    """
    return {
        "equilibrium_day60": fixture("equilibrium_day60", equilibrium(days=60)),
        "capital_goods_day60": fixture("capital_goods_day60", capital_goods(days=60)),
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
