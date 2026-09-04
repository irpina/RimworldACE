# Habituation: a sustained premium becomes the value of labor-power: design

Written before implementation. `docs/47` §3 ended with the boom's premium
still at its peak on the last day: "a permanent rise in demand is a
permanent rise in employment, so the wage stays above value indefinitely",
and named the missing piece as "a higher basket becoming habitual". §7
carried it forward as "the next rule in this family", with the note that it
"needs a speed of its own". This is that rule.

## 1. What is being separated

The value of labor-power is the labor embodied in the *habitual* means of
subsistence. Marx is explicit that the habitual part is not a constant:
"the number and extent of his so-called necessary wants, as also the modes
of satisfying them, are themselves the product of historical development"
(Capital I, ch. 6). A wage that sits above the value of labor-power for
long enough stops being a premium and becomes the standard; the value of
labor-power has risen, and what the same wage now carries above it is
smaller. Nothing about the *paid* wage changed. What changed is how much of
it is the reproduction of labor-power and how much is a deduction from
surplus value.

The model since `docs/46` has three quantities that make this expressible:

- the **basket** `b`, a bundle per worker-day, fixed at seeding;
- the **value of labor-power**, `b` at social labor values, which moves
  only when the technique of making wage goods moves (`docs/20`);
- the **wage premium** `π`, the paid wage's deviation from `b` at current
  prices, set by the reserve army.

What it lacks is a fourth: a **habitual scale** `h` on the basket, so that
the value of labor-power is `h · b` at values, and the premium *over
value* is what the paid wage carries above `h · b` at prices.

## 2. The rule

Per region, one state, `habitual_scale`, `1.0` at seeding. Per day, after
the reserve army has moved the premium:

```
h  +=  α_h · max(0, (1 + π) − h)
```

`α_h` is `habituation_speed`, the fraction of the gap between the standard
and the paid real wage that becomes habit each day. Three properties fall
out of writing it this way:

- **Off by default and bit-identical.** `α_h = 0` returns before touching
  anything, and every place `h` enters is skipped rather than multiplied
  by one when `h == 1.0`, the same discipline `wage_rate` uses for the
  premium.
- **Exactly stationary when on.** At the seeded equilibrium `π` is exactly
  `0.0` (`docs/47` §2), so the gap is `max(0, 1.0 − 1.0) = 0.0`, and
  `h + α_h · 0.0` is `h` to the bit. The equilibrium keeps its
  exactly-zero price range with both rules on.
- **Upward only.** A standard that has risen does not fall when the
  premium goes. That is the asymmetry the concept carries: habits resist
  being unlearned, and a wage that falls back after the standard has risen
  is a wage *below the value of labor-power*, which is the slump's
  substance and not a mistake. It is the same shape `docs/46` chose for a
  negative premium: reported, not prevented. A downward speed could be
  added as a second coefficient; it is not, because nothing in the
  scenarios below needs it and a dead parameter is worse than an absent
  one.

**The paid wage is untouched.** `wage_rate` stays `b` at prices times
`1 + π`, and the reserve-army rule still sets `π` against the seeded
reference employment. The choice here is deliberate and the alternative
was considered: letting the premium be bargained *over the habitual level*
(`wage = h · b · (1 + π)`) makes the real wage ratchet without bound under
a permanent boom, because the tightness that set `π` is still there after
`h` has absorbed it, and the model's only brake, wages cutting investment,
is the 0.25% feedback `docs/47` §3 measured. That is a wage-price spiral
with no wage-profit-accumulation loop to end it, and it would be the
model's artefact rather than Marx's mechanism. What habituation changes is
the *accounting* of a wage the market has already set, and two long-run
quantities that read the standard.

## 3. Where the scale goes

**Into the value of labor-power, and so into the ledger.** The daily
booking in `_produce` becomes

```
necessary_labor        +=  worker_days · h · b_value
wage_deviation_labor   +=  worker_days · b_value · (1 + π − h)
```

so that the two still sum to the wage as paid, `worker_days · b_value ·
(1 + π)`, and `realized_rate_of_surplus_value` is unchanged by `h` by
construction. `rate_of_surplus_value` reads `necessary_labor` and falls as
`h` rises. The living labor is what it was; the line moved again, this
time the other way.

**Into the two long-run readings of the standard.** `docs/46` §3 kept the
premium out of the price system because a bargained premium is a short-run
deviation from exactly that system. The habitual standard is not short-run;
it is the long-run real wage, and the classical system's `b / T` is
precisely the long-run real wage. So `social_wage_bundle` carries `h · b`,
and the uniform rate of profit falls when the standard rises, which is the
oldest result in the subject. Likewise `sector_organic_composition`'s
variable capital, which `docs/42` insisted must be the value of
labor-power and not the money wage, reads `h · b`.

**Into what the economy provisions for.** `throughput_demand`'s worker term
sizes inventory targets at the basket per worker-day at full-capacity
employment. That term becomes `h · b`: the standard the region plans its
wage-good buffers around is the habitual one. The intended outflow in
`_planned_runs` reads the same. This is the one place habituation has a
*behavioral* consequence of its own rather than an accounting one, and it
is small: `docs/46` §3 deliberately left the target at the basket while
consumption ran at `(1 + π) · b`, so under habituation the target moves
toward what workers already buy.

**Not into consumption.** Workers already consume `(1 + π_due) · b`
(`docs/46` §3); the paid wage is unchanged, so what it buys is unchanged.

**Not into the reserve army.** `π` is still measured against the seeded
basket, for the reason in §2.

One derived reading, kept apart from `wage_premium`:

```
premium_over_value  =  (1 + π) / h − 1
```

equal to `π` while `h` is one, and what remains of the premium once the
standard has absorbed the rest.

## 4. Scenarios

**`demand_boom(bargaining=True, habituation=True)`.** The `docs/46` boom,
with both rules. `α_h = 0.02`, a fifty-day time constant against the
reserve army's ten: habits form more slowly than wages move, and the ratio
is the one coefficient here that is a choice rather than a derivation. It
is a `ScenarioParameters` field (`habituation_scenario_speed`) and the
sweep will pick it up.

**`boom_reversal(habituation=True|False)`.** The boom, and then on day 210
final demand returns to its seeded level and the run continues to day 360.
Without habituation the premium falls back to zero and the accounting to
where it started. With it, the standard stays where the boom left it and
the paid wage does not: the wage is below value for the rest of the run,
in a region that is not in crisis. That is the scenario the rule exists
for, and the reason it is upward-only.

New parameters: `habituation_speed` (0.0), `habituation_scenario_speed`
(0.02), `boom_reversal_day` (210).

## 5. Predictions

5.1 **Bit-identical off.** All 211 frozen metrics unchanged to six decimals
with `habituation_speed = 0`, including the 22 bargaining readings.

5.2 **Exactly stationary on.** `h = 1.0` on every day of a 240-day
equilibrium with both rules on; price range exactly `0.0`.

5.3 **The standard follows the premium with a lag and does not overshoot.**
In the boom `π` reaches 0.078 around day 200 and stays; with `α_h = 0.02`
the gap closes by `e^{-0.02 t}`, so `h` ends between **1.06 and 1.075** and
never exceeds `1 + max π` on any day.

5.4 **The premium over value is absorbed.** `premium_over_value` on day
360 is under **0.015**, from a `π` of 0.078.

5.5 **The value moved and the wage did not.** The value of labor-power
`h · b` ends 6 to 7.5% above the bargaining-only run's; the paid wage
differs from that run's by less than 1%, the difference being the
buffer-target channel in §3.

5.6 **The value rate falls toward the realized rate.** Cumulative over the
run, `rate_of_surplus_value` ends between **26.0 and 26.4** (bargaining
only: 26.708), and `realized_rate_of_surplus_value` is within **0.5%** of
the bargaining-only run's 25.680, because the wage as paid is the same
wage.

5.7 **The general rate of profit falls.** The price system's `r`, read at
the end of the boom, falls from 1.1726 to between **1.09 and 1.12**: near
the corn-model approximation `r ≈ T / (h · b_labor) − 1`, in which a 7%
rise in the standard is a 6.5% fall in `r`, and above it because the
enlarged basket broke the rank-one identity (`docs/29`).

5.8 **The buffer channel is small.** The meal price at the end of the boom
is within **1%** of the bargaining-only run's 15.599. Above it, not below,
because the target rose.

5.9 **The reversal leaves the wage below value.** In `boom_reversal` with
habituation, on day 360: `h` is unchanged from its value on day 210 to the
bit (upward only, and `π` is at or below zero after the reversal);
`premium_over_value` is between **−0.08 and −0.04**; and
`realized_rate_of_surplus_value` is *above* `rate_of_surplus_value`, the
slump ordering, while in the same run without habituation the two agree
to within 1e-3.

5.10 **The circuit stays closed.** Cash and value residuals at
floating-point zero in every scenario. The value identity cannot see `h`:
`v + s` is the living labor whatever the split.

## 6. What would make this wrong

If 5.2 fails, some path multiplies by `h` without the `h == 1.0` guard or
the rule has a hidden asymmetry; stop rather than loosen. If 5.7's `r`
falls by much more than the basket rose, the bundle is entering the price
system twice. If 5.9's `h` moves after day 210, the `max(0, ·)` is not
where the design says it is.

## 7. Non-goals

No downward habituation. No change to the reserve-army rule or its
reference. No premium in the price system: `h` is in it, `π` is not, and
that line is the whole point. No worker mobility. No re-run of the sweep;
the coefficients are sweepable and the next sweep picks them up. No
consumer-choice response to the standard, which would need a utility
function the model does not have and should not acquire.
