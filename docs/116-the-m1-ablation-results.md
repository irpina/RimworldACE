# The M1 ablation: results

Measures `docs/115`. 4 cells × 50 seeds, 120 months burn-in then a
180-month recording window. Reproduce with `python -m economy_lab.m1_ablation out.json 50`; the raw
records are 200 runs, one per (rule, seed), and the readings below come
from `pooled`, `per_seed` and `decompose` in that module.

## 1. The table

Distribution rows (α, kurtosis, λ, demises) are fitted on the **pooled**
records across all 50 seeds of a cell; the top three rows are means over
seeds of a per-seed reading, shown with the across-seed standard
deviation.

| | `wright` (L+R) | `neutral` (R only) | `fixed` (L only) | `fixed_neutral` (–) |
|---|---|---|---|---|
| mean largest firm | 154.7 ± 118.2 | 14.2 ± 3.4 | 50.3 ± 31.0 | 25.5 ± 7.6 |
| mean firm count | 118.8 ± 22.6 | 207.7 ± 7.5 | 188.9 ± 15.0 | 137.2 ± 9.0 |
| unemployment | 0.173 ± 0.052 | 0.144 ± 0.017 | 0.197 ± 0.027 | 0.368 ± 0.029 |
| firm-size α (Wright) | **1.337** | 4.715 | 2.022 | 3.358 |
| &nbsp;&nbsp;x_min | 37 | 13 | 39 | 20 |
| demises/month | **17.90** | 10.08 | 24.07 | 27.96 |
| firm-growth ex. kurtosis | **3.979** | −0.358 | 2.591 | 1.919 |
| GDP-growth ex. kurtosis | **2.747** | 0.047 | 0.145 | 0.014 |
| wage share | **0.540** | 0.501 | 0.627 | 0.667 |
| profit-rate skew | 29.3 | 14.0 | 20.1 | 78.9 |
| recession λ | **1.227** | 1.082 | 1.305 | 0.977 |
| income tail α | **1.179** | 10.107 | 1.996 | 12.888 |

Wright's targets: α 1.038, unemployment ~0.17, demises 18/month, wage
share 0.55, recession λ 1.22, income α 1.3. **Bold** marks the cell
nearest each target — every one of them is `wright`.

On the firm-size α: 1.337 is not comparable to Wright's 1.038, because
`docs/114` established the estimate drifts upward with sample size and
this is a ~1M-sample pool. It *is* comparable across the four columns,
which share a sample size.

## 2. The seven predictions

| # | Prediction | Result |
|---|---|---|
| 1 | money conserved to 1e-6 in all four | **pass** — worst 8.95e-09 |
| 2 | both size-neutral cells shrink the largest firm ≥5× | **pass, with a caveat** |
| 3 | both deterministic cells drop firm-growth kurtosis below 1 | **fail — and backwards** |
| 4 | wage share stays in [0.45, 0.65] in all four | **fail** — `fixed_neutral` 0.667 |
| 5 | unemployment moves >5pp in some cell | **pass** — 19.5pp |
| 6 | demises move >2× in some cell | **fail** — largest is 1.78× |
| 7 | no cell reproduces all seven facts | **pass** |

Four of seven. The three failures are the informative part.

**P2's caveat.** On cell means it passes: 154.7/14.2 = 10.9× and
154.7/25.5 = 6.1×. Paired seed by seed it is weaker — the median ratio
is 8.12 for `neutral` but only **4.76** for `fixed_neutral`, with a
minimum of 1.15. The mean passes partly because `wright`'s largest firm
has a standard deviation (118) comparable to its mean (155), so a few
enormous seeds carry it. The claim that survives is about `neutral`, not
about size-neutrality in general.

**P3 is the real failure**, and it fails in the direction that favours
Wright. I predicted contingency carries the fat-tailed growth. It does
not. Decomposing the 2×2 —

| metric | main effect of L | main effect of R | L × R | \|L×R\| / spread |
|---|---|---|---|---|
| largest firm | +82.69 | +46.55 | +57.87 | 0.412 |
| firm count | −18.58 | +0.24 | −70.30 | 0.791 |
| unemployment | −0.071 | −0.124 | +0.100 | 0.446 |
| demises/month | +1.96 | −12.03 | +5.86 | 0.328 |
| wage share | **+0.000** | −0.126 | +0.039 | 0.238 |
| firm-growth ex. kurtosis | **+2.52** | −0.43 | +1.85 | 0.423 |

— firm-growth kurtosis is driven by **L, the law-of-value half** (+2.52),
not by contingency (−0.43, and the wrong sign). Removing randomness while
keeping the size bias leaves kurtosis at 2.59, still heavy. Removing the
size bias while keeping randomness collapses it to −0.358, *below* normal.

So both of Wright's headline distributional facts — the firm-size tail
and Laplace growth — rest on the same ingredient, the one he explicitly
labels *"a bias justified by the law of value"*. `docs/115` §5 said that
outcome would be a vindication. It is, and more completely than predicted:
I expected the two ingredients to do two different jobs, and instead one
of them does both.

**P6 failed** because demises are the most inelastic fact in the table:
10.08 to 27.96 is the full range, a 2.77× spread across cells but only
1.78× from `wright` to any single cell. Firing follows from payroll
exceeding cash, and every cell still pays wages from the same draw.

**P4 failed narrowly** and tells us the wage share is *not* the pure
accounting ratio I claimed. Its main effect from L is +0.000 — exactly
zero to three places, which is the prediction's reasoning being correct
about the law-of-value axis. But R moves it −0.126. Contingency in
revenue feeds back into the share through hiring: firms that draw a
windfall hire, and the share follows employment.

## 3. Three things the table says that the predictions did not ask

**The interaction is everywhere.** |L×R| is between 0.24 and 0.79 of each
metric's spread. The two halves of M1 are not separable contributions;
firm count is almost *entirely* interaction (0.791) with an L main effect
of −18.6 and an R main effect of +0.24. Any statement of the form "X% of
the result is the law of value" is not well-posed in this model.

**Removing L alone is worse than removing both.** `neutral`'s largest
firm is 14.2; `fixed_neutral`'s is 25.5. Strip the size bias and the
economy is *more* concentrated if you also strip the randomness than if
you leave it in. Under `neutral` a firm's expected revenue is flat in
headcount while its wage bill is linear, so growth is actively punished
and the contingent draw is the only thing that ever builds a firm — and
it builds, then kills, small ones. Non-monotonic ablations are the
standing hazard `docs/109` ran into from the other direction.

**`wright` is not an arbitrary point in the space.** It is nearest
Wright's reported value on *all six* of the targets we can score, and the
three mutants miss on every one. That is the strongest evidence this
laboratory has produced that M1 as written is load-bearing rather than
incidental — which is the answer to the question `docs/110` §4 put to it.
Our own grid's finding, that changing the exchange institution moved firm
deaths from 29/month to zero, still stands; what this shows is that
Wright's particular institution is not one you can perturb and keep his
facts.

## 4. What this does not settle

It does not revive the firm-size power law. `docs/114` found lognormal
beats power law in 51 of 100 seeds and loses in none; that is untouched
here, and "the tail" throughout means heavy-tailed, not Pareto.

It does not show the law of value is true of real economies. Every cell
is a model, and the finding is about which line of his code carries which
figure in his paper.

It does not explain the mechanism behind the L × R interaction. The
decomposition locates it; nothing here says why firm count in particular
should be 79% interaction.

## 5. Method note

Prediction 3 was wrong because I reasoned from the *shape* of the
ingredient — `U[0, V]` is a heavy draw, therefore it makes heavy tails —
without checking what the model does with it. The draw is heavy in both
`wright` and `neutral`; what differs is how many times it is taken, and
that is the L axis. A fourth rule for the collection in `docs/101`,
`docs/108` and `docs/110`:

> **The distribution of an input is not the distribution of the output.
> Before attributing a moment to an ingredient, ablate the ingredient.**

Which is what this document is, so the rule is at least self-consistent.
