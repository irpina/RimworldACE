# The shipping binary, built by the real toolchain and verified

Design and results in one: this is a verification of code already
written, and its content is that **two of the five items `docs/85` §6
left for a session at the game are now closed here.**

**The headline: the .NET SDK installs from Ubuntu's archive.
`Economy.Core` builds for `net472` — the framework RimWorld's Mono loads
— with zero warnings and zero errors, the committed check harness runs
for the first time and passes, and the `net472` artifact itself
reproduces the laboratory to the bit under Mono. The library that will
ship is now verified as a built artifact rather than as source.**

## 1. The environment, a third time

`docs/72` §7 said there was no .NET SDK and no way to get one.
`docs/76` §1 found Mono in Ubuntu's archive and noted the lesson: *"the
official toolchain is unreachable" is not the same claim as "no
toolchain is reachable", and only the first was checked.*

The same mistake was still in place. Ubuntu ships `dotnet-sdk-8.0`, and
the first attempt failed with a 404 on a stale package index — which
looks exactly like "not available" and is not:

```
apt-get update && apt-get install -y dotnet-sdk-8.0      # 8.0.131
```

Three rounds of this now. The generalised form is worth writing down
once: **a failure to obtain something is evidence about the attempt, not
about the thing.** A 403 from one host, a 404 from a stale index, and an
absent binary all read as "impossible" and none of them is.

## 2. `net472` builds

```
dotnet build economy_mod/Source/Economy.Core/Economy.Core.csproj -f net472
Build succeeded.  0 Warning(s)  0 Error(s)
```

This is the real project file with its real `TargetFrameworks`, its
`LangVersion 7.3`, its `Deterministic` flag and the
`Microsoft.NETFramework.ReferenceAssemblies` reference — not a hand
invocation of `mcs` against whatever profile Mono defaults to, which is
what every earlier compile in `docs/76` onward actually was. The
distinction matters: `mcs` compiling successfully says the source is
valid C#; the SDK building `net472` says *the thing that ships* is
valid.

## 3. The check harness runs, for the first time

`docs/73` §5, `docs/75` §4, `docs/76` §5 and `docs/85` §6 all listed
this as the one command nobody had run:

```
dotnet run --project economy_mod/Source/Economy.Core.Check

every value-solve fixture reproduced to the bit
every wage fixture reproduced to the bit
every bargaining fixture reproduced to the bit, on every step
```

Every fixture, every case, zero ulps and `0.0e0` relative error on .NET
8 — including `scale_647_day3`'s 1,431 values warm and cold, at 10 and
21 ms. The harness's own code — `Program.cs`, `WageCheck.cs`,
`BargainingCheck.cs`, the `private`→`internal` widening, the
`System.Text.Json` reading — is now exercised rather than merely
compiled-in-principle.

## 4. The shipping artifact reproduces the laboratory

The `net472` DLL the build produced, loaded under **Mono**, against the
committed fixtures:

| check | result |
|---|---|
| value solve, wage, bargaining | 4,060 readings, **0 ulps** |
| the price update | 48 readings, **0 mismatches** |
| the wage-cost refresh | 43 readings, **0 mismatches** |
| `StateCodec` round-trip | 2,078 values, **0 failures** |
| `DayScheduler` invariant | 8 budgets, 5 save points, **0 mismatches** |
| `WealthCoupling` properties | 2,526 checks, **0 failures** |

Every earlier run compiled the source fresh with `mcs`. This runs the
**binary the mod will carry**, on the **runtime the game uses**. That is
as close to the game as anything can get without the game.

## 5. What is left, and it is now three things

`docs/85` §6 listed five. Items 1 and 2 are closed. What remains needs
RimWorld's own assemblies or RimWorld itself:

1. ~~Build `net472`; run the check harness.~~ **Done.**
2. **Build the mod assembly** (`Economy.csproj`) against RimWorld's
   shipped managed DLLs. Those are game files; this environment does not
   have them and should not. The mod's own code compiles against a
   hand-written façade (`docs/85` §5), which catches syntax, types and
   call shapes but not a wrong signature.
3. **The co-load, tab, save/reload and old-save checks** under "Stage 1
   runtime shell" in `HANDOFF.md`. A save file reloading and a tab
   rendering are observations.
4. **Profile the tick.** `PhasesPerTick` is 1 and is a guess
   (`docs/83` §5). It wants a frame graph.

Item 2 is a licensing and file-availability boundary rather than a
capability one, and it is the last thing between here and a build that
could be dropped into the game's `Mods` folder.

## 6. Cost

Two `apt-get` commands, one of which needed `apt-get update` first; one
`dotnet build`; one `dotnet run`; and six drivers re-pointed at the
shipping DLL. About five minutes, against four documents that had
written the whole class of verification off as out of reach.
