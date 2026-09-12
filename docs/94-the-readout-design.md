# A UI that makes value, price, surplus and rent legible: design

Written before implementation. `HANDOFF.md`'s Phase C names five things
and this is the one that had not been started: *"a UI that makes value,
price, surplus and rent legible"*. The tab built so far shows the mod's
**status** — days simulated, schema, self-check — which is diagnostics,
not economics.

## 1. What legible means here, and why it is a design question

The model's quantities are not in units a player can read.

- **Value** is in work-ticks. A yayo value of 735.975 means nothing at a
  glance; 735.975 ticks is **0.031 worker-days**, and that is a sentence.
- **Price** is in silver and is readable, but alone it says nothing this
  project is about.
- **Surplus** lives in the ledger as three labour-time sums — living,
  necessary, surplus. The reading that matters is the **rate of surplus
  value**, `s/v`, which `docs/20` made an *outcome* rather than a
  coefficient and is arguably the project's single headline number.
- **Rent** is accumulated per commodity as the cost advantage of
  infra-marginal extractors. A total means little; rent **as a share of
  the sector's value** is comparable across sectors and across saves.

So the readout is not a dump of state. Four deliberate choices:

| shown | instead of | because |
|---|---|---|
| worker-days | work-ticks | a day is a unit a player has |
| price ÷ value | price, value | the deviation **is** the subject (docs/24) |
| `s/v` as a rate | three labour sums | an outcome, not an input (docs/20) |
| rent as a share of sector value | a silver total | comparable between sectors |

**The price-to-value ratio is the one to get right.** It is the number
that makes the model's claim visible: that prices deviate from labour
values systematically rather than randomly. A player who watches it move
in a glut has understood the point of the mod.

## 2. What is built

```
economy_mod/Source/Economy.Core/EconomyReadout.cs
```

- `ReadoutRow` — a commodity's name, value in worker-days, price,
  price/value, and rent share;
- `RegionReadout` — the rows, plus the wage, the rate of surplus value,
  and the employment;
- `EconomyReadout.Build(...)` — from the snapshot and the ledger totals;
- `Format` helpers so the tab prints the same strings the harness
  checks.

No RimWorld reference: the *content* is testable here even though the
rendering is not. The snapshot grows the three labour sums and the rent
totals, which it must carry anyway for a reload to resume an economy
rather than a price table.

## 3. Predictions

3.1 A row's value in worker-days is the labour value divided by the
region's ticks per worker-day, to the bit.

3.2 `price ÷ value` is computed in **silver per worker-day** on both
sides, so it is a pure number, and is exactly 1.0 when a commodity's
price equals its value at the region's own wage. A ratio that depended
on the tick length would be an artifact.

3.3 The rate of surplus value is `surplus ÷ necessary`, and where the
ledger has necessary labour of zero — a region with no basket — the
readout says so rather than dividing.

3.4 Every degenerate input is survivable: a zero or missing value, a
zero price, a commodity in the price table and not the value table,
NaN. No row throws, and no row renders `NaN` or `∞` to a player.

3.5 The laboratory is unmoved: 322 metrics at zero delta.

## 4. What would make this wrong

If 3.2's ratio is not 1.0 at equality, the two sides are not in the
same units and the headline number is meaningless — which would be
worse than not showing it, because it would look authoritative.

If a degenerate input reaches the tab as `NaN`, the readout has failed
at its only job: a player reading nonsense with confidence is the
failure mode a diagnostics panel exists to prevent.

## 5. What this cannot do

It cannot show that the tab *looks* right, or that the columns fit, or
that the numbers update as a game runs. Those need the game. It can
show that what the tab would print is arithmetically right and
survivable, which is the half that is the mod's fault if it is wrong.

## 6. Cost

One C# file, the snapshot extended, the tab's rendering, and a harness
over the degenerate cases.
