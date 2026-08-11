"""Statistics on primitive prices vs extraction labor.

Correlations implemented inline - no new dependencies.
"""
import csv
import math

LABOR_COEFF = 0.0036
TICKS_PER_HOUR = 2500.0


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def rank(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    return pearson(rank(xs), rank(ys))


def main():
    with open("out/primitives.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["ticks"] = float(r["ticks_per_unit"])
        r["mv"] = float(r["market_value"])
        r["rate"] = r["mv"] / r["ticks"]          # silver per labor tick
        r["ratio"] = r["rate"] / LABOR_COEFF      # vs the game's own labor price

    lx = [math.log(r["ticks"]) for r in rows]
    ly = [math.log(r["mv"]) for r in rows]

    print(f"n = {len(rows)} extractable primitives with authored MarketValue\n")
    print("Correlation of extraction labor with authored price")
    print(f"  Pearson  (log labor, log price): {pearson(lx, ly):+.3f}")
    print(f"  Spearman (rank)                : {spearman(lx, ly):+.3f}")
    print(f"  Pearson  (raw labor, raw price): "
          f"{pearson([r['ticks'] for r in rows], [r['mv'] for r in rows]):+.3f}")

    rates = sorted(r["ratio"] for r in rows)
    med = rates[len(rates) // 2]
    print(f"\nPrice per unit of extraction labor, as a multiple of the game's")
    print(f"own manufacturing labor price (0.0036 silver/tick):")
    print(f"  median {med:.1f}x   min {rates[0]:.1f}x   max {rates[-1]:.1f}x"
          f"   spread {rates[-1] / rates[0]:.0f}x")

    print("\n--- identical labor, different price: the mineral test ---")
    minerals = [r for r in rows if r["method"] == "mine"]
    for r in sorted(minerals, key=lambda r: -r["mv"]):
        print(f'  {r["product"]:20} {r["ticks"]:8.1f} ticks/unit'
              f'   MV {r["mv"]:>6}   rate {r["ratio"]:6.1f}x')

    print("\n--- priced ABOVE the labor-consistent rate (rarity premium) ---")
    for r in sorted(rows, key=lambda r: -r["ratio"])[:8]:
        print(f'  {r["product"]:20} {r["ratio"]:6.1f}x   '
              f'({r["method"]}, {r["ticks"]:.0f} ticks/unit, MV {r["mv"]})')

    print("\n--- priced BELOW (labor-cheap relative to price) ---")
    for r in sorted(rows, key=lambda r: r["ratio"])[:8]:
        print(f'  {r["product"]:20} {r["ratio"]:6.1f}x   '
              f'({r["method"]}, {r["ticks"]:.0f} ticks/unit, MV {r["mv"]})')

    # The industrial core the brief called out
    core = ["Steel", "Plasteel", "Uranium", "WoodLog", "Cloth"]
    sel = [r for r in rows if r["product"] in core]
    if sel:
        print("\n--- the industrial staples ---")
        for r in sorted(sel, key=lambda r: -r["ratio"]):
            print(f'  {r["product"]:20} {r["ratio"]:6.1f}x')
        rr = [r["ratio"] for r in sel]
        print(f'  spread within group: {max(rr) / min(rr):.2f}x')

    print(f"\nValue generated per work-hour of extraction (median): "
          f"{med * LABOR_COEFF * TICKS_PER_HOUR:.0f} silver/hr")
    print(f"Value generated per work-hour of manufacturing (fixed): "
          f"{LABOR_COEFF * TICKS_PER_HOUR:.0f} silver/hr")


if __name__ == "__main__":
    main()
