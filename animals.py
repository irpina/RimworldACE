"""Animal products: generated meat defs, butchery yields, husbandry labor.

Everything here is read from the assembly rather than assumed:

  ThingDefGenerator_Meat.ImpliedMeatDefs  -> meat defName is "Meat_<race>",
      BaseMarketValue = race.meatMarketValue, Nutrition 0.05, Mass 0.03.
      RaceProperties' ctor defaults meatMarketValue to 2.0; only insects
      (0.5) and humanlikes (0.8) override it anywhere in the data.
  StatPart_BodySize.TransformValue        -> stat *= bodySize
      so meat = MeatAmount(140 default) * bodySize,
         leather = LeatherAmount(0 default, declared per race) * bodySize
  Pawn.BodySize                           -> lifeStage.bodySizeFactor * baseBodySize
  Need_Food.BaseHungerRate                -> lifeStage.hungerRateFactor
                                             * race.baseHungerRate * 2.6667e-05
      (x60000 ticks/day = x1.6 nutrition per day)

Husbandry paths are modelled as *competing options*, not averaged - min-cost
picks, and the spread is reported:

  graze    feed labor 0, for animals whose foodType includes rough plant
           matter. Pasture is finite, but that is differential rent, not
           labor content, and is deliberately out of scope.
  hay-fed  nutrition to adulthood / 0.05 per hay unit, times hay's own
           embodied labor.

Hunting is not modelled: the labor is combat time, which is a function of
weapon, skill and animal health, none of which is a def field. Modelling it
would mean inventing numbers, so wild animals simply have no production path
unless they can be tamed and reared.
"""
import xml.etree.ElementTree as ET
from defs import stat, fnum

NUTRITION_PER_DAY = 1.6          # 2.6666666599339806e-05 * 60000 ticks
DAYS_PER_YEAR = 60.0
MEAT_AMOUNT_DEFAULT = 140.0
MEAT_MARKET_VALUE_DEFAULT = 2.0
MEAT_NUTRITION = 0.05
MEAT_MASS = 0.03
BUTCHER_RECIPE = "ButcherCorpseFlesh"

# Flesh types that yield no meat.
NON_FLESH = {"Mechanoid", "EntityMechanical", "Drone"}

# Joint production: one carcass yields meat AND leather.
#
# Ran the same test that settled mining spoil. It does NOT discriminate here:
# meat_only / count / mass / value all give extraction 95.4/hr, fabrication
# 6.9/hr, R2 0.948 to three decimals. Animal products are so labor-cheap
# under grazing that they cannot move an aggregate fit. The test has limits
# and this is one of them - reported rather than papered over.
#
# So the choice is made on principle, not evidence. "meat_only" is rejected
# because it leaves 24 leather defs with literally zero labor and a positive
# price, an undefined implied rate. "value" apportions by market value, which
# reintroduces exactly the circularity the solver exists to avoid. "mass" is
# physical and non-circular; it coincides with "count" here because meat and
# leather both have Mass 0.03.
APPORTION = "mass"           # "meat_only" | "mass" | "count" | "value"


def _lifestage_factors(db):
    out = {}
    for _, dn, el in db.defs("LifeStageDef"):
        out[dn] = {
            "hunger": fnum(el, "hungerRateFactor") or 1.0,
            "body": fnum(el, "bodySizeFactor") or 1.0,
        }
    return out


def _nutrition_to_adult(race, stages):
    """Sum nutrition eaten from birth to the adult life stage."""
    ages = race.find("lifeStageAges")
    if ages is None or len(ages) == 0:
        return None
    base_hunger = fnum(race, "baseHungerRate")
    if not base_hunger:
        return None
    entries = []
    for li in ages:
        d = li.findtext("def")
        try:
            m = float(li.findtext("minAge") or 0)
        except ValueError:
            m = 0.0
        entries.append((d, m))
    total = 0.0
    for i, (sdef, min_age) in enumerate(entries):
        if i + 1 >= len(entries):
            break                      # final stage is adulthood; stop
        days = (entries[i + 1][1] - min_age) * DAYS_PER_YEAR
        f = stages.get(sdef, {}).get("hunger", 1.0)
        total += days * f * base_hunger * NUTRITION_PER_DAY
    return total


def inject_generated_meat(db):
    """Add the meat ThingDefs RimWorld generates at load, so the rest of the
    pipeline sees them the way DefDatabase would."""
    existing = {dn for _, dn, _ in db.defs("ThingDef")}
    added = []
    for _, dn, el in list(db.defs("ThingDef")):
        race = el.find("race")
        if race is None:
            continue
        if (race.findtext("fleshType") or "Normal").strip() in NON_FLESH:
            continue
        if not fnum(race, "baseBodySize"):
            continue
        name = "Meat_" + dn
        if name in existing:
            continue
        mmv = fnum(race, "meatMarketValue")
        if mmv is None:
            mmv = MEAT_MARKET_VALUE_DEFAULT
        e = ET.Element("ThingDef")
        ET.SubElement(e, "defName").text = name
        sb = ET.SubElement(e, "statBases")
        ET.SubElement(sb, "MarketValue").text = str(mmv)
        ET.SubElement(sb, "Mass").text = str(MEAT_MASS)
        ET.SubElement(sb, "Nutrition").text = str(MEAT_NUTRITION)
        tc = ET.SubElement(e, "thingCategories")
        ET.SubElement(tc, "li").text = "MeatRaw"
        db.raw.append(("<generated:ThingDefGenerator_Meat>", e))
        added.append(name)
    return added


def butchery_work(db):
    for _, dn, el in db.defs("RecipeDef"):
        if dn == BUTCHER_RECIPE:
            return fnum(el, "workAmount") or 0.0
    return 0.0


def animal_rows(db):
    """One row per rearable animal, with yields and per-path rearing labor."""
    stages = _lifestage_factors(db)
    work_butcher = butchery_work(db)
    things = {dn: el for _, dn, el in db.defs("ThingDef")}
    rows = []
    for dn, el in things.items():
        race = el.find("race")
        if race is None:
            continue
        if (race.findtext("fleshType") or "Normal").strip() in NON_FLESH:
            continue
        body = fnum(race, "baseBodySize")
        if not body:
            continue
        meat_name = "Meat_" + dn
        if meat_name not in things:
            continue

        meat_amount = stat(el, "MeatAmount")
        if meat_amount is None:
            meat_amount = MEAT_AMOUNT_DEFAULT
        meat_qty = meat_amount * body

        leather_def = race.findtext("leatherDef")
        leather_amount = stat(el, "LeatherAmount") or 0.0
        leather_qty = leather_amount * body
        if not leather_def or leather_qty <= 0:
            leather_def, leather_qty = None, 0.0

        nutrition = _nutrition_to_adult(race, stages)
        food = (race.findtext("foodType") or "")
        can_graze = "Rough" in food

        rows.append({
            "race": dn,
            "meat_def": meat_name, "meat_qty": meat_qty,
            "leather_def": leather_def, "leather_qty": leather_qty,
            "body_size": body,
            "nutrition_to_adult": nutrition,
            "can_graze": can_graze,
            "butcher_work": work_butcher,
        })
    return rows


def apportion(row, total_labor, mv_lookup, rule=None):
    """Split one carcass's labor between meat and leather.

    Returns (meat_share, leather_share) summing to total_labor.
    """
    rule = rule or APPORTION
    m, l = row["meat_qty"], row["leather_qty"]
    if not row["leather_def"] or l <= 0:
        return total_labor, 0.0
    if rule == "meat_only":
        return total_labor, 0.0
    if rule == "count":
        w = m / (m + l)
    elif rule == "mass":
        lm = mv_lookup.get(("mass", row["leather_def"])) or 0.03
        mm = MEAT_MASS
        w = (m * mm) / (m * mm + l * lm)
    elif rule == "value":
        lv = mv_lookup.get(("mv", row["leather_def"])) or 1.0
        mv = mv_lookup.get(("mv", row["meat_def"])) or 1.0
        w = (m * mv) / (m * mv + l * lv)
    else:
        w = 1.0
    return total_labor * w, total_labor * (1 - w)
