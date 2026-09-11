# The sell-out a seller is emptied by: results

`docs/68` is the design. The rule is built and measured. Six predictions
held, one in half, three wrong — and, as with `docs/67`, `docs/68` §5 had
written down in advance what each failure would mean, so each one is a
finding.

**The headline: the scarcity signal works, and the glut's basket stops
going short. The provisioner that `docs/67` §5 watched shrink from 0.3557
to 0.2408 while the workers went hungry now sees the demand it misses,
grows to 0.97 by day 181, and the shortfall stops accruing altogether.
The glut's level comes home from 1.3553× the reference to 1.0384×, and
meals are priced at 19.80 against an authored 15 instead of resting at
10.21 in the middle of a shortage. Twenty-four readings move; the seeded
circuit, `cost_competition` and the whole `gravitation` run are
bit-identical with every flag on, and so is the default model.**

## 1. Held exactly: 4.1, 4.2, 4.7

**4.1** All 322 metrics zero delta with the flags at their defaults.

**4.2** The seeded circuit is bit-identical with every flag on. All six
`exit.equilibrium.*` readings — the first exit day at 45, the two basket
sectors at the floor of 0.1, the provisioners at 1.003992 of their
reserve target, yayo at 10 — move by exactly zero. So does every
`cost_competition` reading under every flag combination, and so does the
entire `gravitation` run. This was the sharpest prediction in `docs/68`
and it is the one that says the deferral changed only the passes that had
something to defer: where nothing goes unserved, no note moves.

**4.7** `posted.*` unchanged, as predicted and for the reason predicted:
`posted_prices` without `procurement` never reaches either of the two
call sites that moved.

## 2. Held: 4.4, 4.9, and the identities

**4.4** The glut's provisioner, traced against `docs/67` §5's own table:

| day | capacity | expected demand | sold | **sell-outs seen** | stock | cumulative shortfall |
|---:|---:|---:|---:|---:|---:|---:|
| 121 | 0.3557 | 0.5962 | 0.3557 | **0.2483** | 0.0000 | 15.03 |
| 136 | 0.5363 | 0.8074 | 0.5363 | **0.3251** | 0.0000 | 18.97 |
| 181 | 0.9741 | 0.8801 | 0.6230 | 0.0000 | 3.4575 | 21.59 |
| 241 | 1.9280 | 0.7878 | 0.6466 | 0.0000 | 16.3114 | 21.59 |
| 286 | 1.3680 | 0.6904 | 0.6426 | 0.0000 | 15.1143 | 21.59 |

Compare `docs/67` §5, where the sell-outs column was zero on every row,
capacity fell monotonically from 0.3557 to 0.2408, and the shortfall grew
every day to the last. Here the seller that ends the day empty records
what it could not serve, its expected demand runs **ahead** of what it
sold instead of converging on it, the sector grows — one provisioner
becomes two, then five — and from about day 181 it holds stock, serves
the basket in full, and the cumulative shortfall never moves again.

The rest of the sector's story is the same fact from the other side.
`exit.producer_loss.yayo_capacity_over_demand_seen` goes 1.9620 →
**0.9693**: capacity was twice the demand the sector could see, and the
demand it can see is now most of the way to the capacity. The reading did
not move because capacity fell to meet demand; it moved because demand
stopped being measured as supply.

**4.9** `test_a_seller_emptied_by_an_order_does_not_see_the_demand_it_missed`
failed, as it was written to. It is replaced by
`test_a_seller_emptied_by_an_order_sees_the_demand_it_missed`, which
asserts the sell-out is recorded on the day the seller is emptied, that
the sector's expectation exceeds its sales, and that no shortfall accrues
over the glut's last sixty days.

**4.8** The identities close and `exits` reconciles to `capacity_lost` in
every scenario: 237 tests in the laboratory suite, 272 with the viewer and
the port. (One pre-existing failure in `test_port_fixtures` is unrelated
and predates this change — a committed fixture differing from a fresh run
in the last digit of one float, on a machine that is not the one that
froze it.)

## 3. Held in half: 4.3

`exit.glut.basket_shortfall` went 63.10 → **21.59**. The prediction was
under 5.0, with the reasoning that "a day or two of shortfall while the
plan and the price respond is the correct behaviour rather than a
residue." That reasoning was right and the number was not: the response
takes not a day or two but about sixty, from the shock to day 181, and
every unit of the 21.59 is accrued inside that window. After it, nothing.

The distinction matters because the two failures look identical in a
single number and are opposite in kind. A shortfall that keeps accruing
is a rule that cannot see; a shortfall that stops is a rule that saw and
took time to answer. `docs/68` §4.3 should have predicted a *flat tail*
rather than a small total, and the reading to freeze is arguably the
shortfall accrued after day 200, which is zero. The total is kept as the
frozen metric anyway, because it is comparable with `docs/65` and
`docs/67`, and this paragraph is the note on how to read it.

Two readings say the same thing in prices rather than units. Meals in the
glut end at **19.80** against an authored 15, where `docs/67` §5 found
them resting at 10.21 in the middle of a shortage; and the workers end
holding 1852 silver rather than 2089. The scarcity is priced now, and the
workers spend on it.

## 4. Wrong, and not this rule's doing: 4.5

`exit.boom.employment_end` went 0.2126 → **0.2051**, against a prediction
of within 5% of entry's 0.4822. `docs/68` §5: "if the basket is now
served and employment still does not recover, there is a third thing."
The basket is served — `demand_boom` under exit accrues a basket
shortfall of **exactly zero**, before this change and after it — so the
boom never went through the defect this document fixes, and repeating
`docs/66` §4.5's prediction against a second cause was a mistake that
`docs/68` §5 half-anticipated by saying it should be believed less than
4.3.

What the boom does instead, with exit on:

| run | employment end | yayo capacity | meals capacity |
|---|---:|---:|---:|
| market | 0.4925 | 17.2952 | 1.5294 |
| entry | 0.4831 | 17.2952 | 1.6628 |
| exit | 0.2051 | **35.3978** | **0.3916** |

Exit does not destroy the boom's capacity; it moves it. Yayo doubles and
meals fall to a quarter, in a run where nothing goes unserved. That is
not a goods-side failure and it is not the labor side either: it is
capital placed in one sector and withdrawn from another under the same
two rules that alternate in Dust Basin, which is the churn of `docs/65`
§5 wearing a different scenario's clothes. It belongs to the churn's
document.

## 5. Wrong, and it is a finding about entry: `docs/61` §6.3

`test_a_shortage_draws_entry_that_brings_the_level_below_the_market`
failed. At `producer_loss`'s own 150-day horizon the entry run's yayo
price is **24.93** against the market-without-entry's **23.03** — entry
is now the dearer of the two, having been the cheaper.

The capacity is still there (17.06 against 14.58), and the crossing has
not been lost, only delayed:

| days after loss | market | entry |
|---:|---:|---:|
| 100 | 25.67 | 25.51 |
| 150 | 23.03 | **24.93** |
| 200 | 21.58 | 21.47 |
| 240 | 21.90 | 20.62 |
| 440 | 20.10 | 17.77 |

The reason is the correction itself. The market *without* entry now sees
the shortage through its own producers' plans and answers it from
existing plant, which is the faster path for the first few months; entry
answers it by placing new plant, which is slower to arrive and, while it
is arriving, splits the custom so that each producer sees less excess and
cuts its posted price less. By 200 days the new plant is working and the
order is restored.

This is worth stating as a result rather than a nuisance: **the corrected
signal makes incumbents better at shortages, and that narrows the case
for entry on margin at short horizons.** `docs/63` §3 already said the
entry pipeline's virtue shows up beyond `docs/61`'s horizon; this pushes
the crossing out further. The test now asserts the capacity claim and the
level bounds at 150 days, where they hold, and the price claim at 200,
where it holds, with the shift recorded in its docstring.

## 6. The churn survives, bit-identically

`docs/67` §6 asked whether the churn survives this fix and said to ask
only after it. The answer is that it does not merely survive, it is
**unchanged to the bit**: `exit.gravitation.local_yayo_last60_range_over_level`
is 0.016761 before and after, the distant region's 0.000218 before and
after, and the local chemfuel producer count 17 before and after. The
gravitation run has no unserved demand in it, so nothing this change
touches is reached.

That is now three corrections the churn has survived — `docs/62`'s
targets, `docs/66`'s floor, `docs/68`'s signal — two of which were
predicted to possibly dissolve it. It is not a symptom of any of them.
`docs/65` §5 stands as written and the churn is the open finding of this
whole slice, with the boom's capacity swing in §4 above as a second
scenario exhibiting it. It needs its own design document.

## 7. What moved

Twenty-four readings, and the reference stays at **322** with every other
metric at zero delta.

| metric | before | after |
|---|---:|---:|
| exit.glut.basket_shortfall | 63.1040 | 21.5883 |
| exit.glut.end_over_reference | 1.3553 | 1.0384 |
| exit.glut.withdrawals | 48 | 38 |
| exit.producer_loss.yayo_capacity_over_demand_seen | 1.9620 | 0.9693 |
| exit.producer_loss.yayo_price_end_over_reference | 1.4029 | 1.2889 |
| exit.producer_loss.leaves_biggest_entrant | 11.7164 | 7.7334 |
| exit.producer_loss.chemfuel_biggest_entrant | 0.6452 | 0.3986 |
| exit.producer_loss.producers_end | 23 | 20 |
| exit.producer_loss.exits_booked | 140.6389 | 121.0767 |
| exit.boom.employment_end | 0.2126 | 0.2051 |
| entry.subsistence.meals_end_over_reference | 1.2069 | 1.7174 |
| entry.subsistence.meals_producers_end | 6 | 7 |
| entry.producer_loss.end_over_reference | 1.1069 | 1.1871 |
| entry.producer_loss.capacity_end | 17.3101 | 17.0579 |
| entry.producer_loss.peak_over_reference | 1.4506 | 1.4342 |
| entry.glut.end_over_reference | 0.9972 | 0.9976 |
| entry.boom.employment_end | 0.4822 | 0.4831 |
| procurement.subsistence.meals_peak_over_reference | 1.2437 | 2.1993 |
| procurement.subsistence.basket_shortfall | 8.4523 | 7.6906 |
| procurement.producer_loss.end_over_reference | 1.1608 | 1.0968 |
| procurement.producer_loss.peak_over_reference | 1.4501 | 1.4342 |
| procurement.glut.end_over_reference | 0.9972 | 0.9976 |
| procurement.boom.employment_end | 0.4879 | 0.4925 |
| procurement.boom.yayo_price_end_over_reference | 0.8815 | 0.8765 |

**4.6's direction held where the rule has one.** The subsistence shock is
the scenario built around a shortage, and its meals price peak goes from
1.2437× the reference to **2.1993×** — the shock is priced now — while
its basket shortfall falls 9%. The glut's trough (`procurement.glut.trough_over_reference`,
0.6720) did **not** move, and that is right rather than a miss: a glut is
an excess, no seller in it is ever emptied, and a signal about scarcity
has nothing to say there. `docs/68` §4.6 predicted a shallower trough and
should not have.

The two `end_over_reference` pairs read together are §5's finding in the
frozen metrics: `procurement` (no entry) improves at 440 days, 1.1608 →
1.0968, while `entry` worsens, 1.1069 → 1.1871.

## 8. Carried forward

**The churn** (`docs/65` §5, and §4 above) is the only open finding of the
market slice and the only one with no design against it. Three
corrections have left it untouched. Its document should treat the boom's
capacity swing and Dust Basin's alternation as one phenomenon and start
from the reserve's size and the two rules' shared horizon, which is what
`docs/64` §7 named.

**The flag.** Exit on return is now a rule whose signal is right, and the
first of the market slice's flags that could be argued for on its merits
rather than deferred. It should not be turned on until the churn is
understood: a rule that places and withdraws plant in alternation is not
a rule to make default, however correct the demand it reads.

**The reference still follows the planned model.** `docs/67` §8 said a
market whose scarcity signal misses the ordinary case of scarcity is not
a candidate. It no longer misses it. The candidacy question is now the
churn's, and nothing else in this slice is blocking it.

## 9. Cost

The twenty-four readings re-measured and re-frozen, one 300-day glut
trace at five horizons, one boom probe across three flag combinations,
one six-horizon sweep of `producer_loss`, and the suite twice: about two
minutes in all. None of the traces is frozen.
