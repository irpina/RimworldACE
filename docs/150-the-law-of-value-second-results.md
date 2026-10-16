# The law of value, second experiment: results

Scores `docs/149`. **The simple-commodity economy demonstrates the law of
value.** Prices that start equal and move only on excess demand, with
producers who see nothing but one another's incomes, settle on the
technique's labour values. When a technical change halves one good's
labour, they move to the new values. The capitalist arm earns a profit
and survives on every seed. But its prices are no closer to prices of
production than the noise allows, and in this economy prices of
production lie too close to values for the arm to tell the two apart.

The battery is `economy_lab/law_of_value149_results.json`, made with
`python3.12 -m economy_lab.law_of_value out.json 20 6000 second`.

## 1. One fix before the run

The first launch stopped at 19 of 60 runs. One producer's cash had been
left a hair below zero by rounding while it had nothing to order, and
the order rule divided zero by zero. The guard treats that as nothing
to order. It touches no path the first experiment ran, because that
experiment would have stopped on it too. The battery was then rerun
from the start, and the 19 rows that had finished reproduced exactly.

## 2. Scores

`docs/147`'s twelve predictions with their bands unchanged, and
`docs/149`'s three. "Every seed" is stated where the prediction said
so; otherwise the figure is the median.

| # | prediction | measured (median; range) | verdict |
|---|---|---|---|
| 1 | money conserved, < 1e-9 | 2.0e-13 at worst | pass |
| 2 | bit-identical reruns | the tests, and 19 rows across two launches | pass |
| 3 | SC `Δ(v)` in [0.002, 0.10], no seed above 0.20 | **0.084** (0.030–0.182) | **pass** |
| 4 | SC `ρ(v) ≥ 0.98` | **0.988** (0.868–0.999) | **pass** |
| 5 | `Δ(v°) ≥ 3 Δ(v)`; `ρ(v°) < ρ(v)` on every seed | ratio **5.3** (2.3–24.8); **20 of 20** | **pass** |
| 6 | half of day-0 dispersion gone by day [100, 2,000] | **160** (120–3,390) | **pass** |
| 7 | income CV across sectors ≤ 0.15 | **0.151** (0.079–0.212) | **fail**, by 0.001 |
| 8 | SH: `Δ` before and after ≤ 0.10; old ≥ 2× new; price ratio within ±25% of value ratio | 0.086; 0.075; **2.74×**; error −0.7%, within ±25% on 19 of 20 | **pass** |
| 9 | CAP `r̂` in [0.005, 0.5] | 0.18 (0.14–0.38), every seed in band | pass |
| 10 | CAP `Δ(PoP) ≤ 0.10`; `Δ(PoP) < Δ(v)` on ≥ 16 seeds | **0.65** (0.077–1.41); 20 of 20 | **void** (§4) |
| 11 | CAP corr(`log p̄/v`, `log(1+k)`) ≥ 0.5 | 0.47 (0.01–0.90) | **void** (§4) |
| 12 | baseline 296 at +0.000% | 296 at +0.000% | pass |
| 13 | SC median sector utilisation ≥ 0.90 on every seed | 0.92 (0.80–0.99); **14 of 20** | **fail** |
| 14 | no sector empty > 5% of the window, any seed | SC 1.4% at worst; **CAP 70%** | **fail** (CAP) |
| 15 | SC `Δ(v_real) ≤ Δ(v) + 0.01` on every seed | 0.060 against 0.084; **17 of 20** | **fail** as stated |

## 3. The simple-commodity economy

Six numbers carry the result:

| | first experiment | second |
|---|---|---|
| `Δ(v)`, dispersion from values | 0.332 | **0.084** |
| `ρ(v)`, correlation with values | 0.926 | **0.988** |
| `Δ(v°)/Δ(v)`, how much worse the null does | 1.99 | **5.3** |
| median sector utilisation | 0.62 | 0.92 |
| SH, `Δ` against the new values after the change | 0.31 | **0.075** |
| SH, shocked good's price ratio over its value ratio | 1.004 | **0.993** |

The day-0 dispersion is 0.48. Prices now close five sixths of it, and
half of it within 160 days.

**The null fails clearly.** `v°` keeps the depth structure: deep goods
still carry more labour. Its correlation with prices is 0.35 against
0.99, and its dispersion is five times larger. So prices do not just
know that deep goods take more work. They know the technique.

**Prices follow values when values change.** On day 3,000 the most-used
base good's labour is halved without anyone being told. Its value
relative to the rest falls to 0.569, and its relative price falls to
0.569. In the last thousand days prices sit 2.7 times closer to the new
values than to the old.

**The failures are near misses on the mechanism, not the claim.**
Income CV is 0.151 against a band of 0.15. Utilisation reached 0.9 on
14 seeds, not all twenty. The six that fell short (5, 6, 7, 16, 17 and
18) include the three with the largest `Δ(v)`: 5, 6 and 16, at 0.16 to
0.18. Labour actually spent beats technical labour as the predictor on
17 of 20 seeds (median 0.060 against 0.084). The exceptions are seeds 3,
14 and 18, where technical labour wins by 0.01 to 0.02. Where the
market idles producers, prices price the idle time. Where it does not,
technical and realised values coincide and prices sit on both.

## 4. The capitalist arm

Exploration kept the arm alive: every seed made a profit at a rate of
0.14 to 0.38 per day on outlay, with 82 to 96% employment. But with 100
firms it re-enters an empty sector only every 120 days or so. On 16
seeds some sector was empty for more than 10% of the window, and on 7
for more than 40%. An empty sector's price runs away, and that is what
the dispersion measures. Across seeds, the log of `Δ(PoP)` correlates
0.82 with the mean share of sector-days empty. The two seeds whose
sectors stayed occupied (9 and 12) sit on prices of production at 0.096
and 0.077.

`docs/149` §4 said in advance that if prediction 14 failed, the
capitalist predictions would be void. So 10 and 11 are void, and their
figures above are reported, not scored.

There is a second reason they could not have been decisive. In this
technique, at these profit rates, prices of production lie only **0.048**
(median) from values in the same dispersion measure: a small composition
spread and one-day turnover make the transformation small. The best
capitalist seeds have noise of 0.08. Prices were closer to prices of
production than to values on all 20 seeds, but by 0.003 to 0.05, a
margin of the same size as the gap. Prediction 9's band, set on the
profit rate, was the wrong guard. The condition that matters is the gap
between prices of production and values against the noise, and it was
not met.

## 5. What this demonstrates, and what it does not

**Demonstrated, in this laboratory:** in an economy where nothing knows
a labour value, nothing computes one, and no price is anchored to
anything, decentralised trade and the movement of producers toward the
higher income bring market prices to the technique's labour values.
That holds within 8% in dispersion and 0.99 in correlation, from prices
that started equal. It follows a change in technique to the new values.
It is the technique's labour that prices track, not a proxy such as
depth. And where the market's own coordination failures leave producers
idle, prices track the labour actually spent, idle time included: in
Marx's terms, the labour time socially necessary under the conditions
the economy actually has.

**Not demonstrated:**

- That prices of production, not values, are the centre once capital
  rather than labour moves. That needs a capitalist arm that keeps every
  sector occupied, and a technique whose transformation is larger than
  the noise: more varied composition, or longer turnover. It is the
  natural third experiment.
- Anything about real economies, or about the docked economy, whose
  prices remain RimWorld's (`docs/147` §1).
- That the equilibrium is the substance. Once incomes are equal, `p ∝ v`
  is accounting. What the experiment shows is that this market finds
  that state without being told it, holds it, and moves when it moves.

The two experiments differ in two switches, both on
`law_of_value.py` and off by default. The first experiment's battery is
`law_of_value147_results.json` and reproduces under the default
switches.
