# What the M1 ablation entails

Interpretation of `docs/116`. No new runs; this document draws
consequences from measurements already recorded, and proposes the one
experiment that would close the question it leaves open.

## 1. The narrow finding, stated precisely

Wright's abstract claims the model is *"deduced from the assumption that
the law of value is an organising principle of modern economies."*
`docs/110` §4 doubted it, on good grounds: he has exactly one exchange
mechanism, he never varies it, and our own grid had just shown that
changing the exchange institution alone moves firm deaths from 29 a month
to zero. "Deduced from the law of value" was indistinguishable from
"deduced from whatever rule I happened to write."

`docs/116` settles it, and in his favour twice over:

- **The attribution is correct.** The half of M1 he labels the law of
  value is the half that carries the firm-size tail (α 1.337 → 4.715 when
  it is removed).
- **The paper under-claims.** That same half also carries Laplace firm
  growth — main effect +2.52, against contingency's −0.43 — which he
  attributes to the random draw rather than to the law of value.

This is a claim about his model, not about economies. It says the line of
code he points at is the line doing the work. That was not obviously true
and is now checked.

## 2. The deflationary reading, which is also correct

What is "linearity" mechanically? A firm samples the market once per
employee, so **expected revenue is proportional to headcount**, while
payroll is also proportional to headcount. That is a multiplicative growth
process, and multiplicative growth with entry and exit gives heavy tails.
Gibrat, Yule, Simon. It is a known mathematical fact about proportional
growth, not a discovery about capitalism.

So one honest gloss of `docs/116` is: *what Wright calls deriving
capitalism's signature from the law of value is, structurally, the
observation that proportional growth makes heavy tails.* The economics
enters only in **which** quantity he makes proportional to **which**.

That deflation is real and should be stated. But it does not dispose of
the model, for a reason our own table makes visible. Gibrat gives you a
firm-size distribution. Gibrat does not give you a wage share of 0.540, an
unemployment rate of 0.173, a recession duration λ of 1.227, and an income
distribution with a Pareto knee in the top 8% — **simultaneously, from the
same single proportionality, in a model whose entire ontology is actors
and money.** Wright's achievement is the joint fit, and the joint fit
survives the deflation.

What `docs/116` adds is that the joint fit is **not robust**: it lives at
one corner of a 2×2, and all three neighbours miss all six targets.

## 3. The fine-tuning question, which is now the open one

Two readings of "the baseline hits six targets and its three neighbours
miss every one":

**(a) The mechanism is specific and right.** Remove a mechanism, lose the
phenomenon it generates. Models that violate the law of value do not look
like capitalism. This favours Wright.

**(b) The fit is a knife-edge.** A model that matches reality at exactly
one point in its own parameter space and fails at every neighbour is
*less* convincing than one with a basin, because real economies are not
finely tuned.

Our data discriminates partially, and in favour of (a): the mutants do not
fail *randomly*, they fail *directionally*. `neutral` kills tails
specifically (α → 4.715, kurtosis → −0.358, income α → 10.1) while leaving
the wage share nearly intact (0.501). `fixed_neutral` blows up
unemployment (0.368) and the wage share (0.667) specifically. Each
removal costs the phenomenon that ingredient generates. A knife-edge
would look like scatter around the target; this looks like subtraction.

But it is only partial, because **a 2×2 samples four corners and no
interior**. We tested whether M1 is load-bearing. We did not test whether
its fit is robust to *small* perturbations, and those are different
questions.

### The experiment that would close it

Make the size bias continuous. Sample `members ** beta` times instead of
`members` times, so `beta = 1` is `wright` and `beta = 0` is `neutral`,
and sweep beta over roughly [0, 1.5]. Then:

- If the seven facts degrade **smoothly** and there is a **wide** region
  around beta = 1 where they all hold, the fit is a basin, reading (a)
  wins outright, and Wright's claim is about as strong as a model claim
  can be.
- If they hold **only** at beta ≈ 1, it is a knife-edge and the joint fit
  is a tuning result. That would be the most interesting negative finding
  this laboratory has produced.
- A third outcome is live: the facts may not share a region. The wage
  share may want one beta and the firm-size tail another. **Wright reports
  the seven facts but never reports whether one parameter setting gives
  all seven at once** — we would be the first to check.

This is one extra parameter on `economy_lab/m1_ablation.py`, the same
harness, the same runtime. It is the cheapest high-value experiment
currently available and it should be the next thing built, with the
predictions written first.

## 4. What it entails for our own laboratory

The purpose of the dock was never validation. It was calibration and
error-finding, and on that it delivered: `docs/99`'s wage-share identity,
`docs/113`'s measurement defects, `docs/114`'s exponent-convention trap.

`docs/116` now says something specific about the relationship between the
two models. Wright's ontology is actors and money — no commodities, no
techniques, no prices, no labour values. Ours is the full Marxian
apparatus. The ablation shows the statistical signature is generated by
**the proportionality of revenue to labour employed**, and that
proportionality is available in both:

- Wright gets it **by assumption** — sample once per worker.
- We get it **by construction** — workers produce goods, goods sell.

So our extra machinery is **not required for the seven facts**, and it is
**not in conflict with them either**. That is the sound-and-docked
conclusion, and it also locates where our lab is doing original work
rather than reproducing his: differential and absolute rent, technique
choice, Department I, the value/price transformation, regional wage
differentials and the migration that closes them. Wright cannot pose any
of those questions — his model has no commodities to have values.

**For the mod this is a scope result.** The RimWorld implementation does
not need to reproduce Wright's seven distributions to be sound. It needs
the proportionality, which it gets for free from colonists producing
goods. The mod's job is the value machinery, which is the part Wright's
model cannot supply and the part we have spent 80 documents building.

## 5. What it entails methodologically

**Ablations in this class of model are interaction-dominated.** |L×R| is
between 0.24 and 0.79 of spread on **every** metric in `docs/116`. Firm
count is 79% interaction, with main effects of −18.6 and +0.24 — the two
ingredients individually do almost nothing and jointly do everything.

This is the second independent confirmation. `docs/110` found the same
from the other direction in *our* model: procurement × quantum was 0.576
of spread and negative, one rule switching another's mechanism off (the
quantum takes deaths 0 → 29.4 under `cash+posted`, and 1 → 1 under
`+procurement`). Two different codebases, two different ontologies, same
structure. It is looking like a property of the domain rather than of
either implementation.

Three consequences:

1. **Single-factor ablations are close to uninformative here.** "Turn off
   X and see" yields a number that depends entirely on the state of
   everything else, and reporting it without the regime is misreporting.
2. **Direction is not safe to infer from one ablation.** `docs/116`'s
   sharpest case: removing linearity *alone* gives a largest firm of 14.2,
   while removing linearity *and* contingency gives 25.5. Removing one
   thing is worse than removing two. Sign is not stable.
3. **The mod must not ship independent balance knobs.** Any set of sliders
   we expose will interact at the magnitudes above and will not compose.
   Expose few knobs, or expose regime presets we have actually measured.

## 6. What is still open, stated plainly

Docked, with three asterisks:

- **The firm-size power law is weakened, and by us.** `docs/114`: a
  lognormal fits better in 51 of 100 seeds and worse in **0**. Wright did
  not run this test. "Firm size follows Zipf's law" is not supported by
  his own model's output; heavy-tailed is.
- **The income tail is the weakest result in the record.** Not rejected in
  only 46/100 seeds, with the lognormal comparison undetermined in 99/100.
- **Robustness is untested.** §3's beta sweep.

Two smaller items carried forward: the capped `x_min` grid approximation
in `power_law_fit`, and `fund_wage_support` being keyed by region alone,
so nothing records whose payroll it supported.

## 7. What kind of knowledge this is

Not empirical economics. We have not touched real data at any point.

What we have done is **code archaeology on a theoretical claim**: take a
published model, reimplement it, and ask which of its lines produce which
of its advertised results. It catches over-attribution and, here,
under-attribution.

Its limit is hard. It can never elevate a model toward truth, because
every cell in the 2×2 is equally fictional; what varies is which fiction
matches the stylized facts. And "matches the stylized facts" is weak
evidence, because many mechanisms produce heavy tails. `docs/114` is
exactly that weakness biting: the output cannot distinguish two
*distributional families*, so it certainly cannot single out a mechanism.

**The caution that follows:** "we docked with Wright" must not become "our
model is validated." That would chain two weak inferences — his model
matching seven stylized facts, and ours matching his. Neither link carries
that weight. The dock was worth doing for the errors it found, and those
were real.

## 8. A pattern in the failures worth naming

Four of the last five documents recorded a prediction failing because the
prediction reasoned from a **surface property** instead of checking the
model:

| | the surface reading | what was actually true |
|---|---|---|
| `docs/109` | ten gated rules give 1024 cells | they are a dependency stack; 384 |
| `docs/110` | any two rules can be crossed | the model validates prerequisites |
| `docs/114` | our exponent disagrees with his | the measurement was scale-dependent |
| `docs/116` | a heavy input draw makes heavy tails | the count of draws makes them |

The mitigation is already the project's practice and is the only reason
these were caught rather than quietly absorbed: **numbered predictions,
written before the run, scored honestly afterwards.** Three of those four
failures would have been invisible as post-hoc narration. The rule the
table adds to `docs/101`, `docs/108` and `docs/110`:

> **The distribution of an input is not the distribution of the output.
> Before attributing a moment to an ingredient, ablate the ingredient.**
