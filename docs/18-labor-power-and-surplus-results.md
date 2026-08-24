# Labor-power, the subsistence basket, and the surplus ledger: measured results

Recorded after implementing the design in
`docs/17-labor-power-and-surplus-design.md`. The old reference describes the
model with reserves and rent but no wage relation.

## Headline

The wage relation is implemented and the silver circuit closes.

- All 51 tests pass (38 prior + 13 wage-circuit and surplus tests).
- The four-commodity equilibrium is **exactly** stationary: price range
  exactly 0 for yayo, leaves, chemfuel, and meals in both regions over four
  years, with worker cash returning to exactly 900.0 every day.
- 9 of 53 frozen metrics moved, all small and all in the predicted pattern.
- All four material residuals and the cash residual close to floating-point
  zero in every scenario, including the new subsistence shock — the first
  scenario in which silver cycles producer → wage → worker → purchase →
  producer.
- Producer-loss still converges fully: by day 400 leaves sit at 1.900/1891
  and chemfuel at 2.300/151, identical to the pre-wage endpoints, with
  employment back at its equilibrium fixed point.
- Repeated runs are bit-identical.

## The one result: the rate of surplus value

At equilibrium, in both regions, constant over time:

```
s/v = 38.344
```

**It is a free parameter dressed in data, not an emergent quantity.** The
chain is closed-form, exactly as docs/17 predicted:

```
s/v = (ticks_per_worker_day − basket_labor_ticks) / basket_labor_ticks
    = (24000 − 2 × 305) / (2 × 305)
```

Its three legs: the working day (`ticks_per_worker_day`, a parameter), the
basket quantity (`meals_per_worker_day`, a parameter), and the meal's
embodied labor (305 ticks, a datum from the closed analysis). Prices never
enter. Nothing about market dynamics moves it: through the glut, the
producer loss, and a subsistence shock that triples the meal price, the
labor-time s/v stays at 38.344 to five figures.

What *is* path-dependent is the **money** side, and the subsistence shock
demonstrates the difference the ledger exists to keep: when Dust Basin's
provisioning is destroyed, the wage bill explodes (the wage peaks near 146
silver per worker-day against 30 at reference) while necessary labor in
ticks does not change at all. Money wages are not the value of labor-power's
reproduction, and money profit is not surplus value; the model now shows
both distinctions numerically rather than asserting them.

The level — 38 — carries the caveat recorded in advance: the basket is
meals-only, so the value of labor-power is understated and s/v is
correspondingly overstated. RimWorld's own data drives the magnitude too:
a pawn-day of aggregated provisioning labor yields ~79 meals, so feeding a
worker costs ~2.5% of a working day. s/v becomes an emergent quantity only
when labor values are endogenous, the wage can deviate from the basket, or
the basket itself becomes endogenous — all deliberately later.

## Prediction scorecard

### "Equilibrium: zero movement, exactly" — **correct**

Price range exactly 0.0 (not 1e-13 — zero) for all four commodities in both
regions. The engineering held: quantized employment (2^-20 worker-day grid),
power-of-two basket and capacity, and the seeded quantized fixed point
(0.31406497955322266 worker-days, self-reproducing from day one).

### "Glut trough up slightly, toward 14.36–14.38" — **correct**

14.356472 → 14.367961 (+0.0115). Direction and band right; the phrasing
"well under +0.01" was slightly optimistic. The wage raised the drug lab's
full-utilization threshold price from 16.44 to 16.90, so cost curtailment
begins earlier in the price fall.

### "Recovery 9 days, maybe 8" — **correct (8)**

The earlier curtailment drains the overhang faster; the quantized
half-recovery crossing moved one day earlier.

### "Distant trough, arbitrage volume, upstream glut extrema unchanged" — **correct**

All exactly unchanged, including the degenerate day-61 upstream extrema.

### "Producer-loss peak essentially unchanged" — **correct, exactly**

38.630290 on day 119, delta zero at six decimals. Surviving labs run at
full utilization regardless of the wage, and investment timing is coarse
enough that entry lands on the same days.

### "Producer-loss leaf/chemfuel troughs up slightly" — **wrong: unchanged**

Both troughs and their days are exactly unchanged (0.693449 day 70;
1.918998 day 69). The prediction reasoned that a higher zero-utilization
price would idle farms earlier and shallow the crash. In fact the farms
are already fully idle well before the trough in both runs; the trough
depth is set by the damped price formation working off the inventory
overhang, not by where the utilization curve cuts off. The cost floor moves
*when idling begins*, not the floor of the overshoot.

### "Producer-loss terminals drift ≤ 1%" — **direction right, band slightly exceeded**

The day-210 transients moved: leaf terminal price −1.6% (2.5073 → 2.4673),
leaf terminal inventory +2.0% (1425.5 → 1454.4), chemfuel terminal −0.6%,
and the day-168 rebound peaks about −1%. These are transients of a ~460-day
recovery, as flagged; the converged endpoint at day 400+ is identical to
the pre-wage model (1.900/1891, 2.300/151). Reconstruction also costs more
silver with wages in the effective cost: investment spending in the loss
scenario is 7,527 versus 7,397 before.

## Findings beyond the predictions

### The glut is a mass layoff, and subsistence production shrugs

On day 62 of the glut, regional employment collapses from 0.3141 to
0.0002 worker-days — the demand-led plan idles the drug lab, which
collapses the leaf order, which collapses the chemfuel order, all in one
planning pass. The model has had this idling since docs/11; wages make it
visible as unemployment for the first time.

The remarkable part is what does not happen: the meal price never moves
(trough 15.0000, flat), so the wage never moves. Worker meal demand falls
with employment, but the provisioners' demand-led plan contracts output to
match, and the capacity-based inventory target keeps the buffer exactly at
target — the same mechanism that keeps upstream goods degenerate through
the glut extends to the subsistence sector unchanged. Workers idled by the
glut lose their wage days but face no dearer bread.

In the producer-loss scenario the wage does cycle — meal price dips to
11.70 (workers idled, demand down) and overshoots to 16.40 during
reconstruction, taking the wage from 23.40 to 32.80 before settling back —
the first real-wage dynamics the model has produced.

### Wage-push does not propagate at this calibration

The subsistence shock (70% of Dust provisioning destroyed) triples the meal
price (peak ≈ 73) and with it the wage (peak ≈ 146/worker-day). Every
producer's effective cost rises through the cost floor — the drug lab's
wage cost per unit goes from 0.44 to 1.04 silver. And yet yayo and leaf
prices do not move at all: at reference the wage is only ~2.7% of the drug
lab's effective cost, so even a tripled wage cannot compress the 30% margin
below the full-utilization ratio.

This is the same structural finding as docs/16 made for chemfuel, now on
the labor side: **cost-push propagates in proportion to cost share.** A
subsistence crisis at this calibration is a catastrophe for workers (9.1
meals of basket shortfall; labor-power paid below its reproduction cost)
that the drug economy simply does not notice. That asymmetry is not a bug;
it is a legible class fact the model now states numerically.

### Forced saving

During the shock workers cannot buy meals that do not exist: spending
(4,129) falls short of wages (4,729) and worker cash accumulates to 1,500
against the 900 buffer. The unmet basket registers as price pressure and as
`basket_shortfall` in the ledger. Nothing yet acts on worker deprivation —
recorded, visible, deliberately unmodelled.

### Provisioning recovers through the existing machinery

Meal capacity rebuilds 0.30 → 0.71 by day 210 via ordinary margin-driven
and buffer-deficit investment; the meal price is falling back (35.5 and
declining) with workers again obtaining the full basket. No wage-specific
investment logic was added or needed.

## Accounting identities

- Equilibrium: all four price ranges exactly 0.0; worker cash exactly
  900.0 every day; cash residual 0.0; all four material residuals 0.0.
- Subsistence shock (210 days): cash residual 5.8e-11; material residuals
  ≤ 5.2e-13; wages 4,728.56 = spending 4,128.71 + worker-cash accumulation
  599.85 exactly.
- Producer-loss to day 660: residuals ≤ 9.5e-11 with employment, prices,
  and stocks all back at reference values.
- living labor = necessary + surplus per region (tested identity).

## Reference decision

The 9 moved metrics are understood (this document) and the movement is the
designed wage channel, not drift: the reference will be rewritten in its
own commit. The new labor observations (equilibrium employment, wage rate,
s/v, meal settlement; glut employment trough and flat meal price;
producer-loss employment trough and meal price cycle) are frozen in a
separate commit as newly observed quantities, not changed behavior.
