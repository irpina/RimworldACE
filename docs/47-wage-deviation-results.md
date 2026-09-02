# Wages off the value of labor-power: results

`docs/46` set out eight predictions for a reserve-army wage rule. Six held,
one held for the wrong reason, and one was wrong about the channel — and
the wrong one is the finding.

**The headline: the wage moved and the value did not; and the price effect
of a wage above value runs through what workers *buy*, not through what
producers *pay*.**

## 1. What shipped

One rule (`Economy._bargain`), two coefficients, two ledger buckets, one
derived ratio, three scenarios, 22 metrics frozen (211 total), 191 tests.

The wage premium π moves each day a fraction `wage_bargaining_speed` of the
way toward `wage_bargaining_strength × (e − e_ref)`, where `e` is
yesterday's employment over the labor pool and `e_ref` the rate at seeding.
The paid wage is the basket at prices times `1 + π`; workers' consumption
scales with the premium their wages carried; `necessary_labor` stays the
value of labor-power and the deviation is booked beside it as
`wage_deviation_labor`. `realized_rate_of_surplus_value` reads the ledger
with wages as paid. Off by default, and all 189 pre-existing metrics are
unchanged to six decimals with the rule off.

## 2. Held: 5.1, 5.4, 5.5, 5.8

**5.1 Exactly stationary with the rule on.** Premium `0.0` on every day of
a 240-day equilibrium run, price range exactly `0.0`. The reference rate is
the seeded rate on the identical float, so the target is `β × 0.0` and the
premium never leaves zero. Frozen as `bargaining.equilibrium.*`.

**5.4 The premium is a deduction from surplus value.** In the boom the
value rate of surplus value is 26.708 and the realized rate 25.680 — 1.03
below, inside the predicted 1 to 2. In the slump the realized rate is
26.836, *above* the value rate, because over the whole episode workers
were paid 446 work-ticks below the value of their labor-power. The value
rate on and off the rule agree to 2e-8 (the employment quantum), and the
living labor is what it was in both runs. The line moved; the total did
not, which is the same shape `docs/43` found for rent.

**5.5 The reserve army sets the magnitude.** Halving the pool gives a
premium peak 1.972 times the full-pool peak (predicted 1.7 to 2.0). At an
infinite pool the premium is exactly zero throughout: the employment rate
is zero whatever employment does, and the wage is pinned to value. Marx's
limiting case is the arithmetic of a ratio.

**5.8 The circuit stays closed.** Cash and value residuals at floating-point
zero in both scenarios; worker cash at the end of the boom is 0.1% above
the no-rule run's (predicted within 5%). The premium is spent, not hoarded.

## 3. Held, for the wrong reason: 5.2

The boom's premium peaks at **0.0784**, at the top of the predicted 0.05 to
0.08 band. The prediction said it would fall short of the target
`β × 0.079` because the premium raises wage costs, which lowers margins,
which slows the investment that drives employment. That feedback exists
and it is tiny: employment ends at 0.3959 with the rule against 0.3969
without — a 0.25% difference. The premium sits **at** its target, because
the target barely moved. The number landed in the band; the mechanism I
gave for it is a rounding error.

And the premium is still at its peak on the last day. A permanent rise in
demand is a permanent rise in employment, so the wage stays above value
indefinitely. `docs/46` §8 named the piece that would eventually absorb
it — a higher basket becoming habitual — and it is still absent, so this
model has a *permanent* deviation where Marx has a *tendency*.

## 4. Wrong: 5.3, to the bit

Predicted: the value of labor-power identical to the bit in both runs.
Measured: **one ulp apart** — 866.16993045634**92** against 866.16993045634**93**,
a relative gap of 1.3e-16.

The technique is the same in both runs and so is the wage bundle, so the
mathematical value is identical. The *solved* value is not, because the
value solve weights each region's technique by its output, the two regions
run at slightly different outputs when investment differs, and the
weighted average of two equal numbers is not bitwise the same number for
every weight. The substantive claim holds — the premium never touches the
value solve — and the metric freezes the gap so that it can only ever grow
by something reaching in. But the prediction was "to the bit" and the
answer is "to one ulp", and those are different sentences.

## 5. Wrong: 5.6, the slump is shallower

Predicted a trough of −0.15 to −0.25. Measured **−0.113** on day 70, back
to −2e-14 by the end of the run (predicted within 0.01 of zero inside a
hundred days; held).

The arithmetic in the prediction assumed the target sat at −0.32 for the
nine days employment was under 0.2. It does not: employment recovers
progressively from the trough, so the target is climbing back toward zero
while the premium is still falling toward it, and the two meet at a third
of the way down instead of two thirds. A ten-day lag against a nine-day
crisis is a filter, and the filter takes most of it out. The rule *does*
push the wage below value — the sign, the recovery and the negative
deviation ledger all held — but a slump this brief cannot drive it far.

## 6. Wrong about the channel: 5.7

This is the result.

Predicted: the meal price moves by under 1% because wages are 2–4% of
money cost (`docs/22`), and the yayo sector's money margin falls by
several times that. Measured: the meal price ends at **15.599 against
15.000** without the rule — a **4.0%** rise — and yayo's margin falls 1.0%.

The cost-push part of that is what was predicted. The meal producer's wage
cost per unit rises from 0.5334 to 0.5982 silver, and that 0.065 is
**0.43%** of the meal price. Under 1%, as `docs/22` said it would be.

The other 3.6% is not cost. Workers paid 7.8% above value **eat 7.8%
more**, by the consumption rule in `docs/46` §3. Meal output rises from
0.794 to 0.854 of capacity, meal inventory sits below target, and the
price anchor's utilization term does the rest. The wage premium's price
effect arrives through the *demand* for wage goods, and it is eight times
the size of the effect through their *cost*.

That is a different account of wage-price transmission from the one the
project has carried since `docs/22`. There, a wage change reached prices
through the cost floor and was small because the wage share of cost is
small. That is still true of the cost channel. But a wage above value is
also a real wage above the basket, and a real wage above the basket is
extra demand for exactly the sectors that produce the basket. The price of
wage goods rises not because they cost more to make but because more of
them are wanted. Marx's account of the boom has this: rising wages and
rising prices of necessaries together, with the second not caused by the
first through cost. The model got there by running the rule, not by being
told.

Two things follow. First, `docs/22`'s transmission strength was measured
on a wage that could only move with prices, so a real-wage channel never
existed to be measured; its finding stands for what it measured and does
not cover this. Second, the effect is confined to the basket sectors. Yayo
is not a wage good, its price rises 0.4%, and all of that is cost.

## 7. Two things carried forward

**The deviation is permanent under a permanent shock** (§3). A model with
the reserve army and no habituation has a wage that sits above value for
as long as employment sits above its reference. The next rule in this
family is the one that lets a sustained premium become the new basket, and
it needs a speed of its own.

**The real-wage channel is now the larger of the two** (§6). Anything that
later reads "wages barely reach prices" from `docs/22` should read this
section next: that was the cost channel, and the demand channel is eight
times larger for the goods workers buy.

## 8. Cost

The three scenarios together are six runs of 300 to 360 days of the
six-commodity economy, about a second and a half of the seven-second metric
collection. Cheap, because the boom needs no Department I and no exit.
