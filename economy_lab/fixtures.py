"""Write the labor value solve's inputs and answers for the C# port (docs/53).

Each fixture is a real economy, stopped at a day, with everything
``Economy._update_labor_values`` reads written out in the order it reads
it, and the values it then computes from two starting iterates.  The C#
solver is checked against these to the bit.

    python -m economy_lab.fixtures            # writes economy_mod/Source/Fixtures/labor_values/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from .model import EPSILON, Economy
from .scale import synthetic_economy
from .scenarios import capital_goods, equilibrium, technique_change


DEFAULT_DIR = (
    Path(__file__).resolve().parents[1]
    / "economy_mod"
    / "Source"
    / "Fixtures"
    / "labor_values"
)


def _pairs(mapping: Dict[str, float]) -> List[List[object]]:
    """A mapping as a list of pairs, so JSON keeps the model's order."""
    return [[name, float(value)] for name, value in mapping.items()]


def problem(economy: Economy) -> Dict[str, object]:
    """The solve's inputs, exactly as ``_update_labor_values`` sees them."""
    contributors = []
    for region in economy.regions.values():
        for producer in region.producers:
            if not producer.active or producer.last_runs <= EPSILON:
                continue
            process = producer.process
            contributors.append(
                {
                    "region": region.name,
                    "producer": producer.name,
                    "runs": producer.last_runs,
                    "process": {
                        "name": process.name,
                        "outputs": _pairs(process.outputs),
                        "inputs": _pairs(process.inputs),
                        "direct_labor": process.direct_labor,
                        "apportionment": process.apportionment,
                        "capital_labor_per_capacity": process.capital_labor_per_capacity,
                        "capital_bill": _pairs(process.capital_bill),
                        "capital_construction_labor": process.capital_construction_labor,
                        "machines_per_capacity": process.machines_per_capacity,
                    },
                }
            )
    return {
        "tolerance": economy.labor_value_tolerance,
        "max_iterations": economy.labor_value_max_iterations,
        "service_life_days": economy.capital_service_life_days,
        "commodities": [
            [name, commodity.mass_per_unit]
            for name, commodity in economy.commodities.items()
        ],
        "regions": list(economy.regions),
        "contributors": contributors,
    }


def solve_from(economy: Economy, initial: Dict[str, float]) -> Dict[str, object]:
    """What the laboratory computes from a given starting iterate."""
    economy.labor_values = dict(initial)
    economy._update_labor_values()
    return {
        "labor_values": _pairs(economy.labor_values),
        "regional_labor_values": {
            region: _pairs(values)
            for region, values in economy.regional_labor_values.items()
        },
        "stale": sorted(economy.stale_labor_values),
    }


def fixture(name: str, economy: Economy) -> Dict[str, object]:
    converged = dict(economy.labor_values)
    cold = {commodity: 0.0 for commodity in economy.commodities}
    document = {
        "name": name,
        "day": economy.day,
        "problem": problem(economy),
        "cases": [
            {"label": "warm", "initial": _pairs(converged), "expected": solve_from(economy, converged)},
            {"label": "cold", "initial": _pairs(cold), "expected": solve_from(economy, cold)},
        ],
    }
    # Leave the economy as it was found.
    economy.labor_values = converged
    economy._update_labor_values()
    return document


def build_all() -> Dict[str, Dict[str, object]]:
    return {
        "equilibrium_day60": fixture("equilibrium_day60", equilibrium(days=60)),
        "capital_goods_day60": fixture("capital_goods_day60", capital_goods(days=60)),
        "technique_change_day120": fixture(
            "technique_change_day120", technique_change(days_after_entry=60)
        ),
        "scale_647_day3": fixture("scale_647_day3", _scale_economy()),
    }


def _scale_economy() -> Economy:
    economy = synthetic_economy(commodities=647, regions=2, record_history=False)
    economy.step(3)
    return economy


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
