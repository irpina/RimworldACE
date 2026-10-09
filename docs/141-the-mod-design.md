# The mod: carrying the docked economy into the game: design

Written before any of it is built. The laboratory is docked with Wright
(`docs/139`, `docs/140`), and the user's direction is that the mod is
built from a model that is known to work rather than the other way
round. This document says which model that is, how the rest of it gets
into C#, in what order, and what would show the plan is wrong.

## 1. Where the runtime stands

The port is further along than the runtime's README suggests and less
far than its five green slices suggest.

| piece | state |
|---|---|
| `Economy.Core`: value solve, wage and basket, reserve army and habituation, regional price update, wage-cost refresh | ported, bit-exact against the laboratory's fixtures, 579 checks |
| `StateCodec`, `DayScheduler`, `TickBudget`, `WealthCoupling`, `SelfCheck` | built, property-checked |
| `EconomyWorldComponent`, the read-only tab, settlement profiles and regions | built; the day runs one placeholder phase |
| **the economy's state** (`Economy`, `Region`, `Producer`, `Process`, `Route`, `Ledger`, about 190 fields) | **not ported**: the solvers take problem objects assembled by fixtures, not a living economy |
| **the generator** (`scale.synthetic_economy`, which builds an economy from the real def population) | **not ported** |
| **the rest of the day**: throughput and the fund's spending, production, cost ratios, final consumption, arbitrage, purses and accumulation, expectations | **not ported** |

So the five ported solvers are islands. Nothing in C# yet holds an
economy that a day could be run on.

## 2. Decision: the game runs the docked configuration, and only that

The laboratory has many switches and most combinations were never
measured against anything outside itself. One was: the configuration of
`docs/138`, which passed all nine of its predictions against Wright's
battery. That is the configuration the mod carries.

| switch | docked | consequence for the port |
|---|---|---|
| `producer_cash`, `posted_prices` | on | purses, posted prices and the cost-weighted order book are ported |
| `fund_spending_rate` (rule one), `accumulate` (rule two) | on | both Wright rules are ported |
| `procurement`, `entry_on_margin`, `exit_on_return`, `capacity_exit`, `sales_follow_production` | off | not ported |
| wage bargaining, worker mobility, habituation | off | already ported as solvers; not wired |
| investment | off (interval 10^6 days) | not ported |
| reserves, capital bills, projects | none in the population | not ported |
| rationing | proportional | only this branch is ported |

The C# **refuses** any configuration outside this set: constructing an
economy with a switch it does not carry throws, naming the switch. A
port that silently ran a different model from the one that was docked
would defeat the reason for docking first.

This is a narrowing, and it is deliberate. `docs/50`'s gameplay layer
needs bargaining, habituation and mobility; they are already ported and
will be wired when the gameplay layer is designed against a running
economy, not before.

## 3. The world the model runs on

- **Commodities** are the laboratory's population: the closed 653-def
  solve, `economy_lab/data/embodied_labor.csv`, shipped as mod data. The
  game's own defs are not re-read at runtime; that is what keeps the
  game's economy the laboratory's economy.
- **Regions** are the factions `ProfileBuilder` already derives, in
  first-appearance order. A default world has roughly six to ten.
- **Routes** are the generator's ring, which already handles any region
  count.
- **The seed** is the world's `persistentRandomValue` through the same
  SplitMix64 mixer the profiles use. Nothing draws from `Verse.Rand`.
- **The colony is not a producer** (`docs/50` §4), and nothing is
  written to `MarketValue` (the wealth-coupling constraint).

This changes two things the docking held fixed: the region count (2 in
the battery) and the horizon (36 months; a long game runs well past
that, at 60 days to a RimWorld year). The commodity count may change
too, from the battery's 200 to the full population. **None of the three
has been measured**, and finding out in Python costs an afternoon while
finding out in the game costs the port. So the first slice is a
measurement, not code.

## 4. How the rest is ported

The contract stays what `docs/53` made it: **transliterate, do not
translate**, and check to the bit. What changes is the unit of checking.

**A full-state codec.** The laboratory writes an economy's complete
state, every field of every object in the order the model holds it, as
JSON with floats in round-trip form. The C# state model reads it and
writes it back; the two files must be byte-identical. That makes every
later check a comparison of whole states, so a phase cannot agree on
what it was asked about while disturbing something it was not.

**Phase fixtures.** For a phase, the laboratory writes the state before
it and the state after it, from real docked economies on several days
(day 1, a day inside burn-in, and a day inside the over-accumulation
crisis `docs/133` §3 found). The C# runs the phase on the first and
must produce the second exactly.

**Slices, in step order**, each a commit with its fixtures green:

| slice | content |
|---|---|
| 0 | measure the docked configuration at the game's shape (§3) |
| 1 | the full-state codec and the C# state model; round-trip |
| 2 | the generator: the C# builds the docked economy from the CSV, a seed and a region count, matching the laboratory's state after `build_ours` |
| 3 | arrivals, throughput and the fund's spending |
| 4 | production, with the wage, rationing, posted prices and the order book |
| 5 | the value solve and the cost ratios, rewired onto the state model |
| 6 | final consumption and the workers' basket |
| 7 | prices, arbitrage, purses with accumulation and wear, expectations |
| 8 | the whole day, many days, against the laboratory's history |
| 9 | wire the day into `EconomyWorldComponent` and show it in the tab |

Slices 1 to 8 need no game. Slice 9 compiles against `Economy.Facade`
here and needs RimWorld's own assemblies, and a human at the game, to
be called done.

## 5. Predictions

All two-sided. Slice 0's are scored in `docs/142`; the port's as each
slice lands.

**Slice 0, the game's shape** (docked configuration; regions 2, 6 and
10 at 200 commodities; 647 commodities at 6 regions; 1,800 days):

1. **Money is conserved** at every shape: `|balance| < 1e-9` of the
   money stock.
2. **Region count is neutral**: per region, the share of producers still
   employing at day 1,080 and the value added per day in the last year
   are within ±20% of the two-region figure at six and at ten regions.
   This fails if the extra arbitrage routes or the fund rate seeded from
   one region matter.
3. **Commodity count is neutral**: the same two figures at 647
   commodities are within ±20% of 200.
4. **The economy survives a long game**: at day 1,800, at least half the
   producers that employed at day 180 still employ, and the value added
   in the last year is at least half that of the first year after
   burn-in. It fails if the over-accumulation crisis compounds rather
   than settles.
5. **Prices stay inside their bounds**: under 5% of commodity-region
   prices sit at their floor or ceiling on day 1,800.
6. **Cost is linear in producers**: Python seconds per day per thousand
   producers are within ±30% across all shapes.

**The port:**

7. **The docked day is under 60% of the step's code, and over 35%.**
   Measured by tracing which lines of the step's methods a docked day
   executes, against the methods' total.
8. **The state round-trips on the first compile** with no field
   mismatched; if one does, it is an ordering, not an arithmetic, error.
9. **Every ported phase is bit-exact**, and where one is not, the cause
   is a `sum()` ported as `+=` or a dict iterated in the wrong order, the
   two failure families `docs/53` §3 named. A third family would be
   news.
10. **A docked day at the battery's size costs under 20 ms in C#**, the
    `docs/33` projection of a 20× speed-up over Python's 100 ms.

## 6. What would make this wrong

If slice 0 fails predictions 2 to 4, the docked configuration is a
two-region, three-year object and porting it would carry a model that
does not survive the game's shape; the fix belongs in the laboratory,
measured against Wright again, before any C# is written for it. If
prediction 9 finds a third failure family, the bit-exact contract needs
re-examining before the port gets larger. If prediction 10 is off by
more than a factor of five, the tick budget (`docs/82`) is the next
design.

## 7. What it deliberately does not do

- No gameplay: no hiring, no selling, no rent (`docs/50` comes after).
- No write to `MarketValue`, `Rand`, Harmony or any gameplay API.
- No configuration outside §2.
- No new dependency in either language.
