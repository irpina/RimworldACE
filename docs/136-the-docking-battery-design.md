# The docking battery: design

Written before it is run. Measured in `docs/137`; the memo that rests on
it is `docs/138`.

## 1. The decision

`docs/135` §5 put the choice: add a stochastic market rule and chase
Wright's tail, or dock on what a deterministic laboratory shares with
him. The second was chosen. This document fixes the configuration on
which the docking is closed and predicts, two-sided, every row of the
final comparison — the facts that transfer and the facts that do not —
so that `docs/137` is a scoring and not a selection.

## 2. The configuration, each parameter from the sweep that measured it

Nothing here is chosen by taste; each value is the one its own sweep
found, and the document that found it is named.

| parameter | value | from |
|---|---|---|
| `commodities`, `regions` | 200, 2 | `docs/124` §3 |
| `DEMAND` | 800 | `docs/126` §1 (×200) × `docs/130` §2 (k = 4) |
| `basket_in_demand` | on | `docs/128` |
| `producers_per_commodity` | 4 | `docs/130` |
| `cost_spread` | 1.0 | `docs/135` §3, the largest dispersion measured |
| `fund_spending` | on | `docs/132` |
| `cash_multiplier` | 0.3 | `docs/135` §2, the healthiest stock that seeds |
| `accumulate`, `retention_rate` | on, 0.5 | `docs/132`, `docs/135` §4 |
| `construction_cost_multiplier` | 20 | `docs/135` §4, the best cell |
| `producer_employment_quantum` | 1.0 | `docs/124` §3 |
| `investment_interval_days` | 180 | `docs/124` §3 |

Twenty seeds of ours, twenty of the SA control through the same
`facts()`, thirty months after six of burn-in. The four parameters
last swept were each measured with the others at their old values, so
their interaction is untested; that is what predictions 2 and 3 are
for.

## 3. Numbered predictions

All two-sided; medians over seeds unless stated.

1. **Money is conserved on every seed**: `|cash_balance| < 1e-9 M`.
2. **The population lives under the interaction.** Employing producers
   at the end in **[600, 1000]** of 1,000 viable; bankruptcies per run
   in **[30, 250]**.
3. **GDP moves.** GDP growth std in **[0.05, 0.40]** (`docs/135` A at
   ×0.3: 0.18) and GDP growth excess kurtosis in **[−1.5, 10]**.
4. **Sectors are cost-ranked and dispersed, boundedly.** Cost rank ρ in
   **[−1.0, −0.5]**; sector CV in **[0.10, 0.60]**.
5. **There is no tail, and the instrument says so.** The MLE's `x_min`
   over the largest firm, median across seeds, in **[0.10, 0.50]** — a
   fit to the top fraction of the authored spread, as `docs/135` §3
   read it — and firm growth excess kurtosis in **[40, 2000]**. These
   are the facts that do not transfer, pinned rather than left vague.
6. **The wage share keeps its basis and construction is sized.**
   Production wages over value added in **[0.008, 0.020]**; with
   construction wages in **[0.30, 0.80]** (`docs/135` C at 0.5 × 20:
   0.69).
7. **Demises** per firm-month in **[0.002, 0.030]**.
8. **The control is bit-identical** to `docs/129` §2: SA α 1.278,
   growth kurtosis 4.21, wage share 0.538, to the printed digit.
9. **Unemployment** in **[0.55, 0.90]** — the labour-pool ratio
   inherited from `docs/124`, recorded as an artefact and not a fact.

If 1–4 and 6–8 hold and 5 holds *as stated*, the docking is closed on
these terms: our laboratory shares with Wright's the money circuit,
the wage share as an accounting quantity, cost-ranked competition and
an endogenous crisis, and does not share his firm-size or firm-growth
distributions because it has no source of revenue independent of cost.
