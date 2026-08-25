# The scale test: design

Written before implementation. This is not an economics feature — it is the
risk `HANDOFF.md` has listed as "the cheapest large risk to retire" through
three consecutive roadmaps and deferred each time. `docs/31` §9 says this is
the place to stop and do it.

## 1. The question

The laboratory is **six commodities and two regions**. RimWorld is **653
producible defs** and roughly **100 settlements**. Three solvers now iterate
to fixed points every day — labor values, the production-order plan, and (on
demand) prices of production — and nobody has checked whether any of it
survives a hundredfold more entities.

Two failure modes, and they need separating:

- **Cost.** Does a simulated day fit in a budget a mod can actually spend?
- **Calibration.** Do the guarantees — ledgers closing, determinism, the
  exactly stationary equilibrium — survive a graph that is wide rather than
  four nodes?

## 2. What the real population looks like

From `out/embodied_labor.csv`, the closed analysis's solve for 653 defs:

| property | value |
|---|---|
| commodities | 653 |
| **depth 0 / 1 / 2 / 3** | **163 / 252 / 159 / 79** |
| embodied labor | 0 to 404,812 ticks; median 5,040 |
| market value | 0.50 to 5,440 silver; median 121.60 |
| largest categories | 104 meats, 92 buildings, 61 furniture |

**The graph is wide and shallow: maximum depth 3.** That is the single most
important fact for this test, and it was not obvious in advance. Every
iterative solver in the model converges by propagating along the input graph,
so a depth-3 graph converges in a handful of passes no matter how wide it
gets. **Iteration counts should be roughly constant in N; the cost will be
per-iteration work.**

## 3. The generator

`economy_lab/scale.py` builds an economy of arbitrary size from that real
population rather than from invented numbers:

- **Commodities** are taken from the CSV in order — name, embodied labor,
  market value — so the magnitudes and their spread are RimWorld's.
- **Inputs** are synthetic but shape-preserving: a commodity at depth *d*
  draws one to four inputs from depth *d − 1*, chosen by a seeded PRNG.
  The real `costList` graph is not in the committed data; reconstructing it
  needs the game's XML, and the scale question is about *shape and size*,
  not about which specific def feeds which.
- **Direct labor** is the def's embodied labor minus what its inputs carry,
  floored at a small positive value, so the labor solve has something
  non-degenerate to find and the values stay in the observed range.
- **Regions** are replicas with per-region cost jitter, on a **sparse route
  network** — each region connected to a handful of neighbours, because 100
  fully-connected settlements is 4,950 routes and RimWorld's world map is
  not a clique.
- **Capacity and inventory** are seeded from derived demand, the same rule
  `_region` uses.

The generator is deterministic given its seed. That is testable and will be
tested: a scale harness whose output wanders is not a measurement.

### What the generator does not promise

An **exactly stationary** equilibrium. The seeded circuit's exactness rests
on a hand-tuned calibration (`docs/17` §7) that does not generalize to 653
arbitrary commodities, and forcing it would turn this into a calibration
session. The generator aims for a *running, closing, deterministic* economy;
§6 tests what actually survives and the results document reports honestly
which guarantees are size-dependent.

## 4. The budget, stated before measuring

A criterion nobody can move afterwards.

RimWorld runs 60 ticks a second and an in-game day is 60,000 ticks — about
sixteen minutes of real time at 1× speed. So a daily economy update has an
enormous wall-clock window *provided it is amortized* across ticks, and the
binding constraints are different from a naive "must be fast" reading:

| constraint | budget | why |
|---|---|---|
| CPU per simulated day | **< 50 ms** | spreadable over a few hundred ticks without a visible hitch |
| CPU per single tick | < 1 ms | anything more is a stutter |
| resident economy state | **< 50 MB** | a save file and a running colony have to share |

The 50 ms figure is deliberately generous. If the model misses it by an order
of magnitude the verdict is unambiguous; if it misses by 20% the verdict is
"tune it", which is a different session.

## 5. What gets measured

At sizes (commodities × regions) of 6×2, 64×2, 653×2, 653×10, 653×100:

1. wall-clock per simulated day, and its breakdown by phase — production,
   the labor value solve, price update, arbitrage, investment, history;
2. iteration counts for each fixed point, against depth and width;
3. peak resident memory, and the share of it that is `Economy.history`;
4. whether all three ledgers still close;
5. whether identical inputs still give bit-identical histories;
6. construction cost, separately, because the seeding solvers run there.

## 6. Tests

1. The generator is deterministic: same seed, bit-identical history.
2. A generated economy closes its material, silver and value ledgers.
3. The labor value solve converges, and its iteration count does not grow
   with width at fixed depth.
4. A generated economy runs a hundred days without a producer going negative
   or a price hitting a bound.
5. The existing six-commodity scenarios are **bit-identical** before and
   after anything this session touches.

## 7. Predictions

Read off the code before running it.

**7.1 Two O(C × P) recomputations dominate, both structural.**

`_planned_runs` calls `region.throughput_demand(name)` for every commodity on
every iteration of its fixed point, and `throughput_demand` itself sums
`input_per_day` over every producer. That is `commodities × producers` per
iteration.

`_record_history` calls `region.capacity(name)` for every commodity every
day, and `capacity` also sums over every producer. Same product, once a day.

Neither is an algorithmic problem. Both quantities change only when capacity
or activity changes, which is on investment completion — not within a day,
and certainly not within an iteration of a fixed point.

**7.2 Memory is the first hard wall, and `history` is all of it.** Every day
stores, per region, four full commodity dicts plus a computed capacity dict.
At 653 commodities × 100 regions × 240 days that is on the order of **10⁸
stored floats — several gigabytes.** The predicted failure is an out-of-memory
kill or thrashing, before any interesting economics happens.

**7.3 Iteration counts stay flat.** Depth 3 means the plan cascade and the
value solve settle in about five passes at any width. If iteration counts
grow with N, the graph generator has produced cycles the real data does not
have, and that is a bug in the harness rather than a finding about the model.

**7.4 Predicted costs**, at roughly 2 × 10⁷ inner dict operations per second
for CPython:

| size | predicted per-day | verdict |
|---|---|---|
| 6 × 2 (today) | ~0.3 ms | fine |
| 653 × 2 | **1–3 s** | 20–60× over budget |
| 653 × 100 | **50–150 s** | 1000–3000× over budget |

At 653 × 100 a 240-day run is three to ten hours. **The model does not
survive scale as written**, and §7.1 says the reason is two lines rather than
an architecture.

**7.5 Arbitrage is not the problem, given a sparse map.** It is
`routes × commodities` per day, which at ~300 routes and 653 commodities is
under 200,000 operations — real, but two orders below §7.1. It *would* be the
problem on a fully-connected map (4,950 routes), which is an argument about
the route generator rather than about the model.

**7.6 The ledgers close and determinism holds.** These are exact accounting
properties with no size dependence. If either fails at scale it means a
dictionary-ordering or float-accumulation dependence that the two-region
scenarios were too small to expose, which would be a much more interesting
result than the timings.

**7.7 The exact stationary equilibrium will not generalize**, and this
document does not treat that as a failure. It is a property of a hand-tuned
six-commodity calibration; the generated economy is expected to wander and
settle rather than sit still from day zero.

## 8. What happens after the measurement

If §7.1 and §7.2 hold, the fixes are named already: cache the two derived
quantities per region and invalidate them where capacity changes, and make
history opt-in or sampled. Both are mechanical.

The rule for doing them in this session: **no behavioral change.** The frozen
reference must not move by a digit and the six-commodity equilibrium must
stay exactly stationary. A cache that changes an answer is a bug, not an
optimization, and the existing 138 tests plus the 149-metric reference are
the instrument that says which it is.

If the measurement names something *else* as dominant, the fix waits for its
own design document. Optimizing what the profiler did not accuse is how a
laboratory acquires code nobody can explain.

## 9. Non-goals

- Porting anything to C#. This measures the Python model to find out what the
  port would have to avoid.
- Reconstructing RimWorld's real `costList` graph. Shape and size are the
  question; identity is not.
- Making the generated economy exactly stationary.
- Any economics. No new mechanism, no new ledger quantity, no new scenario
  in the frozen reference beyond the timings themselves.
