# Making the session's verification repeatable

Design and results in one. This closes a gap the session itself opened,
and it is the last thing in Phase C that does not need the game.

**The headline: most of what this session verified was verified in a
scratchpad, by drivers nobody else has. Four of the six ported
components, the codec, the scheduler, the wealth coupling and the
component's whole state machine were checked once and then became a
claim in a document. They are now committed harnesses:
`dotnet run --project economy_mod/Source/Economy.Core.Check` and
`… Economy.Drive`, 546 and 28 checks, both passing.**

## 1. The gap, and why it matters here more than most

This project's standard is unusually explicit: `tests/test_port_fixtures.py`
exists so that a model change without a fixture regeneration fails
loudly, and `docs/76` §1 kept a façade in the repository rather than a
scratchpad precisely because "a façade is only trustworthy if it is
maintained."

The same session then verified the price update, the wage-cost refresh,
`StateCodec`, `DayScheduler`, `WealthCoupling`, `SelfCheck`,
`TickBudget` and the component's five-scenario state machine — all with
throwaway drivers under `/tmp`. Every number in `docs/78`, `docs/81`,
`docs/83`, `docs/85`, `docs/89` and `docs/91` was real when it was
measured and **not one of them could be re-measured by anyone else.**

That is worse in this project than in most, because the whole method is
that a later run can contradict an earlier claim. A claim nothing can
contradict is not a result; it is a memory of one.

## 2. What is committed now

**`Economy.Core.Check` grew two files.**

- `PriceCheck.cs` — the price update (docs/77) and the wage-cost
  refresh (docs/79) against their fixture directories, with the same
  two comparisons as the other slices.
- `CoreSelfTest.cs` — the properties of the parts that have no
  fixtures: every double in every fixture through the codec, the
  scheduler invariant at every budget, the wealth coupling's inertness
  and bound over extreme inputs, and the report and budget rules.

`Program.cs` runs all five check groups and returns the first non-zero
code, then prints `ALL PORT CHECKS PASSED`.

```
every value-solve fixture reproduced to the bit
every wage fixture reproduced to the bit
every bargaining fixture reproduced to the bit, on every step
every price and wage-cost fixture reproduced to the bit
core self-test: 546 checks, 0 failures
ALL PORT CHECKS PASSED
```

**`Economy.Drive` is a project.** The five-scenario harness of
`docs/91` — fresh world, a day passing, save and reload, a mid-day
save resumed, a schema-2 save upgraded — now lives beside the others
and runs the same way. It compiles the mod's game-facing sources
directly rather than referencing `Economy.csproj`, because that one
needs RimWorld's assemblies and this must run without them.

```
dotnet run --project economy_mod/Source/Economy.Drive
checks 28, failures 0
THE COMPONENT'S STATE MACHINE IS CORRECT AGAINST A DOCUMENTED HOST
```

## 3. What this is worth

Three things that were true only in a document are now true in the
repository:

- **A regression will be caught.** If someone changes `PriceSolver` or
  the schema guard or the wealth clamp, the harness says so. Before
  this, the fixtures existed but nothing read three of the five slices'.
- **The numbers can be re-derived.** `docs/78`'s 48 readings and
  `docs/85`'s property checks are commands now, not sentences.
- **The next session inherits an instrument** rather than a claim to
  take on trust — which is the same reason `economy_lab/baseline.py`
  exists on the laboratory side.

It also removes an asymmetry that had crept in: the Python side of this
project has 288 committed tests and the C# side had one harness covering
three of eight things. Both sides now fail loudly.

## 4. What is still not verified, and it is two things

Unchanged, and neither is code:

1. **A build against RimWorld's real assemblies** — game files this
   environment does not have and should not.
2. **The game** — start it, save, reload, load an old save, paste the
   three reports.

Everything else in Phase C is built, verified, and the verification is
now repeatable by anyone with the two `dotnet run` commands above.

## 5. Cost

Two files in the check harness, one project file, a `sed` to renamespace
the drive harness, and two name clashes the compiler caught.
