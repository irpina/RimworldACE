# The docking battery: results

Design in `docs/136`. Twenty seeds at the design's configuration,
committed as `economy_lab/battery136_results.json`. **The configuration
collapsed**, and this document is the record of why. The corrected
battery is designed in `docs/138`.

## 1. Scoring the predictions

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | \|cash_balance\| < 1e-9 M every seed | 1.7e-14 | pass |
| 2 | employing ∈ [600, 1000]; bankruptcies ∈ [30, 250] | **71** (7–184); **673** (555–739) | **fail** |
| 3 | GDP growth std ∈ [0.05, 0.40]; kurtosis ∈ [−1.5, 10] | **2.74**; 0.88 | **fail** / pass |
| 4 | cost rank ∈ [−1, −0.5]; sector CV ∈ [0.1, 0.6] | **−0.39**; 0.08 | **fail** / fail |
| 5 | `x_min`/largest ∈ [0.1, 0.5]; growth kurtosis ∈ [40, 2000] | 0.15; **23.5** | pass / fail |
| 6 | production share ∈ [0.008, 0.02]; total ∈ [0.3, 0.8] | 0.0145; **0.915** | pass / fail |
| 7 | demises ∈ [0.002, 0.03] | **0.115** | **fail** |
| 8 | control bit-identical to `docs/129` | α 1.2778, kurtosis 4.2112, wage share 0.5382 | pass |
| 9 | unemployment ∈ [0.55, 0.90] | **0.989** | fail |

Nothing about the collapsed economy is a reading; predictions 3, 5 and
7 "measure" a series of deaths. `docs/136` §2 said the four last-swept
parameters had never been run together and that predictions 2 and 3
were there to test the interaction. They tested it.

## 2. What the interaction does, traced

One seed, the design's configuration, fund and purses as shares of the
money stock at month ends; then the same with one thing changed:

| month | fund | purses | workers | demand scale | employing | deaths |
|---|---|---|---|---|---|---|
| 1 | 0.283 | 0.466 | 0.251 | 0.673 | 944 | 8 |
| 5 | 0.121 | 0.629 | 0.250 | 0.291 | 865 | 21 |
| 6 | **0.010** | 0.643 | 0.250 | 0.258 | 859 | 26 |
| 10 | 0.047 | 0.607 | 0.250 | 0.111 | 128 | 351 |
| 12–30 | **0.000** | 0.5 → 0.27 | 0.250 | ~0.2 | 604 → 43 | 374 → 702 |

Three things, each a parameter interaction and none a rule:

1. **Purses swallow the fund.** A purse's working-capital target is
   five days of outlay, and outlay grows with capacity. At a
   construction unit of 20 accumulation grows total capacity **3× in six
   months and 5× in thirty** (investment off), so the purses' claim on
   the money stock rises from 47% to 68% — silver the fund needed, since
   the fund's spending *is* final demand. Demand scale falls to 0.26 by
   month 6 with nobody yet dead. At a unit of 60 capacity grows 2.7× and
   the fund keeps 14%.
2. **Investment events empty what is left.** `_invest` scales each
   project to the region's cash. With the fund at 12% of M on day 180,
   the event takes it to 1%; the second, on day 360, to zero. Without
   investment the same configuration keeps the fund at 7%, holds 789
   employing at month 30 and loses 117 firms rather than 702. Wright's
   model has no investment; ours was on for the sake of entrants, and it
   is what turned a squeeze into a collapse.
3. **A quarter of the money stock is frozen in the workers' seed.**
   `synthetic_economy` seeds `worker_cash` at a tenth of the fund's;
   the battery scaled the fund by `cash_multiplier` and the workers'
   seed only by demand, so at ×0.3 the workers open with a third of what
   the fund has — 25% of M that only ever buys the basket and never
   comes back. At ×10 it was 1% and invisible.

The cost spread is not implicated (spread 0.1 collapses identically).

## 3. Corrections carried into `docs/138`

- The workers' seed scales with the fund's (`worker_cash ×=
  demand × cash_multiplier / 10`), exactly one at the shipped
  multiplier so nothing before this document moves.
- Investment off for the docking battery (`investment=False`), stated
  as a loss: no entrants, so the firm population can only fall.
- The cash multiplier re-chosen against the purses' *grown* claim, from
  a grid measured at design time in `docs/138` and not from `docs/135`
  A, whose ×0.3 was measured at a unit of 60 with the workers' seed
  frozen.

## 4. Method note

`docs/135` §6 said to read which parameter the failure mode multiplies.
Here the failure mode multiplied three at once, and the design had
named the risk without measuring it — one 900-day run of the combined
configuration would have cost ninety seconds. **When a design says an
interaction is untested, test it before the sweep, not with it.**
