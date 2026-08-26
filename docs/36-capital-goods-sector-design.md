# A capital-goods sector (Department I): design

Written before implementation. This is the item `docs/26` §3.5, `docs/30`
§3.3 and the handoff's omissions list have all been pointing at: **capital
stock still appears from nothing.** Building capacity spends silver and
consumes no matter; machines wear out in the value ledger and are never
replaced by anything.

Section 2 is the finding that makes the rest cheap, and it was found rather
than assumed.

## 1. Why

Two distinct holes, and they turn out to be one hole.

**The circuit.** `_invest` deducts `amount * assumed_effective *
construction_cost_multiplier` from regional cash and appends a
`CapacityProject`. Nothing is consumed. A region with silver can conjure a
refinery. Meanwhile `_set_capital_consumption` charges every unit of output
a slice of the machine that made it — `capital_money_per_capacity /
service_life_days` — and that slice is subtracted from nobody's stock. The
model both destroys capital that does not exist and creates capital out of
money.

**The price system.** `prices_of_production` omits fixed capital entirely,
and says so, because the machines are exogenous: their money price and
embodied labor are imported from the closed analysis, and a price system has
nowhere to put an authored magnitude without contaminating the answer it
exists to produce. `docs/30` measured what that omission costs and the number
is no longer small — fixed capital is **3.54% of the capital advanced**,
where as a *flow* it was 0.05% of cost. The whole point of moving to
advances was to stop confusing stocks with flows; omitting the largest
stock-shaped item undoes it.

Both holes close the same way: make the machines produced.

## 2. The model's fixed capital is already a bill of materials

The six `*_capital_money` / `*_capital_labor` pairs in `ScenarioParameters`
look like authored constants. They are not. Each is a real RimWorld
building, and each decomposes **exactly** into three produced commodities
plus construction work:

| model's machine | RimWorld def | steel | wood | components | work | sum | authored |
|---|---|---:|---:|---:|---:|---:|---:|
| drug lab | `DrugLab` | 75 | 50 | 6 | 3500 | 41607.5 | 41607.5 |
| psychoid field | `HydroponicsBasin` | 100 | – | 1 | 2800 | 13120.0 | 13120.0 |
| refinery | `BiofuelRefinery` | 150 | – | 3 | 2000 | 25835.0 | 25835.0 |
| provisioner | `ElectricStove` | 80 | – | 2 | 2000 | 16940.0 | 16940.0 |
| tailoring bench | `HandTailoringBench` | – | 75 | – | 2000 | 3687.5 | 3687.5 |
| plant pot | `PlantPot` | – | 20 | – | 250 | 700.0 | 700.0 |

at `Steel = 47.5`, `WoodLog = 22.5`, `ComponentIndustrial = 5570` embodied
ticks. Six of six, to the tick. The drug lab's wood is its `costStuffCount`
of 50 at the cheapest admissible stuff, which is what the closed analysis's
solver picks and is why the first attempt at this table was short by exactly
1125 ticks.

**So there is nothing to invent.** Department I is not a new stylization
bolted onto the model; it is the model's own fixed-capital figures read at
one more level of resolution.

The money column does *not* decompose, and that is the second finding:

| machine | bill at market prices | authored MarketValue | wedge |
|---|---:|---:|---:|
| drug lab | 394.5 | 445.0 | +12.8% |
| psychoid field | 222.0 | 230.0 | +3.6% |
| refinery | 381.0 | 390.0 | +2.4% |
| provisioner | 216.0 | 225.0 | +4.2% |
| tailoring bench | 90.0 | 157.2 | +74.7% |
| plant pot | 24.0 | 40.9 | +70.4% |

This is `docs/24`'s authored-price wedge again, on capital goods, ranging
over more than an order of magnitude. Deriving the money side from the bill
therefore *changes* it, and the results document must report by how much
rather than let it pass as a refactor.

## 3. Design

### 3.1 Three commodities, read off the game

| commodity | RimWorld | direct labor | inputs | fixed capital |
|---|---|---:|---|---|
| `steel` | `MineableSteel` | 47.5 | – | none |
| `wood` | `WoodLog` | 22.5 | – | none |
| `components` | `Make_ComponentIndustrial` | 5000 | 12 steel, 2.857 chemfuel | machining table |

Steel and wood are extraction: hand labor against a deposit or a tree, with
no building, which is true of the game and keeps the two goods at the bottom
of the value graph where a productive matrix needs them.

Components are manufactured at a `TableMachining` — 150 steel, 5 components,
3000 work, 37975 embodied ticks — so Department I owns its own means of
production, which is the property that makes it Department I rather than a
third consumer-goods sector.

The 2.857 chemfuel is the *fourth* use of the `docs/08` power stylization
(0.2 chemfuel per 350 ticks of bench time) and is derived, not chosen:
`0.2 * 5000 / 350`. Applying it here rather than exempting Department I is
what stops the new sector from being quietly cheaper than the old ones.

### 3.2 Fixed capital becomes a bill, and the scalars become derived

`Process` gains

```python
capital_bill: Dict[str, float]        # commodities per machine
capital_construction_labor: float     # ticks per machine
machines_per_capacity: float          # machines per unit of daily capacity
```

and the two existing scalars stay as the fallback. **An empty bill is
bit-identical to today**, which is the same compatibility rule fixed capital
itself shipped under in `docs/23`.

Where a bill is present:

```
capital_labor_per_capacity  =  m * (sum_j bill[j]*lambda[j]  +  construction_labor)
capital_money_per_capacity  =  m * (sum_j bill[j]*p[j]       +  construction_labor*w)
```

Both are now endogenous. `lambda` comes from the value solve, which is
already a fixed point and simply gains a term; `p` and `w` are regional, so
a machine costs what machines cost *there*, which is the first time the
model has had a regional capital cost at all.

The value solve becomes circular through fixed capital — components need a
machining table which needs components — and that is correct rather than a
problem. The iteration already handles a cyclic graph; this is what it was
written for.

### 3.3 Replacement is a flow of matter, not a decay of capacity

This is the load-bearing decision, and the first draft of this design got it
wrong.

The obvious move is to let capacity depreciate — `capacity -= capacity/L`
each day — and let `_invest` rebuild it. It does not survive contact with
the model. Capacity decays continuously; investment is episodic, gated on a
margin threshold, a minimum size and an investment interval. A continuous
sink against a lumpy source cannot reproduce itself exactly, and the
equilibrium scenario must report a price range of exactly zero.

The correct move is smaller and truer to what the model already asserts.
`capital_consumed_per_unit` **already charges** every unit of output
`bill/L` of machine, in money and in labor, and has since `docs/23`. That
charge is currently a fiction: nothing is deducted from anything. Making it
real means consuming `m * bill[j] / L` of commodity *j* per unit of output,
from regional inventory, in `_produce`.

Capital is then replaced in place, physically, at exactly the rate the
ledger has always said it wears out. Capacity is untouched, so the
stationary state stays stationary: constant capacity implies a constant
replacement draw, which is an ordinary constant input flow like chemfuel
into leaves.

It is also use-based rather than time-based, for the reason `docs/23` gave:
idle plant must not feed a rising unit cost back into the price anchor.
Time-based depreciation belongs with mothballing and exit, which is still
the next item and is still not this one.

### 3.4 Construction consumes the bill at installation

New capacity consumes `amount * m * bill[j]` outright, plus
`amount * m * construction_labor` of living labor, and the silver deducted
is that bill at regional prices rather than
`assumed_effective * construction_cost_multiplier`.

`construction_cost_multiplier` therefore stops governing anything where a
bill exists. It is not deleted: it still governs bill-free processes, which
is every scenario that does not opt in.

Capacity that cannot be built for want of matter is **not** built. A region
short of components does not get a refinery, which is the entire point.

### 3.5 Fixed capital enters the price system

With the machines produced, `docs/26` §3.5 and `docs/30` §3.3 both expire.
Per unit of output, let `c_i = M_i.p` be circulating cost and `K_i.p` the
fixed capital stock supporting it. Then

```
cost_i     =  c_i + K_i.p / L
advance_i  =  tau_i * cost_i  +  K_i.p
p_i        =  cost_i  +  r * advance_i
```

Depreciation in the cost, the whole undepreciated stock in the advance. It
reduces to today exactly when `K = 0`, and each entry is still
non-decreasing in `r`, so the existing bisection still has a unique root.

Note what this does to the closed form: turnover is no longer a scalar even
when `tau` is uniform, because `K_i/c_i` differs by sector. The uniform-tau
short-circuit added in `docs/30` §3.2 stays — it is still exact where there
is no fixed capital — but a bill-carrying economy will take the bisection
branch. **Bit-exactness of the existing scenarios is preserved because they
have no bill; the new one does not claim it.**

### 3.6 Deliberately not done

- **Capacity decay, mothballing and exit.** Still the next item, for the
  reason in §3.3. Nothing here makes it easier or harder.
- **The buildings as commodities.** Six more commodities to model six
  machines, when three materials plus a construction-labor coefficient
  carries the same information. The cost is that a machine cannot be traded
  or held in inventory, which no scenario asks for.
- **Steel and wood as depletable reserves.** `ResourceReserve` exists and
  would fit, but grade transitions are a separate result and would confound
  this one.
- **Construction as a sector with its own capacity.** Construction labor is
  living labor performed at installation, drawn from the regional pool. A
  builder with a capacity constraint is a queueing model, not a value model.

## 4. Interface

```python
ScenarioParameters(capital_goods=True)     # opt in; default False is today
scenarios.capital_goods()                  # the new scenario
economy.department_one_output()            # gross output of Dept I, per region
economy.capital_bill_draw(region)          # replacement draw, per commodity
prices_of_production()["fixed_capital_share"]   # K.p / advance, aggregate
```

Every coefficient exposed: `steel_direct_labor`, `wood_direct_labor`,
`component_direct_labor`, `steel_per_component`, `chemfuel_per_component`,
`machining_table_bill`, and the six building bills.

## 5. Tests

1. Each of the six bills reproduces its authored `*_capital_labor` to the
   tick at the authored input values. This is §2 as an executable check, so
   the table cannot rot.
2. An empty bill is bit-identical: every existing metric unmoved.
3. Matter is conserved. `commodity_balance` must close for steel, wood and
   components with the replacement draw and construction draw counted.
4. Capacity cannot be built without the bill in stock.
5. The value solve converges with the components/machining-table cycle, and
   `lambda_components` exceeds the authored 5570 by the fixed capital the
   closed analysis omits.
6. The capital-goods equilibrium reports a price range of **exactly zero**.
7. `prices_of_production` with `K = 0` reproduces today's profit rate
   exactly, through the new code path.
8. Department I's gross output is positive in the stationary state — the
   property without which none of §3.5 is defined.

## 6. Predictions

Written before the code, so they can be wrong in public.

**6.1 Department I is a rounding error in the flow and is not in the stock.**
Replacement is 0.18% of direct labor (measured: 12.37 ticks of Department I
labor plus 1.63 of construction, against 7620.79 a day in one region). The
stationary draw is 0.0678 steel, 0.0125 wood and 0.00177 components a day.
So the new sectors will change nothing anybody can see in the flow accounts,
and everything in the advance.

**6.2 `lambda_components` = 5654.7, against 5570 authored: +1.52%.** The gap
is exactly the fixed capital RimWorld's formula omits (`FINDINGS.md`,
`docs/23`), arriving one level deeper than before.

**6.3 The drug lab's embodied labor rises to 42115.7, +1.22%,** and every
other machine by less, because only their components carry fixed capital.
Steel and wood will solve to 47.5 and 22.5 exactly, since they are pure
labor with nothing behind them.

**6.4 The rate of profit falls by about 3.4%, from 1.17257 to about 1.132.**
Profit is essentially unchanged (6.1) while the advance grows by the 3.54%
`docs/30` measured. This is the headline: the model has been overstating
`r` by three and a half percent since `docs/27`, and it said so at the time.

**6.5 The basics go from four to seven.** Currently `{chemfuel, garments,
herbal_medicine, meals}`. Steel, wood and components join — not because they
enter every technique directly (steel does not enter herbal medicine at all)
but through the wage bundle: steel enters the provisioner's stove, the stove
enters meals, and meals enter every sector that employs labor. Leaves and
yayo stay non-basic, because nothing consumes them but yayo and final demand.

**6.6 The money side moves more than the labor side.** Deriving
`capital_money_per_capacity` from the bill removes an authored wedge of
+2.4% to +74.7%, so the *money* value of the fixed capital stock falls
noticeably while its *labor* value rises slightly. The two moving in
opposite directions is the prediction; if they move together, something is
reading the same number twice.

**6.7 The uniform-turnover closed form will no longer fire** for the
capital-goods scenario, and `iterations` will jump from the power-iteration
count to the bisection's. Existing scenarios keep the closed form and stay
bit-exact.

## 7. What would make this wrong

- **If the six bills do not reproduce the authored labor exactly**, §2 is a
  coincidence and the whole design rests on nothing. Test 1 first.
- **If the value solve fails to converge**, the components/machining-table
  cycle is not productive at these coefficients — components would consume
  more of themselves, directly or indirectly, than they produce. At
  `m * bill = 0.2083 * 5 = 1.04 components` per unit of daily capacity, or
  0.0017 per unit of output, it is nowhere near, but it is the failure this
  design invites and it must fail loudly.
- **If the equilibrium price range stops being exactly zero**, stop and
  report. Do not loosen the check, and do not tune a coefficient until the
  forecast comes true.
- **If `r` falls by much more than 3.5%**, the advance is being
  double-counted — most likely by charging `r` on the fixed capital stock
  *and* on the turnover-inflated depreciation flow. `docs/29` §10 made
  exactly this class of error and `docs/30` §7.1 had to correct it.
