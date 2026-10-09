"""Whole runs for the C# port: a start state and the state many days on
(docs/141 slice 8).

    python3.12 -m economy_lab.run_fixtures

Each file is gzip-compressed JSON (fixed mtime)::

    {"case": ..., "seed": s, "regions": r, "commodities": c,
     "days": n, "start": state, "end": state}

The port runs ``n`` whole days from ``start`` and must arrive at ``end``
to the bit.  ``battery_r2_day30`` is the docking battery's own size (200
commodities, two regions, 1,600 producers) and doubles as the timing
case for docs/141 prediction 10.  ``seed``, ``regions`` and
``commodities`` are ``build_ours``'s arguments, so the port's generator
(slice 2) can be checked against ``start``.
"""
from __future__ import annotations

import gzip
import io
import json
import time
from pathlib import Path

from .state_codec import encode
from .wright_battery import DOCKED, build_ours

DIRECTORY = (Path(__file__).resolve().parents[1] / "rimworld" / "economy_mod"
             / "Source" / "Fixtures" / "runs")

#: (file stem, seed, regions, commodities, days)
CASES = (
    ("docked_r2_day180", 0, 2, 24, 180),
    ("docked_r3_day120", 5, 3, 24, 120),
    ("docked_c40_r2_day90", 0, 2, 40, 90),
    ("battery_r2_day30", 0, 2, 200, 30),
    # docs/145: the full population, buildable once the stocks scale.
    ("full_r2_day10", 0, 2, 647, 10),
)


def _compress(document) -> bytes:
    text = json.dumps(document, separators=(",", ":"), allow_nan=False)
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0, compresslevel=9) as handle:
        handle.write(text.encode("utf-8"))
    return buffer.getvalue()


def documents(timings=None):
    out = {}
    for stem, seed, regions, commodities, days in CASES:
        economy = build_ours(seed, commodities=commodities, regions=regions, **DOCKED)
        start = encode(economy)
        began = time.perf_counter()
        economy.step(days)
        if timings is not None:
            producers = sum(len(r.producers) for r in economy.regions.values())
            timings[stem] = ((time.perf_counter() - began) / days, producers)
        out[f"{stem}.json.gz"] = _compress(
            {"case": stem, "seed": seed, "regions": regions,
             "commodities": commodities, "days": days, "start": start, "end": encode(economy)})
    return out


def main() -> None:
    from .interpreter import require_compensated_sum

    require_compensated_sum()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    timings = {}
    for name, data in documents(timings).items():
        (DIRECTORY / name).write_bytes(data)
        print(f"wrote {name}: {len(data):,} bytes")
    for stem, (seconds, producers) in timings.items():
        print(f"python, {stem}: {seconds * 1000:.1f} ms a day, {producers} producers")


if __name__ == "__main__":
    main()
