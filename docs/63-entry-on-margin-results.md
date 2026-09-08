# Entry on margin: capital goes where the price clears cost: results

`docs/61` set out eight predictions on a market that, it turned out, had
a plan hidden in it. `docs/62` records that correction; this document
reads the eight predictions against the corrected market. Five held,
one held only at the horizon the design set, one held for a reason the
design did not give, and one was wrong.

**The headline: entry on margin is the capacity side of a signal the
market already answers. With the stock target the producer's own
(`docs/62`), a sector with idle capacity and a margin above the going
one cuts by itself; what entry adds is capacity where every producer
runs full at that margin. It brings the shortage's level below the
market's own, and then overshoots on its lead time because nothing
exits. With the going margin set inside the authored band, every sector
in both regions ends within 0.06 of it — three by entry, three by their
own cut — and the prices are still to a hundredth of a percent.**

## 1. What shipped

One flag (`entry_on_margin`), one gain (`entry_gain`, 0.05), and the
going margin `docs/62` introduced (`going_margin`, 0.50), which the
design had called `entry_margin_threshold` before it turned out to be
the same number the price rule needed. Per region, an entry backlog per
commodity. Nineteen metrics frozen (299 total), six tests (229 in the
laboratory suite, 264 with the viewer and the port), the `gravitation`
scenario in the catalog and on the command line, and every pre-existing
metric unchanged.

One thing the design did not specify: **entry accrues.** The term is
proportional to a sector's throughput, and a sector of two-thirds of a
unit a day at a margin of 0.8 asks for 0.02 units of capacity an
interval, below the minimum project size of 0.1. In the first run the
provisioners never drew an entrant at any margin. The intention now
accrues per commodity until it is a project's worth, and lapses when the
margin falls below the going one. In `cost_competition`, where the
sector has no shortfall at all, the entrant is placed on the third
interval after the cheap provisioner appears, at 0.12 units from three
accruals of 0.04.

## 2. Held: 6.1, 6.2, 6.5, 6.7, 6.8

**6.1, 6.2** Bit-identical off; and with the flag on at the default
going margin, the seeded circuit and the glut are the market's own runs
to the bit, every commodity, because no expected price clears the best
cost by 0.5 in either. The backlog stays empty.

**6.5** `cost_competition`: the entrant on margin is placed on day 105
and arrives on day 150, copies the low-overhead technique (its process and its overhead are the
cheap provisioner's, asserted), and the meal price ends at **9.49**
against the market's 9.98 and the plan's 12.90, with the cheap technique
holding **62.8%** of the sales across two producers. Below 11, above
60%, as predicted — though the market alone had reached 9.98, and the
entrant's part is the last half silver.

**6.7** `gravitation`, 720 days at a going margin of 0.30:

| sector (Dust Basin) | seeded margin | end margin | producers | how |
|---|---:|---:|---:|---|
| yayo | 0.291 | 0.297 | 6 | entry |
| psychoid leaves | 0.410 | 0.297 | 28 | entry |
| chemfuel | 0.458 | 0.242 | 13 | entry |
| meals | 0.424 | 0.290 | 1 | idle-capacity cut |
| garments | 0.429 | 0.286 | 1 | idle-capacity cut |
| herbal medicine | 0.358 | 0.286 | 1 | idle-capacity cut |

Green River within 0.01 of each. Every price's range over the last 60
days is under 0.02% of its level. Yayo, below the going margin at the
seed, drew six producers once leaves and chemfuel fell and its cost with
them — the cost propagation the design named as the thing to watch.
Chemfuel undershoots by 0.06, just outside the 0.05 the design allowed:
thirteen entrants over a lead time of 45 days, each summoned by a margin
the earlier ones had not yet cut, and no exit to take the surplus back.
The three sectors with idle capacity at the seed drew no entrant at
all: their own cut took them to the going margin first, which is the
finding `docs/62` §5 predicted and the reason the prediction is scored
as held for a reason the design did not give.

**6.8** Identities at 1e-9, 1e-8 and 1e-10 in every scenario.

## 3. Held at the horizon, wrong beyond it: 6.3

`producer_loss` ends day 210 at **1.107×** the reference (the market:
1.161×; the plan: 1.023×), inside the 1.05–1.28 band, with capacity at
17.3 across eight producers. Run to day 500 the pipeline keeps arriving
after the margin has gone: capacity reaches **22.3** across twenty
producers, twice the demand, and the price rests at **0.89×** — below the
reference, and below where anything in the model can move it, because
the idle-capacity cut stops at the going margin and there is no exit.
The market alone rests at 0.98–1.02× over the same span with 14.6 units.
Entry on margin with a 45-day lead and no foresight builds for the
margin it sees, and §7's "the gain or the interval is the next parameter
to read" is the wrong lesson: the missing rule is the one that takes
capacity away.

## 4. Held for the market's reasons: 6.4

Employment on day 360 of `demand_boom` is **0.482** worker-days, above
the seeded 0.318 as predicted — and 0.006 *below* the market's own
0.488. The shortfall rule builds for the boom before any margin
persists long enough to draw entry, and the corrected market absorbs the
boom by employment (`docs/62` §4) without help. The prediction is true
and entry did not make it so.

## 5. Wrong: 6.6

`subsistence_shock` leaves the same basket shortfall, **8.45** units,
with the flag on or off. The five provisioners placed between day 75
and day 135 are the shortfall rule's, and it places them whether the
flag is on or not; every unit of the shortfall is lost before the first
of them arrives. Entry on margin's own project is placed on day 255,
the seventh provisioner, after the shortfall rule has stopped and the
margin has not; by day 360 the meal price is 1.05× the reference
against the market's 1.09×. The design predicted the shortfall would
shrink; it predicted the wrong quantity, because the shortfall is over
before the margin has persisted long enough to matter.

## 6. What the two rules are

`docs/62` and this document together replace `docs/60` §6's thesis.
The market has a restoring force from above, and it has two sides:
producers already there cut when their capacity is idle and their
margin is above the going one; capital not yet there enters when the
margin is above the going one and, in practice, when nothing is idle.
Both read the same number. What neither does is take capacity away,
so every overshoot — the shortage's, the gravitation scenario's
chemfuel — is permanent, and a price can rest below the reference
with no rule that moves it.

## 7. Carried forward

**Exit** is the next design: a producer that cannot earn the going
margin at the utilization it has should, after a time, take its capacity
out. Bankruptcy (`docs/55`) removes only a producer whose purse idles,
which selling a little prevents; what is missing is the classical
counterpart of entry, and it is what would make 6.3's twenty producers
into ten.

**The reference** still follows the planned model, for the reason
`docs/60` §7 gave. The corrected market is now a candidate: it
gravitates, it closes, and its shocks are readable. The decision is
still after exit.

## 8. Cost

Nine runs of 240 to 720 days for the readings, about four seconds; the
five hundred day trace is not frozen.
