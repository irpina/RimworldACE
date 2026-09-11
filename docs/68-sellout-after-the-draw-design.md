# The sell-out a seller is emptied by: design

Written before implementation. `docs/67` §5 records the defect and
`docs/67` §8 names the two candidate shapes. This document says which one
it takes and why, what it does to each reading the exit slice froze, what
it deliberately leaves alone, and what would make it wrong. It is a
correction to `docs/62`'s rule, not a new mechanism, in the same sense
that `docs/62` was a correction to `docs/59`'s; `docs/62` carries a
pointer to it the way `docs/60` carries one to `docs/62`.

## 1. The defect, stated as an invariant

`_note_sellouts` (`economy_lab/model.py:4201`) credits unserved demand to
every active seller of the commodity that is empty — `stock −
pending_out ≤ EPSILON` — **at the moment of the call**. `_final_market`
and `_produce_procurement` make that call *before* the `_buy` that draws
the stock down. So a seller that is emptied *by* the order it is
answering tests as non-empty and is credited nothing.

Instrumented on day 201 of `regional_glut` (`docs/67` §5): unfilled
demand 0.307, the provisioner's stock at the moment of the call 0.289,
sellers counted as empty `[]`. The stock reaches zero microseconds later
in the `_buy` that follows.

`docs/62` wrote the rule for the opposite case — a sector already at zero
could never see the demand that would restart it — and fixed that one.
The case it left is a sector serving *part* of the demand, which is the
ordinary case of scarcity: the case where a price ought to rise and a
plan ought to grow. Two rules read the signal and both go silent. The
plan never grows output to meet the demand, and the posted price never
prices the scarcity; exit then reads a demand that is really a supply and
contracts the sector to fit it.

The invariant this violates:

> **A seller that ends a pass empty with demand still unserved has seen
> that demand.**

Whether the emptiness arrived before the order or with it is an artifact
of the order in which the model's own bookkeeping runs. It is not a fact
about the market, and no rule downstream should be able to tell the
difference.

## 2. The rule

**The note reads the stock the order leaves behind, not the stock it
found.** Every `_note_sellouts` call moves to *after* the `_buy` of its
own pass and before that pass's `_apply_pending`, so `stock −
pending_out` at the moment of the call is exactly what the order left.
The unfilled quantity each call passes is unchanged; only its position
moves. `_note_sellouts` itself is untouched.

Three call sites, and they are not equally wrong (`docs/67` §5, verified
again here and recorded in the handoff):

| site | now | after |
|---|---|---|
| `_final_market` fund pass, `model.py:4475` | already after `_buy` | unchanged |
| `_final_market` basket pass, `model.py:4498` | notes in the first loop, buys in the second after the cash factor is known | note deferred to after the second loop's buys |
| `_produce_procurement` input market, `model.py:4338` | notes before that producer's own `_buy`; later producers in the pass do see it, because `pending_out` accumulates | note deferred to after that producer's input buys |

The fund pass is the shape the other two are brought into line with. It
is not a coincidence that it is also the one whose readings `docs/67`
never faulted.

**The cash-denied shortfall is not a sell-out, and this shape says so
without a special case.** `model.py:4511` denies the workers part of the
basket because they cannot pay; the seller still holds the stock, so
after the draw-down it tests as non-empty and is credited nothing. The
same is true of a producer whose runs are cut by its purse in
`_produce_procurement`: it buys less, the seller is not emptied, and
there is no sell-out. Demand that cannot pay is not demand the seller
saw. Under the old ordering this had to be kept out by hand; under the
new one it falls out.

**The sector already at zero keeps its signal.** A name for which nothing
at all is available buys nothing, so there is no draw-down to wait for —
but the sellers are empty at the deferred call too, and `_note_sellouts`
credits them exactly as before. `docs/62`'s case survives untouched; that
is the point of deferring the call rather than rewriting the predicate.

### Why this candidate and not the other

`docs/67` §8 named two: note after the draw-down, or net the order
against the stock at the point of the call. The second is rejected.

Netting requires knowing *which* sellers the order will empty, and that
depends on the cheapest-first allocation with its price-weighted shares,
its per-seller caps and its purse limits — which is `_buy`'s body. A
correct netting would either duplicate that allocation or approximate it,
and an approximation would credit the wrong sellers: in a sector with a
cheap producer and a dear one, an order that empties only the cheap one
would, under any proportional netting, credit both. That is a worse
error than the one being fixed, because it is silent and it biases
against the producer that was *not* emptied. Running the allocation for
real and reading the result afterwards is the same computation with none
of the approximation, and it is one line moved rather than a second
implementation of the order book to keep in step with the first.

The second shape has one genuine advantage — the note stays next to the
quantity it counts, which reads better — and it is given up deliberately
for the comment that now has to carry it.

## 3. What it does not do

- **It does not touch `_note_sellouts`.** The predicate, the EPSILON and
  the "every active seller, not only those that sold today" rule of
  `docs/62` all stand.
- **It does not touch the inline rule in `_buy`** (`model.py:4184`),
  which credits a seller emptied mid-order with the rest of *that*
  order's want. In these three passes the order is capped at what
  `_available` reports, so it fires only where a purse cuts a take
  short, and it is left as it is. Double-counting is therefore possible
  in principle and absent in practice; if a reading suggests otherwise
  the two rules need reconciling in their own document, not here.
- **It does not change any flag's default.** The sell-out is read by the
  plan and the posted price under `procurement`, which is off by default,
  so the default model is untouched.
- **It does not touch the churn** (`docs/65` §5). `docs/67` §6 says to
  ask whether the churn survives this fix, and the answer belongs in
  `docs/69`, after it is measured — not in the same change.

## 4. Predictions

4.1 Bit-identical off: all 322 metrics zero delta with the flags at
their defaults.

4.2 The seeded circuit is bit-identical **with every flag on**. Nothing
sells out at the seed — the provisioners rest above their reserve target
and the basket is served in full — so no note changes position in a pass
that has no unfilled demand in it. `exit.equilibrium.*`, all six
readings, move by zero. This is the sharpest prediction in the document
and the first thing to check: if any of them moves, the note is firing
where there is nothing to note.

4.3 `exit.glut.basket_shortfall` 63.10 → **under 5.0**. This is the
reading the defect was found in and the one that says the fix worked. It
is not predicted to reach zero: the glut starts with a real shock, and a
day or two of shortfall while the plan and the price respond is the
correct behaviour rather than a residue.

4.4 The glut's provisioner stops contracting. `docs/67` §5's trace has
capacity falling 0.3557 → 0.2408 between days 121 and 286 while the
shortfall grows; after the fix its expected demand should track the
demand rather than its own supply, so capacity at day 240 is **above**
its day-121 value of 0.3557 and its sell-outs seen are non-zero on the
days it ends empty.

4.5 `exit.boom.employment_end` 0.2126 → within 5% of entry's
**0.4822**. `docs/66` §4.5 predicted this of the floor and was wrong
because the floor was not the only thing starving the basket. The claim
is repeated here, against the second cause, and it should be believed
rather less than 4.3 is: if the basket is now served and employment
still does not recover, there is a third thing.

4.6 `procurement.*` and `entry.*` move. They are in scope and they are
expected to move in the scenarios with a shortage in them —
`procurement.subsistence.meals_peak_over_reference`,
`procurement.glut.trough_over_reference`, `entry.subsistence.*`,
`entry.glut.*`. Direction, where the rule has one: a sector that is short
now sees the shortage, so **the price peaks higher and the trough is
shallower**. `equilibrium.*` and the seeded readings under both flags do
not move, by 4.2.

4.7 The `posted.*` readings move too, if any scenario under
`posted_prices` alone empties a seller — but `posted_prices` without
`procurement` does not run `_produce_procurement`'s market, and its final
market is the fund pass, which is already correct. So the prediction is
**`posted.*` unchanged**, and a move there means the basket pass is
reached by a path this document has not traced.

4.8 The identities close, in every scenario and every flag combination,
and `exits` still reconciles to `capacity_lost`.

4.9 `test_a_seller_emptied_by_an_order_does_not_see_the_demand_it_missed`
**fails**, as it was written to. It is replaced by its opposite:
a provisioner that ends the glut empty with the basket short records
sell-outs, and its capacity is not below the demand it faces.

4.10 The churn is **not** predicted either way. `docs/67` §6 asks whether
it survives; this document declines to guess, and `docs/65` §5 remains
open until it is measured.

## 5. What would make this wrong

If 4.2's seeded readings move at all, the deferral has changed a pass
that had nothing to defer, which would mean `_available` and the order
disagree at the seed — a bigger problem than the one being fixed, and one
that would invalidate `docs/62`'s and `docs/67`'s readings too.

If 4.3's shortfall does not fall below 5.0, the sell-out was not the
only thing starving the glut's basket, and the same reasoning that
retired the retirement clause as "a cause, not the cause" (`docs/67` §5)
applies again: look for the third cause before crediting this fix.

If 4.3 holds but 4.5 does not, the basket is provisioned and employment
still does not recover, and the fault is in the boom's labor side rather
than its goods side. That would be a finding about `demand_boom` and not
about this rule.

If `procurement.*` moves in the *opposite* direction to 4.6 — peaks
lower, troughs deeper — then seeing a shortage makes this market supply
less of the good that is short, which would be a defect in the plan's
reading of the sell-out rather than in the signal, and `docs/62` §1 would
need reopening.

If the churn disappears, `docs/65` §5 was downstream of this defect after
all and `docs/67` §6 was right to insist the question be asked here. If
it gets worse, the sell-out was damping it, and either way it is
`docs/69`'s subject and not a reason to change this rule.

## 6. Cost

Two calls moved and the comments that explain why, the `exit.*`,
`procurement.*` and `entry.*` metrics re-measured and re-frozen with the
movement explained, one test replaced by its opposite, the `_exit_metrics`
docstring brought up to date, and a results document. The scenarios under
the market flags are the slow ones; about half a minute of measurement,
one small session.
