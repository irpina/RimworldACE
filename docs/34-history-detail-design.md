# Recording less history: design

Written before implementation. Short, because the scope is.

## 1. Why

`docs/33` §4 measured `Economy.history` at **~16 MiB per simulated day** at
647 commodities × 100 regions — about **3.8 GB** over a 240-day run — against
a structure that is 60 MiB. It is the one finding of the scale test that a
faster language does not fix, and the results document put it on the critical
path for the runtime port rather than behind the economics.

Every day, for every region, history stores four full commodity dictionaries
plus a computed capacity dictionary. The laboratory needs that: the frozen
reference and half the tests read paths through it. **The runtime needs none
of it** — a RimWorld colony does not want a four-year replay of every price
in every settlement resident in memory.

## 2. What changes

Two parameters on `Economy`, both defaulting to today's behavior exactly.

```python
Economy(..., record_history: bool = True, history_every: int = 1)
```

- `record_history=False` — record `{"day": n}` and nothing else. The
  opt-out the port needs.
- `history_every=k` — record a full snapshot every *k*-th day. The sampling
  option `docs/33` named beside opt-out; day 0 and the final day are always
  recorded, so a sampled run still brackets its own range.

Both exposed through `ScenarioParameters`, per the standing rule.

## 3. Design decisions

### 3.1 Default is bit-identical, and the reference proves it

`record_history=True, history_every=1` must produce byte-for-byte the same
`history` list as today. That is not an aspiration — the 154-metric frozen
reference and the exact-stationarity tests read that list, and any movement
in either is the answer.

### 3.2 `series()` refuses rather than lying

`Economy.series(region, commodity, field)` indexes history *by position* and
every caller treats the index as a day number — `prices[SHOCK_DAY + 1:]`,
`prices.index(max(prices))`. Under sampling that index is no longer a day, and
under opt-out there is nothing there at all.

So `series()` raises a clear error naming the setting that disabled it,
rather than returning a shorter list that callers would silently mis-index.
A sampled history is readable through `history` directly, where each
snapshot carries its own `day`.

This is the whole risk of the change and it is worth spending an exception
on: a quietly-truncated series would corrupt every shock metric in the
reference and nothing would fail.

### 3.3 Nothing else reads history at all

Checked rather than assumed: `_produce`, `_update_prices`, the solvers and
the ledgers never look at `history`. It is an output. If that were not true,
opting out would change the simulation, and the whole idea would be unsafe.

## 4. Non-goals

- A columnar store. Replacing the list-of-dicts with per-series arrays would
  save more and cost less per day, but it rewrites every consumer — the
  tests, `behavior.py`, and `scenarios.summary`. That is its own session, and
  it is only worth doing if the laboratory keeps needing full history at
  scale, which this change is designed to make unnecessary.
- Changing what a full snapshot contains.
- `_allocate_orders`, still 42% of a simulated day and still waiting for a
  session that says so first.

## 5. Tests

1. Default output is unchanged — the frozen reference does not move.
2. `record_history=False` leaves only day markers, and the simulation is
   otherwise **bit-identical**: same prices, inventories, cash, ledgers.
3. `history_every=k` records the expected days, including the first and last.
4. `series()` raises, naming the setting, under both.
5. The scale harness at 647 × 100 shows the memory difference.

## 6. Predictions

**6.1 Peak memory at 647 × 100 falls from 87.4 MiB (2 days) to about 60
MiB**, and stops growing with the run length. The structure was measured at
6.0 MiB for 647 × 10, so ~60 MiB at a hundred regions, and the growth term
disappears entirely.

**6.2 CPU per simulated day falls by roughly 5%.** `_record_history` was
0.6% of the profiled run, but the profiler understates dictionary copying;
call it single digits. This is a memory change, not a speed one, and the
results document should not dress it as one.

**6.3 Nothing else moves.** No behavioral metric, no test, no residual.

**6.4 A 240-day run at full scale becomes possible for the first time** — not
fast, at 22 s a day, but no longer bounded by memory. Whether it is worth
running is a separate question this session does not answer.
