# The law of value, first experiment: results

Scores `docs/147`'s twelve predictions. **Four pass and seven fail.**
One of the failures is a whole arm, the capitalist one, which collapsed
on 19 of 20 seeds, so its predictions 10 and 11 are void.

The failures have two causes, both in the mechanism and both found by
diagnosis after the run. Neither is in the claim being tested:

- **An empty sector could never be re-entered.** That is what killed
  the capitalist arm.
- **Input buyers held no buffer.** Producers that use inputs stood idle
  for a quarter to three quarters of each day. Their incomes still
  equalised, so their prices sat above value by the idle time.

Read with that, the result is not a refutation. Prices settle on the
labour **actually spent** per unit, idle time included, much more
closely than on the labour the technique needs. That reading was found
after the fact. `docs/149` states it in advance and fixes both defects.

The battery is `economy_lab/law_of_value147_results.json`, made with
`python3.12 -m economy_lab.law_of_value out.json 20`: twenty seeds of
each arm, 6,000 days, scored over the last 1,000.

## 1. Scores

| # | prediction | measured (median; range) | verdict |
|---|---|---|---|
| 1 | money conserved, < 1e-9 | 1.9e-13 at worst | pass |
| 2 | bit-identical reruns | the tests, and a full rerun of all 60 runs | pass |
| 3 | SC `Δ(v)` in [0.002, 0.10], no seed above 0.20 | **0.332** (0.221–22.3); all 20 above 0.20 | **fail** |
| 4 | SC `ρ(v) ≥ 0.98` | **0.926** (−0.168–0.981) | **fail** |
| 5 | `Δ(v°) ≥ 3 Δ(v)`; `ρ(v°) < ρ(v)` on every seed | ratio **1.99**; 19 of 20 | **fail** on both halves |
| 6 | half of day-0 dispersion gone by day [100, 2,000] | 13 seeds at 110–1,100; **7 never** | **fail** |
| 7 | income CV across sectors ≤ 0.15 | 0.103 (0.046–0.187) | pass |
| 8 | SH: pre and post `Δ` ≤ 0.10; old ≥ 2× new; shocked price ratio within ±25% of value ratio | 0.29, 0.31; **1.33×**; error +0.4%, within ±25% on 17 of 20 | **fails** on three parts, **passes** on the price ratio |
| 9 | CAP `r̂` in [0.005, 0.5] | ±10^33 to 10^69, or −1, on 19 seeds | **fail** |
| 10, 11 | CAP converges on prices of production; deviation follows composition | | **void** (§3) |
| 12 | baseline 296 at +0.000% | 296 at +0.000% | pass |

The day-0 dispersion is the spread of the values themselves: a median of
0.480 (0.245–0.711). So prices close about a third of the distance to
values (0.48 to 0.33), and close it in a hundred-odd days on most seeds.
After that they stop.

## 2. Why SC prices stop short of values

The values are the technique's: one worker-day makes `1/l_i` units. The
producers did not make that much. Over the window, sectors that use
inputs ran at the following share of capacity:

| | median over seeds (range) |
|---|---|
| median sector, all twelve | 0.616 (0.469–0.738) |
| least-utilised sector | 0.33 (0.23–0.54) |

On no seed did the median sector reach 0.9.

Depth-0 sectors, which use no inputs, ran at exactly 1. The rest were
input-starved. A diagnostic copy of seed 0, instrumented outside the
module, shows why. Every market had more demand than supply on 3,738 to
4,437 of its 6,000 days. Its price balances excess demand on average,
through many small shortages and fewer large gluts. A producer that
holds exactly one day's inputs loses production on every short day.
Cash was the limit in only one sector, on half its days.

A producer stood idle still spent a whole worker-day. Incomes per
worker-day equalised, as prediction 7 says, so a sector running at
utilisation `u_i` must price its output above `A p + w l` by the idle
time. In steady state that gives `p = w v_real`, where `v_real` solves
`v = l / u + A v`. That is the labour actually spent per unit, idle
time included. Scored against it (**post hoc**: this statistic was not
in `docs/147`):

| against | `Δ` median (range) | `ρ` median (range) |
|---|---|---|
| technical values `v` | 0.332 (0.221–0.456) | 0.926 (0.728–0.981) |
| labour actually spent, `v_real` | **0.123 (0.075–0.221)** | **0.987 (0.849–0.995)** |

Ranges exclude seed 7 (§3). `Δ(v_real) < Δ(v)` on all 19 of the other
seeds.

Prices sit two to three times closer to the labour actually spent than
to the technical labour. In Marx's terms, the market priced the labour
time this economy socially required, given its own coordination
failures, not the time the technique would need if every producer
worked all day.

## 3. Why the capitalist arm collapsed

A trace of seed 1, from a diagnostic copy:

| day | sectors occupied | hired of 500 | wage | firms' cash | profit rates (spread) |
|---|---|---|---|---|---|
| 100 | 12 | 500 | 2.49 | 32,595 | −0.64 to 0.37 |
| 400 | 12 | 499 | 4.13 | 31,627 | 0.02 to 0.22 |
| 800 | 10 | 411 | 2.33 | 14,596 | −0.79 to 0.22 |
| 1,600 | 3 | 0 | 0.017 | 14,361 | 0.95 to 2,249 |
| 3,000 | 1 | 0 | 0.000 | 14,361 | all 22,005 |

For 400 days the arm behaves as designed: every sector occupied, full
employment, and profit rates converging. Then the first sector empties.
A firm can move only to a sector another firm occupies, so an empty
sector stays empty. With no seller, its price rises 2% a day for ever.
Every firm that needs that good as an input sees an unbounded unit cost
and plans no output, and the economy unravels into one sector. The
profit rate of a firm that sells old stock and buys nothing is then
unbounded, which is what `r̂` reports.

The simple-commodity arm has the same flaw but 500 producers rather than
100, so it rarely meets it. Seed 7 met it: its `Δ(v)` of 22.3 is a
sector that emptied and a price that ran away. Wright's 2008 rule moves
an actor to a random sector, which cannot do this, and ours lacked it.

## 4. What did work

- **Money** closed to 2e-13 over 6,000 days, and every run reproduced
  bit for bit.
- **Incomes equalised** with no agent seeing anything but another's
  income.
- **Prices followed a change in value.** Halving the labour of the
  most-used base good lowered its relative value to 0.569 of its old
  level (median). Its relative market price fell to 0.573. On 17 of 20
  seeds the price fell to within 25% of the value change, though nobody
  in the economy was told of it. That is the part of the law of value
  this experiment shows cleanly.
- **Prices know the technique, not just depth.** The null keeps the
  depth structure, and its correlation with prices was 0.45 against
  0.93. The predicted factor of three on dispersion was not met.

## 5. What follows

`docs/149` makes two changes and nothing else: exploration, so that an
empty sector is re-entered, and a five-day input buffer, so that a short
market day does not idle a producer. It restates `docs/147`'s bands
unchanged and adds the realised-labour test as a prediction.
