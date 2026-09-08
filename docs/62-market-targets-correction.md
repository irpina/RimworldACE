# The market's targets were the plan's: a correction to procurement

Found while building entry on margin (`docs/61`), and recorded before
its results, because every reading `docs/60` froze moves. This document
is design and results in one, since what it describes is a correction
to `docs/59`'s rule and not a new mechanism; `docs/60` carries a pointer
to it.

**The headline: `docs/60`'s market had a plan hidden in it. Every
producer's stock target was its share of a pool sized by the sector's
*throughput at full capacity*, so a sector selling four units a day at
a doubled price held twenty days of the ten it used to sell and saw no
excess. With the target now the inventory life of each producer's own
expected demand, and a producer with idle capacity cutting when its
margin is above the going one, the market gravitates: a glut returns to
within 0.3% of the reference, a 60% capacity loss settles within 2% of
it over five hundred days, and a cost advantage above the going margin
ends at cost plus that margin. Every reading is refreshed.**

## 1. What was wrong

`docs/60` §1 set a producer's price target to "its share of the sector's
sales" of the sector's target, and its plan target to its share of the
same by capacity. The sector's target was `_throughput × target_inventory_days`,
and `Region.throughput_demands` is what the *plan* used to size the
pool: final demand at the reference plus every producer's input draw at
full capacity. That number does not move when a price does. So in the
first entry-on-margin run, `producer_loss` ended with eight yayo
producers holding 198 units between them — the seeded pool of 200 —
selling 4.45 a day at 38 silver, each with its stock at its share of a
target built on ten a day, and none with an excess to cut on. Entry
had fired, capacity was 18.6 against demand of 4.45, and the price did
not move. That is the hidden plan, and it is also why `docs/60` §6
found "every level permanent": the level was pinned by a stock target
the market had no say in.

Replacing the target with the inventory life of yesterday's sales
exposed three more things, each of which had been masked:

- **One day of lost custom was a layoff.** A target of twenty days of
  *yesterday's* sales is zero on the day a rival takes the custom; the
  plan went to zero, employment with it, the wage, every cost, and every
  floor. The glut deflated the whole chain in six days.
- **A sector that ran dry could not restart.** A sell-out was noted only
  for a seller that had sold today, so a sector every buyer found empty
  saw no demand, planned nothing, and stayed empty at the floor.
- **Custom split by warehouse size was an incumbency premium.** A
  seller's weight in a buyer's order was what it *held*, so the
  producer with the larger stock sold more, held more, and sold more.
  An entrant with a cost advantage of 40% ended with 24% of the sales.

## 2. The rule as it now stands

Everything below is under `procurement`; the default model is
bit-identical and the reference confirms it.

**A producer expects its demand.** `Producer.expected_demand` is an
exponential average of the demand it saw each day — its sales plus the
sell-outs noted against it — at `expectation_alpha`, the same 0.05 the
region uses for its expectation of price. In the form
`x += α (d − x)`, which is exact when nothing moved. Its plan and its
stock target read this, not one day's sales.

**The target is the inventory life of that expectation.** For the plan
and for the price alike: `target_inventory_days × expected_demand`. No
pool, no share, nothing from the sector. A lone seeded producer's target
is the pool it used to hold, because the pool was that many days of its
sales.

**The seed places each producer's stock at its own target.** The plan's
pool was the inventory life of throughput at full capacity, which
exceeds the seeded sales wherever capacity does — chemfuel by 3%, meals,
garments and herbal medicine by 7%. A producer opening with the pool
held an excess and cut. The opening inventory the material ledger reads
is taken after this seeding.

**A sell-out is noted for every active seller with nothing left**, and
it raises the price only in proportion to how much of what the seller
was willing to make at its price it actually made
(`last_runs / last_ceiling`). A producer at its ceiling that sold out
raises in full; one whose plan was smaller answers with the plan, which
now sees the demand; one at a price where it would make nothing raises
in full, which is what restarts a dry sector.

**An entrant expects its capacity share of what its sector expects**,
seeded on its first morning beside its posted price. Its stock is not
excess until it fails to sell what it expected.

**Custom is split by what a seller can serve of the order**, not by its
warehouse: the weight is `min(held, order)` at the price factor. Two
sellers who can each fill the order split it by price alone.

**Idle capacity with a margin above the going one cuts.** The one new
term, and the one new parameter: `going_margin` (0.50) with
`idle_capacity_gain` (1.0). A producer whose posted price clears its
cost by more than the going margin, with capacity idle, cuts in
proportion to both:

    own −= idle_capacity_gain × idle × (margin − going) / going

This is the supply response of the producers already in a sector — the
classical mechanism by which the price of a good with spare capacity
gravitates to cost plus the going rate — and it is the same signal
`docs/61` reads for capital that is not there yet. The default sits
above every seeded margin (0.29 to 0.46), so the seeded circuit is
stationary and the term speaks only after a shock; `docs/61`'s
gravitation scenario sets it inside that band.

**Tried and taken out again:** a symmetric stock signal, where a stock
below target raises. It restarted dry sectors, but it also made an
entrant filling its warehouse toward its seeded expectation raise its
price before it had sold anything — `docs/60`'s "empty warehouse read
as scarcity", back by another door. The sell-out change restarts dry
sectors on its own, and the signal stays one-sided.

## 3. What stays exactly stationary

Price range `0.0` and stock range `0.0` over 240 days for **every**
commodity, not only yayo, and every producer's stock equal to the
inventory life of its expected demand to the bit. `docs/60` had tested
yayo alone; chemfuel and meals were drifting at the third decimal under
the pool, because their seeded sales were below their pool's implied
draw. The three identities close at 1e-9, 1e-8 and 1e-11.

## 4. What moved

Fifteen of the seventeen procurement readings; the two equilibrium
ranges stayed at zero. The planned model's numbers are in the last
column, as in `docs/60`.

| reading | docs/60 | now | planned |
|---|---:|---:|---:|
| glut trough / rest | 0.930× / 0.993× | **0.672× / 0.997×** | 0.684× / 1.000× |
| producer-loss peak / end (210 days) | 1.794× / 1.788× | **1.450× / 1.161×** | 2.150× / 1.023× |
| producer-loss capacity | 13.19 | 14.58 | 11.90 |
| boom employment (seeded 0.318) | 0.289 | **0.488** | 0.397 |
| boom yayo price at end | 1.265× | 0.882× | — |
| cost-competition meal price | 14.21 | **9.98** | 12.90 |
| cost-competition cheap share | — | 54% | — |
| technique-change meal price / spread | 14.21 / 0.13% | 12.75 / 19.7% | — |
| subsistence peak / shortfall | 1.214× / 7.63 | 1.244× / 8.45 | 4.96× / 5.70 |

**The glut is a trough the whole chain feels, and it comes back.** The
fund undercuts on what it holds, the producer's sales fall, its stock
is excess against a target that now follows its sales, and it cuts;
leaves and chemfuel see their custom fall a stage later and cut in
turn. Then the fund is out, demand at the low price outruns a plan
built on a twenty-day memory, the sell-outs raise, and the price
returns to the reference — 0.997× on day 180, and between 0.93× and
1.04× thereafter over five hundred days, with the yayo margin ending at
the going 0.51. `docs/60`'s "slow sale" was the pool absorbing the
glut on the producer's behalf.

**The shortage is priced and then competed back.** A peak of 1.45×
instead of 1.79×, because the survivors' plans grow with the sell-outs
they see and the entrants' expectations are seeded, so capacity is
rebuilt to 14.6 and runs; then the rebuilt capacity is idle at the
high price, the margin is above the going one, and the cut brings the
level to 1.16× by day 210 and to within 2% of the reference by day 500.
This is gravitation by the producers already there, before any entry
on margin: `docs/61` §1's "the level stays" was true of the hidden
plan and is not true of the market.

**The boom is absorbed by employment**, at last: 0.488 worker-days on
day 360 against the plan's 0.397, after a price peak of 1.53× on day
210 that the idle-capacity cut then takes *below* the reference, to
0.88×, because the investment the shortfall summoned is now more than
the boom needs. The overshoot is the lead time's; `docs/61` §4 named it.

**A cost advantage above the going margin is used.** The low-overhead
provisioner, with cost 6.40 against 10.40, has a margin of 1.3 at the
going price and capacity idle, cuts, and stops at **9.59** — its cost
times one plus the going margin, to 0.1% — holding 54% of the sales.
The incumbent follows it down to its own cost and sells at 10.46. The
meal price ends at 9.98, below the planned model's 12.90, which the
anchor's average-cost pass-through could not reach. A two-percent
advantage (`technique_change`) leaves both provisioners below the
going margin, neither cuts on idle capacity, and a 20% spread between
them persists with the dearer one holding 59% of the custom: custom
split by a constant elasticity rewards the spread, and nothing in the
rule punishes it. That is a property of the split, recorded and not
repaired.

**The subsistence shock is a shortfall, still.** The tempered sell-out
raises meals at 1.24× and workers go short by 8.45 units; the planned
model's proportional gain spiked to 4.96× and starved them less. The
market's slower price is the workers' loss here, and the reading is
kept for that reason.

The technique-change value residual is 103 ticks against the planned
model's 50.6 — the same residual (`docs/60` §3), on a mix path the
market walks differently, and the test now asks for the same order
rather than the same number.

## 5. Carried forward

`docs/61`'s question changes. The market now gravitates *from above*
wherever capacity is idle; what entry on margin adds is capacity where
there is none to be idle — a sector whose every producer runs full at a
margin above the going one, which is the boom before the shortfall rule
catches up, and the gravitation scenario, where three sectors' seeded
margins exceed 0.30 with their capacity fully used. Its results are
`docs/63`. And the going margin is now one parameter read by both
rules, which is as it should be: capital already placed and capital
not yet placed answer the same signal.

## 6. Cost

Eight runs of 240 to 500 days for the readings, about two seconds; the
five hundred day traces are not frozen.
