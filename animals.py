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

  graze    feed labor 0, for animals that feed themselves off the map -
           foodType including rough plant matter (pasture) or Dendrovore
           (trees). Both are finite, but that is differential rent, not
           labor content, and is deliberately out of scope.

           Dendrovore was added after the rule's first form charged the
           Alphabeaver 68 nutrition of hay it cannot eat, purely because
           its foodType says "DendrovoreAnimal" and not also
           "VegetarianRoughAnimal". Thrumbo and AlphaThrumbo say both, so
           they grazed free at 0.6 and 0.5 ticks per meat while the
           Alphabeaver came out at 717.7 - one animal producing the whole
           1,435x spread across the meat defs. A forest is a free gift of
           nature on exactly the same terms as a pasture.
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


def _eval_curve(points, x):
    """Piecewise-linear SimpleCurve evaluation."""
    if not points:
        return x
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            if x1 == x0:
                return y1
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return points[-1][1]


def post_process_curve(db, stat_name):
    """Read a StatDef's postProcessCurve.

    MeatAmount and LeatherAmount both carry (0,0) (5,14) (40,40)
    (100000,100000) - identity above 40, a large boost below it. Without
    this, every small animal's yield is understated: a sparrow's raw
    140*0.12 = 16.8 becomes 22.8, and a dryad's 1.33 becomes 3.7.
    """
    for _, dn, el in db.defs("StatDef"):
        if dn != stat_name:
            continue
        c = el.find("postProcessCurve")
        if c is None:
            return []
        pts = []
        for li in c.iter("li"):
            t = (li.text or "").strip().strip("()")
            parts = [p for p in t.replace(",", " ").split() if p]
            if len(parts) >= 2:
                try:
                    pts.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass
            else:
                loc = li.find("loc")
                if loc is not None:
                    try:
                        pts.append((float(loc.findtext("x")),
                                    float(loc.findtext("y"))))
                    except (TypeError, ValueError):
                        pass
        return sorted(pts)
    return []


def _lifestage_factors(db):
    out = {}
    for _, dn, el in db.defs("LifeStageDef"):
        out[dn] = {
            "hunger": fnum(el, "hungerRateFactor") or 1.0,
            "body": fnum(el, "bodySizeFactor") or 1.0,
        }
    return out


def _curve_average(el):
    """Verse.Rand.ByCurveAverage: sum(x*y)/sum(y) over the curve's points."""
    if el is None:
        return None
    pts = []
    for li in el.iter("li"):
        t = (li.text or "").strip().strip("()")
        parts = [p for p in t.replace(",", " ").split() if p]
        if len(parts) >= 2:
            try:
                pts.append((float(parts[0]), float(parts[1])))
            except ValueError:
                pass
    wsum = sum(y for _, y in pts)
    return (sum(x * y for x, y in pts) / wsum) if wsum else None


def gestation_days_each(el, race):
    """AnimalProductionUtility.GestationDaysEach (IL).

    Egg layers amortise over the clutch; live-bearers over the litter.
    """
    for comp in el.iter("li"):
        if comp.get("Class") == "CompProperties_EggLayer":
            interval = fnum(comp, "eggLayIntervalDays")
            rng = (comp.findtext("eggCountRange") or "").strip()
            nums = [float(x) for x in rng.replace("~", " ").split() if x.replace(".", "", 1).replace("-", "", 1).isdigit()]
            avg = (sum(nums) / len(nums)) if nums else 1.0
            if interval and avg:
                return interval / avg
    # RaceProperties' ctor defaults gestationPeriodDays to -1, not 0, and
    # RimWorld propagates that negative straight through - insects, which
    # spawn from hives rather than gestate, get a small negative gestation
    # cost. Defaulting to 0 here overstated insect nutrition by ~5-10%.
    gest = fnum(race, "gestationPeriodDays")
    if gest is None:
        gest = -1.0
    litter = _curve_average(race.find("litterSizeCurve")) or 1.0
    return gest / litter if litter else gest


def _nutrition_to_adult(race, stages, el=None):
    """AnimalProductionUtility.NutritionToAdulthood (IL):

        NutritionToGestate + sum over stages i>=1 of
            (minAge[i] - minAge[i-1]) * 60 * lifeStageAges[i].hungerRateFactor
            * baseHungerRate

    Two things to note. The interval is charged at the hunger factor of the
    stage being *entered*, not the one being lived through. And RimWorld's
    own utility omits the per-day scaling that Need_Food actually applies
    (hungerRateFactor * baseHungerRate * 2.6667e-05 per tick = *1.6 per day),
    so its "nutrition" is 1.6x smaller than what a pawn really eats. We keep
    the 1.6 because we convert to hay, which carries real nutrition - see
    validate_animals.py, which checks the unscaled value against the game.
    """
    ages = race.find("lifeStageAges")
    if ages is None or len(ages) < 2:
        return None
    base_hunger = fnum(race, "baseHungerRate")
    if not base_hunger:
        return None
    entries = []
    for li in ages:
        try:
            m = float(li.findtext("minAge") or 0)
        except ValueError:
            m = 0.0
        entries.append((li.findtext("def"), m))

    # gestation, charged at the final (adult) stage's hunger factor
    total = 0.0
    if el is not None:
        adult_f = stages.get(entries[-1][0], {}).get("hunger", 1.0)
        total += gestation_days_each(el, race) * adult_f * base_hunger

    for i in range(1, len(entries)):
        days = (entries[i][1] - entries[i - 1][1]) * DAYS_PER_YEAR
        f = stages.get(entries[i][0], {}).get("hunger", 1.0)
        total += days * f * base_hunger
    return total * NUTRITION_PER_DAY


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
    meat_curve = post_process_curve(db, "MeatAmount")
    leather_curve = post_process_curve(db, "LeatherAmount")
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
        meat_qty = _eval_curve(meat_curve, meat_amount * body)

        leather_def = race.findtext("leatherDef")
        leather_amount = stat(el, "LeatherAmount") or 0.0
        leather_qty = _eval_curve(leather_curve, leather_amount * body)
        if not leather_def or leather_qty <= 0:
            leather_def, leather_qty = None, 0.0

        nutrition = _nutrition_to_adult(race, stages, el)
        food = (race.findtext("foodType") or "")
        can_graze = "Rough" in food or "Dendrovore" in food

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
