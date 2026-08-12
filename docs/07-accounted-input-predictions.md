# Predictions before accounted-input production

These predictions were recorded after freezing the Stage 0 behavioral baseline
and before implementing input-output processes. They are forecasts to compare
against the next model, not acceptance targets and not numbers to tune toward.

## Assumptions

The current `unit_cost` affects a producer's utilization decision, but no
material input is consumed, no operating payment leaves the producer, and
capacity entry consumes no capital good. Production is therefore still a free
ledger source and producers cannot become insolvent or stop for lack of inputs.

The predictions below assume the first accounted-input implementation:

- consumes a real upstream inventory for every unit produced;
- preserves roughly the current normal-equilibrium cost structure;
- permits input shortage to curtail downstream output;
- makes replacement capacity consume an explicit construction fund or capital
  input rather than appearing freely;
- begins from a reasonably stocked, internally consistent equilibrium.

If the first implementation omits the last two assumptions, the producer-loss
predictions in particular should be expected to miss.

## Metric-by-metric forecast

| baseline metric | frozen value | predicted value | direction and reason |
|---|---:|---:|---|
| `arbitrage.export_volume` | 13 units | **10–13** | Flat to moderately lower. Input use reduces the flow of new local surplus while the injected stock still supplies most exports. |
| `equilibrium.distant_price_range` | 0 silver | **0–0.5** | Essentially unchanged if the input chain is initialized consistently; small positive movement is plausible from one-day production and replenishment lags. |
| `equilibrium.local_price_range` | 0 silver | **0–0.5** | Same expectation as the distant region. A range materially above 0.5 would suggest endogenous stock cycling rather than an unavoidable consequence of accounting inputs. |
| `glut.distant_trough_day` | day 82 | **day 79–82** | Unchanged to slightly earlier because fewer shipments should reach the distant market before the spread closes. Route delay still governs most of the timing. |
| `glut.distant_trough_price` | 20.105683 | **20.3–21.0** | Higher and shallower. Lower export volume transmits less of the local glut. |
| `glut.local_half_recovery_days` | 9 days | **5–8 days** | Faster. Curtailed downstream output should consume the injected excess without simultaneously replacing as much of it. |
| `glut.local_half_recovery_quadrums` | 0.6 quadrums | **0.33–0.53** | Same recovery prediction expressed in quadrums. |
| `glut.local_trough_day` | day 67 | **day 64–67** | Unchanged to three days earlier. Accounted costs and input limits should make producer curtailment bite sooner after the price collapse. |
| `glut.local_trough_price` | 12.790741 | **14–16** | Higher and shallower by roughly 1–3 silver because production should contract more decisively during the glut. |
| `producer_loss.capacity_recovery_days` | 75 days | **90–120 days** | Slower by one to three quadrums. Replacement capacity must now wait for and consume real inputs or finance. Failure to recover inside the current 150-day post-shock window is possible. |
| `producer_loss.capacity_recovery_quadrums` | 5 quadrums | **6–8 quadrums** | Same capacity forecast expressed in quadrums. |
| `producer_loss.local_peak_day` | day 119 | **day 130–150** | Later by roughly 11–31 days because constrained entry prolongs the shortage. |
| `producer_loss.local_peak_price` | 38.630290 | **44–54** | Higher by roughly 5–15 silver. Remaining producers can be input-constrained and replacement supply arrives later. |

## Expected pattern

The important prediction is not any single number. It is the contrast between
the two shocks:

- the glut should become **shallower and shorter** because low-price production
  contracts against real costs and inputs;
- the producer-loss shortage should become **higher and longer** because
  productive capacity and its inputs cannot be recreated freely;
- equilibrium should remain close to stationary if the new material circuit is
  initialized coherently.

If both shocks simply become more volatile in the same direction, inspect
stock initialization and process timing before interpreting that as an
economic result.
