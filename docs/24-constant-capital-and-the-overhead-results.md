# Constant capital, and what the operating overhead actually is: results

Recorded after implementing the design in
`docs/23-constant-capital-and-the-overhead-design.md`.

## Headline

The operating overhead has an economic interpretation now, and it is not a
flattering one: **it is the gap between RimWorld's authored price level and
anything the model can account for.** Fixed capital explains 0.05% of it.

- All 97 tests pass (84 prior + 13 for the value ledger and the price
  decomposition).
- **No behavioral metric moved.** Not one price, inventory, capacity,
  employment, or recovery-day figure. Capital consumption is carved *out of*
  `unit_cost` rather than added to it, so the utilization curve sees the same
  float it saw before.
- Fifteen value observations moved: labor values up 0.09–0.19%, the rate of
  surplus value down 0.12%.
- A **third closing ledger** joins material and silver: the value of output
  equals c + v + s to floating-point zero.
- The classical magnitudes are computable for the first time: organic
  composition **20.67**, value rate of profit **1.77**, s/v **38.30**.

## 1. Fixed capital: implemented, and negligible

`FINDINGS.md` recorded that RimWorld's formula transfers no value from fixed
capital — a workbench contributes nothing to what it produces. The model now
does transfer it, using each sector's real building from the closed analysis.

The predicted magnitudes held exactly:

| sector | building | depreciation (silver) | % of cost | (ticks) | % of living labor |
|---|---|---:|---:|---:|---:|
| yayo | `DrugLab` | 0.01082 | 0.067% | 1.011 | 0.289% |
| psychoid leaves | `HydroponicsBasin` | 0.00074 | 0.056% | 0.042 | 0.091% |
| chemfuel | `BiofuelRefinery` | 0.00068 | 0.043% | 0.045 | 0.179% |
| meals | `ElectricStove` | 0.00477 | 0.046% | 0.359 | 0.118% |

Fixed capital is **0.353% of constant capital** at equilibrium. Labor values
rose by 0.09–0.19% and nothing else changed.

So the vanilla omission is real but quantitatively minor, and that is the
useful result: RimWorld's buildings are cheap relative to what they produce
across a service life, so repairing the formula would move prices by a
fraction of a percent. **Predicted under 0.5% of constant capital; measured
0.353%.**

## 2. The overhead is the authored-price wedge

Subtracting everything the model can account for from each unit's price:

| sector | price | inputs | wages | capital | attributable | **wedge** | wedge % |
|---|---:|---:|---:|---:|---:|---:|---:|
| chemfuel | 2.3000 | 0 | 0.0312 | 0.00068 | 0.0319 | **1.5327** | 66.6% |
| psychoid leaves | 1.9000 | 0.1150 | 0.0578 | 0.00074 | 0.1735 | **1.1509** | 60.6% |
| meals | 15.0000 | 0 | 0.3813 | 0.00477 | 0.3860 | **9.9952** | 66.6% |
| yayo | 21.0000 | 15.6600 | 0.4375 | 0.01082 | 16.1083 | **−0.0108** | −0.05% |

For the two goods the model builds from labor alone, two-thirds of RimWorld's
authored price is neither inputs, nor wages, nor capital consumption. The
66.6% is exactly the calibration showing through: `docs/13` derived the
overhead as `reference_price × 14 / 21`, and 14/21 is two-thirds.

**The yayo wedge is negative**, and it is reported rather than clamped.
RimWorld's yayo price does not quite cover its inputs, wages, and capital
consumption at reference — 21.00 against 21.01. That is a statement about the
authored price, not an error in the model, and the surplus readings are named
by their assumption rather than as a "lower" and "upper" bound precisely so
that a negative wedge does not produce a nonsensical inverted band.

### What the wedge is, and what this session refuses to claim

It is tempting to call the wedge surplus value. For the wage good the two
ledgers then agree to two decimals — meals show a money rate of surplus value
of **38.33** against a labor-time rate of **38.30**.

**That agreement is an identity, not evidence**, and the design document
committed to saying so before the number was computed. Both figures come from
the same wage and the same basket: with the basket priced at two meals, money
s/v is `price / wage_per_unit − 1 = 24000/610 − 1`, which is the labor-time
expression term for term. It would agree whatever the truth was.

So the model reports the wedge under its own name and gives surplus as two
readings that state their assumption. Nothing inside the laboratory
distinguishes surplus from a cost the model does not represent — energy
beyond the modelled chemfuel, tools, maintenance, land, a colony's other
overheads. Reporting an estimator-dependent quantity as a range with its
assumptions named is what `FINDINGS.md` did with the 3–4× versus 14×
extraction premium, for the same reason.

## 3. The result: surplus produced is not surplus realized

The wedge read as surplus gives each sector a money rate of surplus value,
against a **uniform** labor-time rate of 38.30:

| sector | money s/v | labor s/v | |
|---|---:|---:|---|
| chemfuel | **72.58** | 38.30 | realizes ~1.9× what it produces |
| psychoid leaves | 29.90 | 38.30 | realizes ~0.78× |
| meals | 38.33 | 38.30 | agrees by construction |
| yayo | **11.18** | 38.30 | realizes ~0.29× |

Every sector performs surplus labor at the same rate — the working day and
the basket are uniform — but the prices they sell into distribute that
surplus very differently. The drug lab buys leaves and chemfuel at prices
containing surplus, and sells into a yayo price that barely covers them, so
it realizes under a third of the surplus its workers performed. Chemfuel,
selling at a price with almost no input cost behind it, realizes nearly
double.

This is the transformation problem as arithmetic rather than as an argument,
and it is the sharpest illustration the project has produced of why the four
ledgers must stay separate: labor value, market price, surplus value, and
rent genuinely do not move together, and three of the four are now measured
independently in the same run.

## 4. The value ledger closes

A third accounting identity now holds beside material and silver:

```
value of output  =  c  +  v  +  s
```

At equilibrium, Dust Basin, cumulative over 240 days:

| quantity | ticks |
|---|---:|
| circulating constant capital | 947,955.8 |
| fixed constant capital | 3,354.0 |
| **constant capital c** | **951,309.8** |
| **variable capital v** | **46,033.2** |
| **surplus labor s** | **1,762,985.9** |
| organic composition c/v | **20.67** |
| value rate of profit s/(c+v) | **1.77** |

The residual closes to floating-point zero (relative 5 × 10⁻¹⁶), and it is a
real check rather than a tautology: `c` is accumulated from the material draw
and the capital worn out, `v` and `s` from employment and the basket, and the
output value from the solved labor values — three independently maintained
paths that have to agree.

**It earned its keep immediately by catching two bugs.** Producers added
outside the investment path — the entrants in `technique-change` and
`cost-competition` — were carrying no fixed capital, because capital was set
only at seeding and on project completion; capital is now refreshed daily for
every producer, like wage and extraction costs already were. And revaluing a
whole run at final labor values does not close when a technique changes
mid-run, so value produced is now accumulated as a flow at the values
prevailing when each unit was made.

One residual survives, deliberately. In `technique-change` the identity
closes only to 9 × 10⁻⁶ relative, because values are solved from the
*previous* day's output weights (`docs/19`), so while the technique mix is
shifting, output valued socially does not quite equal the individual costs
behind it. It is a bounded transient of the one-day lag, it does not
accumulate, and it has its own test saying so rather than a loosened
tolerance on the main one.

## 5. Prediction scorecard

### "No behavioral movement" — **correct, and stronger than predicted**

The design predicted "fewer than 10 of 85 metrics move, none by more than
0.5%." In fact **zero** behavioral metrics moved. The design document
contradicted itself here — §4 specified carving capital out of `unit_cost`
while §6 predicted costs rising by the depreciation term — and the
implementation followed §4, which is both the cleaner reading and the one
that isolates the measurement completely.

### "Fixed capital under 0.5% of constant capital" — **correct** (0.353%)

### "Labor values rise 0.1–0.3%, s/v falls to 38.20–38.34" — **correct**

Values rose 0.09–0.19%; s/v landed at **38.298**.

### "Organic composition roughly 2–4" — **wrong: 20.67**

Badly wrong, and for a reason worth recording. The prediction was an
intuition about how capital-intensive the circuit looked. The measured figure
is high because **v is tiny**, not because c is large: necessary labor is
only 2.5% of the working day, since the basket is meals-only. The same
understatement of the value of labor-power that `docs/18` flagged as
inflating s/v inflates c/v by the same mechanism. Any figure built on v in
this model carries that caveat.

There is a second reason to read 20.67 cautiously: `c` is accumulated stage
by stage, so leaves count as constant capital when the drug lab consumes
them, having already counted chemfuel as constant capital when the farm
consumed it. That is correct period accounting for a sector, but it means the
vertically integrated circuit reports a higher c/v than a consolidated view
of the same economy would.

### "Value rate of profit well above the historical literature" — **correct** (1.77)

For the same reason: v is understated.

## 6. What this does and does not fix

`docs/22` said the model's ceiling was that money costs are mostly
unexplained residual. That is now **measured and named** rather than
unexplained — but it is not removed. The wedge is still two-thirds of price
upstream, and labor is still 2–4% of money cost, so a labor-saving technique
still moves price by half a percent.

The honest conclusion is that **the wedge cannot be closed while RimWorld's
authored prices are the reference.** Every economically meaningful component
the model can support has now been carved out of it, and two-thirds remains.
Closing it means deriving prices from the technical data and the wage instead
of anchoring them to `MarketValue` — prices of production, with a uniform
profit rate — which would move every price in the model and is named as the
next step rather than attempted here.

That is the same seam `FINDINGS.md` found from the outside, now measured from
the inside: authored prices embed a labor rate far above what the model pays.
The wage is 3.1 silver per in-game work-hour against the 9/hour RimWorld's
own fabrication constant embeds and the ~95/hour its extraction prices imply.

## Reference decision

Two commits. The first refreshes fifteen value observations and explains
them; the second adds sixteen new ones as a pure insertion. 85 metrics to
101.
