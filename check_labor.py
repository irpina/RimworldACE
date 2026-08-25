"""Show the arithmetic behind an info card's Labor content rows.

The mod displays two numbers per thing and gives no working. This prints
the working, so a row on the info card can be checked against the recipe
on the same card rather than taken on trust.

    python check_labor.py Gun_BoltActionRifle
    python check_labor.py MeleeWeapon_Knife Plasteel
    python check_labor.py MeleeWeapon_Knife Steel Plasteel WoodLog

With no stuff named, a stuffable thing is shown for every stuff it can be
made from, cheapest first — which is also how you can see that the mod is
no longer reporting one flat number for all of them.
"""
import csv
import sys

from defs import DefDb, cost_list, cost_stuff_count, stat

CSV = "out/embodied_labor.csv"
TICKS_PER_WORK_SECOND = 60.0
TICKS_PER_INGAME_HOUR = 2500.0


def readable(value):
    """The same precision rule the StatWorker uses."""
    if value >= 100:
        return "{:,.0f}".format(value)
    if value >= 10:
        return "{:.1f}".format(value).rstrip("0").rstrip(".")
    if value >= 1:
        return "{:.2f}".format(value).rstrip("0").rstrip(".")
    return "{:.3f}".format(value).rstrip("0").rstrip(".")


def as_card(ticks):
    """Render ticks the way the info card will: at most two units."""
    if ticks <= 0:
        return "0"
    work_seconds = ticks / TICKS_PER_WORK_SECOND
    hours = ticks / TICKS_PER_INGAME_HOUR
    parts = []
    if hours >= 1:
        parts.append(readable(hours) + " in-game h")
    if work_seconds >= 1:
        parts.append(readable(work_seconds) + " work-s")
    if len(parts) < 2:
        parts.append(readable(ticks) + " ticks")
    return " · ".join(parts)


def load():
    rows = {}
    with open(CSV, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows[row["defName"]] = (
                float(row["extraction_labor"]),
                float(row["fabrication_labor"]),
            )
    return rows


def stuff_options(db, element):
    """Every stuff this def can be made from, via its stuff categories."""
    by_category = {}
    for _, name, el in db.defs("ThingDef"):
        if name is None or el is None:
            continue
        props = el.find("stuffProps")
        if props is None:
            continue
        categories = props.find("categories")
        for li in categories if categories is not None else []:
            if li.text:
                by_category.setdefault(li.text.strip(), set()).add(name)
    wanted = set()
    categories = element.find("stuffCategories")
    for li in categories if categories is not None else []:
        if li.text:
            wanted |= by_category.get(li.text.strip(), set())
    return wanted


def work_factor(db_elements, stuff, work_stat):
    element = db_elements.get(stuff)
    if element is None or work_stat is None:
        return 1.0
    props = element.find("stuffProps")
    if props is None:
        return 1.0
    factors = props.find("statFactors")
    for child in factors if factors is not None else []:
        if child.tag == work_stat and child.text:
            return float(child.text)
    return 1.0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    target = sys.argv[1]
    chosen = sys.argv[2:]

    labor = load()
    if target not in labor:
        print("not in the solve: " + target)
        return
    db = DefDb()
    elements = {}
    for _, name, el in db.defs("ThingDef"):
        if name is not None and el is not None:
            elements.setdefault(name, el)
    element = elements.get(target)
    if element is None:
        print("no XML def for " + target)
        return

    extraction, fabrication = labor[target]
    count = cost_stuff_count(element)
    ingredients = cost_list(element)
    work_stat = (
        "WorkToMake" if stat(element, "WorkToMake") else
        "WorkToBuild" if stat(element, "WorkToBuild") else None
    )

    print("=" * 66)
    print(target)
    print("=" * 66)

    if ingredients:
        print("\nfixed ingredients (their extraction + their fabrication):")
        ext_sum = fab_sum = 0.0
        for name, quantity in ingredients:
            ing_ext, ing_fab = labor.get(name, (0.0, 0.0))
            ext_sum += quantity * ing_ext
            fab_sum += quantity * ing_fab
            print("  {:>6.0f} x {:<24} ext {:>10,.0f}   fab {:>10,.0f}".format(
                quantity, name, quantity * ing_ext, quantity * ing_fab))
        print("  {:>35} ext {:>10,.0f}   fab {:>10,.0f}".format(
            "subtotal", ext_sum, fab_sum))
        own = fabrication - fab_sum
        print("\nthis thing's own work: {:,.0f} ticks = {:.0f} work-s".format(
            own, own / TICKS_PER_WORK_SECOND))
        print("  (should equal the card's \"Work to make\" for a "
              "non-stuffable thing)")

    if count <= 0:
        print("\nnot stuffable, so the card shows one value:")
        print("  Extraction labor    " + as_card(extraction))
        print("  Fabrication labor   " + as_card(fabrication))
        return

    options = stuff_options(db, element) & set(labor)
    if chosen:
        options = [s for s in chosen if s in labor] or sorted(options)
    else:
        options = sorted(options, key=lambda s: sum(labor[s]))

    # The shipped base excludes stuff; the worker adds it back.
    cheapest = min(options, key=lambda s: sum(labor[s])) if options else None
    all_options = sorted(stuff_options(db, element) & set(labor),
                         key=lambda s: sum(labor[s]))
    solver_pick = all_options[0] if all_options else None
    base_ext = extraction - (count * labor[solver_pick][0] if solver_pick else 0)
    base_fab = fabrication - (count * labor[solver_pick][1] if solver_pick else 0)

    print("\nstuffable: {:.0f} units of stuff".format(count))
    print("  solver's cheapest stuff : {}".format(solver_pick))
    print("  shipped stuff-free base : ext {:,.0f}   fab {:,.0f} ticks".format(
        base_ext, base_fab))
    print("  work stat for the factor: {}".format(work_stat))
    print("\n{:<18}{:>28}{:>28}".format("stuff", "Extraction labor",
                                        "Fabrication labor"))
    print("-" * 74)
    for name in options:
        ext = base_ext + count * labor[name][0]
        fab = (base_fab + count * labor[name][1]) * work_factor(
            elements, name, work_stat)
        print("{:<18}{:>28}{:>28}".format(name, as_card(ext), as_card(fab)))


if __name__ == "__main__":
    main()
