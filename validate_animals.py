"""Validate our animal model against RimWorld's own Animal Economy table.

The fixture in data/ is a dev-mode CSV export (Debug output -> Economy ->
Animal Economy -> copy CSV). It is the game computing, at runtime with every
generated def present, several of the quantities we derive statically. That
makes it a real oracle rather than a self-consistency check.

Note on units: RimWorld's AnimalProductionUtility omits the per-day scaling
that Need_Food actually applies (x1.6). We keep the 1.6 because we convert
nutrition into hay, which carries real nutrition - so our value is compared
against the fixture after dividing it back out.
"""
import csv
import os
import sys

from defs import DefDb
from animals import animal_rows, inject_generated_meat, NUTRITION_PER_DAY

FIXTURE = os.path.join("data", "rimworld_animal_economy.csv")
TOL = 0.02          # 2% - the exported table is rounded for display


def load_fixture():
    out = {}
    with open(FIXTURE, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) < 16 or row[1] in ("", None):
                continue
            name = row[1]
            def num(i):
                try:
                    return float(row[i].replace("$", "").replace(",", ""))
                except (ValueError, IndexError):
                    return None
            out[name] = {
                "hunger_adult": num(3),
                "eaten_yearly": num(4),
                "gestation_each": num(7),
                "body_size": num(11),
                "adult_age_days": num(13),
                "nutrition_to_adult": num(14),
                "adult_meat_amount": num(15),
            }
    return out


def main():
    fx = load_fixture()
    db = DefDb(); inject_generated_meat(db)
    ours = {r["race"]: r for r in animal_rows(db)}

    checks = [
        ("meat amount", lambda o: o["meat_qty"], "adult_meat_amount"),
        ("body size", lambda o: o["body_size"], "body_size"),
        ("nutrition to adult", lambda o: o["nutrition_to_adult"] / NUTRITION_PER_DAY
         if o["nutrition_to_adult"] else None, "nutrition_to_adult"),
    ]

    print(f"fixture rows: {len(fx)}   our animals: {len(ours)}\n")
    failures = []
    for label, get, key in checks:
        n = ok = 0
        worst = (0.0, None)
        for name, exp in fx.items():
            want = exp.get(key)
            o = ours.get(name)
            if o is None or want is None or want <= 0:
                continue
            got = get(o)
            if got is None:
                continue
            n += 1
            rel = abs(got - want) / max(abs(want), 1e-9)
            # MeatAmount/LeatherAmount use toStringStyle Integer, so the
            # exported table is rounded; 3.74 is displayed as "4".
            rounds_equal = (label == "meat amount"
                            and abs(round(got) - want) < 0.51)
            if rel <= TOL or rounds_equal:
                ok += 1
            else:
                failures.append((label, name, got, want, rel))
                if rel > worst[0]:
                    worst = (rel, name)
        pct = (100.0 * ok / n) if n else 0.0
        flag = "OK " if ok == n else "FAIL"
        extra = f"   worst: {worst[1]} ({worst[0]*100:.1f}% off)" if worst[1] else ""
        print(f"  {flag} {label:22} {ok}/{n} within {TOL*100:.0f}%  ({pct:.1f}%){extra}")

    if failures:
        print(f"\n{len(failures)} mismatches:")
        for label, name, got, want, rel in failures[:20]:
            print(f"    {label:20} {name:18} ours={got:10.2f} game={want:10.2f}  {rel*100:5.1f}%")
    else:
        print("\nall checks pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
