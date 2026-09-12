# Stage 1: the regional price update in C#: results

`docs/77` is the design. The slice is built, compiled and run.

**The headline: the price rule is bit-exact under Mono, `exp` included —
48 of 48 prices, zero ulps. The transcendental was not the problem. What
the measurement did find is a defect in Mono's *decimal parser*, which
first showed up as a false failure in this slice's own harness and is a
real hazard for the save/load work in Phase C's engineering half.**

## 1. Held: 6.1, 6.3, and 6.2 better than predicted

**6.1** `equilibrium_day60` moves no price at all. At the seed the
pressure is exactly `0.0`, `exp(0.0)` is exactly `1.0`, the desired price
is exactly the anchor and the anchor is exactly the reference, so the
damped step moves nothing. Asserted with equality in
`test_the_stationary_circuit_does_not_move_its_prices`.

**6.2** `docs/77` declined to predict bit-exactness for the three
fixtures whose pressure is non-zero, and said that agreement would mean
"both runtimes reached the same libm, not that the port earned it". They
agree — **all 48 readings across all four fixtures, zero ulps** — and
that reading of the result stands. CPython's `math.exp` and Mono's
`Math.Exp` both end up in the platform's glibc here; a different
platform's libm may not, and the `exp` question is answered for this
machine rather than settled.

So the determinism contract survives its first transcendental. It
survives it *contingently*, and the contingency is worth writing into
`HANDOFF.md` rather than forgetting.

**6.3** The laboratory is unmoved: 322 metrics at zero delta, suite at
285 tests with the one pre-existing `scale_647_day3` failure.

## 2. A false failure, and the diagnosis that matters

The first run of the price driver reported:

```
price readings compared 48, exact 47, max ulp 1
  input_shortage_day90/Green River/chemfuel:
    expected 2.2998477131672592 got 2.2998477131672588 (1 ulp)
```

Which is exactly what `docs/77` §1 said a failure would look like, in
exactly the fixture built to make `exp` work hardest. The obvious
conclusion was the wrong one, and it took four steps to rule out:

1. **Compute the pressure for that reading.** It is exactly `0.0`, so
   `exp` returned exactly `1.0`. The transcendental was never in it.
2. **Compare every parsed input, bit for bit.** All identical.
3. **Step the whole expression in both languages from the same
   constants.** Both give `400266168eceab8d` — the same double. Python's
   `repr` prints it `2.299847713167259` and C#'s `"R"` prints it
   `2.2998477131672588`; two spellings of one number, which is what made
   the driver's message look like a real disagreement.
4. **Look at what the driver compared.** It compared the computed double
   against the fixture's expected value *as Mono's `double.Parse` had
   read it* — and that parse is wrong by one ulp.

The lesson is about instruments, not about the port: **a comparison must
not run through the component under suspicion.** The fixed driver passes
inputs and receives outputs as hexadecimal bit patterns, with Python
doing the comparison, so no decimal parser is on the path at all:

```
input  mismatches 0
output mismatches 0 of 48
```

## 3. The real finding: Mono's `double.Parse` is not correctly rounded

```
                     Mono double.Parse   CPython float()
2.299847713167259    400266168eceab8e    400266168eceab8d
0.1                  3fb999999999999a    3fb999999999999a
1.05                 3ff0cccccccccccd    3ff0cccccccccccd
866.1699304563492    408b115c047fc4ea    408b115c047fc4ea
41.97                4044fc28f5c28f5c    4044fc28f5c28f5c
```

Short decimals are fine; the 16-significant-digit one is a ulp out. This
is a known weakness of Mono's strtod path and it is not going to be
fixed for us.

**Why it matters beyond this driver.** RimWorld runs on Mono, and Phase C
still has to put *the full economic state through save and load*. If any
of that state round-trips through decimal text — which is what
`Scribe_Values` does for a `double` — then the state that comes back is
not bit-identical to the state that went in, and the laboratory's
exactness discipline stops at the save file. That is a design
constraint on the persistence slice, discovered by accident and worth
more than the slice that found it:

> **Persist doubles as bits, not as decimal.** `BitConverter.DoubleToInt64Bits`
> into a `long`, or the round-trip is not one.

The save/load slice should be designed around that from the start rather
than discovering it in a reload-determinism check, which is exactly what
`EconomyWorldComponent`'s existing check would have caught eventually —
loudly, and much later.

**It does not cast doubt on `docs/76`.** A mis-parse can only manufacture
a *failure*: the expected value is read wrong and disagrees with a
correctly computed one. It cannot manufacture a pass, because that would
need the computed value to be wrong in exactly the same direction. The
4,060 readings that matched, matched.

## 4. Where Phase C stands

Four slices ported, compiled, and bit-exact under the runtime the game
uses:

| slice | docs | readings | exact |
|---|---|---:|---|
| the value solve | 53, 54 | 2,988 | .NET 8 and Mono |
| the basket and the wage | 72, 73 | 112 | Mono |
| the reserve army and habituation | 74, 75 | 960 | Mono |
| the regional price update | 77, 78 | 48 | Mono, `exp` included |

One arithmetic slice is left — `_update_wage_costs`, which drags in
`Process.labor_per_unit` and the process graph with it — and after that
the model's planned core is ported.

The engineering half is untouched and is the larger half: the daily tick
amortised across ticks, the full state through save and load (now with a
known constraint on it, §3), the UI, and the `MarketValue` wealth
coupling. **None of those can be finished without the game running**,
and that remains a human's step, not this environment's.

## 5. Cost

Four fixtures, one compile, five runs of the driver and two of a
throwaway one written to settle §2. The diagnosis cost more than the
slice, and produced the finding.
