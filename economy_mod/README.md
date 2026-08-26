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

```powershell
dotnet build .\economy_mod\Source\Economy\Economy.csproj --configuration Release
```

Override `RimWorldDir` if the game is installed somewhere else. The compiled
assembly is written directly to `economy_mod/1.6/Assemblies`.
