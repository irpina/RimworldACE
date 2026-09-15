# Endogenous demand and accumulation: results

Design in `docs/132`. Three sweeps, all at `k = 4`, `DEMAND = 800`,
thirty months: both rules on (20 seeds), rule one alone (5), rule two
alone (5), committed as `economy_lab/battery132_{both,fund,acc}.json`.

## 1. Two things built differently from the design, and why

**Rule one was rebuilt before the sweep.** As first built it scaled the
authored quantities and kept each good's price elasticity of 0.8. On
one seed, two final goods in short supply (`PsychicEmanator`, capacity
1,000 against a target stock of 4,278) raised their posted prices 16–26×,
and because their own demand was inelastic they drew the fund's fixed
money into themselves: the authored value rose 3.7× while the median
final price *fell* 22%, and every other final good's demand fell to
0.27 of authored. The rule as shipped splits the fund's money by each
good's value share at seeding and buys `share × money / price` — unit
elasticity per good. With that, the scale holds at 0.996 over 180 days
and the scarce good climbs alone (31×) while taking *less* quantity.
`docs/132` §2 carries the amendment.

**Construction is paid to the fund, not to workers.** The design said
workers. Built that way, workers held **33% of the money stock** after
180 days: their basket demand is a quantity per worker-day, so silver
paid to them beyond the basket is never spent, and the sink had only
moved from `investment_spending` to `worker_cash`. The fund is the one
sector with a spending rule, so construction silver goes there. A
worker spending rule would be a third addition and is not made here.

## 2. Scoring the predictions

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | bit-identical off; 867 employing reproduced | 296 zero + 26 n/a; fixtures bar `scale_647_day3`; **867** | pass |
| 2 | \|cash_balance\| < 1e-6 M with both on | **7.8e-14** (5.7e-13 rule one alone) | pass |
| 3 | rule one alone: GDP growth std ∈ [0.03, 0.30]; fund ∈ [0.2, 0.95] of M | **0.0026** (off: 0.019); **0.962** | **fail** / fail |
| 4 | rule two alone: sector CV ∈ [0.2, 3.0]; cost rank ∈ [−1, −0.5] | **0.021**; −0.80 | **fail** / pass |
| 5 | both: growth std ∈ [0.05, 0.5]; kurtosis ∈ [1, 40] | 0.14; **544** | pass / **fail** |
| 6 | both: `x_min` span ∈ [1, 20]; median α ∈ [0.5, 2.5] | **113** (16–1,811); 2.26 | **fail** / pass |
| 7 | both: demise rate ∈ [0.005, 0.10] | 0.0127 | pass |
| 8 | both: wage share ∈ [0.008, 0.02]; with construction ∈ [0.01, 0.05] | 0.0148; **0.735** | pass / **fail** |
| 9 | both: GDP growth kurtosis ∈ [0, 10] | 1.90 (−1.2 to 14.2) | pass, but see §3 |

The rules work as mechanisms — money is conserved to 1e-13, the
cheaper firm is the larger one, wear kills — and every prediction about
what they would *produce* failed, in three specific ways.

## 3. Why, each measured

**Endogenous demand made GDP smoother, not rougher.** The fund holds
96% of the money stock and spends 0.34% of it a day; distributions
arrive at about the same rate; so `rate × cash` is a constant to three
figures and the demand it generates is the authored constant in a
different notation. GDP growth std fell from 0.019 to 0.0026 because
rule one also removed the 0.8 price elasticity that had let quantities
wobble. Wright's E1 spends a uniform share of holdings *per activation*
— half of what an actor holds, on average, every month — against a
money stock of a hundred coins an actor. Ours turns the fund over in
three hundred days. The rule is right and the **money stock is ten
times too large against the flow**, a battery calibration inherited
from `docs/124` §3, where it was chosen to survive payroll before rule
one existed. Prediction 9's pass is the kurtosis of a series with a
body of ±0.01 and means nothing.

**Accumulation is proportional growth at equal rates.** Within a
sector every firm faces one posted price (`docs/131`), so margins
differ only by the overhead spread — about 3% of unit cost — and so do
growth rates. Sector CV rose from 0.0000 to 0.021 in thirty months,
which is 3% drift differences compounding, exactly. Gibrat needs
heterogeneous rates or noise; ours has 3% of the former and, by the
lab's founding principle, none of the latter. Meanwhile total capacity
grows 2.6× against a demand that does not, utilisation falls, wear
(∝ capacity) outruns margin, and firms die by attrition: 178 of 1,000
per run, employment down to 594, unemployment 0.80. **The lab's first
endogenous crisis is an over-accumulation crisis**, which is not
nothing, but it is not a firm-size distribution — the growth series it
leaves is on/off attrition (kurtosis 544) and the size fit bifurcates
as before.

**Construction is 73% of value added.** Retained earnings are half of
an excess that is 87% of daily outlay, plus wear at 15% of outlay,
against a construction unit of sixty days' cost per unit of daily
capacity. Every one of those numbers is a scenario parameter
(`retention_rate`, `COST_SHARE_OF_PRICE`, `construction_cost_multiplier`,
`capital_service_life_days`) and none was chosen for this. The
production wage share kept its basis at 0.0148, as predicted; the
total is dominated by a construction sector the scenario never sized.

## 4. What this leaves

The two rules exist, are gated, conserve money and pass their unit
tests. What the sweeps say is that the *parameters around them* were
all chosen for other purposes: the money stock for payroll survival,
the cost spread for a distinctness test, the construction unit and
service life for Department I on a six-commodity scenario. Three
parameter questions, each a sweep and not a rule:

1. **Money stock against flow.** `CASH_MULTIPLIER` down from 10 with
   rule one on, until either GDP moves or payroll fails; rule one may
   itself be what makes a smaller stock survivable, since the fund
   now spends what it receives.
2. **Cost spread.** `cost_spread` up from 0.1 with rule two on. If
   sector CV rises with it and keeps rising over time, the lab has
   Gibrat with heterogeneous drift, and the tail question becomes
   askable without noise.
3. **Construction against margin.** `retention_rate` and the
   construction unit set so that construction is a plausible share of
   value added, and the over-accumulation crisis either stays or goes.

None of these changes the model. `docs/134` is the design for all
three, with the standing question — whether a deterministic lab can
produce Wright's tail at all, or whether his lottery is load-bearing —
stated as a prediction rather than a suspicion.

## 5. Method note

Nine predictions, five of them about rates and spreads whose values
were sitting in the scenario file. Prediction 3 failed because
`CASH_MULTIPLIER` was ten; prediction 8 because
`construction_cost_multiplier` was sixty. Both were greppable. The rule
from `docs/131` §3 — check each prediction against the design's own
choices — extends to the *inherited* choices: **before predicting what
a rule does, read the parameters it will multiply.**
