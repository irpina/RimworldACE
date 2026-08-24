# Endogenous labor values: measured results

Recorded after implementing the design in
`docs/19-endogenous-labor-values-design.md`. The previous reference
describes the model with the wage relation but with labor values imported
from `FINDINGS.md` as constants.

## Headline

Labor values are now solved from the process graph, and the rate of surplus
value has stopped being a coefficient.

- All 68 tests pass (51 prior + 17 for the solve and relative surplus value).
- **Zero of 65 frozen metrics moved.** Value feeds back into no behavioral
  path, and the reference update is a pure insertion of 10 new observations.
- The solve **reproduces the closed analysis exactly** where it should, and
  misses by exactly the flagged stylization where it should.
- Equilibrium remains exactly stationary; all material and silver residuals
  close to floating-point zero in every scenario, including the new one.
- Runs are bit-identical on repeat.

## The validation: does the solve reproduce `FINDINGS.md`?

This was the test worth running. The closed analysis solved 653 defs from
extraction outward without reference to price. The laboratory's circuit uses
the same per-unit ratios and the same direct-labor figures, so a correct
propagation must land on the same numbers — except at the one link `docs/08`
declared stylized, where it must miss by exactly the amount that stylization
implies.

| commodity | endogenous | closed analysis | difference | predicted |
|---|---:|---:|---:|---:|
| chemfuel | 25.00 | 25.00 | 0 | 0 |
| meals | 305.00 | 305.00 | 0 | 0 |
| psychoid leaves | 47.45 | 46.20 | +1.25 | +1.25 |
| yayo | 734.60 | 719.60 | +15.00 | +15.00 |

Every figure matches the prediction in `docs/19` exactly. The two input-free
commodities agree to the bit. The two downstream commodities are high by
precisely the stylized chemfuel link — 0.05 chemfuel per leaf carries 1.25
ticks, and yayo inherits eight of those plus its own 0.2 chemfuel, for
15.00 ticks, or 2.08% of yayo's value.

Nothing else differs. That is the propagation machinery validated against an
independent 653-def solve, without re-deriving it and without touching a
figure in `FINDINGS.md`, which remains the authored reference on the
`Commodity` alongside the model's own solve.

## The one result: s/v is now an outcome

`docs/18` had to report the rate of surplus value as a free parameter dressed
in data: 38.344 followed in closed form from the working day, the basket
quantity, and an authored constant for the meal's embodied labor. Prices never
entered, and neither did anything else the model did.

It is now solved. The value of labor-power is the basket at endogenous social
values, so it moves when the conditions of producing wage goods move — and
only then. Two scenarios establish both halves of that claim.

### Prices move; the rate of surplus value does not

The subsistence shock destroys 70% of Dust Basin's provisioning capacity. The
money side responds violently:

| quantity | equilibrium | subsistence shock |
|---|---:|---:|
| meal price | 15.000 | 35.521 |
| wage (silver/worker-day) | 30.000 | 71.043 |
| **meal labor value (ticks)** | **305.00** | **305.00** |
| **s/v** | **38.344** | **38.344** |

The money wage more than doubles. The value of labor-power does not move at
all, because destroying capacity does not change how much labor a meal takes.
The same invariance holds across the glut, the producer loss, and the
depletion scenario: all four report meals at exactly 305 ticks and s/v at
38.344.

This is the four-ledger rule made numerical rather than asserted. A doubling
of money wages that leaves the value of labor-power untouched is exactly the
distinction the project refuses to collapse.

### Technique moves; the rate of surplus value follows

The new `technique-change` scenario introduces a second provisioning producer
in Dust Basin at day 60, with half the living labor per meal. The working day
stays at 24,000 ticks and the basket stays at two meals — both are asserted in
tests, because a scenario that quietly shortened the day or shrank the basket
would be demonstrating something else entirely.

| quantity | before | after |
|---|---:|---:|
| social value of meals (ticks) | 305.00 | 266.999 |
| Dust Basin individual value | 305.00 | 228.750 |
| Green River individual value | 305.00 | 305.000 |
| necessary labor per worker-day | 610.00 | 533.998 |
| **s/v (instantaneous)** | **38.344** | **43.944** |

Predicted in `docs/19`: a fall to ≈266.875 and a rise to ≈43.96. Measured:
266.999 and 43.944. The small overshoot on value has a specific cause worth
recording — the adopting region's own labor demand falls with its technique,
so Dust Basin's employment drops from 0.314065 to 0.312031 worker-days, its
meal demand drops with it, and its share of social output falls slightly,
pulling the social average marginally back toward the laggard's 305.

**Green River adopts nothing and its s/v rises identically.** Value is social:
a productivity gain anywhere in the wage-goods sector cheapens labor-power
everywhere. That is relative surplus value, and it emerged from the process
graph rather than from a parameter.

The classical picture appears alongside it. The adopter produces at 228.75
against a social value of 266.999 — below social value, which is where
super-profit comes from — while the laggard produces at 305, above it. The
social value sits between them, which is what "socially necessary" means when
conditions are genuinely heterogeneous. Average and marginal are now
separately visible quantities, as the project's operational definition
requires.

### So: free or emergent?

**Emergent, with one leg still exogenous.** The chain is now:

```
process direct labor + input ratios
      -> social labor value of meals (solved, output-weighted)
      -> value of labor-power = basket x that value
      -> necessary labor -> surplus labor -> s/v
```

Two of the three legs that fixed s/v in `docs/18` are now outcomes: the meal's
embodied labor is solved rather than imported, and the composition of
techniques in society determines it. The working day (24,000 ticks) and the
basket quantity (two meals) remain parameters, so s/v is still *bounded* by
choices — but it is no longer *determined* by them. A change in technique
moves it with nothing else touched, which was the whole test.

## Prediction scorecard

### "Zero movement in all 65 metrics" — **correct**

Exactly zero. The reference update is a pure 40-line insertion with no
deletions. The prediction that `equilibrium.rate_of_surplus_value` might move
in its last printed digit did not materialize: the authored round trip landed
on 304.99999999999994 and the solve produces exactly 305.0, a relative change
of 2 × 10⁻¹⁶ that vanishes well below the sixth decimal, leaving 38.344367
unchanged.

### "Endogenous values reproduce the closed analysis" — **correct, exactly**

All four figures as predicted, to the digit.

### "s/v rises to ≈43.96 on technique change" — **correct (43.944)**

Direction, mechanism, and magnitude all as predicted. The 0.016 shortfall is
the employment feedback described above, which the prediction did not
anticipate.

### "Social value between individual values" — **correct**

228.75 < 266.999 < 305.00.

## The finding beyond the predictions: value falls, price does not

The technique change lowers the social value of meals by 12.46% and moves the
meal price by nothing at all. It stays at exactly 15.000, and so does the
wage.

This is not a bug, and it is worth being precise about why. Price formation in
this model is anchored to a static reference price and driven by inventory
coverage and unmet demand. The demand-led plan curtails provisioning to
demand, so the supply-demand balance after the technique enters is identical
to the one before it; nothing in the price rule can see that half the output
now costs half the labor. The cost floor does see it — the efficient producer
has a lower wage cost per meal — but a cost advantage only becomes a price
movement through competition, and the model has no exit, no undercutting, and
no mechanism by which a cheaper producer takes share from a dearer one.

So the model currently shows a productivity gain appearing **immediately and
fully in value**, and **not at all in price**. The honest reading is that this
is half of a real mechanism: value responds correctly, and the transmission
from value to price is missing rather than modelled. It joins the static
reference price (documented in `docs/16`) as a known limitation, and it is the
strongest argument yet for the competitive machinery — exit, or price
formation that reads cost — that the roadmap has been deferring.

Note also what this means for the surplus story. Because the price and the
wage did not move, the *money* value of labor-power is unchanged while its
*labor* value fell 12.46%. Money profit per meal is unchanged for the laggard
and higher for the adopter, while s/v rose for both. Four quantities, moving
independently, exactly as the standing rule insists they must be allowed to.

## A note on the aggregate form

The social value is total labor over total output, so a producer's weight is
its realized share of supply. One consequence surfaced in testing: the
aggregate ratio is not bit-stable when producers run at differing levels,
because `(r₁A + r₂A) / (r₁B + r₂B)` does not round to exactly `A/B`. The
observed wobble is ~10⁻¹³ relative, far below any reported precision, and the
equilibrium path — where every day's runs are identical — remains exactly
stationary. The corresponding test asserts a tight tolerance rather than bit
equality, and says why.

The zero-output rule works as designed: the glut idles the drug lab
completely, and yayo's value holds at 734.6 instead of vanishing or jumping.

## Reference decision

The reference was rewritten to add the 10 new observations, in its own commit,
labelled as newly observed quantities. No existing metric changed, so nothing
was overwritten — the diff is insertion-only. 65 metrics to 75.
