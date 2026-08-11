# The endogenous rate test

RimWorld's own formula makes this question unaskable: it *sets* the price of
labor at `0.0036` silver/tick and seeds the recursion with authored prices, so
asking "what rate does the data imply" just returns the constant you fed it.

`solver.py` breaks the circularity. Embodied labor is computed from extraction
work amounts and production work amounts only — no market value enters at any
point. That gives an independent labor measure to regress price against.

## The solver

Minimum-cost hyperpath from extraction, relaxed from `+inf` to a fixed point.
Converges in 4 iterations. Cycles (steel → components → machines → steel) need
no special handling: every option cost is non-negative and monotone in its
inputs, so a cycle can never lower a cost and simply never wins.

- **653 defs** get an embodied-labor value; 1285 are unreachable from
  extraction (animals, plants, generated meat/leather defs, buildings needing
  trade-only inputs like Neutroamine, and everything gated behind
  `specialProducts`).
- Production depth: 163 at depth 0 (extraction), 252 at depth 1, 159 at
  depth 2, 79 at depth 3. RimWorld's production graph is shallow.
- 180 defs used a substitutable input (cheapest-by-labor); 109 had more than
  one production option and took the minimum-labor path. Both flagged in
  `out/embodied_labor.csv`.
- **Joint production arrives through the back door.** There are zero
  multi-output *recipes* in XML, so the apportionment rule looked unreachable
  at first. But mining spoil is a joint product (space + chunks), and the
  choice turned out to matter a lot — see below. The stone case is handled by
  `BYPRODUCT`; butchery (meat + leather from one carcass) by `APPORTION` in
  `animals.py` — see `05-animals.md`, where the same test that settled stone
  turned out **not** to discriminate.

### Mining spoil: a joint-production call the data settled

Natural rock declares a `mineableThing` (a chunk) with `mineableDropChance`
0.25 and no explicit yield — `BuildingProperties`' constructor defaults
`mineableYield` to 1 and `mineableDropChance` to 1.0, so a granite cell drops
one chunk a quarter of the time. Mining that cell is done for the *space*;
the chunk is spoil.

Charging chunks the full mining cost (1200–4800 ticks per chunk) is the
obvious first move and it is wrong:

| chunk treatment | a (extraction) | b (fabrication) | a/b | R² |
|---|---|---|---|---|
| bears full mining labor | 60.7/hr | 14.0/hr | 4.3× | 0.854 |
| **free byproduct** | **96.5/hr** | **6.6/hr** | **14.7×** | **0.948** |

*(figures from the solve as it stood at that point, before animal products;
the comparison between the two rows is what matters, not the absolute values)*

Charging it halves the extraction rate, breaks agreement with the
independent primitives estimate (~101/hr), and drops R² by 0.09. Treating
chunks as costless restores all three. `BlocksGranite` goes from 320 ticks
(implying 7.0 silver/hr, below even the fabrication rate) to 80 ticks
(28.1/hr, right at the single-rate median).

So RimWorld prices stone as though the chunk were free, and `BYPRODUCT =
"free"` is the empirically supported default rather than an assumption. This
is the joint-production question from the brief arriving through the back
door — and for stone it was decidable from the data rather than by fiat.

### One modelling decision worth knowing about

`ComponentIndustrial` can be *mined* out of ancient ruins for 1250 ticks or
*manufactured* for 5570 — a 4.5× gap that propagates to every good using
components. Socially necessary labor time is a reproduction cost, so the
default (`SCAVENGING = "exclude"`) drops mining options for goods that can
actually be produced. This changes 225 defs by up to 4.5×. Every headline
number below is reported under both settings; the conclusion does not depend
on the choice.

## Result: there is no single rate

Two models, both through the origin, over the 647 defs with a price:

| model | | R² |
|---|---|---|
| `price = r · L` | r = 0.01068 (**26.7** silver/work-hour) | 0.852 |
| `price = a·E + b·F` | a = 0.03792 (**94.8**/hr), b = 0.00271 (**6.8**/hr) | **0.948** |

where `E` is labor originating at extraction and `F` is labor added by
fabrication (`E + F = L` exactly, verified on all 653 rows).

Adding one parameter takes R² from 0.852 to 0.948. **a/b = 14.0× in levels** —
but see the estimator-sensitivity section below before quoting that number.

### Two confirmations

**The fabrication rate was predicted and recovered.** RimWorld hardcodes
`0.0036` silver/tick for fabrication work. The regression was never given
that number — it fits `b` from prices and labor amounts derived separately —
and returns **0.0027, i.e. 0.75× the hardcoded constant.** That is a
falsifiable prediction about a number the pipeline never saw, landing within
30% of it. It is a sanity check on the whole chain, not an exact recovery —
the residual 27% is real and most plausibly reflects that our fabrication
labor includes *upstream* fabrication (components made rather than bought at
their authored 32 silver), which RimWorld's own formula never charges for.

**The extraction rate matches the primitives analysis.** `02-primitives.md`
estimated a median 101 silver/work-hour from 30 hand-authored primitive
prices; this regression returns **94.8** — within 6%. Note this is
consistency, not independent corroboration: 22 of those 30 primitives are
harvested, and both estimates read the same `harvestWork` field. For a real
bound on that shared input, see the plant sensitivity in `robustness.py`.

### The gradient

If one rate governed the economy, implied rates would not move with a good's
labor mix. They move monotonically:

| fabrication share of embodied labor | n | median implied rate |
|---|---|---|
| 0–20% | 58 | 114.6 silver/hr |
| 20–40% | 42 | 90.1 |
| 40–60% | 56 | 85.9 |
| 60–80% | 151 | 33.4 |
| 80–100% | 212 | 24.2 |

Animal products are excluded here. Included, the top bucket reads 345/hr,
because a median over defs weights a thrumbo hide the same as a steel bar
while least squares effectively ignores it - the butchery artifact of
`05-animals.md` inflates the bucket without touching the fit.

Five buckets, strictly monotone, a 4.9× fall. The more of a good's labor is
fabrication, the less that labor is worth.

### Robustness to the scavenging policy

| | single r | a (extraction) | b (fabrication) | a/b | R² |
|---|---|---|---|---|---|
| `SCAVENGING=exclude` | 0.01068 | 94.8/hr | 6.8/hr | 14.0× | 0.948 |
| `SCAVENGING=include` | 0.01302 | 91.9/hr | 6.4/hr | 14.5× | 0.946 |

Once stone is treated correctly the scavenging choice barely matters — 14.0×
versus 14.5×. The component question was load-bearing only while the stone
byproduct question was being answered wrongly.

## Robustness: the magnitude is estimator-dependent

The fit above is OLS in levels, which minimises absolute error and is
therefore dominated by expensive goods: **the ten priciest goods carry 47% of
the squared-error weight, the top fifty carry 76%.** Re-weighting changes the
ratio a lot:

| estimator | extraction | fabrication | ratio |
|---|---|---|---|
| OLS in levels | 94.8/hr | 6.8/hr | **14.0x** |
| OLS, equal relative weight | 47.9/hr | 15.7/hr | **3.1x** |
| least squares in log space | 97.6/hr | 26.1/hr | **3.7x** |

*(animal products excluded)*

What survives every estimator: extraction exceeds fabrication, and two rates
beat one. The log-space R2 goes 0.548 -> 0.712 with all defs, 0.777 -> 0.839
with animals excluded. So the split is real; the multiple is a choice about
what you average over. 14x describes where the game's total value sits; 3-4x
describes a typical item.

`robustness.py` reproduces all of this, plus the plant-labor sensitivity.

## What it means

**RimWorld's economy pays several times more for an hour of extraction labor
than for an hour of fabrication labor** — roughly 95 versus 7 weighting by
total value, roughly 48 versus 16 weighting goods equally. The asymmetry found in the
primitives is not an artifact of that small sample — it is the dominant
structural feature of the whole price system. Its *direction* survives every
robustness check applied; its magnitude does not, ranging from ~3x to 14x
depending on weighting.

Mechanically the cause is now clear. RimWorld computes a fabricated good's
price as authored input prices plus one hardcoded constant times the final
step's work. The authored input prices embed an implicit labor rate several times higher
than that constant, and the two were never reconciled —
exactly the unreconciled pair of value systems the project set out to find,
but located at a different seam than expected. It is not `workAmount` versus
`BaseMarketValue`. It is **extraction labor versus fabrication labor**, priced
several times apart inside `BaseMarketValue` itself.

For play, this says something concrete: in RimWorld, crafting pays poorly. A
colonist-hour at a workbench adds ~7-16 silver of value depending on
estimator; the same hour at a mining face adds ~48-95. Value is claimed where materials enter the colony, and
labor spent transforming them is nearly free — which is precisely the
divergence between labor time and value that the mod exists to surface.

### The residuals are the interesting part

Against the single-rate baseline:

**Overpriced** — GauranlenSeed 31.2×, Ambrosia 26.7×, Drug_Psilocap 22.3×,
inert relics 11.9–19.8×, Gold 18.7×, RawFungus 17.2×. Rarity- and
event-gated goods, the same cluster `02-primitives.md` and `03-overrides.md`
found from two other directions.

**Underpriced** — Dye 0.32×, VoidSculpture 0.38×, the Anomaly hearts 0.41×,
TrapIED_EMP 0.41×, Shell_EMP 0.41×. Component-heavy goods, whose labor cost
is dominated by manufacturing components the game prices at a flat authored
32 silver. Note this cluster is the most sensitive to the scavenging policy.

The residual against the two-rate baseline is a usable measure of price set by
role rather than production — a better one than the single-rate residual,
because it no longer confounds "priced by rarity" with "made mostly of
materials".

## Caveats

- Price here is RimWorld's `BaseMarketValue`, which for ~466 defs is itself
  computed. That is not circular for this test — embodied labor is
  independent — but it does mean the fit partly measures the internal
  consistency of RimWorld's formula, which is what makes recovering `b ≈
  0.0036` a validation rather than a discovery.
- 1295 defs are unreachable and excluded; the sample skews toward
  manufactured goods and buildings.
- Extraction labor assumes nominal `MiningSpeed`/yield and excludes
  prospecting, hauling, and travel. Real extraction labor is higher, which
  would widen the gap, not narrow it.
- OLS through the origin is dominated by expensive items; the per-good
  median and the bucket medians are reported alongside for that reason.
