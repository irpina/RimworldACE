# Phase A: closing the last holes

A narrative summary of `docs/36` through `docs/43`, written to complement
`docs/25` rather than repeat it. That document covered the laboratory up to
the scale test. This one covers the four sessions that finished the
economics: Department I, capacity depreciation and exit, recreation in the
basket, and absolute rent.

The detailed record is in the design/results pairs. Every feature was
designed in a committed document *before* it was implemented, and every
prediction was scored afterward whether or not it held.

---

## The scoreboard

Four sessions, twenty-three numbered predictions.

| document | right | wrong |
|---|---:|---:|
| `docs/37` Department I | 6 | 1 |
| `docs/39` capacity exit | 3 | 2 |
| `docs/41` recreation | 4 | 2 |
| `docs/43` absolute rent | 3 | 2 |
| **total** | **16** | **7** |

**Every one of the seven wrong predictions produced that session's actual
result.** That is not a coincidence and it is the strongest argument for the
method: a prediction written down before the code is a hypothesis, and a
hypothesis that fails tells you where your model of your own model was
wrong. The right ones confirmed arithmetic; the wrong ones changed what the
project believes.

---

## The one lesson that keeps recurring

**A quantity that is a reliable proxy in one accounting stops being one in
another.** Four instances now, in four different guises:

| where | the proxy | why it failed |
|---|---|---|
| `docs/30` | profit per unit of capital *consumed* stands for the rate of profit | consumed is a flow, advanced is a stock; they differ by the turnover time |
| `docs/37` §3.7 | the value ledger's fixed-capital share stands for the price system's | the ledger's advance is finished goods at value; the price system's is what a producer lays out |
| `docs/39` §5 | the installed plant stands for the plant in the price system | prices of production read the technique at full utilization; the ledger reads the stock |
| `docs/43` | the organic composition stands for the price-value deviation | with fixed capital the markup gains a `K/cost` term, and `K/cost` is not `c/v` |

Each time the two quantities were *related*, *similar in size*, and
*different*. Each time the error was invisible until a number came out wrong
by a factor that could not be explained away — 16× in `docs/37`, a whole
ordering in `docs/43`.

The rule those four add up to: **derive it in the accounting you are using;
do not carry it across.** The project has been scrupulous about keeping
value, price, surplus and rent distinct as *concepts* since the beginning.
The failure mode is subtler: quietly reusing a *ratio* computed in one system
as an estimate in the other.

---

## The result that survived being corrected

`docs/37` §4 is the arc's biggest single finding, and it is the one that
needed the most care afterwards.

Yayo holds **67.3%** of the modelled economy's fixed capital and psychoid
leaves another **22.3%**. Both are non-basic — nothing but yayo consumes
leaves, and nothing at all consumes yayo. So:

| plant present in | `r` |
|---|---:|
| nothing | 1.1725658096440321 |
| the non-basic sectors only (89.6% of the stock) | 1.1725658096434017 |
| the basic sectors only (10.4%) | 0.5182496068869114 |

**Nearly nine tenths of the economy's fixed capital moves the general rate of
profit by 6e-13 — the bisection's own tolerance, which is to say by nothing.**
The whole 56% collapse comes from the other tenth, and a third of *that* from
the stove the workers' meals are cooked on. Sraffa's basic/non-basic theorem,
on real data, with the most expensive machine in the economy sitting on the
inert side of it.

The correction came two sessions later. `docs/37` §8 had written, as its own
what-would-make-this-wrong, that making yayo basic would release that inert
capital and move `r` "a long way". `docs/41` made yayo basic and it does not:
stripping the plant from yayo and leaves then moves `r` by **4.3%**, real
where it had been 6e-13, and nowhere near a long way.

**Non-basic is a veto. Basic is only permission.** How much a sector's plant
then weighs is set by its plant-to-cost ratio, not by the size of its stock.
The sharpest form of it: at **one part in four thousand** of a yayo per
worker-day, every commodity in the model is already basic and `r` has moved
0.07%. A category flipping is not a magnitude changing.

---

## What the model became

Nine commodities where there were six, and the three new ones are not
decoration: steel, wood and components are what the model's own machines are
made of. The six authored fixed-capital constants turned out to be bills of
materials that decompose **to the tick** — `DrugLab` is 75 steel, 50 wood, 6
components and 3,500 ticks of construction work, and 75×47.5 + 50×22.5 +
6×5570 + 3500 is exactly the 41,607.5 the closed analysis measured. Seven of
seven. Department I was not invented; it was the model's own numbers read one
level deeper.

With that:

- **Capital no longer appears from nothing.** Plant is rebuilt out of stock
  at the rate the ledger has charged since `docs/23`, and new capacity
  consumes its bill outright.
- **Fixed capital is in the price system**, closing the omission `docs/26`
  §3.5 and `docs/30` §3.3 both flagged. It is 13.05% of the advance and it
  takes the rate of profit from 1.173 to 0.518.
- **Capacity can be lost**, by exactly the part of a day's wear a
  replacement did not make good. There is no decay rule and no exit rule in
  the code.
- **The basket can include the final good**, which gives the model its first
  self-referential price — yayo's price sits on both sides of yayo's own
  cost equation — and the fixed point handles it without comment.
- **Absolute rent is measured**: 75.7% of chemfuel's value, 229 work-ticks a
  day, with the deviations summing to floating-point zero so that rent can
  only ever be a deduction from surplus value.

Through all of it the equilibrium reports a price range of **exactly zero**
and three ledgers that close.

---

## What the model refuses to do, and why that is the finding

Twice in this arc the honest answer was that a mechanism cannot be built yet,
and both times the blocker was already on the omissions list.

**Absolute rent cannot be a flow** because producers hold no cash and the
region that would pay the rent also owns the reserve. A separate landowner
needs somewhere to spend before rent can move at all, or regional cash drains
until the wage bill fails. So `docs/43` ships a bound and not a payment, and
says so rather than shipping a dead parameter.

**Social labor value still cannot migrate to a superseded technique.** The
handoff had listed competitive exit as the blocker. Exit exists now, and it
turns out to be necessary but not sufficient: a superseded producer with a
positive margin covers its maintenance and never sheds. What is missing is a
cheaper rival driving that margin down.

---

## Three findings about RimWorld, not about the model

**Components do not pay.** `Make_ComponentIndustrial` is 12 steel and 5,000
ticks for one component worth 32 silver. The steel is 22.8 of that, so the
game leaves 9.2 silver for 5,000 ticks of work — 0.00184 a tick against a
subsistence wage of 0.001749. The margin over cost is **1.45%**, and applying
the `docs/08` power stylization takes it to a **loss of 6.12 silver on a
32-silver product.** The stylization was applied rather than exempted: turning
it off would have made the sector profitable, and that would have been the
only reason to turn it off.

**The authored-price wedge shows up on buildings too**, and it is large and
irregular — a drug lab's MarketValue is 12.8% above its bill of materials, a
hand tailoring bench 74.7% above. `docs/24` found this wedge on commodities;
capital goods carry it as well, so deriving a machine's money cost from its
bill *lowers* it by 1% to 40%.

**A per-tick stylization does not survive a fourteen-fold extrapolation.**
The power coefficient was calibrated on a 350-tick recipe and applied to a
5,000-tick one, where it exceeds the entire value added. Recorded rather than
repaired, because repairing it needs a power model and not a coefficient.

---

## Two defects the exactness requirement caught

Both were found because a capital-goods equilibrium refused to be exactly
stationary, and neither was in the new code.

**`_planned_runs` converged on a tolerance, not a fixed point.** It returned
a plan differing from the plan its own input orders were computed from — by
up to 1e-9. Invisible while the input graph was shallow enough to land on the
fixed point in a single step; fixed capital made it cyclic, and the gap
surfaced as steel stock climbing 9e-13 a day. It is exact equality now, and
no metric moved, which says the old models were already landing on the fixed
point and were simply never required to.

**The seeding guard tested a proxy.** It refused any producer below its
full-utilization price ratio. Department I found the case that gets wrong: a
sector priced below the ratio is curtailed but not stopped, and if what it is
curtailed to still clears the circuit's call on it fourteen times over, the
equilibrium is exactly as stationary as before.

Neither would have been found by a test suite that checked residuals to seven
decimal places. **The requirement that the equilibrium's price range be
exactly zero is the most productive constraint in the project**, and the two
times it looked unreachable it was pointing at a real defect rather than at
itself.

---

## Where it goes next

Phase A is finished. What remains in Stage 0 is optional rather than
structural: monopoly rent proper, credit and bankruptcy, producer-level cash,
mothballing, moral depreciation, more than two regions.

The next real work is Stage 1, and it is a different kind of work — porting a
deterministic model into a game runtime, where the constraints are frame time
and save compatibility rather than exactness. `docs/33` measured two of them
already: the daily update must be amortized across ticks, and the history
design must not be inherited.
