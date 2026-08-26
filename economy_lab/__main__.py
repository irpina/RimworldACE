"""Run the initial benchmark scenarios and print compact summaries."""

from __future__ import annotations

import argparse
import json

from .scenarios import (
    arbitrage,
    capacity_exit,
    capital_goods,
    cost_competition,
    equilibrium,
    generous_basket,
    perishable_meals,
    input_shortage,
    producer_loss,
    recreation_basket,
    regional_glut,
    reserve_depletion,
    subsistence_shock,
    summary,
    technique_change,
)


SCENARIOS = {
    "equilibrium": equilibrium,
    "glut": regional_glut,
    "producer-loss": producer_loss,
    "arbitrage": arbitrage,
    "input-shortage": input_shortage,
    "depletion": reserve_depletion,
    "subsistence-shock": subsistence_shock,
    "technique-change": technique_change,
    "cost-competition": cost_competition,
    "generous-basket": generous_basket,
    "perishable-meals": perishable_meals,
    "capital-goods": capital_goods,
    "capacity-exit": capacity_exit,
    "recreation-basket": recreation_basket,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=[*SCENARIOS, "all"], default="all", nargs="?")
    args = parser.parse_args()
    names = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    result = {name: summary(SCENARIOS[name]()) for name in names}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
