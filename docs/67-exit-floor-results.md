# The exit floor: results

`docs/66` set out ten predictions on a two-line fix. Four held, one held
in half, and five were wrong — and the five are worth more than the four,
because `docs/66` §5 wrote down in advance what each failure would mean
and every one of them meant the thing it said.

**The headline: the floor works and it was not the whole disease. The
seed's tailors and herbalists now rest at exactly the minimum plant in
both regions and keep working, and the gravitation basket shortfall goes
115.78 to zero. But the glut's shortfall only falls 94.39 to 63.10, and
the reason is a second defect the deletion was hiding: a seller emptied
by the very order it is answering records no sell-out. It therefore
expects only what it managed to sell, and exit — correctly, on a false
signal — shrinks the sector to fit its own supply while a third of the
workers' meals go unserved every day. Exit is not wrong here. Its input
is.**

## 1. What shipped

Two changes in `_exit`, exactly as `docs/66` §2 specified. The
withdrawal is floored:

    floor = max(min_investment_capacity, capacity − surplus)
    withdrawn = min(exit_gain × (1 − r) × surplus, capacity − floor)

and retirement now fires on `expected_demand ≤ EPSILON` — the producer
whose custom has gone — instead of on the plant's size. The retirement
branch is taken first, so a producer already resting on the floor when
its custom finally goes is still retired rather than left as a husk.

Twenty-two `exit.*` readings re-measured and re-frozen; the reference
stays at 322 metrics and every one of the other 300 is zero delta. Seven
tests, one replaced and one added: 237 in the laboratory suite, 270 with
the viewer and the port.

## 2. Held: 4.1, 4.2 in part, 4.9, 4.10

**4.10, run first as `docs/66` said to.** `python -m economy_lab
overshoot` runs. It had been raising `cannot price 'chemfuel'`, because
deleting the tailors' bench broke the link that makes chemfuel basic and
the price system had no solution. With the basket alive the solution is
back.

**4.1** All 300 non-exit metrics zero delta. The model off the flag is
untouched.

**4.2, the half that is the fix.** Tailors and herbalists end at
**exactly 0.1** in both regions, from 0.25, and both are producing —
`garments_capacity_end` and `medicine_capacity_end` move 0 → 0.1. The
cooperative, the fields and the refinery are unchanged to the bit; a
sector at full utilization still has no surplus. The first withdrawal is
still day 45.

**4.9** The three identities close at 7e-9, 1.1e-7 and 1e-10, and the
`exits` ledger still reconciles to what `capacity_lost` gained, in every
scenario.

## 3. Wrong, and the prediction said what it would mean: 4.2's second half

The provisioners were predicted unchanged to the bit at 1.003612 of
their reserve target. They end at **1.003992** — 0.038% off, not a
rounding. Nothing is wrong with the floor: their target is 0.6986 and
0.1 is far below it, so the floor never binds on them. The movement is
the wage. Clothing and medicine are an eighth of the subsistence basket
each; alive, they are priced, and the basket costs what it costs, so the
wage differs, so every effective cost differs, so the provisioners'
margin and their expectation walk a slightly different path. This is the
smallest instance of the finding in §4 and it is the same finding.

## 4. Wrong, and it invalidates a claim in `docs/65`: 4.6

`docs/66` §4.6 predicted the four readings `docs/65` §2 called clean —
the ones that "do not run through the basket" — would move less than 1%.
They moved:

| reading | docs/65 | now | move |
|---|---:|---:|---:|
| producer_loss leaves biggest entrant | 9.687 | 11.716 | +20.9% |
| producer_loss chemfuel biggest entrant | 0.838 | 0.645 | −23.0% |
| producer_loss yayo price / reference | 1.1545 | 1.4029 | +21.5% |
| cost_competition incumbent / expected | 1.1000 | 1.1167 | +1.5% |

`docs/66` §5: "If 4.6's clean readings move more than 1%, then `docs/65`
§2 was wrong to call them clean." It was wrong, and the reason is worth
stating plainly, because it applies to every reading this laboratory will
ever take on the market model. **Nothing in this economy is outside the
basket.** The basket is what a worker-day costs; the wage is that cost;
the wage is in every producer's `wage_cost_per_unit`; so it is in every
effective cost, every margin, every posted price and every entry and exit
decision. Deleting two sectors of four hundredths of a unit a day moved
the yayo price after a 60% capacity loss by 21%. "Runs through the
basket" is not a property some readings have and others lack.

Two test bounds were tuned to the old values and are now bounds on the
claims instead: the leaves entrant is asserted an order of magnitude
below entry's 66 rather than below 10, and the incumbent is asserted to
land within the reserve and never through it rather than exactly on it.
The floor invariant — never below `1 + reserve` — is the part that must
hold exactly, and it does.

## 5. Wrong, and it is a second defect: 4.4, 4.5

`exit.gravitation.basket_shortfall` went 115.78 → **0**, as predicted.
`exit.glut.basket_shortfall` went 94.39 → **63.10**, and the prediction
was under 1.0. `demand_boom` employment went 0.2063 → **0.2126** against
a prediction of 0.4822. `docs/66` §5: "If 4.4's shortfalls do not fall to
near zero, something else deletes or starves the basket, and the
retirement clause was a symptom rather than the cause." It was a cause,
not the cause. Here is the other one, traced day by day in the glut:

| day | provisioner capacity | expected demand | sold | sell-outs seen | stock | basket short/day |
|---:|---:|---:|---:|---:|---:|---:|
| 121 | 0.3557 | 0.5473 | 0.624 | 0.000 | 0.482 | 0.000 |
| 136 | 0.3557 | 0.4209 | 0.289 | 0.000 | 0.000 | 0.334 |
| 181 | 0.3557 | 0.3026 | 0.289 | 0.000 | 0.000 | 0.351 |
| 241 | 0.2865 | 0.2591 | 0.233 | 0.000 | 0.000 | 0.400 |
| 286 | 0.2408 | 0.2178 | 0.196 | 0.000 | 0.000 | 0.435 |

From day 136 the provisioner is empty every single day, the workers go
short by more than it sells, and the sell-outs it sees are **exactly
zero**. Its expectation converges on what it managed to supply, its
capacity follows its expectation down through the reserve, and the
shortfall grows as the capacity shrinks. The workers are not poor: they
end holding 2089 silver against a basket costing 2.75 a day. The meals
are not dear: the price rests at 10.21 against an authored 15. There are
simply not enough of them, and nothing in the model says so.

**The mechanism.** `_note_sellouts` counts a sell-out only for a seller
already empty when the order arrives — `stock − pending_out ≤ EPSILON` —
and `_final_market` calls it *before* `_buy` draws the stock down.
Instrumented on day 201: unfilled demand 0.307, the provisioner's stock
at the moment of the call 0.289, the list of sellers counted as empty
`[]`. The stock goes to zero microseconds later, in the `_buy` that
follows. A seller that is emptied *by* the order it is answering is
invisible to the rule; only a seller that was already empty *before* it
counts.

`docs/62` wrote this rule to fix the opposite case — "a sector that ran
dry could never see the demand that would restart it" — and fixed it for
a sector at zero. The case it left is a sector serving part of the
demand, which is the ordinary case of scarcity and the one that matters,
because it is the case where a price ought to rise and a plan ought to
grow. Two rules read the sell-out and both are silenced: the plan, so
output never grows to meet the demand, and the posted price, so the
scarcity is never priced. Exit then reads a demand that is really a
supply, and does exactly what it was designed to do to it.

This defect predates exit. Before exit the sector kept its plant and
merely under-produced; exit is what turns a silent signal into a
contracting sector, which is why it surfaced here. It is now asserted as
current behaviour by
`test_a_seller_emptied_by_an_order_does_not_see_the_demand_it_missed`,
which is written to fail when it is fixed.

## 6. Wrong, and `docs/65` §5 survives: 4.7, 4.8

**4.7** The glut was predicted to come down from 1.3299× to between 1.05
and 1.30. It ends at **1.3553×** — it went up. **4.8** Green River was
predicted to stay converged under 1e-4; its last-60 range is
**2.18e-4**. Dust Basin's stays above 1% (0.01676) and its chemfuel
producer count stays at 17 against entry's 13, both as predicted.

`docs/66` §5 said that if these came out *better* than predicted the
churn was downstream of the deleted basket and `docs/65` §5 was wrong.
They came out worse. The churn is not the basket's doing, it survived the
fix unchanged, and it is still the open question `docs/65` §5 named.
Whether it is also downstream of the sell-out defect in §5 is the first
thing to check after that fix, and not before: the glut is exactly the
scenario where a sector is emptied every day.

## 7. What the rule is now

Exit withdraws the capacity a producer holds beyond a reserve over the
demand it expects, in proportion to how far its return falls short of the
going one, after the lead time, and never below the larger of that
reserve and the smallest plant the fund would build. Retirement is for a
producer whose custom has gone. The invariant of `docs/66` §1 holds:
capital cannot withdraw below what no rule could rebuild.

What it still does is trust `expected_demand`, and §5 is the finding that
`expected_demand` is not demand whenever a seller is emptied by an order.

## 8. Carried forward

**The sell-out a seller is emptied by** is the next design, `docs/68`. It
is a correction to `docs/62`'s rule, not a new mechanism, and the shape
is visible: the sell-out has to be measured against what the order could
not take, which means noting it after the stock is drawn down rather than
before, or netting the order against the stock at the point of the call.
Both change the seeded circuit not at all — nothing sells out there — and
both change the glut, the boom and the subsistence shock. Its results
should re-read 4.4, 4.5 and, per §6, 4.7 and 4.8.

**The churn** (`docs/65` §5) is still open and is now the only finding of
this slice with no design against it.

**The reference** still follows the planned model. §4 is a reason to be
slower about changing that, not faster: a market whose scarcity signal
misses the ordinary case of scarcity is not yet a candidate.

## 9. Cost

The twenty-two readings re-measured, one 300-day glut trace instrumented
day by day, and one three-day trace with the sell-out call spied on:
about twelve seconds in all. None of the traces is frozen.
