# Driving the component against a fake host: results

`docs/90` is the design. The façade gained behaviour, the component was
driven through five scenarios, and **running found three defects that
compiling and reasoning had both missed.**

```
checks 28, failures 0
THE COMPONENT'S STATE MACHINE IS CORRECT AGAINST A DOCUMENTED HOST
```

## 1. What was driven

A fake host — a `Scribe` that really stores under a label, a tick
counter that really advances, a world with twelve settlements on real
tiles — and the component taken through:

1. a fresh world: `FinalizeInit(false)`;
2. 60,010 ticks, crossing a day boundary;
3. a save, and a reload into a *new* component instance;
4. a save taken mid-day, and a reload resuming at its cursor;
5. a save poked back to `schemaVersion = 2` with economy state and a
   cursor in it, loaded.

All through the real public entry points — `FinalizeInit`,
`WorldComponentTick`, `ExposeData`. Reflection reads private fields for
assertions only.

## 2. Held: every prediction

**4.1** A fresh world runs its checks, passes, and records the three
load-only checks as `Skipped` — not `Passed` and not `Failed`.

**4.2** Ticking past 60,000 completes a day: `CompletedDays` increments,
the cursor returns to 0, timing is recorded, and the budget line stops
reading "no day has run yet" — it now reads
`recommend PhasesPerTick=1 for a 2 ms budget; day total 0.258 ms`.

**4.3** Schema and cursor round-trip the fake `Scribe`; a reloaded
component reports `reproduced 12/12 on reload` and passes.

**4.4** A schema-2 save ends at schema 3 with **empty** economy state, a
zero cursor, and the old-save check passing.

**4.5** The laboratory is unmoved: 322 metrics at zero delta.

## 3. The three defects, and what each says

`docs/90` §1 predicted that "reasoning found one; running finds the ones
reasoning misses". It found three, all in the self-check rather than in
the state machine, and all the *same error in different clothes*:
**reporting a failure for a case that does not apply.**

**One. An upgraded save was reported as a failed resume.** The check
compared the cursor the save carried (7) against the cursor after load
(0) — but a schema-2 upgrade *deliberately* resets the cursor, so the
correct behaviour was being reported as a bug. It now checks that an
upgraded save resumed at 0, and says why.

**Two. A save with no profiles was reported as a determinism failure.**
`CompareWithLoaded` returns "nothing saved to compare" when there is
nothing to compare, which is a case the check does not apply to. It
skips now.

**Three. A perfect reload was reported as a failure.** The expectation
was `"reproduced 12/12"`; the actual sentence is
`"reproduced 12/12 on reload"`. A string comparison against a sentence
spelled out in two places, which is exactly the kind of thing that is
invisible until something runs.

The third is the most instructive, because it is the one that would have
reached the game. A person following `docs/89`'s "read the log" would
have seen `FAIL reload determinism` on a reload that was perfect, and
reasonably concluded the mod was broken. **A self-check that cries wolf
is worse than no self-check**, and the only thing that catches it is
exercising it.

The first two are the same distinction `docs/88` §5.2 drew between "no
checks ran" and "all checks passed", and that `docs/89` §4 already fixed
once at a different level. Three instances now. The general form is
worth stating: **a check has three outcomes, not two, and deciding
which of them applies is as much of the logic as the comparison is.**

## 4. What this does and does not establish

It establishes that the component's state machine — schema upgrade,
cursor persistence and resumption, day completion, phase timing,
self-check verdicts — is correct against a host that behaves as
documented, and that the report it will print is accurate rather than
alarming.

It establishes nothing about RimWorld: not that the real `Scribe`
behaves like this one, not when `FinalizeInit` is really called, not
that the assembly loads, and nothing whatever about the tab rendering.
`docs/90` §2 said so in advance and it is repeated here so the summary
cannot drift.

What it does change is the expected *content* of the in-game session. A
person now runs a mod whose reports have been seen to be right when
things are right — so a `FAIL` in the game's log is evidence about
RimWorld rather than a coin-flip between a real problem and a
mis-worded check.

## 5. Phase C

| component | state |
|---|---|
| five arithmetic slices | ported, 4,151 readings, zero ulps |
| persistence, scheduler, wealth coupling | built and property-tested |
| `Economy.Core` for `net472` | builds clean, artifact bit-exact under Mono |
| the check harness | has run, every fixture exact |
| game-facing wiring | builds against ground truth, **and now runs** — 28 assertions |
| the self-check | built, exercised, three defects fixed |

Two things remain and neither is code:

1. **A build against RimWorld's real assemblies.** Game files this
   environment does not have and should not.
2. **The game.** Start it, save, reload, load an old save, paste three
   reports.

## 6. Cost

Behaviour added to the façade, a fake world of twelve settlements, a
five-scenario harness, three defects found and fixed, and this document.
