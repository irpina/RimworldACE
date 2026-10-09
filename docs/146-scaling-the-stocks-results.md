# Scaling the stocks with the economy, and re-docking: results

Scores `docs/145`'s eleven predictions. Seven pass. Three fail on one
of their two parts each, and one fails as stated for a reason outside
both models.

**The fix works.** With the fund, the workers' seed and the labour pool
scaled to the authored demand, the full 647-commodity population builds,
conserves money, and docks on the money circuit, the cost ranking, the
dispersion, the GDP movement and the demise rate. **It does not make
size irrelevant.** At 647 commodities the wage share is set by a
different staple, firm growth is more kurtotic, and more sectors die.

The battery is `economy_lab/battery145_results.json` (twenty seeds each
side, `python3.12 -m economy_lab.redock`). The long runs are
`economy_lab/game_shape145_results.json` (three seeds, 1,800 days).

## 1. The battery at 647 commodities

| # | prediction | measured (median; range) | verdict |
|---|---|---|---|
| 1 | the docked battery at 200 unchanged | builds and runs identically; the run fixture regenerates byte-identical | pass |
| 2 | \|cash_balance\| < 1e-9 M | 8.0e-14 at worst | pass |
| 3 | employing ∈ [1,941, 3,073]; deaths ∈ [129, 647]; fund ∈ [0.03, 0.30] | 2,058 (1,650–2,454); 472 (378–708); 0.105 | pass |
| 4 | GDP growth std ∈ [0.015, 0.08]; kurtosis ∈ [−1.5, 8] | 0.045 (0.027–0.071); 2.32 | pass |
| 5 | cost rank ∈ [−1, −0.6]; sector CV ∈ [0.07, 0.30] | −0.786; 0.152 | pass |
| 6 | `x_min`/largest ∈ [0.1, 0.6]; growth kurtosis ∈ [30, 1000] | 0.162; **1,921** (200–8,967) | half fails |
| 7 | production share ∈ [0.008, 0.02]; total ∈ [0.6, 0.95] | **0.0361** (0.0338–0.0373); 0.830 | half fails |
| 8 | demises ∈ [0.002, 0.02] per firm-month | 0.0088 | pass |
| 9 | the control bit-identical to `docs/139`'s | equal under 3.11; within 4e-13 under 3.12 | fails as stated |
| 10 | unemployment ∈ [0.85, 0.97] | 0.941 | pass |

Against `docs/139` at 200 commodities:

| fact | 200 (`docs/139`) | 647 | ratio |
|---|---|---|---|
| employing | 718 | 2,058 | 2.87 |
| bankruptcies | 127 | 472 | 3.73 |
| fund share at end | 0.105 | 0.105 | 1.00 |
| GDP growth std | 0.061 | 0.045 | 0.74 |
| cost rank | −0.795 | −0.786 | |
| sector CV | 0.146 | 0.152 | |
| production wage share | 0.0198 | 0.0361 | 1.82 |
| with construction | 0.837 | 0.830 | |
| demises per firm-month | 0.0070 | 0.0088 | 1.25 |
| unemployment | 0.937 | 0.941 | |

The producer population is 3.235 times larger. Employing grows a little
less than that, and deaths a little more.

### Prediction 4: GDP moves less, as predicted

The std fell to 0.74 of `docs/139`'s. That is inside the band and in the
predicted direction, but less than the √3.2 fall that independent
sectors would give, so the sectors' fluctuations are partly common.

### Prediction 6: the tail stays absent; growth kurtosis rises

`x_min` over the largest firm is 0.16, so the instrument still finds no
power-law tail, as at 200. Firm-growth excess kurtosis rose from 231 to
a median of 1,921, past the band's 1,000. Excess kurtosis of a pooled,
heavy-tailed sample grows with the sample, and this one pools 3.2 times
as many firms. That explanation is untested: the battery's rows keep the
statistic, not the growth rates, so it cannot be subsampled from them.
Either way, kurtosis was never near Wright's ~3.

### Prediction 7: a different staple sets the wage share

The production wage share is 0.0361 against 0.0198. The cause is the
staple rule, not the size. `synthetic_economy` chooses the cheapest
depth-0 commodity as the basket. The 200-commodity sample's staple is
Meat_Megascarab, and the full population's is Meat_Locust. Both cost 0.5
silver, but the locust embodies 31.8 ticks of labour against 62.2. The
basket quantity is fixed in labour, so it holds twice as many units, and
a worker-day's basket costs 7.55 silver against 3.86, a factor of 1.96.
The wage share rose by 1.82.

`docs/129` §3 already said the wage share is an input here. This
confirms it, and adds that the input depends on which commodity the
generator happens to pick. The share including construction, 0.830, is
unchanged, because construction dominates it.

### Prediction 9: the interpreter, again

Wright's model was not touched, and its runs are identical: the same
firm sizes and fitted exponents. The summary statistics differ in their
last digits, by at most 4e-13 relative, because `docs/139` was computed
under CPython 3.11 and this under 3.12, whose `sum()` is compensated
(`docs/142` §2). Under 3.11, seed 0 reproduces `docs/139` to the bit.

## 2. Five years at 647 commodities

Prediction 11, on the `docs/141` slice-0 instrument: two regions, three
seeds, 1,800 days, against the 200-commodity runs of `docs/142`.

| | 200 commodities | 647 commodities | change |
|---|---|---|---|
| share of producers employing at day 1,080 | 0.473 | 0.362 | **−23.4%** |
| value added a day per region, last year, ÷ scale | 4.31 M | 4.24 M | −1.7% |
| survivors, day 180 to 1,800 | 0.67 to 0.78 | 0.54 to 0.72 | |
| prices at the floor, day 1,800 | 13.5% to 17.3% | 17.0% to 19.9% | |
| largest \|balance\| | 0 | 7.5e-14 | |

**11. Commodity count is neutral: half fails.** Value added per unit of
authored demand is neutral, within 2%. The employing share is 23.4%
lower, just outside the ±20% band, on every seed (17.5% to 27.0%
lower). The economy delivers the same output per unit of demand with a
smaller share of its producers working. The extra deaths are sectors:
more prices sit at the floor, and fewer of day 180's producers survive.

`docs/145` §5 said in advance what this failure means. The full
population carries sectors the battery's sample did not, and they die.
So it is not the same economy at a larger size.

## 3. What this decides

- **The lab keeps `scale_stocks`.** It is the right rule for the stocks.
  It removes the refusal, keeps the money circuit, the cost ranking and
  the GDP figures docked, and costs nothing at 200.
- **The game keeps 200 commodities**, as `docs/145` §5 set out. The
  full population builds and runs, but it is a different economy: a
  different staple and a quarter fewer producers working. Moving the
  game to 647 would be a choice to run that economy. It would also
  triple the daily cost.
- **The staple rule is now a known calibration lever.** A rule that
  picks the staple by its labour content, rather than by its price,
  would make the wage share independent of the sample. That is a
  scenario change for the laboratory, to be designed and docked like
  this one.

## 4. The port

`DockedDay.Build` takes the same scale. The fixtures at 24 and 40
commodities moved with the laboratory, and the 200-commodity battery
fixture regenerated byte-identical. A new run fixture at the full 647
commodities (5,176 producers, 10 days) is built, run, saved after every
phase and run under Mono, all to the bit. Its save is 3.2 MB at two
regions.
