#!/bin/sh
# Build Labor Content's one assembly, then verify what was built.
#
# This used to invoke the csc.exe that Windows ships with the .NET
# Framework, because HANDOFF.md said not to install the .NET SDK. That
# constraint lapsed when Stage 1 needed the SDK anyway, so the build now
# goes through LaborContent.csproj like economy_mod's does, and works on
# macOS as well as Windows.
#
# Two properties changed with the compiler, and both are improvements.
# Roslyn honours -deterministic, so two builds of identical source are
# byte-identical and the committed DLL *can* now be checked against the
# committed source by rebuilding — the warning HANDOFF.md carried about
# that applies only to the old csc builds. And Roslyn reads source as
# UTF-8, so the U+00B7 separator no longer depends on the ANSI codepage.
# verify.py still checks the separator; that failure mode was real once.
#
# The source stays at C# 5 (LangVersion 5 in the csproj) so a Windows
# machine with no SDK can still build it the old way.
#
# Usage:  sh rimworld/mod/Source/build.sh  [path to RimWorld]
# ROOT below is rimworld/, the directory holding mod/ and spike/.
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

DOTNET="${DOTNET:-dotnet}"
if ! command -v "$DOTNET" >/dev/null 2>&1; then
    if [ -x "$HOME/.dotnet/dotnet" ]; then
        DOTNET="$HOME/.dotnet/dotnet"
    else
        echo "no dotnet on PATH and none at ~/.dotnet/dotnet" >&2
        echo "see economy_mod/README.md for the toolchain" >&2
        exit 1
    fi
fi

# RimWorld memory-maps the assembly while it runs, so the compiler cannot
# replace it. On Windows that surfaces as CS0016 "user-mapped section
# open", which reads like a permissions problem and is not one.
if pgrep -qi "RimWorld" 2>/dev/null || tasklist 2>/dev/null | grep -qi "RimWorldWin64"; then
    echo "RimWorld is running; it holds the assembly open." >&2
    echo "Close the game and run this again." >&2
    exit 1
fi

# The csproj defaults to each platform's usual Steam install. A path
# argument overrides it.
if [ -n "$1" ]; then
    set -- -p:RimWorldDir="$1"
else
    set --
fi

"$DOTNET" build "$ROOT/mod/Source/LaborContent/LaborContent.csproj" \
    --configuration Release --nologo "$@"

echo "built mod/Assemblies/SocialProduction.LaborContent.dll"

cd "$ROOT" && "${PYTHON:-python3}" mod/Source/verify.py
