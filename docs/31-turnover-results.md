# Turnover: results

Recorded after implementing the design in `docs/30-turnover-design.md`.

## Headline

The project was printing two numbers as rates of profit and neither was one.
Both are fixed, and the fix was mostly dividing by a figure the model already
held.

- All 138 tests pass (124 prior + 14). **No behavioral metric moved**; 149
  metrics, with five renames that carry their values across unchanged.
- The price system's rate is **24.62 → 1.1726 per day**, and the old number
  survives as the **gross markup** — the factor by which price exceeds cost.
- **Not one relative price moved**, which is the point: uniform turnover is a
  scalar, so it rescales the rate and redistributes nothing.
- The value ledger gains a real rate of profit: **0.0305 per day** on capital
  advanced, against the **1.7326** flow ratio it has been printing since
  `docs/23`.
- Realized turnover is **56.8 days**, not the 21 the price system assumes,
  because yayo is nobody's input and its finished stock appears in no cost
  flow.
- `perishable_meals` — the one differential turnover RimWorld justifies —
  lifts the rate to **2.08** and widens every deviation, yayo from 54 meals
  to **476**.

## 1. What was wrong

Two errors of the same shape. **The model charged profit against a day's flow
while holding twenty days of stock.**

`docs/26` wrote `p = (1 + r)Mp`, which advances capital for exactly one
production period. `docs/27` and `docs/29` both flagged the consequence —
"`r` is a rate per production period and the period is a day" — without
fixing it, so the headline numbers 38.34 and 24.62 were daily rates nobody
could argue about.

Meanwhile `value_rate_of_profit` divides surplus by `c + v` where both are
*cumulative flows*. That is profit per unit of capital **consumed**, which is
a real quantity and is not a rate of profit. It has been reported under that
heading since `docs/23`.

## 2. The price system: a rate, and the old number under an honest name

```
p_i  =  M_i·p  +  r · τ_i · (M_i·p)  =  (1 + r τ_i)(M_i·p)
τ_i  =  production period + the commodity's own inventory life  =  21 days
```

| quantity | value |
|---|---:|
| gross markup (price over cost) | **24.623882** |
| turnover, every commodity | 21 days |
| **profit rate, per period** | **1.1725658** |

`r × 21 = 24.6239` to nine places, which is test 2 of the design.

**Not one relative price moved.** With uniform turnover `1 + rτ` is a single
constant, `p = kMp` is the pre-turnover system exactly, and the diagonal
factors out. The test asserts this structurally rather than against
remembered digits: every sector's price over its own cost is the same
constant, to nine places, which is what "the diagonal factors out" means.

So **turnover rescales the profit rate and redistributes nothing.** Only
*differential* turnover moves a relative price — §5.

### An implementation note that belongs in the record

`docs/30` §2.1 specified bisection on the Perron root, and §3.2 predicted the
invariance without saying how it would be preserved numerically. It was not:
bisection converges to within a tolerance, and the last bits leaked into the
prices, breaking the `docs/29` test that a non-basic technique change leaves
the basic prices *bit-identical*.

The fix is to solve the uniform case in closed form — `r = (k − 1)/τ`, which
is §3.2's own algebra — and fall back to bisection only when turnover
actually differs. That is the right answer rather than a patch, but it was
prompted by a failing test rather than designed in, and the design document
was the poorer for treating a numerical property as a mathematical one.

## 3. The ledger: capital advanced, measured rather than assumed

The model holds the stock, so the advance is read off it.

| component | ticks | share |
|---|---:|---:|
| commodity capital in stock | 464,396.95 | **96.34%** |
| installed plant | 17,072.72 | 3.54% |
| wage advance (one period) | 550.07 | **0.11%** |
| goods in transit | 0.00 | 0.00% |
| **total** | **482,019.75** | |

The wage advance — what the pre-turnover system effectively charged profit
against for a pure-labor good like meals — is **one part in nine hundred** of
the capital actually tied up.

| rate | value | what it divides by |
|---|---:|---|
| flow ratio `s/(c+v)` | 1.7326 | capital **consumed** per period |
| **rate of profit on advances** | **0.030479/day** | capital **advanced** |

A factor of 56.8, which is the realized turnover time — the number the model
should have been dividing by.

Both are kept and both are reported. `value_rate_of_profit` is referenced by
four earlier documents and remains a correct measure of profit per unit of
throughput; it simply is not the rate of profit, and its docstring now says
which one is.

## 4. Realized turnover is 56.8 days, not 21

The price system assumes 21 — one period to make it, twenty to sell it. The
circuit actually ties capital up for nearly three times that, and the reason
is structural rather than a calibration slip.

**Yayo is nobody's input.** Its 200 units per region are 63.4% of all
commodity capital in the model, and they appear in no cost flow anywhere,
because `c` only counts what production consumes. Psychoid leaves are another
32.7%; the two together are over 95%.

Take yayo's stock out of the advance and the ratio lands at 22.1 days —
within a day and a half of the 21 the price system assumes. So the gap is
entirely the finished-goods inventory of the final product, and the test
asserts it by that decomposition rather than by the number.

This is a real distinction between two accounting frames rather than an error
in either. A cost flow measures what is used up; an advance measures what is
laid out. A final good waiting for a customer is laid out and never used up.

## 5. Differential turnover, and the only kind the game justifies

RimWorld's simple meals start to rot after four days. The market cannot hold
twenty days of them, and that is a fact about the game rather than a knob.

| commodity | uniform τ | perishable meals |
|---|---:|---:|
| **profit rate, per day** | 1.1726 | **2.0792** |
| gross markup | 24.624 | 43.647 |
| meals | 1 | 1 |
| chemfuel | 0.08197 | **0.32125** |
| herbal medicine | 1.31148 | **5.13994** |
| garments | 7.2558 | **34.0989** |
| psychoid leaves | 0.25649 | **1.31106** |
| yayo | 54.146 | **475.823** |

Two mechanisms compound. A wage good that turns over in five days instead of
twenty-one **releases capital**, and the same surplus over a smaller advance
is a higher rate. Then everything that still turns over in twenty-one days
carries twenty-one periods of that higher rate, while meals carry five.

So **differential turnover widens the deviations rather than narrowing
them**, in this configuration. That is a finding about the configuration and
not a defect: a cheap, fast-rotting wage good against slow-moving
manufactured drugs is a real structural asymmetry, and the price system is
right to price it.

Behaviorally the scenario is a smaller change than it sounds: the meal buffer
falls from 13.60 to 2.72 units and the circuit is **still exactly stationary**
— zero price range, six commodities, both regions, four years.

## 6. The three rates, and why two of them differ by 38×

The project now reports three numbers that are easy to confuse.

| | value | what it is |
|---|---:|---|
| gross markup | 24.62 | price over cost, per turnover, in a hypothetical uniform-rate price system |
| price system `r` | 1.173/day | the uniform rate that system would pay, **fixed by the basic sector alone** |
| ledger rate on advances | 0.0305/day | the rate this economy **actually** realizes at RimWorld's authored prices, over all its capital |

The last two differ by a factor of 38 and both are correct. `r` is a property
of the *basic* subsystem — meals, garments, medicine and chemfuel — whose
advance is small, and Sraffa's theorem says non-basics cannot touch it. The
ledger figure averages the whole economy, in which 96% of the advance is the
yayo circuit's stock and yayo is non-basic.

This is the same divergence `docs/27` reported between `r = 38.34` and the
value rate of profit 1.77, restated with both sides now measured on
comparable bases. It is not going away and it should not: it is the
transformation problem's aggregate failure, showing up as a gap between what
a uniform-rate system would require and what a real one distributes.

## 7. Prediction scorecard

Every prediction in `docs/30` §7 held.

| prediction | predicted | measured |
|---|---|---|
| 7.1 profit rate per period | 1.17257 | **1.1725658** |
| 7.2 relative prices | unchanged | unchanged |
| 7.3 capital advanced | 481,742 | 482,020 |
| 7.3 commodity / fixed / wage shares | 96.4 / 3.5 / 0.1% | 96.34 / 3.54 / 0.11% |
| 7.3 yayo share of stock | 63% | 63.39% |
| 7.4 rate on advances | 0.0305/day | 0.030479 |
| 7.5 realized turnover | 56.8 days | 56.845 |
| 7.7 perishable profit rate | 2.08 | 2.0792 |
| 7.7 perishable yayo / meals | 475.9 | 475.823 |
| 7.8 behavioral movement | none | none |

**7.1 was the one that mattered**, because it was a correction rather than a
forecast. `docs/29` §10 left an envelope of 0.28, reasoning that
`1 + r ≈ 25.62 / 20`. That compounds `r` over twenty periods; the classical
formulation charges it once on the advance, so the correction is additive and
the answer is `24.62 / 21 = 1.17`. A factor of four, and it is the difference
between two economic claims rather than an arithmetic slip. `docs/30` §7.1
said so before the code existed.

**The one line that came out wrong is inside 7.3.** The fixed-capital
component was predicted at 16,795 ticks and measured 17,073, 1.65% higher.
The prediction computed it as depreciation flow × service life; the
implementation measures installed capacity × capital per unit of capacity.
Those agree only when every machine runs flat out, and some plant is idle. The
implementation is right — the machines exist whether or not they ran today —
and the prediction was computing a different quantity, which is worth
recording because it is exactly the flow-versus-stock confusion the whole
session is about, committed once more in the design document itself.

**7.6 disarmed a coincidence and it duly appeared.** `0.030479 × 60 = 1.829`
per RimWorld year against a flow ratio of 1.7326 — agreement to 5.5%. It
means nothing: the realized turnover (56.8 days) is close to the length of a
RimWorld year (60 days), so dividing by one and multiplying by the other
nearly cancels. Predicting the coincidence in advance is the only reliable way
to stop it being read as confirmation.

## 8. A third seeding defect, from the same family

`docs/29` reported two guards that broke the first time a mechanism saw more
than one of something. Here is the third: `_region` seeded every stock from
`parameters.target_inventory_days`, the global default, rather than from the
commodity's own inventory life. Identical while they were equal; wrong the
moment meals started rotting.

It showed up as `perishable_meals` failing to be exactly stationary by
7 × 10⁻¹¹, which is the kind of residual that would have been easy to wave
through as floating-point noise. It was not noise: the run was seeded with
twenty days of meals and spent 240 days converging to four.

The exact-stationarity invariant earned its keep. A tolerance-based check
would have passed.

## 9. Where this leaves the next step

Turnover is done and it did what it was supposed to: the two rates the
project reports are now rates. Neither is *comfortable* — 1.17 per day for
the basic sector's uniform rate, 0.0305 per day realized — but they are
quantities that can be argued about, which the previous ones were not.

What is left in the economics, unchanged in order:

1. **A capital-goods sector (Department I).** Building capacity still spends
   silver without consuming material, which is the last place something
   appears from nothing. It is also what would let fixed capital into the
   price system — now more visible than before, since the plant is 3.5% of
   the advance where its depreciation was 0.05% of cost.
2. **Capacity depreciation and exit**, so competition is for survival and not
   only for orders.
3. **Recreation in the basket**, deferred in `docs/28` §2.2 because the
   obvious candidate is yayo and it would create a wage-price loop through
   the commodity every scenario is measured on. Worth doing alone.

And `HANDOFF.md`'s standing recommendation now comes due: **the scale test
should jump the queue.** `docs/29` said "after turnover would be a defensible
place to stop", and this is that place. The economics has three closing
ledgers, a price system with an interpretable profit rate, and six
commodities — and nobody has checked whether any of it survives 654 defs and
a hundred settlements at an acceptable tick cost.

## Reference decision

Two commits. The first implements turnover, re-points every test that read
the old quantity, and fixes the seeding defect; 124 tests to 138. The second
freezes fifteen new observations and five renames, with no behavioral metric
moving; 134 metrics to 149.
