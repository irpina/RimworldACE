# Stage 1: the value solve in C#: design

Written before implementation. `HANDOFF.md` describes Phase C as "the
bulk of the work": port the model to deterministic C#, six to ten sessions.
This is the first of them, and it is deliberately the smallest slice that
can fail in the way the whole port could fail.

## 1. Why the value solve, and why first

`docs/50` §6 orders what the game must carry by what reads what, and the
value solve is at the bottom: a hired worker's labor-power has a value
only if the region can solve one. It is also the piece the laboratory has
validated hardest — exact against the closed analysis for 447 commodities
(`docs/33`), and against the four hand-derived values before that
(`docs/20`) — so a port of it has the strongest reference any piece of
the model will ever have.

And it is the piece where the port's real risk lives. The laboratory's
histories are reproducible to the bit, and the whole design-then-measure
method rests on that. A port that reproduced them to `1e-9` would pass
every test in `tests/` and still not be the same model: the exact
stationarity requirement that `docs/44` calls "the most productive
constraint in the project" is a bit-level claim, and it was two bit-level
defects that the requirement caught. So the question this slice asks is
not "can C# compute labor values" but **"can C# compute the laboratory's
labor values, to the bit, from the laboratory's own inputs"**. If the
answer is no, the port needs a different determinism contract before
anything else is moved, and it is better to learn that on 250 lines than
on 3,500.

## 2. What is built

```
economy_mod/Source/Economy.Core/            a library with no RimWorld reference
    Economy.Core.csproj                     net472 for the game, net8.0 for the harness
    CompensatedSum.cs                       CPython's float sum, exactly
    LaborValueProblem.cs                    the solve's inputs, in the laboratory's order
    LaborValueSolver.cs                     the solve
economy_mod/Source/Economy.Core.Check/      a console harness, net8.0
    Program.cs                              reads fixtures, solves, compares
economy_mod/Source/Fixtures/labor_values/   what the laboratory says the answer is
economy_lab/fixtures.py                     writes those, from real economies
```

**The library has no game in it.** It references nothing from RimWorld and
nothing from Unity, and the `Economy` mod does not reference it yet. It is
compiled for `net472` because that is what the game's Mono runtime loads,
and for `net8.0` so the harness can run it on the build machine without
the game. When it is wired into the mod it will be a second assembly in
`1.6/Assemblies`, and `verify.py` will check it the way it checks the
first. Not this session: nothing goes into the game's folder that has not
been seen loading in the game.

**The fixtures are real economies.** `economy_lab/fixtures.py` builds the
six-commodity equilibrium at day 60, Department I's nine-commodity circuit
at day 60, the technique-change economy at day 120 (two provisioners in
one region, so individual values differ from social ones), and the
647-commodity synthetic economy at day 3. From each it writes the solve's
*inputs* exactly as `_update_labor_values` sees them — every active
producer with its realized runs, its process's outputs and inputs in the
order the model holds them, its capital bill, and every commodity's mass —
and the solve's *outputs* from two starting points: warm, from the values
the economy had converged to, and cold, from all zeros. The Python side
sets `labor_values` to the starting point and calls the solve, so the
expected answer is what the laboratory itself computes from that iterate,
not a copy of a number it had already.

**The harness compares two ways.** Within tolerance, `1e-9` relative, which
is what a port that was merely correct would pass. And to the bit, which
is what this port claims. Both are reported per fixture and per case, with
the largest difference in units in the last place, so that a failure says
how far off it is and not only that it is.

## 3. The determinism contract

Bit-exactness between CPython and C# is not automatic, and the two places
it can break are known in advance.

**Summation.** Since 3.12, CPython's `sum()` over floats uses Neumaier's
compensated summation, and `docs/33` already found the laboratory
depending on it: a `+=` loop and a `sum()` over the same terms differ in
the last bit. The solve uses `sum()` in three places — the inputs' carried
labor per run, a joint process's mass total, and a capital bill at values
— and `+=` in two: accumulating each commodity's labor and its output.
The port replicates each exactly: `CompensatedSum` is a transliteration of
`builtin_sum_impl`'s float path, including the final `if (c) f += c`, and
is used where and only where the laboratory uses `sum()`.

**Order.** Floating-point addition is not associative, so the order of
every accumulation is part of the answer. The laboratory's orders are:
regions in insertion order and producers in list order for contributors;
input names *sorted* for the carried labor; output names *sorted* in the
social pass and in *insertion* order for the output totals; a joint
process's outputs in insertion order for the mass total; and region
names sorted for the individual values. The fixture writes lists, not
maps, wherever insertion order matters, and the solver sorts with ordinal
string comparison, which is what Python's `str` ordering is for the ASCII
names the model uses.

**Arithmetic.** Both runtimes use IEEE 754 binary64 with round-to-nearest.
The .NET JIT does not contract `a * b + c` into a fused multiply-add
unless asked, and the expressions are written with the laboratory's
parenthesisation: `(runs * per_run_total) * share`, `(labor * share) /
life`. Mono on x64 uses SSE2, as does .NET 8, so the harness's answer is
the game's answer; the one platform where that would not hold, 32-bit
x87, is not one RimWorld 1.6 ships on.

## 4. What it deliberately does not do

- **It does not touch `economy_mod`'s shipped assembly.** The mod's csproj,
  its `verify.py` surface of 30 symbols, and its DLL are unchanged.
- **It does not port anything but the solve.** No prices, no ledger, no
  step. The order for the rest is in `docs/50` §6 and does not change.
- **It does not amortise across ticks or design the runtime's history.**
  `docs/33` named both as constraints on the port; they are constraints on
  the *step*, and the step is not in this slice.
- **It does not take a dependency.** The harness reads JSON with
  `System.Text.Json`, which ships in `net8.0`; the library needs no JSON.
- **It does not run in the game.** See §2.

## 5. Predictions

5.1 **The six-commodity fixtures are bit-exact**, warm and cold, in both
regions' individual values as well as the social ones. The graph is
acyclic in inputs and every process has one output, so the only places
order and summation matter are the ones §3 lists.

5.2 **Department I is bit-exact**, including the circular component
sector, because the capital bill at values is a `sum()` over sorted names
that `CompensatedSum` reproduces. If this fails and 5.1 holds, the bill is
the place to look.

5.3 **The 647-commodity fixture is bit-exact for the social values and
for the individual values.** The synthetic wiring has up to four inputs
per process and every process has one output, so nothing new is
exercised; it is the volume that is being tested.

5.4 **Cold and warm starts converge to the same bits** in Python, and
therefore in C#, for every fixture. The solve stops when successive
iterates agree within `1e-12`; from any start the last iterate is the
fixed point to that tolerance, and the fixed point is unique for a
productive matrix. If they differ, the tolerance stop is landing on
different iterates from different sides, and the fixture records which.

5.5 **The `net472` and `net8.0` builds of the library produce identical
bits.** Same IL, same arithmetic; the harness runs `net8.0` and the game
will run the other, and the prediction is that this does not matter.
Only the first half is testable this session.

5.6 **The solve at 647 commodities takes under 20 ms in C#** against the
Python figure `docs/33` measured for the whole day. This is the port's
whole promise in one number and the least important prediction here,
because a solve that is fast and wrong is worse than one that is slow and
right.

## 6. What would make this wrong

A single ulp anywhere. §3 says where to look: if only the Department I
fixture differs, the bill; if the individual values differ and the social
ones do not, the region ordering or the left-to-right `a + b + c`; if
everything differs by one ulp in the same direction, the compensated sum's
final `if (c)`. If the 647 fixture alone differs, an input name is
colliding on ordinal versus code-point order, which would mean the model's
names are not ASCII after all.
