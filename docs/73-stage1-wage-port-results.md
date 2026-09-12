# Stage 1: the basket and the wage in C#: results

`docs/72` is the design. The slice is built. **Its claim is weaker than
`docs/54`'s and deliberately so**: the C# was written to the contract and
has not been compiled, because this environment has no .NET SDK and the
network policy blocks Microsoft's distribution host. `docs/72` §7 said
that in advance so the claim could not be quietly borrowed from the
previous slice.

**The headline: the fixture set is complete, every branch of the wage is
taken by some fixture, and the transliteration's order and arithmetic
reproduce the laboratory on all 112 readings to the bit. What is
unverified is that the C# compiles and runs — one command on a machine
with the SDK, and `docs/72` §5.1 is then either measured or refuted.**

## 1. What was built

| file | what |
|---|---|
| `economy_lab/wage_fixtures.py` | the generator, beside `fixtures.py` |
| `economy_mod/Source/Fixtures/wages/*.json` | four fixtures, both regions each |
| `economy_mod/Source/Economy.Core/WageProblem.cs` | the inputs and the running totals |
| `economy_mod/Source/Economy.Core/WageSolver.cs` | six readings and the settlement |
| `economy_mod/Source/Economy.Core.Check/WageCheck.cs` | the harness, same two comparisons |
| `tests/test_port_fixtures.py` | four cases, and the existing class renamed in spirit |

The library still references nothing from RimWorld, nothing was copied
into the game's folder, and `verify.py`'s expected surface is unchanged.

## 2. The fixture shape changed, and the reason is a finding

`docs/72` §4 planned to record what a settlement *posted* — a difference.
That is wrong, and the fixtures caught it before the C# did.

`Ledger.add` accumulates onto a running total, and `_settle_labor` pays
the bill with `region.cash -= wage_bill`. So what a day posts depends on
what was already there. In `equilibrium_day60`:

```
wages_paid  posted   +13.326840677261316
cash        moved    −13.326840677254950
```

The same wage bill, against a purse of 94,246 silver and a ledger total
of 2,460: the subtraction from the large purse loses low bits the ledger
posting keeps. **A fixture of differences would have let the port agree
with the fixture while disagreeing with the model** — it would have
reproduced a number the laboratory itself does not compute. The fixtures
now carry `before` and `after` absolute, and the port posts onto the
totals it is given. `test_the_settlement_totals_are_absolute_and_not_differences`
asserts the effect is real rather than theoretical, so the shape cannot
be simplified back without something failing.

This is the same class of error `docs/33` found with `+=` against
`sum()`, and it is worth naming as a rule for the rest of the port:
**a fixture must carry the state a magnitude is computed against, not
only the magnitude.**

## 3. Every branch is taken

`docs/72` §6 said that if a branch could not be reached by any scenario,
that should be said rather than covered by an invented economy. All four
are reachable:

| fixture | premium | standard | branch |
|---|---:|---:|---|
| `equilibrium_day60` | 0 | 1 | both multiplies skipped |
| `capital_goods_day60` | 0 | 1 | skipped, over nine commodities |
| `wage_deviation_day180` | **+0.010389** | 1 | `wage_rate` multiplies; deviation's first arm |
| `habituation_day240` | **−0.002669** | **1.022299** | `value_of_labor_power` multiplies; deviation's second arm |

The last one is the interesting one and it was not forced: `boom_reversal`
with habituation leaves the standard where the boom put it and the
premium **negative**, so the fixture that exercises the second arm is
also the wage-below-value case `docs/51` exists for. Its posted
`wage_deviation_labor` is −6.86 work-ticks on the day.

In every fixture the second region is neutral while the first is not,
which is the one-region trap `docs/72` §4 named: a port reading social
values regionally would pass a single-region fixture and fail these.

## 4. What was verified here, and how

`docs/72` §5.2 and §5.3 held: the laboratory is unmoved — 322 metrics at
zero delta — and the test suite is green at 276 tests, with the one
pre-existing `scale_647_day3` failure that predates this work and fails
with every change stashed.

§5.4 held exactly: in the neutral fixtures `wage_rate == basket_cost` and
`value_of_labor_power == basket_labor_value`, bit for bit, which is the
skipped multiply asserted as a property.

**The transliteration was then checked by shadowing it.** Since the C#
cannot be run here, its logic was re-implemented in Python *from the C#
source rather than from the model* — the ordinal sort, the compensated
sum, both skipped multiplies, the floor-then-multiply, and the running
totals — and run against the committed fixtures:

```
compared 112 readings across 4 fixtures
max ulp 0
BIT EXACT
```

That is a real check of the part most likely to be wrong — the order of
the terms, the branch structure, and what each magnitude accumulates onto
— and it is **not** a check that the C# compiles, that .NET's doubles
behave as expected, or that `StringComparer.Ordinal` agrees with Python's
sort on any name outside ASCII. The shadow is not committed: a second
implementation of the same rule is a maintenance liability, and its job
was done the moment it ran.

## 5. What is not verified, precisely

1. **The C# does not compile in this session.** Not "probably compiles" —
   unrun. Syntax, accessibility (`Program.Comparison` and `Program.Compare`
   were widened from `private` to `internal` for the new harness) and the
   project files are unchecked.
2. **`docs/72` §5.1 is unmeasured.** The bit-exactness claim for the port
   itself stands or falls on
   `dotnet run --project economy_mod/Source/Economy.Core.Check`, which now
   runs both fixture directories and returns non-zero if either is not
   exact.
3. **`docs/72` §5.5's identity is unchecked** on the C# side; it holds in
   the laboratory, which is where `docs/47` §3 established it.
4. **Ordinal against code point.** C# `StringComparer.Ordinal` compares
   UTF-16 code units and Python compares code points; they agree on every
   name in the model, all ASCII, and would diverge only for a basket good
   named outside the basic plane. Worth a line in whatever names goods at
   game scale.

## 6. The next slice, and a note on ordering

`docs/54` §6's list after this one: **the reserve-army premium and
habituation** — the rules that move the two magnitudes this slice took as
inputs. They are the natural next slice and they now have a fixture
generator shaped for them: the same four economies already carry the
premium and the standard as state, and what is missing is only the day's
update.

**The unbuilt C# should be built before that.** Two unbuilt slices
stacked would mean a compile failure in the first is discovered while
debugging the second, which is exactly the confusion `docs/53` §1 chose a
small first slice to avoid. One `dotnet run`, then `docs/74`.

## 7. Cost

Four fixtures — the dearest is 240 days of a six-commodity circuit —
about nine seconds to generate, the suite at 65 seconds, and the shadow
at under a second. No game was run and none was needed.
