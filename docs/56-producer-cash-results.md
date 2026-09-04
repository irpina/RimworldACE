# Producer-level cash: results

`docs/55` set out eight predictions. Six held, one held better than
written, and one was wrong about the clock by a factor of twenty-five and
right about everything else.

**The headline: money profit is a flow now, and in the stationary circuit
it is exactly what the owners spend — 210 silver a day distributed, 210
silver a day of yayo bought — while the one sector that sells below its
cash cost is held at its purse's rest point without anyone being
bankrupted or anyone else being touched.**

## 1. What shipped

One flag (`producer_cash`), two coefficients (`working_capital_days`,
`bankruptcy_idle_days`), one purse per producer, one liquidity ration in
the same pass as the reserve and labor rations, four payment paths
(inputs and plant matter from the drawing producer, wages split by labor
used, final consumption from the owners' fund, exports and construction
matter from the fund), one settlement (purses above their working capital
distribute to the fund; producers idle for long enough are removed), one
scenario (`cash_circuit`), 20 metrics frozen (251 total), 8 tests (210
total). The viewer shows purses as a series and the money profit
distributed in the market-price panel, beside the notional it replaces
and never mixed with the surplus panel.

Every payment path is guarded and the rule is off by default: all 231
pre-existing metrics unchanged to six decimals (6.1).

## 2. Held: 6.2, 6.3, 6.5, 6.6, 6.8

**6.2 Exactly stationary.** Price range `0.0` over 240 days with purses.
Every purse holds the same float on every day after the first, because
the settlement sets it to its target rather than subtracting to it. The
fund drifts by **−3.5e-9** silver over the run, against a bound of one.

**6.3 Nobody is rationed** in the six-commodity circuit: zero runs lost to
liquidity, zero wages the fund had to cover, no bankruptcies.

**6.5 The rest of Department I is untouched**: no other purse below
target on the last day, no sector lost capacity, no other sector
rationed.

**6.6 The boom is funded**, and better than the 2% predicted: employment
on day 360 is the **same float** with purses and without. The fund's low
point is 92,711 silver; nothing that reads it ever bound. A purse reaches
prices only through what it stops a producer making, and in the boom it
stops nothing.

**6.8 Silver conserves** with the purses inside the identity: residuals of
7e-9, 8e-9 and 7e-9 in the three scenarios — ulps accumulated over
hundreds of days of a settlement that sets a purse to its target rather
than moving the exact excess, which is the price paid for 6.2's
bit-stationary purses and is the right trade.

## 3. Held, to the quantum: 6.7

The daily distribution per sector matches output times price less inputs
and wages per unit to **8e-6** silver a day, not the 1e-6 predicted. The
gap is the employment quantum: employment is floored to a multiple of
`2^-20` worker-days (`docs/17` §7), so the wage bill actually paid is a
few millionths below the unquantized labor cost the decomposition
reports, and the purse keeps the difference. The notional the price
decomposition has printed since `docs/23` is a flow now, and it has the
same number, to the rounding the model has always carried.

And the flows sum to something the design did not predict. The whole
region distributes **210.000000** silver a day, which is ten yayo a day at
21 silver: exactly what the fund spends on final consumption. Every
other sale is a transfer between producers, or from workers who were paid
by producers; the only silver that enters the producers' purses from
outside them is the owners' spending, so the only silver that can leave
them as profit is the same amount. Kalecki's identity — capitalists earn
what they spend — falls out of the bookkeeping, and the fund's drift of
−3.5e-9 is that identity measured.

## 4. Wrong about the clock: 6.4

Predicted: the component purse drains within 20 days. Measured: the
component price first moves on **day 557**.

The prediction forgot what `docs/37` §6 already said. The component
sector is priced below its cost, so the utilization curve already held it
at **3.0%** of capacity before any purse existed; a sector making
0.0019 units a day and losing 6.12 silver on each loses two hundredths of
a silver a day, and five days of working capital at full-capacity outlay
is 12 silver. The purse takes 550 days to empty, not 20.

What happens afterward is what the design said would. The liquidity
ration cuts runs to what yesterday's revenue pays for, output falls short
of the circuit's call, the shortfall raises the price, and the price
rests at **1.3655×** its authored 32 — inside the predicted 1.1 to 1.5 —
from day 694 on, unchanged to the sixth decimal for the remaining five
hundred days. No bankruptcy, no capacity lost, 1.45 runs curtailed over
the whole run. The `docs/39` rest point, where the maintenance rule took
2,200 days to get the price up 19.8%, is reached here in 140 days with a
36.6% rise, because a purse is a harder constraint than a margin.

Utilization at the rest point is **0.030**, not the 0.3 to 0.8 predicted,
for the same reason as the clock: the curve had it at 3% already, and the
rest point is a price at which 3% pays for itself, not a higher output.

One thing moved that the design said would not. The yayo price range in
`cash_circuit` is **7.2e-5** silver, not zero: components are in yayo's
plant bill, so a dearer component is a dearer drug lab, and the cost
ratio moves the anchor by a few ten-thousandths. That is the `docs/21`
channel working, not a purse reaching a price; §4 of the design was
right about the mechanism and wrong to say the range would be exactly
zero in a scenario where a price is *meant* to move.

## 5. Carried forward

**Money profit is real now**, which is what `docs/50` needed and what
`docs/43` needed for rent as a flow: a landlord can be paid out of a
purse. The absolute rent bound can become a payment in a later slice.

**The fund is the capitalist class as a single household.** It is
regional, it cannot fail, and it spends only on the final good. That is
enough for the circuit to close and not enough for `docs/50`'s colony,
which is one owner among many. Owner-level funds are a later slice.

**The pool is still a consignment.** Who is paid for a unit sold is
decided by supply shares, not by whose unit it was, and an import sold
the day after a local unit pays the local producer. Producer-level
inventory is the procurement slice (`docs/59`), and this is the reason it
is next after prices.

**The 2,200-day rest point and the 140-day one are the same point.**
`docs/39` and this document measure the same sector with two different
constraints and get the same shape. Whichever binds first sets the clock.

## 6. Cost

Four runs, one of them 1,200 days of Department I, about 1.5 seconds of
the metric collection.
