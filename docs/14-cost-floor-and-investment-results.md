# Cost floor and investment motives: measured results

This comparison was recorded after implementing all three changes from
`docs/13-cost-floor-and-investment-design.md` and before rewriting
`behavior_baseline.json`. The old reference describes demand-led replenishment
without input costs or construction-fund investment.

## Headline

The cost floor and buffer-aware investment resolve the remaining free-ledger-
source problems without creating equilibrium oscillation.

- All 30 tests pass (25 prior + 3 cost-floor + 2 buffer-resolution).
- Four-year equilibrium price and inventory paths are exactly stationary for
  all three commodities in both regions.
- Repeated scenarios produce identical histories.
- All material residuals close to floating-point zero.
- Silver balances close to floating-point zero, including investment spending.
- The post-shock buffer scar (leaves at 1,451 instead of 1,600) resolves:
  upstream prices return to reference and stocks reach their targets.

Sixteen of 53 frozen observations move; thirty-seven remain unchanged.

## Prediction scorecard

### "Equilibrium metrics unchanged" — **correct**

Both price ranges remain exactly 0. The arithmetic check in docs/13 was right:
all three producers' effective cost ratios at reference prices (1.34 to 1.50)
are above the 1.05 full-utilization threshold.

### "Zero additional movement in the glut" — **wrong**

Five glut metrics moved. The prediction failed because it only considered
upstream input price movements (which don't occur in the glut) and overlooked
that the effective cost *itself* rose (from 14.0 to 15.66 for the drug lab).
The utilization curve's reference cost changed even without any price movement.

At the glut's trough price of ~14.34, the old ratio was 14.34/14.0 = 1.024
(at full utilization). The new ratio is 14.34/15.66 = 0.916 (well inside the
curtailment zone). The drug lab now curtails production during the glut, which:

- makes the trough shallower (14.34 → 14.36, +0.1%);
- speeds recovery (11 → 9 days, −18%);
- reduces arbitrage volume (12.38 → 11, −11%) because less surplus forms.

All upstream glut metrics remain at their day-61 degenerate values — the
demand-led control continues to prevent upstream excursion, and the cost floor
adds nothing there.

### "Small or zero movement in producer-loss" — **partially wrong**

The final-good headline is unchanged: price still peaks at 38.63 on day 119
and capacity still reaches 80% after 75 days. The early upstream path
(troughs, trough days) is also unchanged — the cost channel and buffer
investment don't affect the immediate shock response.

But six producer-loss metrics moved significantly, all in the terminal/peak
upstream observations. This was unexpected from the cost floor alone but is a
direct and correct consequence of the buffer-deficit investment motive:

- chemfuel price peak: 2.44 → 2.93 (+20%), shifted from day 125 to day 210
- leaves price peak: 2.43 → 2.82 (+16%), shifted from day 125 to day 168
- chemfuel terminal stock: 115.7 → 103.9 (−10%)
- leaves terminal stock: 1,427.5 → 1,425.5 (−0.1%)
- chemfuel terminal price: 2.38 → 2.93 (+23%)
- leaves terminal price: 2.10 → 2.51 (+19%)

These are higher because the buffer-rebuild investment is drawing silver and
creating additional capacity during the observation window. The system is
actively rebuilding — the terminal values are a transient, not a converged
state.

### "Buffer scar resolves" — **correct**

Extended to day 660, leaves converge to 1,891/1.900 and chemfuel to 151/2.300.
Both are at their targets at exactly reference prices. The stocks are higher
than the original 1,600/120 because the new replacement capacity raised
throughput demand, which raised the target. This is a new, larger, self-
consistent equilibrium — not a scar.

### "Input-shortage shows earlier/deeper yayo curtailment" — **correct**

The cost channel pre-empts the material channel entirely. With the cost floor,
the drug lab curtails on cost before running out of leaves — minimum leaf
inventory is 117 (never a physical shortage), but the leaf price reaches
4.92 (2.6×) and yayo price reaches 34.86 (1.66×). Previously, the lab ran
until leaves physically ran out (min stock 24) with yayo peaking at 38.02.

The curtailment is smoother and earlier, which is better economics: the price
signal propagates through cost rather than waiting for physical exhaustion.

## Complete 53-metric comparison

| metric | old | new | delta | delta % |
|---|---:|---:|---:|---:|
| `arbitrage.export_volume` | 12.381259 | 11.0 | −1.381259 | −11.156% |
| `equilibrium.distant_price_range` | 0 | 0 | 0 | n/a |
| `equilibrium.local_price_range` | 0 | 0 | 0 | n/a |
| `glut.distant_trough_day` | 81 | 80 | −1 | −1.235% |
| `glut.distant_trough_price` | 20.415752 | 20.464413 | +0.048661 | +0.238% |
| `glut.local.chemfuel.*` | (all 10) | (unchanged) | 0 | +0.000% |
| `glut.local.psychoid_leaves.*` | (all 10) | (unchanged) | 0 | +0.000% |
| `glut.local_half_recovery_days` | 11 | 9 | −2 | −18.182% |
| `glut.local_half_recovery_quadrums` | 0.733333 | 0.6 | −0.133333 | −18.182% |
| `glut.local_trough_day` | 66 | 66 | 0 | +0.000% |
| `glut.local_trough_price` | 14.340916 | 14.356472 | +0.015556 | +0.108% |
| `producer_loss.capacity_recovery_days` | 75 | 75 | 0 | +0.000% |
| `producer_loss.capacity_recovery_quadrums` | 5 | 5 | 0 | +0.000% |
| `producer_loss.local.chemfuel.inventory_peak` | 119.2 | 119.2 | 0 | +0.000% |
| `producer_loss.local.chemfuel.inventory_peak_day` | 61 | 61 | 0 | +0.000% |
| `producer_loss.local.chemfuel.inventory_trough` | 96.131386 | 96.131386 | 0 | +0.000% |
| `producer_loss.local.chemfuel.inventory_trough_day` | 119 | 119 | 0 | +0.000% |
| `producer_loss.local.chemfuel.price_peak` | 2.442762 | 2.934490 | +0.491728 | +20.130% |
| `producer_loss.local.chemfuel.price_peak_day` | 125 | 210 | +85 | +68.000% |
| `producer_loss.local.chemfuel.price_trough` | 1.918998 | 1.918998 | 0 | +0.000% |
| `producer_loss.local.chemfuel.price_trough_day` | 69 | 69 | 0 | +0.000% |
| `producer_loss.local.chemfuel.terminal_inventory` | 115.688738 | 103.894490 | −11.794248 | −10.195% |
| `producer_loss.local.chemfuel.terminal_price` | 2.378374 | 2.934490 | +0.556116 | +23.382% |
| `producer_loss.local.psychoid_leaves.inventory_peak` | 1568 | 1568 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.inventory_peak_day` | 61 | 61 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.inventory_trough` | 645.255425 | 645.255425 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.inventory_trough_day` | 119 | 119 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.price_peak` | 2.429603 | 2.817404 | +0.387801 | +15.961% |
| `producer_loss.local.psychoid_leaves.price_peak_day` | 125 | 168 | +43 | +34.400% |
| `producer_loss.local.psychoid_leaves.price_trough` | 0.693449 | 0.693449 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.price_trough_day` | 70 | 70 | 0 | +0.000% |
| `producer_loss.local.psychoid_leaves.terminal_inventory` | 1427.549520 | 1425.508582 | −2.040938 | −0.143% |
| `producer_loss.local.psychoid_leaves.terminal_price` | 2.103104 | 2.507273 | +0.404169 | +19.218% |
| `producer_loss.local_peak_day` | 119 | 119 | 0 | +0.000% |
| `producer_loss.local_peak_price` | 38.630290 | 38.630290 | 0 | +0.000% |

## Why the terminal values are still transient

The producer-loss terminal observations (day 210) capture the buffer-rebuild
investment in progress, not the converged state. Extended to day 660:

| day | leaf price / stock | chemfuel price / stock |
|---:|---:|---:|
| 210 (frozen terminal) | 2.507273 / 1,425.509 | 2.934490 / 103.895 |
| 400 | 1.900000 / 1,891.125 | 2.300001 / 151.319 |
| 460 | 1.900000 / 1,891.125 | 2.300000 / 151.319 |

The path converges to reference prices with enlarged stocks. The enlargement
is not a scar — it reflects the higher throughput demand from additional
installed capacity. Each upstream target scales by `throughput_demand ×
target_inventory_days`, and the extra producers add to throughput demand.

## What the model gained

Three properties that were previously absent:

1. **The cost channel.** When input prices rise, downstream producers curtail on
   margin before running out of material. Price signals propagate through cost,
   not just through physical rationing. This is the behavior the original
   docs/07 predictions attributed to the cost floor.

2. **Investment has an opportunity cost.** Capacity is no longer a free ledger
   source. Building requires silver, constraining the scale and pace of
   replacement. 7,397 silver was spent on investment in producer-loss — a real
   draw on the regional pool.

3. **Buffer recovery.** Post-shock inventory scars resolve rather than
   persisting. The system builds temporary surplus capacity, refills buffers,
   and the surplus goes idle under the demand-led control law.

## Reference decision

These changes follow from the documented design in docs/13, resolve the
identified structural gaps (free capacity entry, missing cost floor, permanent
buffer scar), preserve a perfectly stationary equilibrium, and keep all
material and silver ledgers closed. The new behavior is accepted. The
reference should be rewritten in a separate commit.
