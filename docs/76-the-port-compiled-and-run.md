# The port, compiled and run: all three slices to the bit under Mono

Design and results in one, like `docs/62`, because what it describes is a
**verification** of code already written rather than a new mechanism.
`docs/73` §5 and `docs/75` §4 both recorded the same gap — the C# was
written to the contract and had never been compiled — and both named the
one command that would close it. This document closes it a different
way, and gets a better answer than the one that was asked for.

**The headline: `Economy.Core` compiles clean and runs, and all three
ported slices reproduce the laboratory to the bit — 4,060 readings, zero
ulps — under *Mono*, which is the runtime RimWorld actually loads. The
gap `docs/73` and `docs/75` left is closed for the library that ships.
What is still unbuilt is the build-machine harness, and the reason is
one missing assembly rather than anything about the port.**

## 1. What the environment turned out to have

`docs/72` §7 recorded that this environment has no .NET SDK and that the
network policy blocks Microsoft's distribution host — `builds.dotnet.
microsoft.com` answers 403 at the proxy. Both are true, and both were
taken as the end of the question. They are not.

Ubuntu's archive is reachable, and it carries **Mono**:

```
apt-get install -y mono-mcs        # mcs 6.8.0.105, mono runtime
```

That is not the game's build toolchain — RimWorld mods are built for
`net472` with the reference assemblies, and `Economy.Core.csproj` targets
`net472` and `net8.0`. It is something better for this particular
question: Mono is the runtime **the game itself executes managed code
on**. A bit-exactness result under Mono is closer to what the port has to
be true of than the same result under .NET 8, which is where `docs/54`
measured the value solve.

The lesson, and it generalises past this project: *"the official
toolchain is unreachable" is not the same claim as "no toolchain is
reachable", and only the first was checked.*

## 2. The library compiles

```
mcs -target:library -out:Economy.Core.dll Economy.Core/*.cs
```

Zero errors, zero warnings, first attempt, across all six files —
`CompensatedSum`, `LaborValueProblem`, `LaborValueSolver`,
`WageProblem`, `WageSolver`, `BargainingSolver`. Nothing about the two
unbuilt slices needed fixing to compile, which is a mildly interesting
result on its own: the transliteration discipline produces code that is
syntactically conservative, because it is copying a structure rather than
inventing one.

## 3. It reproduces the laboratory, to the bit

A scratchpad driver — the committed harness cannot run here, §5 — reads
the **committed fixtures**, runs the real solvers, and compares every
reading by units in the last place:

```
runtime: Mono 4.0.30319.42000
value-solve readings 2988
wage readings         112
bargaining readings   960
compared 4060, exact 4060, max ulp 0
BIT EXACT under a real C# runtime
```

| slice | docs | readings | previously |
|---|---|---:|---|
| the value solve | 53, 54 | 2,988 | measured under .NET 8 |
| the basket and the wage | 72, 73 | 112 | shadow-checked in Python only |
| the reserve army and habituation | 74, 75 | 960 | shadow-checked in Python only |

**The two shadow checks were right.** `docs/73` §4 and `docs/75` §1
reported zero ulps from a Python re-implementation written off the C#
source, and said plainly that this checked order, branch and
accumulation and nothing about whether the code built or how a real
runtime would evaluate it. Both predictions now hold under a compiler and
a runtime. The shadow was a good instrument and it is retired: there is
no reason to run it again now that the real thing runs.

**The value solve gains a runtime it did not have.** `docs/54` measured
it on .NET 8 on the build machine. It is now also exact on Mono, which is
what the game will run it on — the single most load-bearing assumption
of Phase C, and it was untested until now.

## 4. What this says about the two rules the slices produced

Both fixture rules earned their keep and are confirmed rather than
merely plausible:

- `docs/73` §2 — a fixture carries the state a magnitude is computed
  against. The settlement readings include the purse deltas that differ
  from the ledger postings in the last bits, and the port reproduces
  *those*, which a difference-shaped fixture would never have tested.
- `docs/75` §3 — a fixture is checked for the branches it takes. The
  960 bargaining readings include 59 step-pairs where habituation's
  taken branch fires, which the original three fixtures never reached.

## 5. What is still not built, precisely

**The check harness.** `Economy.Core.Check` — `Program.cs`,
`WageCheck.cs`, `BargainingCheck.cs` — does not compile here, and every
error is the same one:

```
9 × CS0246: The type or namespace name `JsonElement' could not be found
3 × CS0234: The type or namespace name `Json' does not exist in the namespace `System.Text'
```

`System.Text.Json` is absent from Mono 6.8's class library and present in
the `net8.0` the harness targets. **There is no other error** — no
syntax, and in particular no `CS0122`, which is what a mistake in
widening `Program.Comparison` and `Program.Compare` from `private` to
`internal` would have produced. So the harness is sound apart from an
assembly this environment does not have, and it remains unrun.

**What that leaves for a machine with the SDK** is smaller than it was
and still real:

1. `dotnet run --project economy_mod/Source/Economy.Core.Check` — confirm
   the harness itself works and that the same fixtures pass on .NET 8.
2. `net472` specifically. Mono 6.8's default profile is close to it and
   is not it; the `csproj` targets `net472` for the game and that build
   has not been done since the two new files landed.
3. Loading `Economy.Core` **in the game**, which changes `verify.py`'s
   expected surface and needs a human at the game — unchanged from
   `docs/54` §6 and still the boundary of everything here.

## 6. Where Phase C stands

| slice | written | compiles | bit-exact |
|---|---|---|---|
| the value solve | yes | yes | **.NET 8 and Mono** |
| the basket and the wage | yes | **yes** | **Mono** |
| the reserve army and habituation | yes | **yes** | **Mono** |

`docs/74` §7's "no third unbuilt slice" rule is **discharged**: there are
now no unbuilt slices. The next arithmetic slice can start without
stacking risk, and the candidates are unchanged — the regional price
update, and `_update_wage_costs` with the process graph behind it.

The engineering half of Phase C is untouched and is now the larger half:
the daily tick amortised across ticks, the full economic state through
save and load, the UI, and the `MarketValue` wealth coupling that
`HANDOFF.md` lists as the project's second-largest remaining risk. None
of those can be finished without the game running, and that is a human's
step and not this environment's.

## 7. Cost

One `apt-get install`, one compile, a scratchpad driver with a hundred
lines of hand-rolled JSON because Mono has none, and three runs. About
ten minutes, against two documents that had written the gap off as
unclosable here.
