# Wages off the value of labor-power: design

Written before implementation. `docs/17` §3 declared this a non-goal in as
many words — "deviations of the wage from the value of labor-power —
bargaining, the reserve army, wages above value in booms — are the
interesting dynamics and are deliberately **not** built" — and left one
promise: the wage is a single rule with the basket exposed, "so later
sessions can move the wage off value without re-architecting." This is that
session.

## 1. What is being separated, and why it matters

Since `docs/17` the model has had a *value of labor-power* — the basket at
social labor values, `basket_labor_value` — and a *wage* — the basket at
current prices. They have been the same bundle read in two numeraires, and
so the money wage has never been able to move except by prices moving.

Marx's account (Capital I, ch. 25) is that the wage oscillates *around* the
value of labor-power, and that what regulates the oscillation is the
**industrial reserve army**: the pool of labor not employed. When
accumulation draws the pool down, wages rise above value; when a crisis
throws workers out, wages fall toward and below it. The value of labor-power
does not move in either case — it is the labor embodied in the habitual
means of subsistence — so the deviation is a redistribution of surplus
value between the two classes, not a change in how much surplus there is.

The model already has every ingredient. It has a regional labor pool
(`Region.labor_pool`, one worker-day a day, roughly three times equilibrium
employment) that `docs/17` §3 put in "so that labor is a real constraint the
model *can* express". It has employment as a daily outcome. It has a
separate ledger for the value of labor-power. What it lacks is the one rule
connecting them.

## 2. The rule

Per region, per day, a **wage premium** π — a dimensionless deviation of
the paid wage from the basket's cost:

```
wage  =  basket at current prices  x  (1 + π)
```

driven by the employment rate against its seeded reference:

```
e       =  worker_days_earned / labor_pool          (0 when the pool is infinite)
target  =  β (e − e_ref)
π      +=  α (target − π)
```

Proportional and damped, no threshold. `β` is `wage_bargaining_strength`:
how far the wage moves per unit change in the employment rate. `α` is
`wage_bargaining_speed`: the fraction of the gap closed each day. `e_ref` is
the employment rate at seeding, held on the region as
`reference_employment_rate` in the same way `seed_unit_cost` is — a measured
state, not a coefficient, so it is not a `ScenarioParameters` field.

Three consequences of writing it this way:

- **Off by default and bit-identical.** `β = 0` makes the target zero, the
  premium stays exactly `0.0`, and `wage_rate` skips the multiply.
- **Exactly stationary when on.** At the seeded equilibrium `e == e_ref`
  to the bit, because both are the identical expression on the identical
  float, so `target = β × 0.0 = 0.0` and π never leaves zero. The
  equilibrium scenario keeps its exactly-zero price range with bargaining
  switched on. If that ever fails, the rule has a hidden asymmetry and the
  right response is to stop, not to loosen the check.
- **An infinite reserve army pins the wage at value.** With `labor_pool =
  inf` the employment rate is zero whatever employment does, so π is
  identically zero. That is Marx's limiting case and it falls out of the
  arithmetic.

The premium can go negative. Wages below value are not an error here; they
are the slump half of the mechanism, and `docs/17` already books the milder
form (an unobtainable basket) as `basket_shortfall`.

## 3. Where the premium goes

**Into every cost that reads the wage.** `_update_wage_costs` prices each
producer's living labor at `wage_rate`, so the premium reaches effective
unit cost, the cost floor, and the price anchor through the same machinery
the subsistence shock uses. Construction labor is priced at the regional
wage (`capital_money_per_capacity`), so it is bargained too. Nothing new is
plumbed; the wage-push channel `docs/17` §3 named is the whole transmission.

**Into workers' consumption, not their savings.** Workers spend the wage
they were paid, and a premium spent on nothing would pile up as
`worker_cash` and drain the region until the wage bill fails. So the basket
workers buy scales with the premium the wages carried:

```
desired  =  quantity × worker_days_due × (1 + π_due)
```

where `π_due` is the premium on the wages being spent (yesterday's, on the
model's wages-today-bread-tomorrow rhythm). Above value they eat more than
the basket; below it, less. The silver returns to producers as basket
revenue and the circuit stays closed. `throughput_demand`'s worker term
stays at the basket — it sizes inventory *targets*, at the full-capacity
convention, and a target that chased the premium would move buffers for a
short-run reason.

**Not into the value of labor-power.** `basket_labor_value` and the
`necessary_labor` ledger are untouched. The premium is booked beside them:

- `wage_premium_paid[region]` — silver: `worker_days × basket cost × π`.
- `wage_deviation_labor[region]` — work-ticks: `worker_days × necessary_per_day × π`,
  the labor value of what workers appropriate beyond (or short of) the
  reproduction of their labor-power. Signed.

And one derived ratio, kept apart from the existing one:

```
rate_of_surplus_value           =  (L − v) / v            unchanged: wages at value
realized_rate_of_surplus_value  =  (L − v − δ) / (v + δ)  wages as paid, δ = wage_deviation_labor
```

This is the same shape as `docs/43`'s result for rent: a deviation of price
from value is a **deduction from surplus value, never a creation of it**.
The living labor `L` is what it was; the premium moves the line between
the two shares.

**Not into the price system.** `prices_of_production` takes the wage as the
physical bundle (`social_wage_bundle`) and solves a long-run system. A
bargained premium is a short-run deviation from exactly that system, and
folding it in would make `r` depend on yesterday's employment. The gap
between the price system's `r` and the ledger's money profitability will
open under a premium, and that gap is a reading, not a defect.

## 4. Scenarios

**`demand_boom`.** Final demand for yayo in Dust Basin rises by
`boom_demand_multiplier` (1.25) on day 60 and the run continues to day 360.
Measured without bargaining: yayo is already at full capacity, so the extra
demand is met by investment, and employment climbs from 0.3175 to 0.3969
worker-days — a rise of 0.079 in the employment rate. Run twice, bargaining
off and on (`β = 1`, `α = 0.1`), so every effect is a difference between
two runs of the same shock.

**`wage_slump`.** `regional_glut` with bargaining on. The glut idles the
yayo sector: employment falls to 0.0004 on day 62 and stays under 0.2 for
nine days before recovering. Short and violent, which is what a crisis is.

**`reserve_army_sweep`.** The boom at pools of 1.0, 0.5 and inf. Same shock,
different reserve army.

New parameters, all through `ScenarioParameters`:
`wage_bargaining_strength` (0.0), `wage_bargaining_speed` (0.1),
`boom_demand_multiplier` (1.25), `bargaining_scenario_strength` (1.0).

## 5. Predictions

**5.1 Nothing moves with the rule off.** All 189 frozen metrics unchanged,
and the equilibrium scenario reports exactly 0 price range with bargaining
*on* as well as off.

**5.2 The boom lifts the wage above value by less than the employment
rise.** The target is `β × 0.079 ≈ 0.079`. The premium raises every
producer's wage cost, which lowers the margin that drives investment, which
slows the employment rise that drives the premium. So the premium's peak
should land **between 0.05 and 0.08**, and reach it after the employment
does, because `α = 0.1` is a ten-day lag.

**5.3 The value of labor-power does not move at all.** `basket_labor_value`
in the bargaining run equals the non-bargaining run's to the bit at every
day. Investment adds capacity of the same technique, so the social
technique is unchanged and the value solve sees nothing. This is the
sentence the whole session exists to make true numerically: *the wage moved
and the value did not.*

**5.4 The realized rate of surplus value falls by the premium; the value
rate does not.** At the equilibrium `s/v = 26.708`, a premium of 0.07 gives
`(26.708 − 0.07) / 1.07 = 24.9`. Cumulatively over the run the realized
rate should sit **1 to 2 below** the value rate, and the value rate itself
should match the non-bargaining run to within the employment mix — which
means exactly, since 5.3 holds and `s/v` per worker-day is a value ratio.

**5.5 The reserve army sets the magnitude.** The same boom at a pool of 0.5
moves the employment rate twice as far, so the premium peak should be
**1.7 to 2.0 times** the pool-1.0 peak — less than 2.0 because the larger
premium feeds back harder on investment. At an infinite pool the premium is
**exactly zero** throughout.

**5.6 The slump pushes the wage below value, briefly and by a lot.** Nine
days near zero employment against `e_ref = 0.3175` is a target of about
`−0.3`; with `α = 0.1` the premium should reach **−0.15 to −0.25** and be
back within 0.01 of zero within a hundred days of the trough. The
cumulative `wage_deviation_labor` for the run is negative: over the whole
episode workers are paid below the value of their labor-power, and the
realized rate of surplus value for the run is *above* the value rate.

**5.7 The premium's price effect is small and its profit effect is not.**
`docs/22` measured wages at 2–4% of money cost. A 7% wage premium should
move the meal price by **under 1%** in the boom, while the yayo sector's
money margin falls by several times that. The transmission is weak for the
reason `docs/22` gave, and it is the profit share, not the price level,
that a wage deviation moves.

**5.8 The circuit stays closed.** Cash residual and value residual at
floating-point zero in every scenario. Worker cash at the end of the boom
run is within 5% of the non-bargaining run's: the premium is spent, not
hoarded.

## 6. Tests

1. Off by default: bargaining parameters at zero leave a 240-day
   equilibrium bit-identical.
2. Exactly stationary with bargaining on: premium `== 0.0` on every day of
   the equilibrium scenario and price range exactly zero.
3. An infinite pool gives a premium of exactly zero through the boom.
4. The boom's premium is positive, peaks after employment does, and the
   value of labor-power is identical to the non-bargaining run.
5. `realized_rate_of_surplus_value` is below `rate_of_surplus_value` in the
   boom and above it in the slump; both agree exactly with the premium off.
6. The slump's premium goes negative and recovers.
7. Ledgers close in the boom and the slump.
8. Halving the pool roughly doubles the peak premium.

## 7. What would make this wrong

- **If the equilibrium is not exactly stationary with bargaining on**, the
  rule has an asymmetry between `e` and `e_ref` and the check is not to be
  loosened. Stop and report.
- **If the value of labor-power moves in the boom**, something in the
  bargaining path reaches the value solve, and the whole account of the
  premium as a *deviation from* value is confused with a *change in* value.
  That would be the fifth instance of the project's recurring error
  (`docs/30`, `docs/37` §3.7, `docs/39` §5, `docs/43`).
- **If worker cash drifts monotonically**, the premium is being paid and
  not spent, and §3's consumption rule is not doing its job.
- **If the pool sweep shows the premium *independent* of the pool**, the
  rule is reading employment rather than the employment rate, and it is
  not modelling a reserve army at all.

## 8. Non-goals

No worker mobility between regions. No wage floor at subsistence — a wage
below value is the slump's substance and is reported, not prevented. No
change to the price system. No habituation of a sustained premium into the
value of labor-power (a higher basket becoming the norm), which is a real
mechanism in Marx and would need a rule for how fast habits form. No
sensitivity re-run: the boolean-free design means the new coefficients are
sweepable, and the next sweep will pick them up.
