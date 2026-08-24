# Endogenous labor values: decisions

Recorded **before** implementation, in the style of `docs/08`, `docs/11`,
`docs/15`, and `docs/17`. Every choice below is a modelling convention with
no oracle to settle it inside the laboratory, so it is declared, argued, and
exposed rather than discovered in the diff.

`Commodity.labor_value` has been a frozen import from `FINDINGS.md` since the
first Stage 0 commit. `Process.direct_labor` has been recorded and unused for
value purposes since `docs/08`. This session connects them: labor values are
solved from the process graph, so that the value of a commodity is produced
by the model rather than handed to it.

The immediate stake is the result `docs/18` had to report as a caveat. The
rate of surplus value is currently 38.344 by closed-form construction —
`(ticks_per_worker_day − basket_labor_ticks) / basket_labor_ticks` — because
the value of labor-power is read off an authored constant. Making values
endogenous is what turns s/v from a parameter into an outcome.

---

## 1. The value equation

**Decision: value is denominated in work-ticks, and equals transferred value
plus living labor, per unit of output.**

For a single commodity `c` produced by a set of producers:

```
v(c) = Σ_p runs_p × [ Σ_i inputs_p(i) × v(i) + direct_labor_p ] × share_p(c)
       ────────────────────────────────────────────────────────────────────
                        Σ_p runs_p × outputs_p(c)
```

- **transferred value** — `Σ_i inputs(i) × v(i)` — dead labor passed on by
  the means of production consumed, valued at the same social values;
- **living labor** — `direct_labor` — the work performed in this process;
- **`share_p(c)`** — the existing mass apportionment rule from `docs/08`,
  reused unchanged. Joint products split transferred *and* living labor by
  physical mass. That rule was already implemented, unit-tested, and
  unexercised; this is the first mechanism that would actually consume it.

Ticks, not silver, is the unit. The surplus ledger already denominates
necessary and surplus labor in ticks (`docs/17`), so endogenous values drop
straight in with no conversion. A display conversion to silver
(`labor_value_per_tick`, 11.4/720) stays available for reporting, clearly
labelled as a display scale and not a price.

**Value is not price and does not become price.** Nothing about the solve
enters `effective_unit_cost`, the utilization curve, price formation,
investment, or arbitrage. Read §6 for the single quantity that changes.

## 2. The solve: iterate to a fixed point

**Decision: solve by iteration from the previous day's values, with an
explicit convergence tolerance and a loud failure on non-convergence.**

The current circuit is acyclic (`chemfuel → leaves → yayo`, `provisioning`
standalone), so a topological pass would suffice today. Iteration is chosen
anyway because it survives the graph the project intends to grow into: any
system where basic goods enter their own production — chemfuel fuelling the
refinery that makes it, meals feeding the workers who grow the meals — is
cyclic, and a topological solve does not merely lose accuracy there, it has
no answer at all.

Iterating `v ← A^T v + l` converges exactly when the input matrix is
productive (spectral radius below one), which is the same condition under
which the economy can reproduce itself at all. A system that fails to
converge is one that consumes more of some good than it makes; the right
response is to say so, not to return a number. The solve therefore raises
after `labor_value_max_iterations` (default 1000), matching how
`_planned_runs` already treats a non-converging plan.

This also keeps the laboratory dependency-free. The closed-form alternative,
`v = (I − A^T)^{-1} l`, needs a matrix inverse — a linear algebra dependency
for a result the iteration reaches in a handful of passes on a four-commodity
system.

Determinism: iteration order is sorted by commodity name, the initial guess
is the previous solve, and the tolerance is absolute. Identical inputs give
identical values bit-for-bit.

## 3. Whose technique counts: output-weighted, socially

**Decision: the social value of a commodity is total labor (transferred plus
living) divided by total output, across all active producers in all regions.
Individual per-region values are computed and exposed beside it.**

This is HANDOFF's stated operational definition — output-weighted labor per
unit among active producers — and it is the faithful reading: the value of a
commodity is set by the labor socially necessary to produce the output that
actually meets demand, not by the best or the worst technique in use.

Note what the aggregate form means. Because it is total labor over total
output rather than an average of per-producer ratios, a producer's weight is
its realized share of output. A producer curtailed by the demand-led plan
counts less; a producer running flat out counts more. Value therefore
responds to the composition of supply, which is precisely why the project
insists on labelling **average** and **marginal** reference points
separately: labor value follows the average of realized conditions, while
price and rent follow the marginal producer required to clear demand.

**Rejected: capacity weighting.** Weighting by installed capacity instead of
realized output would make value independent of utilization, which is
attractive — it stops a demand shock from moving a supply-side magnitude, and
it needs no zero-output rule. It is rejected because it answers a different
question: capacity weighting describes the labor a society *could* expend
under its installed structure, not what it *did*. It is retained for one
purpose only, in §4.

**Rejected: per-region value scopes.** Computing a separate social value in
each region would treat the two regions as two societies. The regions trade,
share a price system through arbitrage, and are described throughout the
project as one economy with costly internal transport, so the social average
is taken across both. This is a genuine choice and the alternative is
defensible: if a later session makes trade rare enough that the regions are
economically separate, the scope should narrow, and per-region individual
values are exposed so that work needs no new machinery.

**Individual values.** For each region, the same equation restricted to that
region's producers, using **social** values for inputs — a producer buys its
means of production on the market at prevailing terms and adds its own labor.
The gap between a region's individual value and the social value is the
classical source of super-profit for the producer with better-than-average
conditions, and it is where §7's scenario does its work.

## 4. Two edge cases, decided in advance

**Zero output.** When no producer of a commodity produces anything on a day —
routine, not exotic: the glut idles the drug lab completely — the ratio is
undefined. **Decision: hold the last computed value and mark it stale.**
Value is a property of conditions of production, which do not evaporate
because nobody produced today. The alternative, recomputing from capacity
whenever output stops, would make value jump on the day a plant idles and
jump back when it restarts, manufacturing movement out of a demand event.

**Initialization.** At construction nothing has been produced, so there are
no output weights. **Decision: seed the solve with capacity weights** —
the technique average of the installed structure — then switch to realized
output from the first produced day. This is the one place capacity weighting
survives, and it is confined to a single pass before any history exists.

## 5. What happens to the authored figures

**Decision: `Commodity.labor_value` keeps its authored `FINDINGS.md` figure,
unchanged and immutable. Endogenous values live on the `Economy` beside it.**

`FINDINGS.md` is closed analysis. The frozen figures are not overwritten, not
recalibrated, and not quietly reinterpreted; they stay exactly where they are
as the authored reference, and the model's own solve is a second, separately
named quantity. Where both appear in a report they are labelled distinctly —
`authored_labor_value` versus `labor_value_ticks` — because the entire point
is to be able to compare them.

That comparison is this session's validation, and it is a real test rather
than a formality. The closed analysis solved 653 defs from extraction outward
without reference to price. The laboratory's four-commodity circuit uses the
same per-unit ratios and the same direct-labor figures. If the propagation
machinery is correct, it must reproduce the closed analysis exactly — except
for the one link `docs/08` flagged as stylized, which must show up as a
discrepancy of exactly the size that stylization implies.

Predicted, in ticks:

| commodity | endogenous | authored (FINDINGS) | difference | attributable to |
|---|---:|---:|---:|---|
| chemfuel | 25.00 | 25.00 | 0 | — |
| meals | 305.00 | 305.00 | 0 | — |
| psychoid leaves | 47.45 | 46.20 | +1.25 | stylized 0.05 chemfuel/leaf |
| yayo | 734.60 | 719.60 | +15.00 | 0.2 chemfuel/yayo + 8 × 1.25 |

The two commodities with no inputs must match to the bit. The two downstream
commodities must miss by exactly the stylized chemfuel link and nothing else
— 2.08% on yayo. Any other discrepancy is a bug in the solve, and the session
reports it rather than adjusting anything.

## 6. The one quantity that changes: necessary labor

**Decision: the surplus ledger's necessary labor switches from the authored
basket value to the endogenous social value of the basket. Nothing else reads
labor values.**

This is what makes s/v emergent. Necessary labor per worker-day becomes
`Σ basket(c) × v_social(c)` with `v` solved from the graph, so the value of
labor-power now moves when the conditions of producing wage goods move —
which is the mechanism the whole concept exists to describe.

It changes no behavior. Necessary labor is observational; no price, cost,
plan, or investment decision reads it. The model's behavioral channels are
unchanged from `docs/17`, so the frozen metrics should not move (§8).

**Timing: one day's lag.** Values are solved after production, from the day's
realized runs; the wage paid during production therefore uses the value
prevailing at the start of the day — the previous solve, or the capacity-
seeded solve on day one. This matches the model's established rhythm (one day
per stage of propagation, `docs/08`; wages today and bread tomorrow,
`docs/17`) and avoids a self-referential loop in which the value of
labor-power depends on labor performed in the same day that the value of
labor-power helps account for.

## 7. The scenario: relative surplus value

**Decision: add a `technique-change` scenario in which a more productive
provisioning technique enters one region.**

At day 60, Dust Basin gains a second provisioning producer whose process has
half the direct labor per meal (`meal_efficient_direct_labor`, default
152.5 ticks) and the same capacity. Nothing else changes: no parameter of the
wage, the basket, or the working day is touched.

What should follow, if the mechanism is real:

1. the social value of meals falls, because part of society's meal output is
   now made in half the time;
2. the value of labor-power falls with it, since the basket is meals;
3. necessary labor per worker-day falls, surplus labor rises, and **s/v rises
   in both regions** — including the region that adopted nothing;
4. Dust Basin's individual meal value sits **below** social value, Green
   River's **above**, with social value between them.

That is relative surplus value: surplus rises not by lengthening the working
day or cutting the wage, but by cheapening the goods that reproduce labor.
The working day is fixed at 24,000 ticks throughout, and the basket stays at
two meals — both are inputs to the run, and neither moves.

Predicted magnitudes. Both regions' meal demand is ≈0.628/day against
1.0/day capacity per producer, so the demand-led plan curtails all
provisioning producers of a region pro-rata and the output mix follows
capacity: Dust splits its 0.628 evenly between the old and new techniques.

```
Dust individual   = (0.314 × 305 + 0.314 × 152.5) / 0.628 = 228.75 ticks
Green individual  =                                          305.00 ticks
social            = (0.314×305 + 0.314×152.5 + 0.628×305) / 1.256
                  =  266.875 ticks
necessary/day     = 2 × 266.875 = 533.75
s/v               = (24000 − 533.75) / 533.75 ≈ 43.96
```

So s/v should rise from **38.34 to ≈43.96**, with no parameter changed.

**A limitation to state now rather than discover later.** The inefficient
technique is not driven out. The model has no exit, depreciation, or
mothballing (a standing omission), and both producers clear their cost floor
comfortably at the equilibrium meal price, so the old technique keeps half
the output indefinitely. In a competitive account the efficient technique
would expand and social value would migrate toward 152.5. What the model
demonstrates is therefore the *direction and mechanism* of relative surplus
value, and the SNLT-as-average concept working over genuinely heterogeneous
conditions — not the full competitive dynamic, which needs exit.

## 8. Predictions for the 65 frozen metrics

**Zero movement, with one metric at risk in its last digit.**

Nothing feeds back into behavior, so every price, inventory, capacity,
employment, and recovery-day metric should be exactly unchanged.

The exception is `equilibrium.rate_of_surplus_value` (frozen at 38.344367).
Necessary labor currently divides the authored meal value by
`labor_value_per_tick`, and that round trip lands on 304.99999999999994
rather than 305. The endogenous solve produces exactly 305.0, a relative
change of 2 × 10⁻¹⁶ — below the sixth decimal the reporter prints, so the
metric is predicted to stay 38.344367, and if it moves it will be by one unit
in the last printed digit. Any larger movement in any metric means value has
leaked into a behavioral path and must be found, not accepted.

New quantities to be frozen separately, as newly observed rather than
changed: the four endogenous values, per-region individual values, and the
technique-change scenario's s/v before and after.

## 9. Non-goals

Explicitly not in this session:

- **Labor content of resource grades.** `ResourceGrade` carries a silver
  extraction cost and no labor dimension, so depletion moves cost and rent
  but not value. Making poorer deposits cost more *labor* is the natural next
  step for the value side of the rent story, and it is deliberately deferred:
  it touches living-labor accounting, the wage bill, the labor pool, and the
  value solve at once, and belongs in a session that can measure it alone.
- Values reacting back onto prices in any way (that is a market-mechanism
  question, and price is not value).
- Endogenous SNLT with a moving-average or expectation lag.
- Competitive exit of superseded techniques (needs depreciation).
- Absolute rent; wage bargaining; the reserve army. Unchanged non-goals.
- No RimWorld runtime work. No sensitivity re-run.

## 10. New parameters

| parameter | default | meaning |
|---|---|---|
| `labor_value_tolerance` | 1e-12 | absolute convergence tolerance, ticks |
| `labor_value_max_iterations` | 1000 | raise rather than return a non-solution |
| `meal_efficient_direct_labor` | 152.5 | the entering technique, ticks/meal |
| `technique_change_day` | 60 | when it enters |

## 11. Implementation order

1. Model: the solve, the social and individual value maps, capacity seeding,
   the hold-last rule, history recording. Values computed but unread.
2. Switch necessary labor to the endogenous basket value; verify the
   65 metrics.
3. Tests: reproduction of the closed-analysis figures, the transferred-plus-
   living identity, joint-product apportionment in value, convergence and
   loud non-convergence, hold-last on zero output, determinism.
4. The `technique-change` scenario and its relative-surplus-value tests.
5. Baseline: record deltas against §8; new metrics frozen in their own
   commit, labelled as newly observed quantities.
