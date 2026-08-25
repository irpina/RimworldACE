# Recording less history: results

Recorded after implementing the design in `docs/34-history-detail-design.md`.

## Headline

The one finding of the scale test that a faster language could not fix is
fixed, and the design document's own §3.3 was wrong in a way worth keeping.

- `record_history=False` and `history_every=k`, both defaulting to today's
  behavior. **The 154-metric frozen reference does not move.**
- Memory at full scale falls from **117 MiB after four days to 54.4 MiB**,
  and — the point — **stops growing with the run**.
- The saving matches the growth rate `docs/33` measured independently, so a
  240-day run at full scale goes from ~3.8 GB to a flat 54 MiB.
- 154 tests (147 prior + 7).
- **§3.3 was wrong**: `commodity_balance` read its opening stock out of
  `history[0]`, so opting out broke the material ledger. Fixed properly
  rather than worked around.

## 1. What the numbers say

| commodities × regions | peak, full history | peak, no history | history entries |
|---|---:|---:|---:|
| 6 × 2 | 0.3 MiB | 0.3 MiB | 356 |
| 64 × 2 | 0.3 MiB | 0.3 MiB | 3,478 |
| 647 × 2 | 3.1 MiB | **2.1 MiB** | 34,734 |
| 647 × 10 | 11.0 MiB | **6.2 MiB** | 152,966 |

Three simulated days each. The saving at 647 × 10 is 4.8 MiB over three days
— **1.6 MiB per day**, which is precisely the growth rate `docs/33` measured
independently. At a hundred regions that is ~16 MiB a day, and the
difference between a run that ends and a run that does not.

The structure itself does not change: 2.1 MiB at two regions, 6.2 at ten.
What disappears is the term that scales with *run length*, which is the only
term the runtime port could not have absorbed with faster code.

At full scale — 647 commodities, 100 regions, 64,700 producers — the two
readings after four simulated days are:

| | peak |
|---|---:|
| full history | **117.18 MiB**, growing ~14.9 MiB a day |
| no history | **54.37 MiB**, flat |

**Prediction 6.1 said "about 60 MiB, and stops growing".** It is 54.4 and it
does. Over a 240-day run that is the difference between ~3.8 GB and 54 MiB —
about a seventieth.

## 2. What did not change

**Not one behavioral metric.** The default path is byte-for-byte the same
`history` list it was, which is what the frozen reference and the
exact-stationarity tests were positioned to check.

**Not the simulation, under either setting.** Asserted directly: an
equilibrium run with `record_history=False` gives bit-identical prices,
inventories, cash, worker cash, labor values and rate of surplus value to one
recording everything. That is the property that makes the option safe, and it
is now a test rather than an argument.

**Not the speed, meaningfully.** Prediction 6.2 guessed ~5%; the timings
taken during this session are contaminated — the test suite and the
measurement competed for the machine, and the same full-scale configuration
that measured 22.3 s/day in `docs/33` measured 33.9 s/day here. **No CPU
claim is made from this session's numbers.** `docs/33`'s stand; this change
is about memory and is reported as such.

## 3. `series()` refuses, and that was the risk worth spending on

`Economy.series(region, commodity, field)` returns one value per day and
every caller indexes it positionally as a day number — `prices[SHOCK_DAY +
1:]`, `prices.index(max(prices))`. Under sampling the index is no longer a
day; under opt-out there is nothing there.

So it raises, naming the setting that disabled it. A shorter list would have
been silently mis-indexed by every shock metric in the reference **and
nothing would have failed** — the reference would simply have frozen a set of
wrong numbers. This is the same hazard class as `docs/33`'s one-ulp
divergence, where the test caught what the reference could not, and the same
answer: make the wrong thing impossible rather than unlikely.

## 4. The design was wrong about §3.3, and the fix is better than the claim

> "Nothing else reads history at all. Checked rather than assumed."

It was not checked. `Economy.commodity_balance` opened with

```python
initial = self.history[0]["system_inventory"][commodity]
```

so the *material ledger* — the project's oldest invariant — depended on an
output artifact. Turning history off broke it immediately, at the first run
of the scale harness.

The fix is not a guard. The opening stock is now state, recorded at
construction:

```python
self.opening_inventory = {
    name: self.system_inventory(name) for name in self.commodities
}
```

which is where it belonged. A ledger reading its own report to find out what
it started with is a latent bug independent of this session; it happened to
be harmless only because history was always on.

**The lesson is about the phrase, not the line.** "Checked rather than
assumed" was written to sound like diligence and was doing the opposite —
asserting a property confidently enough that nobody would go and look. A
design document that says "I have not checked this" is worth more than one
that says it has and hasn't.

## 5. Prediction scorecard

| prediction | outcome |
|---|---|
| 6.1 memory falls to ~60 MiB and stops growing | **correct** |
| 6.2 CPU falls ~5% | **not measured** — this session's timings are contaminated |
| 6.3 nothing else moves | correct, and asserted bit-exactly |
| 6.4 a 240-day full-scale run becomes possible | correct on memory; still 22 s/day |
| 3.3 nothing reads history | **wrong** — the material ledger did |

## 6. Where this leaves the port

The `docs/33` finding is retired. The runtime can carry the model's state —
about 54 MiB at 647 commodities and 100 settlements — without carrying a
replay of it, and the laboratory keeps its full history by default because
that is what the reference and half the tests read.

`history_every` is the middle option if a future runtime wants a coarse
series for a UI: it costs one snapshot every *k* days and keeps day zero and
the last day so a sampled run brackets its own range.

Next, unchanged: **`_allocate_orders`**, still 42% of a simulated day, still
waiting for a session that names it first. Then the economics backlog — a
capital-goods sector, capacity depreciation and exit, recreation in the
basket.

## Reference decision

One commit. The reference is untouched: this session added an option and
changed no observation.
