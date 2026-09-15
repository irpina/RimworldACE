# Quantizing employment at the producer: design

Written before implementation. `docs/101` found that our purse-solvency
constraint is Wright's F1 in every respect but one: **F1 floors and ours
does not**, so a drained producer converges to a fixed point instead of
reaching zero, and the bankruptcy branch is unreachable for any producer
that sells anything. This builds the floor.

**The headline claim to be tested: a smallest employable unit is all that
separates a zombie from a death. Give a producer one and `cash_circuit`'s
component sector — purse at 0.7% of target, alive for 1200 days — goes
bankrupt.**

**And the headline doubt: it will not matter. The producer dies at its
fixed point, where it already employs 0.00040 worker-days out of the
region's 0.318 — 0.12% of regional employment. Wright's firms die while
still large, because his revenue is a draw that can fail. Ours would die
only after shrinking to nothing first. If prediction 6 holds, this rule
makes death *reachable* without making it *consequential*, and A7 is the
real divergence.**

## 1. The rule

In `_produce`, on the `producer_cash` path, after the existing
affordability computation and before it is compared with what the
producer wanted:

```
affordable = max(0.0, spendable) / per_run
if producer_employment_quantum > 0:
    worker_days = affordable × direct_labor ÷ ticks_per_worker_day
    worker_days = floor(worker_days ÷ quantum) × quantum
    affordable  = worker_days × ticks_per_worker_day ÷ direct_labor
```

Everything downstream is untouched: `affordable < wanted` still curtails
and books `liquidity_curtailment`, `affordable <= EPSILON` still advances
`liquidity_idle_days`, and thirty of those still reach `_bankrupt`. The
change is one floor, in one place, and it makes an existing branch
reachable rather than adding a new one.

Two guards:

- **A process with no direct labour is skipped.** Quantizing zero
  worker-days would floor every such producer to nothing, which would be
  a rule about labour destroying producers that employ none.
- **The quantum defaults to `0.0`, meaning off**, as every market rule in
  this project does (`posted_prices`, `procurement`, `entry_on_margin`,
  `exit_on_return`). It changes a committed scenario's outcome, so it
  cannot be on by default without moving the baseline.

## 2. Why the quantum cannot be chosen from first principles here

Wright's unit is one worker, because his actors are people. Ours is a
flow of labour-ticks, and the laboratory's regions are **smaller than one
person**:

| | worker-days per day |
|---|---:|
| the whole of Dust Basin | **0.318189** |
| `psychoid_leaves` | 0.154000 |
| `yayo` | 0.145833 |
| `meals` | 0.008087 |
| `chemfuel` | 0.006294 |
| `garments` | 0.002685 |
| `herbal_medicine` | 0.000663 |
| **`components`** | **0.000395** |
| `steel` | 0.000145 |
| `wood` | 0.000014 |

A quantum of one worker-day is three times the region's entire
employment. The region's existing `employment_quantum` is `2^-20`
(9.5e-07), which exists for bit-exact basket flows and is four orders of
magnitude too fine to be a cliff for anybody.

So there is no defensible single value, and picking one that kills
`components` and spares the rest would be fitting the parameter to the
answer — the error `docs/100` §6 was written about. **The quantum is
therefore swept, and the result is a curve rather than a number.**

This is itself a finding worth recording: the laboratory is calibrated at
a scale where "one worker" is not a meaningful unit. The gameplay layer
will not have that problem — a colony has three to fifteen pawns — so the
quantum becomes natural exactly where `docs/50` needs it.

## 3. Numbered predictions

Measured in `docs/103`.

1. **Inert by default.** `python -m economy_lab.baseline` reports 322
   metrics with no nonzero delta. The quantum is `0.0` and the branch
   returns before touching anything.
2. **Inert where the purse does not bind.** With the rule **on**, at any
   quantum, `equilibrium`, `gravitation` and `complete_market` are
   **bit-identical** to the rule off. Their `liquidity_curtailment` is
   0.000000, so no producer is ever short and the floor is never applied
   to a binding quantity. If this fails, the rule is reaching further
   than intended and the implementation is wrong.
3. **A window exists** in which `cash_circuit`'s `components` producer
   goes bankrupt and no other producer does. I expect its lower edge near
   components' affordable worker-days at the fixed point (~4.6e-04) and
   its upper edge set by whichever healthy producer has the smallest
   *affordable* — not smallest actual — employment.
4. **Bankruptcy is dated, not immediate.** In that window,
   `ledger.bankruptcies` is non-empty and its first entry falls **after
   day 550**, because the purse only reaches its fixed point around day
   600 and thirty idle days must then elapse. A bankruptcy on day 1 would
   mean the floor is biting a solvent producer.
5. **Money is still conserved.** `cash_balance()` stays within 1e-6 after
   a bankruptcy; `_retire` returns the purse to the regional fund.
6. **The macro effect is negligible.** The region's employment rate
   changes by **less than 1% of its level** when `components` dies,
   because the producer was already curtailed to 0.12% of regional
   employment. *This is the prediction I most expect to hold and least
   want to.*
7. **Something downstream notices.** `components` feeds Department I's
   capital replacement (`cash_circuit` sets `capital_goods=True`). With
   the only component producer gone, either unmet capital demand appears,
   or capacity begins to decay, or the scenario raises. I do not know
   which, and will report what happens rather than predicting it.
8. **The bare wage share does not move.** Per `docs/99` it is
   `value_of_labor_power ÷ ticks_per_worker_day`, an identity no quantity
   rule can touch — and a producer dying is a quantity change. If this
   fails, `docs/99`'s identity is wrong.

Predictions 6 and 7 are the ones carrying information. 1–5 are the rule
working as specified; 6 says whether the rule was worth building; 7 is
the one I cannot call.

## 4. What this is not

It is not worker mobility (`docs/50` §5, A5). The labour pool stays a
fixed parameter; what changes is only whether a producer can stop
employing out of it.

It is not A7. A producer's revenue remains a deterministic share of a
deterministic demand. `docs/101` §7 argues that is why purses do not
empty in the first place, and prediction 6 is the test of whether fixing
the floor without fixing the draw accomplishes anything.
