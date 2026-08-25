# Stage 0: what the laboratory has learned so far

A narrative summary of the economy laboratory's arc, written to complement
`HANDOFF.md` rather than repeat it. `HANDOFF.md` is the state document — what
exists, what is next, what not to break. This is the argument: what each layer
was for, what it measured, and what it got wrong.

The detailed record lives in the design/results pairs, `docs/06` through
`docs/35`. Every feature was designed in a committed document *before* it was
implemented, and every prediction was scored afterward whether or not it held.

---

## The method, and why it is the point

Two properties are held above everything: **determinism** (identical inputs
give bit-identical histories) and **ledgers that close to floating-point
zero**. There are now three of those — material, silver, and value.

Three working rules have done most of the work:

1. **Design before code.** Each session's decisions were written down, with
   the rejected alternatives named, before anything was built. This is not
   ceremony: it is what makes a wrong prediction informative rather than
   embarrassing, because the reasoning that produced it is on the record.
2. **Proportional and damped, never threshold-and-switch.** Refused five
   times now (input rationing, inventory control, investment, wages, order
   allocation) on the same grounds: a discontinuity manufactures limit cycles
   that look like economic results.
3. **Four quantities stay distinct.** Labor value, market price, surplus
   value, and rent. Money profit is not surplus value. The model's job is to
   let them move independently, and by the end of this arc it does.

A frozen behavioral reference (now 101 metrics) is re-run after every change.
It is a *report*, not a test: movement never fails a build, but it must be
understood and explained before the reference is rewritten.

---

## The arc: closing one hole at a time

Each layer removed something that was appearing from nothing.

| step | what was free | what it costs now | docs |
|---|---|---|---|
| 3–4 | material appeared from nothing | production consumes accounted inventory | 07–09 |
| — | upstream stocks never recovered | damped demand-led replenishment | 10–12 |
| 5 | producers ignored input prices; capacity was free | cost floor; construction fund; buffer investment | 13–14 |
| 6 | extraction was unlimited | finite graded reserves; differential rent | 15–16 |
| 7 | labor-power was free | a wage buys it, and silver cycles back through the workers' own purchases | 17–18 |
| 8 | labor values were imported constants | solved from the process graph | 19–20 |
| 9 | cost could not reach price | cost-aware anchor; the order book goes to the cheaper producer | 21–22 |
| 10 | fixed capital transferred nothing; the overhead was unexplained | capital depreciates into value; the overhead is measured and named | 23–24 |
| 11 | the profit rate was frozen per sector by calibration | a uniform rate is solved from the technique and the real wage | 26–27 |
| 12 | workers ate and wore and needed nothing else | the basket is food, clothing and medicine | 28–29 |
| 13 | profit was charged against a day's flow | it is charged against the capital actually advanced | 30–31 |
| 14 | nobody knew whether any of it scaled | it does, linearly, and the memory design does not | 32–33 |
| 15 | history grew forever, and the ledger read it | history is optional; the opening stock is state | 34–35 |

---

## The three results that are about the thesis

### 1. The value solve validates against an independent analysis

`FINDINGS.md` solved embodied labor for 653 RimWorld defs from extraction
outward, without price entering the derivation. The laboratory's own solve,
built later and from the same per-unit data, reproduces it: chemfuel and
meals agreed **exactly** for the two commodities with no modelled inputs, and
the two downstream commodities were high by *precisely* the one input link
`docs/08` had flagged as a deliberate stylization — 1.25 ticks on psychoid
leaves, 15.00 on yayo, and nothing else.

That is the propagation machinery checked against an independent instrument
rather than against itself.

### 2. The rate of surplus value is an outcome, not a coefficient

`docs/18` had to report s/v as a free parameter dressed in data: it followed
in closed form from the working day, the basket, and an authored constant.
Once values were solved from the graph (`docs/19`), it became an outcome.

- It does **not** move when prices do. A subsistence shock that doubles the
  meal price and the money wage leaves the labor value of a meal unchanged
  and s/v at 38.30.
- It **does** move when technique does. A provisioning technique with half
  the living labor lowers the social value of the wage good and lifts s/v
  from 38.30 to **44.0** — in *both* regions, including the one that adopted
  nothing, because value is social. That is relative surplus value, emerging
  from the process graph with the working day and the basket held fixed and
  asserted in tests.

### 3. Value and price answer to different things

Two deliberately opposite scenarios, once cost could reach price:

| | labor-saving | capital-saving |
|---|---|---|
| what the entrant saves | living labor | overhead |
| labor value of meals | −12.7% | **0.0%** |
| meal price | −0.47% | **−14.3%** |
| rate of surplus value | 38.30 → 44.0 | **unchanged** |

A falling money wage is not a falling value of labor-power. The four ledgers
are kept apart because the model makes them move apart.

---

## What the last two sessions established

The model's ceiling, named in `docs/22`, was that money costs were mostly an
unexplained residual — `unit_cost`, which `docs/13` had derived as *whatever
makes producers run at full utilization at reference prices*. Over 95% of
cost for meals and chemfuel.

Both candidate explanations were tested before anything was designed.

**It is not fixed capital.** That was implemented anyway, from each sector's
real RimWorld building, repairing an omission `FINDINGS.md` recorded in
vanilla — where a workbench transfers no value at all to what it produces.
It accounts for **0.05% of cost** and 0.353% of constant capital. RimWorld's
buildings are cheap relative to their lifetime output, so the vanilla
omission is real but quantitatively minor.

**It is the authored-price wedge.** Subtracting inputs, wages, and capital
consumption from each unit's price leaves **two-thirds of the price**
unattributed for the goods the model builds from labor alone — and 66.6% is
exactly `reference_price × 14 / 21` showing through from the original
calibration. The overhead was never a cost. It was the wedge holding
RimWorld's authored price level apart from the model's wage.

That is the same seam the research spike found from the outside, now measured
from the inside. The wage is 3.1 silver per in-game work-hour; RimWorld's own
fabrication constant embeds 9/hour and its extraction prices imply ~95/hour.

**What was refused:** calling the wedge surplus value. For the wage good the
money and labor ledgers then agree to two decimals — but that agreement is an
*identity*, not evidence, since both derive from the same wage and basket and
would agree whatever the truth was. The design document committed to saying
so before the number was computed. The wedge is reported under its own name,
and surplus is given as two readings that state their assumption.

### The classical magnitudes, at last

| quantity | value |
|---|---:|
| rate of surplus value s/v | 38.30 |
| organic composition c/v | 20.67 |
| value rate of profit s/(c+v) | 1.77 |

And a third closing identity, `value of output = c + v + s`, to floating-point
zero. It is a real check rather than a tautology — three independently
accumulated paths — and it caught two bugs within minutes of existing.

### Surplus produced is not surplus realized

Every sector performs surplus labor at the same rate. What they *realize* in
money differs wildly:

| sector | money s/v | labor s/v |
|---|---:|---:|
| chemfuel | 72.58 | 38.30 |
| psychoid leaves | 29.90 | 38.30 |
| meals | 38.33 | 38.30 (agrees by construction) |
| yayo | **11.18** | 38.30 |

The drug lab buys inputs at prices containing surplus and sells into a yayo
price that barely covers them, realizing under a third of what its workers
performed. That is the transformation problem as arithmetic rather than as an
argument.

---

## The price system: solved, and deliberately not adopted

`docs/24` concluded that the authored-price wedge could not be closed while
`MarketValue` is the anchor, and named prices of production as the
resolution. `docs/27` computed them, and they are not the resolution.

Folding the subsistence basket into the input matrix gives a price system
with no authored magnitude anywhere in it — `p = (1 + r)Mp`, solved by
iteration, with the profit rate as an outcome rather than a coefficient.
Sraffa's structure then decides the answer: **meals is the only basic
commodity**, because every sector employs labor and the provisioning process
has no modelled inputs. A single basic good made by labor alone is a corn
model, so

```
r  =  T / (b · l) − 1  =  38.344
```

which is the rate of surplus value, arrived at from the price side without a
value magnitude entering the computation. That is a genuine result. What
follows from it is not usable: a gross markup of 39.34 meets yayo's
two-stage input chain twice, pricing a unit of yayo at **a hundred meals**
where RimWorld says one and a half.

Nothing is wrong with the arithmetic. The input to it is. `r` is the
reciprocal of the basket's share of the working day, and the basket was meals
only, so necessary labor was 2.5% of the day. That looked like the
prerequisite, and `docs/27` reordered the backlog to fix it first.

**It was not the prerequisite.** See the next section.

The same session measured the transformation problem at the aggregate level,
beside `docs/24`'s sectoral version. Normalized so that total price equals
total value, total profit comes to **1.526×** total surplus. Marx's two
invariance postulates do not both hold, and choosing the other normalization
moves the discrepancy rather than removing it.

Relative surplus value shows up here too: in `technique-change`, halving the
living labor in part of society's meal output lifts the uniform profit rate
from 38.34 to **44.06**, with the working day, the basket and every material
technique untouched. The wage good is the only lever on `r` because it is the
only basic commodity — asserted directly, on a purpose-built three-good
economy where changing the non-basic sector's technique leaves the profit
rate *bit-identical*.

---

## What the basket turned out not to be

`docs/29` enlarged the basket to food, clothing and medicine, with every
figure from the closed analysis: `Apparel_BasicShirt` at 1,620 embodied
ticks, `MedicineHerbal` at 400, quantities from a cold-biome wardrobe
replaced annually and 7.5 doses a year.

Necessary labor rose from 2.5% to 3.6% of the working day. Every ratio
built on the value of labor-power fell by about 30%:

| quantity | meals only | enlarged |
|---|---:|---:|
| rate of surplus value s/v | 38.30 | **26.71** |
| organic composition c/v | 20.67 | **14.42** |
| **value rate of profit s/(c+v)** | 1.768 | **1.733** |
| uniform profit rate r | 38.34 | **24.62** |
| yayo against its authored price | 71.6× | **38.7×** |

Two things to read off that table. The value rate of profit moved **2%**
where the other ratios moved 30%, because it has constant capital in the
denominator too and `c` is fourteen times `v` either way — enlarging the
basket repairs two of the three headline ratios and barely touches the
third. And halving yayo's deviation still leaves a unit of yayo pricing at
fifty-four meals where RimWorld says one and a half.

**The constraint was never the basket.** `r ≈ T / (basket labor) − 1`, so a
profit rate near 1 needs a bundle embodying half a working day. One
provisioner's day feeds **39.3 workers** on RimWorld's own numbers, which
means closing that gap in meals alone takes thirty-nine meals a day. A
deliberately indefensible `generous_basket` scenario — three meals, half a
garment and half a dose — still lands at s/v 11.4.

So the rate of surplus value this project reports is not a calibration
artifact to tune away. **It is RimWorld's**, and the colony that accumulates
wealth implausibly fast does so because its labor is implausibly productive.
That is a statement about the game rather than about the laboratory, and it
is the closest thing the arc has produced to a claim about the artifact
under study.

The session also reached the **general Sraffa case** for the first time. The
tailors' bench is powered, so chemfuel enters a wage good and becomes basic —
and that one material input breaks the identity that had made the uniform
profit rate exactly the rate of surplus value. `r` falls 8% below the
rank-one figure, because the price system marks material inputs up by `1 + r`
and the value system does not. A control scenario removing the link restores
the identity exactly.

And one caveat could finally be **retired**. `docs/24` reported that the
money and labor rates of surplus value agreed for meals, and refused to call
it evidence, since under a meals-only basket both were the same expression in
the same wage. With three goods the derivation no longer closes: garments
realize 28.5 against a labor rate of 26.7, medicine 13.3, and meals land
within 1.5% as a small real difference rather than a tautology.

---

## The last hole: profit was charged against the wrong thing

`docs/31` closed the arc's final accounting gap, and it is the smallest-
sounding and most embarrassing of them. **The model charged profit against a
single day's flow while holding twenty days of stock.**

Two numbers were printed as rates of profit and neither was one. The price
system's `p = (1 + r)Mp` advances capital for exactly one production period,
so its `r` was a *daily* rate — 38.34, then 24.62, magnitudes nobody could
argue about. And `value_rate_of_profit` divided surplus by `c + v` as
cumulative *flows*, making it profit per unit of capital consumed rather than
per unit advanced.

The correction is `p_i = (1 + r τ_i)(M_i · p)`, with turnover read off each
commodity's own inventory life rather than a new parameter — inventing one
would let turnover be tuned away from the stock the model actually holds,
which is the whole point. The results:

| quantity | before | after |
|---|---:|---:|
| price system, per period | 24.62/day | **1.1726/day** |
| the same number, renamed | — | gross markup **24.62** |
| ledger, flow ratio | 1.7326 | 1.7326 (kept) |
| **ledger, on capital advanced** | — | **0.0305/day** |

**Uniform turnover moves no relative price**, because `1 + rτ` is a scalar.
That invariance is asserted bit-exactly, and it means only *differential*
turnover redistributes anything — which `perishable_meals` demonstrates, since
RimWorld's simple meals rot after four days: the rate rises to 2.08 and yayo
goes from 54 meals to 476.

The measurement that was worth the session is the turnover time itself.
Capital is tied up for **56.8 days**, not the 21 the price system assumes,
because **yayo is nobody's input** — its finished stock is 63% of all
commodity capital and appears in no cost flow anywhere. Take it out and the
figure lands at 22.1. A cost flow measures what is used up; an advance
measures what is laid out; a final good waiting for a customer is laid out
and never used up.

The advance itemizes to 96.3% commodity stock, 3.5% installed plant, and
**0.11% wages** — so the wage advance, which is what the old formulation
effectively charged profit against for a pure-labor good, is one part in nine
hundred of the capital in play.

---

## The size question, finally asked

Every layer above was measured on **six commodities and two regions**.
RimWorld is 653 producible defs and roughly a hundred settlements, and three
roadmaps in a row called this "the cheapest large risk to retire" and
deferred it. `docs/33` retired it in one session.

The most useful fact came out of the data rather than the code. The real
graph is **wide and shallow** — 163 / 252 / 159 / 79 defs at depths 0 to 3,
maximum depth 3. Every fixed point in the model propagates along the input
graph, so width buys work per pass and not more passes, and iteration counts
stay flat at any size.

**The architecture is linear**, after one method changed.
`Region.throughput_demand` is O(producers) and was being called once per
commodity inside a fixed point — so a simulated day was O(commodities ×
producers) several times over, and the profiler put it at 84% of the run.
Computing all of them in one pass over each producer's *inputs* made it
O(producers × inputs):

| | before | after |
|---|---|---|
| 10.1× the commodities costs | **22.5×** the time | **10.9×** the time |
| 647 commodities × 2 regions | 0.97 s/day | 0.40 s/day |
| 647 × 100 (full scale) | ~50 s/day | **22.3 s/day** |

Against a 50 ms budget that is still 446× over — but it is a *constant
factor* now rather than a scaling failure, and a C# port at a conservative
20× lands at about 1.1 s per simulated day, under 20 µs a tick once
amortised across a 60,000-tick day.

**Memory is the failure that a faster language does not fix.**
`Economy.history` grows about 16 MiB per simulated day at full scale — 3.8 GB
over a 240-day run. That is a design decision, not an implementation cost,
and it moved onto the critical path for the runtime port.

### The result that came free

The harness was built to measure cost and it delivered the arc's largest
validation. `docs/20` checked the labor value solver against `FINDINGS.md` on
**four** commodities. Run at 647, of the 611 with a positive authored figure:
36 had their direct labor floored by the generator's own synthetic wiring,
164 sit downstream of one of those, and **all 447 remaining commodities
reproduce the closed analysis's embodied labor exactly**. Not approximately —
`scale.value_solve_exact_share` is frozen at 1.0.

### And a lesson about the two instruments

The batch method claimed bit-equality with the one it replaced, argued from
"the terms accumulate in the same producer order". The argument was wrong:
**CPython's `sum` compensates its floating-point error and a `+=` loop does
not**, so the two disagreed in the last bit wherever a commodity had more
than one consumer. The frozen reference did not notice, because it rounds to
six decimals. The equivalence test did, within a minute of existing. That is
precisely the division of labour the tests and the reference were separated
for.

---

## Predictions that were wrong, and what they taught

Kept because they are the most informative part of the record.

- **Downstream cost-push would propagate** (`docs/16`). It did not — chemfuel's
  input share was too small. Correct diagnosis: cost-push is proportional to
  input share. It only became possible at all once the price anchor could
  read cost, three sessions later.
- **The producer-loss peak would fall** to 26–33 (`docs/22`). It **rose** to
  45.25. The reasoning tracked the leaf price *trough* but the yayo peak
  arrives 56 days later, during the leaf *overshoot*. The anchor amplifies
  the cycle rather than damping the peak.
- **Organic composition would be 2–4** (`docs/24`). It is **20.67** — high
  because v is tiny, not because c is large. Necessary labor was 2.5% of the
  working day under the meals-only basket, and is 3.6% under the enlarged
  one, which brings c/v to 14.42 and no further.
- **`_record_history` would be the second-largest cost** (`docs/32` §7.1).
  It is **0.6%** of a simulated day, against 84% for the function it was
  paired with. Both are O(producers) called per commodity — the same shape —
  but one runs once a day and the other five times per iteration of a fixed
  point. **Where a function sits matters more than what it costs**, and
  reading the code without counting call sites got that backwards.
- **Memory would be the first hard wall** (`docs/32` §7.2). It is not first:
  at 22 s a day nobody reaches day 240 to run out of it. The *conclusion*
  survived the timing being wrong, because the CPU cost is a language
  constant and the memory is not.
- **A turnover correction would put `r` near 0.28** (`docs/29` §10). It is
  **1.17**, four times higher. The envelope compounded `r` over twenty
  periods where the classical formulation charges it once on the advance.
  `docs/30` §7.1 caught and corrected it before implementing anything, which
  is what an envelope labelled as an envelope is for.
- **The fixed-capital advance would be 16,795 ticks** (`docs/30` §7.3). It is
  **17,073**, because the prediction computed it as depreciation flow times
  service life while the implementation measures installed plant. Those agree
  only when nothing is idle. A 1.65% miss, and it is the stock-versus-flow
  confusion the session exists to fix, committed once more inside the design
  document that fixes it.
- **The enlarged basket would unblock the price system** (`docs/27`). It did
  not, and `docs/28` said so in advance rather than discovering it
  afterward. Recorded here as a wrong *reordering* rather than a wrong
  number: the reasoning identified a real understatement and then assumed,
  without checking the magnitude, that removing it would be enough.
- **Upstream troughs would shallow** with the wage (`docs/18`). Unchanged:
  the farms were already fully idle before the trough. The cost floor moves
  *when idling begins*, not the floor of the overshoot.
- **Chemfuel's production price would equal its value ratio exactly**
  (`docs/26`). It is 0.999383 of it. Both goods are pure-labor, so the price
  ratio *is* exactly 25/305 — but labor values have carried the plant's
  embodied labor since `docs/23`, and the prediction forgot the model's own
  most recent feature. A small number with a real lesson: the fixed-capital
  omission is not cosmetic bookkeeping, it changes which identities hold
  exactly.

---

## The standing caveats

**The basket is still not complete**, but the gap is now small and measured.
Food, clothing and medicine are in; shelter is out because a bed and a room
amortize to under 20 ticks a worker-day, an order of magnitude below the
smallest component that *is* modelled; recreation is out because the obvious
candidate is the model's own final good and putting it in the basket would
create a wage-price loop through the commodity every scenario is measured on.
So `v` is still understated, and every ratio built on it is still inflated —
but by a bounded amount rather than an unknown one.

**Three rates are easy to confuse, and all three are now reported.** The
gross markup (24.62) is price over cost per turnover. The price system's `r`
(1.17/day) is the uniform rate that system would pay, and it is fixed by the
*basic* sector alone. The ledger's rate on advances (0.0305/day) is what this
economy actually realizes at RimWorld's authored prices, across all its
capital. The last two differ by a factor of 38 for Sraffa's reason: 96% of the
advance is the yayo circuit's stock, and yayo is non-basic.

**Fixed capital is still outside the price system.** It is 3.5% of the capital
advanced, where as a depreciation flow it was 0.05% of cost — so the omission
`docs/26` §3.5 bounded is more visible than it was. The fix is a capital-goods
sector.

---

## Where it goes next

**`_allocate_orders`**, which is now 42% of a simulated day and whose fixes
are mechanical: it sorts one-element lists, keys four dictionaries by
`id(producer)`, and rebuilds its commodity grouping on every iteration. The
history reshape that stood beside it is done (`docs/35`).

Behind it, in the economics: a capital-goods sector, which building capacity
needs anyway — silver is still spent without consuming material — and which
is what would let fixed capital into the price system. Then capacity
depreciation and exit, so competition is for survival and not only for
orders. And recreation in the basket, which is worth doing on its own rather
than alongside something else.

**Current state:** 154 tests, 154 frozen metrics, six commodities, two
regions, three closing ledgers, a classical price system with an
interpretable profit rate computed beside the authored one, a harness that
runs the same model at 647 commodities across 100 regions, and an equilibrium
that is still exactly stationary — a price range of exactly zero, in both
regions, across four in-game years.
