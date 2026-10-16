# Can the laboratory demonstrate the law of value? Design

Written before anything is built or run. The question is whether market
prices, set by nothing but supply and demand, come to rest on labour
values: the labour theory of value in its testable form. This document
says why the docked economy cannot answer that, what economy can, and
what it must show.

## 1. Why the docked economy cannot answer it

In the docked economy any agreement between price and value would be put
there by construction:

1. **Its labour values are inputs.** `scale.build_processes` sets each
   commodity's direct labour to whatever makes its embodied labour equal
   the closed analysis's figure for the RimWorld def.
2. **Its costs are its authored prices.** Inputs are sized at 45% of the
   RimWorld market value and total unit cost at two thirds of it. The
   rest is an overhead paid in silver, which is why the production wage
   share is 2 to 4%: cost is mostly not labour.
3. **Its prices are anchored to its authored prices.** The anchored rule
   moves around `reference_price`, the posted rule passes cost through,
   and both clamp between multiples of `reference_price`.

So a price-value comparison there reproduces RimWorld's authoring, which
`FINDINGS.md` already measured: it prices extraction labour three to
fourteen times above fabrication labour.

## 2. What would count as a demonstration

The claim tested is the classical one, in the form Ian Wright tested in
his 2008 simple-commodity model (*The emergence of the law of value in a
dynamic simple commodity economy*), here with produced inputs:

> In a decentralised economy where prices respond only to excess demand
> and producers move toward higher income, labour values are the centre
> of gravity of market prices. Where capital rather than labour moves,
> and moves toward the higher profit rate, the centre is the prices of
> production instead, and they depart from values in the direction the
> composition of capital predicts.

One thing is not a demonstration, and the design must not confuse the
two. If labour is the only non-produced cost and incomes are equal, then
`p = A p + w l`, so `p = w v`. That is accounting, true of any economy
in that state. The substantive claim is **dynamic**: that agents who know
nothing of values, starting from prices that carry no information about
them, find that state and stay near it. So:

- **No price may be computed from a value or a cost.** Prices start
  equal for every good and move only on excess demand.
- **No agent may see a value.** Producers compare incomes, or profit
  rates, with one another, and nothing else.
- **The technique is drawn blind**, from a stream that never sees a
  price.

## 3. The economy: `economy_lab/law_of_value.py`

Self-contained and stdlib-only, with the laboratory's SplitMix64 stream
and its two rules: bit-identical histories under a fixed seed, and money
conserved to floating-point zero. It does not touch `model.py`, so the
baseline cannot move.

### 3.1 The technique

Twelve goods in four depths of three. A depth-0 good needs labour only.
A good at depth `d > 0` draws one to three inputs from shallower depths,
each at a coefficient `U[0.1, 0.5]` units per unit of output. Direct
labour is `U[0.1, 1.0]` worker-days per unit. Values solve `v = l + A v`
exactly, in depth order, because `A` is triangular. Consumers spend on
all twelve goods, with budget shares drawn `U[0.5, 1.5]` and normalised.

### 3.2 The market, common to every arm

Every good has one market each day. Sellers offer all the stock of it
they hold. Buyers send money orders. With `S` units offered, `D` silver
ordered and price `p`, the traded quantity is `T = min(S, D/p)`. Each
buyer receives `T` in proportion to its order, and each seller sells `T`
in proportion to its stock, all at `p`. The price then moves on excess
demand alone:

    e = (D/p − S) / (D/p + S),     p ← p · exp(γ e),     γ = 0.02

Every price starts at 1. Unsold stock is carried. Money moves only
between agents, so it is conserved.

### 3.3 Arm SC: simple commodity production

500 producers, each self-employed in a sector drawn uniformly, each with
100 silver. A producer supplies one worker-day a day. Each day, in this
order:

1. **Produce** `y = min(1/l_s, min_j held_j / A_sj)`, consuming the
   inputs.
2. **Order** the inputs for one full day's output not already held, at
   today's prices, scaled down to the cash if short. Then order
   consumption goods with `σ = 0.1` of the cash left, split by the budget
   shares.
3. **Trade**, then move prices.
4. **Income**: today's sales revenue less today's input spending, kept
   as an exponential average with weight `λ = 0.02`.
5. **Move**: with probability `μ = 0.01`, compare the income average
   with a random other producer's. If the other's is higher, take up
   its sector and its average. Goods already held are kept and still
   sold.

### 3.4 Arm SH: a technical change

The SC arm, except that on day 3,000 the direct labour of the depth-0
good with the largest column sum in `A` (the most-used input) is halved.
Its value falls by half, and every good downstream of it gets cheaper
in labour. Nobody is told.

### 3.5 Arm CAP: capitalist production

500 workers and 100 firms, each firm in a sector drawn uniformly. The
workers hold half the money and the firms half. The wage starts at 1.
Each day:

1. **Order.** A firm plans output `y* = φ · cash / c_s` with
   `c_s = A_s · p + w l_s` and `φ = 0.1`. It orders the inputs that
   output needs and does not hold, and `l_s y*` worker-days.
2. **Hire.** Labour demanded `L` against the 500 offered. Hiring is
   `min(L, 500)`, rationed in proportion to orders, and the wage bill is
   shared equally among the workers. The wage moves on excess demand
   for labour, as prices do.
3. **Trade.** Firms' input orders, workers' consumption (`σ = 0.1` of
   their cash) and the owners' consumption (`δ = 0.02` of each firm's
   cash), then prices move.
4. **Produce** `y = min(hired/l_s, min_j held_j / A_sj)`.
5. **Profit rate**: averages of revenue and of outlay (inputs and
   wages), each with weight `λ`. The rate is their ratio less one.
6. **Move**, as in SC, comparing profit rates rather than incomes.

Labour does not move here. Capital does.

### 3.6 What is measured

Twenty seeds for each of SC, SH and CAP: 6,000 days each, with the last
1,000 days as the window. Over a window, `p̄_i` is the geometric mean
of good `i`'s daily price. Each statistic is computed across the twelve
goods, one point per good, per unit, never per sector total. The
per-unit comparison avoids the spurious correlation that sector size
gives to price and value totals.

- **Dispersion** `Δ(x) = std_i log(p̄_i / x_i)`. It is scale-free, so
  the money level and the wage drop out. On day 0 every price is 1, so
  `Δ(v)` is the spread of the values themselves.
- **Correlation** `ρ(x)`: Pearson correlation of `log p̄` with `log x`.
- **The null**: values `v°` solved from the same input matrix with the
  direct-labour vector permuted across the goods by a seeded shuffle.
  `v°` keeps the depth structure (deep goods still carry more labour),
  so it asks whether prices know the actual technique or only that deep
  goods take more work. It is scored on the SC runs; no extra runs.
- **Prices of production** at the window's aggregate profit rate `r̂`
  (total revenue over total outlay, less one): `p = (1 + r̂)(A p + l)`,
  solved in depth order with the wage as numéraire.
- **Composition** `k_i = (A v)_i / l_i`, dead labour over living, per
  unit. Depth-0 goods have `k = 0`, so the statistic uses
  `log(1 + k_i) = log(v_i / l_i)`. (Amended before any run: the first
  draft wrote `log k`, which is undefined at depth 0.)

## 4. Predictions

Medians over the twenty seeds unless stated.

1. **Money is conserved** on every run: the relative change of total
   money stays below 1e-9 on every day.
2. **Determinism**: two runs of a seed are bit-identical.
3. **SC prices settle on values**: `Δ(v)` in **[0.002, 0.10]**, with no
   seed above 0.20. Below 0.002 would mean the instrument read the
   equilibrium identity, not noisy market prices.
4. **SC prices track values**: `ρ(v) ≥ 0.98`.
5. **The null fails**: `Δ(v°) ≥ 3 Δ(v)`, and `ρ(v°) < ρ(v)` on every
   seed.
6. **The approach takes time**: the first day on which the 100-day
   trailing `Δ(v)` is below half its day-0 value is in **[100, 2,000]**.
   Faster than 100 days would mean the prices are not finding anything
   by trade.
7. **Incomes equalise**: across sectors, the coefficient of variation of
   window income per worker-day is at most **0.15**.
8. **Prices follow a change in value (SH)**:
   - `Δ(v_old)` over days 2,000 to 3,000 is at most 0.10, and `Δ(v_new)`
     over the last window is at most 0.10.
   - In the last window, `Δ(v_old) ≥ 2 Δ(v_new)`.
   - The shocked good's price ratio, after over before, both relative to
     the geometric mean of all prices, is within ±25% of its value
     ratio computed the same way.
9. **CAP earns a profit**: `r̂` per day, on outlay, is in **[0.005,
   0.5]**. Outside that band, prices of production and values are too
   close, or the arm too far from a steady state, to tell apart, and
   predictions 10 and 11 are void rather than failed.
10. **CAP prices settle on prices of production, not values**:
    `Δ(PoP)` at most **0.10**, and `Δ(PoP) < Δ(v)` on at least 16 of 20
    seeds.
11. **CAP deviates from values as the transformation says**: the
    correlation across goods of `log(p̄/v)` with `log(1 + k)` is at least
    **0.5**. Goods with more dead labour per unit of living labour sell
    above their value.
12. **The laboratory's default behaviour is unchanged**:
    `python -m economy_lab.baseline` reports 296 at +0.000%.

## 5. What would make this wrong, and what it would mean

- **3 and 4 pass, 5 fails.** Prices know only that deep goods take more
  work. That is a weak law of value at best.
- **3 fails with 7 passing.** Incomes equalised while prices did not
  reach values. That cannot happen in a steady state (§2's identity), so
  it would mean the window is not a steady state: the market oscillates.
  It would be a statement about this market's stability, not about value.
- **3 fails with 7 failing.** Mobility is too weak or too noisy for
  this market. Raising `μ`, or lowering `γ`, after seeing the results
  would be a second experiment, and it would be reported as one.
- **10 fails while 3 passes.** The capitalist economy does not find
  prices of production. That is the classical claim the arm tests, and
  it would be a substantive negative.

## 6. What a pass would show, and what it would not

A pass shows that in an economy built only from a technique, a market
and mobility, labour values are where prices go. Nobody computes them
and nothing anchors them, and with capital mobile the prices of
production are where they go instead. It reproduces Wright's 2008
result with produced inputs and extends it to the capitalist case.

It does not show that real economies behave this way. It does not
settle any claim that labour is the source of value in a sense beyond
this. And it does not bear on the docked economy, whose prices remain
RimWorld's.
