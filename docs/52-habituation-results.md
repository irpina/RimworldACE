# Habituation: a sustained premium becomes the value of labor-power: results

`docs/51` set out ten predictions. Five held, five were wrong in part, and
one of the wrong ones is a correction to how `docs/47` should be read.

**The headline: the standard followed the premium and absorbed it, the
value of labor-power rose 7.5% while the premium was unchanged — and the
meal price came back down, because most of `docs/47`'s demand-channel price
rise was a buffer target that never followed what workers were buying.**

## 1. What shipped

One rule (`Economy._habituate`), one state (`Region.habitual_scale`), one
coefficient (`habituation_speed`, off by default), one derived reading
(`premium_over_value`), one reading renamed apart (`value_of_labor_power`
beside `basket_labor_value`), one scenario (`boom_reversal`) and one
option (`demand_boom(habituation=True)`), 20 metrics frozen (231 total),
9 tests (200 total), and the viewer shows the standard and the premium
over value as series and in the surplus panel.

The standard enters four places: the ledger's `necessary_labor`, the
price system's wage bundle, the sector organic composition's variable
capital, and the inventory targets for wage goods. It enters the paid wage
nowhere. Every entry is skipped rather than multiplied by one while the
standard is at one, and all 211 pre-existing metrics are unchanged to six
decimals with the rule off (5.1).

## 2. Held: 5.1, 5.2, 5.3, 5.4, 5.10

**5.2 Exactly stationary with both rules on.** Standard `1.0` on every day
of a 240-day equilibrium, price range exactly `0.0`. The gap the rule
closes is `(1 + 0.0) − 1.0`, which is `0.0` to the bit.

**5.3 The standard follows the premium with a lag and never overshoots.**
It ends at **1.0746**, at the top of the predicted 1.06 to 1.075, and its
peak sits 0.0045 *below* one plus the premium's peak on every day. The
premium itself ends at 0.0791 against the bargaining-only run's 0.0784: the
rule does not touch it, and the 0.9% difference is the price channel in §3.

**5.4 The premium over value is absorbed.** `(1 + π) / h − 1` ends at
**0.0041**, from a premium of 0.079. What was a 7.9% deduction from surplus
value on day 200 is a 0.4% deduction on day 360, and the rest is the
reproduction of labor-power at a higher standard.

**5.10 The circuit stays closed.** Cash and value residuals at
floating-point zero in both scenarios. The value identity cannot see the
standard, as designed: `v + s` is the living labor whatever the split.

## 3. Wrong: 5.5 and 5.8, and this is the result

Predicted: the money wage within 1% of the bargaining-only run's, and the
meal price within 1% of its 15.599, *above* it because the target rose.

Measured: the meal price ends at **15.086** — 3.3% *below* the
bargaining-only run and 0.6% above the wage-at-value run's 15.000 — and the
money wage is 3.2% lower with it. The premium is the same; the basket it
multiplies is cheaper.

The reason is the one channel `docs/51` §3 called "small". `docs/46` §3
deliberately left the inventory target for wage goods at the basket while
workers paid a premium consumed `(1 + π)` baskets, and `docs/47` §6 then
measured a 4.0% meal-price rise and attributed 3.6 points of it to demand.
That attribution was right about *where* the rise came from and wrong
about what it was. Consumption above an unmoved target holds inventory
below target indefinitely, and the price anchor's utilization term prices
that deficit as a shortage. It was a transition the planner never
finished, because the planner was never told the standard had changed.
Habituation tells it. The target rises to `h · b`, production is planned
to meet it, inventory returns to target, and the meal price settles at the
cost-push level `docs/47` measured for the cost channel — 0.43% — plus a
residual.

So `docs/47` §6's ratio of eight between the demand channel and the cost
channel stands for the model *as it was*, with buffers that ignore the
standard, and does not stand once the standard is something the economy
plans around. With the target following the standard the two channels are
of the same order. The claim that survives is the one about direction: a
wage above value reaches the price of wage goods through what workers buy,
not through what producers pay. The claim about magnitude was a fact about
a planning convention.

## 4. Wrong in part: 5.6, 5.7

**5.6** The cumulative rate of surplus value ends at **25.953**, just below
the predicted 26.0 to 26.4, because the standard formed at the top of its
predicted band and the cumulative necessary labor is correspondingly
larger. The realized rate is **25.672** against the bargaining-only run's
25.680 — 0.03% apart, inside the predicted 0.5%. The wage as paid is the
same wage; the line moved.

**5.7** The uniform rate of profit falls from 1.1726 to **1.1275** — 3.8%,
not the 6.5% the corn-model approximation gave. The approximation
`r ≈ T / (h · b) − 1` is a circulating-capital formula; with fixed capital
at 13% of the advance (`docs/37`) and turnover in the denominator, the
basket is a smaller share of what profit is charged against, and a rise in
it moves `r` by less. The direction and the mechanism held; the elasticity
came from the wrong accounting, which is the fourth entry in `docs/44`'s
table of exactly that mistake, and now the fifth.

## 5. Wrong in part: 5.9, the reversal

Predicted a standard fully formed by day 210, then frozen to the bit, a
premium over value between −0.08 and −0.04, and the two rates agreeing to
1e-3 without the rule.

Measured: the standard at day 210 is **1.021**, not 1.07. Employment
follows investment on a 45-day lead and the premium follows employment on
a 10-day lag, so the premium is barely above 0.05 by day 200; a 50-day
habit had absorbed a quarter of it. The standard then keeps forming for
the few days after the reversal that the decaying premium still sits
above it — it moves by **0.0011** — and stops when the two cross. It is
upward-only, as designed; "to the bit from day 210" assumed the premium
fell the day demand did, and it falls ten days behind.

What the scenario was for held: on day 360 the premium is **0.0001** —
the wage is back at the basket — and the premium over value is
**−0.0217**. The wage is below the value of labor-power in a region that
is not in crisis, and the realized rate (26.575) sits above the value
rate (26.403), the slump ordering, with no slump. Without the rule the
premium ends at −0.0 and the premium over value is the premium: the wage
is at value and there is nothing for it to sit below.

The "agree to 1e-3 without the rule" prediction was wrong for a reason
that has nothing to do with the rule: both rates are *cumulative* over the
run, and the boom's 150 days of premium are in the ledger whether or not
demand reversed. The daily rates would agree; the ledger's do not, by
0.131. The test asserts what the design meant.

## 6. Carried forward

**Buffers were part of the wage-price story** (§3). Any reading of
`docs/47` §6 should be followed by this section. The next thing that reads
"the demand channel is eight times the cost channel" should ask what the
inventory target was doing.

**The reversal scenario is under-formed at day 210.** A reversal at day
300 with the run extended to 450 would show the standard near its peak
before the wage falls back. It is a parameter (`boom_reversal_day`) and
the viewer can run it; it was left at 210 so the results score the design
as written.

**Downward habituation is still absent**, deliberately, and the reversal
shows what its absence means: the standard stays at 1.022 forever.

## 7. Cost

Four runs of 360 days, about 0.8 s of the metric collection.
