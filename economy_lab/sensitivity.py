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


def integer_parameters(baseline: ScenarioParameters) -> set:
    """Fields that must stay whole, read off the dataclass rather than listed.

    This used to be four names typed by hand, and by the time the model had
    grown to 129 parameters it was missing five: `technique_change_day`,
    `cost_competition_day`, `history_every`, `labor_value_max_iterations`
    and `production_price_max_iterations`.  Perturbing those produced a
    float where an int was required, and the sweep reported the resulting
    `TypeError` under the heading "refused to seed" — which reads as a
    finding about the model and was a bug in the harness.

    `bool` is a subclass of `int` in Python and is excluded separately, so
    the check has to run after `excluded_parameters`.
    """
    return {
        parameter.name
        for parameter in fields(baseline)
        if isinstance(getattr(baseline, parameter.name), int)
        and not isinstance(getattr(baseline, parameter.name), bool)
    }


def excluded_parameters(
    baseline: ScenarioParameters,
) -> Dict[str, str]:
    """Parameters a proportional sweep cannot say anything about, and why.

    Reported rather than silently skipped.  A parameter absent from the
    ranking with no explanation reads as "no effect measured", which is a
    different and much stronger claim than "not measurable this way".
    """
    excluded: Dict[str, str] = {}
    for parameter in fields(baseline):
        value = getattr(baseline, parameter.name)
        if isinstance(value, bool):
            excluded[parameter.name] = (
                "regime switch, not a magnitude: a boolean has no +/-10%"
            )
        elif float(value) == 0.0:
            excluded[parameter.name] = (
                "zero at baseline, so a proportional perturbation is zero"
            )
    return excluded


def parameter_variants(
    baseline: ScenarioParameters,
) -> Iterable[Tuple[str, str, float, float, ScenarioParameters]]:
    skip = excluded_parameters(baseline)
    whole = integer_parameters(baseline)
    for parameter in fields(baseline):
        name = parameter.name
        if name in skip:
            continue
        original = float(getattr(baseline, name))
        for direction, factor in (("minus", 1.0 - PERTURBATION), ("plus", 1.0 + PERTURBATION)):
            perturbed = original * factor
            if name in whole:
                perturbed = float(max(1, round(perturbed)))
            value = int(perturbed) if name in whole else perturbed
            yield (
                name,
                direction,
                original,
                perturbed,
                replace(baseline, **{name: value}),
            )


def run_sweep() -> List[Dict[str, object]]:
    baseline_parameters = ScenarioParameters()
    baseline_outputs = collect_behavioral_metrics(baseline_parameters)
    rows: List[Dict[str, object]] = []

    for name, direction, original, perturbed, parameters in parameter_variants(
        baseline_parameters
    ):
        input_change = (perturbed - original) / original
        try:
            outputs = collect_behavioral_metrics(parameters)
        except Exception as failure:  # noqa: BLE001
            # A perturbation the circuit refuses is a *result*, not a crash.
            # docs/17 section 7 engineered several of these deliberately:
            # `meals_per_worker_day` and `meal_capacity_per_day` are part of
            # the exact-stationarity calibration, and moving them by a tenth
            # is meant to break the seeding rather than to be absorbed.  The
            # sweep reports which parameters refuse and what they said.
            rows.append(
                {
                    "parameter": name,
                    "direction": direction,
                    "baseline_parameter": original,
                    "perturbed_parameter": perturbed,
                    "actual_parameter_change_pct": input_change * 100.0,
                    "metric": "REFUSED",
                    "unit": type(failure).__name__,
                    "baseline_output": "",
                    "perturbed_output": "",
                    "absolute_delta": "",
                    "relative_delta_pct": "",
                    "normalized_output_change": "",
                    "elasticity": "",
                    "note": str(failure)[:300],
                }
            )
            continue
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
                    "note": "",
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
        if row["metric"] == "REFUSED":
            continue
        current = strongest.get(str(row["parameter"]))
        if current is None or float(row["elasticity"]) > float(current["elasticity"]):
            strongest[str(row["parameter"])] = row
    return sorted(
        strongest.values(),
        key=lambda row: (-float(row["elasticity"]), str(row["parameter"])),
    )


def parameter_reach(rows: List[Dict[str, object]]) -> Dict[str, int]:
    """How many metric readings a parameter moves at all.

    The primary ranking, and the reason is that the elasticity is not one.
    An elasticity divides by the metric's baseline, so a metric whose
    baseline happens to sit near zero turns any absolute movement into a
    huge number: `glut.local.employment_trough` has a baseline of 0.000412
    worker-days, and a move of 0.017 scores 418. That put `daily_demand` and
    `producer_capacity_per_day` at the top of the ranking on an artifact of
    the denominator, and filled the next fifteen places with event *timings*
    -- trough and peak day indices -- which are step functions of the
    parameters and jump by a hundred days at a time.

    Reach cannot be gamed by one denominator. It answers "does this
    parameter matter anywhere", which is what a screening sweep is for, and
    the ordering it produces is legible: the working day first, then the
    subsistence basket, then the techniques of the wage goods. That is what
    a model whose central quantity is the value of labor-power ought to say.

    The elasticity is kept beside it, because where the baseline is a real
    magnitude it is the more informative number.
    """
    reach: Dict[str, int] = {}
    for row in rows:
        if row["metric"] == "REFUSED":
            continue
        if abs(float(row["normalized_output_change"])) > 1e-9:
            name = str(row["parameter"])
            reach[name] = reach.get(name, 0) + 1
    return reach


def refusals(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Perturbations the circuit refused to seed, in parameter order."""
    return sorted(
        (row for row in rows if row["metric"] == "REFUSED"),
        key=lambda row: (str(row["parameter"]), str(row["direction"])),
    )


def ranking_text(rows: List[Dict[str, object]]) -> str:
    ranking = parameter_ranking(rows)
    reach = parameter_reach(rows)
    readings = len({str(row["metric"]) for row in rows if row["metric"] != "REFUSED"}) * 2
    lines = [
        "Stage 0 one-at-a-time parameter sensitivity (nominally +/-10%)",
        "",
        "Ranked by REACH: how many of the metric readings a parameter moves at",
        f"all, out of {readings} (every metric, both directions). Reach is the",
        "primary score because the elasticity beside it is not trustworthy as a",
        "ranking: it divides by the metric's baseline, and a metric whose",
        "baseline sits near zero turns any absolute movement into a huge number.",
        "glut.local.employment_trough has a baseline of 0.000412 worker-days, so",
        "a move of 0.017 scores 418 -- which is what put daily_demand and",
        "producer_capacity_per_day on top of the old ranking, and filled the next",
        "fifteen places with peak and trough DAY INDICES, which are step",
        "functions that jump a hundred days at a time.",
        "",
        "Elasticity is still reported, because where the baseline is a real",
        "magnitude it is the more informative number. Integer parameters are",
        "rounded and their actual perturbation is in the CSV.",
        "",
        f"{'rank':>4}  {'parameter':38} {'reach':>7} {'elasticity':>12}  {'strongest output'}",
        "-" * 120,
    ]
    ordered = sorted(
        ranking,
        key=lambda row: (
            -reach.get(str(row["parameter"]), 0),
            -float(row["elasticity"]),
            str(row["parameter"]),
        ),
    )
    for index, row in enumerate(ordered, start=1):
        name = str(row["parameter"])
        lines.append(
            f"{index:4}  {name:38} "
            f"{reach.get(name, 0):7} {float(row['elasticity']):12.4f}  "
            f"{row['metric']} ({float(row['absolute_delta']):+.6f} {row['unit']})"
        )

    inert = [
        str(row["parameter"])
        for row in ranking
        if reach.get(str(row["parameter"]), 0) == 0
    ]
    lines.extend(
        [
            "",
            "No measured effect on the captured outputs:",
            "  " + (", ".join(inert) if inert else "none"),
        ]
    )

    refused = refusals(rows)
    lines.extend(["", "Refused to seed (a result, not a crash):"])
    if refused:
        for row in refused:
            lines.append(
                f"  {str(row['parameter'])} {str(row['direction'])}: "
                f"{row['unit']}"
            )
            lines.append(f"      {row['note']}")
    else:
        lines.append("  none")

    lines.extend(["", "Not swept, and why:"])
    for name, reason in sorted(
        excluded_parameters(ScenarioParameters()).items()
    ):
        lines.append(f"  {name:32} {reason}")
    lines.extend(
        [
            "",
            "Scale metrics read out/embodied_labor.csv rather than a scenario,",
            "so they are parameter-independent by construction.  Their zeros",
            "in this sweep are structural and are not evidence about any",
            "parameter.",
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
