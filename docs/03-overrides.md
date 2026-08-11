# The deliberate overrides

49 defs (not 25 — the earlier count missed `ParentName` inheritance) carry an
authored `MarketValue` *and* a `costList`/`costStuffCount`. Because an authored
value short-circuits the calculation entirely, each of these is a place where
someone looked at what the formula would produce and typed a different number.

`out/overrides.csv` has the full table with the input/labor split. Computed
values come from `value_model.py`, a transcription of
`CalculatedBaseMarketValue` that reproduces the worked assault-rifle example
exactly (482).

## What the humans actually did

Three distinct behaviours, and they are not subtle once sorted.

### 1. Flattening a category to one price

The largest pattern. Cost differences within a category are erased in favour
of a single legible number.

**Shells** — all seven priced at exactly 55, against computed values from 47.5
to 92.5:

| shell | computed | authored |
|---|---|---|
| Shell_EMP | 92.5 | 55 |
| Shell_Incendiary | 65.0 | 55 |
| Shell_HighExplosive | 63.0 | 55 |
| Shell_Smoke | 47.5 | 55 |
| Shell_Firefoam | 47.5 | 55 |
| Shell_Toxic | 42.0 | 55 |
| Shell_Deadlife | 18.75 | 55 |

A 4.9× cost spread collapsed to a flat price. Mortar ammo is priced by what
the player should pay for a shell, not by what it costs to make one.

**Relics** — all eight `RelicInert*` at 500 against a computed 200.
**Mechanitor implants** — `ControlSublink`, `RemoteRepairer`, `MechFormfeeder`,
`RemoteShielder`, `RepairProbe`, `ControlSublinkHigh` all at 1200 against
computed values from 640 to 1912.

### 2. Rounding a computed value to a legible number

A distinct population where the authored number is *within a few percent* of
what the formula produces. These read as: compute it, then snap it.

| def | computed | authored |
|---|---|---|
| RemoteRepairer | 1203.52 | 1200 |
| RemoteShielder | 1203.52 | 1200 |
| PsychicEmanator | 1302.20 | 1300 |
| VanometricPowerCell | 1390.00 | 1200 |
| InfiniteChemreactor | 1608.80 | 1500 |
| DetoxifierLung | 1028.60 | 925 |

Every authored value across all 49 is a round number. None of the computed
values are. That is the clearest signal in the dataset that these were typed
by a person aiming at legibility.

### 3. Genuine repricing

Where authored and computed genuinely diverge, the marked-up goods are the
predicted cluster: drugs, serums, and artifacts.

| def | computed | authored | × |
|---|---|---|---|
| JuggernautSerum | 17.50 | 200 | **11.4×** |
| MetalbloodSerum | 20.00 | 200 | **10.0×** |
| UnstablePowerCell | 65.08 | 400 | 6.2× |
| VoidsightSerum | 19.50 | 60 | 3.1× |
| Telescope | 127.00 | 350 | 2.8× |
| ShieldGeneratorBullets/Mortar | 414.08 | 1000 | 2.4× |
| GhoulResurrectionSerum | 25.00 | 60 | 2.4× |
| MindNumbSerum | 34.50 | 80 | 2.3× |
| WakeUp | 15.24 | 35 | 2.3× |
| Flake | 8.50 | 14 | 1.6× |
| GoJuice | 35.16 | 53 | 1.5× |
| SmokeleafJoint | 8.02 | 11 | 1.4× |
| Yayo | 16.46 | 21 | 1.3× |

Every recreational and combat drug in the game is marked up. Not one is
marked down. The Anomaly serums — trivially cheap to produce, enormously
powerful — carry the two largest markups in the dataset.

The markdowns are fewer and mostly mild, with one extreme:

| def | computed | authored | × |
|---|---|---|---|
| GravlitePanel | 25.48 | 4 | **0.16×** |
| Shell_EMP | 92.50 | 55 | 0.59× |
| RepairProbe | 1911.52 | 1200 | 0.63× |
| ControlSublinkHigh | 1707.52 | 1200 | 0.70× |
| MedicineIndustrial | 23.02 | 18 | 0.78× |
| OxygenPump | 261.20 | 200 | 0.77× |

`GravlitePanel` is the outlier: an Odyssey structural material cut to a sixth
of its computed cost, which is what you do to a material you intend players to
use in bulk.

Tally: **34 marked up, 12 marked down, 3 at parity.**

## What this says

The overrides are not corrections to a miscalibrated formula. They are the
formula being set aside wherever price needs to carry a gameplay signal:

- **Category coherence beats cost accuracy.** All shells cost the same because
  a player choosing between shell types should not be doing cost arithmetic.
- **Power is priced, not production.** The serums are the clearest case in the
  game of price tracking use-value — what the item *does* — with production
  cost ignored by an order of magnitude.
- **Drugs are uniformly dear.** A consistent editorial thumb on the scale,
  applied to every drug and to nothing else in the same direction.

For the mod, these 49 are the ground truth for "price set by role rather than
production." They pair with the primitives finding: the same judgment that
prices gold at 5× its labor prices a Juggernaut serum at 11× its cost. Same
boundary, drawn twice, at opposite ends of the production graph.
