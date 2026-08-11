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

- **496 defs** get an embodied-labor value; 1315 are unreachable from
  extraction (animals, plants, generated meat/leather defs, buildings needing
  trade-only inputs like Neutroamine, and everything gated behind
  `specialProducts`).
- Production depth: 29 at depth 0 (extraction), 237 at depth 1, 157 at depth
  2, 73 at depth 3. RimWorld's production graph is shallow.
- 171 defs used a substitutable input (cheapest-by-labor); 14 had more than
  one production option and took the minimum-labor path. Both flagged in
  `out/embodied_labor.csv`.
- **Joint production never arises.** There are zero multi-output recipes in
  XML — every joint case in RimWorld is a `specialProducts` recipe, which is
  code-driven and excluded. The apportionment rule the brief worried about is
  unreachable; `APPORTION` remains as a documented hook.

### One modelling decision worth knowing about

`ComponentIndustrial` can be *mined* out of ancient ruins for 1250 ticks or
*manufactured* for 5570 — a 4.5× gap that propagates to every good using
components. Socially necessary labor time is a reproduction cost, so the
default (`SCAVENGING = "exclude"`) drops mining options for goods that can
actually be produced. This changes 225 defs by up to 4.5×. Every headline
number below is reported under both settings; the conclusion does not depend
on the choice.

## Result: there is no single rate, and the gap is 12.7×

Two models, both through the origin, over the 496 defs with a price:

| model | | R² |
|---|---|---|
| `price = r · L` | r = 0.01123 (**28.1** silver/work-hour) | 0.841 |
| `price = a·E + b·F` | a = 0.03936 (**98.4**/hr), b = 0.00310 (**7.8**/hr) | **0.957** |

where `E` is labor originating at extraction and `F` is labor added by
fabrication (`E + F = L` exactly, verified on all 496 rows).

Adding one parameter takes R² from 0.841 to 0.957. **a/b = 12.7×.**

### Two independent confirmations

**The fabrication rate was predicted and recovered.** RimWorld hardcodes
`0.0036` silver/tick for fabrication work. The regression was never given
that number — it fits `b` from prices and labor amounts derived separately —
and returns **0.00310, i.e. 0.86× the hardcoded constant.** Under the other
scavenging policy it returns 0.00426, or 1.18×. The true constant sits
between them. That is a falsifiable prediction about a value the pipeline
never saw, and it held.

**The extraction rate matches the primitives analysis.** `02-primitives.md`
estimated a median 101 silver/work-hour for extraction labor from 30 hand-
authored primitive prices. This regression, over a different set of 496 defs
by a different method, returns **98.4 silver/work-hour** — agreement within
3%, from independent data.

### The gradient

If one rate governed the economy, implied rates would not move with a good's
labor mix. They move monotonically:

| fabrication share of embodied labor | n | median implied rate |
|---|---|---|
| 0–20% | 58 | 114.6 silver/hr |
| 20–40% | 47 | 96.8 |
| 40–60% | 63 | 78.7 |
| 60–80% | 171 | 35.8 |
| 80–100% | 157 | 23.6 |

Five buckets, strictly monotone, a 4.9× fall. The more of a good's labor is
fabrication, the less that labor is worth.

### Robustness

| | single r | a (extraction) | b (fabrication) | a/b | R² |
|---|---|---|---|---|---|
| `SCAVENGING=exclude` | 0.01123 | 98.4/hr | 7.8/hr | 12.7× | 0.957 |
| `SCAVENGING=include` | 0.01419 | 88.2/hr | 10.7/hr | 8.3× | 0.954 |

## What it means

**RimWorld's economy pays roughly 98 silver per hour of extraction labor and
roughly 8 per hour of fabrication labor.** The 11× asymmetry found in the
primitives is not an artifact of that small sample — it is the dominant
structural feature of the whole price system, and it survives every robustness
check applied.

Mechanically the cause is now clear. RimWorld computes a fabricated good's
price as authored input prices plus one hardcoded constant times the final
step's work. The authored input prices embed an implicit labor rate an order
of magnitude higher than that constant, and the two were never reconciled —
exactly the unreconciled pair of value systems the project set out to find,
but located at a different seam than expected. It is not `workAmount` versus
`BaseMarketValue`. It is **extraction labor versus fabrication labor**, priced
12.7× apart inside `BaseMarketValue` itself.

For play, this says something concrete: in RimWorld, crafting barely pays. A
colonist-hour at a workbench adds ~8 silver of value; the same hour at a
mining face adds ~98. Value is claimed where materials enter the colony, and
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
- 1315 defs are unreachable and excluded; the sample skews toward
  manufactured goods and buildings.
- Extraction labor assumes nominal `MiningSpeed`/yield and excludes
  prospecting, hauling, and travel. Real extraction labor is higher, which
  would widen the gap, not narrow it.
- OLS through the origin is dominated by expensive items; the per-good
  median and the bucket medians are reported alongside for that reason.
