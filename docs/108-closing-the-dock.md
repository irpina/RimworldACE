# Closing the dock: two corrections to the record

`docs/107` closed A5 and with it `docs/50` §5's critical path. Before
moving to the mod I re-read the audit's own instructions and found two
items whose status had changed under later work without anyone
re-measuring them. Both are measured here. One is a status change nobody
had noticed; the other is a re-measurement `docs/98` explicitly asked
for, and its answer is against the expectation that asked for it.

## 1. A2 is live, not latent

`docs/98` recorded A2 — *the wage is advanced and the advancer bears the
risk* — as **latent**: `ledger.fund_wage_support` measured 3.73e-13,
floating-point dust, so `docs/97`'s prediction 2 was marked a failure and
`docs/98` §5 proposed the branch be "either exercised or removed".

It is exercised. The branch is live in exactly the configuration that
`docs/105`'s deaths are live in, and in no other:

| configuration | `fund_wage_support` | share of wage bill | deaths |
|---|---:|---:|---:|
| neither (`docs/98`'s) | 3.73e-13 | 1.16e-17 | 0 |
| quantum only | 8.03e-13 | 2.51e-17 | 0 |
| flag only | 3.53e-13 | 1.10e-17 | 0 |
| **both** (`docs/105`'s) | **9.75e-04** | **3.86e-08** | **2** |

The same joint condition that makes A3 live makes A2 live, which is not a
coincidence: both are the purse actually binding, seen from the two
sides. A producer that can be short of its payroll is a producer whose
payroll someone else may have to cover.

**`docs/97`'s prediction 2 passes** — it asked for a strictly positive
figure and gets one. It failed in `docs/98` only because the
configuration measured could not reach the branch, which is the recurring
defect class in a gentler form: a finding true of the run and reported of
the model. The rule added at `docs/101` — *before reporting that a rule
is absent, search for it* — needs a companion: **before reporting that a
branch is dead, find the configuration that would reach it.**

### What the support does not do

It does not prevent the death. 9.75e-04 silver against a 25279.5 wage
bill is 3.9 parts in a hundred million; the machinists die on day 582
anyway. So A2's divergence from Wright is **narrower than `docs/98` said
and real**: our advancer bears the risk far enough to die of it, and a
residual the purse cannot cover is still socialised to the fund rather
than ending the firm on the spot.

### The support outlives the firm that started it

Stepped day by day, the first support is on **day 549** — 33 days before
the death — and the last is on **day 1200**, the final day of the run.
The machinists are gone from 582. So the fund is still topping up
*somebody's* payroll six hundred days after the failure that began it:
the cascade `docs/105` measured in capacity (psychoid_leaves 104.03,
yayo 13.00) has a monetary shadow that does not close. Nothing here
identifies which producers, because `fund_wage_support` is keyed by
region alone. That is a limit of the ledger, and it is worth widening
before anyone builds on this.

## 2. A6 re-measured, and the answer is the wrong way round

`docs/98` §5 item 4 asked for A6 to be re-measured once the reserve army
could move, on the reasoning that the share did not move *because* the
army was frozen. The army moves now. Twenty 30-day windows on
`demand_boom(bargaining=True)`, realized share = (necessary + wage
deviation) ÷ living:

| | mean | min | max | spread | peak premium |
|---|---:|---:|---:|---:|---:|
| mobility off | 0.0372955 | 0.0360904 | 0.0376603 | **4.2095%** | 0.0784 |
| mobility on | 0.0371824 | 0.0360904 | 0.0375071 | **3.8102%** | 0.0396 |

The bare share is 0.0001% of level in both, as the identity requires.

**The share still moves, and it moves less.** An endogenous reserve army
was supposed to make the distribution *more* volatile; here it makes it
calmer, by 9.5% of its own movement. The reason is immediate once seen:
mobility's entire effect is to damp the wage premium, and with
bargaining but no habituation the premium *is* the realized share's only
movement. Making the army endogenous does not add a channel — it
regulates the one channel that was already there.

Note the floor. Both runs have the same minimum, 0.0360904, to seven
figures: that is `value_of_labor_power ÷ ticks_per_worker_day`, the
`docs/99` identity, and it is what the windows before the boom bites
read. Mobility lowers the ceiling and leaves the floor exactly where it
was, which is the signature of a rule that damps rather than shifts.

**A6 survives.** `docs/97`'s prediction 5 asked for ≥1% movement and gets
3.81% with both rules on. But the account of *why* it moves is one
channel narrower than `docs/98` left it, and the reasoning that motivated
this re-measurement was wrong — not in what it predicted, which it did
not predict, but in the mechanism it assumed.

## 3. The audit is closed

All seven propositions are measured and every divergence is named:

| | proposition | status |
|---|---|---|
| A1 | money is conserved | holds |
| A2 | the advancer bears the risk | **live, narrow** (§1) |
| A3 | a firm that cannot pay dies | closed, `docs/105` |
| A4 | class position is emergent | **diverges, deliberately** |
| A5 | the reserve army is endogenous | closed halfway, `docs/107` |
| A6 | the shares fluctuate | holds, 3.81% (§2) |
| A7 | revenue is a draw | half built, half declined |

Three things remain, and none of them is the audit.

**The instrument's loose end.** `docs/100` §3 is still open: the SA
reference's stylized facts are single-snapshot Hill readings, never
fitted against Wright's reported exponents. The paper is in hand now, so
it is doable. It validates the instrument, not our laboratory.

**A4 and the rest of A5 are the mod.** A4 wants a colony that can
*become* an employer, which is emergent class position. A5 is closed only
between regions — nobody enters or leaves the workforce, so the
unemployment we report is still bounded by a total supply no rule sets.
Both are R2, the population layer, which `docs/97` §3 named the
destination and put out of scope for the audit.

That convergence is the audit's actual result. The divergences that
remain did not scatter; they collected on the one piece of work that was
always next.
