# Stage 1: the reserve army and habituation in C#: results

`docs/74` is the design. The slice is built, and its claim carries the
same caveat as `docs/73`'s and for the same reason: **the C# is written
to the contract and has not been compiled.** Four predictions held, one
half, and the half is a finding about the fixtures rather than the rules.

**The headline: the rule is exactly stationary where the circuit is, over
sixty steps and to the bit, which is `docs/46` §2's claim asserted rather
than assumed. And a sequence with frozen employment cannot reach
habituation's taken branch — the first three fixtures never turned the
ratchet, and a fourth was added because of it.**

## 1. Held: 6.2, 6.3, 6.5

**6.2** `equilibrium_stationary` holds the premium at exactly `0.0` and
the standard at exactly `1.0` for all sixty steps, in both regions, with
the bargaining strength at 1.0 and the rule therefore *running* rather
than returning early. `docs/46` §2 claimed the rule is exactly
stationary where the circuit is; the employment rate equals the seeded
reference to the bit, so the target is exactly zero and nothing moves.
`test_the_rules_are_exactly_stationary_where_the_circuit_is` asserts it
with `assertEqual` on every step.

This is the prediction worth having made. A rule that drifted a single
ulp a day would show sixty ulps here and pass any tolerance anyone would
think to write; it is caught only because the assertion is equality and
the fixture is a sequence.

**6.3** The laboratory is unmoved: 322 metrics at zero delta. The suite
is at 281 tests with the one pre-existing `scale_647_day3` failure that
predates this work.

**6.5** The shadow check — the C# re-implemented in Python *from the C#
source*, as `docs/73` §4 — reports:

```
compared 960 readings across 4 fixtures
max ulp 0
BIT EXACT
```

960 readings is two magnitudes × sixty steps × two regions × four
fixtures, and every one of them is compared, not only the last of each
sequence.

## 2. Held: the ratchet never falls

`docs/74` §6.4's first half. Across every fixture, every region and every
step, `habitual_scale` is non-decreasing —
`test_the_standard_ratchets_and_never_falls` asserts it over all 240
step-pairs. The upward-only clause does what `docs/51` says.

## 3. Half wrong, and it is a finding about the fixture shape

`docs/74` §6.4's second half predicted "at least one step where the
premium falls and the standard does not". No fixture shows it, and the
reason is structural rather than accidental.

**A sequence freezes employment.** The steps exercise the accumulation
and nothing else in the model runs, which is what makes the expected
values the laboratory's own call rather than a re-derivation (`docs/74`
§2). But with the employment rate held still the target premium is a
constant, so the premium converges to it *monotonically*: it cannot fall
and then be overtaken. The wage-below-value crossing is a property of a
real history, not of an iterated rule.

Worse, and only visible once it was looked for: the three fixtures
`docs/74` §5 specified **never reach `_habituate`'s taken branch at all.**
`boom_reversal_habituating` starts with the premium at −0.00244 and the
standard at 1.02230, so the gap is negative for all sixty steps and the
rule returns at the `if` every time. The sequence was exercising the
early return and the untaken branch, and the design did not notice
because it reasoned about what the *scenario* contains rather than what a
*frozen sequence* of it does.

`boom_habituating` — `demand_boom` with both rules on, taken mid-boom —
was added for this. There the premium is 0.01269 against a standard of
1.00721, the gap is positive, and the standard rises on **59 of 59**
step-pairs, ending at 1.02383. The taken branch is now covered.

The rule this leaves for the rest of the port, next to `docs/73` §2's:
**a fixture must be checked for which branches it actually takes, not
which branches its scenario contains.** A sequence is a different object
from the history it was drawn from, and the difference is exactly the
kind of thing a coverage claim gets wrong.

## 4. What is not verified

Unchanged from `docs/73` §5 and now doubled:

1. **Neither this slice's C# nor the wage slice's has been compiled.**
   Two slices are stacked unbuilt, which `docs/73` §6 warned against and
   `docs/74` §7 accepted with its eyes open.
2. The mitigation held up in the writing: `BargainingSolver.cs`
   references nothing from `WageSolver.cs`, and the harness runs the
   three fixture directories separately and returns the first non-zero
   code, so a failure in one does not mask the other.
3. **No third unbuilt slice.** `docs/74` §7 set this rule and it stands.
   The next session with a toolchain runs
   `dotnet run --project economy_mod/Source/Economy.Core.Check`, which
   now checks all three directories, before writing anything new.

## 5. Where the port stands

Three of `docs/50` §6's layers are written:

| slice | docs | built | measured |
|---|---|---|---|
| the value solve | 53, 54 | yes | **yes** — 1,494 values, zero ulps |
| the basket and the wage | 72, 73 | no | shadow only — 112 readings |
| the reserve army and habituation | 74, 75 | no | shadow only — 960 readings |

What remains in Phase C after the compile: the regional price update,
`_update_wage_costs` with the process graph behind it, the daily tick
amortised across ticks, the full economic state through save and load,
the UI, and the `MarketValue` wealth coupling. The port is at the point
where the *arithmetic* slices are nearly done and the *engineering*
slices — persistence, scheduling, UI — have not started; `HANDOFF.md`'s
"the economics is the part that is nearly solved" applies to the port as
much as to the laboratory.

## 6. Cost

Four fixtures of sixty steps, about eleven seconds to generate; the suite
at eighty seconds; the shadow under a second. No game was run.
