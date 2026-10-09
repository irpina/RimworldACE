"""Write the wage relation's inputs and answers for the C# port (docs/72).

The same shape as ``economy_lab.fixtures``, which does this for the value
solve (docs/53): each fixture is a real economy, stopped at a day, with
everything the wage reads written out in the order the laboratory reads
it, and the answers taken from the laboratory's own calls rather than
re-derived here.

The six readings are pure and are called directly.  ``_settle_labor``
mutates -- it posts to the ledger, pays the wage bill and sets the day's
employment -- so it is called on a deep copy, with the copy's deltas as
the expected answer and the inputs it was given written into the fixture.
Deriving the *inputs* is allowed; deriving the *expected output* is not,
which is what keeps a fixture from being a formula written twice.

    python -m economy_lab.wage_fixtures     # writes rimworld/economy_mod/Source/Fixtures/wages/
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, List

from .model import EPSILON, Economy, Region
from .scenarios import boom_reversal, capital_goods, demand_boom, equilibrium


DEFAULT_DIR = (
    Path(__file__).resolve().parents[1]
    / "rimworld"
    / "economy_mod"
    / "Source"
    / "Fixtures"
    / "wages"
)


def _pairs(mapping: Dict[str, float]) -> List[List[object]]:
    """A mapping as a list of pairs, so JSON keeps the model's order."""
    return [[name, float(value)] for name, value in mapping.items()]


def _finite(value: float) -> object:
    """An infinite labor pool as JSON's null, since JSON has no infinity."""
    return None if value == float("inf") else float(value)


def region_problem(region: Region) -> Dict[str, object]:
    """Everything the wage reads off one region, in the model's order."""
    return {
        "name": region.name,
        "subsistence_basket": _pairs(region.subsistence_basket),
        "prices": _pairs(region.prices),
        "wage_premium": region.wage_premium,
        "habitual_scale": region.habitual_scale,
        "labor_pool": _finite(region.labor_pool),
        "worker_days_earned": region.worker_days_earned,
        "ticks_per_worker_day": region.ticks_per_worker_day,
        "cash": region.cash,
        "worker_cash": region.worker_cash,
    }


def problem(economy: Economy) -> Dict[str, object]:
    """The wage's inputs: the regions, and the social values they read."""
    return {
        "employment_quantum": economy.employment_quantum,
        "commodities": list(economy.commodities),
        "labor_values": _pairs(economy.labor_values),
        "regions": [region_problem(region) for region in economy.regions.values()],
    }


def readings(economy: Economy) -> List[Dict[str, object]]:
    """The six pure readings, from the laboratory's own methods."""
    out = []
    for region in economy.regions.values():
        out.append(
            {
                "region": region.name,
                "basket_cost": region.basket_cost(),
                "wage_rate": region.wage_rate(),
                "basket_labor_value": economy.basket_labor_value(region),
                "value_of_labor_power": economy.value_of_labor_power(region),
                "employment_rate": region.employment_rate(),
                "premium_over_value": region.premium_over_value(),
            }
        )
    return out


def _settlement_inputs(region: Region) -> Dict[str, object]:
    """The day's labor, as `_produce` would hand it to `_settle_labor`.

    Rebuilt from each active producer's realized runs, which is exactly
    what the production step accumulated; the producers are listed in the
    region's own order so the sum compensates in the same sequence.
    """
    entries = []
    for producer in region.producers:
        if not producer.active or producer.last_runs <= EPSILON:
            continue
        entries.append(
            {
                "producer": producer.name,
                "ticks": producer.last_runs * producer.process.direct_labor,
            }
        )
    return {
        "labor_by_producer": entries,
        "labor_performed": sum(entry["ticks"] for entry in entries),
    }


def settlement(economy: Economy, region_name: str) -> Dict[str, object]:
    """What `_settle_labor` does to a copy, given those inputs.

    The copy is what makes this read-only: the routine pays a wage bill and
    posts four ledger entries, and the fixture is the difference it made.
    """
    inputs = _settlement_inputs(economy.regions[region_name])
    clone = copy.deepcopy(economy)
    region = clone.regions[region_name]
    active = [
        p for p in region.producers if p.active and p.last_runs > EPSILON
    ]
    labor_by_producer = {
        id(p): p.last_runs * p.process.direct_labor for p in active
    }
    before = {
        "wages_paid": clone.ledger.wages_paid.get(region_name, 0.0),
        "living_labor": clone.ledger.living_labor.get(region_name, 0.0),
        "necessary_labor": clone.ledger.necessary_labor.get(region_name, 0.0),
        "wage_premium_paid": clone.ledger.wage_premium_paid.get(region_name, 0.0),
        "wage_deviation_labor": clone.ledger.wage_deviation_labor.get(region_name, 0.0),
        "cash": region.cash,
        "worker_cash": region.worker_cash,
    }
    clone._settle_labor(
        region, active, labor_by_producer, inputs["labor_performed"]
    )
    after = {
        "wages_paid": clone.ledger.wages_paid.get(region_name, 0.0),
        "living_labor": clone.ledger.living_labor.get(region_name, 0.0),
        "necessary_labor": clone.ledger.necessary_labor.get(region_name, 0.0),
        "wage_premium_paid": clone.ledger.wage_premium_paid.get(region_name, 0.0),
        "wage_deviation_labor": clone.ledger.wage_deviation_labor.get(region_name, 0.0),
        "cash": region.cash,
        "worker_cash": region.worker_cash,
    }
    return {
        "region": region_name,
        "inputs": inputs,
        "worker_days_earned": region.worker_days_earned,
        # Absolute, not a difference.  `Ledger.add` accumulates onto a
        # running total and the two purses are subtracted from and added
        # to, so what the day posts depends on what was already there: the
        # same wage bill lands on a different last bit against a larger
        # base.  A fixture of differences would hide that and the port
        # would pass it while disagreeing with the model.
        "before": {key: before[key] for key in sorted(before)},
        "after": {key: after[key] for key in sorted(after)},
    }


def fixture(name: str, economy: Economy) -> Dict[str, object]:
    return {
        "name": name,
        "day": economy.day,
        "problem": problem(economy),
        "readings": readings(economy),
        "settlements": [
            settlement(economy, region) for region in economy.regions
        ],
    }


def build_all() -> Dict[str, Dict[str, object]]:
    """Four economies, chosen so every branch in docs/72 s2 is taken.

    `equilibrium` and `capital_goods` take both skips -- no premium and no
    standard -- and differ in how many terms the basket sums over.
    `demand_boom` with bargaining puts a premium in force in one region
    and not the other.  `boom_reversal` with habituation moves the
    standard and leaves the premium *negative*, which is the second arm of
    the deviation branch and the wage below value.
    """
    return {
        "equilibrium_day60": fixture("equilibrium_day60", equilibrium(days=60)),
        "capital_goods_day60": fixture("capital_goods_day60", capital_goods(days=60)),
        "wage_deviation_day180": fixture(
            "wage_deviation_day180", demand_boom(120, bargaining=True)
        ),
        "habituation_day240": fixture(
            "habituation_day240", boom_reversal(180, habituation=True)
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
    from .interpreter import require_compensated_sum

    require_compensated_sum()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    for path in write_all(args.out):
        print(path)


if __name__ == "__main__":
    main()
