# Absolute rent: design

Written before implementation. `docs/15` §42 listed absolute rent as a
non-goal — "Only differential rent" — and the handoff has carried it as an
omission ever since. This closes it, and the shape of the closure is not the
one the backlog assumed.

## 1. What absolute rent is, and why it is not differential rent

Differential rent, which the model has had since `docs/16`, is the advantage
of a better deposit over the worst one in use. The marginal deposit pays
nothing; that is what makes it marginal.

Absolute rent is what the marginal deposit pays anyway. Marx's argument is
structural rather than about fertility:

1. Extraction and agriculture have a **lower organic composition of
   capital** than the social average — more living labor per unit of
   constant capital.
2. A low-composition sector produces **more surplus value per unit of
   capital** than the average, so its commodities' *value* exceeds their
   *price of production*.
3. Under free competition that excess would be redistributed to
   high-composition sectors through the equalization of profit rates.
4. **Landed property blocks the redistribution.** The owner can simply
   refuse access, so capital does not flow in freely, and the product sells
   above its price of production — up to its value.
5. The difference is absolute rent, and it is a **deduction from the
   economy's surplus value**, not an addition to it.

Every step of that is checkable against quantities this model already
computes. Step 1 is an organic composition. Step 2 is value against price of
production, which `prices_of_production` has reported since `docs/27`. Step 5
is an aggregate identity.

**That is the substance of this session: the mechanism is a proposition, and
the model can test it rather than assume it.**

## 2. Absolute rent cannot be a transfer in this model, and that is a finding

The obvious implementation is a payment: the extracting producer hands rent
to the landowner. It cannot be written, and the reason is one the handoff
already lists as a separate omission:

> individual producer cash accounts and transfer pricing (wages are paid
> from the regional pool; producer-level exploitation accounts need
> producer-level cash)

Producers hold no cash. The region does, and the region also owns the
reserves — `Region.reserves` — so a rent payment from a producer to its
landlord is a transfer from the region to itself, which is exactly nothing.

Nor can the landowner be split out cheaply. A landowner who receives rent and
does not spend it drains regional cash monotonically, and the model raises
rather than quietly stopping wages:

```
region {name!r} cannot cover its wage bill
```

So a landowner needs a *consumption pattern* before rent can flow at all —
classically luxuries, which here means yayo, which changes final demand,
which changes everything the scenario is measured against. **A third income
class is a session of its own and this is not it.**

What absolute rent can be here is two things: a measured bound, and a price
effect. §3 and §4.

## 3. The measurement

Three quantities, all derived from what the model already solves.

**Sector organic composition.** Per unit of output, at social labor values:

```
c_i  =  sum_j a_ij * lambda_j   +   K_i * lambda / L      (constant capital)
v_i  =  l_i * necessary_per_tick                          (variable capital)
```

`necessary_per_tick` is the basket's labor value divided by the working day,
which is what `basket_labor_value` already computes — so `v` is the *value of
labor-power*, not the wage in silver. The social average is the
output-weighted mean, and is the number `organic_composition()` reports
per region.

**The deviation.** Value minus price of production per unit, both in the
labor-value numeraire so that they are commensurable and the aggregate
identity of §5 holds by construction.

**The bound.** `max(0, lambda_i - p_i) * output_i`, summed over the sectors
holding reserves. Zero where the deviation is negative: a sector whose
production price already exceeds its value has no absolute rent to collect,
because there is nothing being redistributed away from it.

## 4. The price effect, gated and deferred

`absolute_rent_fraction`, defaulting to 0.0 and therefore bit-identical,
would raise an extraction commodity's price anchor toward its value by that
fraction of the gap. Proportional and damped, no threshold.

It is **specified and not built**, because §2's cash problem means the rent
would be collected from nobody and paid to nobody. Building the price effect
without the payment would raise a price and leave the silver unaccounted,
which breaks `cash_balance` — the one thing in this model that has never been
allowed to break. Named here so the next session does not have to re-derive
why.

## 5. Predictions

**5.1 Chemfuel has the lowest organic composition in the model**, and it is
far below average. Chemfuel has no material inputs at all and holds 1.9% of
the economy's plant, so its `c` is nearly zero while its `l` is 25 ticks a
unit. Herbal medicine and meals should be next, for the same reason. Yayo and
components should be highest — yayo's inputs are eight leaves a unit.

**5.2 The absolute-rent bound on chemfuel is large: roughly 75% of its
value.** `docs/37` recorded chemfuel's price of production at 0.243 of its
labor value, the largest deviation of any commodity in the model. If Marx's
mechanism holds, that deviation *is* the room absolute rent has.

**5.3 The deviation ranks the sectors the same way the composition does.**
This is the actual Marxian claim and the only one that can be wrong in an
interesting way: sectors below the average composition should sell below
their value under prices of production, and sectors above it should sell
above. If the two orderings disagree, step 2 of §1 does not hold in this
model and the whole account has to be withdrawn.

**5.4 The deviations sum to exactly zero across the economy.** The
labor-value numeraire sets total price equal to total value by construction,
so the positives and the negatives must cancel. This is worth asserting
because it is the quantitative form of "rent is a deduction from surplus
value and not a creation of it" — absolute rent is purely redistributive, and
the model should be able to say so to floating-point tolerance rather than as
an argument.

**5.5 Turnover contaminates 5.3.** `docs/31` established that a sector's
price of production also reflects its turnover time, not only its
composition, and meals have a 4-day inventory life against everyone else's
20. So the ranking in 5.3 should hold for the eight sectors that share a
turnover and may not for meals. If 5.3 fails, this is the first thing to
check before withdrawing anything.

## 6. Tests

1. Composition and deviation are computed for every sector, and the
   deviations sum to zero to within 1e-9 of total value.
2. Chemfuel's composition is the lowest and its deviation the most negative.
3. The bound is zero for every sector whose production price exceeds its
   value.
4. `absolute_rent_fraction` defaults to 0.0 and nothing moves.

## 7. What would make this wrong

- **If the deviations do not sum to zero**, the two systems are not being
  read in the same numeraire and every comparison in the document is void.
- **If composition and deviation do not co-rank** (allowing for 5.5), the
  Marxian account of absolute rent does not describe this economy, and the
  right response is to report that rather than to reach for a different
  definition of composition until one fits.
- **If `v` is computed from the money wage** rather than the value of
  labor-power, the composition is a price ratio wearing a value's name. The
  project has made exactly this class of substitution three times now
  (`docs/30`, `docs/37` §3.7, `docs/39` §5), and this is the fourth place it
  could happen.
