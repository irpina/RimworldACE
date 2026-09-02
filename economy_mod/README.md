# Social Production: Economy

This is the Stage 1 RimWorld 1.6 runtime mod. The current vertical slice:

- adds a persistent `WorldComponent` with a one-day simulation cadence;
- derives a **deterministic profile** for every settlement the world
  generated — faction, tile, biome, hilliness — and groups settlements into
  **regions** by faction;
- persists those profiles, re-derives them on load, and **reports whether the
  two agree**;
- adds a read-only Economy main tab that lists them;
- leaves all vanilla trade prices and gameplay systems unchanged;
- uses no Harmony patches.

## Determinism, and why the profiles are saved at all

The profiles are a pure function of the saved world, so storing them is
redundant — *unless* the stored copy is used to check that the function stayed
pure. It is. On load the component re-derives every profile and compares it
against what was written, and the tab shows the result:

```
Reload determinism    reproduced 27/27 on reload
```

A mismatch means part of the derivation depends on state that is not in the
save. That would be invisible otherwise and fatal once the Stage 0 model is
integrated, because the whole laboratory rests on identical inputs giving
identical histories.

Nothing is rolled. `Verse.Rand` is global mutable state shared with the
game's own generation, so drawing from it would make this component's output
depend on what else drew first. Where variation is wanted it comes from
hashing stable identity — the world's `persistentRandomValue` and the tile id
— through the same SplitMix64 mixer `economy_lab/scale.py` uses.

## Verifying the build

```powershell
python economy_mod/Source/verify.py
```

On macOS, `cli_reader.py` needs `pefile`, which Homebrew's Python refuses to
install into (PEP 668). Run it from the project venv:

```sh
python3 -m venv .venv && .venv/bin/pip install pefile   # once
.venv/bin/python economy_mod/Source/verify.py
```

Checks the compiled assembly rather than the source: that every type the defs
reference exists, that `Rand` and Harmony are **not** referenced, that no
gameplay-writing API is on the binding surface, and that the surface is
exactly the 30 expected game symbols. A read-only claim nobody can check by
playing is worth checking by reading.

The deterministic economic model still lives in `economy_lab`. The runtime
shell does not yet pretend that the Stage 0 model is ready for integration.

## Build

The project targets .NET Framework 4.7.2, matching RimWorld's Mono runtime,
and builds with the .NET 8 SDK. It references RimWorld's installed managed
assemblies and uses Microsoft's framework reference-assembly package at build
time.

```sh
dotnet build economy_mod/Source/Economy/Economy.csproj --configuration Release
```

The compiled assembly is written directly to `economy_mod/1.6/Assemblies`.

`RimWorldDir` defaults to the usual Steam install for the platform you are
on — Windows and macOS put the managed assemblies in different places, and
the project handles both:

| | install | managed assemblies |
|---|---|---|
| Windows | `C:/Program Files (x86)/Steam/steamapps/common/RimWorld` | `RimWorldWin64_Data/Managed` |
| macOS | `~/Library/Application Support/Steam/steamapps/common/RimWorld` | `RimWorldMac.app/Contents/Resources/Data/Managed` |

Override it for a non-default install:

```sh
dotnet build economy_mod/Source/Economy/Economy.csproj --configuration Release \
    -p:RimWorldDir=/path/to/RimWorld
```

The build fails with a named error if no `Assembly-CSharp.dll` is there,
rather than with a wall of unresolved-type errors.

### macOS toolchain

The .NET SDK's macOS installer is a `.pkg` needing admin rights. The
official install script does not, and puts an SDK under `~/.dotnet`:

```sh
curl -sSL https://dot.net/v1/dotnet-install.sh | sh -s -- --channel 8.0 --install-dir "$HOME/.dotnet"
```

That install puts nothing on `PATH`, so either add it —

```sh
export PATH="$HOME/.dotnet:$PATH"
```

— or invoke `~/.dotnet/dotnet` directly. `mod/Source/build.sh` falls back to
`~/.dotnet/dotnet` on its own when `dotnet` is not on `PATH`.

Verified with 8.0.424 — the same SDK version the Windows machine uses.
`net472` is a valid target on macOS because
`Microsoft.NETFramework.ReferenceAssemblies` supplies the reference
assemblies; no Mono or Framework install is involved.

### Development link

RimWorld loads whatever is in its `Mods` folder, so both mods are symlinked
there rather than copied — regenerate or rebuild and the game sees it, with
no copy step to forget.

```sh
MODS="$HOME/Library/Application Support/Steam/steamapps/common/RimWorld/RimWorldMac.app/Mods"
ln -sfn "$PWD/mod"         "$MODS/SNLT"
ln -sfn "$PWD/economy_mod" "$MODS/SocialProductionEconomy"
```

On Windows these are directory junctions with the same two names. Note that
on macOS the `Mods` folder is *inside the app bundle*, so a Steam validation
or update can remove the links; re-running the two commands is the fix.
