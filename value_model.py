"""Reimplementation of RimWorld's CalculatedBaseMarketValue, from IL.

See docs/01-formula.md. Used to ask what the formula *would* have produced
for defs where a human authored an explicit MarketValue instead.
"""
from defs import DefDb, stat, cost_list, cost_stuff_count, fnum

LABOR_COEFF = 0.0036
WORK_THRESHOLD = 2.0
STUFF_FALLBACK = 2.0


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
                fixed.append((allowed[0], float(cnt) if cnt else 1.0))
            if not ok:
                continue
            try:
                yield_n = float(p.text.strip())
            except (AttributeError, ValueError):
                yield_n = 1.0
            work = fnum(r, "workAmount") or 0.0
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
            self._cache[defname] = authored
            return authored
        _stack = _stack or set()
        if defname in _stack:
            return 0.0                       # cycle guard
        _stack = _stack | {defname}
        v = self.calculated(defname, _stack=_stack)
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
