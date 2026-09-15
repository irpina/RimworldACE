# Making the battery askable: design

Written before anything is built or run. Measured in `docs/127`.

`docs/125` §4 ended with three follow-ups. This takes the first two —
a money wage share, and a scenario in which most firms can live — and
starts by correcting `docs/125`'s own diagnosis of why they cannot.

## 1. The diagnosis, corrected

`docs/125` §3 said the economy collapses under `producer_cash` because
`synthetic_economy` *"spreads daily final demand of 1.0 over hundreds of
commodities so most producers are sub-viable under a hard budget
constraint"*. The budget was the wrong suspect. Measured today on the
`docs/124` configuration, **before a single day runs**, from each
producer's capacity and its process's direct labour:

| full-capacity employment | producers (of 400) |
|---|---|
| ≥ 0.1 workers | 150 |
| ≥ 1 worker | 74 |
| ≥ 5 workers | 16 |
| median | **0.019 workers** |

The one-worker quantum floors 326 of the 400 producers to zero on day
one; thirty idle days later `_settle_purses` bankrupts them. The ~14
survivors are the ≥5-worker firms. **That is why a 1000× endowment
range changed nothing — the constraint is labour scale, not silver.**
Wright's world is ~1000 actors in ~100–200 firms, so his *smallest*
firm is one person and his median a few; ours is 400 firms whose median
needs a fiftieth of a person.

The fix is therefore a scenario parameter, not a model change:
`daily_demand`, which the generator pulls every upstream requirement
from. At ×200 the median producer needs ~3.7 whole workers.

## 2. Which wage share

Wright's wage share is wages paid over firm revenue, and his firms buy
no inputs, so his revenue *is* value added. Our producers buy inputs and
plant matter from each other. The like-for-like quantity is therefore

    money wage share  =  wages paid ÷ (sales receipts − producer purchases)

with the gross ratio wages ÷ receipts reported beside it as the wrong
number one would get by not thinking about it. Neither is booked today:
`wages_paid` is, receipts and purchases are not. Two observational
ledger dicts, keyed by region, booked where silver already changes hands
(`_pay_sellers`, `_pay_for_draws`). The default model never reaches
either call — both live inside `producer_cash` — so `baseline` must
still show 322 metrics at zero delta.

**And the prediction that matters, made by reading the scenario rather
than assuming the ontology.** `synthetic_economy` sets
`basket_fraction = 0.02`: the subsistence basket costs two per cent of a
working day, and the wage rate *is* the basket's price. So the money
wage bill is a few per cent of what the labour produces, whatever the
prices do. The money share will be as small as the value share was —
**not** because our lab lacks something Wright's has, but because in
our lab the wage share is an *authored* quantity and in his it is an
*outcome* of the rules. That is the finding this document is designed to
pin down, and `§4` tests it directly by turning the parameter.

## 3. What is built

- `model.py`: `Ledger.sales_receipts` and `Ledger.producer_purchases`,
  both `Dict[str, float]` by region, both observational.
- `wright_battery.py`: `DEMAND` scale applied to `daily_demand` and to
  every silver endowment (money is nominal; flows scale with demand);
  `build_ours(seed, *, demand, basket_fraction, quantum)` so the tests
  in `§4` are the same function with a knob turned; `money_wage_shares`
  in the record and `money_wage_share` in `facts()`. For the SA control
  the record's money share *is* its existing wage share, so the shared
  instrument compares like with like.
- Tests for the two ledger dicts (the silver identity still closes;
  receipts − purchases − wages is what the purses and fund gained) and
  for the battery's new knobs.

## 4. Numbered predictions

All two-sided, per `docs/120` §1.

1. **The rescale rescues the population.** At `DEMAND = 200`, one seed,
   180-day run, `producer_cash` and quantum on: employing producers at
   the end of the run in **[300, 400]** (was 14), bankruptcies in
   **[0, 40]** (was 499).
2. **It was the quantum.** Same configuration with
   `producer_employment_quantum = 0`: the employing-producer count
   differs from prediction 1's by **fewer than 10%**. If instead the
   quantum still removes a large share of firms at ×200, §1's diagnosis
   is incomplete and the budget was a co-suspect after all.
3. **The money wage share is small and authored.** At `DEMAND = 200`
   and the shipped `basket_fraction = 0.02`, wages ÷ value added lands
   in **[0.01, 0.10]** — Wright's 0.55 is not approached — and the
   gross ratio wages ÷ receipts is smaller still.
4. **Turning the parameter moves it, roughly one-for-one.** At
   `basket_fraction = 0.5`, wages ÷ value added lands in **[0.30, 0.80]**.
   If it does, Wright's 0.55 is *reachable* by our lab, but as an input,
   which is the honest statement of what "the wage share transfers"
   would mean here. If the run fails loudly on payroll at this basket,
   that is reported as such and the band is not scored.
5. **Firm growth is still unaskable.** Our producers meet authored
   demand rather than win a lottery, so month-to-month employment barely
   moves: at `DEMAND = 200` the standard deviation of log employment
   growth lands in **[0, 0.05]** and the growth-kurtosis row stays
   unscored. Rescuing the population does not create firm dynamics;
   that is `docs/125` §4's item 2 proper (several firms per commodity,
   entry and exit) and is *not* attempted here.
6. **Nothing default moves.** `python -m economy_lab.baseline` shows all
   322 metrics at zero delta and the existing suite passes.

Prediction 4 is the substance: it is the difference between "our lab
cannot produce Wright's wage share" and "our lab produces whatever wage
share it is told to", and only the second is true if 3 and 4 both hold.
