# Turning the in-game checks into measurements: design

Written before implementation. Three items of Phase C remain and all
three are blocked the same way: they need a running game. This document
does not remove that. It changes what the running game has to produce.

## 1. The problem with "a human checks it"

`docs/87` §4 leaves three things:

1. a build against RimWorld's real assemblies;
2. the co-load, the tab, save and reload, a mid-day resume, an old save;
3. the tick budget, which is a guess.

Item 1 is a build; it either succeeds or names an error. Items 2 and 3
are currently **observations**: a person loads a game, looks at a tab,
and reports an impression. That is weak in three specific ways.

- **It is not reproducible.** "The tab looked right" cannot be
  re-checked later or compared against the next build.
- **It is not precise.** "Reload determinism said reproduced" is a
  different claim from "reproduced 106/106, cursor resumed at phase 3,
  schema was 3 on save and 3 on load".
- **It cannot fail usefully.** A person who does not know the mid-day
  resume exists will not notice that it did not happen.

Every other claim in this project is a machine-produced number that a
later run can contradict. These three are the only ones that are not,
and they are the last three.

## 2. The rule

**The game should produce the evidence, not the person.**

The mod runs its own checks, on load and on demand, and writes a
structured report. The human's job becomes "start the game, paste the
report" — mechanical, reproducible, and checkable by someone who was not
there.

And the report's *logic* does not need the game. A check is a name, an
expectation, an observation and a verdict; rendering a set of them is
string formatting. Both belong in `Economy.Core`, where they can be
tested here, leaving the game side to supply observations and print the
result.

## 3. The tick budget, specifically

`PhasesPerTick` is 1 because a guess was needed (`docs/83` §5). The
honest way to set it is to measure: time each phase in the game, and
choose the count that fits a frame budget.

That arithmetic is also not game-specific. Given per-phase durations and
a target budget in milliseconds, "how many phases fit" is a function.
The game supplies a stopwatch; the function decides; and the
recommendation goes in the report so the next build can use a measured
number instead of a guess.

This does not make the profiling happen here. It makes the profiling
*produce a number the project can act on* rather than an impression
someone has to translate.

## 4. What is built

```
economy_mod/Source/Economy.Core/
    SelfCheck.cs      a check, a report, and the rendering
    TickBudget.cs     per-phase timings -> a recommended PhasesPerTick
```

No RimWorld reference in either. The game side —
`EconomyWorldComponent` filling in observations and logging the report,
the tab showing its summary — is thin by construction and is covered by
`docs/87`'s façade build.

## 5. Predictions

5.1 The report renders deterministically: same checks in, same text out,
with a stable order that does not depend on a dictionary's iteration.

5.2 A report with any failing check reports itself as failed, and one
with none reports as passed; an **empty** report is *not* a pass, because
"no checks ran" and "all checks passed" are different and the first has
been mistaken for the second in every test suite ever written.

5.3 `TickBudget.Recommend` never returns less than 1 — a scheduler that
runs zero phases a tick never finishes a day — and never more than the
phase count. It degrades sanely on nonsense: a zero or negative budget,
a NaN duration, an empty timing set.

5.4 Given timings that comfortably fit, it recommends running the whole
day at once; given timings where one phase alone exceeds the budget, it
still returns 1 and the report says the budget cannot be met, because a
phase is atomic (`docs/82` §2) and no scheduler can split it.

5.5 The laboratory is unmoved: 322 metrics at zero delta.

## 6. What this still does not do

It does not run the game. A person still has to start RimWorld, and if
the mod fails to load, no self-check inside it will say so — that
failure shows up in the log as an assembly error, as it always has.

What changes is everything after loading: instead of five things to
remember to look at, there is one report to copy, and it is wrong in a
way that can be read by someone who was not there.

## 7. Cost

Two C# files of about a hundred lines each, a harness over the
degenerate cases, and the thin game-side wiring.
