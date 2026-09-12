# Stage 1: amortising the day across ticks: design

Written before implementation. `HANDOFF.md` lists this as a Phase C
constraint that is *measured rather than guessed*: about 1.1 s of C#
work per simulated day at full scale, against a day that is 60,000
ticks. The current shell does the whole day in one tick
(`EconomyWorldComponent.WorldComponentTick`'s `while` loop), which at
full scale is a 1.1-second freeze once a day.

## 1. What the problem actually is

Not throughput — `docs/33` settled that: cost is linear in commodities
and regions, and a C# port at a conservative 20× lands the whole day
under 20 µs at laboratory scale. The problem is that the work arrives
**all at once**. RimWorld runs 60 ticks a second at 1×; a day's work
landing in one of them is a visible stall however cheap the day is in
total.

So the day has to be spread. And spreading it must not change it,
which is the part worth designing rather than coding.

## 2. The invariant

> **A day spread over any number of ticks produces exactly the state
> that day produces in one tick.**

Not "approximately" and not "within tolerance" — the same bits. Every
result this project has is a bit-level claim, and an amortiser that
perturbed the last bit would silently unpick all of them.

That invariant has a consequence that decides the design: **the
amortiser may only break between phases, never inside one.** A phase is
an atomic unit of the day — the value solve, the price update, the wage
settlement — and phases are ordered. Breaking inside a phase would let
a later tick read state the phase is halfway through writing, and
ordering between phases is what the laboratory's own day already
guarantees.

This is a weaker form of amortisation than splitting arbitrarily, and
it is the only one that preserves the invariant without reasoning about
every phase's internals. If one phase is itself too expensive to fit a
tick — the value solve at 647 commodities is the candidate, at 4 ms
(`docs/54`) — that is a separate problem, visible as a single long
tick rather than as a wrong answer, and it gets its own treatment if
measurement says it needs one.

## 3. The rules

**One day at a time.** The scheduler never begins day N+1 before day N
is finished. If the game skips ticks — a load, a speed change, a lag
spike — the catch-up runs whole days, and it runs them to completion.

**The cursor is state.** Which phase runs next is part of the economy's
saved state, because a save can land mid-day. It therefore goes through
`StateCodec` (`docs/81`) like everything else, and a save written
mid-day resumes mid-day rather than re-running phases already applied
or skipping phases not yet applied. Re-running a phase is not harmless:
`_settle_labor` pays a wage bill.

**A budget, not a fixed split.** Each tick the scheduler runs phases
until it has used its budget, so a cheap day finishes in one tick and
an expensive one takes many. A fixed "one phase per tick" would make a
six-phase day take six ticks whether or not it needed to, and would
scale wrongly when phases are added.

**Deterministic regardless of budget.** The budget may vary — it is
wall-clock — so the *order and content* of the work must not depend on
it. The scheduler decides only *when* to stop, never *what* to do next.
That is what makes §2's invariant testable: run the same day at every
budget from one phase per tick to all of them, and compare.

## 4. What is built

```
economy_mod/Source/Economy.Core/DayScheduler.cs
```

No RimWorld reference, so the invariant can be measured here:

- `IDayPhase` — a name and an `Execute()`;
- `DayScheduler` — an ordered phase list, a cursor, `AdvanceTick(budget)`
  and `RunWholeDay()`;
- the cursor exposed for `StateCodec` and restored from it.

The `WorldComponentTick` side — reading the real clock, choosing a
budget, and the catch-up loop — is a later step and needs the game.

## 5. Predictions

5.1 **The invariant holds for every budget.** A day of real phases —
the ported price update, wage settlement, bargaining and wage-cost
refresh, over real fixture state — produces bit-identical results run
whole, run one phase per tick, and run at every budget between. Zero
ulps, every field, every budget.

5.2 **The phase sequence is identical too**, not only the end state: the
order phases execute in does not vary with the budget.

5.3 A day interrupted at each possible cursor position and resumed
produces the same state as the uninterrupted day — which is the save
case, and the reason the cursor is persisted.

5.4 The laboratory is unmoved: 322 metrics at zero delta.

## 6. What would make this wrong

If 5.1 fails at some budget, a phase is not atomic — it is reading
something a previous phase left half-written — and the fix is in the
phase boundary, not the scheduler.

If 5.3 fails, the cursor does not capture everything a resumed day
needs, which would mean a phase carries state between phases outside
the snapshot. That is the failure the reload-determinism check in
`EconomyWorldComponent` exists to catch in the game, and catching it
here first is cheaper.

If the real day turns out to have phases that cannot be made atomic —
a fixed point that spans the market and the plan, say — then the
invariant cannot be had at phase granularity and the design needs
re-opening rather than weakening the invariant.

## 7. What this still cannot verify

The budget in ticks, the stall it is meant to prevent, and the catch-up
behaviour after a load all need the game running and a profiler. This
builds the part where *correctness* lives and leaves the part where
*performance* lives, which is the right division: a scheduler that is
fast and wrong is worse than one that is correct and needs tuning.

## 8. Cost

One C# file of about a hundred lines, a harness that runs a real day at
every budget, and three tests. No new fixtures.
