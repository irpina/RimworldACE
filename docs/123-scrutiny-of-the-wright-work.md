# Scrutiny of the Wright work: three things wrong, one softened, two noted

An adversarial re-read of `docs/111`–`docs/122`, done after the model
serving this session changed. The brief was to find what is wrong, not to
restate what is right. Where a defect is found the original document is
annotated in place with a pointer here rather than silently edited.

## 1. WRONG: the clamp is mine, not Wright's

`docs/119` §5–6, `docs/121` point 6 and the corresponding HANDOFF entries
present this line as **Wright's** "overdraft guard," speculate that he
"did not intend it," and ask whether he considers it behavioural or
defensive:

```python
if drawn > self.market:
    drawn = self.market
```

**He never wrote it.** His M1 is *"randomly select a revenue amount m
from the interval [0, V] according to a uniform distribution (V is
reduced by m)"*. The draw is bounded by V **by construction** — it is the
support of the uniform, and "V is reduced by m" is deliberate accounting
of the pool. The clamp line exists in our transcription only because
the `scaled` rule divides the draw by `members ** (1 − β)`, which for
β > 1 can exceed the pool. Under Wright's own rule it is unreachable, and
the verifier's own measurement says so: **0.0% of draws hit it at
β ≤ 1.**

What survives: his model **cannot express β > 1**, because revenue per
selection is bounded by the pool. That is real and it is his design, not
an accident. What does not survive is every sentence attributing a
"guard line" to him, and the question in `docs/121` point 6. It is
withdrawn.

## 2. WRONG: `docs/114`'s explanation of the exponent gap

`docs/114` lines 67–70: *"At n = 1,000 we measure 1.084. Wright's
exponent is what you get at Wright's sample size. The gap was never a
difference between his model and our transcription; it is the same
estimator drifting."*

Both clauses are false, and neither was checked against the paper.

- **His sample size is not 1,000.** *"Data collected over 15 simulated
  years"* by *"after each month … count the number of employees in each
  firm"* — 180 monthly snapshots of ~100 firms, so **n ≈ 20,000**, which
  is our per-seed window almost exactly.
- **It is not the same estimator.** Fig. 2's caption: *"an ordinary
  least squares regression"* on a *"histogram … in log-log scale with a
  constant bin size of 1."* Ours is Clauset–Shalizi–Newman MLE with
  `x_min` by KS minimisation. OLS on a log-log histogram is precisely
  the method CSN (2009) showed to be biased by sparse tail bins.

The 1.084-at-n=1,000 coincidence was a coincidence.

## 3. WRONG: `docs/120` §4's "tension" is not established

`docs/120` §4 and `docs/121` point 7 say the firm-size exponent "wants
β = 1.078" while Laplace growth "wants β = 0.972," that they "disagree by
0.106," and present this to Wright as a newly measured internal tension.

The 1.078 came from finding where our **CSN-MLE** curve crosses his
**OLS-histogram** number. §2 says those are different estimators. Applying
his estimator to our data at β = 1 (20 seeds, employees counted as he
specifies):

| reading of "OLS on a log-log histogram, bin size 1" | median α | seed range |
|---|---|---|
| all non-empty bins | 0.536 | 0.080 – 0.759 |
| bins with count ≥ 2 | 0.749 | 0.487 – 0.913 |
| bins with count ≥ 5 | 0.855 | 0.802 – 0.985 |
| bins with count ≥ 10 | 0.877 | 0.784 – 0.956 |
| CSN-MLE, for comparison | 1.278 | — |

**No reading of his stated method gives 1.038 on our data**, the method
swings by 0.34 across plausible readings and by 0.7 across seeds, and it
sits 0.4–0.7 below MLE on identical samples, in the direction CSN
predicted. His 1.038 therefore cannot anchor a β. Either his fit involved
a choice the caption does not state, or the transcription differs from
his model in a way that shapes the size distribution — and **we cannot
tell which from here**, which is `docs/122` §2's point restated with
teeth.

Withdrawn: the 1.078, the 0.106, and the sentence "his two headline
facts want different strengths of the same ingredient." Not established
either way.

What survives, because it does not depend on his number:

- **Firm-growth kurtosis binds from above.** 3.889 at β = 1.00 against
  5.596 at 1.05, tight intervals, Laplace = 3. This used only Laplace's
  known kurtosis and stands as written.
- **β = 1 is the joint argmin**, and it is robust: re-weighting the loss
  from 0.1 to 0.9 on α leaves the grid argmin at 1.00 every time, with
  the parabolic interpolation moving only 0.975 → 1.023. Replacing the
  α target with our own β = 1 reading changes nothing.

## 4. SOFTENED: "the optimum is β = 1.00 exactly"

It is the argmin **on a 0.05 grid**. Interpolated, it is 0.98–1.02
depending on weighting. "Exactly" is grid resolution talking.

## 5. NOTED: two things a referee would ask about

**The `fixed` cell is not a clean ablation of contingency.** It draws
`market / actors`, a deterministic 1/1000 of the pool, where `wright`'s
draw averages half of it. Total monthly revenue is bounded by spending
inflow either way, so the aggregate is comparable, but the per-selection
scale differs by ~500× and the cell removes the lottery *and* rescales
the draw. `docs/115` chose it as the steady-state share; it should have
said the scale changes too.

**The Vuong test is continuous-on-integer.** `likelihood_ratio` uses the
continuous power-law likelihood and a continuous lognormal on integer
firm sizes. Both families get the same treatment, so the *relative*
comparison `docs/114` rests on is internally consistent, and with
`x_min` ≈ 27–40 CSN consider the continuous approximation adequate. It
is a limitation to state, not a defect.

## 6. What the scrutiny did not shake

- Money conservation, bit-identity, determinism (`docs/122` §1).
- The estimators recovering planted answers (`docs/122` §1).
- `docs/113`'s geometric-null correction to fact 5.
- `docs/116`'s 2×2: M1 load-bearing; linearity carries Laplace growth.
- `docs/120` §1–2: the one-sided band was an error; kurtosis binds above.
- `docs/119` §5's *measurement* — the cap counts — as distinct from its
  attribution.

## 7. The pattern

Sections 1–3 share a cause: **a claim about Wright was made without
re-reading Wright.** The clamp attribution, the sample size, and the
estimator were all checkable in the PDF in under five minutes each, and
each was asserted instead. `docs/117` §8 catalogued four failures of
reasoning-from-the-surface about the *model*; these three are the same
failure about the *paper*. The rule this adds is the plainest yet:

> **Before stating what an author did, find the sentence where they
> did it.**
