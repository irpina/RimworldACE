# Docking with the Social Architecture of Capitalism: results

Measured against `docs/97`'s nine predictions. As written: five passed,
two failed, one passed by half, and one of the failures corrects
`docs/97`'s own headline. **After `docs/99`: six passed, two failed** —
see the banner below.

**Corrected by `docs/101`.** A3 below is **wrong as stated**. "Neither is
the wage bill" is false: `_produce` has curtailed output to what the purse
affords since `docs/55`, and `_outlay_per_run` includes the wage — for
five of the circuit's nine processes it is *nothing but* the wage. The
measurement (zero deaths by wage bill) stands; the explanation does not.
Producers do not die of the wage bill because the curtailment is
**continuous** where Wright's F1 is **floored**, so a drained purse
reaches a fixed point instead of zero. `cash_circuit`'s component producer
sits at 0.7% of its purse target, alive, for 1200 days.

**Corrected by `docs/100`.** §3 of this document is **refuted**. The
paper arrived; Wright's rule F1 fires against the firm's *money
holdings*, which is the rule §3 rejected, and his model is stationary
with a persistent reserve army. The rule §3 adopted — firing against
trailing revenue — collapses the transcription to 27 firms and 50%
unemployment. "One rule decides whether a capitalist economy has a
reserve army at all" is **withdrawn**. §2's lab-side audit is unaffected.

**Corrected by `docs/99`.** The headline below is **wrong**. The wage
share does move — 4.2% of its level over a demand boom — and the
measurement that said otherwise was taken on four scenarios where
`wage_bargaining_strength` defaults to `0.0`, so the rule that moves it
never ran. That is the same "*a default is not a scenario*" error this
document catches in its own prediction 4, committed eleven paragraphs
earlier. What survives: `necessary ÷ living` is an **identity**,
`value_of_labor_power ÷ ticks_per_worker_day`, which no quantity rule can
move — so §2's A6 reading measured the wrong ratio *and* the wrong
configuration. **A6 passes**, and the scorecard is six of nine, not five.
§5's step 4 is retired. Everything else here stands.

**The headline, corrected: our lab's wage share does not move. It is
0.036090 in every thirty-day window of a 720-day run, to fifteen
significant figures. Wright's model produces fluctuating wage and profit
shares as a central result; ours has a distribution between wage and
profit that is, to measurement precision, a constant. That is the sharpest
thing docking found, and `docs/97` did not predict it — it predicted this
one would pass.**

Second: `docs/97` claimed our producers "cannot fail from the wage side,
because `_pay_wages` tops up from the regional fund." The branch is real
but **it is never taken**. Across every committed scenario the fund's wage
support totals 1e-13 — floating-point residue from splitting a bill, not
support. The divergence is **latent, not live**, which is a weaker and
more honest finding than the design document asserted.

## 1. The scorecard

| # | prediction | verdict |
|---|---|---|
| 1 | A1 holds: `cash_balance()` within 1e-6 | **pass** |
| 2 | A2 fails live: `fund_wage_support` strictly positive | **fail** — latent, 1e-13 |
| 3 | A3 fails: 0 deaths by wage bill, exits positive | **pass** |
| 4 | A5 fails: `labor_pool` is `inf` in every scenario | **fail** — it is `1.0` |
| 5 | A6 holds: shares sum to 1 *and* fluctuate ≥1% | ~~**half**~~ → **pass** (`docs/99`) |
| 6 | SA reference reproduces facts 1 and 6 | **pass** — re-established on the paper's own rules (`docs/100`) |
| 7 | SA self-organises into three classes, employers <20% | **pass** |
| 8 | SA conserves money to the bit | **pass** |
| 9 | `baseline` reports 322 metrics unchanged | **pass** |

## 2. The lab side

### A1 — money is conserved (prediction 1, pass)

| scenario | `cash_balance()` | `producer_cash` |
|---|---:|---|
| `equilibrium` | `+0.000e+00` | off |
| `cash_circuit` | `-1.898e-08` | on |
| `gravitation` | `+1.834e-09` | on |
| `complete_market` | `-3.201e-10` | on |

Inside 1e-6 everywhere, and exactly zero where no purse is in play. The
one proposition our architecture shares with Wright's outright.

### A2 — who bears the wage risk (prediction 2, fail)

`ledger.fund_wage_support`, summed:

| scenario | total | per region |
|---|---:|---|
| `equilibrium` | 0 | — (no purses) |
| `cash_circuit` | ~0 | 2.4e-13, 1.4e-13 |
| `gravitation` | ~0 | 4.6e-13, 3.9e-13 |
| `complete_market` | ~0 | 1.1e-12, 3.7e-13 |

Those are last-bit residues of `wage_bill × labor / labor_performed`
summed back, not a fund covering anybody's payroll. **Producers do pay
their own wage bills in every committed scenario.**

This matters in two directions. The reassuring one: the regional pool is
not silently absorbing risk today, so the handoff's open item is smaller
than it looked. The unreassuring one: the branch is **untested by
anything that runs**, and `docs/96` is this project's own precedent for
what an unreachable branch is worth — a latent false verdict nobody could
find until the state that reaches it arrives. A colony that hires pawns
is exactly that state.

### A3 — what kills a producer (prediction 3, ~~pass~~ — **explanation withdrawn by `docs/101`**)

> The table is right and the reason given under it is wrong. There *is* a
> solvency rule on the purse and it *does* include wages; it simply cannot
> reach a conclusion. See `docs/101` §3.

| scenario | exits | retired | bankruptcies | deaths by wage bill |
|---|---:|---:|---:|---:|
| `equilibrium` | 0 | 0 | 0 | **0** |
| `cash_circuit` | 0 | 0 | 0 | **0** |
| `gravitation` | 0 | 0 | 0 | **0** |
| `complete_market` | 107 | 0 | 0 | **0** |

Firm death in our lab is entirely a *return* phenomenon: `_exit` retires
capital that has earned below the going rate for the investment lead time.
The wage bill is not a solvency constraint and cannot become one while A2
holds as it does. Wright's architecture makes the wage bill *the* solvency
constraint, and §3 below shows that this single choice is what separates a
stationary economy from a monopoly.

### A5 — the reserve army (prediction 4, fail — and the prediction was
simply wrong)

`docs/97` predicted `labor_pool` would be `inf`, reading the dataclass
default. Every committed scenario sets it:

| scenario | `labor_pool` | employment rate |
|---|---:|---:|
| `equilibrium` | 1.0 | 0.3175 / 0.3175 |
| `cash_circuit` | 1.0 | 0.3182 / 0.3182 |
| `gravitation` | 1.0 | 0.3632 / 0.3471 |
| `complete_market` | 1.0 | 0.4679 / 0.3502 |

So the reserve army is bounded and measured, not unbounded. *A default is
not a scenario*, and reading one for the other is the mistake here.

The proposition still diverges, for the reason underneath the prediction
rather than the one stated: **the pool is a fixed parameter and employment
is a fraction of it.** Employment moves (0.3175 → 0.4679); the pool never
does. Nobody enters, nobody leaves, and no rule sizes it. That is
`docs/50` §5's worker mobility, reached from a second direction.

### A6 — the shares (prediction 5, ~~half~~ — **retracted by `docs/99`**)

> Everything in this subsection measures `necessary ÷ living` on scenarios
> where bargaining is off. That ratio is an identity and those scenarios
> form no premium, so it could not have moved whatever the model did.
> With bargaining on, the realized share moves 4.2%. Kept as written so
> the error stays legible.

Shares sum to one exactly: `1.000000000000` in every window, both
scenarios. That half is close to tautological given how `necessary_labor`
and `surplus_labor` are defined, and should not be credited as much.

The half that matters, measured over twenty-four consecutive thirty-day
windows (the ledger is cumulative, so a level reading is a running
average and looks constant by construction — these are differenced):

| scenario | wage share min | max | spread | relative |
|---|---:|---:|---:|---:|
| `equilibrium` | 0.036090 | 0.036090 | 4.1e-15 | 0.0000% |
| `complete_market` | 0.036090 | 0.036090 | 2.5e-08 | 0.0001% |

The prediction asked for movement of at least 1% of level. It fails by
about five orders of magnitude, and it fails in `complete_market` — purses,
posted prices, procurement, entry *and* exit all on, 107 exits over the
run. **The most dynamic configuration we have redistributes nothing
between wage and profit.** `s/v` reads 26.708 in all four scenarios and
agrees to four decimal places across configurations that differ in
whether firms hold money at all.

That is worth stating plainly: capacity churns, prices gravitate, firms
exit — and the class distribution of the product does not notice. Our
business cycle, such as it is, is a cycle in *quantities* with a frozen
distribution. Wright's is a cycle in the distribution itself.

## 3. The instrument, and three failed reconstructions

> **Refuted by `docs/100`.** Six rule bodies were wrong, not three, and
> the one this section settles on — firing against trailing revenue — is
> not Wright's. Kept as written so the error stays legible; read
> `docs/100` §2 for the six, and §4 for which of them did the damage
> (none alone: the monopoly needed the whole broken combination).

`economy_lab/social_architecture.py`: Wright's model, stdlib only,
integer coins, deterministic under a seed, importing nothing from
`model.py` (a test reads the import graph with `ast` to check, rather than
grepping the text — the module's docstring names `economy_lab.model` in
prose and the first version of that test failed on its own docstring).

`docs/97` §0 graded the rule bodies **unobtained**, and that turned out to
be the load-bearing gap. Three reconstructions failed before one worked,
and the failures are the most informative part of this document.

**First: deadlock.** Hiring required a candidate with
`money > wage_max`. At a symmetric start every actor holds exactly the
mean, so nobody ever cleared the bar, no firm was ever born, and every
coin drained into the market pool — which nothing can draw from when no
firm exists. An absorbing state reached in the first month. The
corroborated wording is "sufficient ex ante funds to pay the **average**
wage"; against `wage_max/2` the economy self-organises. A test pins this.

**Second: monopoly, blamed on the wrong rule.** With hiring fixed, firm
sizes concentrated without limit — 18 firms at 400 months, the largest
holding 699 of 1000 actors, unemployment falling to zero. I supposed the
cause was drawing the hirer from *all* actors including employees, which
makes attachment ∝ (firm size × owner wealth), i.e. super-linear, and
super-linear preferential attachment gives a winner rather than a power
law. Restricting the pool to owners slowed it and **did not stop it**:

| pool | months | firms | largest | unemployment |
|---|---:|---:|---:|---:|
| `all` | 400 | 18 | 699 | 0.004 |
| `owners` | 400 | 25 | 361 | 0.009 |

A reasonable hypothesis, cleanly falsified. Both variants are kept as
`candidate_pool` so the falsification stays measurable.

**Third: the rule that was actually wrong.** I had the firing test
comparing the wage bill against the owner's *accumulated purse*. The
corroborated wording is "if **current revenues** do not cover the expected
wage bill". A rich owner buffers its payroll out of stock indefinitely, so
no large firm ever dies:

| firing test | months | firms | largest | firm Hill | income Gini | unemployment |
|---|---:|---:|---:|---:|---:|---:|
| `funds` | 150 | 138 | 27 | 2.28 | 0.894 | 0.017 |
| `funds` | 400 | 25 | 361 | 0.71 | 0.936 | 0.009 |
| `funds` | 800 | 5 | **992** | — | 0.722 | **0.000** |
| `revenue` | 150 | 109 | 64 | 1.10 | 0.879 | 0.327 |
| `revenue` | 400 | 124 | 38 | 1.63 | 0.901 | 0.306 |
| `revenue` | 800 | 111 | 122 | 1.61 | 0.927 | **0.333** |

Read the last three rows. Against revenue the economy is **stationary**:
~110 firms at every horizon, a heavy but bounded firm-size tail, and an
unemployment rate that settles near a third and stays there. Against
funds it monopolises and unemployment goes to zero.

**One rule decides whether a capitalist economy has a reserve army at
all**, and it is the rule our lab does not have (A3). That is the
substantive result of docking, and it was found by the reconstruction
failing rather than by the reconstruction succeeding.

### Predictions 6, 7, 8

**6 — pass, qualitatively and only qualitatively.** Firm sizes are
heavy-tailed (Hill 1.1–1.6, in the neighbourhood of Zipf) and income is
two-class (Gini 0.88–0.93, Hill ~0.7–0.8, top decile taking two thirds).
Per `docs/97` §0 **no exponent here is reported as agreeing with
Wright's**, because Wright's exponents are unobtained. These are
statements about shape.

**7 — pass.** From every actor unemployed and equally rich:

| seed | employers | employees | unemployed |
|---|---:|---:|---:|
| 0 | 116 (11.6%) | 566 | 318 |
| 1 | 127 (12.7%) | 547 | 326 |
| 2 | 103 (10.3%) | 556 | 341 |

Three classes, employers a stable minority under 20%, across seeds.

**8 — pass, exactly.** Integer coins, every rule a transfer; the total
after any number of steps equals the initial total with no tolerance.

### Prediction 9 — pass

`python -m economy_lab.baseline`: 322 metrics, every delta `+0.000%`.
This slice adds an instrument, a document and sixteen tests, and changes
no default model behaviour.

## 4. What this is worth, and what it is not

**It is not a validation of our model.** `docs/97` §2 argued the two models
have no observable in common and that stands: nothing in §2 above compares
a number of ours to a number of Wright's, because there is no such pair.
Anyone reading this as "the economy lab has been checked against the
literature" is reading it wrong.

**It is an audit of our wiring, and the wiring has one clear hole.** A3,
A5 and A6 are the same hole seen three times:

- no rule makes the wage bill a solvency constraint (A3),
- so nothing makes employment an outcome, and the pool is a parameter (A5),
- so the split between wage and profit never moves (A6).

§3 shows what that costs, in a model where the same choice is the
difference between a stationary economy with a persistent reserve army and
one firm employing 99% of the population.

**The instrument is a reconstruction, and its authority is limited
accordingly.** Two of its three rule bodies were settled by *which variant
reproduces a reported result*, which is weak evidence and the kind this
project normally refuses. It is recorded as weak deliberately. The
firing-rule finding in §3 is the one I would still expect to survive
reading the paper, because it follows from the corroborated wording rather
than from fitting; the hiring-threshold and candidate-pool choices are the
ones most likely to be wrong.

**Obtaining the paper is now the highest-value single action available.**
Every full-text route was blocked here (`docs/97` §0). It is not
expensive for a human: one PDF, from `arxiv.org/abs/cond-mat/0401053` or
the author's own copy. With it, §3's three reconstructions resolve to
right or wrong in an afternoon, and prediction 6 can be restated with
exponents instead of shapes.

## 5. What follows

1. **Read the paper and re-run §3.** Cheap, and it upgrades everything
   here from provisional to settled.
2. **Design the wage bill as a solvency constraint** (A3), with the
   `fund_wage_support` branch either exercised or removed. §2's A2 finding
   makes this smaller than expected: the branch is already unused, so
   making the purse binding may be closer to deleting a fallback than to
   writing a rule.
3. **Then worker mobility** (A5) — `docs/50` §5's remaining critical-path
   omission, which is also what makes a colony able to hire.
4. **Re-measure A6 afterwards.** If the shares still do not move once the
   wage bill binds and the pool can change size, that is a much deeper
   finding about our model than this document can claim, and it would
   deserve its own arc.

Steps 2 and 3 are the same rule from the mod's side: a colony that pays
pawns out of its own silver and must let them go when it cannot. Docking
did not divert us from the mod; it named the rule the mod needs and
showed, on a working model, what happens when that rule is absent.
