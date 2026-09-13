# Docking with the Social Architecture of Capitalism: design

Written before implementation. The target is Ian Wright, *The social
architecture of capitalism*, Physica A **346** (2005) 589–620.

**The headline: the two models have no observable in common, so docking
cannot mean comparing outputs. Not one of Wright's seven stylized facts
is measurable on a deterministic six-producer model, and not one of our
322 baseline metrics has a counterpart in his. What Wright supplies is
an *architecture* — a short list of structural propositions about how a
capitalist economy is wired — and those are auditable against our lab at
N=6. Reading our rules against them before writing a line of code has
already found one divergence: our producers cannot fail from the wage
side, because `_pay_wages` tops up from the regional fund any purse that
cannot pay.**

**Corrected by `docs/98`.** The headline's second sentence overstated the
finding. The fund's top-up branch is real, but measurement shows it is
**never taken**: `fund_wage_support` totals 1e-13 across every committed
scenario, which is float residue from splitting a bill, not support.
Producers do pay their own wage bills today. The conclusion that the wage
bill is not a solvency constraint (A3) stands and was confirmed — 0 deaths
by wage bill against 107 exits on return — but it holds because no rule
tests solvency against the wage bill at all, not because the fund rescues
anyone. Prediction 4 was also wrong: `labor_pool` is `1.0` in every
scenario, not `inf`; I read the dataclass default for the scenarios. And
prediction 5, expected to pass, **failed**: the wage share does not
fluctuate. §5's numbering is unchanged so the scorecard lines up.

## 0. What I could and could not obtain

This matters because the predictions below have to be falsifiable, and a
prediction resting on a misremembered rule is not.

The egress proxy blocked every full-text route: `arxiv.org` (403 at
CONNECT), the author's own copy at `ianwrightsite.files.wordpress.com`,
`semanticscholar.org`, `ar5iv`, and both secondary write-ups. **I have
not read the paper in this session.** What follows is assembled from
search results, and is graded:

| grade | content |
|---|---|
| **quoted** | the abstract's list of stylized facts — returned verbatim, and consistent across three independent results |
| **corroborated** | the ontology (actors and money only); three parameters *M*, *N*, *w*; nine rules; the loop order S₁, H₁, E₁, M₁, F₁, W₁; a month is *N* applications of the rule; money conserved; class position emergent |
| **single-source** | that *R* = mean wealth per capita ÷ mean salary is the governing dimensionless parameter (from a 2024 replication, not from Wright) |
| **unobtained** | the exact form of each rule, the wage interval's bounds, the reported exponents, the figures |

Everything in §4 and §5 is built only on **quoted** and **corroborated**
material. Nothing in the numbered predictions depends on a rule detail I
could not confirm. §6's replication targets are marked where they rest on
unobtained numbers, and those are to be re-checked against the paper
before any of them is reported as passed or failed. *A failure to obtain
something is evidence about the attempt, not about the thing* — the
correct reading of the blocked fetches is that this document is provisional
on the paper, not that the paper says what I remember.

## 1. What the SA model is

An ontology of **actors and money, and nothing else**. No commodities, no
techniques, no production functions, no prices. Wright's stated aim is to
isolate the economic consequences of the *social relations of production*
— the enduring architecture — from any particular economic mechanism.

Each actor is an employer, an employee, or unemployed; the state is not
assigned but emerges. One simulation step selects an actor and runs the
rules in order: hiring, expenditure into a common pool of latent demand,
a market sample drawing revenue from that pool to a firm, firing, and
wage payment. A firm is a coalition: an owner plus employees. An employee
adds value to the firm by drawing a random slice of demand and is paid a
fixed wage. A firm that cannot cover its expected wage bill fires; a firm
that fires everyone ceases to exist.

The abstract's seven results, quoted:

| # | quantity | distribution |
|---|---|---|
| 1 | firm size | power law |
| 2 | firm growth | Laplace |
| 3 | GDP growth | Laplace |
| 4 | firm demises | lognormal |
| 5 | recession duration | exponential |
| 6 | income | lognormal–Pareto |
| 7 | firm rate of profit | gamma-like |

plus business-cycle phenomena and wage and profit shares fluctuating
about empirically consistent values.

## 2. Why the outputs cannot be compared

|  | Economy Lab | SA model |
|---|---|---|
| actors | 6–12 producers, 2 regions | 10³–10⁴ |
| dynamics | deterministic, bit-exact | stochastic |
| commodities | 6–9, with technical coefficients | none |
| production | input–output with labor coefficients | none; revenue is a draw |
| labor values | solved (SNLT) | absent |
| prices | posted, gravitating | absent |
| class position | assigned by scenario | emergent |
| the object | one economy's trajectory | an ensemble's distributions |

A power law needs a population. With six producers there is no firm-size
distribution to fit, no demises to count, and no recessions to time. Our
determinism is not incidental either — it is the project's central method
(`docs/53`) — and every one of Wright's results is a property of a
stationary *distribution* that only exists because the model is random.

So the mismatch is not a gap to be closed. **It is a complementarity.**
Wright has no commodities, no technique and no labor values — which is
exactly what we compute. We have no population — which is exactly what he
measures. Neither model is a candidate to replace the other, and a
head-to-head comparison of outputs would be a category error rather than
a validation.

That is also why docking is worth doing. The complement is precisely the
piece `docs/50` §5 named as the last omission on the critical path.

## 3. Three readings of "dock", and which one is chosen

**R1 — replicate and compare.** Implement the SA model beside ours,
reproduce its seven facts, ask which ours shares. Answer, by §2: none,
by construction. This validates a second model standing next to ours, not
ours. *Rejected as the goal; adopted as the instrument*, because an
architecture audit that cannot run the architecture it audits against is
rhetoric.

**R2 — SA as the population layer.** Note what Wright has that we lack
and need: firms holding cash that hire, pay and die; a labor market where
the unemployed are hired and fired; an *endogenous* reserve army. That is
`docs/50` §5's worker mobility, and it is what the mod needs, because a
RimWorld pawn is an actor that gets hired, paid and fired. *Adopted as
the destination*, and out of scope for this slice.

**R3 — architectural audit.** Wright's propositions about *wiring* are
not statistical and do not need a population. They are checkable against
our lab today, at N=6, and each one that fails is either a real defect or
a divergence we should be able to name and defend. *Adopted as this
slice.*

Order: R1 builds the instrument, R3 uses it, R2 is the design that
follows.

## 4. The architectural propositions

Wright's architecture, reduced to what is checkable. The third column is
my reading of our code before measuring, and §5 turns each into a
prediction.

**A1 — Money is conserved.** Total coins are fixed; every rule is a
transfer. *Ours:* `cash_balance()` is the same residual, and 24 assertion
sites already pin it to 1e-7 or tighter. Expected to **hold**.

**A2 — The wage is advanced, and the advancer bears the risk.** The
employer pays out of the firm's own funds before revenue is known.
*Ours:* with `producer_cash` on, `_pay_wages` splits the bill by labor
used and each producer pays from its purse — but any residual a purse
cannot cover is taken from `region.cash` and booked as
`fund_wage_support`. With `producer_cash` off, the region pays the whole
bill. Either way **the producer does not bear the risk**. Expected to
**diverge**.

**A3 — A firm that cannot pay sheds labor; a firm with no labor dies.**
The wage bill is the solvency constraint, and it is what makes firm death
endogenous and frequent. *Ours:* `_exit` retires on *return* — below the
going rate for the investment lead time — and `_bankrupt` fires on
`bankruptcy_idle_days`. Neither is the wage bill. Given A2 the wage bill
*cannot* bind. Expected to **diverge**, and this is the same regional-pool
item the handoff has carried open.

**A4 — Class position is emergent.** *Ours:* producers are producers,
authored by the scenario. Expected to **diverge, deliberately** — but the
divergence should be *stated*, because `docs/50`'s gameplay layer wants a
colony that can become an employer.

**A5 — The reserve army is endogenous.** In Wright, unemployment
fluctuates and drives the cycle. *Ours:* `Region.labor_pool` is a
parameter, and its default is `float("inf")` — so `employment_rate()`
returns 0.0 and the reserve army is not merely exogenous but *unbounded*
by default. Expected to **diverge**. This is `docs/50` §5's omission,
reached from a second direction.

**A6 — Wage share and profit share fluctuate and sum to one.** *Ours:*
`price_decomposition` and `rate_of_surplus_value` exist; whether the
shares close to one is a genuine check. Expected to **hold**, untested.

**A7 — The market is a common pool; revenue is a draw, not a
certainty.** A firm's revenue is bounded by what others happen to spend.
*Ours:* demand is seen and rationed, sell-outs are noted (`docs/68`), and
with `posted_prices` and `procurement` on there is a real allocation —
but nothing is stochastic. Expected to **partially hold**: the
*bounded-by-others'-spending* half is there, the *draw* half is not.

## 5. Numbered predictions

Measured in `docs/98`. Each is falsifiable and stated so it can fail.

1. **A1 holds exactly.** Across all five reference scenarios at 1080
   days, `cash_balance()` stays within 1e-6, with `producer_cash` both on
   and off.
2. **A2 fails, and the failure is quantifiable.** In at least one
   scenario with `producer_cash` on, `ledger.fund_wage_support` is
   strictly positive — i.e. the fund really does absorb wage risk rather
   than this being a dead branch. I expect a positive figure; if it is
   zero everywhere, A2's divergence is latent rather than live and the
   finding is weaker than stated.
3. **A3 fails, and no producer ever dies of the wage bill.** Over the
   same runs, the count of retirements attributable to an unpayable wage
   bill is exactly **0**, while `_exit` retirements are positive.
4. **A5 fails, and by default is not even bounded.** In every committed
   scenario, `region.labor_pool` is `inf` — hence `employment_rate()` is
   identically 0.0 — except where a scenario sets it deliberately. I
   predict at most a small minority of scenarios set it.
5. **A6 holds.** Wage share plus profit share sums to 1.0 within 1e-6 in
   the decomposition, and both move by at least 1% of their level over a
   1080-day run in at least one scenario (i.e. they *fluctuate*, not just
   sum).
6. **The SA reference reproduces at least fact 1 and fact 6** — a
   heavy-tailed firm-size distribution and a two-class income
   distribution with an exponential-ish bulk and a heavier tail. These
   are the two that are unambiguous at N=1000 without fitting machinery.
   *Marked provisional*: exponents are **unobtained**, so this predicts
   the qualitative shape only, and no exponent will be reported as
   matching Wright until the paper is in hand.
7. **The SA reference self-organises into classes from a symmetric
   start.** Beginning with every actor unemployed and holding equal
   money, after 100 simulated months the population contains all three
   states, and the employer share is under 20%.
8. **Money is conserved in the SA reference to the bit** — total coins
   after any number of steps equals the initial total exactly, since
   every rule is an integer transfer.
9. **Zero deltas.** `python -m economy_lab.baseline` reports 322 metrics
   unchanged. This slice adds an instrument and a document; it changes no
   default model behaviour.

Prediction 6 is the one most likely to disappoint, and 2 is the one whose
failure would most change the story.

## 6. What is being built

`economy_lab/social_architecture.py` — Wright's model, stdlib only (no
numpy; the project has no third-party dependency and this slice does not
introduce one), deterministic under an explicit seed, **importing nothing
from `model.py`**. It is an instrument, not a component of our economy,
and it must not be able to affect the baseline.

Money is integer coins throughout, which makes prediction 8 exact rather
than approximate and sidesteps every float question the rest of the
project has had to answer.

Distribution readings are plain Python: log-binned histograms, a Gini
coefficient, and a Hill estimator for the tail. No fitting library, and
no exponent reported as agreeing with Wright until §0's **unobtained**
row is closed.

## 7. What this does for the mod

A2, A3 and A5 are one object seen three times: **the firm does not face
its own wage bill, so nothing makes employment an outcome.** The regional
fund is the reason, and the handoff has carried it as an open item since
`docs/55` without a reason to prioritise it. Wright's architecture gives
the reason, and it is the same rule the gameplay layer needs — a colony
that hires pawns, pays them out of its own silver, and has to let them go
when it cannot.

So docking is not a detour from the mod. A5 *is* worker mobility, and A2
is what makes hiring a decision with a cost. The audit tells us which of
our rules can carry that weight and which cannot, before we build the
colony on top of them.
