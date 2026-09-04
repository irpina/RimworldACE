# The laboratory viewer: results

`docs/48` said what the viewer would show and what it would refuse to do.
This records what shipped, what the acceptance check read off the screen,
and the three places the design met the code and had to give.

## 1. What shipped

```
python -m economy_lab.viewer          # http://127.0.0.1:8765/
```

Six files of Python under `economy_lab/viewer/` and three of HTML, CSS and
JavaScript under `static/`. Ten JSON endpoints, all of them reads except
the two that run something on request — a scenario, or the metric
collection — and cache it. Thirty-three tests in `tests/test_viewer.py`.
No dependency on either side of the socket.

Nothing in the laboratory changed. The 191 tests pass unchanged and
`python -m economy_lab.baseline` shows a delta of exactly zero on all 211
metrics, which the viewer's own Metrics page also reports after collecting:
**211 shown, 0 moved beyond rounding.**

## 2. The acceptance check

The design's "done" was one person, one command, one browser, and the
docs/47 result visible without a terminal. Run `demand_boom` twice, with
`bargaining` false and then true, and open Compare with the first as A and
the second as B.

| Dust Basin, day 360 | A: wages at value | B: bargaining on | B − A |
|---|---:|---:|---:|
| meals price (silver) | 15.0000 | 15.5992 | **+3.99%** |
| meals inventory (units) | 18.0435 | 17.4203 | −3.45% |
| meals labor value (work-ticks) | 305.3588 | 305.3588 | −5.7e-14 |
| rate of surplus value s/v | 26.7082 | 26.7082 | −5.3e-7 |
| realized rate, wages as paid | 26.7082 | 25.6796 | −3.85% |
| uniform profit rate (per day) | 1.1726 | 1.1726 | 0 |

The three rows docs/47 rests on are on one screen: the price moved, the
value did not, and the realized rate fell while the value rate held — the
premium is a deduction from surplus value, not a change in its amount. The
row that moved is shaded red on the page; the rows that did not are white.
`docs/47` is one click from the run, and the §6 explanation of *why* the
price moved — demand for wage goods, not their cost — is in it.

## 3. Where the design gave

**A sampled history has no summary.** `docs/48` §2.2 said the viewer reads
`history` directly so that a `history_every` override "produces a sparser
chart rather than a wrong one". True of the charts. But the end-state
summary the run page shows is `scenarios.summary`, and that calls
`series()`, which refuses a sampled history for exactly the reason docs/34
gave. So a sampled run carries its charts, its ledgers — those read the
ledger and the readings, not the series — and a note in place of the
summary saying why. The design did not think about which of its outputs
were positional.

**The documents cross-reference in backticks.** The design promised that
`docs/NN` in running text would become a link. Forty-seven documents write
it as `` `docs/NN` ``, in code spans, which the renderer protects from
every other substitution. A code span whose whole content is a document
reference is now a link wearing code styling; nothing else inside a code
span is touched. Found by counting the links in the rendered docs/47 and
getting zero.

**An infinite reserve army is a word.** `demand_boom` takes `labor_pool=inf`
for the sweep's limiting case. JSON has no infinity, and the first pass
turned it into null, so a run of the unbounded pool was labelled as though
the option had not been set. It is the string `inf` in the document and in
the run's label now; the key was always right, because the key is computed
before the document is.

## 4. What it costs

A run document is 100 to 400 KB for the ordinary scenarios and 6.3 MB for
`capacity_exit`, which is 4,001 days of nine commodities in two regions
and is the one the page marks slow before the button is pressed. A
scenario takes a tenth of a second; the slow one three and a half; the
metric collection twelve. All of it is cached under its key for the life
of the server process and none of it runs on page load.

## 5. What it still does not do

Everything `docs/48` §4 listed, and two things the build made visible:

- **It does not draw a sweep as a curve.** `recreation_sweep` and
  `reserve_army_sweep` are tables. A curve over five points of
  `yayo_per_worker_day` would be honest, and docs/41 §2 is that curve; the
  page has the rows and not the picture.
- **It does not remember runs across a restart**, by the design's own
  choice (§2.4), and the first session made the case for the choice: the
  runs that mattered were remade in under a second each.
