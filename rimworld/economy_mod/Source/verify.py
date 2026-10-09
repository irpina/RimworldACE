"""Check what is actually inside the built Stage 1 economy assembly.

`economy_mod` makes two claims in its About text and its README: that it is
**read-only** with respect to vanilla gameplay, and that what it derives is
**deterministic**. Both are claims about code that nobody can check by
playing, because a mod that quietly rolled a die or nudged a price would look
exactly like one that did not until much later.

This checks them against the compiled assembly, using the repository's own
ECMA-335 reader (`cli_reader.py`) rather than a decompiler nobody is allowed
to install:

1. Every type the defs and the tab reference exists.
2. `Verse.Rand` is **not** referenced anywhere. Rand is global mutable state
   shared with the game's own generation, so drawing from it would make this
   component's output depend on what else drew first. Nothing here rolls.
3. Harmony is not referenced. No patches, so no vanilla behaviour changed.
4. Nothing on a denylist of gameplay-writing APIs is referenced.
5. The binding surface is exactly the expected set, so a RimWorld update can
   only break what is listed.

Run via `python rimworld/economy_mod/Source/verify.py` after building.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spike"))

from cli_reader import Assembly  # noqa: E402

ASSEMBLIES = Path(__file__).resolve().parents[1] / "1.6" / "Assemblies"

DLL = ASSEMBLIES / "SocialProduction.Economy.dll"

#: The ported model (docs/53 onward).  A second assembly beside the mod's,
#: and the one the mod's new behaviour actually lives in.
CORE_DLL = ASSEMBLIES / "SocialProduction.Economy.Core.dll"

#: The types the port's harnesses and the mod both name.  A rename here is
#: a missing-method exception at load rather than a compile error, because
#: the two assemblies are versioned together only by convention.
CORE_REQUIRED_TYPES = (
    "SocialProduction.Economy.Core.LaborValueSolver",
    "SocialProduction.Economy.Core.WageSolver",
    "SocialProduction.Economy.Core.BargainingSolver",
    "SocialProduction.Economy.Core.PriceSolver",
    "SocialProduction.Economy.Core.WageCostSolver",
    "SocialProduction.Economy.Core.StateCodec",
    "SocialProduction.Economy.Core.DayScheduler",
    "SocialProduction.Economy.Core.WealthCoupling",
    "SocialProduction.Economy.Core.SelfCheckReport",
    "SocialProduction.Economy.Core.TickBudget",
    "SocialProduction.Economy.Core.CompensatedSum",
)

REQUIRED_TYPES = (
    # Named by economy_mod/1.6/Defs/MainButtonDefs/Economy_MainButton.xml;
    # a rename here is a red error at load and no tab at all.
    "SocialProduction.Economy.MainTabWindow_Economy",
    "SocialProduction.Economy.EconomyWorldComponent",
    "SocialProduction.Economy.ProfileBuilder",
    "SocialProduction.Economy.SettlementProfile",
)

#: Referencing any of these would contradict the read-only claim.  Matched as
#: substrings of the fully-qualified name, so `TradeUtility` catches
#: `RimWorld.TradeUtility` without needing its namespace pinned.
FORBIDDEN = (
    "Rand",          # determinism: nothing is rolled
    "Harmony",       # read-only: nothing is patched
    "TradeUtility",
    "TradeDeal",
    "StatWorker",
    "StatExtension",
    "PriceUtility",
    "ThingDefCountClass",
)

#: Measured from the built assembly, not predicted.  Update deliberately when
#: the mod genuinely needs a new game API, and never to make this pass.
EXPECTED_SURFACE = [
    "RimWorld.BiomeDef",
    "RimWorld.Faction",
    "RimWorld.MainTabWindow",
    "RimWorld.Planet.Hilliness",
    "RimWorld.Planet.PlanetTile",
    "RimWorld.Planet.Settlement",
    "RimWorld.Planet.Tile",
    "RimWorld.Planet.World",
    "RimWorld.Planet.WorldComponent",
    "RimWorld.Planet.WorldGrid",
    "RimWorld.Planet.WorldInfo",
    "RimWorld.Planet.WorldObject",
    "RimWorld.Planet.WorldObjectsHolder",
    "UnityEngine.Color",
    "UnityEngine.GUI",
    "UnityEngine.Rect",
    "UnityEngine.Vector2",
    "Verse.Def",
    "Verse.Find",
    "Verse.GameFont",
    "Verse.IExposable",
    "Verse.LoadSaveMode",
    "Verse.Log",
    "Verse.LookMode",
    "Verse.Scribe",
    "Verse.Scribe_Collections",
    "Verse.Scribe_Values",
    "Verse.Text",
    "Verse.TickManager",
    "Verse.Widgets",
]


def failures():
    if not DLL.exists():
        return ["assembly not built: " + str(DLL)]

    problems = []
    asm = Assembly(str(DLL))
    asm._build_owner_maps()

    defined = {
        "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
        for _, r in asm.iter_table(2)
        if asm.string(r["Name"]) != "<Module>"
    }
    for required in REQUIRED_TYPES:
        if required not in defined:
            problems.append(
                "type missing from the assembly: {} not in {}".format(
                    required, sorted(defined)
                )
            )

    external = sorted(
        {
            "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
            for _, r in asm.iter_table(1)
        }
    )
    for banned in FORBIDDEN:
        hits = [name for name in external if banned in name]
        if hits:
            problems.append(
                "{} is referenced, which contradicts the read-only and "
                "deterministic claims: {}".format(banned, hits)
            )

    # The mod's behaviour now lives in the ported model, so an assembly
    # that does not reference it predates the wiring (docs/85) and would
    # run the old code silently.  Staleness is invisible otherwise: the
    # file loads, the tab appears, and none of the new rows are there.
    if not any(name.startswith("SocialProduction.Economy.Core") for name in external):
        problems.append(
            "{} does not reference the ported model, so it was built before "
            "the wiring landed: rebuild it (economy_mod/README.md)".format(DLL.name)
        )

    surface = [
        name
        for name in external
        if name.startswith(("RimWorld", "Verse", "UnityEngine"))
    ]
    if surface != EXPECTED_SURFACE:
        added = sorted(set(surface) - set(EXPECTED_SURFACE))
        gone = sorted(set(EXPECTED_SURFACE) - set(surface))
        problems.append(
            "the assembly's game binding surface changed: "
            "added {}, removed {}".format(added, gone)
        )
    return problems


def core_failures():
    """Check the ported model's assembly, if it has been built.

    Its central claim since docs/53 is that it has **no RimWorld and no
    Unity in it** — that is what lets it be tested on a build machine, and
    what `docs/76` and `docs/92` rest on. The claim has been true by
    inspection and by the fact that it compiles without the game's
    assemblies; this checks it against the binary, which is the only
    version of the claim a RimWorld update cannot quietly falsify.

    Absent rather than failing when the assembly has not been built, so a
    checkout that has only ever run the Python side is not reported as
    broken.
    """
    if not CORE_DLL.exists():
        return ["{} has not been built; run the net472 build "
                "(economy_mod/README.md)".format(CORE_DLL.name)]

    asm = Assembly(CORE_DLL)
    problems = []

    defined = {
        "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
        for _, r in asm.iter_table(2)
    }
    for required in CORE_REQUIRED_TYPES:
        if required not in defined:
            problems.append(
                "{} is missing from {}".format(required, CORE_DLL.name))

    external = sorted(
        {
            "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
            for _, r in asm.iter_table(1)
        }
    )
    game = [
        name
        for name in external
        if name.startswith(("RimWorld", "Verse", "UnityEngine"))
    ]
    if game:
        problems.append(
            "the ported model references the game, which it must not "
            "(docs/53 section 2): {}".format(game)
        )
    for banned in FORBIDDEN:
        hits = [name for name in external if banned in name]
        if hits:
            problems.append(
                "{} is referenced by the ported model: {}".format(banned, hits))
    return problems


def main():
    problems = failures()
    problems += core_failures()
    if problems:
        for problem in problems:
            print("FAIL: " + problem)
        raise SystemExit(1)
    print(
        "verified: {} types present, nothing rolled, nothing patched, "
        "binding surface is the {} expected symbols; the ported model "
        "carries {} types and no game reference at all".format(
            len(REQUIRED_TYPES), len(EXPECTED_SURFACE), len(CORE_REQUIRED_TYPES)
        )
    )


if __name__ == "__main__":
    main()
