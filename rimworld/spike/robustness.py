"""Robustness checks on the two-rate result.

Three questions, each raised because the headline as first reported could be
an artifact:

1. The 0-20%-fabrication bucket showed a median implied rate of 344.8/hr
   against a fitted extraction coefficient of 94.8/hr. Those should agree.
   Does excluding animal products reconcile them?
2. The main fit is OLS in levels, so R^2 is dominated by expensive goods and
   the coefficients are estimated off large-absolute-value items. Does 14x
   survive a fit that weights relative rather than absolute error?
3. Plant harvest labor is the one input never checked against the game. How
   far does the extraction coefficient move if it is wrong?
"""
import math

from solver import Graph, INF
from value_model import Model
from rate_test import fit_single, fit_two, r2, TICKS_PER_HOUR


def build(scale_harvest=1.0):
    """Solve and return per-def rows. scale_harvest perturbs plant labor."""
    import primitives
    orig = primitives.plant_rows

    def scaled(db, things):
        rows = orig(db, things)
        for r in rows:
            r["ticks_per_unit"] *= scale_harvest
        return rows

    if scale_harvest != 1.0:
        primitives.plant_rows = scaled
        import solver as _s
        _s.plant_rows = scaled
    try:
        g = Graph()
        g.solve()
        m = Model(g.db)
        rows = []
        for d in g.things:
            v = g.val[d]
            if v == INF or v <= 0:
                continue
            p = m.base_market_value(d)
            if not p or p <= 0:
                continue
            e, f = g.decompose(d)
            o = g.best[d]
            rows.append({
                "def": d, "p": p, "L": v, "E": e, "F": f,
                "husbandry": o.method == "husbandry",
                "cat": (g.things[d].findtext("thingCategories/li") or ""),
            })
        return rows
    finally:
        primitives.plant_rows = orig
        import solver as _s
        _s.plant_rows = orig


def fit_log(rows, lo=1e-5, hi=1.0, rounds=6, steps=60):
    """Minimise sum of squared log-ratios: relative, not absolute, error.

    price = a*E + b*F is not log-linear, so this is a small 2-D search
    rather than a closed form. Coarse-to-fine over a grid; no dependencies.
    """
    def loss(a, b):
        s = 0.0
        for r in rows:
            pred = a * r["E"] + b * r["F"]
            if pred <= 0:
                return float("inf")
            s += (math.log(pred) - math.log(r["p"])) ** 2
        return s

    alo, ahi, blo, bhi = lo, hi, lo, hi
    best = (None, None, float("inf"))
    for _ in range(rounds):
        for i in range(steps):
            a = alo * (ahi / alo) ** (i / (steps - 1))
            for j in range(steps):
                b = blo * (bhi / blo) ** (j / (steps - 1))
                v = loss(a, b)
                if v < best[2]:
                    best = (a, b, v)
        a, b, _ = best
        alo, ahi = a / 3, a * 3
        blo, bhi = b / 3, b * 3
    return best[0], best[1]


def log_r2(rows, a, b):
    act = [math.log(r["p"]) for r in rows]
    pred = [math.log(a * r["E"] + b * r["F"]) for r in rows]
    return r2(act, pred)


def fit_two_weighted(rows):
    """OLS on price/p = a*(E/p) + b*(F/p): equal relative weight per good."""
    see = sum((r["E"] / r["p"]) ** 2 for r in rows)
    sff = sum((r["F"] / r["p"]) ** 2 for r in rows)
    sef = sum((r["E"] / r["p"]) * (r["F"] / r["p"]) for r in rows)
    sep = sum(r["E"] / r["p"] for r in rows)
    sfp = sum(r["F"] / r["p"] for r in rows)
    det = see * sff - sef * sef
    if abs(det) < 1e-18:
        return float("nan"), float("nan")
    return ((sep * sff - sfp * sef) / det, (sfp * see - sep * sef) / det)


def buckets(rows, label):
    print(f"\n  {label}")
    out = {}
    for r in rows:
        share = r["F"] / r["L"] if r["L"] else 0.0
        out.setdefault(min(4, int(share * 5)), []).append(r["p"] / r["L"])
    names = ["0-20% fab", "20-40%", "40-60%", "60-80%", "80-100% fab"]
    for k in sorted(out):
        v = sorted(out[k])
        med = v[len(v) // 2]
        print(f"    {names[k]:14} n={len(v):4}  {med * TICKS_PER_HOUR:8.1f} /hr")


def main():
    rows = build()
    animals = [r for r in rows if r["husbandry"]]
    clean = [r for r in rows if not r["husbandry"]]
    print(f"n = {len(rows)}   animal products = {len(animals)}   "
          f"rest = {len(clean)}")

    # ---- 1. does excluding animal products reconcile the bucket table? ----
    print("\n=== 1. MEDIAN IMPLIED RATE BY FABRICATION SHARE ===")
    buckets(rows, "all defs (as first reported)")
    buckets(clean, "animal products excluded")

    # ---- 2. does 14x survive a relative-error fit? ----
    print("\n=== 2. ESTIMATOR SENSITIVITY (all defs) ===")
    print(f'  {"estimator":26}{"extraction":>12}{"fabrication":>13}{"a/b":>8}{"R2":>8}')
    for name, rs in (("all defs", rows), ("animals excluded", clean)):
        a, b = fit_two(rs)
        R = r2([x["p"] for x in rs], [a * x["E"] + b * x["F"] for x in rs])
        print(f'  {"OLS levels  (" + name + ")":26}{a*TICKS_PER_HOUR:>12.1f}'
              f'{b*TICKS_PER_HOUR:>13.1f}{a/b:>8.1f}{R:>8.3f}')
        aw, bw = fit_two_weighted(rs)
        print(f'  {"OLS relative(" + name + ")":26}{aw*TICKS_PER_HOUR:>12.1f}'
              f'{bw*TICKS_PER_HOUR:>13.1f}{aw/bw:>8.1f}{"":>8}')
        al, bl = fit_log(rs)
        print(f'  {"log-space   (" + name + ")":26}{al*TICKS_PER_HOUR:>12.1f}'
              f'{bl*TICKS_PER_HOUR:>13.1f}{al/bl:>8.1f}{log_r2(rs, al, bl):>8.3f}')

    # ---- 3. how much does plant harvest labor matter? ----
    print("\n=== 3. PLANT HARVEST LABOR SENSITIVITY ===")
    print(f'  {"harvestWork scaled":22}{"extraction":>12}{"fabrication":>13}{"a/b":>8}{"R2":>8}')
    for s in (0.5, 0.75, 1.0, 1.5, 2.0):
        rs = build(s)
        a, b = fit_two(rs)
        R = r2([x["p"] for x in rs], [a * x["E"] + b * x["F"] for x in rs])
        print(f'  x{s:<21.2f}{a*TICKS_PER_HOUR:>12.1f}{b*TICKS_PER_HOUR:>13.1f}'
              f'{a/b:>8.1f}{R:>8.3f}')


if __name__ == "__main__":
    main()
