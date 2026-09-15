# Several firms per commodity: design

Written before anything is built or run. Measured in `docs/131`.

## 1. Why

`docs/124` §5 through `docs/129` §3 have said the same thing four ways:
our firm-size reading is the input-output graph, because the generator
gives every commodity exactly one producer per region and sizes it to
authored demand. `docs/125` §4's item 2 asked for a scenario in which
firm size could be a market outcome. The model can already host one —
a sector's order book is shared among its producers by posted price
with elasticity `competitive_share_elasticity = 2.0` (`docs/21`,
`docs/57`), investment completes new entrants into a sector, and
bankruptcy removes them — but the generator never builds a sector with
more than one firm in it, so none of that machinery has been exercised
at scale.

This puts several firms in every sector and measures what the model's
own competition does with them. It does **not** add a market lottery,
retained-profit growth or any other Wright rule to our lab; the point is
to find out what our rules produce, and the design predicts they will
not produce his tail.

## 2. What is built

A generator parameter, `producers_per_commodity: int = 1`, with
`cost_spread: float = 0.1`. When `k > 1`, each commodity's authored
capacity is split equally among `k` producers, and each producer's
operating overhead is multiplied by `1 + cost_spread × (u − ½)` for a
`u` from a **separate** deterministic stream (`_Random(seed + 1)`), so
the `k = 1` path does not consume a single draw it did not before and
the fixtures stay bit-identical. Names are `region:commodity#j`. The
battery passes the knob through and adds two structural readings:

- **cost rank ρ**: Spearman correlation, pooled over sectors with at
  least two employing producers, between within-sector overhead rank
  and within-sector employment rank. Competition that works makes it
  negative.
- **sector CV**: the median over such sectors of the coefficient of
  variation of employment among the sector's producers. Dispersion the
  competition generates, as opposed to dispersion the graph authored.

The battery run is `k = 4` at `DEMAND = 800`, so that a quarter-sized
firm still needs the same ~3.7 whole workers `docs/126` chose. That is
1,000 viable firms per run against `docs/129`'s 250.

## 3. Numbered predictions

All two-sided.

1. **Bit-identical at `k = 1`.** Fixtures unchanged bar the one-ULP
   `scale_647_day3`; baseline 322 at zero.
2. **The population lives.** After 180 days, employing producers in
   **[700, 1000]** of 1,000 viable and bankruptcies in **[0, 150]**.
3. **Competition orders the sector.** Cost rank ρ at day 180 in
   **[−1.0, −0.3]**: the cheaper producer is the larger one. Above −0.3
   the elasticity is not doing what `docs/21` says at this scale.
4. **But it does not spread the sector.** Sector CV in **[0.05, 0.40]**.
   A 10% overhead spread through an elasticity of 2 is a ~20% share
   spread; nothing in our rules amplifies that into orders of
   magnitude, because no producer's share feeds back into its cost.
5. **Growth remains inventory oscillation.** Firm growth excess
   kurtosis in **[10, 500]** and growth std in **[0.1, 0.5]** — the same
   signature as `docs/129`, now with four times the firms.
6. **Demises rise but stay an order below Wright's.** Demise rate per
   firm-month in **[0.005, 0.05]** (Wright 0.18; `docs/129` 0.0099):
   smaller firms sit nearer the quantum.
7. **The exponent still does not settle.** Across 20 seeds the MLE's
   `x_min` spans a factor in **[10, 1000]** between its smallest and
   largest, which is `docs/119` §2's bifurcation and the sign that
   there is no power law to find.

Predictions 3 and 4 together are the finding: the model's competition
is real and bounded. If 4 fails high — a CV above 0.4 — then something
in the order book, posted prices, entry or exit *does* amplify a small
cost difference, and that mechanism is the first thing our lab would
have in common with Wright's, worth its own document.
