# A capital-goods sector (Department I): results

`docs/36` designed it, made seven numbered predictions, and named the one
error that would invalidate the whole thing. Six predictions were right,
several to four significant figures. One was wrong by a factor of sixteen,
and chasing it down produced the result that matters more than anything the
design anticipated.

## 1. What shipped

Nine commodities instead of six. Steel and wood are extracted, components are
made from steel at a machining table which is itself made of steel and
components, and every sector's plant is rebuilt out of that stock at exactly
the rate the ledger has charged since `docs/23`. Capacity construction
consumes the bill outright. Fixed capital is in the price system.

The capital-goods equilibrium reports a price range of **exactly zero** across
all nine commodities in both regions over four years, and all three residuals
close. `capital_goods()` is the scenario; ten metrics are frozen.

Two things had to be corrected on the way and neither was tuning; §5 covers
them.

## 2. The bills of materials: confirmed, seven of seven

`docs/36` §2's table was the load-bearing claim and §7 said to test it first.
Every one of the six machines, plus the machining table Department I needs for
itself, reproduces its authored embodied labor **to the tick** at
`Steel = 47.5`, `WoodLog = 22.5`, `ComponentIndustrial = 5570`:

| machine | bill + work | authored |
|---|---:|---:|
| drug lab | 41607.5 | 41607.5 |
| psychoid field | 13120.0 | 13120.0 |
| refinery | 25835.0 | 25835.0 |
| provisioner | 16940.0 | 16940.0 |
| tailoring bench | 3687.5 | 3687.5 |
| plant pot | 700.0 | 700.0 |
| machining table | 37975.0 | 37975.0 |

It is a unit test now, so the table cannot rot silently.

## 3. The predictions

### 3.1 Right: 6.1, the size of Department I

Predicted 0.1837% of direct labor. Measured **0.1837%** — 12.39 ticks of
Department I labor plus 1.63 of construction, against 7633.84 a day in one
region. The stationary draw was predicted at 0.0678 steel, 0.0125 wood and
0.00177 components a day; it is 0.0679580, 0.0125104 and 0.0017765.

### 3.2 Right: 6.2, the components gap

Predicted `λ_components = 5654.7`, +1.52% over the authored 5570. Measured
**5654.891129**, +1.5241%.

The gap is the fixed capital RimWorld's formula omits, arriving one level
deeper than `docs/23` found it. Steel and wood solve to **exactly** 47.5 and
22.5 — pure labor with nothing behind them, and if they ever move, fixed
capital has leaked into a sector that has none. Both are frozen for that
reason.

### 3.3 Right: 6.3, the machines

Predicted the drug lab at 42115.7, +1.22%. Measured **42116.85, +1.2242%**.
Every other machine moved by less, and the two made only of wood did not move
at all:

| machine | labor, derived | authored | | money, derived | authored | |
|---|---:|---:|---:|---:|---:|---:|
| drug lab | 42116.85 | 41607.5 | +1.22% | 400.62 | 445.0 | −9.97% |
| machining table | 38399.46 | 37975.0 | +1.12% | 450.25 | 455.0 | −1.04% |
| provisioner | 17109.78 | 16940.0 | +1.00% | 219.50 | 225.0 | −2.45% |
| refinery | 26089.67 | 25835.0 | +0.99% | 384.50 | 390.0 | −1.41% |
| psychoid field | 13204.89 | 13120.0 | +0.65% | 226.90 | 230.0 | −1.35% |
| tailoring bench | 3687.50 | 3687.5 | 0.00% | 93.50 | 157.2 | −40.52% |
| plant pot | 700.00 | 700.0 | 0.00% | 24.44 | 40.9 | −40.25% |

### 3.4 Right: 6.6, the two sides move in opposite directions

That table is also prediction 6.6, and it holds in both halves: labor rises by
0 to 1.22% while money falls by 1.04% to 40.52%. The labor side rises because
components carry fixed capital the closed analysis omitted; the money side
falls because the authored MarketValue of a building carries `docs/24`'s wedge
over its own bill of materials, and deriving it removes that wedge. The
prediction said that if the two moved *together*, something was reading the
same number twice. They did not.

### 3.5 Right: 6.5, four basics become seven

`{chemfuel, garments, herbal_medicine, meals}` becomes
`{chemfuel, components, garments, herbal_medicine, meals, steel, wood}`, and
for exactly the reason predicted: steel does not enter herbal medicine at all
— the plant pot is wood — but steel enters the provisioner's stove, the stove
enters meals, and meals enter every sector that employs labor. Leaves and yayo
stay non-basic. §4 is what that turned out to be worth.

### 3.6 Right: 6.7, the closed form stops firing

Uniform turnover stops being a scalar once `K_i/c_i` differs by sector, so the
`docs/30` §3.2 short-circuit is skipped and the bisection runs. Iterations go
from 13 to 26. Existing scenarios keep the closed form and stay bit-exact,
which the whole 154-metric reference confirms.

### 3.7 Wrong, by a factor of sixteen: 6.4, the rate of profit

Predicted a fall of about 3.4%, from 1.17257 to about 1.132.

**Measured 0.5182496069 — a fall of 55.80%.**

`docs/36` §7 said this exact outcome means the advance is being double
counted, so that was tested before anything else was believed. It is not.
`p_i = cost_i + r·advance_i` holds **sector by sector** to 2.6e-13 across all
nine, with depreciation once in the cost and the standing stock once in the
advance. That check is now a test, written per-sector rather than in aggregate
precisely because an aggregate can be made to balance by a compensating error.

The prediction was wrong for a reason worth stating plainly, because it is a
reasoning error and not an arithmetic one.

**I predicted the price system's answer from the value ledger's number.**
`docs/30` measured fixed capital at 3.54% of capital advanced and I assumed
the price system would see the same share. It does not, and the two are not
measuring the same thing. The ledger's advance is dominated by finished-goods
inventory valued at labor value — 200 units of yayo at 736 ticks is 147,200
ticks of it. The price system's advance is what the producer actually lays
out: inputs plus wages, held for `τ` days. Because wages are 3.6% of the
working day (`docs/28`), that outlay is tiny — **chemfuel's circulating cost
is 2.4% of its own production price**, since chemfuel is pure labor and
almost none of that labor is paid for. Fixed capital measured against an
outlay that small is enormous:

| sector | circulating cost | plant `K·p` | `K/cost`, days | `τ`, days |
|---|---:|---:|---:|---:|
| chemfuel | 0.1442 | 8.1310 | 56.4 | 21 |
| meals | 1.7592 | 65.3531 | 37.1 | 21 |
| components | 85.3037 | 2642.09 | 31.0 | 21 |
| psychoid leaves | 0.5709 | 5.3457 | 9.4 | 21 |
| yayo | 80.5199 | 218.066 | 2.7 | 21 |
| garments | 14.9802 | 8.5860 | 0.6 | 21 |
| herbal medicine | 2.3072 | 0.5381 | 0.2 | 21 |
| steel, wood | — | 0 | 0 | 21 |

The plant is **13.05% of the price system's advance**, not 3.54%. And the fall
is larger than even that share implies, because meals is a wage good: its
production price nearly triples, so the wage per tick doubles from 0.002631 to
0.005768, so every sector's cost rises, so `r` falls again. Removing the plant
from meals alone recovers `r` to 0.712904 — 30% of the whole fall from one
sector that is 2.4% of the fixed capital stock.

The high-level lesson: **a share measured in one accounting does not transfer
to another.** The project has been careful to keep value and price apart
everywhere else, and then I estimated one from the other anyway.

## 4. The result nobody predicted: 89.6% of the fixed capital does nothing

The three new sectors, on their own, move the rate of profit by
**+0.0000%** — identical to twelve figures. They are non-basic until the plant
makes them basic, and a non-basic sector cannot touch `r`. That was the first
thing checked when the number looked wrong, and it is frozen as a metric so it
stays true.

Pushing on that produced the real finding. Yayo holds **67.3%** of the
economy's fixed capital and psychoid leaves another **22.3%** — 89.6% between
them — and both are non-basic. So:

| plant present in | `r` |
|---|---:|
| nothing | 1.1725658096440321 |
| the non-basic sectors only (89.6% of the stock) | 1.1725658096434017 |
| the basic sectors only (10.4% of the stock) | 0.5182496068869114 |
| everything | 0.5182496069 |

**Nearly nine tenths of the economy's fixed capital moves the general rate of
profit by 6e-13, which is the bisection's own tolerance — that is, by
nothing.** The entire 56% collapse is produced by the remaining tenth, and
most of that tenth by the stove behind the meals in the workers' basket.

This is Sraffa's basic/non-basic theorem, and the project has not seen it bite
before because until now there was nothing in the model whose distribution
between basic and non-basic sectors was so lopsided. `docs/27` computed the
basics as an observation. This is what the observation was for.

It also says something about the model's subject. The drug lab is the most
expensive machine in the economy and the largest single block of capital in
it, and it is economically inert with respect to distribution: what a drug
cartel invests in its own plant cannot change the general rate of profit,
because nobody's production requires yayo. What can change it is the stove
the workers' meals are cooked on.

## 5. Two defects found on the way

Both were found because the capital-goods equilibrium refused to be exactly
stationary, and neither was a Department I bug.

### 5.1 The run plan converged on a tolerance, not on a fixed point

`_planned_runs` stopped once no run moved by more than `EPSILON`, and returned
a plan that differed from the plan **its own input orders had been computed
from**. Invisible while the input graph was shallow enough to land on the
fixed point in a single step. Fixed capital makes it cyclic, the loop began
stopping one iterate early, and the gap showed up as steel stock climbing
9e-13 a day in an equilibrium that is supposed to be exact to the bit.

It converges on exact equality now, in nine iterations. **No existing metric
moved**, which says the old models were already landing on the fixed point —
they were simply never required to.

### 5.2 The seeding guard tested a proxy

`_assert_reference_full_utilization` refused any producer below its
full-utilization price ratio, on the grounds that a curtailed producer would
silently break the stationary equilibrium. That is a proxy, and Department I
found the case it gets wrong: a sector priced below the ratio is curtailed but
not *stopped*, and if what it is curtailed to still clears the circuit's call
on it by a wide margin, the equilibrium is exactly as stationary as before.

It tests the property the proxy stood for now — the runs a producer's
utilization permits must cover the runs the stationary circuit asks of it —
and its docstring names what it still does not catch, which is a producer
whose capacity is below its own draw. The old check did not catch that either;
saying so beats claiming an improvement that was not made.

## 6. A finding about RimWorld's prices: components do not pay

The case that exposed §5.2 is worth reporting on its own terms.

`Make_ComponentIndustrial` is 12 steel and 5000 ticks of work for one
component worth 32 silver. The steel is 22.8 of that, so RimWorld leaves
**9.2 silver for 5000 ticks** — 0.00184 silver a tick, against a subsistence
wage of 0.001749 a tick. So the wage bill is 8.74 and the whole cost is
31.54: the margin is **1.45% of cost**, against the 5% the full-utilization
convention wants.

Apply the `docs/08` power stylization — 0.2 chemfuel per 350 ticks of bench
time, the same coefficient the tailoring bench uses — and it costs 6.57 silver
on a 5000-tick recipe. That is more than the entire 9.2-silver margin: cost goes to 38.12 against a
price of 32, so the sector **loses 6.12 silver on every 32-silver component**
at RimWorld's own authored prices.

The stylization was **applied, not exempted.** Turning it off would have made
the sector profitable, and the only reason to turn it off would have been to
make the sector profitable, which is the one thing the project's rules forbid.
So components run loss-making, at 39.9% utilization, demand-constrained at
fourteen times the circuit's call on them, and the equilibrium is exact
regardless. `Producer.unattributed_margin` has said since `docs/23` that a
negative margin is a finding about the authored price rather than an error;
this is the largest one yet.

What it shows is that the stylization does not extrapolate. It was calibrated
on a 350-tick recipe and applied to one fourteen times longer, and at that
range a linear per-tick power draw exceeds the whole value added. Recorded
here rather than repaired, because repairing it needs a power model, not a
coefficient.

## 7. What is still missing

- **Capacity decay, mothballing and exit** — still the next item, and
  `docs/36` §3.3 explains why it had to stay out: a continuous sink against
  episodic investment cannot reproduce itself exactly. The consequence is
  that a replacement shortfall is *not* throttled. A region that cannot
  replace its machines runs them into the ground and the model does not
  notice, because noticing is precisely capacity decay.
- **New plant's value is not booked.** Replacement closes on both sides —
  the plant consumed transfers `K/L`, the plant rebuilt takes materials as
  circulating capital and construction labor as living labor, and the two
  cancel, which is why `value_balance` still closes at 2e-8. *New* capacity
  draws its materials (so the material identity closes) but its value is not
  credited anywhere, because the model keeps no plant stock account. Named
  rather than hidden.
- **Construction labor for new capacity is bought, not employed.** It is
  paid for in silver at the region's wage and does not enter the labor pool.
  Replacement construction labor does. The asymmetry exists because
  `_invest` runs after employment has been quantized for the day.
- **Steel and wood are inexhaustible.** `ResourceReserve` would fit and was
  deliberately left out so grade transitions do not confound this result.

## 8. What would make this wrong

- If `p_i = cost_i + r·advance_i` ever stops holding sector by sector, the
  advance is double counted and §3.7's number is worthless. It is a test.
- If `λ_steel` or `λ_wood` moves off 47.5 or 22.5, fixed capital has leaked
  into a sector that has none. Both are frozen.
- If the three new sectors ever move `r` on their own, the fall is coming
  from somewhere other than the plant. Frozen as
  `capital_goods.production.basics` and the labor share beside it.
- §4's claim rests on yayo and leaves staying non-basic. If anything ever
  consumes yayo as an input, 89.6% of the fixed capital stops being inert and
  the rate of profit moves a long way. That is a prediction, and it is the
  first thing to check if a later scenario makes yayo an input to anything.
