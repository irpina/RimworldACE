# Constant capital, and what the operating overhead actually is: decisions

Recorded **before** implementation, in the style of `docs/08`, `docs/11`,
`docs/15`, `docs/17`, `docs/19`, and `docs/21`.

`docs/22` ended by naming the model's ceiling: `Producer.unit_cost` is a
calibration residual with no economic interpretation, it is over 95% of money
cost for meals and chemfuel, and an economy whose costs are mostly unexplained
residual can only say so much about labor. This session takes that apart.

Two measurements, taken before designing anything, decide what the session can
honestly claim.

---

## 1. What the overhead is not: fixed capital

The obvious candidate is capital consumption. `docs/13` gave capacity a
construction cost in silver, and `FINDINGS.md` recorded that RimWorld's own
formula **transfers no value from fixed capital at all** — a workbench
contributes nothing to what it produces, so all constant capital in vanilla is
circulating. Repairing that omission is worth doing on its own merits.

It does not explain the overhead. Each sector's real building is in the closed
analysis, with both a money price and an embodied-labor figure:

| sector | building | market value | embodied labor |
|---|---|---:|---:|
| drug lab | `DrugLab` | 445.0 | 41,607.5 |
| psychoid fields | `HydroponicsBasin` | 230.0 | 13,120.0 |
| chemfuel refinery | `BiofuelRefinery` | 390.0 | 25,835.0 |
| provisioners | `ElectricStove` | 225.0 | 16,940.0 |

Machines are needed in proportion to the labor performed at them: one machine
occupied for one worker-day supports `ticks_per_worker_day` of work, so a unit
of daily output needs `direct_labor / ticks_per_worker_day` machines. Spread
over a service life, the resulting transfer per unit is:

| sector | machines/unit | depreciation (silver) | as % of cost | (ticks) | as % of living labor |
|---|---:|---:|---:|---:|---:|
| yayo | 0.014583 | 0.01082 | **0.067%** | 1.011 | 0.289% |
| psychoid leaves | 0.001925 | 0.00074 | **0.056%** | 0.042 | 0.091% |
| chemfuel | 0.001042 | 0.00068 | **0.043%** | 0.045 | 0.179% |
| meals | 0.012708 | 0.00477 | **0.046%** | 0.359 | 0.118% |

At a 600-day service life, fixed capital consumption is **under a tenth of a
percent of cost** in every sector. Even a punishing 60-day life leaves it
under 1%. RimWorld's buildings are cheap relative to what they produce over
their lives, so transferring their value correctly changes almost nothing.

That is worth implementing and worth reporting — it turns `FINDINGS.md`'s
structural note into a measured magnitude, and it means the vanilla omission
is quantitatively as well as formally minor — but it is not the answer.

## 2. What the overhead is: the authored-price wedge

The overhead is the gap between RimWorld's authored `MarketValue` and a cost
built from inputs, wages, and capital consumption. Subtracting everything the
model can actually account for:

| sector | old overhead | attributable cost | wedge | wedge as % of price |
|---|---:|---:|---:|---:|
| yayo | 0.0000 | 16.1083 | −0.0108 | −0.1% |
| psychoid leaves | 1.1517 | 0.1735 | 1.1510 | **60.6%** |
| chemfuel | 1.5333 | 0.0319 | 1.5326 | **66.6%** |
| meals | 10.0000 | 0.3861 | 9.9952 | **66.6%** |

For the two goods with no modelled inputs the wedge is two-thirds of the
price, which is no coincidence: `docs/13` derived the overhead as
`reference_price × region_cost / 21`, and 14/21 is exactly two-thirds. The
overhead was never a cost. It was the calibration holding RimWorld's authored
price level apart from the model's wage.

This is `FINDINGS.md`'s central result, arrived at from the inside. Authored
prices embed an implicit labor rate far above what the model pays: the wage is
30 silver for a 24,000-tick day, or 3.1 silver per in-game work-hour, against
the 9/hour that RimWorld's own fabrication constant embeds and the ~95/hour
its extraction prices imply. The wedge is that discrepancy, per unit.

### The decision, and the thing not to claim

**Decision: reclassify the overhead out of cost, and report what it is as an
explicitly unattributed quantity — not as surplus.**

It is tempting to call the wedge surplus value. For the wage good the money
and labor ledgers then agree exactly: meals show a money rate of surplus value
of 38.33 against a labor-time rate of 38.34.

**That agreement is an identity, not evidence.** Both figures derive from the
same wage and the same basket: with the basket priced at 2 meals, money s/v is
`price / wage_per_unit − 1 = 24000/610 − 1`, which is the labor-time
expression term for term. It would agree no matter what the truth was, so it
cannot be used to argue that the wedge is surplus.

The honest position is that **the model cannot tell**. The wedge is either
surplus value, or real costs the model does not represent — energy beyond the
modelled chemfuel, tools, maintenance, land, transport, the rest of a
colony's overheads — or some mixture. Nothing inside the laboratory
distinguishes them.

So the ledger will report a **band** rather than a number:

- **lower bound**: the wedge is entirely unmodelled cost, so surplus is only
  what the old calibration called profit;
- **upper bound**: the wedge is entirely surplus, so surplus is price minus
  attributable cost.

Reporting an estimator-dependent quantity as a range with its assumptions
named is what `FINDINGS.md` did with the 3–4× versus 14× extraction premium,
and for the same reason: the direction is robust and the magnitude is not.

## 3. Part A — fixed capital that transfers value

**Decision: a process carries the capital its technique requires, in both
silver and labor ticks, and that capital transfers to the product by use.**

Two new `Process` fields, both defaulting to zero so bare models are
unaffected: `capital_money_per_capacity` and `capital_labor_per_capacity`,
each the capital supporting one unit of daily output. The scenarios compute
them from the building table in §1.

Transfer per unit of output is `capital_per_capacity / capital_service_life_days`
(default 600 days, ten in-game years). Since one unit of daily capacity
produces one unit per day, that is the capital divided by the units it makes
across its life.

**Use-based, not time-based.** Depreciation attaches to output rather than to
the calendar, so unit cost does not depend on utilization. Time-based
depreciation is the more realistic reading for a building and is the reason
idle plant is expensive, but it makes unit cost rise as output falls, which is
a positive feedback into the price anchor — precisely the shape that has
manufactured limit cycles in this model before (`docs/08`, `docs/11`). Use-based
is also the standard Leontief–Sraffa simplification. Time-based depreciation is
deferred, and belongs with mothballing and exit, where idle capacity is the
subject rather than a side effect.

**Where the money goes: nowhere.** Depreciation is a cost accrual, not a
payment. No silver moves and no material moves, so both ledgers are untouched.
This is deliberate and it exposes a standing gap rather than hiding one:
building capacity spends silver (`docs/13`) but consumes no material, because
no capital-goods sector produces anything. A real Department I — machinery as
a produced commodity that investment consumes — is the proper treatment and is
named as deferred in §7.

**The labor transfer is exogenous, like direct labor.** The buildings are not
in the modelled circuit, so their embodied labor comes from the closed
analysis rather than from the value solve, exactly as `Process.direct_labor`
does. The value equation gains a constant term and stays acyclic:

```
v(c) = Σ inputs × v(input) + direct_labor + capital_labor_transfer
```

Labor values rise by 0.1–0.3%. Constant capital now includes a fixed
component, which is what `FINDINGS.md` observed RimWorld omits entirely.

## 4. Part B — the overhead leaves the cost side

**Decision: `unit_cost` splits into capital consumption plus a named
`unattributed_margin`. The utilization curve keeps using their sum, so
behavior is preserved.**

```
attributable_cost = inputs + wages + capital consumption
reservation_price = attributable_cost + unattributed_margin
```

`unattributed_margin` is seeded as the old overhead minus the new capital
consumption, held constant per unit. Producers curtail on the reservation
price exactly as they curtail on effective cost today, and the cost anchor
from `docs/21` continues to track the reservation price, so the *only*
behavioral change in the entire session is that costs rise by the depreciation
term — under 0.1%.

**Why the margin is additive and constant rather than a rate on capital.** A
required return should scale with capital employed. Here capital is so small
(§1) that a rate on it would collapse the reservation price to near
attributable cost, margins would explode, investment would flood in, and the
whole calibration would come apart. Holding the wedge constant per unit is not
a theory of the wedge; it is a refusal to invent one, and it keeps the
measured quantity visible instead of dissolving it into a coefficient.

**The subtraction hazard, checked loudly.** For yayo the old overhead is zero
while capital consumption is 0.0108, so the margin goes slightly *negative* —
RimWorld's yayo price does not quite cover its inputs, wages, and capital
consumption at reference. That is a real finding about the authored price, not
an error, so a negative margin is permitted and reported rather than clamped.
What is not permitted is a producer silently dropped below full utilization at
reference prices; the existing seeding assertion already refuses that, and it
now runs against the reservation price.

## 5. Part C — the ledger the project has been building toward

**Decision: accumulate constant capital, and report the classical ratios in
value terms, with the money side as a band.**

Per region, in work-ticks:

- **constant capital `c`** — circulating inputs at their own labor values,
  plus fixed capital consumed;
- **variable capital `v`** — necessary labor (already accumulated);
- **surplus `s`** — living labor beyond necessary (already accumulated);
- **organic composition** `c / v`;
- **value rate of profit** `s / (c + v)`.

These are the magnitudes the whole project has been assembling and has never
been able to state. They stay observational, in ticks, and are never mixed
with silver: the rate of profit in value terms and money profitability are
different quantities, and this model now has both.

Alongside them, per sector, the diagnostic that motivated the session: the
per-unit decomposition of price into inputs, wages, capital consumption, and
the wedge — and the comparison of each sector's **money** rate of surplus
value against the uniform **labor-time** rate. Those two agree by construction
only for the wage good; where they diverge, they measure how much surplus a
sector realizes versus how much it produces. Predicted from the seeded state:
yayo 11.18 against 38.34, chemfuel 72.70, leaves 29.87. A sector buying inputs
whose prices contain surplus realizes less than it produced; a sector selling
into a price that does, more. That is the transformation problem made
arithmetic, and reporting it is this session's most substantive new
observation.

## 6. Predictions

**Behavior: nearly frozen.** Attributable cost plus margin exceeds the old
effective cost by exactly the capital consumption, 0.04–0.07%. Since the
`docs/21` anchor is a ratio against the seeded cost, and the seed rises by the
same amount, equilibrium prices are unchanged and the equilibrium price range
stays exactly zero. Predicted: **fewer than 10 of 85 metrics move, none by
more than 0.5%**, with movement concentrated where a utilization threshold is
crossed near a boundary — the producer-loss path, and the quantized recovery
days.

**Labor values rise 0.1–0.3%**, so the rate of surplus value falls slightly
from 38.344 — predicted to land between 38.20 and 38.34, since necessary
labor is the basket at the new, slightly higher meal value.

**The organic composition will be very low.** Constant capital is dominated by
circulating inputs, and for the two extraction-like sectors there are none, so
c/v should be near zero upstream and substantial only for yayo, whose inputs
are 94% of its cost. Predicted regional c/v of roughly 2–4, and a value rate
of profit well above anything in the historical literature, for the reason
`docs/18` already recorded: the basket is meals-only, so v is understated.

**Fixed capital will look irrelevant, and that is the finding.** Predicted
under 0.5% of constant capital in every sector.

## 7. Non-goals

- **A capital-goods sector (Department I).** Machinery as a produced commodity
  that investment consumes materially is the proper treatment of the gap in
  §3. It is a fifth commodity with its own process, its own reserves question,
  and a rewrite of the investment path; it deserves a session.
- **Time-based depreciation and mothballing.** Deferred with exit, §3.
- **Adopting prices of production.** Deriving prices from the technical data
  and the wage, instead of anchoring them to authored `MarketValue`, is the
  real resolution of the wedge — and it is a much larger change that would
  move every price in the model. This session measures the wedge and leaves
  the price system where it is.
- Equalized profit rates; wage bargaining; absolute rent; credit; RimWorld
  runtime work; sensitivity re-run.

## 8. New parameters

| parameter | default | meaning |
|---|---|---|
| `capital_service_life_days` | 600.0 | ten in-game years of use-based depreciation |
| `drug_lab_capital_money` / `_labor` | 445.0 / 41607.5 | `DrugLab`, from the closed analysis |
| `psychoid_field_capital_money` / `_labor` | 230.0 / 13120.0 | `HydroponicsBasin` |
| `refinery_capital_money` / `_labor` | 390.0 / 25835.0 | `BiofuelRefinery` |
| `provisioner_capital_money` / `_labor` | 225.0 / 16940.0 | `ElectricStove` |

## 9. Implementation order

1. Fixed capital on the process; depreciation into cost and into the value
   solve. Measure the 85-metric delta and understand it.
2. Split `unit_cost` into capital consumption and the unattributed margin,
   with the reservation price preserving behavior.
3. The `c`/`v`/`s` accumulation, organic composition, value rate of profit,
   and the per-sector price decomposition with the money-versus-labor s/v
   comparison.
4. Tests: the equilibrium still exactly stationary, the margin band bracketing
   surplus, depreciation raising values by the predicted sliver, the negative
   yayo margin reported rather than clamped, ledgers closing, determinism.
5. Reference rewrite with the deltas explained; new observations frozen
   separately.
