# Upstream production control: decision before implementation

This decision is recorded before changing the model. It addresses the missing
demand control identified in `docs/10-upstream-observation-results.md`; it does
not add capital goods or make producers pay for inputs.

## Decision

**Use a damped replenishment/order rule alongside the future cash cost floor.**

For each commodity in each region, compute planned output from:

1. the commodity's current intended outflow—final demand plus the inputs local
   producers intend to use today; and
2. a proportional correction that closes part of the gap between opening stock
   and the existing throughput-scaled inventory target.

In notation:

```text
target_stock = target_inventory_days × full-capacity throughput demand
stock_correction = replenishment_rate × (target_stock - opening_stock)
planned_output = clamp(intended_outflow + stock_correction, 0, desired_output)
```

`desired_output` is the producer's existing price/capacity-limited output. The
rule therefore cannot force an unprofitable or capacity-infeasible producer to
run harder than it already would. Input rationing remains a later constraint on
the planned runs.

The new `replenishment_rate` coefficient will be exposed through
`ScenarioParameters`. It is a fraction of the stock gap corrected per day, not
a days-of-cover threshold. The default should be conservative enough that the
seeded equilibrium remains exactly stationary and the proportional feedback
does not manufacture a limit cycle.

## Why the future cost floor does not subsume this

Paying cash for inputs answers two questions:

- can the producer afford the run?
- is expected output revenue sufficient to cover input and operating cost?

It does not answer how many units buyers currently want. A profitable upstream
producer can still buy inputs and manufacture at capacity into an unwanted
stockpile. In the current glut, leaf and chemfuel prices remain above their
full-utilization thresholds even after the overhang forms. Adding an input bill
would change margins but would not guarantee that either price crosses a
curtailment boundary, and tuning it until it does would make inventory control
an accidental property of calibration.

The two controls are therefore complementary rather than duplicated:

- **material replenishment/order control** determines the quantity currently
  called for by demand and desired buffer stocks;
- **cash cost and liquidity control** will determine whether that plan is
  profitable and financeable.

When cash accounting lands, actual output should be the minimum permitted by
the material plan, capacity/price utilization, input availability, and finance.

## Why intended outflow is the order signal

Using downstream producers' intended input requirements makes the process graph
order-driven without abandoning simultaneous production. Every plan is computed
from the day's opening state. Today's upstream output still cannot become
today's downstream input, so the one-day-per-stage propagation decision in
`docs/08-accounted-input-design.md` remains intact and producer list order
cannot affect results.

The mutually dependent plans are solved as a deterministic fixed point, starting
from each producer's existing price/capacity-limited output and iterating
downward until no planned run changes beyond floating-point tolerance. Failure
to converge is an explicit error rather than an order-dependent partial plan.

The downstream requirement must be based on each consumer's current intended
runs, not its full installed capacity. That is the missing signal in the glut:
when the drug lab curtails, the leaf order contracts immediately. Input
availability may later reduce actual runs below intended runs; the existing
single-pass allocation limitation remains, and any unused material stays in
stock for the next day's correction.

## Why the correction is proportional and damped

An order-only rule with no buffer correction would preserve any inherited stock
error forever: output would merely replace current use. The proportional term
gives the inventory target restoring force in both directions:

- excess stock reduces planned output below intended outflow until the excess
  drains;
- deficient stock raises planned output toward the capacity ceiling.

There is no on/off boundary. A smaller gap produces a smaller correction, so
the control approaches the target continuously rather than cycling across a
threshold. Clamping at zero and `desired_output` enforces physical bounds; it is
not a threshold production regime.

The stock target continues to use full-capacity throughput demand. Installed
productive structure therefore determines the desired buffer, while current
orders determine today's replacement flow. This avoids making the target
collapse at the same moment a temporary downstream curtailment occurs.

## Rejected alternatives

### Cost floor as the only control

Rejected because profitability and liquidity do not measure wanted quantity.
It would leave overproduction possible whenever margins remain positive, and it
would make the existence of a restoring force depend on price calibration.

### Price-triggered curtailment

Rejected as the primary fix. The model already has a smooth price-utilization
curve and it failed to remove the overhang because the displaced price remained
above full utilization. Moving or adding a threshold would treat the symptom,
introduce another dominant calibration parameter, and risk discontinuous
stop/start behavior.

### Inventory threshold

Rejected in threshold form. Days-of-cover is the right material state variable,
but a switch at a chosen cover level would invite the same manufactured limit
cycles that led `docs/08` to reject all-or-nothing input rationing. The chosen
rule uses the inventory target continuously instead.

### Pure order-driven production

Rejected without a stock correction. It is faithful to current requirements but
has no mechanism to restore buffers after shocks, losses, or initialization
errors. The chosen rule is order-driven production plus damped replenishment.

## Expected checks

The rule is acceptable only if:

- the four-year equilibrium price range remains exactly zero in both regions;
- the glut's upstream stocks return toward their pre-shock targets rather than a
  permanently displaced stationary point;
- the input-shortage scenario still binds and propagates proportionally;
- producer ordering remains irrelevant;
- all material ledgers close and identical inputs reproduce identical histories.

Any baseline movement must be inspected before the reference is rewritten.
