# The laboratory viewer: design

Written before implementation. The laboratory has been reachable only
through the terminal: `python -m economy_lab <scenario>` prints a JSON
summary, `python -m economy_lab.baseline` prints a delta table, and the
sweep's two output files are read raw. Forty-seven documents explain what
the model found and nothing lets a person *watch* a scenario run. This
session builds the thing that does, and only that.

The viewer is an instrument, not a feature of the model. It reads what the
laboratory already computes and draws it. Nothing in it can move a number
the terminal would not also print.

## 1. What it shows

Five things, each on its own page of a single browser window.

**Run.** Pick a scenario, optionally override parameters, run it, and see
the time series: price, inventory, unmet demand, capacity and cost ratio
per region and per commodity; employment, wage rate, wage premium, regional
cash and worker cash per region; reserve remaining and marginal cost where
a region holds one; and the social labor value of every commodity. The
shock day is a vertical rule on every chart. Below the charts, the
end-state summary the terminal prints today.

**Ledgers.** The classical magnitudes for the run, side by side and never
merged. Five panels, one per concept, each carrying its own unit:

| panel | quantity | unit | source |
|---|---|---|---|
| labor value | social value per unit, and each region's individual value | work-ticks | `economy.labor_values`, `regional_labor_values` |
| market price | the current regional price, and its decomposition into inputs, wages, capital consumed and the unattributed margin | silver | `region.prices`, `price_decomposition` |
| price of production | the classical price relative to meals, beside labor value and the authored price in the same ratio; the uniform profit rate; the basics | ratio | `prices_of_production`, `_production_price_report` |
| surplus value | c, v, s in work-ticks; s/v; the realized rate with wages as paid; organic composition; the value rate of profit; per-sector composition; price minus value per unit | work-ticks | the value ledger, `sector_organic_composition`, `price_value_deviation` |
| rent | differential rent accumulated per commodity; the absolute rent bound per day | silver / work-ticks per day | `ledger.differential_rent`, `absolute_rent_bound` |

The money margin lives in the market-price panel under its own name,
`unattributed margin`, with the two surplus readings that name their
assumption (docs/23). It is never placed in the surplus panel. That is
the one rule the layout exists to enforce: **money profit is not surplus
value**, and a viewer that put them in one table would undo what the
ledgers were built to keep apart.

**Compare.** Two runs of the same scenario, as differences. Choose A and
B from the runs already made in this session; every series is drawn as
B − A, and every end-state and ledger figure is a row of A, B, delta,
delta %. Overlays are available as a toggle, but the difference is the
default, because "the meal price rose 4% in one run and not the other" is
a statement about a difference and the eye is poor at reading a 4% gap
between two overlaid lines.

**Metrics.** The 211 frozen metrics against `behavior_baseline.json`. The
reference column loads at once; the current column is collected on a
button, because it takes about twelve seconds, and is cached for the rest
of the session. Beside it, the sensitivity ranking: reach, elasticity and
strongest output per parameter, with a drill-down into every reading the
parameter moved. The sweep itself is **never launched** from the viewer;
it reads the two files the sweep wrote.

**Documents.** Every `docs/NN-*.md`, rendered in the same window. Each
scenario names the design and results documents that introduced it, so a
run is one click from its explanation, and the document list also shows
which other documents mention the scenario.

## 2. How it is structured

```
economy_lab/viewer/
    __init__.py
    __main__.py      python -m economy_lab.viewer [--port N] [--no-browser]
    server.py        http.server handler; the JSON endpoints and the static files
    catalog.py       the scenario registry: function, options, shock day, documents, cost
    runs.py          run a scenario, serialize the Economy to one JSON document, cache it
    markdown.py      Markdown to HTML, standard library only
    static/          index.html, app.js, style.css
```

The server is `http.server.ThreadingHTTPServer` from the standard library
and speaks JSON. The client is one HTML page with hand-written JavaScript
and CSS; the charts are SVG built by the page. No framework and no
charting library, on the standing rule that the laboratory takes no
dependency. That rule was weighed against a charting library once and the
answer is the same as it has always been: the viewer's charts are lines
with a marker on one day, and a library would cost more in build tooling
than it saves in drawing code.

### 2.1 Endpoints

| method | path | returns |
|---|---|---|
| GET | `/api/scenarios` | every scenario: name, description, kind, options with defaults, shock day, cost tier, documents |
| GET | `/api/parameters` | every `ScenarioParameters` field: name, type, default, and the group its source comment puts it in |
| POST | `/api/run` | `{scenario, options, overrides}` → the run document, from cache when the key is known |
| GET | `/api/runs` | the keys and labels of every run made this session |
| GET | `/api/metrics` | the frozen reference |
| POST | `/api/metrics/collect` | the current metrics, collected on demand and cached |
| GET | `/api/sensitivity` | the ranking: reach, elasticity, strongest output per parameter |
| GET | `/api/sensitivity/<parameter>` | every reading the parameter moved, both directions |
| GET | `/api/docs` | number, title, file of every document |
| GET | `/api/docs/<n>` | one document rendered to HTML |

### 2.2 The run document

One JSON object per run, and the same object every time for the same key:

- `key`: the SHA-256 of the canonical JSON of `{scenario, options,
  overrides}`, sorted keys, no whitespace;
- `days`: the recorded day of every snapshot;
- `regions`: per region, per field, per commodity, one array the length
  of `days`; scalar regional fields as one array each;
- `labor_values`: per commodity, one array;
- `shock_day`: from the catalog, or null for the scenarios with no shock;
- `summary`: exactly what `scenarios.summary` returns;
- `ledgers`: the five panels of section 1;
- `elapsed_seconds`: how long the run took, so the page can say so.

The history is read from `Economy.history`, never recomputed. `series()`
refuses a sampled history for good reason (docs/34); the viewer reads
`history` directly and carries each snapshot's own day, so an override of
`history_every` produces a sparser chart rather than a wrong one.

### 2.3 Overrides

An override is a field name and a value. The server rejects a name that is
not a `ScenarioParameters` field, and coerces the value to the field's
annotated type: `int` fields stay integers, `bool` fields accept `true` and
`false`, everything else is a float. That is the same rule the sweep
learned to follow the hard way (docs/45 §1), and the viewer inherits it
rather than repeating the lesson.

Scenario *options* — `bargaining`, `labor_pool`, `route_capacity`,
`loss_fraction` and the others each function exposes — are separate from
parameter overrides and are passed as keyword arguments. A run's key covers
both.

### 2.4 Cost tiers and caching

Every run is cached in memory for the life of the server process under its
key. Runs are made only by an explicit request; nothing runs on page load
except reading the catalog. The catalog marks `capacity_exit` as *slow*
(4,000 days, about three seconds) and the metric collection as *slow*
(about twelve seconds), and the page says so on the button before it is
pressed. The sweep has no button.

The cache is not written to disk. A run costs a tenth of a second and the
slow one three, so a restart loses nothing worth keeping, and a disk cache
would need invalidating whenever the model changed, which is a second
mechanism for a first mechanism that is not needed.

### 2.5 Sweeps

Two scenarios do not return an `Economy`. `recreation_sweep` returns rows
and is shown as a table. `reserve_army_sweep` returns one economy per pool
size; it is shown as a table of the readings docs/47 §2 reports per pool,
and any single pool can be run as `demand_boom` with `labor_pool` set to see
its series.

### 2.6 Documents

The Markdown renderer handles what the forty-seven documents use: ATX
headings, paragraphs, bulleted and numbered lists, fenced code, pipe tables
with alignment, block quotes, horizontal rules, emphasis, inline code and
links. Text of the form `docs/NN` becomes a link to that document inside
the viewer. It does not attempt the rest of CommonMark, and a construct it
does not know is rendered as the text it was written as, which is a
legible failure.

## 3. Determinism

The viewer adds no source of variation. Same scenario, same options, same
overrides: same key, same run, same JSON. The run document is built by
walking sorted dictionaries, and a test asserts that two runs of the same
key serialize to the same bytes. Timing is reported but is not part of the
document's cached body, so the elapsed figure is the only thing that
differs between two runs of the same key and it is not in the comparison.

## 4. What it deliberately does not do

- **It does not change the model.** `python -m economy_lab.baseline` shows
  zero deltas on all 211 metrics after this work, and the 191 tests pass
  unchanged. The viewer imports the laboratory; the laboratory does not
  know the viewer exists.
- **It does not tune.** Overrides live in the request and the cache. There
  is no way to save an override as a new default, write a baseline, or
  edit a parameter file.
- **It does not launch the sweep** or refresh its files.
- **It does not run anything on page load** except the catalog, the
  parameter list and the frozen reference, all of which are reads.
- **It does not merge ledgers.** No panel carries a quantity in two units,
  and no table places a money figure beside a work-tick figure without a
  column that says which is which.
- **It does not persist runs across restarts**, for the reason in §2.4.
- **It does not add a dependency**, on either side of the socket.
- **It does not serve anything outside the repository**, and binds to
  `127.0.0.1` only.

## 5. Done means

A person who has never opened a terminal can be told to run one command,
open one address, choose `demand_boom`, run it with bargaining on and
again with it off, and see on the compare page that the Dust Basin meal
price ends 4.0% higher in one run than the other, with docs/47 §6 one
click away explaining that the difference is demand and not cost.
