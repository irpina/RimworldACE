"""Embodied labor solver, seeded at extraction.

Non-circular by construction: authored MarketValues contribute nothing. The
only exogenous inputs are extraction work amounts (mining hit points, plant
harvest work). Nature contributes zero - a mineral vein's labor content is
the work to mine it, not what the mineral "is worth".

This is a minimum-cost hyperpath problem, not a plain Leontief inverse. Each
def may have several production options; we take the cheapest in labor, per
the brief. Because every option cost is non-negative and monotone in its
inputs, relaxing from +inf converges without special cycle handling - a cycle
(steel -> components -> machines -> steel) can never lower a cost, so it
simply never wins.

Joint production: there are zero multi-output *recipes* in the XML, but joint
production still arrives twice through the back door - mining spoil (space +
chunks, see BYPRODUCT in primitives.py) and butchery (meat + leather, see
APPORTION in animals.py).
"""
import csv
import math
from defs import DefDb, stat, cost_list, cost_stuff_count, fnum
from primitives import mining_rows, plant_rows

INF = float("inf")
MAX_ITERS = 200
EPS = 1e-6

# Joint-production apportionment now lives with the case that needs it:
# see APPORTION in animals.py and BYPRODUCT in primitives.py.

# Scavenging policy. Some manufactured goods can be mined out of ancient
# ruins rather than made - ComponentIndustrial is minable at 1250 ticks but
# costs 5570 to actually manufacture, a 4.5x gap that propagates to every
# good that uses components.
#
# Socially necessary labor time is a *reproduction* cost: the labor required
# to make the thing again. Digging a manufactured good out of a finite
# ancient deposit is not reproduction, so the default drops extraction
# options for any def that can also be produced. Set to "include" to take
# the literal cheapest path instead.
SCAVENGING = "exclude"      # "exclude" | "include"


class Option:
    __slots__ = ("work", "inputs", "yield_n", "kind", "subst", "label", "method")

    def __init__(self, work, inputs, yield_n, kind, subst=False, label="",
                 method=None):
        self.work = work
        self.inputs = inputs        # [(frozenset(alternatives), qty)]
        self.yield_n = yield_n or 1.0
        self.kind = kind            # extract | recipe | cost
        self.subst = subst
        self.label = label
        self.method = method        # mine | harvest, for extract options


class Graph:
    def __init__(self, db=None, animals=True, apportion=None):
        self.db = db or DefDb()
        self.apportion = apportion
        if animals:
            from animals import inject_generated_meat
            inject_generated_meat(self.db)
        self.things = {dn: el for _, dn, el in self.db.defs("ThingDef")}
        self.options = {d: [] for d in self.things}
        self._build_categories()
        self._build_stuff()
        self._add_extraction()
        self._add_recipes()
        self._add_costs()
        if animals:
            self._add_animals()

    def _add_animals(self):
        """Meat and leather, via competing husbandry paths.

        Grazing and hay-feeding are separate options; min-cost picks and
        spread() reports the gap. Hay is referenced as a substitutable set of
        one so its own embodied labor is picked up from the solve.
        """
        from animals import animal_rows, apportion
        mv = {}
        for dn, el in self.things.items():
            mv[("mv", dn)] = stat(el, "MarketValue")
            mv[("mass", dn)] = stat(el, "Mass")
        self.animal_rows = animal_rows(self.db)
        for r in self.animal_rows:
            paths = []
            if r["can_graze"]:
                paths.append(("graze", 0.0, []))
            n = r["nutrition_to_adult"]
            if n:
                # hay carries its own embodied labor; 0.05 nutrition per unit
                units = n / 0.05
                paths.append(("hayfed", 0.0, [(frozenset(["Hay"]), units)]))
            for label, extra, inputs in paths:
                total = r["butcher_work"] + extra
                meat_share, leather_share = apportion(r, total, mv,
                                                      self.apportion)
                if r["meat_qty"] > 0 and r["meat_def"] in self.options:
                    self.options[r["meat_def"]].append(Option(
                        work=meat_share, inputs=inputs,
                        yield_n=r["meat_qty"], kind="extract",
                        method="husbandry", label=f'{r["race"]}/{label}'))
                if r["leather_def"] and r["leather_def"] in self.options \
                        and r["leather_qty"] > 0:
                    self.options[r["leather_def"]].append(Option(
                        work=leather_share,
                        inputs=inputs if leather_share > 0 else [],
                        yield_n=r["leather_qty"], kind="extract",
                        method="husbandry", label=f'{r["race"]}/{label}'))

    # ---------------------------------------------------------- categories
    def _build_categories(self):
        parent = {}
        for _, dn, el in self.db.defs("ThingCategoryDef"):
            parent[dn] = el.findtext("parent")
        self.cat_members = {}
        direct = {}
        for dn, el in self.things.items():
            tc = el.find("thingCategories")
            for li in (tc if tc is not None else []):
                if li.text:
                    direct.setdefault(li.text.strip(), set()).add(dn)
        # a def in category C is also in every ancestor of C
        for cat, members in direct.items():
            c = cat
            seen = set()
            while c and c not in seen:
                seen.add(c)
                self.cat_members.setdefault(c, set()).update(members)
                c = parent.get(c)

    def _build_stuff(self):
        self.stuff_by_cat = {}
        for dn, el in self.things.items():
            sp = el.find("stuffProps")
            if sp is None:
                continue
            cats = sp.find("categories")
            for li in (cats if cats is not None else []):
                if li.text:
                    self.stuff_by_cat.setdefault(li.text.strip(), set()).add(dn)

    # ---------------------------------------------------------- producers
    def _add_extraction(self):
        things = list(self.db.defs("ThingDef"))
        for r in mining_rows(self.db, things) + plant_rows(self.db, things):
            prod = r["product"]
            if prod not in self.options:
                continue
            self.options[prod].append(Option(
                work=r["ticks_per_unit"], inputs=[], yield_n=1.0,
                kind="extract", label=r["source"], method=r["method"]))

    def _resolve_filter(self, li):
        """Return (alternatives, qty). alternatives is a frozenset of defNames."""
        f = li.find("filter")
        alts = set()
        if f is not None:
            tds = f.find("thingDefs")
            for c in (tds if tds is not None else []):
                if c.text:
                    alts.add(c.text.strip())
            cats = f.find("categories")
            for c in (cats if cats is not None else []):
                if c.text:
                    alts |= self.cat_members.get(c.text.strip(), set())
            dis = f.find("disallowedThingDefs")
            for c in (dis if dis is not None else []):
                if c.text:
                    alts.discard(c.text.strip())
        alts &= set(self.things)
        cnt = li.findtext("count")
        try:
            qty = float(cnt) if cnt else 1.0
        except ValueError:
            qty = 1.0
        return frozenset(alts), qty

    def _add_recipes(self):
        for _, rdn, r in self.db.defs("RecipeDef"):
            prods = r.find("products")
            if prods is None or len(prods) == 0:
                continue                      # surgeries, specialProducts
            # RecipeDef.WorkAmountForStuff (IL): workAmount defaults to -1 and
            # falls back to the first product's WorkToMake stat. 9 of the 57
            # product-recipes rely on this, all cooking plus Make_BeamGraser.
            work = fnum(r, "workAmount")
            if work is None or work < 0:
                first = prods[0].tag
                work = stat(self.things[first], "WorkToMake") or 0.0 \
                    if first in self.things else 0.0
            ings = r.find("ingredients")
            inputs, subst = [], False
            ok = True
            for li in (ings if ings is not None else []):
                alts, qty = self._resolve_filter(li)
                if not alts:
                    ok = False
                    break
                if len(alts) > 1:
                    subst = True
                inputs.append((alts, qty))
            if not ok:
                continue
            for p in prods:
                target = p.tag
                if target not in self.options:
                    continue
                try:
                    yield_n = float(p.text.strip())
                except (AttributeError, ValueError):
                    yield_n = 1.0
                self.options[target].append(Option(
                    work=work, inputs=inputs, yield_n=yield_n,
                    kind="recipe", subst=subst, label=rdn))

    def _add_costs(self):
        for dn, el in self.things.items():
            cl = cost_list(el)
            csc = cost_stuff_count(el)
            if not cl and csc <= 0:
                continue
            work = max(stat(el, "WorkToMake") or 0.0,
                       stat(el, "WorkToBuild") or 0.0)
            inputs = [(frozenset([td]), qty) for td, qty in cl]
            subst = False
            if csc > 0:
                sc = el.find("stuffCategories")
                alts = set()
                for li in (sc if sc is not None else []):
                    if li.text:
                        alts |= self.stuff_by_cat.get(li.text.strip(), set())
                alts &= set(self.things)
                if alts:
                    inputs.append((frozenset(alts), csc))
                    subst = subst or len(alts) > 1
            self.options[dn].append(Option(
                work=work, inputs=inputs, yield_n=1.0,
                kind="cost", subst=subst, label="costList"))

    # ---------------------------------------------------------- the solve
    def option_cost(self, o, val):
        total = o.work
        for alts, qty in o.inputs:
            cheapest = min((val.get(a, INF) for a in alts), default=INF)
            if cheapest == INF:
                return INF
            total += qty * cheapest
        return total / o.yield_n

    def solve(self, scavenging=None):
        """Relax to a fixed point, then apply the scavenging policy and
        re-relax until the set of dropped options is stable.

        The policy can only be applied against solved values: dropping a
        mining option is valid only if a manufacturing option is actually
        reachable. Applying it blind wrongly strands Steel, whose only
        alternative (ExtractMetalFromSlag) has unreachable inputs.
        """
        policy = SCAVENGING if scavenging is None else scavenging
        self.scavenged = []
        self._relax()
        if policy == "exclude":
            for _ in range(10):
                dropped = []
                for d, opts in self.options.items():
                    mined = [o for o in opts
                             if o.kind == "extract" and o.method == "mine"]
                    if not mined:
                        continue
                    made = [o for o in opts if o.kind != "extract"]
                    if any(self.option_cost(o, self.val) < INF for o in made):
                        dropped.append(d)
                if not dropped:
                    break
                for d in dropped:
                    self.options[d] = [
                        o for o in self.options[d]
                        if not (o.kind == "extract" and o.method == "mine")]
                self.scavenged.extend(dropped)
                self._relax()
        return self.val

    def _relax(self):
        val = {d: INF for d in self.things}
        depth = {d: None for d in self.things}
        best = {d: None for d in self.things}

        for it in range(MAX_ITERS):
            changed = 0
            for d, opts in self.options.items():
                for o in opts:
                    total = o.work
                    dmax = 0
                    ok = True
                    for alts, qty in o.inputs:
                        # cheapest-by-labor valid input
                        cheapest, cd = INF, 0
                        for a in alts:
                            v = val.get(a, INF)
                            if v < cheapest:
                                cheapest, cd = v, (depth.get(a) or 0)
                        if cheapest == INF:
                            ok = False
                            break
                        total += qty * cheapest
                        dmax = max(dmax, cd)

                    if not ok:
                        continue
                    cand = total / o.yield_n
                    if cand < val[d] - EPS:
                        val[d] = cand
                        depth[d] = dmax if o.kind == "extract" else dmax + 1
                        best[d] = o
                        changed += 1
            if not changed:
                break
        self.iterations = it + 1
        self.val, self.depth, self.best = val, depth, best
        return val

    def decompose(self, d, _stack=None):
        """Split embodied labor into (extraction-origin, fabrication-added).

        Walks the winning options backwards. Extraction work is labor spent
        at the boundary; every other option's own workAmount is fabrication.
        The two always sum to the def's embodied labor.
        """
        if not hasattr(self, "_decomp"):
            self._decomp = {}
        if d in self._decomp:
            return self._decomp[d]
        _stack = _stack or set()
        if d in _stack:
            return 0.0, 0.0
        o = self.best.get(d)
        if o is None:
            return 0.0, 0.0
        _stack = _stack | {d}
        ext = fab = 0.0
        for alts, qty in o.inputs:
            cheapest, pick = INF, None
            for a in alts:
                v = self.val.get(a, INF)
                if v < cheapest:
                    cheapest, pick = v, a
            if pick is None:
                continue
            e, f = self.decompose(pick, _stack)
            ext += qty * e
            fab += qty * f
        # Primary production (mining, harvesting, husbandry) is extraction;
        # everything else adds fabrication labor. Inputs are accumulated
        # either way - hay-fed husbandry is an extraction option that still
        # carries hay's own embodied labor.
        if o.kind == "extract":
            ext += o.work
        else:
            fab += o.work
        res = (ext / o.yield_n, fab / o.yield_n)
        self._decomp[d] = res
        return res

    def spread(self, d):
        """Labor cost of the dearest vs cheapest option, for multi-recipe defs."""
        opts = self.options.get(d) or []
        if len(opts) < 2:
            return None
        costs = []
        for o in opts:
            total, ok = o.work, True
            for alts, qty in o.inputs:
                cheapest = min((self.val.get(a, INF) for a in alts), default=INF)
                if cheapest == INF:
                    ok = False
                    break
                total += qty * cheapest
            if ok:
                costs.append(total / o.yield_n)
        if len(costs) < 2 or min(costs) <= 0:
            return None
        return max(costs) / min(costs)


def category_of(el):
    tc = el.find("thingCategories")
    if tc is not None and len(tc) and tc[0].text:
        return tc[0].text.strip()
    if el.find("building") is not None:
        return "Building"
    return ""


def main():
    from value_model import Model
    g = Graph()
    g.solve()
    m = Model(g.db)

    rows = []
    for d, el in g.things.items():
        v = g.val[d]
        if v == INF:
            continue
        o = g.best[d]
        price = m.base_market_value(d)
        ext, fab = g.decompose(d)
        rows.append({
            "defName": d,
            "category": category_of(el),
            "path": o.kind,
            "source": o.label,
            "direct_labor": round(o.work / o.yield_n, 1),
            "extraction_labor": round(ext, 1),
            "fabrication_labor": round(fab, 1),
            "embodied_labor": round(v, 1),
            "work_hours": round(v / 2500.0, 3),
            "depth": g.depth[d],
            "market_value": round(price, 2) if price else 0.0,
            "silver_per_tick": round(price / v, 6) if v > 0 and price else None,
            "substitutable": o.subst,
            "recipe_spread": (round(s, 2) if (s := g.spread(d)) else None),
        })

    rows.sort(key=lambda r: -r["embodied_labor"])
    with open("out/embodied_labor.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    unreachable = [d for d in g.things if g.val[d] == INF]
    print(f"converged in {g.iterations} iterations")
    print(f"defs with an embodied labor value : {len(rows)}")
    print(f"unreachable from extraction       : {len(unreachable)}")
    print(f"used a substitutable input        : {sum(1 for r in rows if r['substitutable'])}")
    print(f"multiple production options       : "
          f"{sum(1 for r in rows if r['recipe_spread'])}")
    from collections import Counter
    print("\nby production depth:")
    for dep, n in sorted(Counter(r["depth"] for r in rows).items()):
        print(f"  depth {dep}: {n}")
    print("\n-> out/embodied_labor.csv")


if __name__ == "__main__":
    main()
