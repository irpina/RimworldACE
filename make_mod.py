"""Generate the labor-ledger mod's XML patches from the solved graph.

Each producible def gets two statBases entries written by a
PatchOperationConditional, which handles defs that have no <statBases>
element yet and is marked success=Always so a def belonging to an absent
DLC cannot break loading.

The element name is not cosmetic. A direct child of <Patch> must be named
<Operation>, but an entry in a PatchOperationSequence's <operations> list
is an ordinary list item and must be <li>. Getting that wrong loads
nothing and logs "List item found with name Operation that is not <li>",
which is exactly what the five expansion files did until 2026-08-25.

Defs RimWorld generates at load (meat) cannot be patched, because there is no
XML node to patch. They are skipped and reported.
"""
import csv
import os
import xml.sax.saxutils as sax

from defs import DefDb
from animals import inject_generated_meat

TICKS_PER_SECOND = 60.0
OUT_DIR = os.path.join("mod", "Patches")
CSV = os.path.join("out", "embodied_labor.csv")

EXPANSIONS = ("Royalty", "Ideology", "Biotech", "Anomaly", "Odyssey")

# Things whose info card the stat has no business on.
SKIP_CATEGORIES = {"Unfinished"}


def xml_backed_defnames():
    """Map XML-backed defNames to their owning Core/DLC package."""
    db = DefDb()
    generated = set(inject_generated_meat(db))
    out = {}
    for src, dn, _ in db.defs("ThingDef"):
        if dn and not src.startswith("<generated"):
            out[dn] = src.split(os.sep, 1)[0]
    return out, generated


def operation(dn, ext, fab, indent="  ", element="Operation"):
    """One def's patch.

    `element` is "Operation" at the top level of <Patch> and "li" inside a
    PatchOperationSequence's <operations> list; see the module docstring.
    """
    d = sax.escape(dn)
    body = (f"<SNLT_ExtractionLabor>{ext}</SNLT_ExtractionLabor>"
            f"<SNLT_FabricationLabor>{fab}</SNLT_FabricationLabor>")
    return [
        f'{indent}<{element} Class="PatchOperationConditional">',
        f'{indent}  <xpath>/Defs/ThingDef[defName="{d}"]/statBases</xpath>',
        f"{indent}  <success>Always</success>",
        f'{indent}  <match Class="PatchOperationAdd">',
        f'{indent}    <xpath>/Defs/ThingDef[defName="{d}"]/statBases</xpath>',
        f"{indent}    <value>{body}</value>",
        f"{indent}  </match>",
        f'{indent}  <nomatch Class="PatchOperationAdd">',
        f'{indent}    <xpath>/Defs/ThingDef[defName="{d}"]</xpath>',
        f"{indent}    <value><statBases>{body}</statBases></value>",
        f"{indent}  </nomatch>",
        f"{indent}</{element}>",
    ]


def validate(paths):
    """Refuse to ship a patch file RimWorld would reject.

    XML that parses is not XML that loads. Every one of these rules was
    satisfied by the version that silently patched nothing for three
    weeks, except the one it broke.
    """
    import xml.etree.ElementTree as ET

    problems = []
    for path in paths:
        root = ET.parse(path).getroot()
        name = os.path.basename(path)
        if root.tag != "Patch":
            problems.append(f"{name}: root is <{root.tag}>, expected <Patch>")
        for child in root:
            if child.tag != "Operation":
                problems.append(
                    f"{name}: <Patch> child is <{child.tag}>, expected <Operation>"
                )
        # A PatchOperationSequence's <operations> is an ordinary list, so its
        # entries must be <li>. <Operation> there logs "List item found with
        # name Operation that is not <li>" and applies nothing.
        for holder in root.iter("operations"):
            for item in holder:
                if item.tag != "li":
                    problems.append(
                        f"{name}: <operations> entry is <{item.tag}>, expected <li>"
                    )
                elif item.get("Class") is None:
                    problems.append(f"{name}: <operations> entry without a Class")
        # Only operations need a Class. <mods><li>Anomaly</li></mods> is a
        # list of plain strings and must not be caught by this.
        for op in root.iter("Operation"):
            if op.get("Class") is None:
                problems.append(f"{name}: <Operation> without a Class attribute")
    if problems:
        for problem in sorted(set(problems))[:10]:
            print("  INVALID: " + problem)
        raise SystemExit(f"{len(problems)} structural problems; refusing to ship")
    print(f"  validated           : {len(paths)} files load-shaped")


def main():
    patchable, generated = xml_backed_defnames()
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))

    ops = {package: [] for package in ["Core", *EXPANSIONS]}
    skipped_gen, skipped_missing, skipped_cat = [], [], []
    for r in rows:
        dn = r["defName"]
        if r.get("category") in SKIP_CATEGORIES:
            skipped_cat.append(dn)
            continue
        if dn in generated:
            skipped_gen.append(dn)
            continue
        if dn not in patchable:
            skipped_missing.append(dn)
            continue
        ext = float(r["extraction_labor"]) / TICKS_PER_SECOND
        fab = float(r["fabrication_labor"]) / TICKS_PER_SECOND
        if ext <= 0 and fab <= 0:
            continue
        package = patchable[dn]
        if package not in ops:
            skipped_missing.append(dn)
            continue
        ops[package].append((dn, round(ext, 3), round(fab, 3)))

    os.makedirs(OUT_DIR, exist_ok=True)
    old_combined = os.path.join(OUT_DIR, "SNLT_LaborContent.xml")
    if os.path.exists(old_combined):
        os.remove(old_combined)

    total = 0
    written = []
    for package, package_ops in ops.items():
        package_ops.sort(key=lambda t: t[0])
        total += len(package_ops)
        lines = ['<?xml version="1.0" encoding="utf-8"?>', "<Patch>", "",
                 f"  <!-- Generated by make_mod.py from {CSV}. {len(package_ops)} {package} defs.",
                 "       Do not hand-edit; regenerate instead. -->", ""]
        indent, element = "  ", "Operation"
        if package != "Core":
            lines += ['  <Operation Class="PatchOperationFindMod">',
                      f"    <mods><li>{package}</li></mods>",
                      '    <match Class="PatchOperationSequence">',
                      "      <success>Always</success>", "      <operations>"]
            indent, element = "        ", "li"
        for dn, ext, fab in package_ops:
            lines += operation(dn, ext, fab, indent, element)
        if package != "Core":
            lines += ["      </operations>", "    </match>", "  </Operation>"]
        lines += ["", "</Patch>", ""]
        out = os.path.join(OUT_DIR, f"SNLT_LaborContent_{package}.xml")
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        written.append(out)
        print(f"wrote {out}: {len(package_ops)} defs")

    validate(written)
    print(f"  patched defs        : {total}")
    print(f"  skipped, generated  : {len(skipped_gen)} (no XML node to patch)")
    print(f"  skipped, not in XML : {len(skipped_missing)}")
    print(f"  skipped, category   : {len(skipped_cat)}")
    if skipped_gen:
        print(f"    e.g. {', '.join(sorted(skipped_gen)[:5])}")


if __name__ == "__main__":
    main()
