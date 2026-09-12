# Stage 1: amortising the day across ticks: results

`docs/82` is the design. `DayScheduler` is built, compiled and measured.
Every prediction held.

**The headline: a real day of ported phases produces bit-identical state
whether it runs in one tick or is spread across eight, and whether or
not it is interrupted by a save at any point in the day. The invariant
`docs/82` §2 set — spreading the day must not change the day — holds at
every budget and every cursor.**

## 1. What was measured

A day built from four real ported phases over real fixture state:

```
phases in the day: 4  (bargain, wagecost, settle, prices)
```

- `bargain` — `BargainingSolver.Step` over both regions (docs/74)
- `wagecost` — `WageCostSolver.UpdateWageCosts` (docs/79)
- `settle` — `WageSolver.Settle` over both regions (docs/72)
- `prices` — `PriceSolver.UpdatePrices` (docs/77)

The state is drawn from four committed fixtures chosen so nothing is
neutral: the shortage economy for prices, the wage-deviation economy for
the settlement, the habituating boom for bargaining, and Department I's
circuit for the wage costs. Each run rebuilds the state from the
fixtures, so the runs are independent rather than sequential.

The comparison is a **fingerprint of bit patterns** — every price, both
bargaining magnitudes per region, every producer's wage cost, and the
settlement's employment, wage bill and purse — against the same day run
whole, which is what the shell does today.

## 2. Held: 5.1 and 5.2

```
budgets tried: 8, state mismatches: 0, order mismatches: 0
```

Every budget from one phase per tick to eight — more than the day has —
produces the identical fingerprint **and** the identical phase sequence.
5.2 is worth having tested separately from 5.1: a scheduler could reach
the right end state by a different route, and a different route is a
different thing to debug when a phase is added later.

## 3. Held: 5.3, the save case

```
interrupt-and-resume points: 5, mismatches: 0
```

The day was stopped after 0, 1, 2, 3 and 4 phases, the cursor read as a
save would read it, a **fresh scheduler** built as a load would build
one, `ResumeAt` called with the saved cursor, and the day finished. All
five produce the uninterrupted day's fingerprint.

That is the case the cursor is persisted for, and the reason it matters
is concrete: `settle` pays a wage bill. A resumed day that re-ran it
would pay twice, and a resumed day that skipped it would not pay at all
— neither is a rounding error, and both would be invisible until a
ledger identity failed much later.

## 4. Held: 5.4

The laboratory is unmoved: 322 metrics at zero delta. Nothing in
`economy_lab/` was touched by this slice at all.

## 5. What the design got right, and what it deferred

The decision that made this testable was `docs/82` §3's last rule: **the
scheduler decides only when to stop, never what to do next.** The budget
is a phase count here rather than a duration, so every budget can be
tried exhaustively; the game side converts wall-clock into a count
before calling, which keeps the clock out of the deterministic part.
A scheduler that consulted the clock inside its own loop could not have
been tested this way at all.

What is deferred is exactly what `docs/82` §7 said: the budget's real
value, the stall it exists to prevent, and the catch-up after a load all
need the game and a profiler. This slice establishes that amortising is
*safe*, not that any particular amortisation is *enough*.

One thing measurement cannot settle and the design named: if a single
phase is too expensive for one tick — the value solve at 647 commodities
is the candidate, 4 ms by `docs/54` — that shows up as one long tick
rather than a wrong answer, and it needs its own treatment. Nothing here
prevents it and nothing here hides it.

## 6. Where Phase C stands

| part | state |
|---|---|
| the planned model's arithmetic, five slices | ported and exact, 4,151 readings |
| the persistence codec | built and exact, 2,078 values |
| the day scheduler | built, invariant holds at every budget |
| wiring codec and scheduler into `EconomyWorldComponent` | **needs the game** |
| the UI | **needs the game** |
| the `MarketValue` wealth coupling | **needs the game** |

Everything in the top half has no RimWorld reference, which is what let
it be measured. Everything in the bottom half terminates in an
observation — a save file reloading, a tab rendering, a raid arriving —
that cannot be made from outside a running game.

## 7. Cost

One C# file, one harness running thirteen days' worth of work (eight
budgets and five resume points), and this document. Under a minute of
machine time.
