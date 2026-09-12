# Stage 1: the reserve army and habituation in C#: design

Written before implementation. `docs/54` §6 named this third in
`docs/50` §6's order and `docs/73` §6 confirmed it: the two rules that
*move* the premium and the standard that `docs/72`'s slice took as
inputs. `docs/53`'s determinism contract — transliterate, do not
translate — and `docs/73` §2's rule — a fixture carries the state a
magnitude is computed against — both govern here without restatement.

## 1. What is in it

Two methods, twenty lines of Python between them:

| laboratory | what it is |
|---|---|
| `Economy._bargain` | the premium closes a fraction of the gap to what the reserve army allows (docs/46) |
| `Economy._habituate` | the standard closes a fraction of the gap to the paid real wage, **upward only** (docs/51) |

Together with `docs/72`'s slice this closes the wage: that one reads the
premium and the standard, this one writes them, and nothing else in the
model does.

**Out of scope, with a reason.** `_update_wage_costs` also reads
`wage_rate` and is the wage's reach into every producer's cost — it is
the obvious next thing and it is not this slice, because it needs
`Process.labor_per_unit` and with it the process graph, which is a
surface several times this one's. It goes with the cost slice, not the
wage slice.

## 2. Why this slice is small and still worth a document

Both rules are two lines of arithmetic. What makes them worth the same
care as the value solve is that they are the model's only **stateful
accumulators outside the ledger**: `wage_premium` and `habitual_scale`
are carried from day to day by `+=`, so an error of one ulp on day one is
compounded by every day after it. The value solve iterates to a fixed
point and forgets where it started; these do not forget.

That changes what a fixture has to be. A single application proves
almost nothing — a wrong rounding survives one step. The fixtures here
are therefore **sequences**: the laboratory's own method called N times
on a copy, with the state after every step recorded, so that a port that
drifts is caught on the step it starts drifting.

## 3. The three places bit-exactness can break here

**The early return.** Both methods return before touching anything when
their parameter is zero, and both comments say why: a model without the
rule must be bit-identical rather than merely close. A port that
multiplied by a zero strength instead would agree to the bit on every
fixture here and diverge the first time a scenario used a negative
premium and a zero speed, because `x + 0.0 * y` is not `x` when `y` is
infinite or NaN and is `-0.0 + 0.0` when `x` is negative zero.
**Transliterate the branch.**

**The compound assignment.** `region.wage_premium += speed * (target -
premium)` is one rounding of the product, one of the difference, and one
of the sum, in that order. Written as `premium = premium * (1 - speed) +
speed * target` — algebraically identical, three different roundings —
it would be wrong. The C# is `WagePremium += ...` with the same
parenthesisation.

**The upward-only comparison.** `if gap > 0.0` where `gap` may be
negative zero: `-0.0 > 0.0` is false in both languages, so this one is
safe, and it is written down because the next person to read it should
not have to re-derive that.

## 4. What is built

```
economy_mod/Source/Economy.Core/
    BargainingSolver.cs     the two rules, and the state they move
economy_mod/Source/Economy.Core.Check/
    BargainingCheck.cs      a third fixture directory, same two comparisons
economy_mod/Source/Fixtures/bargaining/
economy_lab/bargaining_fixtures.py
```

A separate file and a separate harness entry, deliberately.
`docs/73` §5 left the wage slice's C# **unbuilt**, and this session
cannot build either — so two slices are now stacked unbuilt, which
`docs/73` §6 warned against. The mitigation is that each slice's C# is
independent: `BargainingSolver.cs` references nothing from
`WageSolver.cs`, so a compile error in one does not hide a compile error
in the other, and the harness reports the three directories separately.
That is a worse position than building each slice as it lands and it is
the best available one; §7 says what to do about it.

## 5. The fixtures

Three economies, each run as a sequence of at least sixty steps, both
regions:

| fixture | what it exercises |
|---|---|
| `equilibrium_stationary` | both early returns *not* taken and the gap exactly zero: the premium and the standard must stay at 0.0 and 1.0 to the bit for sixty days |
| `boom_bargaining` | a positive gap, the premium climbing, habituation off |
| `boom_reversal_habituating` | both rules on, the standard ratcheting up and the premium later falling below it |

The first is the sharpest. `docs/46` §2 claims the rule is *exactly*
stationary where the circuit is — the employment rate equals the seeded
reference to the bit, so the target is exactly zero — and a port that
drifted by one ulp a day would show 60 ulps of drift here while passing
any tolerance anyone would write.

Each step records the premium and the standard **after** it, and the
employment rate and reference the step read, because §2's rule from
`docs/73` applies to state as much as to ledgers.

## 6. Predictions

6.1 Every fixture reproduces to the bit, on every step, not only the last.

6.2 `equilibrium_stationary` holds the premium at exactly `0.0` and the
standard at exactly `1.0` for all sixty steps, in both regions, in the
laboratory. If it does not, `docs/46` §2's stationarity claim is wrong
and that is a finding about the model rather than the port.

6.3 The laboratory is unmoved: 322 metrics at zero delta.

6.4 `boom_reversal_habituating` shows the ratchet: the standard is
non-decreasing across every step, and there is at least one step where
the premium falls and the standard does not. That is the wage below the
value of labor-power, which is the scenario `docs/51`'s upward-only
clause exists for.

6.5 The shadow check of `docs/73` §4 is extended to the new rules and
reports zero ulps across every step of every fixture. This is the only
verification available in this environment and its limits are exactly
those `docs/73` §4 named.

## 7. What this slice cannot verify, and what to do about it

Still no .NET SDK; still blocked from installing one. So, as in
`docs/73`: written to the contract, not measured against it.

**Two unbuilt slices is the real cost of continuing.** The honest
accounting: the first build on a machine with the SDK now has to work
through whatever is wrong in *both*, and the slices were written by
someone who could not see a compiler error. Against that, the fixtures
and the shadow catch the class of error that matters most — order,
branch and accumulation — and a compile error is loud, local and cheap to
fix, where a silent arithmetic divergence is none of those.

The rule this sets for the rest of Phase C: **no third unbuilt slice.**
The next session with a toolchain builds both and closes `docs/73` §5
before anything else is written.

## 8. Cost

One C# file of about a hundred lines, a generator, three fixtures of
sixty steps each, a harness entry and three tests. The economies are the
ones `docs/72` already built. Well under a session.
