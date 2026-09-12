# Stage 1: the basket and the wage in C#: design

Written before implementation. `docs/54` §6 names the next slices of the
port in `docs/50` §6's order, and this is the first of them: **the basket
and the wage**. `docs/53` is the template and its determinism contract —
*transliterate, do not translate* — governs here without restatement.

## 1. Why this slice, and what is in it

The value solve was the bottom of `docs/50` §6's order because a hired
worker's labor-power has a value only if the region can solve one. The
wage is the next layer up and it is what a player actually sees: a number
of silver a day, against a number of work-ticks a day, with the gap
between them the surplus the colony lives on. `docs/50`'s four player
decisions all read it.

It is also a slice with a strong reference and a small surface. Five
functions and one settlement routine:

| laboratory | what it is |
|---|---|
| `Region.basket_cost` | silver per worker-day, the basket at current **prices** |
| `Region.wage_rate` | the basket times one plus the premium |
| `Economy.basket_labor_value` | work-ticks per worker-day, the basket at social **values** |
| `Economy.value_of_labor_power` | that, times the habitual standard |
| `Region.employment_rate` | yesterday's employment over the labor pool |
| `Region.premium_over_value` | what the paid wage carries above the standard |
| `Economy._settle_labor` | the quantization, the wage bill, and four ledger postings |

**The premium and the standard are inputs to this slice, not outputs.**
`wage_premium` and `habitual_scale` are read as state. The rules that
*move* them — the reserve army (`docs/46`) and habituation (`docs/51`) —
are the slice after this one, exactly as `docs/54` §6 ordered them. That
boundary is what keeps this slice small enough to fail cheaply.

**What is deliberately out:** `_pay_wages` (docs/55's producer-level
cash), which belongs with the purses, and `_workers_consume`, which is a
market and not a wage.

## 2. The three places bit-exactness can break here

`docs/53` §3 found two — CPython's compensated `sum()` and dictionary
order — and both recur. A third is new to this slice.

**Compensated summation, again.** `basket_cost` and `basket_labor_value`
are both `sum(...)` over a generator, so both take Neumaier compensation.
`CompensatedSum` already exists and is used unchanged.

**Sorted order, not insertion order.** Both sums iterate
`sorted(self.subsistence_basket.items())` — Python's string sort, which
is ordinal by code point. C#'s default string comparison is *culture-
aware* and would order differently for any basket whose names differ
outside ASCII, and the summation order changes the last bit. Every sort
in the port is `StringComparer.Ordinal`, and this document says so once
so that later slices inherit it.

**The skipped multiply.** `wage_rate` returns `basket` unchanged when
`wage_premium == 0.0`, and `value_of_labor_power` returns the basket
unchanged when `habitual_scale == 1.0`. Both comments say why: `x * 1.0`
is not always `x` in the sense that matters — it is here for finite `x`,
but the laboratory made the skip explicit so that a model without the
rule reads the same bits it always did, and a port that "simplifies" the
branch away is a port that can diverge the first time someone changes the
neutral value. **Transliterate the branch.**

A fourth is not a float question but will bite as hard. `_settle_labor`
quantizes employment with `floor(x / q) * q`. `Math.Floor` and Python's
`math.floor` agree on doubles, but Python's `floor` returns an *int* and
the multiply that follows is int × float. For the grid values in use the
two are identical; the port must still do the division, the floor and the
multiply in that order and not fold them.

## 3. What is built

```
economy_mod/Source/Economy.Core/
    WageProblem.cs      the basket, the prices, the values, the state it reads
    WageSolver.cs       the six functions and the settlement, transliterated
economy_mod/Source/Economy.Core.Check/
    Program.cs          a second fixture directory, same two comparisons
economy_mod/Source/Fixtures/wages/
    written by the laboratory
economy_lab/fixtures.py
    wage_problem / wage_fixture, the same shape as the value solve's
```

The library still references nothing from RimWorld. Nothing is copied
into the game's folder and `verify.py`'s expected surface does not
change; loading any of `Economy.Core` in the game remains a separate step
with a human at the game, as `docs/54` §6 left it.

## 4. The fixtures

The same shape as `docs/53` §2's, and for the same reason: inputs in the
laboratory's order, expected outputs from the laboratory's own call, so
the fixture cannot be a copy of a number the model already had.

Four economies, chosen so that every branch in §2 is taken by something:

| fixture | what it exercises |
|---|---|
| `equilibrium_day60` | the neutral case: premium 0, standard 1, both skips taken |
| `wage_deviation_day120` | a premium in force, so `wage_rate`'s multiply happens and `wage_premium_paid` posts |
| `habituation_day240` | a standard that has moved, so `value_of_labor_power` multiplies and the two-branch deviation takes its second arm |
| `capital_goods_day60` | nine commodities, so the basket sums over more terms and Department I is in the values |

Each writes both regions, because the basket, the prices and the premium
are regional and the labor values are not — and a port that read social
values regionally would pass a one-region fixture.

## 5. Predictions

5.1 Every fixture reproduces **to the bit**, zero ulps, on every reading:
the two silver magnitudes, the two labor magnitudes, the employment rate,
the premium over value, and the four ledger postings.

5.2 The laboratory is unmoved: `python -m economy_lab.baseline` zero
deltas on all 322 metrics, because nothing in `economy_lab/` changes
except a fixture generator that only reads.

5.3 `tests/test_port_fixtures.py` grows a case for the new directory and
fails the moment the model moves without the fixtures being regenerated,
which is what it is for.

5.4 The neutral fixture's `wage_rate` equals its `basket_cost` **bit for
bit**, and its `value_of_labor_power` equals its `basket_labor_value` bit
for bit. That is §2's skipped multiply asserted as a property rather than
as a hope.

5.5 The deviation fixtures' postings satisfy the identity `docs/47` §3
states: `wages_paid = necessary_labor's money form + wage_premium_paid`,
within the model's own tolerance, on both sides of the port.

## 6. What would make this wrong

If any reading is within `1e-9` but not to the bit, the contract
`docs/54` established has already failed on its second slice, and the
cause is almost certainly one of §2's three — check the sort first, then
the compensation, then the branch.

If the *laboratory* moves when the fixture generator is added, the
generator is not read-only; it must not call anything that mutates, and
`docs/53`'s generator restores the economy after each solve precisely
because the value solve does mutate.

If a fixture cannot be built because no scenario takes a branch — most
likely the two-armed deviation in `_settle_labor` — then that branch is
unreachable in every scenario the laboratory has, and it should be said
so rather than covered by a synthetic economy invented to reach it.

## 7. What this slice cannot verify here

**The C# is not compiled in this session.** This environment has no .NET
SDK and the network policy blocks Microsoft's distribution host, so
`WageProblem.cs`, `WageSolver.cs` and the harness change are written and
reviewed but **not built and not run**. The Python side — the fixture
generator, the committed fixtures and the test — is complete and
verified here.

That is a real gap and it is recorded as one rather than papered over:
`docs/73` cannot claim bit-exactness until `dotnet run --project
economy_mod/Source/Economy.Core.Check` has been run on a machine with the
SDK, which is a step for the Windows or Mac checkout. Until then the
claim is "written to the contract", not "meets it". `docs/54`'s claim was
measured; this slice's must not borrow its authority.

## 8. Cost

Two C# files of a few hundred lines, a generator beside the existing one,
four fixtures, a harness case and a test. The fixtures are cheap — the
dearest economy is 240 days of a six-commodity circuit. One session,
plus one build-and-run on a machine with the SDK.
