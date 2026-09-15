# The paper arrived: `docs/98` §3 is refuted

The PDF (arXiv:cond-mat/0401053v2) was supplied, and
`economy_lab/social_architecture.py` is now a **transcription** of
Wright's rules rather than a reconstruction of them.

**The headline: `docs/98` §3's central finding is backwards. It reported
that firing against a firm's accumulated funds sends the model to
monopoly and that only firing against trailing revenue yields a reserve
army — and concluded that "one rule decides whether a capitalist economy
has a reserve army at all". Wright's rule F1 fires against `m_a`, the
firm's *money holdings*, and his model is stationary: ~130 firms, ~17%
unemployment, firm-size Hill ≈ 1.2, across three seeds and 300 months.
The rule `docs/98` rejected is the paper's. The rule `docs/98` adopted,
put back into the transcription, collapses the economy to 27 firms and
50% unemployment.**

Worse, `docs/98` §4 predicted this would be the finding most likely to
survive contact with the paper — "because it follows from the
corroborated wording rather than from fitting". The corroborated wording
was §2.7's informal walkthrough. The formal rule is Equation (2). **The
prose and the equation disagree, and I had only the prose.**

## 1. What F1 actually says

> **Firing rule F1(a): (Deterministic).**
> (1) If actor *a* is an employer, *a* ∈ C, then determine the number of
> workers to fire, *u*, according to the formula
> `u = max(|W_a| − ⌊m_a / ⟨w⟩⌋, 0)` … *no workers are fired if the ex
> ante wage bill is payable from the firm's current money holdings (the
> wage bill is calculated from the average wage and the number of
> employees).*

Money holdings, and the bill reckoned at the **average** wage ⟨w⟩ rather
than at what these particular employees earn — because under W1 wages are
redrawn at every payment, so there is no such thing as their wage.

Against that, §2.7's walkthrough: "*If the active actor is a capitalist
owner of a firm it may decide to fire employees if current revenues do
not cover the expected wage bill.*" Every secondary source quotes that
sentence. It is the one I built on.

## 2. The six errors

| # | rule | the reconstruction | the paper |
|---|---|---|---|
| 1 | H1 | filter candidates by `m > ⟨w⟩`, *then* draw | draw from all of `C ∪ U` weighted by wealth, *then* test the threshold — **a hire can fail** |
| 2 | E1 | the active actor `a` spends | a **different** actor `b ∈ A − {a}` spends |
| 3 | **F1** | test the bill against **trailing revenue** | test against **`m_a`, money holdings** |
| 4 | F1/W1 | wage fixed at hire | wage **redrawn at every payment** from discrete `[w_a, w_b]`; the bill reckoned at `⟨w⟩` |
| 5 | W1 | each employee paid on **its own** activation; a short employer pays **nothing** | the **whole payroll** paid when the **employer** activates; a short employer **part-pays** from `[0, m_a]` |
| 6 | state | integer coins, exact conservation | `m_i ∈ R+`; conservation to float precision |

What the reconstruction got right, and is now confirmed: H1's candidate
set is `C ∪ U`, the non-workers — `docs/98`'s `candidate_pool="owners"`
default was correct, and the `"all"` variant it kept for falsifiability
was never Wright's. H1's weighting by wealth, the whole of M1, SR1's
order, and the month as `N` applications are all as built.

## 3. What the transcription does

At the paper's own parameters — "*In all reported results, N = 1000 and
M = 100000 … the wage interval is set to ω = [10, 90]*", so ⟨w⟩ = 50 and
mean wealth 100, twice the average wage:

| seed | month | firms | largest | unemployment | firm Hill |
|---:|---:|---:|---:|---:|---:|
| 1 | 50 | 123 | 369 | 0.147 | 1.30 |
| 1 | 150 | 156 | 36 | 0.198 | 1.44 |
| 1 | 300 | 141 | 207 | 0.144 | 1.11 |
| 2 | 300 | 98 | 307 | 0.185 | 0.81 |
| 3 | 300 | 144 | 39 | 0.265 | 1.51 |

Stationary, with no drift toward concentration over 300 months. Money is
conserved to between 1e-11 and 1e-9 — float precision, as `m_i ∈ R+`
requires.

Over months 240–300 (seed 1), one reading per month:

| quantity | mean | min | max |
|---|---:|---:|---:|
| wage share | 0.595 | 0.195 | 2.146 |
| income Gini | 0.754 | 0.411 | 0.942 |
| firm-size Hill | 1.210 | 0.465 | 2.225 |
| unemployment | 0.165 | 0.054 | 0.307 |

with a terminal wealth Gini of 0.708, top decile 0.567, wealth Hill 1.67.

A firm-size Hill near 1 is Zipf's law of firm size; a wealth tail index
near 1.7 is a Pareto tail; a wage share fluctuating about 0.6 is the
empirical labour share. A share above 1.0 in a bad month is not a bug —
it is aggregate capitalist income going negative when the month's wage
bill exceeds the month's market samples.

**No exponent here is claimed to match Wright's fitted values.** The
paper reports fits; these are bare Hill readings on single snapshots, and
the between-month spread (0.465 to 2.225) shows how noisy one snapshot
is. Matching his figures properly is a separate exercise.

## 4. Which error did the damage

Each error reintroduced on its own, into the transcription, 200 months,
seed 3:

| variant | firms | largest | unemployment | firm Hill |
|---|---:|---:|---:|---:|
| **paper** | 198 | 31 | 0.208 | 1.53 |
| + error 1 (filter-first) | 177 | 33 | 0.164 | 2.22 |
| + error 2 (spend-self) | 148 | 126 | 0.170 | 1.24 |
| + error 3 (fire-on-revenue) | **27** | **280** | **0.501** | 1.36 |
| + error 5 (pay-per-employee) | 193 | 48 | 0.211 | 1.87 |

**No single error reproduces `docs/98`'s monopoly.** That behaviour
needed the whole broken combination, which is why isolating it by
reasoning failed: I changed one rule at a time in a model where five
others were already wrong, and read the response as evidence about the
rule I was changing.

Error 3 is the only one with a large isolated effect — and it runs the
*other* way. In Wright's model, testing solvency against trailing revenue
concentrates firms and drives unemployment to 50%. The rule `docs/98`
adopted because it reproduced Wright's reported results is the rule that,
in Wright's own model, destroys them.

## 5. The corrected scorecard

Nothing here touches the lab-side audit. `docs/98` §2's readings stand:
A1 holds, A2 is latent, A3 and A5 diverge, and A6 passes per `docs/99`.
Six of nine predictions, unchanged.

What changes is the *authority* of the instrument and one conclusion
drawn from it:

- **Withdrawn**: "one rule decides whether a capitalist economy has a
  reserve army at all" (`docs/98` §3, §4). It does not.
- **Strengthened**: A3's divergence. Our lab has no rule that tests a
  producer's solvency against its wage bill; Wright has exactly one, F1,
  and it is load-bearing — it is what makes firm death and the reserve
  army endogenous rather than parametric.
- **Upgraded**: prediction 6 passes on the paper's rules at the paper's
  parameters, not on a guess.

## 6. Why the reconstruction failed, in one line

**I chose a rule body because it reproduced the result the paper
reports.** That is fitting to the answer, and it cannot distinguish "this
is the rule" from "this is *a* rule that, combined with my five other
mistakes, happens to land near the published figure". `docs/98` §4 said
so about errors 1 and 2 and then exempted error 3 on the strength of a
sentence of prose. The exemption was the mistake; the prose was informal
and the equation was not available to check it against.

The general form, which the last three documents have each hit: **a
model calibrated against its target's outputs cannot then be evidence
about its target's mechanism.** `docs/97` §2 made this argument about our
lab and Wright's model; it applies just as sharply to a reconstruction
and the paper it reconstructs.

## 7. What follows

The A3 design is now better specified than it would have been. F1 is
directly portable to our producers, and it is simpler than what `docs/98`
§5 step 2 proposed:

- test the wage bill against **what the purse holds**, not against a
  trailing revenue window — which means no new state, since
  `producer.cash` already exists;
- reckon the bill at the **going wage** times the labour employed, which
  `region.wage_rate()` already gives;
- shed labour down to what the purse affords, and retire a producer that
  can afford none.

That is a rule with no new parameters and no new bookkeeping, and
`docs/98` §2 measured the conditions it lands in: producers pay their own
wage bills today, and `fund_wage_support` is dead, so the fallback it
replaces is already unused. Gated off by default, as every market rule in
this project is, so the 322-metric baseline stays at zero deltas.

Still true, and now the only remaining reconstruction risk: the figures
in §3 are single-snapshot Hill estimates, not fits to the paper's
reported exponents. Comparing properly against Wright's Figures is the
one piece of docking still open on the instrument side.
