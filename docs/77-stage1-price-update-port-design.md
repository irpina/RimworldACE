# Stage 1: the regional price update in C#: design

Written before implementation. `docs/54` §6 named this second in its
list and `docs/76` §6 leaves it as one of two arithmetic slices still
unported. It is taken now because it is the slice that tests the
determinism contract's hardest case, and that question should be
answered before the engineering half of Phase C rather than during it.

**Answered by `docs/78`:** outcome 1 — the two libms agree on these
inputs and all 48 readings are exact. The slice found a defect anyway,
in Mono's *decimal parser* rather than its `exp`.

## 1. Why this slice is the interesting one

Every ported line so far has been `+`, `-`, `*`, `/` and comparison.
IEEE 754 specifies all of those to the bit, which is why `docs/76` got
4,060 readings with zero ulps and why it was never really in doubt once
the summation order and the branch structure were right.

`_update_prices` calls **`exp`**.

`exp` is *not* specified to the bit by IEEE 754. CPython's `math.exp` is
the platform libm's; Mono's `Math.Exp` is its own or the platform's
depending on build; .NET 8's is a different implementation again. Two
correctly-rounded implementations would agree, but almost no libm
guarantees correct rounding for `exp` — the usual guarantee is under one
ulp, which is exactly the size of disagreement this project's whole
method treats as fatal.

So this slice asks a question the previous three could not:

> **Does the transliteration contract survive a transcendental?**

The honest possibilities, all of them acceptable outcomes to *report*:

1. They agree to the bit on these inputs. Likely if both end up in the
   same glibc `exp`, and it would say the contract holds here without
   proving it holds everywhere.
2. They differ by an ulp or two. Then the contract as `docs/54` stated
   it — transliterate and check to the bit — **cannot be met for any
   slice containing `exp`**, and Phase C needs a decision: ship a
   correctly-rounded `exp` in `Economy.Core`, or accept a divergence and
   change what the laboratory's reference means.
3. They differ wildly, which would mean an argument error rather than a
   rounding one.

`docs/53` §1 chose the value solve first because it was "the smallest
slice that can fail in the way the whole port could fail". This is the
smallest slice that can fail in the *other* way the port could fail, and
it has been sitting unasked for three slices.

## 2. What is in it

`Economy._update_prices`, the branch taken when `posted_prices` is off —
the planned model's price rule, which is what the reference still
follows (`docs/71` §5). Thirty-five lines:

- the throughput guard, which leaves a price alone rather than driving it
  to the floor on a division by nothing;
- the coverage gap and the unmet-demand ratio;
- the pressure, and `exp` of it;
- the cost anchor, written as `1 + kappa * (ratio - 1)` so that it is
  exactly `1.0` at a ratio of exactly `1.0` for any kappa — the thing
  that keeps the four-year equilibrium price range at exactly zero;
- the clamp to the authored band, and the damped step toward it.

**Out of scope:** `_update_posted_prices`, which is the market model's
rule and belongs with the market slices; and `_dispatch_arbitrage`, which
reads prices but is a different mechanism.

## 3. Places bit-exactness can break

Beyond `exp`, which is §1:

**`max(target, EPSILON)` and the clamp.** Python's `max`/`min` return the
*first* argument on a tie and propagate NaN differently from .NET's
`Math.Max`/`Math.Min`, which return NaN if either argument is NaN.
Neither difference is reachable with finite positive inputs here, and
both are written as the laboratory writes them rather than reasoned
around.

**`region.cost_ratio.get(name, 1.0)`.** A missing key means exactly
`1.0`, which makes the anchor exactly the reference price. A port that
defaulted to `0.0` would put the anchor at `reference * (1 - kappa)` and
the equilibrium would drift immediately.

**The order of the final step.** `old + speed * (desired - old)` is one
subtraction, one multiply, one add. Any algebraic rearrangement rounds
differently, as `docs/74` §3 said of the premium.

## 4. What is built

```
economy_mod/Source/Economy.Core/PriceSolver.cs       the rule and its inputs
economy_mod/Source/Fixtures/prices/                  four fixtures
economy_lab/price_fixtures.py                        the generator
```

The harness is **not** extended this time. `Economy.Core.Check` still
does not compile in this environment (`docs/76` §5: `System.Text.Json`),
so adding a fourth directory to it would add unverifiable code to an
unverified file. The scratchpad Mono driver `docs/76` §3 used covers this
slice instead, and the harness gets all four directories in one edit on
a machine that can build it.

## 5. The fixtures

Four economies, one call to `_update_prices` each, both regions and
every commodity — the rule is a single pass, so a sequence adds nothing
that a second fixture would not:

| fixture | what it exercises |
|---|---|
| `equilibrium_day60` | the stationary case: pressure exactly zero, `exp(0.0)` exactly 1.0, prices unmoved to the bit |
| `regional_glut_day120` | a large positive inventory, so the gap is negative and `exp` runs well below one |
| `input_shortage_day90` | unmet demand, so the second pressure term is non-zero and `exp` runs above one |
| `technique_change_day120` | a moved cost ratio, so the anchor is not the reference price |

`equilibrium_day60` is the sharp one for the same reason it was in
`docs/74` §5: at the seed the pressure is exactly zero, so `exp` is
called with exactly `0.0` and must return exactly `1.0`. Every libm does.
That is the one `exp` result that is safe, and it is worth having a
fixture that isolates it, because if the others disagree by an ulp this
one still tells us the argument is being computed identically.

## 6. Predictions

6.1 `equilibrium_day60` reproduces to the bit and its prices do not move:
the stationary claim, and the `exp(0.0)` case.

6.2 The other three reproduce **within one ulp**, and this document
declines to predict bit-exactness. Recording that refusal in advance is
the point: if they come out exact, it is because both runtimes reached
the same libm, not because the port earned it, and the next `exp` on a
different machine may not.

6.3 The laboratory is unmoved: 322 metrics at zero delta.

6.4 If §6.2 is not exact, the worst disagreement is **1 ulp on the price
itself** and not on the pressure: `exp` is the only unspecified step, and
the damped step that follows it divides the error by the adjustment
speed rather than amplifying it.

## 7. What would make this wrong

If the pressure disagrees before `exp` is called, the fault is in the
coverage gap or the unmet ratio and §3 names the two candidates.

If `equilibrium_day60` moves, the stationary claim is broken in the port,
and since the same claim is asserted in the laboratory's own tests that
would be a port error rather than a model finding.

If the disagreement is larger than a few ulps, `exp` is being called with
a different argument, which is §3 again and not the transcendental.

## 8. Cost

One C# file of about eighty lines, a generator, four fixtures, one Mono
run and three tests. The dearest economy is 120 days of a six-commodity
circuit.
