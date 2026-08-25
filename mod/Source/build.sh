#!/bin/sh
# Build Labor Content's one assembly, then verify what was built.
#
# Uses the C# compiler Windows already ships with the .NET Framework
# rather than the .NET SDK, which HANDOFF.md says not to install. That
# constrains the source to C# 5 — no interpolated strings, no
# expression-bodied members — which is why StatWorker_LaborContent.cs is
# written the way it is.
#
# This csc predates Roslyn's -deterministic, so it stamps a fresh MVID
# into every build: two builds of identical source differ in their bytes.
# The committed DLL therefore cannot be checked against the committed
# source by hash. What can be checked is its *content*, which is what
# verify.py does and what this script runs afterwards.
#
# Usage:  sh mod/Source/build.sh  [path to RimWorld]
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RIMWORLD="${1:-/c/Program Files (x86)/Steam/steamapps/common/RimWorld}"
MANAGED="$RIMWORLD/RimWorldWin64_Data/Managed"
CSC="/c/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe"

if [ ! -f "$MANAGED/Assembly-CSharp.dll" ]; then
    echo "no RimWorld assemblies at: $MANAGED" >&2
    exit 1
fi

# RimWorld memory-maps the assembly while it runs, so csc cannot replace
# it and reports CS0016 "user-mapped section open", which reads like a
# permissions problem and is not one.
if tasklist 2>/dev/null | grep -qi "RimWorldWin64"; then
    echo "RimWorld is running; it holds the assembly open." >&2
    echo "Close the game and run this again." >&2
    exit 1
fi

mkdir -p "$ROOT/mod/Assemblies"

"$CSC" \
    -target:library \
    -optimize+ \
    -nologo \
    -warnaserror+ \
    -out:"$(cygpath -w "$ROOT/mod/Assemblies/SocialProduction.LaborContent.dll")" \
    -reference:"$(cygpath -w "$MANAGED/Assembly-CSharp.dll")" \
    -reference:"$(cygpath -w "$MANAGED/UnityEngine.CoreModule.dll")" \
    "$(cygpath -w "$ROOT/mod/Source/LaborContent/StatWorker_LaborContent.cs")"

echo "built mod/Assemblies/SocialProduction.LaborContent.dll"

cd "$ROOT" && python mod/Source/verify.py
