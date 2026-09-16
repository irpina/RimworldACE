# What we would put to Ian Wright

Supersedes `docs/121`, which is kept with its annotations. Everything
`docs/123` withdrew is gone from here; everything `docs/125` §1
replaced is replaced. Points 1–6 are about his model, from a stdlib
reimplementation of the nine rules at his three parameters that
conserves money to 1e-9 over 100 seeds and is verifiable in a minute
(`python -m economy_lab.verify_wright`). Point 7 is about ours.

We are not economists and have touched no empirical data. Every claim
below is about a model's output.

---

## On the measurements

**1. Your firm-size exponent and ours differ by an amount your
estimator does not explain.** Your α = 1.038 is an OLS slope on a
log-log histogram with unit bins. We built that estimator and
calibrated it on data of known exponent: at true α = 1.5 it reads
about 0.5, the bias does not shrink with sample size, and for true
α ≤ 1 — the Zipf case — it returns a *negative* exponent when every
bin is kept. On our transcription's output, no rule for dropping sparse
bins takes it above 0.88; the MLE on the same runs reads 1.28. Inverting
the calibration, your 1.038 implies a true exponent near 1.84, thinner
than ours by ~0.16. Either your fit involved a choice the caption does
not state, or the transcription differs from your model in a way that
shapes the tail. We cannot tell which from here; your code or your
Fig. 2 data would settle it in an afternoon.

*(Convention note: α_Wright = α_CSN − 1. Zipf is 1.0 in yours, 2.0 in
theirs.)*

**2. Fact 5 needs a geometric null.** Recession durations are whole
years. Against a continuous exponential your model's own durations give
KS = 0.50, p = 0.000 — an apparent refutation that is an artefact of a
step function against a smooth CDF. Against the geometric, KS = 0.027,
p = 0.22, λ = 1.165 against your 1.22. The fact holds; the usual test
does not test it.

**3. On your model's output a lognormal fits firm sizes better than a
power law.** Vuong's normalised log-likelihood ratio, 100 seeds: the
lognormal is favoured in 51, the power law in 0, undetermined in 49.
It beats an exponential in 98 — the tail is certainly heavy — but
"Zipf" is not what the data your model generates supports. We hold the
income-tail version of the same test loosely; it is our weakest result.

## On the mechanism

Your model has one exchange rule, so the paper cannot ask how much of
the result is the social relations and how much is M1. We made M1's two
ingredients — sampling once per employee ("a bias justified by the law
of value") and a random amount ("to reflect contingency") —
independently switchable, then made the size bias a continuous exponent
β with β = 1 your rule.

**4. M1 as written is load-bearing and your attribution is right.**
Across the 2×2, your rule is nearest your reported value on all six
scoreable targets and the three mutants miss on every one. Removing the
size bias takes the firm-size exponent from 1.34 to 4.7: the tail stops
existing.

**5. You under-credit the law of value.** You attribute Laplace firm
growth to the random draw. It is carried by the linearity: main effect
on growth kurtosis +2.52 for linearity against −0.43 for contingency.
Remove randomness and the kurtosis stays at 2.6; remove the size bias
and it collapses below Gaussian. Both of the results you lead with rest
on the ingredient you label the law of value.

**6. β = 1 is the joint optimum of your own two firm-level facts, and
the model reverts rather than runs away above it.** Scored against
Laplace's kurtosis and a firm-size target with no bands, the grid
argmin is β = 1.00 for every weighting from 0.1 to 0.9 (parabolic
interpolation 0.975–1.023), and growth kurtosis binds from above:
3.89 at β = 1.00 against 5.60 at 1.05. Above β = 1 the draw from
`U[0, V]` begins to exceed the market — your M1 as written cannot, so
this is our continuous extension speaking, not your rule — and the
mechanism degenerates toward "whoever is selected takes what is left",
which is β = 1 behaviour again. We have withdrawn an earlier claim
that the two facts want different β; it rested on crossing our MLE
curve with your OLS number, which point 1 says cannot be done.

## On our own model

**7. Given your two rules, a deterministic commodity economy shares
your money circuit and not your distributions.** Our laboratory has
commodities, techniques, labour values, prices of production, two
regions and a subsistence wage; it has no individuals and no
randomness. We added your E1 and H1/F1 in our terms — an owners' fund
that spends a share of its silver, producers that build capacity out
of retained earnings and lose it to unpaid wear — and ran your battery
through one instrument on both models, twenty seeds each.

| | your model | ours |
|---|---|---|
| money conserved | 1e-9 | 1e-14 |
| wage share | 0.54 (an outcome) | 0.02 (an input: the basket) |
| GDP growth std | 0.08 | 0.06 |
| firm-size tail | heavy, family undetermined | **none** |
| firm growth | Laplace | attrition (kurtosis ~200) |
| cheaper firm is larger | — | ρ = −0.80 |
| crisis | none | over-accumulation into fixed demand |

The tail does not appear because nothing in our lab lets a firm's
revenue vary independently of its cost: within a sector the posted
price converges to one price, the cost advantage goes to the profit
rate and not to size, and a cost spread of even ±50% yields a sector
dispersion of 0.15 that stops growing when over-capacity sets in. Your
M1 gives every firm a fresh draw every month. **Your lottery is
load-bearing**, and we would put that more strongly than the paper
does: it is not a convenience for generating heterogeneity but the
sole source of the two distributions your model is known for. A model
with your social relations and any *deterministic* allocation of
revenue would, on our evidence, produce your wage share and your
money circuit and none of your tails.

What we would like to know from you is whether you see that as a
result about capitalism — that the distributions require contingency
in exchange, not merely inequality in relations — or as a result about
models.

## What we would not claim

None of this is evidence about real economies. Our lab reproduces your
facts and asks which lines produce which; that can catch
mis-attribution (points 5 and 6) and cannot move a model toward truth.
Against ourselves: three of our own conclusions were withdrawn within a
week of being written (`docs/120`, `docs/123`), and one battery
configuration collapsed on a parameter interaction its design had
named and not tested (`docs/137`). The document trail is public and
the verifier is one command.
