"""Run a deliberate one-at-a-time Stage 0 parameter sensitivity sweep."""

from __future__ import annotations

import argparse
import csv
from dataclasses import fields, replace
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .behavior import collect_behavioral_metrics
from .scenarios import ScenarioParameters


DEFAULT_CSV = Path(__file__).with_name("sensitivity_results.csv")
DEFAULT_RANKING = Path(__file__).with_name("sensitivity_ranking.txt")
PERTURBATION = 0.10
INTEGER_PARAMETERS = {
    "standard_travel_days",
    "loss_travel_days",
    "investment_interval_days",
    "investment_lead_days",
}


def parameter_variants(
    baseline: ScenarioParameters,
) -> Iterable[Tuple[str, str, float, float, ScenarioParameters]]:
    for parameter in fields(baseline):
        name = parameter.name
        original = float(getattr(baseline, name))
        for direction, factor in (("minus", 1.0 - PERTURBATION), ("plus", 1.0 + PERTURBATION)):
            perturbed = original * factor
            if name in INTEGER_PARAMETERS:
                perturbed = float(max(1, round(perturbed)))
            yield (
                name,
                direction,
                original,
                perturbed,
                replace(baseline, **{name: perturbed}),
            )


def run_sweep() -> List[Dict[str, object]]:
    baseline_parameters = ScenarioParameters()
    baseline_outputs = collect_behavioral_metrics(baseline_parameters)
    rows: List[Dict[str, object]] = []

    for name, direction, original, perturbed, parameters in parameter_variants(
        baseline_parameters
    ):
        outputs = collect_behavioral_metrics(parameters)
        input_change = (perturbed - original) / original
        for metric_name in sorted(baseline_outputs):
            baseline_metric = baseline_outputs[metric_name]
            current_metric = outputs[metric_name]
            baseline_value = float(baseline_metric["value"])
            current_value = float(current_metric["value"])
            delta = current_value - baseline_value
            if baseline_value == 0:
                relative_delta = None
                normalized_change = abs(delta) / baseline_parameters.reference_price
            else:
                relative_delta = delta / abs(baseline_value)
                normalized_change = abs(relative_delta)
            elasticity = (
                normalized_change / abs(input_change) if input_change else 0.0
            )
            rows.append(
                {
                    "parameter": name,
                    "direction": direction,
                    "baseline_parameter": original,
                    "perturbed_parameter": perturbed,
                    "actual_parameter_change_pct": input_change * 100.0,
                    "metric": metric_name,
                    "unit": baseline_metric["unit"],
                    "baseline_output": baseline_value,
                    "perturbed_output": current_value,
                    "absolute_delta": delta,
                    "relative_delta_pct": (
                        "" if relative_delta is None else relative_delta * 100.0
                    ),
                    "normalized_output_change": normalized_change,
                    "elasticity": elasticity,
                }
            )
    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def parameter_ranking(
    rows: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    strongest: Dict[str, Dict[str, object]] = {}
    for row in rows:
        current = strongest.get(str(row["parameter"]))
        if current is None or float(row["elasticity"]) > float(current["elasticity"]):
            strongest[str(row["parameter"])] = row
    return sorted(
        strongest.values(),
        key=lambda row: (-float(row["elasticity"]), str(row["parameter"])),
    )


def ranking_text(rows: List[Dict[str, object]]) -> str:
    ranking = parameter_ranking(rows)
    lines = [
        "Stage 0 one-at-a-time parameter sensitivity (nominally +/-10%)",
        "",
        "Score is the largest normalized output response divided by the actual",
        "input change. Nonzero outputs use proportional change. The equilibrium",
        "price-range baselines are zero, so their absolute movement is normalized",
        "to the 21-silver reference price. Integer day parameters are rounded and",
        "their actual perturbation is reported in the CSV.",
        "",
        f"{'rank':>4}  {'parameter':38} {'score':>10}  {'direction':9} {'strongest output'}",
        "-" * 112,
    ]
    for index, row in enumerate(ranking, start=1):
        lines.append(
            f"{index:4}  {str(row['parameter']):38} "
            f"{float(row['elasticity']):10.4f}  {str(row['direction']):9} "
            f"{row['metric']} ({float(row['absolute_delta']):+.6f} {row['unit']})"
        )

    inert = [
        str(row["parameter"])
        for row in ranking
        if float(row["elasticity"]) == 0.0
    ]
    lines.extend(
        [
            "",
            "No measured effect on the captured outputs:",
            "  " + (", ".join(inert) if inert else "none"),
            "",
        ]
    )
    return "\n".join(lines)


def write_ranking(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ranking_text(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--ranking", type=Path, default=DEFAULT_RANKING)
    args = parser.parse_args()

    rows = run_sweep()
    write_csv(args.csv, rows)
    write_ranking(args.ranking, rows)
    print(ranking_text(rows), end="")
    print(f"CSV: {args.csv}")
    print(f"Ranking: {args.ranking}")


if __name__ == "__main__":
    main()
