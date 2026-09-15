# Endogenous demand and accumulation: design

Written before anything is built or run. Measured in `docs/133`.

## 1. Why, and the decision behind it

`docs/131` §2 ended the scenario work: what still separates our lab
from Wright's signature is two rules he has and we do not. Final demand
in our lab is a constant the scenario author writes down, so GDP cannot
fluctuate; and nothing a producer earns changes what it is allotted
tomorrow, so firm size cannot be a market outcome. The decision taken
was to dock fully before building the mod, on the grounds that a mod
built on a model with a hole in it is a dead end. So this adds the two
rules — gated, bit-identical when off, as every rule since `docs/55` —
and predicts what they do.

They are additions to the ontology and the design says so. Wright's
E1 is an actor spending a uniform share of its money; H1 is a firm
hiring when its money covers a wage; F1 is a firm firing what its money
cannot cover. Ours are the same three things said in our terms: the
owners' fund spending a share of its silver, a producer building
capacity out of retained earnings, and plant that wears unless the purse
replaces it.

## 2. Rule one: the fund spends a share of its silver

`fund_spending_rate: float = 0.0`. When positive, each region's final
demand is scaled daily so that the money value of the day's authored
basket equals `rate × region.cash`:

    scale = rate × cash / Σ_final base_i × price_i
    demand_i = base_i × scale × (price elasticity term, unchanged)

The scale enters `Region.daily_demand` and the final-demand term of
`Region.throughput_demand`, so the plan's inventory targets follow the
money and not only the day's purchases. At `scale = 1.0` the multiply
is exact and the rule is invisible; a scale is only computed when the
rate is positive. The battery seeds the rate from the initial state so
that day one's demand equals the authored demand:
`rate = Σ base_i × price_i / cash` at construction.

The circuit this closes: the fund is paid distributions and pays for
final goods; workers are paid wages and buy the basket; producers
receive both and pay wages and inputs. Money value of final demand is
then a *flow out of a stock*, which is what Wright's E1 is, and it will
fall when the fund is drained and rise when distributions arrive.

**Amended before the sweep (see `docs/133` §1).** The first build
scaled the authored *quantities* and kept each good's price elasticity
of 0.8. Traced on one seed, two final goods in short supply raised
their posted prices, and because their own demand was inelastic they
drew the fund's fixed money into themselves: the authored value rose
3.7× while the median final price fell, and every other final good's
demand fell to 0.27 of authored. The rule as built therefore splits the
fund's money by each good's value share at seeding and buys
`share × money / price` of it — unit elasticity per good, so a scarce
good's price rise reduces the *quantity* it takes and not the money the
rest get. `demand_scale` is kept as the ratio of today's money to the
authored value at seeding, for the record. Predictions unchanged.

## 3. Rule two: accumulation, and wear

`accumulate: bool = False`, with `retention_rate: float = 0.5`. Under
`producer_cash`, for a process with **no bill of materials** (which is
every synthetic process; processes with a bill already wear and are
replaced by `docs/36`–`docs/38` and are untouched):

- **Wear.** Plant wears at `1 / capital_service_life_days` a day. Its
  replacement costs `capacity × unit / life`, where `unit` is the same
  construction unit `_invest` uses for a bill-free process,
  `effective_unit_cost × construction_cost_multiplier`. The purse pays
  what it can; the unpaid fraction of the day's wear is shed, through
  the existing `capacity_lost` book. This is F1: what the money does not
  cover is lost.
- **Accumulation.** In `_settle_purses`, `retention_rate` of the excess
  above the working-capital target is built into the producer's own
  capacity at the same unit, immediately, and the rest is distributed
  as before. This is H1: a firm grows out of what it earns, and — as
  `docs/131` §1 measured — the order book already allots by capacity,
  so growth wins custom.
- **Construction is labour.** Both payments go to the region's
  `worker_cash` and are booked in a new `Ledger.construction_wages`,
  by region. A bill-free process has nothing to build a machine out of
  but labour, and paying the silver to workers rather than into the
  `investment_spending` sink is what keeps the money stock constant,
  which Wright's is and which rule one needs. They are *not* booked to
  `wages_paid` or `living_labor`: no ticks of living labour are
  measured for them, the value identity is left exactly as it was, and
  the money wage share of `docs/126` keeps its basis. The battery
  reports the share with and without them.

Investment by the fund (`_invest`) is left as it is. Its sink is small
at the shipped basket (`docs/129` §3) and it is the only source of
entrants, which the firm-size distribution needs.

## 4. Numbered predictions

All two-sided. The configuration is `docs/131`'s: `k = 4`,
`DEMAND = 800`, twenty seeds, thirty months. Design-time baselines from
one seed of that configuration with both rules off: GDP growth std
**0.019**, firm growth std **0.22**, money wage share **0.010**.

1. **Bit-identical off.** Baseline 322 at zero, fixtures unchanged bar
   `scale_647_day3`, and the battery with both rules off reproduces
   `docs/131`'s one-seed reading, 867 employing at day 180.
2. **Money is conserved with both rules on.** `cash_balance` stays
   within **1e-6 × M** over the thirty months.
3. **Rule one alone makes GDP move.** GDP growth std in
   **[0.03, 0.30]**, and the fund's cash at the end of the window is
   in **[0.2, 0.95]** of M — neither drained nor hoarded.
4. **Rule two alone makes size a market outcome.** Sector CV in
   **[0.2, 3.0]** (was 0.0000) and cost rank ρ in **[−1.0, −0.5]**: the
   cheaper producer is now the larger one by a margin that is not
   rounding.
5. **Both: firm growth becomes accumulation.** Growth std in
   **[0.05, 0.50]** and excess kurtosis in **[1, 40]** (was 118): the
   on-off inventory signature gives way to a series with a body.
6. **Both: the exponent settles.** Across twenty seeds the MLE's
   `x_min` spans a factor in **[1, 20]** (was 408) and the median α
   lands in **[0.5, 2.5]**. Whether it is Wright's ~1 is not predicted;
   that there is a tail to fit is.
7. **Both: demises rise.** Rate per firm-month in **[0.005, 0.10]**
   (was 0.0029): wear now kills.
8. **Both: the wage share keeps its basis.** Production wages over
   value added in **[0.008, 0.020]**; with construction wages added,
   in **[0.010, 0.050]**.
9. **Both: GDP growth kurtosis** in **[0, 10]**. Laplace is 3. A reading
   inside the band with a body of ±0.05 would be the first of Wright's
   growth facts our lab has ever produced.

Predictions 4 and 6 are the substance; 3 and 9 are the ones docking
was for.
