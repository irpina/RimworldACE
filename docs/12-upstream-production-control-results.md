# Upstream production control: measured results

This comparison was recorded after implementing the design in `docs/11` and
before rewriting `behavior_baseline.json`. The old reference still described
the known-bug behavior while these numbers were measured.

## Headline

The control law resolves the upstream hysteresis without creating equilibrium
oscillation.

- All 25 tests pass (the prior 23 plus two production-control tests).
- Four-year equilibrium price and inventory paths are exactly stationary for
  all three commodities in both regions.
- Repeated scenarios produce identical histories.
- All material residuals remain around 1e-11 or smaller.
- The glut leaves psychoid stock at exactly 1,600 and chemfuel at exactly 120,
  both at reference price. The former permanent overhang does not form.
- The input-shortage scenario still binds at 56 unmet leaves/day and 24 units
  minimum leaf stock.

Thirty-nine of 53 frozen observations move; fourteen remain unchanged.

## Interpretation

### Glut

The drug lab's current plan becomes the psychoid farm's order. When yayo output
contracts, leaf and chemfuel production contract with it rather than continuing
at capacity. The upstream stocks therefore remain at their pre-shock targets
throughout the scenario instead of accumulating 171.071 leaves and 4.277 fuel.

The same replenishment rule also acts on yayo itself. Excess final stock cuts
planned output more directly, so the local trough is shallower (12.790741 to
14.340916) even though half-gap recovery takes two more whole days. The distant
trough is also shallower, and arbitrage falls 4.76% because less surplus remains
worth exporting.

### Drug-lab capacity loss

The final-good headline is unchanged: price still peaks at 38.630290 on day 119
and capacity still reaches 80% after 75 days. The upstream paths change sharply.

The leaf and chemfuel price crashes become shallower because upstream production
now responds to the lost orders. At the same time, their inventories reach lower
troughs. This is not a contradiction: destroying lab capacity reduces installed
full-capacity throughput, and therefore reduces the materially justified buffer
target. The control drains stock toward that smaller target rather than producing
at full rate into a market that has lost 60% of its immediate productive demand.
As replacement labs arrive, orders and targets rise again.

The producer-loss endpoints are still terminal observations, not equilibria.
Their paths remain in recovery at day 210.

### Input shortage

The scenario still exercises the material constraint:

| observation | result after control |
|---|---:|
| peak unmet leaf demand | 56.0/day |
| minimum leaf stock | 24.0 |
| leaf price maximum | 9.499959 |
| minimum yayo stock | 82.026045 |
| yayo price maximum | 38.016442 |
| final leaf capacity | 79.147436/day |

Output still degrades proportionally rather than shutting off. The change does
not bypass input rationing; it supplies a wanted-output plan for rationing to
constrain.

## Complete 53-metric comparison

| metric | old | new | delta | delta % |
|---|---:|---:|---:|---:|
| `arbitrage.export_volume` | 13 | 12.381259 | -0.618741 | -4.760% |
| `equilibrium.distant_price_range` | 0 | 0 | 0 | n/a |
| `equilibrium.local_price_range` | 0 | 0 | 0 | n/a |
| `glut.distant_trough_day` | 82 | 81 | -1 | -1.220% |
| `glut.distant_trough_price` | 20.105683 | 20.415752 | +0.310069 | +1.542% |
| `glut.local.chemfuel.inventory_peak` | 124.276777 | 120 | -4.276777 | -3.441% |
| `glut.local.chemfuel.inventory_peak_day` | 72 | 61 | -11 | -15.278% |
| `glut.local.chemfuel.inventory_trough` | 120 | 120 | 0 | +0.000% |
| `glut.local.chemfuel.inventory_trough_day` | 61 | 61 | 0 | +0.000% |
| `glut.local.chemfuel.price_peak` | 2.3 | 2.3 | 0 | +0.000% |
| `glut.local.chemfuel.price_peak_day` | 61 | 61 | 0 | +0.000% |
| `glut.local.chemfuel.price_trough` | 2.215520 | 2.3 | +0.084480 | +3.813% |
| `glut.local.chemfuel.price_trough_day` | 180 | 61 | -119 | -66.111% |
| `glut.local.chemfuel.settled_inventory` | 124.276777 | 120 | -4.276777 | -3.441% |
| `glut.local.chemfuel.settled_price` | 2.215520 | 2.3 | +0.084480 | +3.813% |
| `glut.local.psychoid_leaves.inventory_peak` | 1771.071075 | 1600 | -171.071075 | -9.659% |
| `glut.local.psychoid_leaves.inventory_peak_day` | 72 | 61 | -11 | -15.278% |
| `glut.local.psychoid_leaves.inventory_trough` | 1600 | 1600 | 0 | +0.000% |
| `glut.local.psychoid_leaves.inventory_trough_day` | 61 | 61 | 0 | +0.000% |
| `glut.local.psychoid_leaves.price_peak` | 1.9 | 1.9 | 0 | +0.000% |
| `glut.local.psychoid_leaves.price_peak_day` | 61 | 61 | 0 | +0.000% |
| `glut.local.psychoid_leaves.price_trough` | 1.698233 | 1.9 | +0.201767 | +11.881% |
| `glut.local.psychoid_leaves.price_trough_day` | 180 | 61 | -119 | -66.111% |
| `glut.local.psychoid_leaves.settled_inventory` | 1771.071075 | 1600 | -171.071075 | -9.659% |
| `glut.local.psychoid_leaves.settled_price` | 1.698233 | 1.9 | +0.201767 | +11.881% |
| `glut.local_half_recovery_days` | 9 | 11 | +2 | +22.222% |
| `glut.local_half_recovery_quadrums` | 0.6 | 0.733333 | +0.133333 | +22.222% |
| `glut.local_trough_day` | 67 | 66 | -1 | -1.493% |
| `glut.local_trough_price` | 12.790741 | 14.340916 | +1.550175 | +12.120% |
| `producer_loss.capacity_recovery_days` | 75 | 75 | 0 | +0.000% |
| `producer_loss.capacity_recovery_quadrums` | 5 | 5 | 0 | +0.000% |
| `producer_loss.local.chemfuel.inventory_peak` | 167.446333 | 119.2 | -48.246333 | -28.813% |
| `producer_loss.local.chemfuel.inventory_peak_day` | 77 | 61 | -16 | -20.779% |
| `producer_loss.local.chemfuel.inventory_trough` | 121.2 | 96.131386 | -25.068614 | -20.684% |
| `producer_loss.local.chemfuel.inventory_trough_day` | 61 | 119 | +58 | +95.082% |
| `producer_loss.local.chemfuel.price_peak` | 2.178103 | 2.442762 | +0.264659 | +12.151% |
| `producer_loss.local.chemfuel.price_peak_day` | 61 | 125 | +64 | +104.918% |
| `producer_loss.local.chemfuel.price_trough` | 1.086166 | 1.918998 | +0.832832 | +76.676% |
| `producer_loss.local.chemfuel.price_trough_day` | 83 | 69 | -14 | -16.867% |
| `producer_loss.local.chemfuel.terminal_inventory` | 156.123638 | 115.688738 | -40.434900 | -25.899% |
| `producer_loss.local.chemfuel.terminal_price` | 1.666634 | 2.378374 | +0.711740 | +42.705% |
| `producer_loss.local.psychoid_leaves.inventory_peak` | 1793.121599 | 1568 | -225.121599 | -12.555% |
| `producer_loss.local.psychoid_leaves.inventory_peak_day` | 210 | 61 | -149 | -70.952% |
| `producer_loss.local.psychoid_leaves.inventory_trough` | 925.541877 | 645.255425 | -280.286452 | -30.283% |
| `producer_loss.local.psychoid_leaves.inventory_trough_day` | 92 | 119 | +27 | +29.348% |
| `producer_loss.local.psychoid_leaves.price_peak` | 1.762350 | 2.429603 | +0.667253 | +37.862% |
| `producer_loss.local.psychoid_leaves.price_peak_day` | 127 | 125 | -2 | -1.575% |
| `producer_loss.local.psychoid_leaves.price_trough` | 0.488952 | 0.693449 | +0.204497 | +41.824% |
| `producer_loss.local.psychoid_leaves.price_trough_day` | 72 | 70 | -2 | -2.778% |
| `producer_loss.local.psychoid_leaves.terminal_inventory` | 1793.121599 | 1427.549520 | -365.572079 | -20.387% |
| `producer_loss.local.psychoid_leaves.terminal_price` | 1.648383 | 2.103104 | +0.454721 | +27.586% |
| `producer_loss.local_peak_day` | 119 | 119 | 0 | +0.000% |
| `producer_loss.local_peak_price` | 38.630290 | 38.630290 | 0 | +0.000% |

## Reference decision

These changes follow directly from the documented control law, resolve the
specific hysteresis bug, preserve a perfectly stationary equilibrium, and keep
the shortage scenario binding. The new behavior is accepted. The behavioral
reference should therefore be rewritten in a separate commit whose message
states that demand-led replenishment intentionally moved the numbers.
