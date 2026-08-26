# Absolute rent: results

`docs/42` set out to test Marx's account of absolute rent against the model's
own quantities rather than assume it. Five predictions: three right, two
wrong — and the wrong ones produced a sharper result than the right ones.

**The headline: Marx's foundation for absolute rent holds exactly in a
circulating-capital economy, and fixed capital breaks it.**

## 1. What shipped

Three measurements, no mechanism: `sector_organic_composition`,
`price_value_deviation`, `absolute_rent_bound`. Six metrics frozen, 183 tests.

The mechanism is deliberately absent and `docs/42` §2 explains why. Absolute
rent cannot be a *transfer* here, because producers hold no cash and the
region that would receive the rent is also the region that would pay it —
`Region.reserves` is regional property. A separate landowner needs a
consumption pattern before rent can flow at all, or regional cash drains
until the wage bill fails. A third income class is its own session.

`docs/42` §4 also specified an `absolute_rent_fraction` price effect and
§6 test 4 was written to check it defaults to zero. Neither exists: the
parameter was not added, because a dead knob is worse than a named absence.
Test 4 is void and is recorded as such rather than quietly dropped.

## 2. Right: 5.2, 5.4, and the composition ordering at the extremes

**5.4 The deviations sum to exactly zero.** Predicted, and measured at
6.6e-17 of total value — floating-point zero. This is the quantitative form
of the proposition that redistribution through the price system creates no
value, so absolute rent can only be a **deduction from surplus value, never
an addition to it**. The model can now say that to machine precision instead
of by argument.

**5.2 Chemfuel's absolute-rent bound is 75.7% of its value.** Predicted
"roughly 75%". Chemfuel's production price is 0.243 of its labor value, the
largest deviation of any commodity in the model, and that gap *is* the room
landed property would have. In flow terms it is 229.08 work-ticks a day.

**5.1's substance, if not its ranking.** Yayo (30.56) and components (3.63)
are the two highest compositions, exactly as predicted.

## 3. Wrong: 5.1's ranking

Predicted chemfuel would have the lowest organic composition in the model.
It is **fifth**:

| sector | c/v | p/λ |
|---|---:|---:|
| steel | 0.0000 | 0.068546 |
| wood | 0.0000 | 0.068546 |
| herbal medicine | 0.0013 | 0.069266 |
| meals | 0.0329 | 0.183625 |
| chemfuel | 0.0502 | 0.243112 |
| garments | 0.4036 | 0.111124 |
| psychoid leaves | 0.7764 | 0.203413 |
| components | 3.6291 | 0.430675 |
| yayo | 30.5571 | 1.459577 |

Steel and wood have **exactly zero** constant capital — no material inputs
and no plant at all, being hand labor against a deposit or a tree. I wrote
the prediction before Department I existed in my head as a set of sectors,
and forgot the two it had added. The reasoning behind it was right: chemfuel
has no material inputs and holds 1.9% of the economy's plant, so its `c` is
nearly nothing. It just is not the *smallest* nearly-nothing.

Regional average composition is 14.4394, so **eight of nine sectors are below
average and one is above.** Yayo alone carries the positive deviation that
balances the other eight.

## 4. Wrong, and this is the result: 5.3

Predicted the deviation would rank the sectors the same way the composition
does — Marx's step 2, that a below-average composition means a value above
the price of production.

Look at the table above. Garments has a composition **eight times** chemfuel's
and sells at 0.111 of its value against chemfuel's 0.243. The ranking is
broken, and `docs/42` §7 said the response to that is to report it rather
than to reach for a definition of composition that fits.

So the next thing was to find out what breaks it. It is not the composition
measure and it is not turnover — `docs/42` §5.5 nominated turnover as the
contaminant, and in this scenario every sector shares a 21-day turnover, so
that alibi is unavailable.

**It is fixed capital, and the test is clean:**

| economy | deviation monotone in composition? |
|---|---|
| six commodities, no plant anywhere (`equilibrium`) | **yes, exactly** |
| nine commodities, plant in the price system (`capital_goods`) | **no** |

In the plant-free circuit the ordering is perfect:

| sector | c/v | p/λ |
|---|---:|---:|
| chemfuel | 0.0000 | 0.067295 |
| meals | 0.0000 | 0.067336 |
| herbal medicine | 0.0000 | 0.067412 |
| garments | 0.3965 | 0.090771 |
| psychoid leaves | 0.7510 | 0.111043 |
| yayo | 30.4761 | 1.512740 |

Marx's step 2 holds without qualification. Add fixed capital and it fails.

### 4.1 Why

Without plant, the price system is `p_i = (1 + rτ)(M_i·p)` with a uniform
`τ`, so **every sector's markup over cost is the same number** and the
deviation reduces to `cost_i / λ_i` — the paid share of each commodity's
value. That share is monotone in the organic composition, because a sector
with more constant capital has more of its value bought rather than donated
as unpaid labor.

With plant the markup becomes `1 + rτ + r·K_i·p / cost_i`, and the new term
is sector-specific. Measured, it ranges from **11.88 for steel and wood to
38.60 for chemfuel** — a factor of three across the economy. `K/cost` is a
different ratio from `c/v` and nothing forces them to agree:

| sector | c/v | `K/cost`, days | markup over cost |
|---|---:|---:|---:|
| chemfuel | 0.0502 | 56.4 | 38.60 |
| meals | 0.0329 | 37.1 | 30.01 |
| components | 3.6291 | 31.0 | 27.15 |
| psychoid leaves | 0.7764 | 9.4 | 16.66 |
| yayo | 30.5571 | 2.7 | 13.28 |
| garments | 0.4036 | 0.6 | 12.18 |
| steel, wood | 0.0000 | 0.0 | 11.88 |

Chemfuel has a low composition *and* the heaviest plant relative to its
circulating cost, so it moves up the deviation ranking; garments has a high
composition and a wooden bench, so it moves down. They cross.

### 4.2 What that means for absolute rent

Marx's argument for absolute rent is stated for a circulating-capital
economy, and in one it is exactly right. Once fixed capital is in the price
system the argument's premise — *low composition, therefore value above
price of production* — stops being reliable, and the two have to be measured
separately rather than one inferred from the other.

For the model's one landlord this happens not to matter: chemfuel is below
average in composition **and** sells far below its value, so it has absolute
rent available on either reading. But that is a coincidence of this economy,
not a rescue of the inference. A sector could be below average in composition
and above its value — garments is only two steps away from it — and would
then have no absolute rent despite meeting Marx's stated condition.

This is a fourth instance of the pattern the project keeps finding: **a
quantity that is a reliable proxy in one accounting stops being one in
another.** `docs/30` on stocks against flows, `docs/37` §3.7 on the
composition of the advance, `docs/39` §5 on utilization, and now composition
against the price-value deviation. The rule those add up to is the same every
time: derive it, do not carry it across.

## 5. Right in an unexpected way: 5.5

`docs/42` §5.5 predicted turnover would contaminate the ranking and named it
as the thing to check before withdrawing anything. It was checked first, and
it is innocent here — every sector shares a 21-day turnover in this scenario.

But the *form* of the prediction was right: the ranking is broken by a
second sector-specific term in the markup, and turnover would be exactly such
a term if it varied. `perishable_meals` sets meals to a 4-day life, and in
that scenario turnover and fixed capital would break the ranking together.
Not measured here, and named as the obvious next check.

## 6. What is still missing

- **The rent itself.** Absolute rent remains a bound, not a flow. It needs
  producer-level cash and a landowner with a consumption pattern, which the
  handoff has listed as a separate omission since the beginning.
- **Monopoly rent proper** — price sustained *above* value by scarcity,
  rather than up to value by landed property. That is a different mechanism
  and this document does not touch it.
- **The absolute-rent bound under differential rent.** The two are computed
  independently and never interact; a full treatment would ask whether the
  marginal deposit's absolute rent is bounded by the intramarginal
  deposits' differential rent.
- **The sensitivity sweep**, still stale since the cost floor, and now the
  last thing standing between Stage 0 and a stable model.

## 7. What would make this wrong

- If `rent.deviations_sum_over_value` ever leaves floating-point zero, the
  value and price systems are not being read in one numeraire and every
  comparison here is void.
- If `rent.deviation_monotone_without_plant` stops being 1, §4's whole
  diagnosis is wrong — it rests on the plant-free case being *exactly*
  monotone, not approximately.
- If `rent.deviation_monotone_with_plant` ever becomes 1, fixed capital has
  stopped breaking the ranking and §4 is stale. Both are frozen as booleans
  for that reason.
- If `sector_organic_composition` is ever rebuilt on the money wage instead
  of the value of labor-power, it becomes a price ratio wearing a value's
  name. There is a test that doubles every price and requires the
  composition not to move.
