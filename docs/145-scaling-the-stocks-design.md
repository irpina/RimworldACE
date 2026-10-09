# Scaling the stocks with the economy, and re-docking: design

Written before the battery is run. `docs/142` §1 found that the
laboratory refuses the docked economy above about 480 commodities. This
document says what the fix is, why it is that fix and not another, and
what the re-dock at the full population must show.

## 1. The fault

`build_ours` sets three stocks per region from the authored demand per
final good, `demand`, alone:

| stock | value | sized in |
|---|---|---|
| the fund | 1,000,000 × `cash_multiplier` × `demand` | `docs/124`, `docs/137` |
| the workers' seed | 100,000 × `demand` × `cash_multiplier` / 10 | `docs/137` §2 |
| the labour pool | 400 × `demand` worker-days | `docs/124` |

Every final good carries `demand`, so the economy's flow grows with the
number of final goods while these stocks do not. The 647-commodity
population has 79 final goods to the battery's 25. The purses' working
capital is 1.38 times the fund, so the laboratory refuses to build. Had
it built, the labour pool would also have been short: producers at full
capacity need 391,740 workers against 320,000.

## 2. The fix: the stocks keep the ratio to the flow that docked

What `docs/133` to `docs/137` calibrated was not a sum of silver. It was
the money stock **against the flow**: `docs/133` found the fund ten
times too large against what it spent, and `docs/138` chose
`cash_multiplier` 0.3 for the ratio of the fund to the authored demand
it buys. That ratio is what should carry to a larger economy.

So `build_ours(scale_stocks=True)` multiplies all three stocks by

    scale = authored final demand a day, at reference prices
            / the same at the battery's 200 commodities

The factor is exactly 1.0 at 200, because the two sums are the same
floats added in the same order, so the docked battery does not move by
a bit. `DOCKED` turns it on. The default stays off, so every earlier
sweep reproduces.

Measured at design time, seed 0, two regions:

| commodities | scale | purses over the fund | full-capacity workers over the pool |
|---|---|---|---|
| 200 | 1.000 | 0.450 | 0.416 |
| 400 | 1.923 | 0.431 | 0.42 |
| 647 | 3.077 | 0.448 | 0.398 |

With the stocks scaled, a 647-commodity economy builds and, over 90
days, keeps 2,562 of 5,176 producers employing with money conserved to
7e-14.

Two alternatives were rejected. **Scaling by the number of final goods**
is cruder: the purses follow the cost of the whole requirement cascade,
which the authored value tracks and a count does not. **Scaling only
the fund** leaves the labour pool short at 647, which would make the
re-dock a test of a binding labour constraint the battery never had.

The battery's unemployment figure now reads the pool the economy has
rather than recomputing the default one. At 200 commodities and two
regions the two are the same number.

## 3. The re-dock

The `docs/138` instrument, unchanged: twenty seeds, two regions, six
months of burn-in and twenty-four measured, Wright's model alongside as
the control. The only change is `commodities=647`. Counts scale with the
producer population, 5,176 against 1,600, a factor of 3.235. Rates,
shares and shapes do not.

## 4. Predictions

Medians over twenty seeds unless stated. Bands are `docs/138`'s, with
the counts multiplied by 3.235.

1. **The docked battery at 200 is unchanged.** `build_ours(seed,
   **DOCKED)` builds and runs the same bits with and without the switch,
   and the 200-commodity run fixture regenerates byte-identical.
2. **Money is conserved on every seed**: `|cash_balance| < 1e-9 M`.
3. **The population lives**: employing in **[1,941, 3,073]**;
   bankruptcies in **[129, 647]**; fund at end in **[0.03, 0.30]** of M.
4. **GDP moves, modestly**: GDP growth std in **[0.015, 0.080]**, and
   excess kurtosis in **[−1.5, 8]**. Three times as many sectors average
   more noise away, so the std should fall from `docs/139`'s 0.061, by up
   to √3.2 to about 0.034, and stay in the band.
5. **Sectors are cost-ranked and boundedly dispersed**: cost rank ρ in
   **[−1.0, −0.6]**; sector CV in **[0.07, 0.30]**.
6. **No tail, and the instrument says so**: `x_min` over the largest
   firm in **[0.10, 0.60]**; firm growth excess kurtosis in **[30,
   1000]**.
7. **The wage share keeps its basis**: production wages over value
   added in **[0.008, 0.020]**, and with construction in **[0.60,
   0.95]**. `docs/139` measured 0.0198, at the band's top edge, so this
   is the prediction most likely to fail on a small shift.
8. **Demises** per firm-month in **[0.002, 0.020]**.
9. **The control is bit-identical** to `docs/139`'s.
10. **Unemployment** in **[0.85, 0.97]**: the artefact, scaled with its
    pool.

And `docs/141`'s prediction 3, re-run on the slice-0 instrument at two
regions, three seeds, 1,800 days:

11. **Commodity count is neutral**: at 647 commodities, the share of
    producers employing at day 1,080 is within ±20% of the 200-commodity
    figure, and so is value added a day per region in the last year
    **divided by the scale factor**. Value added in silver must grow with
    the authored demand, so the undivided figure cannot be neutral.

## 5. What would make this wrong

If 3, 5 or 8 fails, the docked economy's behaviour depends on its size
through something other than its stocks, and "the docked configuration"
would have to name a size. If only 4 fails, low, the economy is too
large to move and Wright's GDP fact is a small-economy fact in ours. If
11 fails on the employing share, the full population carries sectors
the battery's sample did not, and the game should keep 200.

## 6. What follows

The C# generator transliterates `build_ours` with `DOCKED`, so it takes
the same scale, and the port's fixtures are regenerated. Whether the
game then runs the full population is a separate decision. At six
regions it is 15,528 producers, about three times the battery's daily
cost.
