# Turning the in-game checks into measurements: results

`docs/88` is the design. `SelfCheck`, `TickBudget` and the game-side
wiring are built. Every prediction held.

```
checks 103, failures 0
SELF-CHECK AND BUDGET SOUND
```

## 1. What the game will print

The report the mod now writes on load, and again once a day has been
timed — this is a rendering of the real types, from the real
`net472` binary, with a plausible set of observations:

```
[Social Production: Economy] self-check: all 5 checks passed
  PASS save schema: expected 3, observed 3
  PASS reload determinism: expected 106/106, observed 106/106
  PASS mid-day resume: expected phase 3 of 4, observed phase 3 of 4
  PASS schema-2 save: expected no economy state, observed no economy state
  PASS tick budget: expected measured, observed recommend PhasesPerTick=4
       for a 2 ms budget; day total 0.2 ms, worst phase 0.05 ms
```

That replaces five things a person had to remember to look at with one
block to copy. It is reproducible, it is precise, and — the part that
matters — **it can fail in a way that someone who was not there can
read.**

## 2. Held: 5.1 and 5.2

Rendering is deterministic and in insertion order, not a dictionary's:
the same checks render the same text, twice in a row and across two
independently built reports.

**An empty report is not a pass**, and neither is an all-skipped one.
`Passed` requires `Ran > 0 && Failures == 0`, and the summary of an
empty report says `NO CHECKS RAN` rather than something reassuring.
This was the prediction worth writing down — "no checks ran" has been
mistaken for "all checks passed" in every test suite ever written, and
a self-check that reported a pass when the mod failed to reach its own
checks would be worse than no self-check at all.

## 3. Held: 5.3 and 5.4

`TickBudget.Recommend` was run over 7 timing sets × 6 budgets,
including NaN durations, infinities, negatives, a zero budget, a
negative budget and 1e9. It is **always** between 1 and the phase
count. One a tick is the floor because a scheduler that runs zero
phases never finishes a day; the phase count is the ceiling because
there is nothing else to run.

Comfortable timings recommend the whole day at once. An oversized phase
still returns 1 **and** `BudgetUnreachable` reports it, and the
description says so in words:

```
NO SINGLE PHASE FITS -- a phase is atomic and cannot be split
```

That is the case `docs/82` §2 named and could not measure: a phase is
atomic by design, so when one exceeds the frame budget no scheduler can
help, and the honest thing is to say it rather than to slice something
that must not be sliced.

**5.5** The laboratory is unmoved: 322 metrics at zero delta.

## 4. The wiring, and a bug the design's own reasoning caught

`EconomyWorldComponent` now runs the checks at `FinalizeInit`, logs the
report, times each tick's phases with a `Stopwatch`, and re-runs the
checks once a day has been timed so the budget line carries a
measurement instead of `no day has run yet`. The tab shows the summary
and points at the log.

The first version re-ran the checks as `RunSelfCheck(true)` — as if
loaded — and on a **fresh** world that would have reported the
load-only checks as *failures* rather than skips. The world now
remembers how it started. It is the same distinction `docs/88` §5.2
made one level down: a case that does not apply is a skip, and
reporting it as a failure is as wrong as reporting it as a pass.

The clock lives in the component and not in the scheduler, which
`docs/82` §3 requires and which this is the first code to actually
depend on: `AdvanceTick` is timed from outside, so the deterministic
part never sees a duration.

Everything compiles `net472` against the ground-truth façade
(`docs/87`), 0 errors and 0 warnings — so this wiring, like the last,
**uses no RimWorld API the previous real build did not already
resolve.**

## 5. Phase C, and what one session at the game now costs

| component | state |
|---|---|
| five arithmetic slices | ported, 4,151 readings, zero ulps |
| persistence (`StateCodec`) | 2,078 values exact |
| day scheduler (`DayScheduler`) | invariant holds, 8 budgets, 5 save points |
| wealth coupling (`WealthCoupling`) | 2,526 property checks |
| `Economy.Core` for `net472` | builds clean; artifact bit-exact under Mono |
| the check harness | **has run**, every fixture exact on .NET 8 |
| game-facing wiring | builds `net472` against ground truth, adds no new RimWorld API |
| the self-check | built, 103 checks, and it is what the game will report |

What is left is one sitting, and it is now nearly mechanical:

1. Build `Economy.csproj` against RimWorld's real assemblies.
2. Start the game with both mods. **Read the log.**
3. Save, reload. **Read the log.**
4. Load a pre-schema-3 save. **Read the log.**
5. Paste the three reports.

Step 5 is the deliverable, and it is a machine's output rather than a
person's impression. If a check fails it names what it expected, what it
saw, and why the difference matters. If `PhasesPerTick` is wrong, the
budget line says what it should be.

## 6. What is still true

None of this runs the game, and no amount of it can. If the mod fails to
load, no self-check inside it will say so — that is an assembly error in
the log, as it always was. What has changed is everything after loading.

## 7. Cost

Two C# files, a 103-check harness over the degenerate cases, the
game-side wiring, and one bug found by taking the design's own
distinction seriously a second time.
