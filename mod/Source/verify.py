"""Check what is actually inside the built Labor Content assembly.

The .NET Framework csc that builds this mod predates `-deterministic`, so
it stamps a fresh MVID into every build and two builds of identical source
differ in their bytes. The committed DLL cannot be verified against the
committed source by hash.

What can be verified is its content, using the repository's own ECMA-335
reader (`cli_reader.py`) rather than a decompiler nobody is allowed to
install. Three things matter and all three have burned us or nearly have:

1. The type name the StatDefs reference actually exists. A typo there is
   a red error at load and no stats at all.
2. `ValueToString` is present and virtual, i.e. it really overrides the
   base rather than shadowing it.
3. The unit separator is U+00B7 and not mojibake. The source has no
   byte-order mark, so csc reads it in the ANSI codepage; a literal `·`
   in a string arrives in the assembly as `Â·`. This is not hypothetical
   — it happened, and it is why the source writes `\\u00B7`.

Run via `sh mod/Source/build.sh`, or directly.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cli_reader import Assembly  # noqa: E402

DLL = Path(__file__).resolve().parents[1] / "Assemblies" / "SocialProduction.LaborContent.dll"
WORKER = "SocialProduction.LaborContent.StatWorker_LaborContent"
#: MethodAttributes: Public | Virtual | HideBySig.
EXPECTED_FLAGS = 0x00C6


def failures():
    if not DLL.exists():
        return ["assembly not built: " + str(DLL)]

    problems = []
    asm = Assembly(str(DLL))
    asm._build_owner_maps()

    types = {
        "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
        for _, r in asm.iter_table(2)
        if asm.string(r["Name"]) != "<Module>"
    }
    if WORKER not in types:
        problems.append(
            "the StatDefs' workerClass is missing from the assembly: "
            "{} not in {}".format(WORKER, sorted(types))
        )

    methods = {
        asm.string(r["Name"]): r["Flags"]
        for mi, r in asm.iter_table(6)
        if asm._owner_of_method(mi) == WORKER
    }
    if "ValueToString" not in methods:
        problems.append("ValueToString is not defined; nothing would be overridden")
    elif methods["ValueToString"] != EXPECTED_FLAGS:
        problems.append(
            "ValueToString is not a public virtual override "
            "(flags {:#06x}, expected {:#06x})".format(
                methods["ValueToString"], EXPECTED_FLAGS
            )
        )

    data = DLL.read_bytes()
    if " · ".encode("utf-16-le") not in data:
        problems.append("the U+00B7 unit separator is not in the assembly")
    if " Â· ".encode("utf-16-le") in data:
        problems.append(
            "mojibake separator found: csc read the source in the ANSI "
            "codepage. Write the character as an escape, not a literal."
        )
    for probe in ("in-game h", "work-s", "ticks"):
        if probe.encode("utf-16-le") not in data:
            problems.append("unit label missing from the assembly: " + probe)

    # The smaller the binding surface, the less a RimWorld update can break.
    external = {
        "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
        for _, r in asm.iter_table(1)
    }
    rimworld = sorted(
        name for name in external
        if name.startswith("RimWorld.") or name.startswith("Verse.")
    )
    if rimworld != ["RimWorld.StatWorker", "Verse.ToStringNumberSense"]:
        problems.append(
            "the assembly's RimWorld binding surface grew: {}".format(rimworld)
        )
    return problems


def main():
    problems = failures()
    if problems:
        for problem in problems:
            print("FAIL: " + problem)
        raise SystemExit(1)
    print(
        "verified: {} overrides ValueToString, separator is U+00B7, "
        "binds only to RimWorld.StatWorker and Verse.ToStringNumberSense".format(
            WORKER.rsplit(".", 1)[1]
        )
    )


if __name__ == "__main__":
    main()
