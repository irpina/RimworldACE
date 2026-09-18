"""Validate value_model against RimWorld's own Recipes debug table.

Cases transcribed from a dev-mode export (Debug output -> Economy ->
Recipes). Only recipes that exist in XML are checkable: the table also lists
recipeMaker-generated ones (Make_Gun_AssaultRifle and friends), which exist
only in DefDatabase at runtime.

This caught the ingredient-count bug: a recipe's <count> is in *ingredient
value* units, not thing counts. Make_ComponentSpacer's `<Gold>0.3</Gold>` is
really 3 gold, because gold is small-volume stuff and
IngredientCount.CountRequiredOfFor divides by ValuePerUnitOf (0.1).
"""
import sys

from defs import recipe_getter, count_required
from value_model import Model

# (recipe, cheapest ingredients value, cheapest products value)
CASES = [
    ("Make_ComponentIndustrial", 22.8, 32.0),
    ("Make_ComponentSpacer", 190.0, 200.0),
    ("Make_ChemfuelFromWood", 84.0, 80.5),
    ("Make_StoneBlocksGranite", 0.0, 18.0),
    ("Make_StoneBlocksSandstone", 0.0, 18.0),
    ("Make_StoneBlocksVacstone", 0.0, 40.0),
    ("Make_Pemmican", None, 22.4),
    ("Make_Kibble", None, 55.0),
    ("CookMealSimple", None, 15.0),
    ("CookMealFine", None, 20.0),
    ("CookMealLavish", None, 40.0),
    ("Make_Wort", None, 12.5),
    ("ExtractMetalFromSlag", 0.0, 28.5),
    ("Make_Penoxycyline", 12.0, 18.0),
    ("Make_WakeUp", 12.0, 35.0),
    ("Make_GoJuice", 33.0, 53.0),
    ("Make_Flake", 7.6, 14.0),
    ("Make_Yayo", 15.2, 21.0),
    ("Make_PsychiteTea", 7.6, 10.0),
    ("Make_SmokeleafJoint", 6.4, 11.0),
    ("Make_MedicineIndustrial", 20.5, 18.0),
    ("Make_SubcoreBasic", 159.0, 200.0),
    ("Make_Shell_Toxic", 42.0, 55.0),
    ("Make_GravlitePanel", 19.0, 4.0),
    ("Make_BiomutationPulser", 445.0, 800.0),
    ("Make_MetalbloodSerum", 20.0, 200.0),
    ("Make_JuggernautSerum", 17.5, 200.0),
    ("Make_VoidsightSerum", 19.5, 60.0),
    ("Make_MindNumbSerum", 34.5, 80.0),
    ("Make_GhoulResurrectionSerum", 25.0, 60.0),
    ("Make_Shell_Deadlife", 18.8, 55.0),
]
TOL = 0.02


def main():
    m = Model()
    recipes = {dn: r for _, dn, r in m.db.defs("RecipeDef")}

    def ingredients_value(rdef):
        ings = rdef.find("ingredients")
        if ings is None:
            return None
        getter = recipe_getter(rdef)
        total = 0.0
        for li in ings:
            f = li.find("filter")
            tds = f.find("thingDefs") if f is not None else None
            if tds is None or len(tds) != 1:
                return None            # substitutable; game picks cheapest
            name = tds[0].text.strip()
            el = m.things.get(name)
            if el is None:
                return None
            try:
                base = float(li.findtext("count") or 1)
            except ValueError:
                base = 1.0
            qty = count_required(base, el, getter)
            if qty is None:
                return None
            total += qty * m.base_market_value(name)
        return total

    def products_value(rdef):
        ps = rdef.find("products")
        if ps is None:
            return None
        total = 0.0
        for p in ps:
            try:
                cnt = float((p.text or "1").strip())
            except ValueError:
                cnt = 1.0
            total += cnt * m.base_market_value(p.tag)
        return total

    ni = oki = np_ = okp = 0
    fails, skipped = [], []
    for name, exp_i, exp_p in CASES:
        r = recipes.get(name)
        if r is None:
            # recipeMaker-generated: exists only in DefDatabase at runtime
            skipped.append(name)
            continue
        if exp_i is not None:
            got = ingredients_value(r)
            if got is not None:
                ni += 1
                if abs(got - exp_i) <= TOL * max(1.0, exp_i):
                    oki += 1
                else:
                    fails.append((name, "ingredients", got, exp_i))
        if exp_p is not None:
            got = products_value(r)
            if got is not None:
                np_ += 1
                if abs(got - exp_p) <= TOL * max(1.0, exp_p):
                    okp += 1
                else:
                    fails.append((name, "products", got, exp_p))

    print(f"  {'OK ' if oki == ni else 'FAIL'} ingredient values  {oki}/{ni} within {TOL*100:.0f}%")
    print(f"  {'OK ' if okp == np_ else 'FAIL'} product values     {okp}/{np_} within {TOL*100:.0f}%")
    if skipped:
        print(f"  --  skipped            {len(skipped)} recipeMaker-generated, "
              f"no XML node to check")
    if fails:
        print(f"\n{len(fails)} mismatches:")
        for name, what, got, want in fails:
            if got is None:
                print(f"    {name:30} {what}")
            else:
                print(f"    {name:30} {what:12} ours={got:9.2f} game={want:9.2f}")
        return 1
    print("\nall checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
