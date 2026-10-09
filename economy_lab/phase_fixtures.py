"""Write the per-phase fixtures the C# port is checked against (docs/141 §4).

    python -m economy_lab.phase_fixtures

For each case, one docked day is run with every phase ``Economy.step``
calls wrapped so that the whole state is encoded after it.  The wrapping
is on the real ``step``, so the list of phases and their order are the
model's own and cannot drift from a copy.  A phase called from inside
another phase is not recorded separately: it belongs to its caller.

Each file is gzip-compressed JSON (fixed mtime, so the bytes are
deterministic)::

    {"case": ..., "states": [state, ...], "phases": ["begin", "_migrate", ...]}

``states[0]`` is the economy before the day; ``states[k]`` is the state
after ``phases[k - 1]``.  ``begin`` is the day counter's increment, which
``step`` does before the first phase.  So phase ``k`` maps ``states[k]``
to ``states[k + 1]``.
"""
from __future__ import annotations

import gzip
import io
import json
from pathlib import Path

from . import model
from .state_codec import encode
from .state_fixtures import COMMODITIES
from .wright_battery import DOCKED, build_ours

DIRECTORY = (Path(__file__).resolve().parents[1] / "rimworld" / "economy_mod"
             / "Source" / "Fixtures" / "phases")

#: (file stem, seed, regions, commodities, the day to record).  Chosen so
#: that every phase a docked day runs changes state in some case: day 1 is
#: the first day; on day 61 and day 35 shipments both arrive and leave;
#: on day 30 at 40 commodities producers go bankrupt.
CASES = (
    ("docked_r2_day1", 0, 2, COMMODITIES, 1),
    ("docked_r2_day61", 0, 2, COMMODITIES, 61),
    ("docked_r3_day35", 5, 3, COMMODITIES, 35),
    ("docked_c40_r2_day30", 0, 2, 40, 30),
)

#: Methods ``step`` may call directly, in the order it calls them.
PHASES = (
    "_migrate", "_arrive_shipments", "_complete_projects", "_refresh_throughput",
    "_produce", "_update_labor_values", "_update_cost_ratios",
    "_track_differential_rent", "_final_market", "_consume", "_workers_consume",
    "_update_prices", "_dispatch_arbitrage", "_settle_purses",
    "_update_expectations", "_exit", "_invest",
)


def record_day(economy) -> dict:
    """Run one day of ``economy`` and return every state along the way."""
    states = [encode(economy)]
    phases = []
    depth = [0]
    originals = {name: getattr(model.Economy, name) for name in PHASES}

    def wrap(name, original):
        def wrapper(self, *args, **kwargs):
            if depth[0] == 0 and not phases:
                # The first phase of the day: what precedes it is "begin".
                phases.append("begin")
                states.append(encode(self))
            depth[0] += 1
            try:
                return original(self, *args, **kwargs)
            finally:
                depth[0] -= 1
                if depth[0] == 0:
                    phases.append(name)
                    states.append(encode(self))
        return wrapper

    try:
        for name, original in originals.items():
            setattr(model.Economy, name, wrap(name, original))
        economy.step(1)
    finally:
        for name, original in originals.items():
            setattr(model.Economy, name, original)
    final = encode(economy)
    if final != states[-1]:
        raise RuntimeError("the step changed state after its last recorded phase")
    return {"states": states, "phases": phases}


def build(seed: int, regions: int, commodities: int, day: int):
    economy = build_ours(seed, commodities=commodities, regions=regions, **DOCKED)
    economy.step(day - 1)
    return economy


def documents():
    """``{file name: compressed bytes}`` as the laboratory writes them now."""
    out = {}
    for stem, seed, regions, commodities, day in CASES:
        recorded = record_day(build(seed, regions, commodities, day))
        document = {"case": stem, "phases": recorded["phases"],
                    "states": recorded["states"]}
        text = json.dumps(document, separators=(",", ":"), allow_nan=False)
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, compresslevel=9) as handle:
            handle.write(text.encode("utf-8"))
        out[f"{stem}.json.gz"] = buffer.getvalue()
    return out


def main() -> None:
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, data in documents().items():
        (DIRECTORY / name).write_bytes(data)
        print(f"wrote {name}: {len(data):,} bytes")


if __name__ == "__main__":
    main()
