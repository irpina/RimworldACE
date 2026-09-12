# Driving the component against a fake host: design

Written before implementation. `docs/89` §5 left three things, and
said of them that verifying the in-game ones "means watching a program
run in a game I cannot launch". That is true of RimWorld. It is not
true of **the mod's own logic**, and the distinction is worth one more
slice.

## 1. What is actually untested

The game-facing code now compiles against a ground-truth façade
(`docs/87`). Compiling is not running. Nothing has ever *executed*:

- the schema-3 upgrade path, and what a pre-schema-3 save does to it;
- the mid-day cursor being written, read back, and resumed at;
- the self-check's verdicts on a fresh world versus a loaded one;
- the scheduler being driven by `WorldComponentTick` across many ticks;
- the phase timing feeding `TickBudget`.

Every one of those is a branch in code this session wrote, and every one
is currently believed rather than observed. `docs/89` §4 already found a
bug in that code by *reasoning* — the self-check re-run reporting skips
as failures on a fresh world. Reasoning found one; running finds the
ones reasoning misses.

## 2. What a fake host can and cannot show

RimWorld's contribution to these paths is small and mechanical: a tick
counter, a `Scribe` that stores a value under a label and hands it back,
and a world that lists settlements. None of that is *interesting* — it
is plumbing the mod reads and writes through.

So the façade gains behaviour: a `Scribe` that really stores, a tick
counter that really advances, and a switch for the load mode. Then the
component can be driven through the sequence a session at the game would
drive it through, **in a test**, and its self-check read back.

What this cannot show, stated plainly so the results document cannot
overclaim:

- that RimWorld's real `Scribe` behaves like the fake one;
- that `FinalizeInit` is called when the fake harness calls it, or with
  the argument the harness passes;
- anything about rendering, the tab, or the game loading the assembly.

It shows that **the mod's own state machine is correct given a host that
behaves as documented.** That is the half of the remaining risk that is
the mod's fault if it is wrong.

## 3. What is built

```
economy_mod/Source/Economy.Facade/FakeHost.cs
```

Behaviour for the façade: a `Scribe` store keyed by label, a settable
tick counter, a load-mode switch, and a reset between scenarios. The
signature mirror in `RimWorldFacade.cs` stays a mirror; the behaviour
sits beside it, and neither ships.

And a harness that drives four scenarios:

| scenario | what it must show |
|---|---|
| fresh world | self-check runs, load-only checks **skip** rather than fail |
| a day passes | the scheduler advances, the day completes, timing is recorded |
| save and reload | the cursor and schema survive; the reloaded component resumes |
| a pre-schema-3 save | loads clean with no economy state, and says so |

## 4. Predictions

4.1 A fresh world's self-check **runs and passes**, with the three
load-only checks recorded as `Skipped` — not `Passed`, which is
`docs/88` §5.2's distinction, and not `Failed`, which is the bug
`docs/89` §4 fixed by reasoning and this would have caught.

4.2 Ticking past a day boundary completes a day: `CompletedDays`
increments, the cursor returns to 0, and `phaseMillis` is non-empty so
the budget line stops reading "no day has run yet".

4.3 A save and reload round-trips the schema and the cursor through the
fake `Scribe`, and the reloaded component's self-check reports the
determinism and resume checks as **run** rather than skipped.

4.4 A component loaded from a save whose `schemaVersion` is 2 ends with
schema 3, **empty** economy state, a zero cursor, and the "old save
loads clean" check passing — not skipped, because that case did apply.

4.5 The laboratory is unmoved: 322 metrics at zero delta.

## 5. What would make this wrong

If 4.1 shows the load-only checks as `Passed`, the fresh-world path is
claiming results it does not have, which is the failure mode
`docs/88` §5.2 was written against.

If 4.4 ends with economy state present, the schema guard does not fire
and a pre-schema-3 save would be read as though it carried state — the
"catastrophic rather than wrong-by-a-ulp" case `docs/80` §2 named.

If driving many ticks never completes a day, the `WorldComponentTick`
restructure is wrong in a way the compile could not show, which is
exactly what this slice exists to find.

## 6. Cost

One file of fake behaviour, one harness, four scenarios. No new
fixtures and no game.
