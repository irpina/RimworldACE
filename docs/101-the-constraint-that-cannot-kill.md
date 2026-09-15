# A3: the constraint exists, binds, and cannot kill

**`docs/98`'s A3 finding is wrong. It reported that no rule in the
laboratory makes the wage bill a solvency constraint, and that firm death
is purely a matter of return. In fact `_produce` has curtailed output to
what the purse affords since `docs/55`, and `_outlay_per_run` includes the
wage. For five of the circuit's nine processes — chemfuel, meals, herbal
medicine, steel and wood, which buy no inputs at all — the purse
constraint *is* the wage bill, and the rule is Wright's F1 exactly.**

**Except for one thing, and it is the whole thing: F1 floors. Ours does
not. `u = max(|W_a| − ⌊m_a / ⟨w⟩⌋, 0)` means a firm holding less than one
average wage fires everybody and ceases trading. Our
`affordable = spendable ÷ outlay_per_run` is continuous, so a purse of any
positive size buys a positive number of runs, which make sales, which
refill the purse to sustain exactly those runs. The producer converges to
a fixed point and lives there forever.**

Measured: `cash_circuit`'s component producer drains from 11.938 to
**0.083** — 0.7% of its 11.90 target — then holds at 0.082951 with
0.00189832 runs a day, unchanged from day 800 to day 1199. Its
`liquidity_idle_days` never exceeds **0** across 1200 days, against a
`bankruptcy_idle_days` threshold of 30. It is a zombie: permanently
insolvent against its intended scale, permanently alive.

## 1. What is actually there

In `_produce`, on the `producer_cash` path, before the day's runs are
committed:

```
per_run    = self._outlay_per_run(p, region)          # inputs + wages
spendable  = p.cash - self._plant_matter_cost(p, region)
affordable = max(0.0, spendable) / per_run
if affordable < wanted:
    ledger.liquidity_curtailment[p.commodity] += wanted - affordable
    planned[id(p)] = affordable
if affordable <= EPSILON:
    p.liquidity_idle_days += 1
else:
    p.liquidity_idle_days = 0
```

and `_settle_purses` bankrupts a producer whose `liquidity_idle_days`
reaches `bankruptcy_idle_days` (30). So the shape is all there: shed
output down to what the purse affords, and retire one that can afford
nothing.

`_outlay_per_run` is `input_cost_per_run(prices) + direct_labor ×
wage_rate ÷ ticks_per_worker_day`. The wage is in it. How much of it the
wage is varies enormously by process — Dust Basin, `cash_circuit`:

| process | outlay/run | wage | inputs | wage share |
|---|---:|---:|---:|---:|
| chemfuel | 0.0437 | 0.0437 | 0.0000 | **1.0000** |
| steel | 0.0831 | 0.0831 | 0.0000 | **1.0000** |
| wood | 0.0393 | 0.0393 | 0.0000 | **1.0000** |
| meals | 0.5334 | 0.5334 | 0.0000 | **1.0000** |
| herbal_medicine | 0.6995 | 0.6995 | 0.0000 | **1.0000** |
| garments | 4.9615 | 2.8330 | 2.1286 | 0.5710 |
| psychoid_leaves | 0.1958 | 0.0808 | 0.1150 | 0.4127 |
| components | 37.9104 | 8.7437 | 29.1667 | 0.2306 |
| yayo | 16.2718 | 0.6121 | 15.6597 | 0.0376 |

For the five at 1.0000 the constraint is purely a wage constraint, which
is the only kind Wright can have — the paper is explicit that "*in this
formulation of the model there is no constant capital*". Our rule is
therefore *stronger* than F1 wherever a process buys inputs, and
*identical* to it wherever one does not.

## 2. Where it binds

| scenario | curtailment | bankruptcies | inactive |
|---|---|---:|---:|
| `equilibrium` | 0.000000 | 0 | 0 |
| `cash_circuit` | **1.451509** (`components`) | 0 | 0 |
| `gravitation` | 0.000000 | 0 | 0 |
| `complete_market` | 0.000000 | 0 | 0 |

Inert where the circuit is stationary — the same discipline `_bargain`
keeps at zero strength — and live in exactly the scenario `docs/56` built
to drain a purse.

## 3. Why it never kills

The component producer, stepping `cash_circuit` a day at a time:

| day | purse | runs | idle days |
|---:|---:|---:|---:|
| 0 | 11.938469 | 0.00189832 | 0 |
| 200 | 7.662565 | 0.00189832 | 0 |
| 400 | 3.386661 | 0.00189832 | 0 |
| 600 | 0.081840 | 0.00186715 | 0 |
| 800 | 0.082951 | 0.00189832 | 0 |
| 1199 | 0.082951 | 0.00189832 | 0 |

The purse falls for six hundred days and then **stops**, at a level that
finances exactly the output whose sales finance that level. Nothing in
the rule can push it below: curtailment is proportional, so halving the
purse halves the runs rather than stopping them, and the sales fall in
step. Zero is an asymptote, not a destination.

`liquidity_idle_days` only advances when `affordable <= EPSILON`, which
needs a purse of essentially exactly zero. A producer with a millionth of
a coin still affords a millionth of the runs, still sells, and resets the
counter. **The bankruptcy branch is unreachable for any producer that
sells anything at all** — which is the same class of defect as `docs/96`'s
false resume verdict, found the same way, and this time it was sitting
under a finding that said the rule did not exist.

## 4. The difference from F1, exactly

Wright's firms employ **whole workers**. `⌊m_a / ⟨w⟩⌋` is an integer, and
the gap between one worker and none is a cliff. A firm that cannot afford
a single average wage employs nobody, and by the paper's own definition an
actor with no employees and no employer is unemployed — the firm has
ceased to exist. Death is reachable because employment is discrete.

Our producers employ a continuous flow of labour-ticks. There is no
smallest employable worker, so there is no cliff, so there is no death.

That is the whole divergence, and it is one floor wide.

It is worth noticing that our model *already knows* about this. Regional
employment is quantized: `_settle_labor` floors worker-days onto an
`employment_quantum` grid, precisely so that a day's basket flow is exact.
The quantum exists at the region; it does not exist at the producer, and
the producer is where solvency is decided.

## 5. Corrections

- **`docs/98` A3 is withdrawn** as stated. "Neither is the wage bill" was
  wrong: the purse constraint is a wage constraint, and for five of nine
  processes it is nothing else. Prediction 3's *measurement* stands — zero
  deaths by wage bill — but its explanation was wrong. The correct
  explanation is §3: not that nothing tests solvency, but that what tests
  it cannot conclude.
- **`docs/100` §7 is withdrawn.** It proposed building this rule, with
  the flourish that it needs "no new state, since `producer.cash` already
  exists". It needs no new state because it already exists. Building it
  would have duplicated `_produce`'s own arithmetic.

## 6. The pattern, a fourth time

`docs/96`: a branch nothing could reach. `docs/98` prediction 4: a default
read for a scenario. `docs/99`: a rule measured with its channel off.
Now: a rule reported absent that was present all along.

`docs/99` §5 drew the rule "before reporting that a rule does not do
something, show the rule running." That was not enough, because it assumes
you have found the rule. The addition: **before reporting that a rule is
absent, search for it.** The A3 audit read `_exit` and `_bankrupt`,
reasoned about them correctly, and never grepped `_produce` for the word
`cash`. Four documents, four variants of the same failure — asserting the
negative from an incomplete reading.

## 7. What follows

The interesting question is no longer "should the wage bill bind" — it
does. It is **whether a producer should be able to die of it**, and there
are two candidate answers.

**(a) Quantize employment at the producer.** Give a producer a smallest
employable unit, as the region already has, and F1's cliff appears: a
purse that cannot afford one unit affords none, the idle counter starts,
and `_bankrupt` becomes reachable. Small, local, no new concepts, and it
uses machinery the model already has. It would make `cash_circuit`'s
zombie die, which is a *change to a committed scenario's outcome* and so
must be gated off by default like every other market rule.

**(b) Attack the reason the purse never empties: A7.** In Wright a firm's
revenue is a draw from a common pool and can simply be nothing; in ours a
producer sells its share of a deterministic demand. `docs/98` marked A7
"partially holds" and moved on. §3 suggests A7 is the *load-bearing*
divergence and A3's inertness is downstream of it — a producer whose
revenue cannot fail has a purse that cannot empty, whatever the solvency
rule says.

(b) is the deeper finding and the harder build, and it collides with this
project's central method: revenue as a draw means a pseudo-random stream,
and `docs/53`'s contract requires the C# port to reproduce the laboratory
to the bit under Mono. Two PRNGs agreeing bit-for-bit across CPython and
Mono is a real constraint, not an incidental one, and it should be decided
deliberately rather than discovered halfway through an implementation.

So: **(a) is the next build, and (b) is the next design question, and it
needs a decision before anything is written.**

## 8. What was changed

Nothing in the model. Six tests in `tests/test_wage_solvency.py` pin the
constraint's existence, that it is exactly the wage bill for a pure-labour
process, that it is inert at equilibrium and binds in `cash_circuit`, and
that the death path is unreachable. `docs/98` and `docs/100` carry
correction banners. `python -m economy_lab.baseline` reports 322 metrics
with no nonzero delta.
