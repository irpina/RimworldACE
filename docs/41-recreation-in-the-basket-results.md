# Recreation in the basket: results

This scenario existed to fire one standing prediction, written in `docs/37`
§8 and repeated as `docs/40` §7.2. **It fired, and the prediction was half
wrong — in a way that corrects how the project has been reading its own
biggest result.**

Four of the six predictions were right, two were wrong, and both wrong ones
are the same confusion: I treated *basic* as a magnitude when it is a
category.

## 1. What shipped

Yayo enters the workers' basket at a quantity that is deliberately not
calibrated — RimWorld's recreation need is met mostly for free, and no colony
lives on drugs, so a single "true" figure would be an invention. The default
is 0.0625 a worker-day and the answer is reported over a sweep.

The equilibrium reports a price range of **exactly zero** across all nine
commodities in both regions, and all three ledgers close. This is the first
self-referential price in the model — yayo's price is on both sides of yayo's
own cost equation, through the wage — and the fixed point handles it without
comment.

## 2. Right: the structure

**7.1 All nine commodities become basic.** Yayo through the wage bundle,
psychoid leaves through yayo. The non-basic category empties for the first
time in the project.

**7.3 Leaves matter more than yayo, despite holding a third of the plant.**
Stripping the plant out of one sector at a time, at the default quantity:

| plant stripped from | `r` | recovered |
|---|---:|---:|
| nothing | 0.448970 | — |
| yayo (67.3% of the stock) | 0.454697 | +0.005727 |
| psychoid leaves (22.3%) | 0.461727 | +0.012757 |
| both | 0.468349 | +0.019379 |

Leaves recover **2.2×** what yayo recovers while holding a third as much
plant, exactly as predicted and for the predicted reason: what weighs on the
rate of profit is `K/cost`, and leaves' is 9.4 days against yayo's 2.7.

**7.4 Quantities barely move.** Yayo output rises 0.2%, the money wage rises
from 41.9700 to 43.2825 (+3.128%, predicted 3.1%), and every labor value is
unchanged to six decimal places — tighter than the "less than 0.1%"
predicted.

**7.5 `s/v` falls to about 25.3.** Measured **25.3108** against a predicted
25.3. `docs/40` §6 had written test 6 the wrong way round — as `s/v` rising —
and §7.5 corrected it in the same document before any code existed. The
correction is kept in both places rather than tidied away.

## 3. Wrong: 7.2 and 7.6, and they are one error

**7.2 predicted `r` ≈ 0.30, with 0.25–0.40 counting as right. Measured
0.448970** — a fall of 13.4%, well outside the band.

**7.6 predicted a step: "almost the whole effect on `r` appears between 0 and
the smallest tested value, and the curve is then gentle. If `r` instead moves
smoothly from 0.5182 as the quantity grows, basicness is not doing the work."**

It moves smoothly. The design named its own failure condition and the
condition fired:

| yayo per worker-day | basics | `r` | `r` with no plant anywhere |
|---:|---:|---:|---:|
| 0 | **7** | 0.518250 | 1.172566 |
| 0.000244 | **9** | 0.517892 | 1.167743 |
| 0.003906 | 9 | 0.512648 | 1.104332 |
| 0.015625 | 9 | 0.497161 | 0.967792 |
| 0.0625 | 9 | 0.448970 | 0.726207 |
| 0.25 | 9 | 0.345942 | 0.458442 |
| 0.5 | 9 | 0.279181 | 0.342369 |

Look at the first two rows. **At one part in four thousand of a yayo per
worker-day, every commodity in the model is already basic — and the rate of
profit has moved by 0.07%.** The category flips completely and takes almost
nothing with it. Everything after that is the quantity.

## 4. The correction: basicness is binary, its weight is not

`docs/37` §4 found that 89.6% of the economy's fixed capital sits in yayo and
psychoid leaves, both non-basic, and moves the general rate of profit by
6e-13 — by nothing. That finding stands; it is Sraffa's theorem and it is
exact.

What I then wrote in `docs/37` §8 does not:

> If anything ever consumes yayo as an input, 89.6% of the fixed capital
> stops being inert and **the rate of profit moves a long way.**

The first clause is right. Once yayo is basic, stripping the plant from yayo
and leaves moves `r` from 0.448970 to 0.468349 — a real 4.3%, where before it
was 6e-13. **The inert capital genuinely stops being inert.**

The second clause is wrong. 4.3% is not a long way, and it is not what
produced the 13.4% fall in `r`; most of that came from the wage. The
inference — *these sectors hold most of the plant, so if they became basic
they would matter a lot* — confuses two different things:

- **Non-basic is a veto.** A non-basic sector's technique cannot affect `r`
  at all, whatever it holds. That is a theorem and it is why 89.6% of the
  plant did nothing.
- **Basic is only permission.** Once permitted, how much a sector's plant
  weighs on `r` is set by how much of it enters everyone else's cost — the
  `K/cost` ratio, and the coefficient by which the sector enters the
  others. Yayo enters other sectors only through 0.0625 units in a wage
  bundle that is itself 3.6% of the working day.

So a sector can hold two thirds of the economy's fixed capital, be basic, and
still be nearly irrelevant to the rate of profit. **Lifting a veto is not the
same as exercising it.** `docs/37` §8 is annotated with a pointer here.

## 5. Where the fall actually comes from

The right-hand column of §3's table is the wage effect with the plant removed
entirely, and it falls faster than `r` does: from 1.1726 to 0.7262 at the
default quantity, a 38% fall with no fixed capital in the system at all.

The reason is that the price system's wage is `p·b/T` at *production prices*,
and yayo's production price is 1074 against meals' 56. So 0.0625 yayo a
worker-day adds 3.1% to the money wage at authored prices and far more than
that to the wage the price system charges. Putting an expensive luxury in the
subsistence basket is a large change to the value of labor-power however
small the quantity looks in units.

There is also a second-order result in that column worth recording: **the
plant's cost in `r` shrinks as the basket grows.** It is 0.654 at zero yayo,
0.277 at 0.0625, and 0.063 at 0.5. A higher wage leaves less room for profit,
so there is less profit for the fixed capital to be measured against. The two
mechanisms are not additive.

## 6. What is still missing

- **Tolerance and addiction.** `Yayo` carries `addictiveness 0.01` and a
  `Psychite` chemical need, so a real recreation basket would *grow* with
  consumption. That is a different model of the value of labor-power.
- **Other recreation goods**, which would let the basket substitute — a
  demand system, not this.
- **Recreation as leisure rather than as a good.** The honest reading of
  RimWorld is that recreation is mostly time, and time is not a commodity.
  The model has no division of the working day beyond
  `ticks_per_worker_day`.
- **The sensitivity sweep**, still stale since the cost floor. It now has a
  further reason to be re-run: `yayo_per_worker_day` is a parameter whose
  effect on `r` is large and continuous, which is exactly what a sweep is
  for.

## 7. What would make this wrong

- If `recreation.production.profit_rate_at_epsilon` ever moves far from
  0.5179, the mechanism in §4 has changed and this document needs
  re-deriving. It is frozen for that reason, beside
  `basics_at_epsilon = 9`, because the pair is the whole argument.
- If the equilibrium stops being exactly zero, the self-referential wage
  is the first suspect — though the actual failure during development was
  duller than that, and is in §8.
- §4's correction rests on `K/cost` being what weighs a sector's plant. If
  a later scenario shows a basic sector with a *low* `K/cost` moving `r` a
  lot, that account is wrong.

## 8. One defect, and it was not the interesting one

The first attempt raised yayo's capacity to make room for the basket and left
psychoid leaves at 80 a day. Leaves capacity is *derived* from
`producer_capacity_per_day`, and overriding the yayo entry in the capacity
table alone does not touch it — so the fields were four units a day short of
what the drug lab now wanted, leaves stock fell 0.159 a day, and the
equilibrium's price range came out at 1.62 instead of 0.

Worth recording because the diagnosis went to the exotic explanation first.
The scenario had just introduced the model's first self-referential price and
that was the obvious suspect; it was innocent. The bug was that a derived
parameter was bypassed rather than raised.
