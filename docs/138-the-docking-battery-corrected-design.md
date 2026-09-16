# The docking battery, corrected: design

Written before it is run. Measured in `docs/139`; the memo rests on
that, in `docs/140`.

## 1. What changed since `docs/136`

`docs/137` §2 traced the collapse to three interactions and §3 named
the corrections. Two are in `build_ours` now — the workers' seed
scales with the fund's, and `investment=False` puts the fund's
investment events beyond the run — and the third is the choice of
money stock, which `docs/137` said must be measured against the
purses' *grown* claim rather than taken from `docs/135` A. Measured at
design time, one seed, thirty months, investment off, workers' seed
scaled, both rules on, spread 1.0, retention 0.5:

| cash × | unit | employing | deaths | fund at end | GDP growth std | sector CV | cost rank |
|---|---|---|---|---|---|---|---|
| **0.3** | **20** | **789** | **91** | 0.095 | 0.032 | 0.14 | −0.81 |
| 0.3 | 60 | 588 | 213 | 0.261 | 0.044 | 0.12 | −0.78 |
| 1 | 20 | 727 | 160 | 0.313 | 0.020 | 0.16 | −0.76 |
| 1 | 60 | 548 | 247 | 0.681 | 0.018 | 0.15 | −0.75 |
| 3 | 20 | 738 | 140 | 0.637 | 0.007 | 0.20 | −0.81 |
| 3 | 60 | 524 | 270 | 0.885 | 0.018 | 0.17 | −0.81 |

Every cell survives once investment is off and the workers' seed is
scaled — which is the confirmation of `docs/137` §2's diagnosis that
this document needed before choosing anything. The unit of 20 is
better than 60 at every stock (fewer deaths, more employing), and
×0.3 × 20 is the best cell on both counts with the most GDP movement
of the 20-unit column. It is also the cell with the *least* silver
left in the fund, 9.5%, which is the price of a demand that moves.

## 2. The configuration

As `docs/136` §2, with: `investment=False`; the workers' seed scaled;
`cash_multiplier = 0.3`, `construction_cost_multiplier = 20` from the
grid above. Everything else unchanged and sourced as there. Twenty
seeds each side, thirty months after six of burn-in.

## 3. Numbered predictions

All two-sided; medians over twenty seeds unless stated. The anchors are
the one-seed row above, with bands wide enough for seed variance
(`docs/133`'s twenty-seed ranges ran to ±50% on counts).

1. **Money is conserved on every seed**: `|cash_balance| < 1e-9 M`.
2. **The population lives**: employing in **[600, 950]**; bankruptcies
   in **[40, 200]**; fund at end in **[0.03, 0.30]** of M.
3. **GDP moves, modestly**: GDP growth std in **[0.015, 0.080]**;
   excess kurtosis in **[−1.5, 8]**.
4. **Sectors are cost-ranked and boundedly dispersed**: cost rank ρ in
   **[−1.0, −0.6]**; sector CV in **[0.07, 0.30]**.
5. **No tail, and the instrument says so**: `x_min` over the largest
   firm, median, in **[0.10, 0.60]**; firm growth excess kurtosis in
   **[30, 1000]**.
6. **The wage share keeps its basis**: production wages over value
   added in **[0.008, 0.020]**; with construction in **[0.60, 0.95]**.
7. **Demises** per firm-month in **[0.002, 0.020]**.
8. **The control is bit-identical** to `docs/129` §2.
9. **Unemployment** in **[0.85, 0.97]**, an artefact of the labour-pool
   ratio and of a population that only shrinks with investment off.

If 1–4 and 6–8 hold and 5 holds as stated, the docking is closed on
the terms `docs/136` §3 set out.
