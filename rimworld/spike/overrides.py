"""Defs where a human authored a MarketValue despite the formula being able
to compute one. Reports what the override did, and by how much."""
import csv
from defs import DefDb, stat, cost_list, cost_stuff_count
from value_model import Model


def main():
    m = Model()
    rows = []
    for _, dn, el in m.db.defs("ThingDef"):
        authored = stat(el, "MarketValue")
        has_cost = bool(cost_list(el)) or cost_stuff_count(el) > 0
        if authored is None or not has_cost:
            continue
        inputs, labor, computed = m.breakdown(dn)
        rows.append({
            "defName": dn,
            "authored": authored,
            "computed": round(computed, 2),
            "input_value": round(inputs, 2),
            "labor_value": round(labor, 2),
            "multiple": round(authored / computed, 2) if computed else None,
            "stuff_based": cost_stuff_count(el) > 0,
        })

    rows.sort(key=lambda r: -(r["multiple"] or 0))
    with open("out/overrides.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} defs carry an authored MarketValue despite having costs\n")
    hdr = f'{"defName":32}{"authored":>10}{"computed":>10}{"x":>8}  note'
    print(hdr)
    print("-" * (len(hdr) + 12))
    for r in rows:
        note = "stuff-based (fallback 2/unit)" if r["stuff_based"] else ""
        mult = f'{r["multiple"]:.1f}' if r["multiple"] else "inf"
        print(f'{r["defName"]:32}{r["authored"]:>10}{r["computed"]:>10}'
              f'{mult:>8}  {note}')

    ups = [r for r in rows if r["multiple"] and r["multiple"] > 1]
    downs = [r for r in rows if r["multiple"] and r["multiple"] < 1]
    print(f"\nmarked UP:   {len(ups)}")
    print(f"marked DOWN: {len(downs)}")
    print(f"\n-> out/overrides.csv")


if __name__ == "__main__":
    main()
