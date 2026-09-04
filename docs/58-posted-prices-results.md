# Firm-posted prices: results

`docs/57` set out eight predictions. Three held, one held better than
written, and four were wrong in a way that reorders the remaining work:
**a posted price needs a stock of its own to respond to, and the
laboratory's producers do not have one.** The rule ships, off by default
and marked experimental, and `docs/59` is the consequence.

## 1. What shipped, and how it differs from the design

One flag (`posted_prices`), two states per producer (`posted_price`,
`last_cost`), one derived state (`order_fill`), and the rule of `docs/57`
§2 with two changes the first run forced:

- **The integral gain is its own parameter**, `posted_price_speed`, at
  0.02, not `price_adjustment_speed` at 0.22. §2 says why.
- **A producer reads its own order fill beside the pool's pressure**:
  `pressure + gain × (fill − sector mean fill)`, exactly zero for a lone
  producer. §5 says why it was not enough.

Twelve metrics frozen (263 total), six tests (216 total), and the
anchored rule of `docs/21` bit-identical: all 251 pre-existing metrics
unchanged (6.1).

## 2. The design's rule, as written, spiralled

With the anchored rule's speed reused as an integral gain, the glut's
yayo price fell to 10 silver, below the utilization floor, production
stopped, stock ran out, and the integrated shortage carried the price to
**86.8 silver on day 180 — 4.1× the reference and rising**. `producer_loss`
reached **351 silver, 16.7×**. The anchored rule applies `exp(pressure)`
as a *level*, bounded by the clamp; the same expression applied as a
daily *factor* compounds for as long as stock is below target, which
after a curtailment is thirty days. A proportional gain is not an
integral gain, and the design used one as the other. Fixed before any
metric was frozen; recorded because the number is the lesson.

## 3. Held: 6.1, 6.2, 6.4, 6.8

**6.2 Exactly stationary.** Price range `0.0` over 240 days. Every
producer's posted price equals the regional price on every day, and the
seeded markups — 1.29 on yayo, 1.41 on leaves, 1.46 on chemfuel, 1.42 on
meals — are what `docs/21` §2 derived from the authored prices once and
never wrote down; they are readable now.

**6.4 Cost passes through in full, and better than the prediction
measured it.** The design measured pass-through on the two contested
scenarios, which §5 shows are the wrong instrument. The clean instrument
is `subsistence_shock`: the meal price rises, the wage rises with it,
every sector's cost rises, and every sector's posted price rises by
exactly its cost — the yayo markup after the shock is **1.2906**, its
seeded value to four decimals, and the largest markup drift across the
five unshocked sectors is **0.0016**, on garments and medicine, the two
other basket goods, whose own stock the dearer wage disturbed. Under the
anchored rule the
yayo price ended 0.3% up on the same shock; here it ends **20.2%** up,
because leaves and chemfuel and the wage all passed through. `κ` is one
by construction and the number says so.

**6.8 The ledgers close** in every scenario, with producer cash on or
off; sellers paid at their own posted price sum to what the buyer paid,
by construction.

## 4. Wrong: 6.3 and 6.5, the level is wherever the shock left it

Predicted: the glut rests at 60 to 85% of the reference. Measured: a
trough of 18.2 on day 89 — shallower than the anchored 14.4, because the
gain is smaller — and then **27.8 silver, 1.32× the reference, on day
420**, with stock at target to twelve decimals and pressure at 2e-13.

The mechanism is not a defect in the rule; it is what the rule is. The
trough curtailed production, stock fell short, the integrated shortage
carried the price past the reference, and when stock reached target the
integration stopped *there*. `docs/57` §3 said the level would be
"neutrally stable between the floor and the entry threshold", and it is;
what the design did not see is that a shock does not leave the price
inside the band it started in. `producer_loss` rests at **4.17×** and the
subsistence shock leaves meals at the **5× cost cap** for the rest of the
run. The band's width is the whole clamp.

What is missing is the classical restoring force from above. `_invest`
builds only where there is a *shortfall*; a sector selling at four times
cost with its stock at target attracts nobody. Entry on margin alone is
the mechanism that would bring a posted price back toward cost plus the
going rate of profit, and it is not in the model. That is the next thing
after `docs/59`, not before it, because entry into a sector needs a
sector whose producers own their sales.

## 5. Wrong: 6.6 and 6.7, a contested sector on one pool does not converge

Predicted: the two provisioners' posted prices end within 5% of each
other. Measured: in `technique_change` the incumbent asks **20.9** and
the entrant **9.07**, a spread of 131%, with the entrant posting *below
its own cost* and the meal price oscillating between 8 and 13 silver for
a hundred days. In `cost_competition` the incumbent asks 43.4 and the
entrant 8.3.

The order-fill term was meant to fix this and could not, because the
pool's pressure is the larger term and it is *shared*. When the entrant
undercuts, the incumbent loses custom and cuts — correctly — but the
entrant, now supplying most of a sector it cannot fully serve alone,
leaves the pool short, the pool's pressure turns positive, and *both*
producers raise. The incumbent, selling nothing, raises on a shortage it
did not cause and cannot relieve. Then stock recovers, the pressure turns
negative, both cut, the entrant's cut takes it below cost, it curtails,
and the cycle repeats. A producer that could see its *own* stock rising
would cut and stop cutting; one that can only see the pool cannot tell
its own glut from its rival's shortage.

So the finding is not that posted prices need a better formula. It is
that a posted price is a claim about a stock the poster owns, and the
laboratory's producers own nothing: the pool is the plan's, and
`docs/56` already had to invent supply shares to decide who a sale
belongs to. Producer-level inventory — procurement, the third
imposition — is not the step after this one; it is the step this one
needed first. `docs/59` is written accordingly, and 6.6's question about
profit-rate equalization is deferred to it.

## 6. What is kept

The rule stays, off by default, because two of its properties are
exactly what the next slice needs and are now tested: it is exactly
stationary, and cost passes through in full with markups preserved. What
`docs/59` replaces is the signal — a producer's own stock and unfilled
orders instead of the pool's — and not the arithmetic.

## 7. Cost

Six runs, about a second of the metric collection.
