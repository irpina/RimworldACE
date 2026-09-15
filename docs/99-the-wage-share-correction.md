# The wage share: a correction to `docs/98`

**`docs/98`'s headline was wrong, and wrong in the way `docs/98` itself
named two paragraphs later. The wage share does move — 4.2% of its level
over a demand boom — and the measurement that said otherwise was taken on
four scenarios in which the rule that moves it is switched off by
default. `docs/98` caught exactly this mistake in its own prediction 4
("*a default is not a scenario*") and then made it again, in the finding
it led with.**

What survives is smaller, sharper, and worth more than what it replaces:
**the share at the value of labor-power is an identity.** It is
`value_of_labor_power ÷ ticks_per_worker_day`, and no rule about
quantities can move it — not the wage bill binding, not entry, not exit,
not worker mobility. That is not a defect. It is the model being right
about something, and it retires `docs/98` §5's step 4 before it was built.

## 1. The identity

Two lines of `_settle_labor` decide it:

```
necessary_labor += worker_days × value_of_labor_power(region)
living_labor    += labor_performed
worker_days      = quantize(labor_performed ÷ ticks_per_worker_day)
```

So

```
wage share = necessary ÷ living
           = (labor_performed ÷ ticks_per_worker_day) × VLP ÷ labor_performed
           = VLP ÷ ticks_per_worker_day
```

The quantity of labor cancels. Measured against the algebra:

| | value |
|---|---:|
| `value_of_labor_power` | 866.169930456 |
| `ticks_per_worker_day` | 24000.0 |
| VLP ÷ ticks (predicted) | 0.036090414 |
| measured bare share | 0.036090369 |

Agreement to seven significant figures; the last digits differ because
the employment quantum floors `worker_days` onto a grid, so the realised
ratio sits a hair under the identity. `docs/98` reported this number
frozen to fifteen significant figures across a 720-day `complete_market`
run and read it as a pathology. **It is an identity, and freezing is what
an identity does.**

It also names its own escape. Only two things can move the bare share:
the **value of labor-power** (technical change in wage goods, or
habituation moving the standard) and the **length of the working day**.
That is the classical distinction between relative and absolute surplus
value, and our model reproduces it by construction rather than by
accident. A model in which building a factory moved `s/v` would be the
one with the defect.

## 2. What `docs/98` measured, and what it should have

`equilibrium`, `cash_circuit`, `gravitation` and `complete_market` all
take `wage_bargaining_strength` and `habituation_speed` from
`ScenarioParameters`, where both default to **0.0**. `_bargain` and
`_habituate` each return before touching anything at zero — deliberately,
so that a model without the rule stays bit-identical rather than merely
close. So no premium ever forms, `wage_deviation_labor` stays empty, and
the *realized* share is bit-identical to the bare one.

`docs/98` measured `necessary ÷ living` — the identity — in four
scenarios where the only other channel was disabled, and concluded the
laboratory "redistributes nothing between wage and profit". Two errors
stacked: the wrong ratio, and the wrong configuration.

Re-measured on `demand_boom`, twenty windows of thirty days:

| run | bare share | realized share | peak premium |
|---|---:|---:|---:|
| no bargaining | 1.56e-08 (0.0000%) | 1.56e-08 (0.0000%) | 0.000000 |
| **bargaining** | 2.18e-08 (0.0001%) | **1.57e-03 (4.2095%)** | +0.078387 |
| bargaining + habituation | **1.59e-03 (4.2640%)** | 1.59e-03 (4.2505%) | +0.079110 |

Read the three rows against §1.

- With bargaining, the **realized** share moves 4.2% and the bare share
  does not. That is the premium being booked apart from the value of
  labor-power — `docs/46`'s deliberate choice, working.
- With habituation, the **bare** share moves too, by almost exactly the
  same amount. Habituation moves the habitual standard, which moves the
  value of labor-power, which is the identity's one escape. The algebra
  predicted which run would move the bare share, and it did.

Prediction 5 of `docs/97` asked for movement of at least 1% of level.
**It passes at 4.2%**, on the scenario built for it.

## 3. The corrected scorecard

| # | prediction | `docs/98` | corrected |
|---|---|---|---|
| 1 | A1 money conserved | pass | pass |
| 2 | A2 fund support live | fail (latent) | fail (latent) |
| 3 | A3 no death by wage bill | pass | pass |
| 4 | A5 `labor_pool` is `inf` | fail (it is 1.0) | fail (it is 1.0) |
| 5 | A6 shares sum *and* fluctuate | **half** | **pass** |
| 6–9 | the instrument, the baseline | pass | pass |

**A6 holds.** Our lab has fluctuating wage and profit shares, which is
what Wright's model produces and what `docs/98` said ours did not. Six of
nine predictions pass.

## 4. What this does to the docking programme

`docs/98` §5 listed four steps. This document settles two of them without
building anything.

- **Step 4, "re-measure A6 after the wage bill binds", is retired.** The
  bare share cannot respond to a solvency rule — the identity forbids it —
  and the realized share already moves. There was never a deeper finding
  waiting behind it.
- **Step 2's motivation changes.** Making the wage bill a solvency
  constraint (A3) is still worth doing, but *not* as a fix for the shares.
  It is worth doing because §3 of `docs/98` showed, on a working model,
  that this single rule is the difference between a stationary economy
  with a persistent reserve army and one firm employing 992 of 1000
  actors. It is a rule about **employment and firm death**, and it should
  be judged on those.

Unchanged: A3 and A5 are real divergences, A2 is latent, and the paper is
still unobtained.

## 5. The pattern, twice

`docs/98` found prediction 4 wrong because I read `Region.labor_pool`'s
dataclass default (`inf`) instead of what the scenarios set (`1.0`), and
wrote "*a default is not a scenario*" as the lesson. The headline of the
same document rests on the same mistake about
`wage_bargaining_strength`. Writing the lesson down did not prevent
committing it eleven paragraphs earlier.

What would have caught it: the audit read *defaults and code paths* and
never asked whether the paths it was auditing were **live in the runs it
measured**. A branch that is off is indistinguishable from a branch that
does nothing, and `docs/96` made the same point about a branch nothing
could reach. Three times now this project has been bitten by unreached
code presenting as a finding.

So the rule this document adds: **before reporting that a rule does not
do something, show the rule running.** `docs/99`'s tests do that — one
asserts the premium is zero without bargaining, and the next asserts the
share moves with it, so the finding and its refutation sit side by side
and neither can rot silently.

## 6. What was changed

Nothing in the model. Six tests in `tests/test_wage_share.py` pin the
identity, its escape, and the fact that the channel is off by default.
`docs/98` carries a correction banner. `python -m economy_lab.baseline`
reports 322 metrics unchanged.
