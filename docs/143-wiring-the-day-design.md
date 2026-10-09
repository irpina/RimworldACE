# Wiring the docked day into the world: design

Written before any of it is built. `docs/141` slices 1 to 8 are done:
the C# holds the laboratory's whole state, builds the docked economy
from a seed to the bit, and runs its days to the bit for 180 days. Slice
9 is what `docs/141` §4 left for last, putting that day inside
`EconomyWorldComponent`. This document says what slice 9 has to contain
that `docs/141` did not spell out, what it decides, and what would show
it wrong.

## 1. What slice 9 turned out to need

`docs/141` described slice 9 as wiring plus a tab. Reading the component
against the port shows three more pieces.

- **A save format for the whole state.** The component persists the
  economy as one string in one `Scribe_Values.Look`, with every double
  written as its bits (`docs/80`, `docs/81`). That codec carries the old
  `EconomySnapshot`: prices, stocks and a few scalars. The docked state
  is about 190 fields. The JSON codec that checks the port lives in the
  harness and uses `System.Text.Json`, which the game's runtime does not
  have, and adding it would be a dependency.
- **A region count from the world.** `ProfileBuilder` already derives
  regions from factions. The economy needs that count once, when it is
  built.
- **A commodity count.** `docs/141` §3 left this open between the
  battery's 200 and the full population. Slice 0 has now closed it: the
  laboratory **refuses** to build the docked economy above about 480
  commodities. The fund is a fixed sum per region and the purses' working
  capital grows with the number of final goods, so at 647 the purses ask
  for 1.38 times the fund (`docs/142`).

## 2. Decisions

1. **The game builds `build_ours(seed, commodities=200, regions=n,
   **DOCKED)`.** That is the configuration that docked, at the size that
   docked. The full population waits for a laboratory fix that scales
   the fund with the economy, measured against Wright again, as
   `docs/141` §6 requires. The port does not invent that fix.
2. **The save format is generated**, like the state model, by
   `economy_lab/state_codegen.py`: a token stream in which a double is
   its sixteen hex digits, an integer is decimal, a string is
   percent-escaped, and every collection carries its count. It lives in
   `Economy.Core`, so it compiles for the game's runtime with no
   dependency. Schema 4. A schema-3 save loads with no economy and builds
   one, which is what a schema-2 save already does.
3. **Regions are built once.** The economy is created on the first day
   a world has at least one faction region, with that many regions and
   the world's `persistentRandomValue` as the seed. A faction founded or
   destroyed later does not rebuild it. Changing the region count of a
   running economy is a model question the laboratory has not asked.
4. **Each docked phase is one scheduler phase**, fifteen a day, one per
   tick. The scheduler and its resume rule are unchanged; a save landing
   mid-day resumes at the next phase.
5. **Nothing in the game is touched.** No `MarketValue`, no `Rand`, no
   Harmony, no new RimWorld API: the component compiles against the
   unedited facade.

## 3. How it is checked

All of this runs here, without the game. `Economy.Drive` compiles the
component's own sources against the facade and runs them under **Mono**,
the game's runtime, so the run is also the first time the docked day
executes on Mono at all.

## 4. Predictions

1. **The save format round-trips every state the fixtures hold**:
   decoding and re-encoding gives the same text, and the decoded state
   writes the same JSON as the original, on the first compile. If one
   does not, the cause is ordering, not arithmetic.
2. **Saving and loading after every phase changes nothing**: a run that
   is encoded and decoded between every phase of every day ends
   bit-identical to the run that never was, over the 180-day and the
   battery fixtures.
3. **The battery's state encodes to between 0.5 and 2 MB.** About 30
   numbers per producer at 17 characters, times 1,600 producers, plus
   the regions' maps. Above 2 MB at two regions would make a six-region
   save large enough to matter.
4. **The docked day under Mono is bit-identical to the day under .NET
   8.** `docs/76` found the solvers exact under Mono, and `exp` and `pow`
   both go to the same libm here. This is a statement about this
   machine. Windows and macOS keep the open `exp`/`pow` question
   `docs/141` raised.
5. **A docked day under Mono costs under three times what it costs
   under .NET 8.** Mono's JIT is older. A factor above three would make
   the tick budget (`docs/82`) the next design.
6. **The component compiles against the facade with zero errors and the
   facade unedited**, and `Economy.Drive`'s existing scenarios still
   pass with the economy running.

## 5. What would make this wrong

If prediction 2 fails, the scheduler's mid-day resume is not as safe as
`docs/83` argued, and the save would corrupt a long game slowly. If 4
fails, Mono's arithmetic differs from .NET's somewhere other than the
two transcendental calls, and bit-exactness in the game is in doubt
before any player sees it. If 3 fails high, the save needs compressing,
which is a dependency question.

## 6. What it does not do

- No gameplay, as in `docs/141` §7.
- No commodity count above 200 until the laboratory can build one.
- No in-game measurement. The tick budget, the save in a real game and
  the tab's appearance need a person at RimWorld.
