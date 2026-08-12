# Accounted input-output production: results

Compared against `docs/07-accounted-input-predictions.md`, recorded before the
implementation existed. Nothing here was tuned to make the forecast come true;
where the forecast failed, it failed.

---

## The headline: every frozen metric is unchanged

All thirteen behavioral metrics are bit-identical to the reference frozen at
`cae1ba2`.

```
arbitrage.export_volume                    13 -> 13          +0.000%
equilibrium.distant_price_range             0 -> 0
equilibrium.local_price_range               0 -> 0
glut.distant_trough_day                    82 -> 82          +0.000%
glut.distant_trough_price           20.105683 -> 20.105683   +0.000%
glut.local_half_recovery_days               9 -> 9           +0.000%
glut.local_half_recovery_quadrums         0.6 -> 0.6         +0.000%
glut.local_trough_day                      67 -> 67          +0.000%
glut.local_trough_price             12.790741 -> 12.790741   +0.000%
producer_loss.capacity_recovery_days       75 -> 75          +0.000%
producer_loss.capacity_recovery_quadrums    5 -> 5           +0.000%
producer_loss.local_peak_day              119 -> 119         +0.000%
producer_loss.local_peak_price       38.630290 -> 38.630290  +0.000%
```

The frozen reference is therefore **not** being rewritten. There is nothing to
rewrite.

Eleven of the thirteen predictions forecast movement. All eleven are wrong. The
two that forecast stasis — both equilibrium price ranges — are right, and
`arbitrage.export_volume` landed at 13, the top of its predicted 10–13 range,
by not moving at all.

This is not the model failing to change. Production really does consume
accounted inventory now, and a producer that cannot source inputs really is
curtailed. Three separate things explain the null result, and only the first
was anticipated.

---

## Why 1: a glut cannot be dampened by an input constraint

The prediction said the glut would be shallower and shorter because
"low-price production contracts against real costs and inputs."

The causal direction is wrong, and it is wrong in a way worth keeping.

A glut in the *final* good means the drug lab produces **less**. Producing less
means demanding **fewer** inputs. So a downstream glut makes upstream inputs
*more* abundant, not scarcer. An input constraint can only bite when inputs are
scarce. It is structurally incapable of damping a glut in the good at the end of
the chain.

The observable consequence runs entirely the other way. During the glut, Dust
Basin's yayo price falls to 12.79 and the drug lab curtails; leaf stock rises
from 1600 to 1771 and the leaf price falls from 1.900 to 1.698. The shock
propagates upstream perfectly well — it just arrives as slack.

What the prediction was really describing was the **cash** channel: producers
paying for inputs, so that a low output price squeezes a margin against a real
input bill. That channel is deliberately not in this slice
(`docs/08-accounted-input-design.md` §8), because adding it would move the price
floor and the silver ledger at the same time as the material constraint and make
the deltas uninterpretable. The prediction's mechanism was correct; it was
attached to the wrong session.

## Why 2: capacity entry is still free, exactly as predicted

`docs/07` said plainly that its producer-loss predictions assume replacement
capacity consumes a construction fund, and that "if the first implementation
omits the last two assumptions, the producer-loss predictions in particular
should be expected to miss."

It did omit them — capital goods are the next session's scope — and they missed.
This one is a correctly-flagged known limitation rather than a surprise.

## Why 3: the buffers are twenty days deep and the shocks are smaller than that

This is the substantive discovery, and it was not anticipated at all.

Every stage is seeded at twenty days of cover, which is what "begins from a
reasonably stocked, internally consistent equilibrium" means in
`docs/07`'s own assumptions. Measuring the tightest moment each scenario ever
reaches:

| scenario | leaves, min days of cover | chemfuel, min days | max unmet input/day |
|---|---:|---:|---:|
| equilibrium | 20.00 | 20.00 | 0 |
| glut | 20.00 | 20.00 | 0 |
| arbitrage | 20.00 | 20.00 | 0 |
| producer loss | **11.68** | 20.06 | 0 |
| input shortage | **0.30** | 15.38 | **56.0** |

The four scenarios behind the frozen metrics never get within eleven days of
binding. The constraint is present, correct, and irrelevant to them. Only a
shock aimed directly at an input stage exhausts a buffer.

So the honest reading of the null result is not "the material constraint does
nothing." It is: **a twenty-day buffer absorbs every shock in the existing
benchmark set, because none of those shocks attacks an input.**

---

## What the model gained that the metrics cannot see

The frozen metric set watches yayo and only yayo. The new machinery operates
almost entirely upstream of it, so the instrument is blind to the change by
construction.

Underneath an unchanged producer-loss headline, this is now happening:

| producer-loss shock | before | after |
|---|---|---|
| yayo peak price | 38.63 | 38.63 |
| psychoid leaf price | *no such thing* | falls 1.900 → **0.489** (−74%) |
| psychoid leaf stock | *no such thing* | drains 1600 → 926, rebuilds to 1793 |
| chemfuel price | *no such thing* | falls 2.300 → **1.086** (−53%) |

Destroying 60% of the drug labs crashes the psychoid farm's price by three
quarters and the chemfuel refinery's by half. In the free-production model that
was not a muted effect — it was not representable at all.

The glut leaves a second new behavior: **permanent upstream hysteresis.** Yayo
returns exactly to 21.000 and 200 units, but leaves settle at 1771 units and
1.698 silver and stay there, and chemfuel at 124.3 and 2.216. The stock built up
while the lab was curtailed is never worked off, because once the lab returns to
full rate the farm's output exactly matches its draw again. A one-off glut in a
finished good permanently depresses the price of its inputs. Nothing in the
yayo-only metric set registers this.

### The instrumentation gap

`economy_lab/behavior_baseline.json` cannot detect a regression in any of the
mechanisms added this session. Every one of its thirteen metrics would stay
green if input consumption were deleted tomorrow.

Extending the observation infrastructure is explicitly out of scope this
session, so this is recorded as a recommendation rather than acted on: **the
next session should add upstream metrics to the frozen baseline** — minimum days
of cover per input, peak unmet input demand, and the upstream price trough —
before the model grows further. Until then the 23 unit tests, not the baseline
reporter, are what protects this work.

---

## The new scenario, which does bind

`python -m economy_lab input-shortage` destroys 70% of Dust Basin's psychoid
fields — a shock the previous model literally could not express, since with no
material inputs the drug lab did not care whether the fields existed.

| day | yayo price | yayo stock | leaf price | leaf stock | leaf capacity | unmet leaves/day |
|---:|---:|---:|---:|---:|---:|---:|
| 60 | 21.000 | 200.0 | 1.900 | 1600 | 80.0 | 0 |
| 61 | 21.000 | 200.0 | 1.916 | 1544 | 24.0 | 0 |
| 70 | 21.000 | 200.0 | 2.451 | 1040 | 24.0 | 0 |
| 85 | 21.000 | 200.0 | 4.222 | 200 | 24.0 | 0 |
| 90 | 21.439 | 187.1 | 6.588 | 24 | 24.0 | 56.0 |
| 110 | 33.423 | 101.4 | 9.480 | 24 | 24.0 | 56.0 |
| 130 | 36.736 | 98.1 | 9.500 | 49 | 49.2 | 30.8 |
| 160 | 26.609 | 162.0 | 6.663 | 71 | 70.7 | 9.3 |
| 209 | 21.489 | 196.3 | 5.367 | 78 | 78.4 | 1.6 |

Four things in that table are the point of the session:

1. **A thirty-day silent phase.** The leaf stock drains for a month at 56/day
   while yayo's price does not move at all. The buffer, not the shock, sets when
   the shortage becomes visible downstream.
2. **The input price moves first and moves further.** Leaves go up 5×; yayo goes
   up 1.75×. Scarcity is registered where it happens.
3. **Output degrades, it does not cliff.** Once leaves are exhausted the lab
   runs on that day's 24 leaves — 3 yayo a day against a capacity of 10. This is
   the proportional rationing rule doing exactly what it was chosen for; the
   `all_or_nothing` alternative shuts the lab entirely and is available as a
   parameter.
4. **The fork behaves.** Chemfuel's derived demand nearly halves when the fields
   are wrecked, its price falls to 0.99, its own refinery curtails against that
   price, and the stock stabilises instead of running away. Two consumers
   competing for one input was the case a linear chain could not have tested.

All three material ledgers close to 5×10⁻¹² across this run.

---

## Watch-items from the brief

**Arbitrage volume was flagged as the likeliest thing to destabilize.** It did
not move — still exactly 13 units. The reason is specific rather than lucky:
freight is 3.85 silver after the risk markup, and the widest inter-regional
spread ever reached on leaves is about 0.2 silver and on chemfuel about 0.08.
Neither intermediate good is ever worth shipping, so the route stays effectively
single-commodity and the new widest-spread-first allocation rule never has to
break a tie. This will change the moment freight falls or an intermediate good
gets a real regional price gap, and the allocation rule is in place for when it
does.

**The recovery-day quantization was flagged as a possible false zero.** It is
not the explanation here. `glut.local_trough_price` and
`producer_loss.local_peak_price` are continuous, reported to six decimal places,
and identical to all six. The yayo trajectory is genuinely bit-identical, not
rounded into agreement.

---

## Verdict on the prediction

| prediction | outcome |
|---|---|
| glut shallower and shorter | **failed** — identical, and structurally could not have held without the cash channel |
| producer-loss higher and longer | **failed** — as `docs/07` itself warned, since capacity entry is still free |
| equilibrium near-stationary | **held** — exactly stationary, all three commodities |
| arbitrage flat to moderately lower | **held** at the top of the range, for a reason the prediction did not give |

The forecast's error was not in its numbers. It was in assuming that accounting
for inputs is by itself a cost floor. It is a *material* floor, and a material
floor only binds when material actually runs out. The cost floor the prediction
described needs producers to pay for what they consume, which is the next
session's work.
