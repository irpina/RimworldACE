"""Reimplementation of RimWorld's CalculatedBaseMarketValue, from IL.

See docs/01-formula.md. Used to ask what the formula *would* have produced
for defs where a human authored an explicit MarketValue instead.
"""
from defs import (DefDb, stat, cost_list, cost_stuff_count, fnum,
                  count_required, recipe_getter)

LABOR_COEFF = 0.0036
WORK_THRESHOLD = 2.0
STUFF_FALLBACK = 2.0

# StatWorker.FinalizeValue (IL): if val > stat.roundToFiveOver, round to the
# nearest 5. MarketValue does not declare it - it inherits roundToFiveOver=200
# from the abstract MarketValueBase, which is why reading the raw node misses
# it. This is what makes Gun_AssaultRifle 480 rather than 482, and
# Gun_SniperRifle 530 rather than 532, while the revolver's 135.4 is untouched.
ROUND_TO_FIVE_OVER = 200.0


def finalize(v):
    return round(v / 5.0) * 5.0 if v > ROUND_TO_FIVE_OVER else v


class Model:
    def __init__(self, db=None):
        self.db = db or DefDb()
        self.things = {dn: el for _, dn, el in self.db.defs("ThingDef")}
        self.recipes = [el for _, _, el in self.db.defs("RecipeDef")]
        self._recipe_for = None
        self._cache = {}

    # -- CalculableRecipe ------------------------------------------------
    def _build_recipe_index(self):
        """First recipe (in load order) with exactly one product == def,
        and every ingredient fixed. Mirrors CalculableRecipe."""
        idx = {}
        for r in self.recipes:
            prods = r.find("products")
            if prods is None or len(prods) != 1:
                continue
            p = prods[0]
            target = p.tag
            if target in idx:
                continue          # first match wins
            ings = r.find("ingredients")
            getter = recipe_getter(r)
            fixed = []
            ok = True
            for li in (ings if ings is not None else []):
                filt = li.find("filter")
                tds = filt.find("thingDefs") if filt is not None else None
                allowed = [c.text.strip() for c in tds] if tds is not None else []
                cats = filt.find("categories") if filt is not None else None
                if cats is not None or len(allowed) != 1:
                    ok = False    # not a fixed ingredient -> whole lookup aborts
                    break
                cnt = li.findtext("count")
                base = float(cnt) if cnt else 1.0
                el = self.things.get(allowed[0])
                # <count> is in ingredient-value units, not thing counts
                qty = count_required(base, el, getter) if el is not None else base
                if qty is None:
                    ok = False
                    break
                fixed.append((allowed[0], qty))
            if not ok:
                continue
            try:
                yield_n = float(p.text.strip())
            except (AttributeError, ValueError):
                yield_n = 1.0
            # RecipeDef.WorkAmountForStuff: workAmount < 0 falls back to the
            # first product's WorkToMake stat.
            work = fnum(r, "workAmount")
            if work is None or work < 0:
                prod_el = self.things.get(target)
                work = (stat(prod_el, "WorkToMake") or 0.0) if prod_el is not None else 0.0
            idx[target] = {"work": work, "yield": yield_n, "ingredients": fixed}
        return idx

    def calculable_recipe(self, defname):
        if self._recipe_for is None:
            self._recipe_for = self._build_recipe_index()
        el = self.things.get(defname)
        if el is None:
            return None
        if cost_list(el) or cost_stuff_count(el) > 0:
            return None
        return self._recipe_for.get(defname)

    # -- BaseMarketValue --------------------------------------------------
    def base_market_value(self, defname, _stack=None):
        """Authored value wins; otherwise compute. Mirrors the dispatcher."""
        if defname in self._cache:
            return self._cache[defname]
        el = self.things.get(defname)
        if el is None:
            return 0.0
        authored = stat(el, "MarketValue")
        if authored is not None:
            v = finalize(authored)
            self._cache[defname] = v
            return v
        _stack = _stack or set()
        if defname in _stack:
            return 0.0                       # cycle guard
        _stack = _stack | {defname}
        v = finalize(self.calculated(defname, _stack=_stack))
        self._cache[defname] = v
        return v

    def calculated(self, defname, stuff=None, _stack=None):
        el = self.things.get(defname)
        if el is None:
            return 0.0
        _stack = _stack or set()
        value = 0.0

        recipe = self.calculable_recipe(defname)
        if recipe is not None:
            work = recipe["work"]
            yield_n = recipe["yield"] or 1.0
            for ing, cnt in recipe["ingredients"]:
                value += cnt * self.base_market_value(ing, _stack)
        else:
            wm = stat(el, "WorkToMake") or 0.0
            wb = stat(el, "WorkToBuild") or 0.0
            work = max(wm, wb)
            yield_n = 1.0
            for td, cnt in cost_list(el):
                value += cnt * self.base_market_value(td, _stack)
            csc = cost_stuff_count(el)
            if csc > 0:
                if stuff is not None:
                    value += csc * self.base_market_value(stuff, _stack)
                else:
                    value += csc * STUFF_FALLBACK

        if work > WORK_THRESHOLD:
            value += work * LABOR_COEFF
        return value / yield_n

    def breakdown(self, defname, stuff=None):
        """Return (input_value, labor_value, total) for reporting."""
        el = self.things.get(defname)
        if el is None:
            return 0.0, 0.0, 0.0
        recipe = self.calculable_recipe(defname)
        inputs = 0.0
        if recipe is not None:
            work = recipe["work"]
            yield_n = recipe["yield"] or 1.0
            for ing, cnt in recipe["ingredients"]:
                inputs += cnt * self.base_market_value(ing)
        else:
            work = max(stat(el, "WorkToMake") or 0.0,
                       stat(el, "WorkToBuild") or 0.0)
            yield_n = 1.0
            for td, cnt in cost_list(el):
                inputs += cnt * self.base_market_value(td)
            csc = cost_stuff_count(el)
            if csc > 0:
                inputs += (csc * self.base_market_value(stuff)) if stuff \
                          else csc * STUFF_FALLBACK
        labor = work * LABOR_COEFF if work > WORK_THRESHOLD else 0.0
        return inputs / yield_n, labor / yield_n, (inputs + labor) / yield_n
