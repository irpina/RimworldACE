# A staple sector that feeds its workers: results

Design in `docs/128`. The 40-run sweep with the fix on is committed as
`economy_lab/battery128_results.json`; `battery126_results.json` is the
same sweep with the spiral running, kept for the comparison below.

## 1. Scoring the predictions

| # | prediction | measured | verdict |
|---|---|---|---|
| 1 | staple price at day 120 ∈ [0.8, 1.25]× day one; index ∈ [−0.1, 0.1] | **0.927×**; +0.079 | pass |
| 2 | fixtures unchanged bar the one-ULP `scale_647_day3`; baseline 322 at zero | as stated; 296 zero + 26 n/a | pass |
| 3 | ≤ 20 iterations at 0.02/0.1/0.2/0.5; capacity = 1.25 × basket demand ± 2% | **5 / 7 / 10 / 20**; see below | pass / mis-specified |
| 4 | 0.2 basket lives: employing ∈ [150, 250], deaths ∈ [0, 40], staple ∈ [0.5, 2.0]× | 216; 10; 0.978× | pass |
| 5 | money share ∈ [0.05, 0.15] / [0.25, 0.50] / [0.40, 0.70] at 0.02 / 0.1 / 0.2 | **0.0146 / 0.077 / 0.159** | **fail ×3** |
| 6 | 0.5 basket loses the spiral but still dies | staple 1.42×, **214 employing, 10 deaths, alive** | **falsified** |

The spiral is gone at every basket, the economy lives at every basket
up to a half of the working day, and the wage share came out *below*
every band. Three notes.

**Prediction 3's headroom clause was mis-specified.** The staple's
capacity serves the input graph's own use of it as well as the
workforce, so "1.25 × basket demand" is not the quantity the generator
computes. Against the quantity it does compute — headroom × (graph use +
the basket of the workforce at that requirement) — the capacity closes
to four decimal places, and `tests/test_money_wage_share.py` now pins
that identity. The iteration count at 0.5 is exactly the bound, 20,
which is the geometric ratio doing what §2 of the design said it would.

**Prediction 5 failed in one direction, by one factor, at every
basket.** Measured against the basket: 0.0146/0.02 = 0.73,
0.077/0.1 = 0.77, 0.159/0.2 = 0.79, and 0.454/0.5 = 0.91. The reason
is in the generator's price table. The staple is *chosen* as the
cheapest shallow commodity, and it is cheap per tick of labour value
too: at the authored prices it sells for **0.00804 silver per tick**
against **0.01057** of value added per tick across the economy, a ratio
of **0.761**. A wage that buys `basket_fraction` of a day in labour
value buys 0.76 of that in money, so the money wage share is 0.76 × the
basket, drifting up toward 1 as the staple sector becomes a larger part
of the economy at high baskets. Prices proportional to values would
make the two shares coincide; the generator's are not, and the money
share reads the deviation.

**Prediction 6 was wrong, pleasantly.** I predicted a wall at 0.5 in
the authored cost share. There is none: the staple's own price carries
the wage, and every other price is high enough. The lab now produces a
money wage share of **0.45** with 214 producers alive, and Wright's
0.55 is reachable at a basket somewhere above 0.6. As an input.

## 2. The battery, with and without the spiral

Twenty seeds, ×200, `basket_fraction = 0.02`, medians. The SA control
column is bit-identical between the two sweeps, as it must be.

| fact | Wright | SA control | ours, fix on | ours, spiral (`docs/127`) |
|---|---|---|---|---|
| **money wage share** | **0.55** | **0.538** | **0.0147** | 0.088 |
| gross wage share | — | 0.538 | 0.0097 | 0.061 |
| GDP growth kurtosis | ~3 | −0.10 | **−0.54** | 6.54 |
| firm growth std | — | 1.05 | 0.20 | 0.29 |
| firm growth kurtosis | ~3 | 4.21 | 93 | 102 |
| demise rate /firm-month | 0.18 | 0.156 | 0.0099 | 0.011 |
| largest firm | — | 751 | 2,757 | 2,249 |
| firm-size α (MLE) | 1.038 (OLS) | 1.278 | 0.52 (x_min 28, range 0.3–2.6) | 1.91 (x_min 425) |
| unemployment | ~0.1 | 0.17 | 0.73 | 0.77 |
| capacity rank ρ | — | — | −0.42 | −0.26 |

**`docs/127`'s money wage share of 0.088 was the spiral**, not the
share: wages were being indexed upward faster than the value added they
were measured against. The GDP "excess kurtosis" of 6.5 was the spiral
too; with a stable nominal it is −0.5, a flat series with no fat tails
because final demand is a constant. Both rows of `docs/127` §2 are
superseded by this table, and `docs/127` says so in place.

The α row remains what `docs/127` called it: uninformative. The MLE's
`x_min` now ranges from 3 to 876 across seeds and the exponent from
0.3 to 2.6, which is the `docs/119` §2 bifurcation on a distribution
that is not a power law.

## 3. What this leaves

- **The scenario reproduces its own labour-power.** That was a
  precondition nobody had checked, and the generator's docstring now
  says why it is off by default.
- **The wage share is an input, and it is now measured as one.**
  `basket_fraction` sets it, the staple's price-to-value ratio scales it
  by 0.76, and the economy lives at any setting tried. This closes
  `docs/125` §4's item 1 and `docs/126` prediction 4 together: there is
  no sense in which our lab *reproduces* 0.55, and a clean sense in
  which it can be *set* to it.
- **Two of Wright's facts are still structurally out of reach**, for
  reasons that are now measured rather than suspected: firm growth
  (employment oscillates on inventory cycles, kurtosis ~90, nothing
  accumulates) and GDP growth (a constant final demand gives a flat
  series). Both need the generator's demand to become endogenous —
  `docs/125` §4's item 2, and the `docs/127` §4 list is otherwise
  unchanged.
- **The investment sink is a non-issue at the shipped basket** (2.2%
  of silver over 180 days at interval 180, 3.8% at 15) and stays a
  scenario choice.

## 4. Method note

`docs/127` §3 diagnosed "a cascade from about day 100" and blamed prices
that never see the basket. The cascade was real and the blame was
adjacent: the price *does* see the basket — it *is* the basket — and
that was the problem. One more day of tracing, with the accounts
printed at fifteen-day intervals, found a sum of purse targets passing
the money supply. The rule this adds is narrow: **when a scenario dies,
print the balance sheet over time before naming the cause.** A
snapshot at the end showed 100% of the silver in purses and said
"hoarding"; the series showed *why*.
