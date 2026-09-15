# Sales that follow production: the first endogenous firm death

Measured against `docs/104`'s eight predictions. **Six passed and two
failed**, and both failures are more interesting than the passes.

**The headline: on day 582 of `cash_circuit`, both regions' component
producers go bankrupt because they cannot pay their wage bill. That is
the first endogenous firm death in this model's history. Every previous
retirement was a capital-allocation decision — `_exit` withdrawing from a
sector earning below the going return. This one is a firm that ran out of
money and could not make payroll, which is Wright's F1, and it took four
documents to reach.**

**And it is not marginal. `docs/102` predicted killing the zombie would
change nothing, because it employed 0.12% of the region's labour.
Regional employment falls from 0.31844 to 0.10914 — a 66% collapse —
because the producer was marginal in *employment* and structural in
*function*. It was Department I. Losing it starved plant replacement
across the whole circuit: 104.03 units of psychoid-leaf capacity, 13.00
of yayo, 8.10 of chemfuel, 1.30 of meals, against the 0.125 of components
actually lost.**

## 1. The scorecard

| # | prediction | verdict |
|---|---|---|
| 1 | inert by default; 322 metrics unchanged | **pass** |
| 2 | inert where nobody idles; bit-identical | **pass** |
| 3 | the flag alone leaves `cash_circuit` bit-identical | **fail** — §3 |
| 4 | together, the consecutive idle run exceeds 1 | **pass** — 1 → **29** |
| 5 | and reaches 30; `_bankrupt` fires on the component producer | **pass** — day 582 |
| 6 | money conserved | **pass** — −1.96e-08 |
| 7 | the bare wage share identity holds | **pass** |
| 8 | the macro effect is under 1% | **fail** — **66%**, §4 |

## 2. The two rules are jointly effective

| quantum | `sales_follow_production` | bankruptcies | peak consecutive idle | employment |
|---:|---|---:|---:|---:|
| 0 | off | 0 | 0 | 0.31819 |
| 0 | on | 0 | 0 | 0.31819 |
| 1e-3 | off | 0 | **1** | 0.31844 |
| **1e-3** | **on** | **2** | **29** | **0.10914** |
| 3e-3 | on | 2 (day 565) | — | 0.10609 |

Neither rule does anything alone. `docs/103` established the first row
pair; the third row is its central negative result, the idle counter
pinned at one. Removing the capacity fallback lifts it to 29 and then
`_bankrupt` fires on the thirtieth.

The mechanism is exactly as `docs/104` §1 described it. A producer below
the employment cliff runs nothing; with the fallback it was still paid
its share of the commodity's sales — as the sole component producer, 100%
of them — and the purse rose back above the cliff. Without the fallback
it is paid nothing, the purse keeps falling, and it idles until it dies.

## 3. Prediction 3: the opening day has no yesterday

The flag alone was predicted to leave `cash_circuit` bit-identical,
because `docs/101` measured that no producer is ever liquidity-idle there
and the fallback should therefore never be reached. Curtailment moved
from 1.451509 to 1.457965.

Instrumenting `_supply_shares` shows the fallback condition holding
**exactly 18 times in 1200 days: once for each of nine commodities in
each of two regions, all on day 1.** On the first production day nothing
has been produced yet, so every producer's `last_runs` is zero and every
commodity falls back to capacity. My account of the mechanism was right
about idleness and silent about the initial condition.

I wrote a `self.day > 0` guard, measured it, and found it did not help —
the fallback fires on day **1**, not day 0. Changing the guard to
`self.day > 1` would have made my own prediction retroactively true by
fitting a magic number to it, which is `docs/100` §6's error, so the
guard was reverted.

The unguarded behaviour is in any case the better reading. The inventory
sold on day 1 is the region's seeding; it was produced by nobody
in-model, so no producer has a claim on it, and paying the fund is
correct. A one-day difference in who receives the opening sales
propagates as a small perturbation — prices are bit-identical at 1200
days, and the bankruptcy lands on day 582 either way.

## 4. Prediction 8: marginal in employment, structural in function

`docs/102` predicted, and `docs/103` could not test, that killing the
component producer would move regional employment by less than 1%. It
moves it by 66%.

| | before | after |
|---|---:|---:|
| Dust Basin employment | 0.31844 | **0.10914** |
| Green River employment | 0.31844 | **0.10914** |

`capacity_lost`, over the run:

| commodity | capacity lost |
|---|---:|
| psychoid_leaves | 104.0319 |
| yayo | 13.0040 |
| chemfuel | 8.1033 |
| meals | 1.3004 |
| **components** | **0.1250** |

The producer that died accounted for 0.125 of the capacity destroyed. The
other 126 units are collateral: `cash_circuit` sets `capital_goods=True`,
so components are what every other producer's plant is rebuilt from
(`docs/36`). With no component supplier, plant replacement stops and
capacity decays across the circuit.

So the prediction failed in the direction that makes the rule matter. The
reasoning behind it — "it was already curtailed to nothing, so its death
cannot signify" — confused a producer's *size* with its *position*. A
sector can be arbitrarily small in labour and still be the one everything
else is built out of. That is a Department I property and the model
reproduces it without having been asked to.

It is worth being clear about what this does and does not vindicate. It
does not show our model has Wright's business cycle. It shows that once
firm death is reachable, this circuit's input-output structure propagates
it — which is a property of the circuit, and an argument for taking the
cascade seriously rather than a validation of the rule.

## 5. The identity, again (prediction 7)

Bare wage share 0.036090633 against the identity's 0.036090716, after two
bankruptcies and a 66% employment collapse. `docs/99` has now survived a
hundred bankruptcies (`docs/103`), two bankruptcies with a cascade, and
an economy reduced to zero production. It is an identity.

## 6. Where docking stands

The A3 thread is closed. Our laboratory now has, gated off by default:

- a purse that must cover the wage bill (`docs/55`, found in `docs/101`),
- a floor that makes "cannot afford anybody" reachable (`docs/102`),
- revenue conditional on having produced (`docs/104`),

and together they produce an endogenous firm death from an unpayable
payroll. That is F1's behaviour, reached by three rules where Wright
needs one, because his firms have no constant capital and ours do.

**A7 does not need to be built.** `docs/103` §7 argued that coupling
revenue to employment required Wright's market-sample draw and therefore
a PRNG bit-exact across CPython and Mono under `docs/53`'s contract. It
does not: the coupling was achievable deterministically, because the part
that mattered was *conditionality*, not *randomness*. What a draw would
add is revenue **uncertainty** — a firm that employs people and still
earns nothing — which is a different property from the one needed here,
and is no longer on the critical path for firm death.

That leaves A5, worker mobility, as the remaining divergence on
`docs/50`'s critical path, and the one the gameplay layer actually needs.

## 7. What was changed

`sales_follow_production`, defaulting to `False`, threaded through
`ScenarioParameters`; one condition in `_supply_shares`. Nine tests in
`tests/test_sales_follow_production.py`, including the one that pins
prediction 3's failure so it cannot be quietly forgotten.
`python -m economy_lab.baseline` reports 322 metrics with no nonzero
delta.
