# The sensitivity sweep, re-run: results

The one-at-a-time parameter sweep has been stale since the cost floor landed,
and `HANDOFF.md` has asked for it back every session since. With Phase A
finished (`docs/44`) the model is stable enough to sweep.

It could not run at all. Fixing it turned up four defects, and **three of the
four produced false answers rather than crashes** — which is the worse kind,
because a sweep's output is a list of claims about which parameters matter and
a false zero is indistinguishable from a finding.

## 1. What was wrong with the harness

**Five integer parameters were perturbed into floats.** `INTEGER_PARAMETERS`
was four names typed by hand, and by the time the model had 129 parameters it
was missing `technique_change_day`, `cost_competition_day`, `history_every`,
`labor_value_max_iterations` and `production_price_max_iterations`. The
resulting `TypeError`s were reported under the heading **"refused to seed"**,
which reads as a finding about the model and was a bug in the sweep. It is
derived from the dataclass field types now. **Refusals went from 5 to 0: every
one was mine.**

**Four metric groups ignored the perturbation entirely.** The capital-goods,
capacity-exit, recreation and rent metrics each built their own scenarios with
default parameters, so every parameter would have scored zero against 28 of
the metrics regardless of what it does.

**Two *pre-existing* groups did the same.** `generous_basket()` and
`perishable_meals()` were called with no parameters, which is why
`generous_meals_per_worker_day` and `perishable_meal_days` had been reported
inert.

**Two scenarios had no metrics at all.** `subsistence_shock` and
`input_shortage` were never collected, so `subsistence_loss_fraction` scored
zero because *nothing was looking*. A parameter reported inert is a claim
about the model, and it is only true if some metric could have seen it move.
Seven readings added; no existing metric moved.

Between them, **nine parameters were being reported inert that are not**:

| parameter | reach, now | why it was hidden |
|---|---:|---|
| `unmet_demand_price_pressure` | 14 | `input_shortage` uncollected |
| `perishable_meal_days` | 12 | `perishable_meals()` ignored parameters |
| `generous_meals_per_worker_day` | 10 | `generous_basket()` ignored parameters |
| `generous_garments_per_worker_day` | 10 | same |
| `generous_medicine_per_worker_day` | 10 | same |
| `subsistence_loss_fraction` | 8 | `subsistence_shock` uncollected |
| `maximum_price_factor` | 8 | only binds during the subsistence shock |
| `technique_change_day` | 4 | perturbed to a float, refused |
| `river_unit_cost` | 3 | only the distant region, barely observed |

Nothing moved the other way. 124 parameters swept, 38 still inert.

## 2. The ranking was measuring the wrong thing

The score was an elasticity: the largest normalized output response over the
input change. It divides by the metric's baseline, and the sweep's metric set
contains baselines that sit near zero.

`glut.local.employment_trough` has a baseline of **0.000412 worker-days**. A
move of 0.017 scores **418**. That is what put `daily_demand` and
`producer_capacity_per_day` at the top of the old ranking — not because they
dominate the model, but because they moved one near-zero denominator. The next
fifteen places went to peak and trough **day indices**, which are step
functions that jump a hundred days at a time.

The primary score is **reach** now: how many of the 378 readings (189 metrics,
both directions) a parameter moves at all. Reach cannot be captured by one
denominator, and it answers the question a screening sweep is actually for —
*does this parameter matter anywhere*. The elasticity is kept beside it,
because where the baseline is a real magnitude it is the more informative
number.

## 3. The result: the value of labor-power dominates

| rank | parameter | reach |
|---:|---|---:|
| 1 | `ticks_per_worker_day` | 241 |
| 2 | `meals_per_worker_day` | 207 |
| 3 | `meal_direct_labor` | 203 |
| 4 | `garments_per_worker_day` | 199 |
| 5 | `medicine_per_worker_day` | 197 |
| 6 | `chemfuel_direct_labor` | 190 |
| 7 | `garment_direct_labor` | 184 |
| 8 | `chemfuel_per_garment` | 180 |
| 9 | `producer_capacity_per_day` | 179 |
| 10 | `daily_demand` | 177 |

**The top seven are the working day, the three basket quantities, and the
direct labor of three wage goods.** Nothing else is close. Capacity and final
demand — the things an ordinary market model would put first — come ninth and
tenth.

That is the model saying what it is: every price in it is anchored to a cost
that includes the wage, the wage is the basket at current prices, and the
basket's *value* is the labor embodied in it divided by the working day. Move
the working day and everything moves. It is a satisfying result to get out of
a mechanical screening sweep rather than by assertion, and it is worth saying
that the sweep was not built to demonstrate it.

The fixed-capital money parameters sit near the bottom — `drug_lab_capital_money`
at reach 4, `plant_pot_capital_money` at 2 — which agrees with `docs/24`:
depreciation is 0.05% of cost, and the money side of a machine barely reaches
anything. Their *labor* counterparts do much better (`provisioner_capital_labor`
at 74, `refinery_capital_labor` at 61), because those feed the value solve.

## 4. The 38 that move nothing, and what each group means

**Authored labor values (10).** `chemfuel_labor_value`, `meal_labor_value`,
`labor_value_per_tick` and the rest. These are the closed analysis's figures,
kept on `Commodity` beside the solved ones so the two can be compared rather
than conflated. They move nothing because **the model has solved its own
values endogenously since `docs/19`** and never reads the authored ones for
anything but display. That is the design working, confirmed mechanically.

**Masses (9).** `mass_per_unit` exists only to apportion joint costs, and
**every current process has exactly one output**, so the rule is implemented,
unit-tested, and never exercised. The sweep confirms a known omission rather
than discovering one.

**Solver tolerances and caps (4).** The value solve and the price solve both
converge far inside their tolerances and nowhere near their iteration caps, so
±10% on either changes nothing. That is the healthy answer.

**Never binding at ±10% (11).** `initial_cash`, `labor_pool_worker_days`,
`worker_initial_cash_days`, `investment_margin_threshold`,
`construction_cost_multiplier`, `speculative_inventory_limit`,
`minimum_price_factor`, `expectation_alpha` and three others. Each is a limit
the circuit does not reach. Worth restating as a caution: **"never binds at
±10%" is not "never binds"** — `maximum_price_factor` was in this group until
a scenario that actually stresses prices was collected, and then it appeared
at reach 8.

**Reserve grades (2) and wood (2).** `chemfuel_expensive_reserve` is zero at
baseline so it cannot be perturbed proportionally at all; the depletion
scenario overrides it directly. Wood's price and capacity are inert because
wood is 0.0144 units a day of a nine-commodity economy.

## 5. What the sweep still cannot see

- **The four boolean parameters** — `capital_goods`, `capacity_exit`,
  `recreation_basket`, `record_history` — are regime switches, not
  magnitudes. A ±10% of `False` is meaningless. Their effects are the
  subject of `docs/37`, `docs/39` and `docs/41` respectively, which is a
  better treatment than a sweep could give.
- **One-at-a-time only.** Interactions are invisible. `docs/41` showed a
  case where they matter: `yayo_per_worker_day` has a reach of only 6, and
  yet moving it from zero makes every commodity in the model basic.
- **Scale metrics are parameter-independent by construction** — they read
  `out/embodied_labor.csv`, not a scenario. Their zeros are structural and
  the ranking says so, so that 189 metrics are not silently treated as 189
  chances to detect an effect.

## 6. Cost

A full sweep is 248 metric collections at roughly eleven seconds each, so
about forty-five minutes. `capacity_exit()` alone is 57% of it, because the
rest point it exists to show does not appear until day 2,200 (`docs/39` §7).
That is the price of a metric that measures a slow process, and it is worth
paying deliberately rather than trimming the scenario until the finding
disappears. The sweep is not, and has never been, a per-commit check.
