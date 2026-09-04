# Stage 1: the value solve in C#: results

`docs/53` set out six predictions. Five held, one is half-testable and the
testable half held, and the one that was wrong was wrong about what a
fixture contains rather than about the port.

**The headline: the laboratory's labor values are reproduced in C# to the
bit, on every fixture, from either starting iterate — 1,494 values across
eight cases with a maximum difference of zero ulps — and the 647-commodity
solve takes four milliseconds.**

## 1. What shipped

- `economy_mod/Source/Economy.Core/`: a library with no RimWorld or Unity
  reference, built for `net472` and `net8.0` from one source, holding
  `LaborValueSolver`, its input types, and `CompensatedSum` — CPython's
  `sum()` over floats, transliterated.
- `economy_mod/Source/Economy.Core.Check/`: a `net8.0` console harness
  that reads the fixtures, solves, and reports exact matches, the largest
  difference in ulps, the largest relative difference, and the time.
- `economy_lab/fixtures.py` and four fixtures under
  `economy_mod/Source/Fixtures/labor_values/`, each a real economy stopped
  at a day, with the solve's inputs in the laboratory's own order and the
  answers from a warm and a cold start.
- `tests/test_port_fixtures.py`: the committed fixtures are what the
  laboratory computes today, and warm and cold agree wherever the solve
  decides a value.

The mod's shipped assembly, its csproj, and its `verify.py` surface are
untouched. The library is built to `bin/`, which is ignored, and not to
`1.6/Assemblies`.

## 2. The harness's report

```
fixture                      case  goods iters  exact  max ulp      max rel         ms
capital_goods_day60          warm      9     1  27/27        0        0.0e0       4.07
capital_goods_day60          cold      9     9  27/27        0        0.0e0       0.24
equilibrium_day60            warm      6     1  18/18        0        0.0e0       0.03
equilibrium_day60            cold      6     4  18/18        0        0.0e0       0.04
scale_647_day3               warm    647     1 1431/1431        0        0.0e0       2.76
scale_647_day3               cold    647     5 1431/1431        0        0.0e0       4.23
technique_change_day120      warm      6     1  18/18        0        0.0e0       0.04
technique_change_day120      cold      6     4  18/18        0        0.0e0       0.05

every fixture reproduced to the bit
```

The `goods` column is commodities; `exact` counts social values plus every
region's individual values. The first row's four milliseconds is JIT
warm-up; the cold 647-commodity solve, nine iterations of Department I,
and everything else is under five.

## 3. Held: 5.1, 5.2, 5.3, 5.6

**5.1, 5.2, 5.3** Bit-exact on the six-commodity fixtures, on Department
I with its circular component sector, and on the 647-commodity economy,
social and individual values alike, warm and cold. Nothing in §6 of the
design had to be consulted.

This is the result the slice was built to get, and it is worth saying what
it rests on, because the next slices will rest on the same three things.
The port uses Neumaier summation where the laboratory calls `sum()` and a
running total where it uses `+=`; it walks contributors, inputs, outputs
and regions in exactly the orders `docs/53` §3 listed; and it writes each
expression with the laboratory's parenthesisation. The design predicted
that those three would be sufficient, and on 250 lines they were. The
determinism contract for the rest of the port is therefore known and
cheap: *transliterate, do not translate*.

**5.6** Four milliseconds for 647 commodities, against the design's twenty
and against the 22.3 seconds `docs/33` measured for a whole simulated day
in Python at that scale. The solve is one of the day's larger costs
there; if the rest of the step ports at the same ratio, the day lands
well inside the budget `docs/33` set for it.

## 4. Half-testable: 5.5

Both targets built from the same source with zero warnings. Whether the
`net472` assembly produces the same bits under the game's Mono as the
`net8.0` one does under .NET 8 cannot be tested without the game, and is
not claimed. What can be said is that the IL is the same IL, the
arithmetic is IEEE binary64 on SSE2 either way, and nothing in the solver
touches a runtime library whose behaviour differs between the two —
`Math.Abs`, `List.Sort` with an ordinal comparer, and dictionary lookups.

## 5. Wrong: 5.4, about the fixture, not the solve

Predicted: warm and cold starts converge to the same bits for every
fixture. Measured: they do for every value the solve *determines*, and
they do not for the values it does not. On the 647-commodity fixture, 255
of 647 commodities are **stale** on day 3 — their producers were sized at
`1e-6` capacity by the generator and ran below the solve's epsilon — and a
stale commodity keeps whatever value it started with, by `docs/19` §4's
rule that value describes conditions of production which do not evaporate
because nobody produced today. From a warm start that is the seeded value;
from a cold start it is zero. Both are what the laboratory does; the
prediction forgot that the laboratory does it.

Two things follow. The test now compares the solved values and asserts the
two starts agree on *which* values are stale. And the 647-commodity
fixture is really a 392-commodity solve wired through 784 producers; a
fixture where every sector runs would be a better volume test, and
`synthetic_economy` can make one with more headroom. Left as written,
because the point of the fixture is to be the economy `docs/33` measured,
not a friendlier one.

## 6. Carried forward

**The contract is transliteration.** Every later slice of the port should
be written against the Python line by line, with the same summation and
the same order, and checked to the bit before anything is optimised. A
port that is later made faster can be checked against this one.

**Next slices, in `docs/50` §6's order:** the basket and the wage; the
regional price update; the reserve-army premium and habituation. Each
needs its own fixture generator of the same shape — inputs in the
laboratory's order, outputs from the laboratory's own call — and the
generator here is the template.

**Loading it in the game is a separate step** with a human at the game,
and it changes `verify.py`'s expected surface. Not before the co-load
check `HANDOFF.md` already lists as stale.
