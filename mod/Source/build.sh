#!/bin/sh
# Build Labor Content's one assembly.
#
# Uses the C# compiler Windows already ships with the .NET Framework
# rather than the .NET SDK, which HANDOFF.md says not to install. That
# constrains the source to C# 5 — no interpolated strings, no
# expression-bodied members — which is why StatWorker_LaborContent.cs is
# written the way it is.
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
