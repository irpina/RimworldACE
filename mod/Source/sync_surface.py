"""Set verify.py's expected binding surface from the built assembly.

Run deliberately, never automatically: the check exists to notice when the
surface changes, so it must be updated by someone who looked at the change
and decided it was intended.
"""
import pathlib
import re
import sys

sys.path.insert(0, ".")
from cli_reader import Assembly

NL = chr(10)
asm = Assembly(r"mod\Assemblies\SocialProduction.LaborContent.dll")
asm._build_owner_maps()
surface = sorted(
    "{}.{}".format(asm.string(r["Namespace"]), asm.string(r["Name"]))
    for _, r in asm.iter_table(1)
    if asm.string(r["Namespace"]).startswith(("RimWorld", "Verse"))
)
print("measured surface ({}):".format(len(surface)))
for name in surface:
    print("   " + name)

p = pathlib.Path("mod/Source/verify.py")
text = p.read_text(encoding="utf-8")
block = "    expected = [" + NL
for name in surface:
    block += '        "{}",'.format(name) + NL
block += "    ]"
text = re.sub(r"    expected = \[\n(?:.*\n)*?    \]", block, text, count=1)
text = re.sub(
    r"binding surface is the \w+ expected symbols",
    "binding surface is the {} expected symbols".format(len(surface)),
    text,
    count=1,
)
p.write_text(text, encoding="utf-8")
print("verify.py expected surface updated to {} symbols".format(len(surface)))
