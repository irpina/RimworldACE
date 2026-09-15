# The parameters the rules multiply: design

Written before anything is run. Measured in `docs/135`.

`docs/133` §4 found that the two Wright rules of `docs/132` do what they
say and that what they *produce* is set by four parameters chosen for
other purposes: the battery's money stock, the generator's cost spread,
and the construction unit and retention rate behind accumulation. No
rule changes here; three sweeps over those, all at `k = 4`,
`DEMAND = 800`, both rules on, thirty months.

## 1. The three sweeps

**A. Money stock against flow.** `CASH_MULTIPLIER` ∈ {10, 3, 1, 0.3,
0.1}, one seed each. The fund's spending rate is seeded so that day
one's demand is the authored one whatever the stock, so a smaller stock
turns over faster and the demand it funds follows distributions more
closely.

**B. Cost spread.** `cost_spread` ∈ {0.1, 0.3, 0.6, 1.0}, five seeds
each. Within a sector the posted price is one, so the overhead spread
is the *only* source of growth-rate heterogeneity a deterministic lab
has. This is the Gibrat-with-drift experiment.

**C. Construction against margin.** `retention_rate` ∈ {0.5, 0.2, 0.05}
× `construction_cost_multiplier` ∈ {60, 20}, three seeds each. Both
parameters scale how much of a producer's margin becomes construction,
and therefore how fast total capacity outruns demand.

`build_ours` gains `cash_multiplier`, `cost_spread` and
`construction_cost_multiplier` knobs; the sweep driver is
`economy_lab/parameter_sweeps.py`.

## 2. Numbered predictions

All two-sided; "spread" means the ratio of the largest to the smallest
`x_min` the MLE picks across the cell's seeds.

1. **A: a smaller stock makes GDP move.** GDP growth std is monotone
   non-decreasing as the multiplier falls from 10 to 0.3, and at 0.3 it
   lands in **[0.02, 0.30]** (10: 0.011).
2. **A: there is a floor, and rule one lowers it.** Payroll fails (the
   model's `cannot cover its wage bill`) at some multiplier in
   **[0.1, 1.0]**, and not at 3. `docs/124` §3 measured failure at the
   generator's ×1 *without* rule one; with the fund spending what it
   receives, ×1 is predicted to survive.
3. **B: the spread drives dispersion.** Sector CV at month 30 is
   monotone non-decreasing in `cost_spread`, and at 1.0 lands in
   **[0.15, 1.50]** (0.1: 0.021).
4. **B: and it compounds.** At `cost_spread = 1.0`, sector CV at month
   30 is between **2× and 20×** its value at month 6. Under a linear
   ratio it is drift; under a flat one it is a static cost ranking.
5. **B: it does not make a power law.** At every spread the `x_min`
   spread across seeds is in **[20, 2000]** or the growth kurtosis is
   above **40**. This is the standing question of `docs/133` §4 made
   falsifiable: I predict that a deterministic lab does *not* produce
   Wright's tail from cost heterogeneity alone, and that his lottery is
   load-bearing. A cell that fails both clauses would be the most
   important result since `docs/116`.
6. **C: construction can be made a plausible share.** At
   `retention_rate = 0.05`, `construction_cost_multiplier = 20`, the
   total wage share (production plus construction over value added)
   lands in **[0.03, 0.30]** (0.5 × 60: 0.735), and the production wage
   share stays in **[0.008, 0.020]**.
7. **C: and the crisis eases with it.** Bankruptcies per run at that
   cell land in **[30, 130]** (0.5 × 60: 178, both rules off: 55), and
   end-of-run employing producers in **[700, 1000]** (594).
8. **C: but the ordering survives.** Cost rank ρ stays in **[−1, −0.5]**
   at every cell: the cheaper firm is the larger one however little it
   is allowed to retain.

Predictions 5 and 4 are the substance; 1 and 6 are the calibration.
