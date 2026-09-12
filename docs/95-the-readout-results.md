# A UI that makes value, price, surplus and rent legible: results

`docs/94` is the design. `EconomyReadout` is built, and every prediction
held. This was the one component of `HANDOFF.md`'s Phase C list that had
not been started.

```
core self-test: 579 checks, 0 failures
ALL PORT CHECKS PASSED
```

## 1. Held: 3.1 and 3.2, the headline number

A row's value in worker-days is the labour value over the region's
working day, exactly. And **price ÷ value is exactly `1.0`** for a
commodity priced at its value at the region's own wage — not
approximately, asserted with `==`.

The prediction that mattered was that the ratio must not depend on how
long a tick is. Doubling both the labour values and `ticks_per_worker_day`
leaves it at exactly `1.0`, because both sides are put in silver per
worker-day before dividing. A ratio that moved with the tick length
would have been an artifact wearing the clothes of a measurement, and
`docs/94` §4 said that would be worse than not showing it.

A commodity at twice its value reads `2.0x`. That is the number that
makes this project's subject visible — `docs/24`'s wedge between
authored prices and labour values, in a line a player can read.

## 2. Held: 3.3, the rate of surplus value

`s/v` is surplus over necessary labour — 1.5 from the test's 412.5 and
275.0 — and a region whose necessary labour is zero reports `n/a`
rather than dividing. The headline line reads:

```
wage 41.97 silver/day, s/v 1.5x, employment 0.318 worker-days
```

Three sentences' worth of `docs/20`'s central result in one row.

## 3. Held: 3.4, nothing reaches a player as nonsense

The readout was built from a deliberately hostile table: a commodity
with zero value, one with zero price, one present in prices and absent
from values, a `NaN` value, an infinite price, `NaN` rent and zero
output.

Every row renders without `NaN`, without `Inf`, and without `∞`.
Uncomputable readings render `n/a` — which is a different thing from
`0`, and saying "I cannot tell you" is the honest rendering of a
quantity that does not exist. A commodity with no labour value reports
no ratio rather than a ratio of zero.

This matters more than it looks. A panel like this fails not by
crashing but by printing nonsense with the authority of a measurement,
and a player has no way to tell the difference.

## 4. What the tab does now

Where an economy exists, a region's headline and a row per commodity:
worker-days, silver, price/value, rent share. Where one does not — which
is today, because the model is ported and not yet wired to the world —
it says so:

```
Value, price, surplus, rent:
  not yet: the model is ported and checked, and not yet wired to the world
```

An empty table looks like a broken one. Saying which it is costs a line.

## 5. What this does not show

That the tab *looks* right, that the columns fit, or that the numbers
move as a game runs. Those need the game, and `docs/94` §5 said so in
advance. What is established is that what the tab would print is
arithmetically right and survivable — the half that is the mod's fault
if it is wrong.

The rows are also empty until the model is wired to the world, which is
the last piece of Phase C's port and needs the game to check.

## 6. Phase C, against `HANDOFF.md`'s own list

> *Port the model to deterministic C#; settlement profiles and regional
> membership; the full economic state through save and load; a UI that
> makes value, price, surplus and rent legible; integration with vanilla
> trade without destabilising `MarketValue`.*

| clause | state |
|---|---|
| port the model | five slices, 4,151 readings, zero ulps |
| settlement profiles and regional membership | in the shell since `585bf09` |
| full economic state through save and load | `StateCodec`, wired, 2,078 values exact |
| a UI that makes value, price, surplus and rent legible | **this document** — built and checked, empty until the model is wired |
| `MarketValue` without destabilising it | `WealthCoupling`, default provably inert |

Every clause is now built and machine-checked. Two things are not done
and both need the game: a build against RimWorld's real assemblies, and
running it.

## 7. Cost

One C# file, thirty-three checks in the committed harness, the tab's
rendering, and one name clash the compiler caught.
