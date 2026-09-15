# The M1 ablation: is it the social relations, or the market rule?

Written before anything is built or run.

## 1. The question

Wright's abstract: *"The model is deduced from the assumption that **the
law of value is an organising principle** of modern economies"*, and from
that assumption he derives seven empirical distributions. The causal
claim is that the **social relations of production** — owning, hiring,
paying, firing — produce capitalism's statistical signature.

`docs/110` §4 put a question to that claim. Our own ablation grid found
that changing the *exchange institution*, with the firing rule untouched,
took firm deaths from 29 a month to none. If the institutional form of
exchange can do that in our laboratory, how much of Wright's result is
his social relations and how much is **M1**, the one market rule he
happens to have written?

He cannot answer it. His model contains exactly one exchange mechanism,
and there is nothing else in it to vary. We now can, because `docs/112`
and `docs/114` established the transcription is his model quantitatively
and not merely in spirit.

## 2. What M1 actually contains

Two separable ingredients, and he names both:

> *"Each firm therefore samples the market … once for every employee, to
> reflect the fact that each worker potentially adds value, but **random**
> to reflect **contingency** … a firm with more employees will on average
> sample the market on more occasions than a firm with fewer employees, **a
> bias justified by the law of value**."*

- **Linearity.** Sampling frequency is proportional to headcount. This
  *is* the law of value in the model — the weak form, a statistical
  tendency for a firm's product to be linear in labour expended.
- **Contingency.** The amount is `U[0, V]`, an extremely heavy draw: a
  single sample can take the entire market pool.

So the ablation is a 2×2, and each cell is a coherent economy rather than
a broken one.

| | random draw | deterministic draw |
|---|---|---|
| **revenue ∝ size** | `wright` (baseline) | `fixed` |
| **revenue size-neutral** | `neutral` | `fixed_neutral` |

- `wright` — `U[0, V]` per member, as written.
- `neutral` — `U[0, V] / members`, so expected revenue per firm per month
  is independent of headcount. **The law of value, removed; contingency
  kept.**
- `fixed` — a deterministic `V / N` per member. **Contingency removed;
  the law of value kept.**
- `fixed_neutral` — `V / (N · members)`. Both removed.

Money conservation is untouched in every cell: each rule moves money from
the pool to an owner and nothing else. A cell that leaked would be a bug,
not a variant, which is why prediction 1 exists.

## 3. What gets built

A `market_rule` parameter on `social_architecture.Economy`, defaulting to
`"wright"`. The default path must stay **bit-identical**: the 23 existing
tests and every figure in `docs/112` and `docs/114` depend on it.

Note that the deterministic cells consume no random numbers in M1, so
their RNG streams diverge from the baseline's. That is inherent to
ablating randomness and is not a defect; comparisons are across 50 seeds
per cell, not across matched trajectories.

50 seeds × 4 cells × 300 months ≈ 9 minutes on four cores.

## 4. Numbered predictions

Measured in `docs/116`.

1. **Money is conserved in all four cells**, to 1e-6. A cell that fails
   this is a bug and its other readings are void.
2. **Linearity is what makes the firm-size tail.** In both size-neutral
   cells the largest firm is at least **5× smaller** than in `wright`,
   and the fitted exponent is materially larger — a thinner tail.
3. **Contingency is what makes Laplace growth.** In both deterministic
   cells, firm-growth excess kurtosis falls **below 1**, from `wright`'s
   3.92.
4. **The wage share is the most robust fact**, staying within
   **[0.45, 0.65]** in all four cells. It is an accounting ratio driven by
   the wage draw, which no cell touches.
5. **Unemployment moves materially** — by more than **5 percentage
   points** from `wright`'s 0.171 — in at least one cell.
6. **Demises move by more than 2×** from `wright`'s 17.95/month in at
   least one cell.
7. **No cell reproduces all seven facts.** If one does, then the facts do
   not depend on M1's content, and Wright's attribution to the law of
   value is undermined from the *other* direction — the rule would be
   doing no work at all.

Predictions 2 and 3 are the substance: they would establish that the two
ingredients do *different* jobs, and that the "law of value" half is what
carries the firm-size result he leads with.

## 5. What this can and cannot conclude

If `neutral` destroys the firm-size tail, that **supports** Wright: the
law of value really is doing the work he says it is, and the result is
not an artifact of a random market. That is the outcome I expect, and it
would be a vindication rather than a challenge.

If instead the facts survive every cell, they are properties of the
hiring-and-firing relations alone, and M1's specific content is
incidental.

What it cannot do is settle whether *real* economies work this way. Every
cell is a model. And it cannot revive the firm-size power law that
`docs/114` weakened — where "the firm-size tail" appears here it means the
heavy tail, fitted exponent and largest-firm size, with no claim that the
family is Pareto rather than lognormal.
