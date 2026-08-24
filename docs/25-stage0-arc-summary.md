# Stage 0: what the laboratory has learned so far

A narrative summary of the economy laboratory's arc, written to complement
`HANDOFF.md` rather than repeat it. `HANDOFF.md` is the state document — what
exists, what is next, what not to break. This is the argument: what each layer
was for, what it measured, and what it got wrong.

The detailed record lives in the design/results pairs, `docs/06` through
`docs/24`. Every feature was designed in a committed document *before* it was
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

## What the last session established: the overhead is the seam

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
  because v is tiny, not because c is large. Necessary labor is 2.5% of the
  working day, since the basket is meals-only.
- **Upstream troughs would shallow** with the wage (`docs/18`). Unchanged:
  the farms were already fully idle before the trough. The cost floor moves
  *when idling begins*, not the floor of the overshoot.

---

## The standing caveat on every headline number

The subsistence basket is **meals only**. A real reproduction bundle includes
shelter, clothing, medicine, and recreation. So the value of labor-power is
understated, and every ratio built on `v` — s/v 38.30, c/v 20.67, the value
rate of profit 1.77 — is inflated by the same mechanism. Flagged since
`docs/17`, and it remains the single largest caveat the project carries.

---

## Where it goes next

**Prices of production.** `docs/24` concludes that the wedge cannot be closed
while RimWorld's authored `MarketValue` is the anchor: every economically
meaningful component has been carved out of it and two-thirds remains.
Deriving prices from the technical coefficients, the wage, and a uniform
profit rate is the resolution, and the model already holds every piece —
input-output coefficients, direct labor, fixed capital, a wage, and the
iterative solver. A non-destructive first step is to compute the implied
prices as an *observation* beside the authored ones.

Behind it: capacity depreciation and exit, so competition is for survival and
not only for orders; a capital-goods sector, since building capacity still
spends silver without consuming material; and an enlarged basket, which would
bring every ratio above down to a defensible magnitude.

**Current state:** 97 tests, 101 frozen metrics, four commodities, two
regions, three closing ledgers, and an equilibrium that is still exactly
stationary — a price range of exactly zero, in both regions, across four
in-game years.
