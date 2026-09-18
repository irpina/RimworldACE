"""Build economies of arbitrary size, and measure what they cost.

Not an economics feature: an instrument for the question `HANDOFF.md` has
carried through three roadmaps. The laboratory is six commodities and two
regions; RimWorld is 653 producible defs and roughly a hundred settlements.

The commodity population is the real one — names, embodied labor and market
values come from `economy_lab/data/embodied_labor.csv`, the closed analysis's solve. The
input *edges* are synthetic but shape-preserving: the committed data has no
`costList` graph, and the scale question is about shape and size rather than
about which particular def feeds which. See `docs/32-scale-test-design.md`.
"""

from __future__ import annotations

import argparse
import csv
import cProfile
import pstats
import time
import tracemalloc
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .model import Commodity, Economy, Process, Producer, Region, Route


#: The closed analysis's solve (rimworld/spike/solver.py), frozen here so
#: the laboratory owns its own input; the fixtures pin what it produces.
POPULATION = Path(__file__).with_name("data") / "embodied_labor.csv"

#: Fraction of a commodity's reference price that its inputs cost. Chosen so
#: every generated producer is viable at reference prices; RimWorld's own
#: authored prices do not guarantee that (docs/24 found yayo's does not
#: quite cover its inputs), and a circuit where half the sectors refuse to
#: run measures nothing about scale.
INPUT_COST_SHARE = 0.45

#: The operating-overhead convention of docs/13, unchanged: total unit cost
#: is two thirds of the reference price, and the overhead is what is left
#: after inputs.
COST_SHARE_OF_PRICE = 2.0 / 3.0


class _Random:
    """A tiny deterministic PRNG.

    `random.Random` would do, but its stream is a documented-stable
    implementation detail rather than a promise, and this harness's whole
    value rests on reproducibility. Fifteen lines is cheaper than the
    doubt.
    """

    def __init__(self, seed: int = 20260825) -> None:
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next(self) -> int:
        # SplitMix64.
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def below(self, limit: int) -> int:
        return self.next() % max(limit, 1)


def population(limit: Optional[int] = None) -> List[dict]:
    """The real def population, or an evenly spaced sample of it.

    Sorted by name so the order does not depend on the file, then sampled
    with a fixed stride so a smaller run keeps the depth mix rather than
    taking every shallow def first.
    """
    with POPULATION.open(encoding="utf-8") as handle:
        rows = [
            {
                "name": row["defName"],
                "depth": int(float(row["depth"])),
                "labor": float(row["embodied_labor"]),
                "price": float(row["market_value"]),
            }
            for row in csv.DictReader(handle)
        ]
    rows = [r for r in rows if r["price"] > 0.0]
    rows.sort(key=lambda row: row["name"])
    if limit is None or limit >= len(rows):
        return rows
    stride = len(rows) / float(limit)
    return [rows[int(index * stride)] for index in range(limit)]


def build_processes(
    rows: Sequence[dict], seed: int = 20260825
) -> Tuple[Dict[str, Process], Dict[str, dict]]:
    """One technology per commodity, wired by depth.

    A commodity at depth *d* draws one to four inputs from depth *d − 1*.
    Quantities are set from the *price* target rather than from labor, so
    every producer is viable; direct labor is then whatever makes the
    commodity's embodied labor come out at the closed analysis's figure.

    Where that residual would be negative — the inputs already carry more
    labor than the def does — it floors at one tick, and the commodity is
    reported in the returned record so the results can say how often the
    synthetic wiring contradicted the real figures.
    """
    random = _Random(seed)
    by_depth: Dict[int, List[dict]] = {}
    for row in rows:
        by_depth.setdefault(row["depth"], []).append(row)
    labor = {row["name"]: row["labor"] for row in rows}
    price = {row["name"]: row["price"] for row in rows}

    processes: Dict[str, Process] = {}
    floored: List[str] = []
    for row in sorted(rows, key=lambda item: (item["depth"], item["name"])):
        name, depth = row["name"], row["depth"]
        pool: List[dict] = []
        for shallower in range(depth):
            pool.extend(by_depth.get(shallower, []))
        inputs: Dict[str, float] = {}
        if pool:
            count = 1 + random.below(4)
            budget = INPUT_COST_SHARE * price[name] / float(count)
            for _ in range(count):
                other = pool[random.below(len(pool))]["name"]
                if other == name:
                    continue
                quantity = budget / max(price[other], 1e-9)
                inputs[other] = inputs.get(other, 0.0) + quantity
        carried = sum(
            quantity * labor[other] for other, quantity in inputs.items()
        )
        direct = labor[name] - carried
        if direct < 1.0:
            direct = 1.0
            floored.append(name)
        processes[name] = Process(
            f"{name} production",
            outputs={name: 1.0},
            inputs=inputs,
            direct_labor=direct,
        )
    return processes, {
        "floored": floored,
        "labor": labor,
        "price": price,
    }


def _required_output(
    rows: Sequence[dict],
    processes: Dict[str, Process],
    final_demand: Dict[str, float],
) -> Dict[str, float]:
    """Output each sector must make, cascading demand down the depths.

    The graph is a DAG ordered by depth, so one pass from the deepest
    commodity to the shallowest is exact — no fixed point needed here.
    """
    required = {row["name"]: final_demand.get(row["name"], 0.0) for row in rows}
    for row in sorted(rows, key=lambda item: -item["depth"]):
        name = row["name"]
        runs = required[name]
        if runs <= 0.0:
            continue
        for other, quantity in processes[name].inputs.items():
            required[other] = required.get(other, 0.0) + runs * quantity
    return required


def _required_with_basket(
    rows: Sequence[dict],
    processes: Dict[str, Process],
    final_demand: Dict[str, float],
    staple: str,
    basket_quantity: float,
    ticks_per_worker_day: float,
    *,
    tolerance: float = 1e-6,
    max_iterations: int = 200,
) -> Tuple[Dict[str, float], int]:
    """The requirement cascade with the workforce's basket in the demand
    (docs/128).  The staple's own labor adds workers who need more
    staple, a geometric series whose ratio is the basket's share of the
    working day, so it converges whenever labor-power can be reproduced
    at all.  Returns the requirement and the iterations it took."""
    required = _required_output(rows, processes, final_demand)
    for iteration in range(1, max_iterations + 1):
        workers = sum(
            required[name] * processes[name].direct_labor
            for name in required
        ) / ticks_per_worker_day
        demand = dict(final_demand)
        demand[staple] = demand.get(staple, 0.0) + workers * basket_quantity
        previous = required[staple]
        required = _required_output(rows, processes, demand)
        if abs(required[staple] - previous) <= tolerance * max(previous, 1.0):
            break
    else:
        raise RuntimeError("basket_in_demand did not converge")
    return required, iteration


def synthetic_economy(
    *,
    commodities: int = 653,
    regions: int = 2,
    neighbours: int = 3,
    daily_demand: float = 1.0,
    basket_fraction: float = 0.02,
    capacity_headroom: float = 1.25,
    target_inventory_days: float = 20.0,
    record_history: bool = True,
    seed: int = 20260825,
    basket_in_demand: bool = False,
    producers_per_commodity: int = 1,
    cost_spread: float = 0.1,
) -> Economy:
    """A running economy of the requested size.

    Deliberately does *not* promise an exactly stationary equilibrium: that
    rests on a hand-tuned six-commodity calibration (docs/17 section 7) and
    forcing it here would make this a calibration exercise. What it promises
    is a circuit that runs, closes its ledgers, and reproduces itself given
    the same seed.

    Fixed capital is omitted — it is exogenous data the generator has no
    source for, and it is not what is being measured.

    ``basket_in_demand`` (docs/128) sizes the staple sector to feed the
    workforce the rest of the economy employs, as a fixed point over the
    requirement cascade.  Off, the workers' consumption is not in the
    demand the sectors are sized to, and at any scale where the workforce
    is large against the graph's own use of the staple the staple runs
    short and the wage, which is its price, spirals.  Off by default:
    ``fixtures.py`` pins this generator's output.

    ``producers_per_commodity`` (docs/130) splits each commodity's
    capacity equally among that many producers, whose overheads are
    spread by ``cost_spread`` from a stream separate from the one that
    builds the processes, so that one producer per commodity draws
    nothing it did not draw before.
    """
    rows = population(commodities)
    processes, record = build_processes(rows, seed=seed)
    names = [row["name"] for row in rows]

    goods = [
        Commodity(
            row["name"],
            reference_price=row["price"],
            labor_value=row["labor"],
            target_inventory_days=target_inventory_days,
        )
        for row in rows
    ]

    # Final demand goes to the deepest commodities: those are what the
    # circuit exists to make, and everything upstream is pulled by them.
    deepest = max(row["depth"] for row in rows)
    finals = [row["name"] for row in rows if row["depth"] == deepest]
    if not finals:
        finals = names[-1:]
    final_demand = {name: daily_demand for name in finals}
    required = _required_output(rows, processes, final_demand)

    # A subsistence basket of one cheap, shallow commodity, sized so
    # necessary labor is a small share of the working day — the wage circuit
    # is part of the daily cost being measured, so it has to be present.
    shallow = [row for row in rows if row["depth"] == 0] or rows
    staple = min(shallow, key=lambda row: (row["price"], row["name"]))["name"]
    ticks_per_worker_day = 24_000.0
    basket_quantity = max(
        basket_fraction
        * ticks_per_worker_day
        / max(record["labor"][staple], 1.0),
        1e-6,
    )
    if basket_in_demand:
        required, record["basket_iterations"] = _required_with_basket(
            rows, processes, final_demand, staple, basket_quantity,
            ticks_per_worker_day,
        )

    if producers_per_commodity < 1:
        raise ValueError("producers_per_commodity must be at least 1")
    firms = producers_per_commodity
    spread = _Random(seed + 1) if firms > 1 else None

    region_names = [f"region_{index:03d}" for index in range(regions)]
    built: List[Region] = []
    for index, region_name in enumerate(region_names):
        jitter = 1.0 + 0.01 * ((index % 5) - 2)
        producers = []
        for row in rows:
            name = row["name"]
            process = processes[name]
            capacity = max(required.get(name, 0.0) * capacity_headroom, 1e-6)
            reference_inputs = sum(
                quantity * record["price"][other]
                for other, quantity in process.inputs.items()
            )
            overhead = max(
                0.0,
                COST_SHARE_OF_PRICE * record["price"][name] * jitter
                - reference_inputs,
            )
            if spread is None:
                producers.append(
                    Producer(
                        f"{region_name}:{name}",
                        name,
                        capacity,
                        overhead,
                        process=process,
                    )
                )
                continue
            for firm in range(firms):
                unit = spread.next() / 2.0 ** 64
                producers.append(
                    Producer(
                        f"{region_name}:{name}#{firm}",
                        name,
                        capacity / firms,
                        overhead * (1.0 + cost_spread * (unit - 0.5)),
                        process=process,
                    )
                )
        region = Region(
            region_name,
            cash=1_000_000.0,
            base_daily_demand=dict(final_demand),
            inventory={},
            prices={row["name"]: row["price"] for row in rows},
            producers=producers,
            subsistence_basket={staple: basket_quantity},
            ticks_per_worker_day=ticks_per_worker_day,
            worker_cash=100_000.0,
        )
        built.append(region)

    routes: List[Route] = []
    for index, region_name in enumerate(region_names):
        for step in range(1, neighbours + 1):
            other = (index + step) % len(region_names)
            if other == index:
                continue
            a, b = sorted((region_name, region_names[other]))
            if any(route.a == a and route.b == b for route in routes):
                continue
            routes.append(
                Route(a, b, freight_per_unit=1.0, capacity_per_day=25.0, travel_days=4)
            )

    for region in built:
        for good in goods:
            region.inventory.setdefault(good.name, 0.0)
        for good in goods:
            region.inventory[good.name] = (
                region.throughput_demand(good.name) * good.target_inventory_days
            )

    economy = Economy(goods, built, routes, record_history=record_history)
    economy.scale_record = record  # type: ignore[attr-defined]
    return economy


# --------------------------------------------------------------- measurement


def history_entries(economy: Economy) -> int:
    """Float-valued slots held in `Economy.history`.

    Counted rather than estimated, because the prediction in docs/32 is
    that this is the whole memory story and an estimate would beg the
    question.
    """
    total = 0
    for snapshot in economy.history:
        if "system_inventory" not in snapshot:
            # A day marker from a sampled or disabled history (docs/34).
            continue
        total += len(snapshot["system_inventory"]) + len(snapshot["labor_values"])
        for values in snapshot["regional_labor_values"].values():
            total += len(values)
        for state in snapshot["regions"].values():
            for key in ("price", "inventory", "unmet", "capacity", "cost_ratio"):
                total += len(state[key])
            total += 4
    return total


def measure(
    *,
    commodities: int,
    regions: int,
    days: int,
    profile: bool = False,
    record_history: bool = True,
) -> Dict[str, object]:
    """Build an economy of the given size and time a run of it."""
    tracemalloc.start()
    started = time.perf_counter()
    economy = synthetic_economy(
        commodities=commodities, regions=regions, record_history=record_history
    )
    construction = time.perf_counter() - started

    profile_text = ""
    started = time.perf_counter()
    if profile:
        profiler = cProfile.Profile()
        profiler.enable()
        economy.step(days)
        profiler.disable()
        stream = StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(18)
        profile_text = stream.getvalue()
    else:
        economy.step(days)
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    residuals = economy.commodity_balances()
    return {
        "commodities": len(economy.commodities),
        "regions": len(economy.regions),
        "producers": sum(len(r.producers) for r in economy.regions.values()),
        "routes": len(economy.routes),
        "construction_seconds": construction,
        "seconds_per_day": elapsed / max(days, 1),
        "peak_mib": peak / (1024.0 * 1024.0),
        "history_entries": history_entries(economy),
        "worst_material_residual": max(
            (abs(value) for value in residuals.values()), default=0.0
        ),
        "cash_residual": abs(economy.cash_balance()),
        "floored_direct_labor": len(economy.scale_record["floored"]),  # type: ignore[attr-defined]
        "profile": profile_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commodities", type=int, default=653)
    parser.add_argument("--regions", type=int, default=2)
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--profile", action="store_true")
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="build with record_history=False, as the runtime would",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="run the size ladder from docs/32 section 5",
    )
    args = parser.parse_args()

    if args.sweep:
        ladder = [(6, 2), (64, 2), (653, 2), (653, 10)]
        print(
            f"{'commodities':>12}{'regions':>9}{'producers':>11}"
            f"{'build s':>10}{'s/day':>10}{'peak MiB':>11}"
            f"{'MiB no hist':>13}{'history':>12}"
        )
        for count, places in ladder:
            full = measure(commodities=count, regions=places, days=args.days)
            bare = measure(
                commodities=count,
                regions=places,
                days=args.days,
                record_history=False,
            )
            print(
                f"{full['commodities']:>12}{full['regions']:>9}"
                f"{full['producers']:>11}"
                f"{full['construction_seconds']:>10.2f}"
                f"{full['seconds_per_day']:>10.3f}"
                f"{full['peak_mib']:>11.1f}"
                f"{bare['peak_mib']:>13.1f}"
                f"{full['history_entries']:>12,}"
            )
        return

    result = measure(
        commodities=args.commodities,
        regions=args.regions,
        days=args.days,
        profile=args.profile,
        record_history=not args.no_history,
    )
    for key in (
        "commodities",
        "regions",
        "producers",
        "routes",
        "construction_seconds",
        "seconds_per_day",
        "peak_mib",
        "history_entries",
        "worst_material_residual",
        "cash_residual",
        "floored_direct_labor",
    ):
        print(f"{key:>26}  {result[key]}")
    if result["profile"]:
        print()
        print(result["profile"])


if __name__ == "__main__":
    main()
