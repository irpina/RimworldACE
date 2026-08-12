# Upstream observation and glut hysteresis

This note records an observation-only checkpoint before capital goods are added.
No economic behavior changed in this session.

## The behavioral reference now covers upstream markets

The original thirteen frozen metrics remain unchanged in name, meaning, and
value. Forty additional observations now cover local psychoid leaves and
chemfuel in both the yayo-glut and drug-lab-loss scenarios:

- price trough and peak, with the day of each;
- inventory trough and peak, with the day of each;
- the settled endpoint for the stationary glut path;
- the terminal observation for producer loss, whose upstream path is still
  moving when that scenario ends.

These are report values, not acceptance tests. The 23 invariant tests remain
the authority for accounting and determinism.

Headline newly frozen values include:

| scenario | commodity | price trough | inventory extreme/end state |
|---|---|---:|---:|
| yayo glut | psychoid leaves | 1.698233 on day 180 | settles at 1,771.071075 |
| yayo glut | chemfuel | 2.215520 on day 180 | settles at 124.276777 |
| drug-lab loss | psychoid leaves | 0.488952 on day 72 | trough 925.541877 on day 92 |
| drug-lab loss | chemfuel | 1.086166 on day 83 | peak 167.446333 on day 77 |

## Finding: the glut hysteresis is a control-law bug

The permanent upstream displacement is **not** a reallocation of productive
capacity. Psychoid-leaf capacity stays at 80 units/day, chemfuel capacity stays
at 6, and neither sector starts an investment project.

The sequence is:

1. The yayo injection lowers the final-good price and temporarily curtails drug
   lab output.
2. Psychoid fields and chemfuel synthesis continue at full output, so unused
   inputs accumulate.
3. Yayo later returns to 10 units/day. Its inputs then return to exactly 80
   leaves and 2 chemfuel/day.
4. Upstream production is exactly 80 leaves and 6 chemfuel/day; the remaining 4
   chemfuel feeds the fields. Each upstream inflow therefore exactly equals use.
5. With no net drain, the temporary overhang becomes permanent. The price rule
   correctly assigns a lower price to the excess stock, but that lower price is
   still above the producers' full-utilization threshold, so output does not
   fall and the stock cannot return to target.

The quantities identify the cause exactly. Across a 600-day post-shock trace,
the drug lab produces 21.383884 fewer yayo than an uninterrupted full-capacity
path. The resulting excesses are:

| commodity | observed overhang | missing yayo × input ratio | difference |
|---|---:|---:|---:|
| psychoid leaves | 171.071074804747 | 171.071074804742 | 4.3e-12 |
| chemfuel | 4.276776870119 | 4.276776870119 | 1.3e-13 |

The material ledgers close, so this is not creation or destruction of material.
It is nevertheless a bug in the model's feedback structure: upstream production
responds to price, the price responds to stock, but the displaced price does not
cross the utilization threshold needed to remove the stock displacement. The
model consequently has a continuum of stationary upstream stocks instead of a
unique stock target.

Do not fold a fix into capital-goods work. First choose and document a control
rule that lets excess intermediate inventory reduce net upstream production,
then accept the resulting baseline movement deliberately in its own commit.

## Observation limits to carry forward

### Multi-commodity arbitrage is thresholded, not absent

Arbitrage is single-commodity in the current scenarios by calibration rather
than architecture. Standard-route freight is 3.5 silver plus 10% risk markup,
or 3.85 per unit. The glut's widest intermediate price spread is about 0.2, so
only yayo clears the freight threshold. If freight falls below the intermediate
spread or intermediate volatility rises above freight, those commodities begin
competing abruptly for the same route capacity.

### Recovery days are quantized

The recovery metrics observe the first whole-day crossing of a threshold. A
sub-day path change can therefore report a zero-day delta. A later observation
session should add a continuous complement, preferably area between the price
path and its baseline over a fixed window. Keep the existing recovery-day
metrics for legibility; do not silently replace their semantics.
