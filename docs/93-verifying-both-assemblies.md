# Verifying both assemblies, and catching a stale one

Design and results in one. `HANDOFF.md` has said since `docs/54` that
loading `Economy.Core` in the game "changes `verify.py`'s expected
surface", and nothing had changed it. This does, and finds two things
on the way.

## 1. What `verify.py` was missing

`economy_mod/Source/verify.py` checks the *built assembly* the way
Labor Content's does: the four types the defs name exist, `Rand` and
Harmony are absent, no gameplay-writing API is on the binding surface,
and the surface is exactly 30 expected symbols. It is a good check and
it had two holes.

**It did not know there is a second assembly.** The mod now ships
`SocialProduction.Economy.Core.dll` beside its own, and that is where
all of this session's behaviour lives. Nothing verified it at all.

**The port's central claim had never been machine-checked.** Since
`docs/53` §2 the claim has been that `Economy.Core` has **no RimWorld
and no Unity in it** — that is what lets it be tested on a build
machine, and it is what `docs/76` and `docs/92` rest on. It was true by
inspection, and by the fact that it compiles without the game's
assemblies. Neither is a check a RimWorld update cannot quietly
falsify.

## 2. What was added

`core_failures()` reads the ported model's assembly and requires:

- the eleven types the mod and the harnesses name are defined;
- **no reference whose namespace starts with `RimWorld`, `Verse` or
  `UnityEngine`** — the claim, checked against the binary;
- none of the forbidden names (`Rand`, Harmony, the trade and stat APIs).

It reports the assembly as *absent* rather than broken when it has not
been built, so a checkout that has only run the Python side is not
called broken.

The first run failed, correctly, on the list I had written: the type is
`SelfCheckReport`, not `SelfCheck`, and I had left out `TickBudget` and
`CompensatedSum`. A required-types list that is wrong is worth having
because it fails loudly on the first run; one that is merely
approximate would have passed and checked nothing.

With the list right:

```
verified: 4 types present, nothing rolled, nothing patched,
binding surface is the 30 expected symbols;
the ported model carries 11 types and no game reference at all
```

## 3. The second hole, and it is the useful one

The mod's behaviour now lives in the ported model, so **an assembly
that does not reference `SocialProduction.Economy.Core` was built before
the wiring landed.** That is a check, and it fires:

```
FAIL: SocialProduction.Economy.dll does not reference the ported model,
      so it was built before the wiring landed: rebuild it
```

Which is true. The committed `SocialProduction.Economy.dll` was built
before this session and is stale.

**Staleness is invisible otherwise.** The old assembly loads fine, the
tab appears, the settlement list works — and none of the new rows are
there, no self-check is logged, and the schema stays at 2. A person
would see a mod that works and quietly has none of the new behaviour,
with nothing anywhere saying why. Now the first command they run says
it in one line.

`verify.py` therefore **fails on a fresh checkout, deliberately**, until
the mod assembly is rebuilt. That is the instruction, not a regression.

## 4. What was committed

`SocialProduction.Economy.Core.dll`, built `net472` in Release by the
real SDK. It has no RimWorld dependency — which is the whole point of
it — so an assembly built here is the assembly a build there would
produce, and `Deterministic` is set in its project file. It saves a
step and `verify.py` checks it.

The mod's own assembly is **not** committed from here and could not be:
it needs RimWorld's managed DLLs.

## 5. Where this leaves Phase C

Two things, unchanged and both needing the game:

1. Build `Economy.csproj` against RimWorld's real assemblies. `verify.py`
   now tells you if you forget.
2. Start the game, save, reload, load an old save, paste the three
   reports.

Everything else is built, verified, repeatable, and — as of this
document — checked at the binary rather than only at the source.

## 6. Cost

One function in `verify.py`, one staleness check, a `pip install pefile`,
and a wrong types list that failed on its first run as it should have.
