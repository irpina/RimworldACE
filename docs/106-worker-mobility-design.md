# Worker mobility: design

Written before implementation. This is A5, the last divergence on
`docs/50` §5's critical path, and the one the gameplay layer needs:
*"labor entering and leaving a region's pool with a wage attached. The
colony is the first mover; the general case can wait."*

**What is missing today: `Region.labor_pool` is a parameter. `docs/98`
measured it at `1.0` in every committed scenario and it never changes.
Employment moves (0.3175 to 0.4679 across scenarios) but the pool it is
measured against never does, so the reserve army is exogenous — which is
exactly what `docs/97` A5 says Wright's is not.**

## 1. Why this is the rule that matters

`employment_rate()` is `worker_days_earned ÷ labor_pool`, and `_bargain`
drives the wage premium off its distance from a seeded reference. So the
pool is the denominator of the only channel in the model that moves the
*realized* wage share (`docs/99`). Fixing the numerator and freezing the
denominator means the reserve army can only tighten by producing more,
never by people arriving or leaving.

Wright has no regions, so there is no direct analogue of migration in his
model. What he has is an endogenous pool: actors enter and leave
employment, and the unemployed count is an outcome. The nearest thing our
two-region laboratory can do — and the thing `docs/50` actually asks for
— is to let the pool itself move between regions in response to the wage.

## 2. The rule

At the start of each day, before production and therefore before
`_bargain` reads the employment rate:

- Compute each region's wage, `wage_rate()` = basket cost × (1 + premium).
- Compute the mean wage, and each region's **pull**, `(w − mean) ÷ mean`.
- Regions with negative pull send labour; regions with positive pull
  receive it, in proportion to their pull.
- A sending region's outflow is
  `worker_mobility_strength × (−pull) × labor_pool`, **capped at
  `labor_pool − worker_days_earned`** so that a pool can never fall below
  the labour actually employed out of it.
- The receiving side is apportioned so the total moved is exactly the
  total sent — the last recipient takes the remainder rather than its
  computed share, so conservation is exact rather than near.

`worker_mobility_strength` defaults to `0.0`, meaning off, and the rule
returns before touching anything at zero — the discipline `_bargain` and
`_habituate` already keep, so a model without it stays bit-identical
rather than merely close. A region with an infinite pool is skipped: an
unbounded reserve army cannot meaningfully gain or lose members.

Region order is the sorted name order, so the run is reproducible.

## 3. What "with a wage attached" means

Nothing extra. Wages are regional — a worker-day earns
`region.wage_rate()` wherever it is performed — so labour that moves is
paid the destination's wage by construction. The phrase in `docs/50` §5
is a requirement on the *pool*, not a new payment path, and this is the
one place the existing design already does the right thing.

## 4. Numbered predictions

Measured in `docs/107`.

1. **Inert by default.** 322 metrics, no nonzero delta.
2. **Inert at the symmetric equilibrium.** With the rule **on**,
   `equilibrium` is bit-identical to the rule off: the two regions are
   seeded identically, so their wages are equal, every pull is zero and
   nothing moves. If this fails, either the seeding is not symmetric or
   the rule has an ordering bug.
3. **Labour is conserved.** The sum of `labor_pool` over regions stays
   within 1e-12 of its starting value across a 1200-day run with the rule
   on. This is the invariant that makes the rule a *movement* rather than
   a creation.
4. **No region's employment rate exceeds 1.** The cap in §2 holds, in
   every scenario, on every day.
5. **Labour flows toward the boom.** In `demand_boom(bargaining=True)`,
   which raises Dust Basin's final demand, Dust Basin's pool ends
   **larger** than Green River's.
6. **Mobility damps the premium.** Dust Basin's peak wage premium is
   **lower** with mobility on than with it off, because the arriving
   labour loosens the market that the boom tightened. This is the
   classical result and the reason to want the rule.
7. **The two regions' wages converge.** The gap between their wage rates
   at the end of the run is **smaller** with mobility on than off.
8. **The bare wage share identity holds.** Per `docs/99` it is
   `value_of_labor_power ÷ ticks_per_worker_day`, and migration is a
   quantity change.

Predictions 6 and 7 carry the economics; 3 and 4 are the invariants that
say the rule is a movement of people rather than an accounting leak.
Prediction 2 is the honesty check, and given the last four documents I
will measure it rather than assume it.

## 5. What this is not

It is not the colony as first mover. `docs/50` §5 wants a colony that
hires; this moves an abstract pool between two laboratory regions in
response to a wage gap. It is the Stage 0 half, and it is what the Stage
1 rule will be built on — but a pawn arriving at a settlement is a
gameplay-layer concern and not in this slice.

It is not entry into or exit from the workforce as a whole. Total labour
is conserved by prediction 3. Wright's actors leave employment but never
the economy, and neither do these.
