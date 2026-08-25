# The scale test: results

Recorded after implementing the design in `docs/32-scale-test-design.md`.

## Headline

The risk three roadmaps deferred is retired, and the answer is better than
the design expected — but for a different reason than it expected.

- **The architecture scales linearly** in commodities and in regions, after
  one method changed. Before it, cost was quadratic in commodities.
- **CPU fails the budget in Python and would pass it in C#.** A simulated day
  at 647 commodities × 100 regions costs **22.3 s**, against a 50 ms budget —
  446× over. But the cost is now linear and amortizable, and RimWorld gives a
  daily update sixteen minutes of wall clock.
- **Memory fails architecturally.** `Economy.history` grows ~16 MiB per
  simulated day at full scale: **3.8 GB over a 240-day run**. That is not a
  language constant and the runtime port cannot keep this design.
- **Every correctness guarantee survived.** Ledgers close, determinism holds,
  and the labor value solve reproduces the closed analysis **exactly for all
  447 commodities** the generator did not contaminate — the `docs/20`
  validation, run at four hundred times the width.
- 147 tests (138 prior + 9), 154 frozen metrics, and **no behavioral metric
  moved**.

## 1. The measurement

`economy_lab/scale.py` builds an economy of arbitrary size from the real def
population — names, embodied labor and market values from
`out/embodied_labor.csv` — with synthetic input edges preserving the observed
depth mix. Three days simulated at each size, on this machine, CPython 3.14.

| commodities | regions | producers | build (s) | **before (s/day)** | **after (s/day)** |
|---:|---:|---:|---:|---:|---:|
| 6 | 2 | 12 | 0.01 | 0.003 | **0.002** |
| 64 | 2 | 128 | 0.03 | 0.043 | **0.037** |
| 647 | 2 | 1,294 | 0.40 | 0.966 | **0.404** |
| 647 | 10 | 6,470 | 1.81 | 4.999 | **2.191** |
| 647 | 100 | 64,700 | 18.29 | ~50 (extrapolated) | **22.31** |

**The scaling law changed, not just the constant.** Before: 10.1× the
commodities cost **22.5×** the time. After: 10.1× the commodities cost
**10.9×** the time. Regions were always linear (10× regions → 10.2× time).

Cost is now **345 µs per producer-day** and that single number describes
every row.

## 2. What was slow, and the one method that fixed it

`docs/32` §7.1 predicted two O(commodities × producers) recomputations. The
profiler found the first and acquitted the second.

```
   ncalls  tottime  cumtime  function
    23292    0.050   11.946  Region.throughput_demand      ← 84% of the run
 15069924    4.304    7.057  Producer.input_per_day
        3    0.007    0.088  Economy._record_history       ← 0.6%
```

`throughput_demand` is O(producers) and was being called once per commodity,
inside a fixed point that iterates about five times — and again by the price
update, by arbitrage per route, and by the investment pass. `_record_history`
recomputes `capacity()` per commodity per day, which is the same product but
**once**, and it is 0.6% of the run rather than a problem.

The fix is one method. `Region.throughput_demands()` walks each producer's
*inputs* instead of scanning every producer for each commodity — O(producers
× inputs) rather than O(commodities × producers) — and `Economy` rebuilds the
map once a day, after `_complete_projects` and before anything reads it.
Capacity cannot move in between, so this is a rebuild rather than a cache
with an invalidation rule to get wrong.

### The equivalence test earned its keep in the first minute

The claim was bit-equality, argued from "the terms accumulate in the same
producer order". The argument was wrong. The first version accumulated with
`+=`, and **CPython's `sum` compensates its floating-point error while a
running total does not**, so the two disagreed in the last bit wherever a
commodity had more than one consumer — 95.16560489431755 against
...757, in `producer_loss` at day 210 with five drug labs drawing on one
psychoid field.

The frozen reference did not notice, because it rounds to six decimals. The
test did. That is the division of labor the two instruments were set up for,
working exactly as intended, and it is the strongest argument in the project
so far for having both.

The fix is to collect the terms and hand them to `sum`, which is what the
original did.

## 3. The remaining bottleneck, named and not touched

After the fix, at 647 × 2:

```
        3    0.239    1.662  Economy._produce
        6    0.175    1.243    Economy._planned_runs
       30    0.488    0.965      Economy._allocate_orders    ← 42%
   191796    0.311    0.311  builtins.id
        3    0.207    0.356  Economy._update_labor_values
```

`_allocate_orders` is now the largest single item. It is **O(commodities)
with a heavy constant** rather than quadratic: for each commodity it sorts
the producer list, builds four dicts keyed by `id(producer)`, and runs a
water-filling loop — about 50 µs per commodity, most of it in per-commodity
setup that a one-producer sector does not need. The 191,796 calls to `id()`
are its bookkeeping.

**It is not being fixed here.** `docs/32` §8 committed to fixing only what
the first measurement accused, on the grounds that chasing each successive
bottleneck without a plan is how a laboratory acquires code nobody can
explain. Hoisting the `id()` keys, skipping the sort for single-producer
sectors, and computing the commodity grouping once per `_planned_runs` call
instead of once per iteration are all safe and all obvious — and they belong
to a session that says so first.

## 4. Memory: the failure that is architectural

| days simulated | peak (MiB), 647 × 10 |
|---:|---:|
| 0 (structure only) | 6.0 |
| 2 | 9.5 |
| 8 | 18.7 |

Growth is **1.6 MiB per simulated day at ten regions**, so ~16 MiB per day at
a hundred, and a 240-day run needs **about 3.8 GB**. The structure itself is
modest — 60 MiB at full scale — and every byte of the growth is
`Economy.history`, which stores four full commodity dictionaries plus a
computed capacity dictionary per region per day.

`docs/32` §7.2 predicted memory would be the *first* hard wall. It is not
first — at 22 s/day nobody reaches day 240 to run out of memory — but it is
the wall that a faster language does not move. A C# port is 20–50× faster per
operation; it is not 76× smaller per stored float.

**So history has to change shape before the port**, not after: sampled,
opt-in, or reduced to the series the analysis actually reads. That is a
finding about the design rather than about the size, and it is the one thing
this session found that the port cannot ignore.

## 5. Correctness at width: everything held

**The labor value solve reproduces the closed analysis.** `docs/20` validated
the solver against `FINDINGS.md` on four commodities. Here it runs on 647,
and of the 611 with a positive authored figure:

| | commodities |
|---|---:|
| direct labor floored by the generator | 36 |
| downstream of a floored commodity | 164 |
| **comparable** | **447** |
| **reproducing the authored figure to 1e-9** | **447** |

Every single comparable commodity is exact, and every exception traces to the
generator's own artifact rather than to the solver: where the synthetic
wiring gave a commodity inputs carrying more labor than the def contains,
direct labor floors at one tick and the excess propagates downstream. The
frozen reference pins `scale.value_solve_exact_share` at **1.0**.

That is the most substantial validation the solver has had, and it came free
with an instrument built to measure something else.

**Ledgers close.** The worst material residual at 647 × 100 is 1.9 × 10⁻⁹
absolute against commodities whose embodied labor runs to 400,000 ticks —
relative residuals below 1e-9, which is the same floating-point behavior the
six-commodity scenarios show.

**Determinism holds.** Identical seeds give bit-identical histories at 200
commodities × 4 regions, asserted in the suite.

**Iteration counts stay flat**, as `docs/32` §7.3 predicted from the depth
histogram. The real graph is at most depth 3 — 163 / 252 / 159 / 79 defs at
depths 0 through 3 — and every fixed point in the model propagates along the
input graph, so width costs work per pass and not more passes.

**The exact stationary equilibrium does not generalize**, as §7.7 said it
would not, and the generator does not claim it. That property belongs to a
hand-tuned six-commodity calibration.

## 6. The verdict against the budget

| constraint | budget | measured | verdict |
|---|---|---|---|
| CPU per simulated day | 50 ms | **22.3 s** | fails in Python by 446× |
| CPU per single tick | 1 ms | n/a (amortizable) | passes if chunked |
| resident economy state | 50 MB | **60 MB + 16 MB/day** | **fails architecturally** |

The CPU verdict is more forgiving than the raw ratio suggests, and the
reasoning matters more than the number. Cost is now **linear** in producers,
so it is a constant-factor problem rather than a scaling one. A C# port at a
conservative 20× gives about **1.1 s per simulated day** at full scale;
spread across a day's 60,000 ticks that is under 20 µs a tick. The budget is
met with room, provided the update is amortized rather than run in one tick.

The memory verdict does not soften. 3.8 GB of history is a design decision,
not an implementation cost, and it has to be revisited before anything is
ported.

## 7. Prediction scorecard

| prediction | outcome |
|---|---|
| 7.1 `throughput_demand` inside the plan dominates | **correct** — 84% of the run |
| 7.1 `_record_history`'s `capacity()` is the second cost | **wrong** — 0.6% |
| 7.2 memory is the *first* hard wall | **wrong on order, right on substance** |
| 7.3 iteration counts stay flat | correct |
| 7.4 653 × 2 costs 1–3 s/day | correct — 0.97 before the fix |
| 7.4 653 × 100 costs 50–150 s/day | correct — ~50 before the fix |
| 7.5 arbitrage is not the problem | correct — 300 routes, not 4,950 |
| 7.6 ledgers close and determinism holds | correct |
| 7.7 exact stationarity does not generalize | correct |

**7.1's second half was wrong for an instructive reason.** `capacity()` and
`throughput_demand()` are the same shape — O(producers), called per commodity
— and the prediction treated them as the same problem. They are not: one is
called once a day and the other five times per iteration of a fixed point.
**Where a function sits matters more than what it costs**, and reading the
code without counting call sites got that backwards.

**7.2 was wrong about ordering and right about the danger**, which is the
more useful half. Memory does not bite first because the CPU cost stops the
run before day 240 — but the CPU cost is a language constant and the memory
is not, so the prediction's *conclusion* survives even though its timing
failed.

The design document also, quietly, got its own priority right: it fixed the
budget before measuring, and both failures are unambiguous rather than
arguable.

## 8. Where this leaves the project

The scale question is answered and the roadmap's largest open risk is closed.
Three things follow, in order:

1. **History has to change shape** — sampled or opt-in — and it is now on the
   critical path for the runtime port rather than behind the economics.
2. **`_allocate_orders` deserves one session** of the same kind: measure,
   name, fix only what is accused. It is 42% of a day and the fixes are
   mechanical.
3. **The economics backlog resumes**, unchanged in order: a capital-goods
   sector, then capacity depreciation and exit, then recreation in the
   basket.

And the roadmap's Phase B is done. `HANDOFF.md`'s "Distance to the full
suite" gave four phases and put the scale test in the second; that section
now needs the risk marked retired and the port's constraints written down
while they are fresh.

## Reference decision

Two commits. The first adds the harness, makes throughput demand linear, and
adds nine tests; 138 to 147. The second freezes five structural observations
— **not the timings**, which are machine-dependent and belong in this
document; 149 metrics to 154.
