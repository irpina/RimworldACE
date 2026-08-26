# Recreation in the basket: design

Written before implementation. `docs/28` §2.2 deferred this deliberately and
said why: yayo is the model's own final good, and putting it in the workers'
basket makes it *basic*, which creates a wage-price loop through the one
commodity every scenario is measured on.

`docs/37` §8 then left a standing prediction, in writing, as the last line of
its "what would make this wrong":

> §4's claim rests on yayo and leaves staying non-basic. If anything ever
> consumes yayo as an input, 89.6% of the fixed capital stops being inert and
> the rate of profit moves a long way. That is a prediction, and it is the
> first thing to check if a later scenario makes yayo an input to anything.

This is that scenario. It exists to fire that prediction.

## 1. The quantity is not calibrated, and saying so is the point

RimWorld's recreation need is met mostly for free. A pawn watching clouds,
sitting in a chair or chatting fills the same bar that yayo fills, and
`Need_Joy` deliberately penalises repeating one kind. `Yayo` gives `joy 0.80`
of `joyKind Chemical`, but no colony meets its recreation need on drugs, and
a model that says the reproduction of labor-power *requires* 0.8 of a
worker-day's recreation in cocaine would be asserting something about
RimWorld that RimWorld does not say.

So the quantity is **not** derived from the joy mechanic. It is a parameter,
reported over a sweep rather than at a point — the same discipline `docs/28`
§3.5 used for the generous basket, which existed to bound an answer from
above rather than to be believed.

The default is `yayo_per_worker_day = 0.0625`. It is an exact binary fraction
for the same floating-point reason as every other basket quantity (`docs/17`
§7), and it is deliberately **small**: against a final demand of 10 a day it
is about 0.2% more yayo.

**That smallness is the experiment.** Basicness is binary. A commodity either
enters the production of everything or it does not, and 0.2% of extra demand
flips yayo from one to the other. If `docs/37` §4 is right, a 0.2% change in
quantities will move the rate of profit by tens of percent — which is not a
sensitivity, it is a change of regime.

## 2. What changes structurally

**Yayo becomes basic**, because it enters the wage bundle and the wage bundle
enters every sector that employs labor.

**Psychoid leaves become basic too.** Nothing consumes leaves but yayo; once
yayo is basic, leaves enter everything through it. So *every* commodity in
the model becomes basic, and the non-basic category empties.

**The 89.6% of fixed capital that `docs/39` showed to be inert becomes
live.** Yayo holds 67.3% of the economy's plant and leaves 22.3%, and both
are currently non-basic, which is precisely why `docs/39` measured them as
moving the general rate of profit by 6e-13. That protection ends here.

**A wage-price loop closes through yayo.** Yayo's price enters the wage,
the wage enters yayo's cost, and its own price is now on both sides of its
own equation. The price system handles this — it is an ordinary self-input in
the augmented matrix — but it is the first time the model has had one on the
commodity every scenario is anchored to.

## 3. Calibration

Yayo runs at exactly full capacity in the seeded circuit: capacity 10 a day
against a final demand of 10. Basket demand has nowhere to come from, so the
scenario raises `producer_capacity_per_day` enough to cover it. Leaves and
chemfuel capacity are derived properties and scale on their own.

Deliberately **not** done the other way. Cutting final demand to make room
would hold total yayo output constant and change what is being measured; the
comparison has to be "the same economy plus a basket entry", not "a smaller
economy".

## 4. Non-goals

- **Other recreation goods.** Beer at `joy 0.17` and smokeleaf at 0.80 are
  in the game and are not in the model. Adding a second recreation good
  would let the basket substitute between them, which is a demand system
  and not this.
- **Tolerance, addiction and overdose.** `Yayo` carries `addictiveness 0.01`
  and a `Psychite` chemical need. A basket entry that *grows* with
  consumption is a genuinely different model of the value of labor-power
  and deserves its own session.
- **Recreation as time rather than goods.** The honest reading of RimWorld
  is that recreation is mostly leisure, and leisure is not a commodity. The
  model has no representation of the working day's division beyond
  `ticks_per_worker_day`, and giving it one is a much larger change.

## 5. Interface

```python
ScenarioParameters(recreation_basket=True)     # default False
ScenarioParameters(yayo_per_worker_day=0.0625)
scenarios.recreation_basket()                  # the scenario
scenarios.recreation_sweep()                   # the curve, not the point
```

## 6. Tests

1. With the basket entry off, everything is bit-identical.
2. Yayo and psychoid leaves are both in `basics`, and the non-basic
   category is empty.
3. The equilibrium is exactly stationary with a price range of exactly zero.
4. The three ledgers close.
5. The rate of profit is strictly below the capital-goods figure of 0.5182,
   and the fall is attributable to plant: stripping the plant out of the
   price system must recover a rate close to the no-plant 1.1726.
6. `s/v` rises, because the basket got more expensive while the working day
   did not change.

## 7. Predictions

**7.1 All nine commodities become basic.** Seven now; yayo and leaves join.
The non-basic category empties for the first time in the project.

**7.2 The rate of profit falls to roughly 0.30.** `docs/39` established that
10.4% of the plant — the part in basic sectors — took `r` from 1.1726 to
0.5182. This scenario adds the other 89.6% to the basic subsystem. It is not
a linear extrapolation, because the newly-basic sectors have much lower
plant-to-cost ratios (yayo 2.7 days and leaves 9.4, against chemfuel's 56 and
meals' 37), which is why the prediction is 0.30 and not 0.05. Anywhere in
0.25–0.40 counts as right; outside it, wrong.

**7.3 Leaves matter more than yayo.** Leaves hold a third as much plant as
yayo but their circulating cost is tiny — `K/cost` of 9.4 days against yayo's
2.7 — and it is that ratio, not the stock, that sets how much a sector's
plant weighs on `r`. Stripping the plant from leaves alone should recover
more of `r` than stripping it from yayo alone, despite yayo holding three
times the plant.

**7.4 Quantities barely move.** Yayo output rises about 0.2%. The money wage
rises 3.1%, from 41.97 to about 43.28, being the basket plus 0.0625 yayo at
21 silver. Labor values move by less than 0.1%, because 0.2% more yayo is
0.2% more of a commodity that is 0.18% of the labor performed.

**7.5 `s/v` falls, not rises — and test 6 as written is wrong.** Necessary
labor is the basket at *labor values*, so adding 0.0625 yayo at 736 ticks
adds 46 ticks to a basket currently worth about 866. That is a 5.3% rise in
the value of labor-power against an unchanged working day, so `s/v` falls
from 26.71 to about 25.3. Writing test 6 the wrong way round first is
recorded rather than quietly fixed.

**7.6 The sweep is not linear near zero.** Basicness flips at the first
positive quantity, so almost the whole effect on `r` appears between 0 and
the smallest tested value, and the curve is then gentle. If `r` instead moves
smoothly from 0.5182 as the quantity grows, basicness is not doing the work
and 7.2's mechanism is wrong.

## 8. What would make this wrong

- **If the equilibrium stops being exactly zero**, stop and report. The
  wage-price loop is the first self-referential price in the model and it is
  the obvious suspect, but the calibration change is the likelier one.
- **If `r` does not move**, `docs/37` §4 was wrong about non-basicness
  protecting the rate of profit, and that conclusion has to be withdrawn
  rather than explained.
- **If `r` moves but stripping the plant does not recover it**, the fall is
  coming from the wage rise rather than from the plant, and 7.2's whole
  mechanism is misattributed. Test 5 is what separates them.
