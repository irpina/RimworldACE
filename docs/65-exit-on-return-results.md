# Exit: capital leaves a sector that cannot earn the going return: results

`docs/64` set out nine predictions. Four held, one held in the part that
was the point of the slice and was wrong in its magnitudes, one held for
a reason the design did not give, and three were wrong. Of 39 checks
taken across the nine, 25 held.

**The headline is negative and it is one clause. The rule's signal is
right — the return on capacity is a working exit criterion, the
investment rule reading the market's demand kills the 66-unit entrant
the design was built to kill, and a cost advantage draws the incumbent
down to its custom plus the reserve exactly. But the retirement clause
deletes two of the six seeded sectors on day 45, in both regions, and
nothing can rebuild them. `docs/64` §2 said "no scenario has one" of a
sector whose demand is below the minimum plant. The seed has two.
Clothing and medicine leave the subsistence basket, the basket shortfall
goes from 0.08 to 94.39 in the glut and 0 to 115.78 in gravitation, and
every reading downstream of the basket is taken on a circuit that cannot
reproduce its workers.**

The rule is left as built and off by default. The fix is `docs/66`,
written before it is made, because choosing it inside a measurement is
the thing this project does not do.

## 1. What shipped

One flag (`exit_on_return`, needs `procurement`), a reserve
(`capacity_reserve`, 0.10) and a gain (`exit_gain`, 1.0).
`Producer.below_going_days`, `Ledger.exits`, `Economy._return_and_surplus`,
`Economy._exit` on the investment interval before `_invest`, `_retire`
factored out of `_bankrupt`, and `_invest` reading the sector's summed
`expected_demand` under the flag. The `complete_market()` parameter set
and the `overshoot()` scenario, on the command line and in the viewer
catalog.

Twenty-two metrics frozen (322 total), seven tests (236 in the laboratory
suite, 271 with the viewer and the port), and every pre-existing metric
unchanged.

**6.1 held.** With the flag off the model is bit-identical: all 299
pre-existing frozen metrics show zero delta.

## 2. Held: 6.4, 6.6, 6.9, and the half of 6.3 that mattered

**6.9** The three identities close in every scenario measured —
equilibrium, `producer_loss` at 500, the glut at 300, `cost_competition`,
`gravitation` and `demand_boom` — at procurement's tolerances; the worst
cash residual is 1.6e-9, the worst value residual 5.2e-8, the worst
commodity residual 5.8e-11. The `exits` ledger sums to exactly what
`capacity_lost` gained under the flag, in all four scenarios checked, to
better than 1e-9.

**6.3, the part it was built for.** The `docs/64` §1 correction works.
With `_invest` reading the sector's expected demand instead of the plan's
full-capacity throughput, the entrants the shortage places collapse to
the size of the demand that is actually there:

| sector | biggest entrant, entry alone | with exit | sector expected demand |
|---|---:|---:|---:|
| psychoid leaves | 66.244 | **9.687** | 63.770 |
| chemfuel | 6.991 | **0.838** | 5.505 |

The 66-unit leaves entrant does not appear. This was the finding
`docs/64` §1 recorded from the entry run and the reason the rule could
not coexist with the shortfall rule unchanged; it is now measured rather
than argued.

**6.4** `producer_loss` at day 500: the yayo price rests at **1.1545×**
the reference, inside the predicted 0.95–1.20 and against entry alone's
0.8939×. Exit restores the level a flooded leaves sector had taken out
of it.

**6.6** `cost_competition`, held in every part. The incumbent withdraws
from 1.0 to **0.2715** against an expected demand of 0.2468 — 1.100×,
which is the reserve to three decimals. The meal price ends at 9.6407
against entry's 9.4921 (+1.56%, inside the 2% predicted) and the cheap
technique holds 62.1% of sales against entry's 62.8%. The split is by
price and the incumbent's price did not move, exactly as the design said.

## 3. Wrong, and the reason is one clause: 6.2

`docs/64` §3 gave up exact stationarity of the seed's *capacity* and
predicted the three basket sectors would settle at `(1 + reserve)` times
their expected demand with **no price, stock, sale or purse moving**.
The provisioners did exactly that — Dust Basin ends at 1.0036 of the
reserve target, Green River at 1.0009 — and the cooperative, the fields
and the refinery are unchanged to the bit, and the first withdrawal is on
day 45, as predicted.

The tailors and the herbalists were deleted.

| producer | capacity | expected | r | reserve target | withdrawal | remaining | min plant |
|---|---:|---:|---:|---:|---:|---:|---:|
| Dust provisioners | 1.0000 | 0.6351 | 0.539 | 0.6986 | 0.1391 | 0.8609 | 0.1 |
| Dust tailors | 0.2500 | 0.0397 | 0.136 | 0.0437 | 0.1782 | **0.0718** | 0.1 |
| Dust herbalists | 0.2500 | 0.0397 | 0.114 | 0.0437 | 0.1829 | **0.0671** | 0.1 |

The withdrawal is correct: these producers hold 6.3× the demand they see
and earn an eighth of the going return, and §3 accepted that they should
shrink. What is wrong is where they stop. `(1 + reserve) × 0.0397` is
**0.0437**, and `min_investment_capacity` is **0.1**, so the reserve
target is *below the minimum plant*. The withdrawal lands at 0.0718 and
0.0671, the retirement clause fires, and the whole plant goes.

**And nothing rebuilds it.** `min_investment_capacity` is a *build-side*
floor — `_invest` refuses to place a project below it
(`economy_lab/model.py:5026`) — being used as a *retire-side* trigger. A
sector whose entire demand is smaller than the smallest plant the fund
would build can exist, because it was seeded, but can never be recreated.
The deletion is irreversible by construction.

So the invariant the rule violates states in one line: **capital must not
withdraw below the smallest plant it could rebuild.** `docs/66` is that
fix.

`docs/64` §7 anticipated four ways to be wrong and this is none of them.
It is §2's aside — *"A sector whose whole demand is below that size is
then served by nobody; no scenario has one, and the case is recorded
rather than handled"* — being false about the document's own seed. The
seed has two such sectors in each of two regions.

## 4. What the deletion did downstream

Garments and herbal medicine entered the basket in `docs/29`. With both
sectors dead the workers' basket cannot be filled at any price:

| scenario | basket shortfall, entry alone | with exit |
|---|---:|---:|
| `regional_glut` to day 300 | 0.08 | **94.39** |
| `demand_boom` | 0.00 | **44.12** |
| `gravitation`, 720 days | 0.00 | **115.78** |

Every remaining failure is downstream of this, so none of the three is a
clean reading of exit:

**6.8 wrong.** Employment on day 360 is **0.2063** against entry's
0.4822 — a 57% fall, where 5% was predicted. Employment is realized runs
and those should have been demand either way; they are not, because two
of the three basket goods no longer exist. The yayo price does end above
entry's (1.6167× against 0.8852×), which the prediction called — but not
for its reason: the boom's capacity ends at 33.4 against entry's 17.3, so
this is more plant and a collapsed basket, not the sell-out regaining its
reach.

**6.5 wrong at the level, right in its arithmetic.** The glut's trough
does outlast the lead — 83 days below 0.95×, exactly the figure §6.5
predicted — exit fires 48 times from day 45 at every interval, and the
price overshoots above 1.03× after day 150. But at day 300 it is at
**1.3299×** and that is also its maximum: the price is still climbing,
not settling within 5%. Yayo capacity is 1.99× the demand seen.

**6.3's magnitudes wrong.** Yayo capacity is 1.289× the demand seen
(1.0–1.2 predicted) and there are **23** producers against entry's 20,
where fewer were predicted.

**And the scenario the slice added does not run.** `python -m economy_lab
overshoot` raises:

```
RuntimeError: cannot price 'chemfuel': its technique requires
['garments', 'herbal_medicine'], which nothing produced
```

`summary()` solves the prices of production, and `docs/29` made the
tailors' powered bench the link that turned chemfuel into a *basic*
commodity. Delete the sectors that produce the basket and the price
system has no solution at all — the classical system cannot price a
technique whose inputs nobody makes.

This is the model's own loud check doing its job (`docs/19`: a
non-productive graph fails loudly rather than returning a number), and it
is left failing. A scenario that cannot be summarized is the correct
report of an economy that cannot reproduce its workers, and making
`summary()` tolerate it would convert the defect into a missing field in
a JSON document. `docs/66` §4.10 predicts the command runs again.

## 5. A second finding, and this one §7 did anticipate: 6.7

`gravitation` at a going margin of 0.30 splits by region, and the split
is not the basket:

| | Dust Basin | Green River |
|---|---|---|
| entry alone | margins 0.242–0.297, ranges ≤1.3e-4 | margins 0.247–0.296, ranges 0.0 |
| with exit | margins **0.185–0.300**, ranges **0.012–0.017** | margins 0.276–0.300, ranges ≤5e-5 |

Green River converges: `River psychoid fields` sheds a smoothly decaying
0.0261, 0.0254, 0.0204, 0.0164, 0.0141, 0.0123 over the last six
intervals, and its yayo price is flat to the fourth decimal. Dust Basin
does not, and the reason is visible in its ledger — **exits and projects
alternate**. Over the last six intervals `Dust cooperative` sheds 0.53,
0.43 and 0.41 while `entrant-Dust Basin-yayo-615` and `-630`, placed days
earlier, are themselves withdrawing 0.0026, 0.0020 and 0.0093. The sector
ends with 22 active producers out of 73 entrants ever placed, at a margin
of 0.214 and a price still moving 1.7% over 60 days.

That is `docs/64` §7's fourth condition verbatim: *"If a sector shows
exits and projects alternating, the shortfall rule with expected demand
is rebuilding what exit withdraws inside the reserve, and the reserve is
the wrong size."* It is independent of the retirement defect — Green
River lost its tailors and herbalists too and still converged — so it
survives the `docs/66` fix and needs its own answer.

Chemfuel also ends with 17 producers against entry's 13, where fewer were
predicted; that is the same churn.

## 6. What the rule is now

Off by default and bit-identical off. On, and with procurement, a
producer whose posted margin times its utilization, over the going
margin, has been below one for the investment lead time, with capacity
beyond a 10% reserve over the demand it expects, withdraws
`exit_gain × (1 − r)` of that surplus each investment interval. Below the
minimum plant it is retired outright — **which is the defect**. Under the
flag, `_invest` reads the sector's summed expected demand rather than the
plan's full-capacity throughput.

It should not be switched on for a reading until `docs/66` lands.

## 7. Carried forward

- **`docs/66`: the exit floor.** A build-side minimum used as a
  retire-side trigger. Two candidates were identified while measuring
  and neither was adopted: floor the withdrawal at
  `max(min_investment_capacity, (1 + reserve) × expected)`, which makes
  the two floors one number and keeps the retirement clause for a
  producer whose demand genuinely reaches zero; or refuse to retire a
  sector's last active seller while the sector has demand. The first
  needs no new parameter; the second is closer to §2's intent and leaves
  a producer resting below the smallest plant that could replace it.
  `docs/66` decides, with its own predictions.
- **The reserve and the churn.** Dust Basin's alternation is `docs/64`
  §7's fourth mode and is not fixed by the floor. Whether the answer is
  a larger reserve, a longer memory for the return than for demand, or
  an entry rule that reads the exits already booked in its sector, is
  open. Green River converging under the same rules is the control.
- **Every magnitude in §4 is unusable** and must be re-measured after
  `docs/66`. The four readings in §2 are not: they do not run through the
  basket, and `cost_competition` and the entrant-size table are clean.
- **`docs/64` §3's method was right even though its prediction failed.**
  Naming, before measuring, exactly which quantities were allowed to move
  is what made a four-sector deletion legible in one run instead of
  being absorbed as a plausible new equilibrium. The failure was in the
  §2 aside that went unchecked, not in the discipline.

## 8. Cost

About four seconds for the whole measurement, against the five §8
estimated. Twenty-two readings frozen (322 total); no long-horizon run
beyond the 500-day loss and 300-day glut the design named.

Four of the twenty-two are the defect rather than a result —
`garments_capacity_end`, `medicine_capacity_end` and the two
`basket_shortfall` readings — and are frozen so that `docs/66` cannot
correct the rule quietly.
