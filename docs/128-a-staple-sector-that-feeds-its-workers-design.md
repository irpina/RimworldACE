# A staple sector that feeds its workers: design

Written before anything is built or run. Measured in `docs/129`.

## 1. What `docs/127` §3 was actually seeing

`docs/127` §3 reported that a `basket_fraction` of 0.2 kills the ×200
economy by a cascade from about day 100, and blamed prices that "never
see the basket". That was half right. Traced today, with investment
switched off so it could not be the sink:

| basket | day 45 | day 90 | day 120 |
|---|---|---|---|
| 0.02 | staple price 0.68, wage 5.2 | 1.65, 12.7 | **4.08, 31.5** (was 0.5, 3.9) |
| 0.1 | 1.40, 54 | 51, 1,981 | 149, 5,762 |
| 0.2 | 2.09, 161 | 181,000, 1.4e7 | 1.3e14, 1.0e16 |

**It is a wage–price spiral, and it is running at every basket, the
shipped one included.** The wage *is* the basket's price
(`Region.wage_rate`); posted prices rise on shortage; the staple is
short; so the wage rises, every producer's outlay rises, purse targets
(`working_capital_days × daily_outlay`) rise with them and swallow the
money stock — at 0.2 the sum of purse targets passes the whole money
supply on day 75 and reaches 10¹⁴ times it by day 135 — the fund, the
only final buyer, is left with nothing, and production stops with 100%
of the silver sitting in purses. Not a leak, not the investment sink:
a hoarding deadlock driven by a nominal spiral.

And the staple is short for a reason the generator owns. Measured on
the ×200 scenario, day one, one region:

    staple capacity          204,451 a day
    workforce basket demand  201,092 a day   (26,058 workers × 7.7 units)

`_required_output` cascades final demand down the input graph and sizes
every sector to it with 25% headroom. **The workers' own consumption is
not in that demand.** The staple sector is sized only to whatever
intermediate use the graph happens to make of it, so its inventory
drains from 9.1M to 60k in ninety days at full capacity, and the price
does what a price does. At ×1 with nine workers this was invisible.

## 2. The fix

A generator parameter, `basket_in_demand: bool = False`. When on, the
required output is solved as a fixed point rather than a single cascade:

    required   = cascade(final_demand)
    repeat:
        workers  = Σ_i required_i × labour_i / ticks_per_worker_day
        required = cascade(final_demand + {staple: workers × basket_quantity})
    until the staple requirement moves by less than one part in 10⁶

The staple's own labour adds workers, who need more staple, so it is a
geometric series with ratio (basket share of the staple's labour), which
is below one whenever the basket is a proper fraction of a working day
— Marx's condition for a reproducible economy, and `basket_fraction` is
that fraction by construction. Off by default; `fixtures.py` pins the
generator's output and must not move.

Nothing changes in `model.py`. This is the generator failing to give
the model a scenario in which labour-power can be reproduced, which is
the same family as `docs/126` §1's finding: the scenario, not the
ontology.

## 3. Numbered predictions

All two-sided. `×200` means the `docs/126` battery configuration with
investment off (`investment_interval_days` beyond the run), so that the
spiral is measured on its own.

1. **The spiral stops at the shipped basket.** At ×200,
   `basket_fraction = 0.02`, `basket_in_demand = True`, the staple price
   at day 120 is within **[0.8, 1.25]×** its day-one price (it was
   8.2×), and the mean log price ratio across commodities is within
   **[−0.10, +0.10]** (was +0.176).
2. **Bit-identical when off.** Every fixture in `fixtures.build_all()`
   is unchanged apart from the pre-existing one-ULP `scale_647_day3`
   failure, and `baseline` shows 322 metrics at zero delta.
3. **The fixed point is tame.** For baskets 0.02, 0.1, 0.2 and 0.5 it
   converges in **at most 20** iterations, and the resulting staple
   capacity exceeds the day-one basket demand of the workforce it
   implies by the headroom factor, **1.25 within 2%**.
4. **A 0.2 basket lives.** At ×200 and `basket_fraction = 0.2` with the
   fix on, the economy runs 180 days without a payroll failure, ends
   with employing producers in **[150, 250]** and bankruptcies in
   **[0, 40]** (was 0 and 167), and the staple price at day 180 is
   within **[0.5, 2.0]×** day one.
5. **The money wage share is then the basket, roughly.** With the fix
   on, wages over value added over 180 days lands in **[0.05, 0.15]** at
   0.02, **[0.25, 0.50]** at 0.1 and **[0.40, 0.70]** at 0.2. If 4 and 5
   both hold, Wright's 0.55 is reachable by our lab with the economy
   alive — as an input, which `docs/127` §3 already established is what
   it is here.
6. **0.5 is still too much, and for a different reason.** At
   `basket_fraction = 0.5` the fix removes the spiral (staple price at
   the last recorded day within [0.5, 2.0]× day one) but the economy
   still fails or collapses within 180 days, because the generator's
   authored prices carry a fixed cost share that a wage of half the
   product exceeds. This one is a prediction about *where* the next
   wall is; a 0.5 economy that lives would be a pleasant surprise and
   would falsify it.
