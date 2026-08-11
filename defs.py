"""Load RimWorld XML defs with ParentName inheritance resolved.

RimWorld's XmlInheritance merges a child node onto its resolved parent
recursively, matching by element name: a child element replaces the
parent's element of the same name, otherwise it is appended. This matters
because things like <MarketValue> commonly live on an abstract base
(e.g. StoneBlocksBase) and are inherited by every concrete def.
"""
import copy
import glob
import math
import os
import xml.etree.ElementTree as ET

RIMWORLD = (r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld")
DATA = os.path.join(RIMWORLD, "Data")

# Element names whose children are genuine lists (<li> items), where
# merge-by-element-name is meaningless and the child replaces wholesale.
LIST_LIKE = {"li"}


def _iter_def_files(data_dir=DATA):
    for path in glob.glob(os.path.join(data_dir, "**", "*.xml"), recursive=True):
        # Defs only; skip Languages, Patches, Sounds metadata etc.
        norm = path.replace("\\", "/")
        if "/Defs/" not in norm:
            continue
        yield path


def _merge(parent, child):
    """Return a resolved copy of `child` layered over `parent`."""
    out = copy.deepcopy(parent)
    out.tag = child.tag
    for k, v in child.attrib.items():
        out.attrib[k] = v
    if child.text is not None and child.text.strip():
        out.text = child.text

    # If either side is an <li> list, the child replaces the whole node.
    child_is_list = any(c.tag == "li" for c in child)
    if child_is_list:
        for existing in list(out):
            out.remove(existing)
        for c in child:
            out.append(copy.deepcopy(c))
        return out

    for c in child:
        if c.get("Inherit", "").lower() == "false":
            for existing in out.findall(c.tag):
                out.remove(existing)
            out.append(copy.deepcopy(c))
            continue
        match = out.find(c.tag)
        if match is None:
            out.append(copy.deepcopy(c))
        else:
            merged = _merge(match, c)
            out.remove(match)
            out.append(merged)
    return out


class DefDb:
    def __init__(self, data_dir=DATA):
        self.named = {}      # Name attr -> raw element
        self.raw = []        # (source, element)
        self._resolved = {}
        self._load(data_dir)

    def _load(self, data_dir):
        for path in _iter_def_files(data_dir):
            try:
                root = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            if root.tag != "Defs":
                continue
            src = os.path.relpath(path, data_dir)
            for el in root:
                if not isinstance(el.tag, str):
                    continue
                self.raw.append((src, el))
                nm = el.get("Name")
                if nm:
                    self.named[nm] = el

    def resolve(self, el, _seen=None):
        key = id(el)
        if key in self._resolved:
            return self._resolved[key]
        parent_name = el.get("ParentName")
        if not parent_name:
            res = el
        else:
            _seen = _seen or set()
            if parent_name in _seen:
                res = el  # cycle guard
            else:
                _seen.add(parent_name)
                p = self.named.get(parent_name)
                res = _merge(self.resolve(p, _seen), el) if p is not None else el
        self._resolved[key] = res
        return res

    def defs(self, tag=None, concrete_only=True):
        """Yield (source, defName, resolved_element)."""
        for src, el in self.raw:
            if tag and el.tag != tag:
                continue
            if concrete_only and el.get("Abstract", "").lower() == "true":
                continue
            r = self.resolve(el)
            dn = r.findtext("defName")
            if concrete_only and not dn:
                continue
            yield src, dn, r


# ------------------------------------------------------------- helpers

def stat(el, name):
    """Read a statBases entry as float, or None."""
    sb = el.find("statBases")
    if sb is None:
        return None
    n = sb.find(name)
    if n is None or n.text is None:
        return None
    try:
        return float(n.text.strip())
    except ValueError:
        return None


def cost_list(el):
    """[(thingDef, count)] from <costList>."""
    cl = el.find("costList")
    if cl is None:
        return []
    out = []
    for c in cl:
        try:
            out.append((c.tag, float(c.text.strip())))
        except (AttributeError, ValueError):
            pass
    return out


def cost_stuff_count(el):
    n = el.findtext("costStuffCount")
    try:
        return float(n.strip()) if n else 0.0
    except ValueError:
        return 0.0


def nutrition(el):
    """Nutrition per unit, however the def happens to declare it."""
    v = stat(el, "Nutrition")
    if v is not None:
        return v
    ing = el.find("ingestible")
    if ing is not None:
        for tag in ("CachedNutrition", "nutrition"):
            t = ing.findtext(tag)
            if t:
                try:
                    return float(t.strip())
                except ValueError:
                    pass
    return None


def value_per_unit(el, getter="volume"):
    """IngredientValueGetter.ValuePerUnitOf (IL).

    Volume:    def.IsStuff ? (smallVolume ? 0.1 : 1.0) : 1.0
    Nutrition: def.IsNutritionGivingIngestible ? Nutrition : 0
    """
    if getter == "nutrition":
        return nutrition(el) or 0.0
    if el.find("stuffProps") is None:
        return 1.0
    small = (el.findtext("smallVolume") or "").strip().lower() == "true"
    return 0.1 if small else 1.0


def count_required(count, el, getter="volume"):
    """IngredientCount.CountRequiredOfFor: ceil(count / valuePerUnit).

    A recipe's <count> is in *ingredient value* units, not thing counts.
    Make_ComponentSpacer asks for `<Gold>0.3</Gold>`, and gold is small-volume
    stuff, so that is really 3 gold. Cooking recipes use the nutrition getter,
    so CookMealSimple's `count 0.5` is 10 units of 0.05-nutrition food.
    """
    vpu = value_per_unit(el, getter)
    if vpu <= 0:
        return None
    return math.ceil(count / vpu)


def recipe_getter(recipe_el):
    cls = (recipe_el.findtext("ingredientValueGetterClass") or "").strip()
    return "nutrition" if "Nutrition" in cls else "volume"


def text(el, path, default=None):
    v = el.findtext(path)
    return v.strip() if v is not None else default


def fnum(el, path):
    v = el.findtext(path)
    if v is None:
        return None
    try:
        return float(v.strip())
    except ValueError:
        return None
