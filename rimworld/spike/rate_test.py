"""Endogenous rate test.

Embodied labor is computed without reference to price (solver.py, seeded at
extraction). So we can now ask the question RimWorld's own formula makes
impossible: what silver-per-tick rate does the price structure actually
imply, and is there one rate or two?

Models, both fitted through the origin:
    single  price = r * L
    two-way price = a * E + b * F        E = extraction-origin labor
                                         F = fabrication-added labor

RimWorld pays a hardcoded 0.0036 silver/tick for fabrication work. If the
authored primitive prices embed a *different* implicit rate, the two-way fit
recovers the gap as a != b. That is the two-regime hypothesis, stated so it
can fail.
"""
import csv
import math
from collections import defaultdict

HARDCODED = 0.0036
TICKS_PER_HOUR = 2500.0


def load():
    rows = []
    for r in csv.DictReader(open("out/embodied_labor.csv", encoding="utf-8")):
        L = float(r["embodied_labor"])
        p = float(r["market_value"] or 0)
        if L <= 0 or p <= 0:
            continue
        r["L"], r["p"] = L, p
        r["E"] = float(r["extraction_labor"])
        r["F"] = float(r["fabrication_labor"])
        rows.append(r)
    return rows


def r2(actual, pred):
    ss_res = sum((a - q) ** 2 for a, q in zip(actual, pred))
    mean = sum(actual) / len(actual)
    ss_tot = sum((a - mean) ** 2 for a in actual)
    return 1 - ss_res / ss_tot if ss_tot else float("nan")


def fit_single(rows):
    num = sum(r["p"] * r["L"] for r in rows)
    den = sum(r["L"] ** 2 for r in rows)
    return num / den


def fit_two(rows):
    see = sum(r["E"] ** 2 for r in rows)
    sff = sum(r["F"] ** 2 for r in rows)
    sef = sum(r["E"] * r["F"] for r in rows)
    sep = sum(r["E"] * r["p"] for r in rows)
    sfp = sum(r["F"] * r["p"] for r in rows)
    det = see * sff - sef * sef
    if abs(det) < 1e-9:
        return float("nan"), float("nan")
    a = (sep * sff - sfp * sef) / det
    b = (sfp * see - sep * sef) / det
    return a, b


def pct(vals, q):
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(q * (len(s) - 1))))
    return s[i]


def main():
    rows = load()
    print(f"n = {len(rows)} defs with both an embodied-labor value and a price\n")

    # ---------------------------------------------------------- single rate
    r = fit_single(rows)
    pred = [r * x["L"] for x in rows]
    print("SINGLE-RATE MODEL   price = r * embodied_labor")
    print(f"  r      = {r:.6f} silver/tick  ({r * TICKS_PER_HOUR:.1f} silver/work-hour)")
    print(f"  R^2    = {r2([x['p'] for x in rows], pred):.3f}")
    print(f"  vs RimWorld's hardcoded fabrication rate {HARDCODED} "
          f"({HARDCODED * TICKS_PER_HOUR:.0f} silver/hr): {r / HARDCODED:.1f}x")

    ratios = [x["p"] / x["L"] for x in rows]
    print(f"\n  per-good implied rate, distribution:")
    for q in (0.05, 0.25, 0.5, 0.75, 0.95):
        v = pct(ratios, q)
        print(f"    p{int(q*100):02d}  {v:.5f} silver/tick  ({v * TICKS_PER_HOUR:7.1f} /hr)")
    print(f"    spread p95/p05 = {pct(ratios,0.95)/pct(ratios,0.05):.0f}x")

    # ------------------------------------------------------------- two rate
    a, b = fit_two(rows)
    pred2 = [a * x["E"] + b * x["F"] for x in rows]
    print("\nTWO-RATE MODEL      price = a*extraction + b*fabrication")
    print(f"  a (extraction)  = {a:.6f} silver/tick  ({a * TICKS_PER_HOUR:.1f} silver/work-hour)")
    print(f"  b (fabrication) = {b:.6f} silver/tick  ({b * TICKS_PER_HOUR:.1f} silver/work-hour)")
    print(f"  R^2             = {r2([x['p'] for x in rows], pred2):.3f}")
    if b > 0:
        print(f"  a/b             = {a/b:.1f}x")
    print(f"  b vs hardcoded 0.0036: {b / HARDCODED:.2f}x")

    # --------------------------------------------- does the rate vary with mix
    print("\nIMPLIED RATE BY FABRICATION SHARE")
    print("  (if one rate governed everything, these rows would be flat)")
    buckets = defaultdict(list)
    for x in rows:
        share = x["F"] / x["L"] if x["L"] else 0
        key = min(4, int(share * 5))
        buckets[key].append(x["p"] / x["L"])
    labels = ["0-20% fab", "20-40%", "40-60%", "60-80%", "80-100% fab"]
    for k in sorted(buckets):
        v = sorted(buckets[k])
        med = v[len(v) // 2]
        print(f"    {labels[k]:14} n={len(v):4}  median {med:.5f} silver/tick"
              f"  ({med * TICKS_PER_HOUR:7.1f} /hr)")

    # ------------------------------------------------------------ by category
    print("\nMEDIAN IMPLIED RATE BY CATEGORY (n >= 8)")
    cats = defaultdict(list)
    for x in rows:
        cats[x["category"] or "(none)"].append(x["p"] / x["L"])
    out = [(c, sorted(v)[len(v) // 2], len(v))
           for c, v in cats.items() if len(v) >= 8]
    for c, med, n in sorted(out, key=lambda t: -t[1]):
        print(f"    {c:24} n={n:4}  {med:.5f}  ({med * TICKS_PER_HOUR:7.1f} /hr)")

    # -------------------------------------------------------------- outliers
    print("\nLARGEST OVERPRICED vs single-rate baseline")
    for x in sorted(rows, key=lambda x: -(x["p"] / x["L"]))[:10]:
        print(f'    {x["defName"]:30} {x["p"]/x["L"]/r:7.1f}x   '
              f'price {x["p"]:>9} labor {x["L"]:>10}')
    print("\nLARGEST UNDERPRICED")
    for x in sorted(rows, key=lambda x: (x["p"] / x["L"]))[:10]:
        print(f'    {x["defName"]:30} {x["p"]/x["L"]/r:7.2f}x   '
              f'price {x["p"]:>9} labor {x["L"]:>10}')


if __name__ == "__main__":
    main()
