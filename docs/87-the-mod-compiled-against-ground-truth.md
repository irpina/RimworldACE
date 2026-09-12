# The mod assembly, compiled against ground truth

Design and results in one: a verification of code already written.
`docs/85` §5 left the game-facing wiring "compiled against a stub façade
only", and `docs/86` §5 left "build the mod assembly against RimWorld's
shipped managed DLLs" as the last item that was not an in-game
observation. This closes most of that item and says exactly what is
left of it.

**The headline: the mod's game-facing code builds for `net472` with the
real SDK, zero errors and zero warnings, against a façade whose every
type and member was read out of the last real build's reference tables.
And because that façade contains nothing else, the build proves a
property worth more than itself: the wiring added in `docs/85`
introduces no RimWorld API the previous real build did not already
resolve.**

## 1. Where ground truth came from

RimWorld's managed assemblies are game files. This environment does not
have them and should not — that is a licensing boundary, not a
capability one, and it is the one boundary in this session that should
not be routed around.

But the repository carries
`economy_mod/1.6/Assemblies/SocialProduction.Economy.dll`, built on the
user's machine against **RimWorld 1.6.9676.17924**. A .NET assembly
records every external type and member it uses, so its reference tables
are an exact, redistributable statement of the API surface the mod
touches:

```
apt-get install -y mono-utils
monodis --typeref   .../SocialProduction.Economy.dll
monodis --memberref .../SocialProduction.Economy.dll
```

That yields 44 distinct RimWorld and Unity members and the types behind
them — `RimWorld.Planet.WorldObject.get_Tile`,
`Verse.Scribe_Collections.Look`, `RimWorld.Planet.PlanetTile.tileId`,
`UnityEngine.GUI.set_color`, and the rest.

**It immediately contradicted the hand-written stub.** `docs/85`'s
façade had `Faction` in `Verse`; it is `RimWorld.Faction`. It had
`Tile` and `Faction` on `Settlement`; they are on
`RimWorld.Planet.WorldObject`, which `Settlement` inherits. It had
`Find.World` as a field; it is a property. Each of those would have
compiled fine and been wrong, which is precisely the class of error a
guessed façade cannot catch and this one can.

## 2. What was built

```
economy_mod/Source/Economy.Facade/
    RimWorldFacade.cs        44 members, nothing else
    Economy.Facade.csproj    net472, same as the mod
```

Committed rather than left in the scratchpad, for one reason: a façade
is only trustworthy if it is maintained, and one that lives in a
temporary directory is a claim nobody can re-check. It is never
referenced by `Economy.csproj`, so a real build cannot accidentally pick
it up.

The compile itself uses the real SDK at the mod's real target framework:

```
dotnet build …/Check.csproj      # net472, Economy.Core + Economy.Facade
Build succeeded.  0 Error(s)     # and no warnings
```

## 3. The property this proves, which is the point

The façade contains **exactly** the members the last real build used and
nothing more. So a compile against it can only succeed if the current
source uses no RimWorld API beyond that set.

It succeeded. Therefore:

> **The wiring added in `docs/85` — the schema bump, the encoded
> economy state, the budgeted scheduler advance, the mid-day resume,
> the two new tab rows — introduces no new RimWorld API dependency.**

Every RimWorld member the current code touches is one that a real build
against real assemblies already resolved. The remaining risk of a
signature mismatch is therefore not "somewhere in the game-facing code";
it is confined to members that have already worked once. That is a much
smaller and much better-characterised risk than "unbuilt".

It also says something about the shape of the change: the new behaviour
is carried by `Economy.Core`, which has no RimWorld reference at all and
is verified to the bit, and the game-facing layer stayed a thin adapter.
That was the intent of keeping the codec and the scheduler free of
`Verse`, and this is the evidence that it held.

## 4. What is still not verified, and it is now small

1. **A build against the real assemblies.** The façade's member *shapes*
   were inferred from reference tables, which record names and signatures
   but which this document read as names plus argument shapes. A real
   build is still the authority and is still the first thing to do at the
   game.
2. **Everything in-game**: the co-load, the tab rendering, a save and a
   reload with the determinism row reading `reproduced N/N`, a mid-day
   save resuming at its cursor, a schema-2 save loading clean.
3. **The tick budget.** `PhasesPerTick` is 1 and is a guess (`docs/83`
   §5). A frame graph, not an argument.

Item 1 shrank; items 2 and 3 are unchanged and are observations.

## 5. A note on the façade's upkeep

If someone adds a call to a RimWorld member the mod has not used before,
this build **fails** — the façade will not have it. That is the correct
behaviour and it is the façade's second purpose: it makes growth in the
RimWorld API surface visible and deliberate, in a project whose Stage 1
posture is deliberately minimal (no Harmony, no gameplay mutation, no
`Rand`). Adding the member to the façade is a one-line change and a
moment's thought about whether the surface should grow.

## 6. Cost

One `apt-get`, two `monodis` invocations, a 170-line façade transcribed
from their output, one project file, and one build.
