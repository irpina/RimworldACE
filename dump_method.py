"""Locate and disassemble methods by name across Assembly-CSharp.dll."""
import sys
from cli_reader import Assembly, disassemble

DLL = (r"C:\Program Files (x86)\Steam\steamapps\common\RimWorld"
       r"\RimWorldWin64_Data\Managed\Assembly-CSharp.dll")


def main():
    asm = Assembly(DLL)
    asm._build_owner_maps()
    targets = sys.argv[1:]
    if not targets:
        print("usage: dump_method.py <MethodName|Type::Method> ...")
        return

    # index every method by name
    index = {}
    for mi, r in asm.iter_table(6):
        nm = asm.string(r["Name"])
        index.setdefault(nm, []).append((mi, r))

    for t in targets:
        if "::" in t:
            want_type, want_m = t.split("::", 1)
        else:
            want_type, want_m = None, t
        hits = index.get(want_m, [])
        if not hits:
            print(f"### NOT FOUND: {t}\n")
            continue
        for mi, r in hits:
            owner = asm._owner_of_method(mi)
            if want_type and not owner.endswith(want_type):
                continue
            print(f"### {owner}::{want_m}   (RVA {r['RVA']:#x})")
            il, _ = asm.method_il(r)
            if il is None:
                print("  <no body>\n")
                continue
            for line in disassemble(asm, il):
                print("  " + line)
            print()


if __name__ == "__main__":
    main()
