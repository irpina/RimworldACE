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

## The port, so far: the value solve

`Source/Economy.Core/` is the start of the Stage 0 model in C# (`docs/53`,
`docs/54`): a library with no RimWorld and no Unity reference, built for
`net472` (what the game's Mono loads) and `net8.0` (what the harness runs
on). It holds the labor value solve, ported to the bit from
`economy_lab/model.py`'s `_update_labor_values`, including CPython's
compensated `sum()` where the laboratory uses it.

It is checked against fixtures the laboratory writes from real economies:

```sh
python -m economy_lab.fixtures                       # Source/Fixtures/labor_values/*.json
dotnet run --project economy_mod/Source/Economy.Core.Check --configuration Release
```

The harness reports, per fixture and per starting iterate, how many values
matched exactly, the largest difference in units in the last place, and
the largest relative difference. Exit code 0 is bit-exact everywhere, 1 is
within `1e-9` but not exact, 3 is outside tolerance.
`tests/test_port_fixtures.py` asserts the committed fixtures are what the
laboratory computes today; when the model moves, regenerate them and re-run
the harness, in that order.

The library is **not** yet loaded by the game: nothing goes into
`1.6/Assemblies` that has not been seen loading there, and the mod's own
csproj does not reference it.

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

## Checking the port

Two commands, neither of which needs RimWorld:

```
dotnet run --project Source/Economy.Core.Check
dotnet run --project Source/Economy.Drive
```

The first checks all five ported slices against the laboratory's
committed fixtures — the value solve, the basket and the wage, the
reserve army and habituation, the regional price update, the wage-cost
refresh — and then the properties of the parts that have no fixtures:
`StateCodec`, `DayScheduler`, `WealthCoupling`, `SelfCheck` and
`TickBudget`. It ends with `ALL PORT CHECKS PASSED` or a non-zero exit
code naming what failed.

The second drives `EconomyWorldComponent` through a fresh world, a day
passing, a save and reload, a mid-day save resumed, and a pre-schema-3
save upgraded — against `Source/Economy.Facade`, which is the RimWorld
surface read out of the last real build and **never shipped**.

Regenerate the fixtures with `python -m economy_lab.fixtures`,
`.wage_fixtures`, `.bargaining_fixtures`, `.price_fixtures` and
`.wage_cost_fixtures` when the model moves; `tests/test_port_fixtures.py`
fails when they are stale.

## Verifying the built assemblies

```
python Source/verify.py
```

Checks both: the mod's assembly (the four types its defs name, no
`Rand`, no Harmony, no gameplay-writing API, and the binding surface
exactly as measured) and the ported model's (its eleven types, and
**no reference to RimWorld, Verse or Unity at all** — the claim
`docs/53` §2 makes and `docs/93` finally checks against the binary).

It also fails when `SocialProduction.Economy.dll` does not reference the
ported model, which means it was built before the wiring landed and
would run the old code with none of the new behaviour and nothing
saying so. **On a fresh checkout it fails for exactly that reason**:
rebuild the mod assembly against RimWorld's managed DLLs and it passes.
