# Sales that follow production: design

Written before implementation. `docs/103` built F1's floor and found it
necessary but not sufficient: the drained producer idles on a fifth of
all days, and its longest *consecutive* idle run is one, because **idling
repairs the purse**. This is the weak form of the fix — the one that
needs no randomness — chosen ahead of A7 proper on the grounds that it
isolates the coupling question from the determinism question.

**The claim: an idle producer is paid because of one fallback, and
removing it makes revenue conditional on having produced.**

## 1. The leak, exactly

`_supply_shares` decides who is paid when a commodity is drawn from the
regional pool:

```
weights = [p.last_runs × outputs[name] for p in producers]
total   = sum(weights)
if total <= EPSILON:
    weights = [p.capacity_per_day for p in producers]   # ← the fallback
    total   = sum(weights)
```

Payment is apportioned by **yesterday's realized output** — the model
already has a one-day lag, and a producer is paid today for what it made
yesterday. That part is right and stays.

The fallback is the leak. When *every* producer of a commodity ran
nothing, the apportionment switches to **capacity**, and a producer that
made nothing is paid exactly as though it had. Measured on
`cash_circuit`'s component sector, which is the sole component producer
in Dust Basin: its share reads `1.0` on every day of the oscillation,
whether it ran or not.

Without the fallback, `_pay_sellers` finds no sellers and credits the
regional fund instead (`region.cash += amount`), which conserves silver
and is the defensible reading: the goods came out of the pool, and a
producer that did not make them has no claim on them.

## 2. The rule

A flag, `sales_follow_production`, defaulting to `False`. When set, the
capacity fallback in `_supply_shares` is skipped: a commodity nobody
produced yesterday has no sellers today, and the fund is paid.

One rule, one branch, no new state, no randomness. It cannot perturb any
run in which some producer of every commodity ran every day — which is
the basis of prediction 2.

## 3. Is it defensible economics?

Honestly: **partly.** A real firm can sell from inventory while idle, and
this rule says it cannot. The defence is that in this model a producer
does not hold inventory — output goes to the regional pool and the
producer is paid out of that pool by share (`procurement`, which does
give producers their own stock, is off in every scenario this touches).
So "paid by capacity while producing nothing" is not a firm selling its
inventory; it is a firm being paid for someone else's.

That is a narrow defence and it should be stated as narrow. The rule is
gated off, and if it turns out to matter it deserves its own argument
rather than inheriting this one.

## 4. Numbered predictions

Measured in `docs/105`.

1. **Inert by default.** 322 metrics, no nonzero delta.
2. **Inert where nobody idles.** With the flag on, `equilibrium`,
   `gravitation` and `complete_market` are bit-identical to the flag off.
   Every commodity has a producer that ran, every day, so the fallback is
   never reached.
3. **The flag alone does nothing to `cash_circuit`.** With
   `sales_follow_production=True` and `producer_employment_quantum=0.0`,
   `cash_circuit` is bit-identical to today. `docs/101` measured that
   without the floor no producer is ever idle, so the fallback is never
   reached there either. **The two rules are only jointly effective**,
   and this is the prediction that says so.
4. **Together they break the oscillation.** With the flag on and the
   quantum at 1e-3, the component producer's peak *consecutive* idle run
   exceeds 1 — the number `docs/103` found pinned.
5. **And reach the death.** That run reaches 30 and `_bankrupt` fires: at
   least one entry in `ledger.bankruptcies`, and it is the component
   producer.
6. **Money is conserved.** `cash_balance()` within 1e-6.
7. **The identity holds.** The bare wage share stays
   `value_of_labor_power ÷ ticks_per_worker_day`, per `docs/99`.
8. **The macro effect is small but not nil.** `docs/102` predicted
   killing the zombie would change nothing, and never got to test it.
   Here it should: the component producer was curtailed to 0.12% of
   regional employment, so I expect regional employment to move by **less
   than 1%** — but capacity replacement now has no supplier, so something
   downstream should degrade over the remaining run. I expect a *visible*
   second-order effect and cannot predict its size.

Prediction 3 is the one that keeps this honest: if the flag alone changes
`cash_circuit`, my account of the mechanism in §1 is wrong. Predictions 4
and 5 are the point. Prediction 8 is what `docs/103` could not reach.

## 5. If it does not pan out

The pivot is A7 proper: couple revenue to employment as Wright's M1 does,
which means a draw from a common pool and a pseudo-random stream
reproducible bit-for-bit across CPython and Mono under `docs/53`'s
contract — a hand-rolled integer PRNG, transliterated like every other
ported rule. That is a design document of its own and should not be
started inside this one.

The trigger for pivoting is prediction 5: if the consecutive idle run
grows but still does not reach 30, or if it reaches 30 and the resulting
economy is degenerate in the way `docs/103` §2's large quanta were, then
removing the fallback is not enough and the coupling has to be built
properly rather than patched.
