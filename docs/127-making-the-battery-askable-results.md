# Making the battery askable: results

Design in `docs/126`. Everything measured here is reproducible from
`economy_lab/wright_battery.py` at `DEMAND = 200`; the 40-run sweep is
committed as `economy_lab/battery126_results.json`.

## 1. Scoring the predictions

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | employing producers ∈ [300, 400] at ×200; bankruptcies ∈ [0, 40] | **216**; 10 | **fail** / pass |
| 2 | quantum off differs by < 10% | 250 vs 216 = **13.6%** | **fail**, narrowly |
| 3 | money wage share ∈ [0.01, 0.10]; gross smaller | median **0.088** (0.011–0.106); gross 0.061 | pass |
| 4 | basket 0.5 → share ∈ [0.30, 0.80] | payroll fails day 79 | not scored; see §3 |
| 5 | growth std ∈ [0, 0.05] | **0.291** (0.12–1.08) | **fail** |
| 6 | 322 metrics at zero delta; suite passes | 296 zero + 26 n/a; 287 OK | pass |

Two passes, three failures, one unscorable. The failures are the
informative part.

### Prediction 1 failed against the record, again

The band was written against 400 producers. **150 of them have a capacity
of 1e-6**: `synthetic_economy` builds a producer for every commodity in
the population but only those in the deep commodities' requirement
cascade get any. `docs/124` §5 had already noted *"400 producers carry
only 101 distinct capacity values"*, which was the clue. The viable
population is **250**, and 216 of 250 employing is 86%, against 14 of
250 before. So the rescale did what §1 of the design said it would; the
prediction was scored against a denominator I had not checked. That is
`docs/125` §5's rule, broken a third time, on the very next document.

Over the full 30-month window the population goes on eroding: seed 3
ends at 154 employing with 42 deaths; the pooled demise rate is
**0.011 per firm-month** (was 1.861; Wright's is 0.156).

### Prediction 2: it was the quantum, but not only

With the quantum off there are **zero** bankruptcies and all 250 viable
producers employ. With it on, 34 fail — 13.6%, not under 10%. Measured
at design time, 26 of the 250 cannot reach one whole worker even at
×200 (their full-capacity employment is under 1), and a further eight
are marginal. The mechanism in `docs/126` §1 is confirmed — the quantum
is what kills, the budget does not — but the band was too tight because
the ×200 figure was chosen from the *median* producer, not the tail.

### Prediction 5: employment moves a lot, and it is not growth

I predicted producers would barely move because they meet authored
demand. The log-employment growth series has standard deviation
**0.29** and excess kurtosis **102** (Wright's is ~3). Only 1.4% of the
observations are exactly zero, so this is not intermittent production;
producers' month-to-month employment genuinely swings by ~30% on
inventory cycles. That is not firm growth in Wright's sense (nothing is
accumulating), and the kurtosis row is *still* not scoreable — but for
the opposite reason to the one predicted.

## 2. The battery, both models, 20 seeds each

| fact | Wright reports | SA control | ours at ×200 | ours (`docs/125`) |
|---|---|---|---|---|
| size observations | — | 21,653 | 3,849 | 73 |
| firm-size α (MLE) | 1.038 (OLS) | 1.278 | 1.914 (x_min 425) | n/a |
| largest firm | — | 751 | 2,249 | 6 |
| growth kurtosis | ~3 | 4.21 | 102 | n/a |
| GDP growth kurtosis | ~3 | −0.10 | 6.54 | — |
| demise rate /firm-month | 0.18 | 0.156 | 0.011 | 1.861 |
| **money wage share** | **0.55** | **0.538** | **0.088** | not measured |
| value wage share | — | — | 0.0200 | 0.0200 |
| unemployment | ~0.1 | 0.17 | 0.77 | 0.98 |
| capacity rank ρ | — | — | −0.26 | −0.40 |

The α row is now *a number* rather than unavailable, but with x_min at
425 on a largest firm of 2,249 it is fitted to a fraction of a decade
and should be read as `docs/119` §2 reads such fits: uninformative. The
unemployment row is a scenario artefact — the pool-to-demand ratio was
carried over from `docs/124`, whose pool was already 2.5× full-capacity
employment.

**The wage share row is now a comparison.** Same instrument, same
basis (wages over value added), and the control lands on Wright's 0.55
while ours lands on 0.088. That is the like-for-like `docs/125` §4 asked
for, and §3 says what the gap is.

## 3. The wage share is an input here and an outcome there

The design's substantive claim was that our wage share is *authored*
by `basket_fraction`. Turning the parameter:

| `basket_fraction` | money wage share | outcome at day 180 |
|---|---|---|
| 0.02 (shipped) | 0.088 | 216 employing, 10 deaths |
| 0.1 | 0.366 | 191 employing, 17 deaths, fund at 0 |
| 0.2 | 0.541 | **0 employing, 167 deaths** — cascade from ~day 100 |
| 0.5 | 0.742 to day 79 | payroll fails; with fund ×100, collapses anyway |

The share tracks the parameter — 0.088, 0.366, 0.541 — and reaches
Wright's 0.55 at a basket of 0.2. **And at that basket the economy
dies.** The generator's prices are authored by `population()` with a
fixed cost share and never see the basket, so a wage of a fifth of the
day's product is not covered by the posted price; the fund tops up
purses until it is empty, then producers stop, and because there is one
producer per commodity per region every stoppage starves everyone
downstream through Liebig rationing. The 0.5 basket does the same
faster, and a hundredfold richer fund only changes the date.

So prediction 4's *band* is not scored, but its *substance* is settled
in the direction the design said: our lab produces whatever wage share
it is told to, up to the point where the told share exceeds what the
authored prices can pay. In Wright's model 0.55 falls out of nine rules
about actors and money. In ours it is `basket_fraction`, and the model
has no mechanism by which prices would rise to accommodate it.

## 4. What this leaves

- **The battery is now askable, partly.** Firm size, demises and a
  like-for-like wage share have readings. Growth and GDP kurtosis have
  numbers that mean something other than what Wright's mean.
- **Three scenario facts block the rest**, all previously suspected and
  now measured: one producer per commodity (a death is a supply break);
  prices that do not respond to the wage (a high basket is fatal); and a
  demand that is a constant (GDP kurtosis is inventory noise). The first
  is `docs/125` §4's item 2, the other two are new and both point at the
  same place — the generator authors prices *and* wages *and* demand, and
  a model whose three big ratios are all inputs cannot be asked whether
  it reproduces them.
- **The fund drains at any basket above 0.02.** That is the
  investment/payroll interaction `docs/125` §6 sidestepped with
  `investment_interval_days = 180`, seen from the other side, and it is
  next.

## 5. Method note

Prediction 1 failed because I did not count the producers before
predicting how many would survive. `docs/125` §5 stated the rule the
day before. The rule is right; it needs to be applied to *denominators*
and not only to targets.
