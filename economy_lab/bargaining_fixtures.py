"""Write the bargaining rules' inputs and answers for the C# port (docs/74).

The third of the port's fixture sets, after ``fixtures`` (the value solve,
docs/53) and ``wage_fixtures`` (the basket and the wage, docs/72).

These two rules are the model's only stateful accumulators outside the
ledger: the premium and the standard are carried day to day by ``+=``, so
a single application proves almost nothing and an error of one ulp
compounds.  Each fixture is therefore a **sequence** -- the laboratory's
own method called step after step on a deep copy, with the state after
every step recorded -- so a port that drifts is caught on the step it
starts drifting rather than at the end.

Employment does not move across a sequence, because nothing else in the
model runs: the steps exercise the accumulation, not a simulated history.
That is deliberate and is what makes the expected values the
laboratory's own and not a re-derivation.

    python -m economy_lab.bargaining_fixtures    # writes .../Fixtures/bargaining/
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Dict, List

from .model import Economy
from .scenarios import ScenarioParameters, boom_reversal, demand_boom, equilibrium, replace


DEFAULT_DIR = (
    Path(__file__).resolve().parents[1]
    / "rimworld"
    / "economy_mod"
    / "Source"
    / "Fixtures"
    / "bargaining"
)

STEPS = 60


def problem(economy: Economy) -> Dict[str, object]:
    """What the two rules read that does not change across the sequence."""
    return {
        "wage_bargaining_strength": economy.wage_bargaining_strength,
        "wage_bargaining_speed": economy.wage_bargaining_speed,
        "habituation_speed": economy.habituation_speed,
        "regions": [
            {
                "name": region.name,
                "has_basket": bool(region.subsistence_basket),
                "employment_rate": region.employment_rate(),
                "reference_employment_rate": region.reference_employment_rate,
                "wage_premium": region.wage_premium,
                "habitual_scale": region.habitual_scale,
            }
            for region in economy.regions.values()
        ],
    }


def sequence(economy: Economy, region_name: str, steps: int = STEPS) -> Dict[str, object]:
    """The laboratory's own `_bargain` and `_habituate`, step after step.

    On a deep copy, so the economy handed in is where it was afterwards.
    The order is the model's: bargaining moves the premium, and
    habituation then reads the premium bargaining just set.
    """
    clone = copy.deepcopy(economy)
    region = clone.regions[region_name]
    steps_out: List[Dict[str, float]] = []
    for _ in range(steps):
        clone._bargain(region)
        clone._habituate(region)
        steps_out.append(
            {
                "wage_premium": region.wage_premium,
                "habitual_scale": region.habitual_scale,
            }
        )
    return {"region": region_name, "steps": steps_out}


def fixture(name: str, economy: Economy) -> Dict[str, object]:
    return {
        "name": name,
        "day": economy.day,
        "steps": STEPS,
        "problem": problem(economy),
        "sequences": [sequence(economy, region) for region in economy.regions],
    }


def _bargaining(parameters: ScenarioParameters) -> ScenarioParameters:
    return replace(
        parameters, wage_bargaining_strength=parameters.bargaining_scenario_strength
    )


def build_all() -> Dict[str, Dict[str, object]]:
    """Three economies, each exercising a different part of the rules.

    `equilibrium_stationary` is the sharpest: docs/46 s2 claims the rule
    is *exactly* stationary where the circuit is, so the premium must stay
    at 0.0 and the standard at 1.0 for every one of sixty steps.  A port
    drifting one ulp a day would show sixty and pass any tolerance.

    `boom_habituating` is here because the first three did not reach
    `_habituate`'s *taken* branch: a sequence freezes employment, so the
    premium converges monotonically and the reversal's premium sits below
    a standard the boom already raised, leaving the gap negative for all
    sixty steps.  Taken mid-boom the premium is above the standard and the
    ratchet actually turns (docs/75 s3).
    """
    stationary = _bargaining(ScenarioParameters())
    return {
        "equilibrium_stationary": fixture(
            "equilibrium_stationary", equilibrium(days=60, parameters=stationary)
        ),
        "boom_bargaining": fixture(
            "boom_bargaining", demand_boom(120, bargaining=True)
        ),
        "boom_habituating": fixture(
            "boom_habituating",
            demand_boom(120, bargaining=True, habituation=True),
        ),
        "boom_reversal_habituating": fixture(
            "boom_reversal_habituating", boom_reversal(180, habituation=True)
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
