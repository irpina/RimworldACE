# The mod, slices 0 to 8: results

Scores `docs/141`'s ten predictions. Slice 0 measured the docked
configuration at the game's shape in Python; slices 1 to 8 ported it to
C#. Four predictions pass outright, two pass with a qualification, and
four fail. Two of the failures change the plan.

## 1. Slice 0: the game's shape

Three seeds at each shape, 1,800 days, the docked configuration of
`docs/138`. The figures are in `economy_lab/game_shape142_results.json`,
written by `python3.12 -m economy_lab.game_shape`.

| shape | producers | employing at day 1,080 | value added a day per region, last year | survivors 180 to 1,800 | prices pinned at day 1,800 |
|---|---|---|---|---|---|
| 2 regions, 200 commodities | 1,600 | 0.473 | 4.31 M | 0.67 to 0.78 | 13.5% to 17.3% |
| 6 regions, 200 | 4,800 | 0.467 | 4.34 M | 0.70 to 0.76 | 12.8% to 15.5% |
| 10 regions, 200 | 8,000 | 0.446 | 4.65 M | 0.68 to 0.77 | 12.5% to 15.3% |
| 6 regions, 647 | none | refused at construction | | | |

**1. Money is conserved: passes.** The largest balance in any month of
any run is 1.3e-14 of the money stock.

**2. Region count is neutral: passes on the means.** At six regions the
employing share is 1.3% below the two-region figure and value added 0.6%
above. At ten they are 5.6% below and 7.9% above. One seed at ten
regions is outside the band on its own, at 15.9% below and 21.2% above;
the other two are within 3%.

**3. Commodity count is neutral: fails before any day runs.** The
laboratory refuses to build the docked economy at 647 commodities. Each
region's fund is a fixed sum, the authored 1,000,000 times
`cash_multiplier` times demand. The purses' working capital grows with
the number of final goods, because every deepest commodity carries
authored demand. Seeding the purses takes the whole fund at about 480
commodities.

| commodities | final goods | purse targets over the fund |
|---|---|---|
| 24 | 1 | 0.008 |
| 200 | 25 | 0.450 |
| 300 | 36 | 0.647 |
| 400 | 52 | 0.829 |
| 500 | 61 | 1.046, refused |
| 647 | 79 | 1.378, refused |

This is a calibration fault, not a model fault. The fund was sized for
the battery (`docs/124`, `docs/137`), and nothing scales it with the
economy. `docs/141` §6 says the fix belongs in the laboratory, measured
against Wright again, before the port carries it. Until then the game
runs at 200 commodities (`docs/143` §2).

**4. The economy survives a long game: passes.** Between 67% and 78% of
producers employing at day 180 still employ at day 1,800, against a bar
of half. This counts producers, not identities: a producer that died and
one that started employing would cancel. The last year's value added is
0.94 to 1.19 of the first year after burn-in. The over-accumulation
crisis settles rather than compounds.

**5. Prices stay inside their bounds: fails, at every shape.** 12.5% to
17.3% of commodity-region prices sit at a bound on day 1,800, against a
bar of 5%. Every one is at the floor and none at the ceiling. At day
600 in the two-region run, they are 27 commodities per region that
nobody produces, with no stock and no throughput: sectors whose
producers all went bankrupt, whose price falls to the floor because
nothing holds it up. The figure is the same at two regions as at ten,
so it belongs to the docked configuration, not to the game's shape.
`docs/139` measured at 36 months and never looked at bounds. The
prediction measured dead sectors, not mispriced live ones, and the
honest reading is that **about one sector in eight dies and stays
dead**, because the docked configuration has no entry.

**6. Cost is linear in producers: fails.** On an idle machine, Python
costs 91, 138 and 150 ms a day per thousand producers at two, six and
ten regions, a spread of 66% against a band of ±30%. The cost grows
with routes. The ring connects each region to three neighbours, so the
route count is 1, 15 and 30, and arbitrage's work grows with routes
times commodities. The C# port is the reverse: 13.1, 7.3 and 7.5 ms per
thousand, because its value solve has a fixed cost that larger shapes
spread thinner. The prediction was about Python and fails. It does not
matter for the game, which runs the C#.

## 2. Slices 1 to 8: the port

**7. The docked day is between 35% and 60% of the step's code: passes.**
It is 45.3%, 683 of 1,507 lines, by tracing which lines of the step's
methods a docked day executes (`economy_lab/docked_coverage.py`).

**8. The state round-trips on the first compile: passes.** No field
mismatched.

**9. Every ported phase is bit-exact, and failures come from the two
known families: passes for the port, with a third family found in the
reference.** Every phase of the docked day reproduces the laboratory to
the bit on four real days, and whole runs do so for up to 180 days,
including bankruptcies. The one mismatch along the way was neither a
`sum()` ported as `+=` nor a dict in the wrong order. **The fixtures had
been written under CPython 3.11, whose `sum()` of floats is naive.**
CPython 3.12 made it compensated, and the port matches 3.12. That is a
third family, and it was in the reference, not the port. It also
explains the old `scale_647_day3` "machine difference" in `HANDOFF.md`,
which was an interpreter difference. Every fixture writer now refuses
to run under a naive `sum()` (`economy_lab/interpreter.py`), and the
fixture tests skip under one with the reason stated.

**10. A docked day at the battery's size costs under 20 ms in C#: fails,
narrowly.** It costs 21.0 ms on an idle machine, after two changes that
move no bits: the order book's loop invariants computed once, and
producers grouped by commodity once per phase instead of scanned per
commodity. That is a 7-fold speed-up over Python's 145 ms, against the
20-fold `docs/33` projected. `docs/141` §6 set the alarm at a factor of
five over 20 ms, and this is not near it. Production is 44% of the day
and the value solve 23%.

Slice 2 carried no prediction of its own. The generator reproduces all
four run fixtures' start states from their seeds, to the bit, on the
first compile.

## 3. What changes

- **The game runs 200 commodities.** The full population needs the fund
  scaled with the economy, a laboratory change to be measured against
  Wright first.
- **About one sector in eight dies and stays dead.** That is what the
  docked configuration does over five years, at every shape. A
  gameplay layer that reads prices should know that a floor price
  means a dead sector, not a cheap good.
- **Region count is safe up to ten**, on the means.

## 4. Open risks carried forward

- `Math.Exp` (posted prices) and `Math.Pow` (the order book) call the
  platform's libm. They agree on Linux under both .NET 8 and Mono
  (`docs/144`), but Windows and macOS are untested.
- Fixtures must be written with `python3.12` or later.
