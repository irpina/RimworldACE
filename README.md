# RimworldACE — an economy laboratory

A dependency-free, deterministic simulation of a small commodity economy,
built to make economic rules falsifiable before they go anywhere near a
game. Producers buy inputs, hire workers, make goods, post prices and sell
them; workers spend wages on a subsistence basket; every unit of material,
silver and labor value is booked in a ledger that closes to floating-point
zero. Alongside the model runs a from-the-paper reimplementation of Ian
Wright's *Social Architecture of Capitalism*, a stochastic model of a
capitalist economy that reproduces seven empirical regularities of real
ones. The laboratory has been **docked** with it: the same measuring
instrument, run on both models, gives the same answers wherever a
deterministic economy can be expected to share them, and the differences
are documented rather than tuned away (`docs/136`–`docs/140`).

The project began as a labor-time analysis of the game RimWorld and a
small mod that displays the result. That work is closed and kept, working,
under [`rimworld/`](rimworld/README.md). The laboratory is where the
project is active, and a future game mod will be built from it rather than
the other way round.

## Verifying the Wright results

The laboratory includes the Wright reimplementation, a series of
measurements against it (`docs/111`–`docs/123`), and the docking of our own
model with his (`docs/124`–`docs/140`; the memo is `docs/140`). To check
that work rather than take it on trust:

    python -m economy_lab.verify_wright     # ~60s, no dependencies

Every check recomputes a figure and compares it against what the cited
document claims; a FAIL means a document is wrong. `docs/122` gives the
rest of the audit trail, including where a skeptical reader should push
hardest.

## Layout

| path | |
|---|---|
| `economy_lab/` | The model (`model.py`), its scenarios, the scale ladder, the sensitivity sweep, the Wright reimplementation (`social_architecture.py`), the shared measuring instrument (`wright_battery.py`), the verifier, and the frozen behavioral baseline |
| `economy_lab/data/embodied_labor.csv` | The closed 653-def embodied-labor solve the lab seeds its population from |
| `tests/` | Acceptance and invariant tests, including the pinned fixtures the C# port is verified against |
| `docs/` | Every design and results document, numbered in the order it was written. `01`–`05` belong to the RimWorld spike; everything from `06` on is the laboratory, the port, or the docking |
| `rimworld/` | Everything that touches the game: the research spike, the Labor Content mod, and the Stage 1 runtime shell with its C# port. See [`rimworld/README.md`](rimworld/README.md) |
| `HANDOFF.md` | The running project handoff: decisions made, what not to re-derive, what is next |

## The economy laboratory

`economy_lab/` — a dependency-free, deterministic stock-flow model of a small
economy. It exists so that economic rules can be made falsifiable before UI,
pawn AI, saves, or Harmony complicate debugging. Nothing here touches a
running game.

Two properties are held above everything else: **determinism** (identical
inputs give bit-identical histories) and **ledgers that close to
floating-point zero — material, silver, and value alike**. Every feature below was
designed in a committed document before it was implemented, measured against
a frozen behavioral reference afterward, and the predictions were scored
honestly whether or not they held.

The circuit is six commodities across two regional markets — three goods in
a forking production chain, plus the food, clothing and medicine that
reproduce the workers who make them:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^

provisioning ──> meals ──> the workers who staff all of the above
```

What it models: accounted input-output production; a cost floor that curtails
on margin before material runs out; damped demand-led replenishment; costly,
delayed, capacity-limited arbitrage; capacity investment that consumes a
construction fund; finite resource reserves with ordered grade depletion and
differential rent; the wage relation, with silver cycling producer → wage →
worker → basket purchase → producer; a surplus ledger in work-ticks; labor
values solved endogenously from the process graph; competitive
transmission, where the price anchor reads cost and the order book goes to
the cheaper producer; and fixed capital that transfers its value to the
product, with c, v and s accumulated in work-ticks.

Four quantities are kept strictly distinct and are never collapsed into one
number: **labor value, market price, surplus value, and rent.** Money profit
is not surplus value — a commodity can contain surplus labor and fail to
realize it in a glut.

### Five results worth reading

**1. The endogenous value solve reproduces the closed analysis.** Values
solved from the lab's own process graph agree with the spike's independent
653-def solve (`rimworld/spike/solver.py`) exactly for the two commodities with no modelled inputs
(chemfuel 25 ticks, meals 305), and are high on the two downstream ones by
*precisely* the one link the design documents flagged as stylized — 1.25
ticks on psychoid leaves, 15.00 on yayo. No other discrepancy. That is the
propagation machinery validated against an independent solve rather than
against itself.

**2. The rate of surplus value is now an outcome, not a coefficient.** At
equilibrium **s/v = 38.344**. It does not move when prices do: a subsistence
shock that doubles the meal price and the money wage leaves the labor value
of a meal at exactly 305 and s/v unchanged. It moves when *technique* does: a
provisioning technique with half the living labor lowers the social value of
the wage good, and **s/v rises to 43.944 in both regions — including the one
that adopted nothing** — with the working day and the basket held fixed and
asserted in tests. That is relative surplus value, emerging from the graph
rather than from a parameter. (Both figures are from the meals-only basket
the model carried until `docs/29`; with clothing and medicine in it, s/v is
26.71 and rises to 28.70.)

**3. The overhead is the seam, measured from the inside.** RimWorld's
authored price for a meal is 15 silver. Inputs, wages, and the depreciation
of a real `ElectricStove` account for 0.39 of it; the other **two-thirds of
the price is a wedge the model cannot attribute** to anything. Fixed
capital — implemented from the game's own building costs, repairing an
omission `rimworld/spike/FINDINGS.md` found in vanilla — explains 0.05%. This is the same
seam the research spike found from the outside: authored prices embed a
labor rate far above what the model pays. Every sector performs surplus
labor at the same rate, 38.3, but realizes wildly different amounts of it
in money — 72.6 for chemfuel, 11.2 for yayo — which is the transformation
problem as arithmetic rather than argument.

**4. Value and price answer to different things.** Two deliberately opposite
scenarios, once cost reaches price and the order book goes to the cheaper
producer. A *labor-saving* technique moves the labor value of a meal by
−12.7% and its price by −0.47%. A *capital-saving* one moves the price by
−14.3% and the value by exactly nothing. The rate of surplus value follows
value, not money: it rises in the first case and does not budge in the
second, even though the money wage there falls 14%. Transmission is weak for
labor-saving change for a measured reason — wages are 2–4% of money cost, and
the operating overhead that dominates it is the authored-price wedge: the gap
between RimWorld's `MarketValue` and anything the model can account for.

The classical answer to that wedge is now computed. Folding the subsistence
basket into the input matrix and solving `p = (1 + r)Mp` gives a price system
with no authored magnitude anywhere in it — a uniform profit rate that is an
outcome rather than a coefficient, and Sraffa's basics theorem deciding which
sector's technique can move it.

It was blamed on the meals-only basket, and that was **wrong**. Enlarging the
basket to food, clothing and medicine — every figure from the closed analysis
— cut the rate of surplus value from 38.30 to 26.71 and yayo's deviation from
its authored price from 71.6× to 38.7×, and left both unusable. The real
constraint is RimWorld's own productivity: **one provisioner's working day
feeds 39.3 workers**, so necessary labor is 3.6% of the day and no defensible
bundle changes that by an order of magnitude. The rate of surplus value this
project reports is not a calibration artifact. It is the game's.

**5. Two numbers that were not rates of profit, and now are.** The price
system charged profit against a single day's flow while the model held twenty
days of stock, and the value ledger divided surplus by capital *consumed*
rather than capital *advanced*. Both are fixed: the uniform rate is 1.17 per
day and the old figure survives as the gross markup, while the ledger reports
a rate of profit on advances of 0.0305 per day beside the 1.73 flow ratio.
Uniform turnover moves no relative price — it is a scalar — so the invariance
is asserted bit-exactly, and the circuit turns out to tie its capital up for
**56.8 days rather than 21**, because the finished stock of the final product
appears in no cost flow at all.

### Design and results documents

Each feature has a decision document written *before* implementation and a
results document scoring the predictions afterward.

| doc | |
|---|---|
| **[25-stage0-arc-summary.md](docs/25-stage0-arc-summary.md)** | **Start here: what the laboratory has learned, and what it got wrong** |
| **[44-phase-a-arc-summary.md](docs/44-phase-a-arc-summary.md)** | **Then here: closing the last holes, and the proxy that keeps failing** |
| [06-stage0-economy-lab.md](docs/06-stage0-economy-lab.md) | The laboratory's purpose and shape |
| [07](docs/07-accounted-input-predictions.md) · [08](docs/08-accounted-input-design.md) · [09](docs/09-accounted-input-results.md) | Accounted input-output production: joint products by mass, proportional rationing, simultaneous production |
| [10](docs/10-upstream-observation-results.md) · [11](docs/11-upstream-production-control.md) · [12](docs/12-upstream-production-control-results.md) | The upstream hysteresis bug and the damped demand-led control that fixed it |
| [13](docs/13-cost-floor-and-investment-design.md) · [14](docs/14-cost-floor-and-investment-results.md) | Cost floor, construction-fund investment, buffer-deficit investment |
| [15](docs/15-resource-reserves-design.md) · [16](docs/16-resource-reserves-results.md) | Finite reserves, grade depletion, differential rent |
| [17](docs/17-labor-power-and-surplus-design.md) · [18](docs/18-labor-power-and-surplus-results.md) | Labor-power, the subsistence basket, the wage circuit, the surplus ledger |
| [19](docs/19-endogenous-labor-values-design.md) · [20](docs/20-endogenous-labor-values-results.md) | Endogenous labor values and relative surplus value |
| [21](docs/21-competitive-transmission-design.md) · [22](docs/22-competitive-transmission-results.md) | Competitive transmission: the cost-aware price anchor and the cost-weighted order book |
| [23](docs/23-constant-capital-and-the-overhead-design.md) · [24](docs/24-constant-capital-and-the-overhead-results.md) | Fixed capital, the value ledger, and what the operating overhead actually is |
| [26](docs/26-prices-of-production-design.md) · [27](docs/27-prices-of-production-results.md) | Prices of production: Sraffa's basics, the corn-model profit rate, and the aggregate invariance failure |
| [28](docs/28-enlarged-subsistence-basket-design.md) · [29](docs/29-enlarged-subsistence-basket-results.md) | Clothing and medicine in the basket, and why the constraint was never the basket |
| [30](docs/30-turnover-design.md) · [31](docs/31-turnover-results.md) | Turnover: profit on capital advanced, and the two rates that were not rates |
| [32](docs/32-scale-test-design.md) · [33](docs/33-scale-test-results.md) | The scale test: 647 commodities across 100 regions, and what the runtime port cannot keep |
| [34](docs/34-history-detail-design.md) · [35](docs/35-history-detail-results.md) | Making history optional, and a ledger that was reading its own report |
| [36](docs/36-capital-goods-sector-design.md) · [37](docs/37-capital-goods-sector-results.md) | Department I: machines that are produced, and the nine tenths of the fixed capital that move nothing |
| [38](docs/38-capacity-depreciation-design.md) · [39](docs/39-capacity-depreciation-results.md) | Capacity depreciation and exit: a loss-making sector is disciplined rather than deleted |
| [40](docs/40-recreation-in-the-basket-design.md) · [41](docs/41-recreation-in-the-basket-results.md) | Recreation in the basket: basicness is binary, and its economic weight is not |
| [42](docs/42-absolute-rent-design.md) · [43](docs/43-absolute-rent-results.md) | Absolute rent: Marx's condition holds exactly without fixed capital, and breaks with it |
| [45](docs/45-sensitivity-sweep-results.md) | The sensitivity sweep, re-run: three defects that produced false answers, and what actually matters |

The laboratory's later arcs, each again as a design document with numbered
two-sided predictions followed by a results document that scores them:

| docs | arc |
|---|---|
| [46](docs/46-wage-deviation-design.md)–[52](docs/52-habituation-results.md) | Wages that deviate from the value of labor-power; the lab viewer; habituation |
| [55](docs/55-producer-cash-design.md)–[71](docs/71-the-churn-results.md) | Producer cash, posted prices, procurement, entry on margin, exit on return, the exit floor, sellout after the draw, the churn |
| [53](docs/53-stage1-value-solve-port-design.md)–[54](docs/54-stage1-value-solve-port-results.md), [72](docs/72-stage1-wage-port-design.md)–[96](docs/96-a-review-pass.md) | The C# port of the value, wage, bargaining and price solves, verified to the bit against fixtures the lab writes (the code is under `rimworld/economy_mod/`) |
| [97](docs/97-social-architecture-dock-design.md)–[110](docs/110-the-ablation-grid-results.md) | Docking with Wright's *Social Architecture of Capitalism*: the reference implementation, the producer quantum, the first endogenous firm death, worker mobility, the ablation grid |
| [111](docs/111-fitting-wright-design.md)–[123](docs/123-scrutiny-of-the-wright-work.md) | Fitting Wright's seven facts, goodness of fit, the M1 ablation, the size-exponent sweep, and how to check none of it is fabricated |
| [124](docs/124-wrights-battery-on-our-model-design.md)–[139](docs/139-the-docking-battery-corrected-results.md) | Wright's battery run on our model: a staple sector that feeds its workers, several firms per commodity, endogenous demand and accumulation, the parameter sweeps, and the docking battery |
| **[140](docs/140-what-we-would-put-to-ian-wright.md)** | **The memo: what we would put to Ian Wright** |

### Running it

No dependencies beyond the Python standard library. Everything is
deterministic; a run's history is bit-identical across machines.

```bash
python -m unittest discover -s tests      # ~480 acceptance and invariant tests
python -m economy_lab all                 # every scenario, as JSON
python -m economy_lab technique-change    # relative surplus value
python -m economy_lab cost-competition    # undercutting, and its price effect
python -m economy_lab generous-basket     # the basket, pushed past defensible
python -m economy_lab perishable-meals    # differential turnover: meals rot
python -m economy_lab capital-goods       # Department I: the machines are produced
python -m economy_lab capacity-exit       # competition for survival, not only for orders
python -m economy_lab recreation-basket   # the workers' basket holds the workers' product
python -m economy_lab.baseline            # 322 frozen metrics vs current
python -m economy_lab.scale --sweep       # the size ladder, 6 to 6,470 producers
```

`behavior_baseline.json` freezes 322 behavioral metrics. The baseline reporter
is deliberately a *report*, not a pass/fail test — the invariant tests protect
correctness, while the reporter makes every behavioral change visible and
forces it to be explained before the reference is rewritten.
