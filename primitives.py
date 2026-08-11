"""Extraction labor for RimWorld's authored-value primitives.

Mining, per JobDriver_Mine (IL-verified):
    damage per hit = 80 if building.isNaturalRock else 40
    ticks per hit  = round(100 / MiningSpeed), = 100 at nominal speed
    => ticks to mine one cell = ceil(MaxHitPoints / dmgPerHit) * 100
    => labor per unit = that / building.mineableYield

Plants, per plant.harvestWork / plant.harvestYield.
Growing time is NOT labor - it is elapsed time with no pawn attached, so it
is deliberately excluded. Sowing work is counted where the plant is sowable.
"""
import csv
import math
from defs import DefDb, stat, fnum, text

TICKS_PER_HIT = 100.0      # at MiningSpeed 1.0
TICKS_PER_HOUR = 2500.0
LABOR_COEFF = 0.0036       # silver per tick, from CalculatedBaseMarketValue

# Byproduct policy for mining spoil.
#
# Natural rock declares mineableThing (a chunk) with mineableDropChance 0.25
# and no explicit yield. Mining such a cell is done for the space, not the
# chunk - the chunk is spoil. Charging the full 1200-4800 ticks of mining
# against 0.25 chunks treats the chunk as the purpose of the dig.
#
# This is a joint-production call, and the data decides it. Charging chunks
# the full cost drops the two-rate fit from R2 0.948 to 0.854 and halves the
# extraction rate to 60.7/hr, breaking its agreement with the independent
# primitives estimate (~101/hr). Treating chunks as free restores both. So
# RimWorld prices stone as though the chunk were costless, and "free" is the
# empirically supported default.
BYPRODUCT = "free"         # "free" | "full"


def mining_rows(db, things):
    by_name = {dn: el for _, dn, el in things}
    rows = []
    for _, dn, el in things:
        b = el.find("building")
        if b is None:
            continue
        mt = b.findtext("mineableThing")
        if not mt:
            continue
        hp = stat(el, "MaxHitPoints")
        if hp is None:
            continue
        natural = (b.findtext("isNaturalRock") or "").strip().lower() == "true"
        dmg = 80.0 if natural else 40.0
        # Mineable.TrySpawnYield (IL): drops with probability mineableDropChance,
        # then max(1, EffectiveMineableYield) units. BuildingProperties' ctor
        # defaults mineableYield=1 and mineableDropChance=1.0, so natural rock
        # yields one chunk a quarter of the time. Expected yield is the product.
        my = b.findtext("mineableYield")
        drop = b.findtext("mineableDropChance")
        try:
            base_yield = max(1.0, float(my)) if my else 1.0
            chance = float(drop) if drop else 1.0
        except ValueError:
            continue
        yield_n = base_yield * chance
        if yield_n <= 0:
            continue
        ticks_cell = math.ceil(hp / dmg) * TICKS_PER_HIT
        if chance < 1.0 and BYPRODUCT == "free":
            ticks_unit = 0.0        # spoil from a dig done for other reasons
        else:
            ticks_unit = ticks_cell / yield_n
        prod = by_name.get(mt)
        mv = stat(prod, "MarketValue") if prod is not None else None
        rows.append({
            "source": dn, "method": "mine", "product": mt,
            "yield": yield_n, "hp": hp, "natural_rock": natural,
            "drop_chance": chance, "byproduct": chance < 1.0,
            "ticks_per_unit": ticks_unit,
            "market_value": mv,
        })
    return rows


def plant_rows(db, things):
    by_name = {dn: el for _, dn, el in things}
    rows = []
    for _, dn, el in things:
        p = el.find("plant")
        if p is None:
            continue
        hw = p.findtext("harvestWork")
        hy = p.findtext("harvestYield")
        ht = p.findtext("harvestedThingDef")
        if not (hw and hy and ht):
            continue
        try:
            work, yld = float(hw), float(hy)
        except ValueError:
            continue
        if yld <= 0:
            continue
        sow = p.findtext("sowWork")
        sow_work = float(sow) if sow else 0.0
        sowable = (p.findtext("sowTags") is not None)
        total = work + (sow_work if sowable else 0.0)
        prod = by_name.get(ht)
        mv = stat(prod, "MarketValue") if prod is not None else None
        rows.append({
            "source": dn, "method": "harvest", "product": ht,
            "yield": yld, "harvest_work": work,
            "sow_work": sow_work if sowable else 0.0,
            "ticks_per_unit": total / yld,
            "market_value": mv,
        })
    return rows


def main():
    db = DefDb()
    things = list(db.defs("ThingDef"))
    rows = mining_rows(db, things) + plant_rows(db, things)

    # Best (cheapest-labor) extraction path per product
    best = {}
    for r in rows:
        if r["market_value"] is None:
            continue
        k = r["product"]
        if k not in best or r["ticks_per_unit"] < best[k]["ticks_per_unit"]:
            best[k] = r

    out = []
    for prod, r in sorted(best.items(), key=lambda kv: -kv[1]["market_value"]):
        t = r["ticks_per_unit"]
        mv = r["market_value"]
        out.append({
            "product": prod,
            "method": r["method"],
            "source": r["source"],
            "ticks_per_unit": round(t, 1),
            "work_hours_per_unit": round(t / TICKS_PER_HOUR, 4),
            "market_value": mv,
            "labor_value_at_0.0036": round(t * LABOR_COEFF, 3),
            "price_per_labor_tick": round(mv / t, 5) if t else None,
            "ratio_to_labor_price": round((mv / t) / LABOR_COEFF, 2) if t else None,
        })

    with open("out/primitives.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    hdr = (f'{"product":22}{"method":9}{"ticks/unit":>11}{"MV":>8}'
           f'{"labor value":>13}{"MV/labor":>10}')
    print(hdr)
    print("-" * len(hdr))
    for r in out:
        print(f'{r["product"]:22}{r["method"]:9}{r["ticks_per_unit"]:>11}'
              f'{r["market_value"]:>8}{r["labor_value_at_0.0036"]:>13}'
              f'{r["ratio_to_labor_price"]:>10}')
    print(f"\n{len(out)} extractable primitives -> out/primitives.csv")


if __name__ == "__main__":
    main()
