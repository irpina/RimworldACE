# The docking battery, corrected: results

Design in `docs/138`. Twenty seeds each side, committed as
`economy_lab/battery138_results.json`. **All nine predictions hold**,
and the docking is closed on the terms `docs/136` §3 set out.

## 1. Scoring the predictions

| # | prediction | measured (median; range) | verdict |
|---|---|---|---|
| 1 | \|cash_balance\| < 1e-9 M, every seed | 1.6e-14 | pass |
| 2 | employing ∈ [600, 950]; deaths ∈ [40, 200]; fund ∈ [0.03, 0.30] | **718** (120–863); **127** (68–348); 0.105 | pass |
| 3 | GDP growth std ∈ [0.015, 0.08]; kurtosis ∈ [−1.5, 8] | **0.061** (0.017–1.15); 1.88 | pass |
| 4 | cost rank ∈ [−1, −0.6]; sector CV ∈ [0.07, 0.30] | **−0.795** (−0.88 to −0.74); **0.146** | pass |
| 5 | `x_min`/largest ∈ [0.1, 0.6]; growth kurtosis ∈ [30, 1000] | 0.203; 231 | pass, as stated |
| 6 | production share ∈ [0.008, 0.02]; total ∈ [0.6, 0.95] | 0.0198; 0.837 | pass |
| 7 | demises ∈ [0.002, 0.02] per firm-month | 0.0070 | pass |
| 8 | control bit-identical to `docs/129` | α 1.2778, kurtosis 4.2112, wage share 0.5382 | pass |
| 9 | unemployment ∈ [0.85, 0.97] | 0.937 | pass |

One seed of twenty collapsed (120 employing, 348 deaths, GDP growth
std 1.15) — the `docs/137` mechanism on a seed whose purses grew
fastest; the median is unaffected and the range says so.

## 2. The final table

Same instrument, same basis, twenty seeds each.

| fact | Wright reports | SA control | ours, docked |
|---|---|---|---|
| money conserved | yes, by construction | 1e-9 | **1e-14** |
| wage share (wages ÷ value added) | 0.55 | 0.538 | 0.020 (production); 0.84 with construction |
| firm-size α (MLE) | 1.038 (OLS) | 1.278, x_min 26 of 751 | 2.27, x_min 168 of 785 — **not a fit** |
| firm growth excess kurtosis | ~3 (Laplace) | 4.21 | 231 |
| GDP growth std / kurtosis | — / ~3 | 0.079 / −0.10 | 0.061 / 1.88 |
| demises per firm-month | 0.18 | 0.156 | 0.0070 |
| unemployment | ~0.1 | 0.17 | 0.94 (artefact) |
| cost-ranked sectors (ρ) | — | — | **−0.80** |
| endogenous crisis | — | — | over-accumulation, `docs/133` §3 |

## 3. What is shared and what is not

**Shared.** A closed money circuit that conserves to machine precision
with the fund spending, producers accumulating and plant wearing. A
wage share that is an accounting quantity on the same basis as his. A
GDP series that moves because demand is a flow out of a stock, with a
body (0.06) of the same order as his (0.08) and an excess kurtosis in
Laplace's neighbourhood. Sectors in which the cheaper firm is reliably
the larger one. An endogenous crisis — over-accumulation into fixed
demand — that his model does not have and ours produces from its own
rules.

**Not shared, and why.** His firm-size tail and his Laplace firm
growth. Both come from M1: revenue that varies independently of cost,
every month, for every firm. Our lab's revenue is what a producer's
cost and capacity earn it, deterministically; the only heterogeneity is
a cost spread, which `docs/135` §3 showed gives a bounded dispersion
(sector CV 0.15 here) and no tail. `docs/131` §1 is the mechanism in
one sentence: one price, differential profit, equal size. His wage
share of 0.55 is an outcome; ours is an input, `basket_fraction`, and
`docs/129` §3 showed it can be set to his number with the economy
alive. His demise rate is 20× ours because his firms die by lottery
and ours by attrition.

**Artefacts, named.** Unemployment 0.94 is the labour-pool ratio
inherited from `docs/124` and a population that only shrinks with
investment off. The construction share of 0.84 is `retention_rate` and
the construction unit, both scenario numbers.

## 4. What this closes

`docs/97` asked whether our laboratory was sound by docking it with
Wright's. Forty-two documents later the answer has a shape. The
transcription is sound (`docs/111`–`docs/123`, `verify_wright`). Our
lab, given his two rules and a scenario that can reproduce its own
labour-power, shares his money circuit and his accounting and produces
a crisis of its own, and it does not produce his distributions because
it has no noise and he has nothing else. That is a statement about
what each model *is*, and it is the one `docs/140` puts to him.

The mod can be built on this. It inherits a deterministic economy with
a closed circuit, a wage share it can set, competition that ranks by
cost, and an accumulation rule that produces booms and busts; and it
inherits the knowledge that a firm-size tail would need a rule the
game's determinism forbids, which is a design constraint and not a
defect.
