# Stage 1: the wealth coupling: results

`docs/84` is the design. `WealthCoupling` is built, compiled and
property-tested. Every prediction held.

```
checks 2526, failures 0
THE DEFAULT IS INERT AND THE BOUND HOLDS
```

## 1. Held: 4.1, the default is provably inert

`Factor(Observe, …)` returns **exactly 1.0** across every combination of
14 model prices × 10 authored values × 6 bands — including NaN,
±infinity, negative prices, a zero authored value, and 1e300. And
`ProjectedWealthRatio(Observe, …)` is exactly 1.0 over a portfolio whose
prices have gone to a tenth and to a thousand times authored.

That is the claim the tab makes to the player — "Vanilla prices are
unchanged" — and it is now a checked property rather than a property
that holds because nothing is wired yet. It was worth asserting with
`==` rather than a tolerance: a default that is inert to within a
rounding error is not inert, because wealth is a sum over thousands of
items and a rounding error per item is a raid.

## 2. Held: 4.2, the bound cannot be escaped

`Factor(Bounded, …)` lands inside `[1/(1+b), 1+b]` for every one of the
same combinations, and is always finite. The edge cases are where a
clamp usually fails and they are the ones that were tested:

- a **NaN or infinite** model price falls back to vanilla's own number
  rather than propagating;
- a **zero or negative authored value** has no ratio to speak of and
  also falls back, instead of dividing;
- a **NaN or negative band** is treated as a band of zero, so a
  nonsensical configuration pins the factor at exactly 1.0 rather than
  opening it wide.

At the portfolio level the same holds, and junk stocks — a NaN quantity,
a negative quantity, a good vanilla has never heard of — leave the ratio
at exactly 1.0. A negative stock is excluded deliberately: it is not
something a colony can hold, and allowing it would let one line cancel
another and hide an excursion.

## 3. Held: 4.3, the danger is visible

`Unbounded` over a portfolio whose every price has tripled gives a ratio
of **3.0** to within 1e-12, while `Observe` over the identical input
gives exactly 1.0.

That pair is the whole argument for the design in one line. The same
colony, the same glut, the same stockpile: under the shipped default the
storyteller sees nothing, and under a naive coupling it sees a colony
three times richer and sends raids to match. `Unbounded` exists to
produce that number and is never shipped.

## 4. What this does not settle

Whether a `Bounded` coupling with some band *feels* right is a question
about play, and it needs play. What has changed is that the person
answering it now has an exposure number instead of an intuition, and
that the default is safe while they take their time.

It also does not touch `MarketValue` — nothing here writes it, and the
mod still has no Harmony patch and no gameplay mutation. The coupling is
a calculation about what *would* happen, not a mechanism that makes it
happen.

## 5. Phase C: what is built, and what is not

| component | state | evidence |
|---|---|---|
| the value solve | ported | 2,988 readings, .NET 8 and Mono |
| the basket and the wage | ported | 112 readings, Mono |
| the reserve army and habituation | ported | 960 readings, Mono |
| the regional price update | ported | 48 readings, Mono, `exp` included |
| the wage-cost refresh | ported | 43 readings, Mono |
| persistence (`StateCodec`) | built | 2,078 values exact |
| the day scheduler (`DayScheduler`) | built | invariant holds at 8 budgets, 5 save points |
| the wealth coupling (`WealthCoupling`) | built | 2,526 property checks |
| wiring into `EconomyWorldComponent` | **written** | compiles against a stub façade only |
| the tab's new rows | **written** | compiles against a stub façade only |

The last two are the honest boundary of this environment. They are real
code — the schema bumped to 3, the economy persisted as one encoded
string, `WorldComponentTick` replaced by a budgeted scheduler advance, a
mid-day save resuming at its cursor, two new rows on the tab — and they
have been compiled, against a hand-written façade of the RimWorld API
rather than against RimWorld. That catches syntax, types and call
shapes. It does not catch a wrong signature, and it cannot run.

## 6. What a session at the game has to do

In order, and none of it is open-ended:

1. **Build for real.** `net472` against RimWorld's assemblies, plus
   `dotnet run --project economy_mod/Source/Economy.Core.Check`, which
   has still never run (`docs/76` §5).
2. **The co-load and tab check** already listed in `HANDOFF.md` under
   "Stage 1 runtime shell", stale since Labor Content gained an
   assembly.
3. **Save, reload, and read the determinism row.** It should say
   `reproduced N/N`. A mid-day save should resume mid-day: the new "Day
   in progress" row says which phase.
4. **An old save.** A schema-2 save must load with no economy state and
   no error.
5. **Profile the tick.** `PhasesPerTick` is set to 1 and is a guess
   (`docs/83` §5); the number wants a frame graph, not an argument.

## 7. Cost

One C# file, a property harness over 2,526 combinations, a stub façade
of the RimWorld API so the game-facing code could be compiled at all,
and this document.
