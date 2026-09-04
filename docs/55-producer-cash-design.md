# Producer-level cash: design

Written before implementation. This is the first of the three impositions
that stand between the laboratory and a dynamically complete economy in
Tesfatsion's sense (the ACE Trading World exercise): a model in which
production, pricing and trade are driven by the agents inside it, with no
market-clearing or coordinating condition imposed from outside. The
handoff has carried "individual producer cash accounts" as an omission
since `docs/17`, `docs/43` named it as the blocker for rent as a flow, and
`docs/50` §5 put it on Phase D's critical path. This is that item.

## 1. What silver does today

Every region is one purse. `Region.cash` pays the wage bill, receives the
workers' basket spending, pays for new capacity, and settles imports;
`Region.worker_cash` is the workers' purse. That is the whole monetary
circuit, and three things follow from it that a firm-level economy cannot
have:

- **Nobody pays for inputs.** A drug lab draws psychoid leaves from the
  regional stock and no silver moves, because the buyer and the seller are
  the same purse.
- **Nobody pays for final consumption.** `_consume` removes yayo from
  stock and moves no silver at all. Yayo producers have never been paid.
- **Nobody can fail.** A producer's "cash" is a field on `Producer` that
  nothing has ever read. A sector that sells below its cash cost, which
  `docs/37` §6 found components do, runs on regardless; the only
  discipline it faces is the maintenance rule of `docs/38`, which is a
  margin test on a notional margin, not a purse running dry.

The money profit the ledgers report — the unattributed margin, the two
surplus readings — is therefore a per-unit *notional*, never a flow into
anyone's hands. `docs/23` said as much. What this design changes is that
it becomes a flow.

## 2. The rule

Off by default (`producer_cash = False`), bit-identical off. On:

**Each producer holds silver.** `Producer.cash`, seeded at a **working
capital target**: `working_capital_days` of its full-capacity daily outlay
at seeded prices. The seed comes out of the region's `initial_cash`, so
the economy's silver is what it was; the region keeps the rest as the
**owners' fund**, which is what `Region.cash` becomes.

**A producer pays for what it uses, from its own purse, before it runs.**
Its daily outlay is inputs at the region's prices, plant-replacement
matter at the region's prices, and wages. If the purse cannot cover the
planned runs, the runs are scaled to what it can — a *liquidity ration*,
applied in the same pass and the same proportional form as the reserve
and labor rations, and booked as `liquidity_curtailment` in runs. A
producer that can afford nothing makes nothing.

**A sale pays the sellers.** The region's stock stays a pool, because
producer-level inventory is the procurement slice (`docs/59`) and not this
one; what changes is who the pool's revenue belongs to. Every sale out of
the pool — final consumption, an input draw, a basket purchase, an
export, a construction bill — is paid at the region's price, and the
payment is divided among the commodity's producers in proportion to
their **supply shares**: their share of the sector's realized output,
which is exactly the share the order book of `docs/21` gave them. Where a
commodity has no producer in the region (an import), the pool's owner is
the fund, and the fund is paid.

**Who pays.** Inputs and plant matter: the drawing producer. Wages: the
producer, in proportion to the labor it performed, so the wage bill is
what it was and is merely split. The basket: workers, as today. Final
consumption: the **owners' fund** — the households of the class that
owns the producers, spending what the producers distribute. Imports and
new capacity: the fund, as today.

**Profit is distributed.** At the end of each day a producer whose purse
exceeds its working capital target hands the excess to the fund; one
below it keeps everything. The target is recomputed daily from current
prices, so a producer facing dearer inputs retains more. The fund is
where realized money profit goes, and it is the fund that buys the final
good: the circuit's realization closes through the owners' consumption,
which is where Marx closes it too.

**A producer that cannot pay for long enough fails.** A producer that
could afford no runs on `bankruptcy_idle_days` consecutive days on which
it had runs planned is removed: its capacity is booked to
`capacity_lost`, its residual silver to the fund, and the event to a
`bankruptcies` list. No credit, no rescue.

**New capacity is capitalised.** An entrant completing a project receives
its working capital target from the fund, or what the fund has if that is
less.

## 3. What stays exactly stationary, and why

At the seeded equilibrium every producer runs at the same rate every day,
so its outlay and its revenue are the same floats every day. Its purse
opens at its target `T`, closes at `T − O + R`, and the distribution rule
does not subtract the excess; it *sets* the purse to `T`. So a profitable
producer's cash is `T` on every day to the bit, and the fund receives
`R − O` on every day to the bit. The fund pays `F` for final consumption
and receives `Σ(R − O)`; those two are within floating-point noise of each
other in the seeded circuit (revenue is inputs plus wages plus final
sales, and the workers spend the wages on the basket), so the fund drifts
by an amount the design predicts below rather than by a growing amount.
Prices see none of this, because nothing in `_update_prices` reads a
purse. **The equilibrium's price range stays exactly zero with the rule
on**, which is the test.

A *loss-making* producer's purse falls by `O − R` a day until the
liquidity ration bites, and from then on it makes what yesterday's
revenue pays for. That is the rule doing its job: `docs/39` found that a
sector selling below cost is disciplined rather than deleted, on a
2,200-day maintenance clock. This is the same discipline on a
five-day clock.

## 4. Where it does not reach

- **Not into prices, directly.** The anchor is still the authored price
  moved by the cost ratio (`docs/21`); a purse's state changes what is
  produced, and only through that what the price does. Firm-posted
  prices are `docs/57`.
- **Not into inventory ownership.** The pool is a consignment and the
  supply share is the rule for who is paid. An import sold from the pool
  pays the fund; a local producer's unit sold the day after an import
  arrived pays the local producer. Both are approximations that
  producer-level inventory would remove, and `docs/59` will.
- **Not into the value ledger.** Silver is silver; `c`, `v` and `s` are
  work-ticks and are untouched. The money profit that now flows is
  reported beside them, in its own unit, and never added.
- **Not into the wedge.** The unattributed margin is not a cash outlay,
  because the model does not know what it is (`docs/24`). A producer's
  cash cost is inputs, plant matter and wages, and the wedge is what its
  price carries above them. This is the first time the wedge is a flow:
  it is what gets distributed.
- **Not into workers' or the fund's failure.** The fund cannot go
  bankrupt; final consumption is scaled to what it holds, as imports
  already are. Workers already are cash-constrained (`docs/17`).

## 5. Scenarios

**`equilibrium(producer_cash=True)`** via a parameter, for stationarity.

**`cash_circuit`**: Department I with producer cash. `docs/37` §6 found
the component sector loses 6.12 silver on a 32-silver product once the
power stylization is applied; with a purse, that loss is a draining
purse. This is the scenario that says what the rule does to a sector
that does not pay.

**`demand_boom(producer_cash=True)`** via the parameter: investment is
now funded by a fund that the producers fill, and the boom's employment
path should survive that.

New parameters: `producer_cash` (False), `working_capital_days` (5.0),
`bankruptcy_idle_days` (30).

## 6. Predictions

6.1 **Bit-identical off.** All 231 frozen metrics unchanged.

6.2 **Exactly stationary on.** Equilibrium price range `0.0` over 240
days with `producer_cash = True`; every producer's purse equal to its
target on every day after the first, to the bit; the fund's total drift
over the run under **1 silver** on an initial 100,000.

6.3 **Nobody is liquidity-rationed in the six-commodity equilibrium**:
`liquidity_curtailment` is exactly zero, because every seeded sector's
price covers its cash cost.

6.4 **Components are rationed, not bankrupted.** In `cash_circuit` the
component purse drains to zero within **20 days**, output falls, the
price rises on the shortfall, and a rest point is reached where
yesterday's revenue funds today's runs: component capacity utilization
between **0.3 and 0.8** at the end, price between **1.1× and 1.5×** the
authored 32, no bankruptcy. The `docs/39` rest point, reached in days
rather than years, because a purse is a faster signal than plant wear.

6.5 **The rest of Department I is untouched.** No other sector's purse
falls below target on any day, and no other sector is rationed.

6.6 **The boom is funded.** With producer cash on, `demand_boom`'s
employment on day 360 is within **2%** of the run without it, and the
fund never falls below the construction bill it is asked to pay.

6.7 **Money profit is a flow that matches the notional.** In the
equilibrium, the daily distribution per sector equals the sector's output
times its price less its inputs and wages per unit — the price
decomposition's `surplus_if_margin_is_surplus` plus `capital_consumed`,
because a bill-free process pays nothing in cash for the plant the ledger
charges it for — to within **1e-6** silver, on every day. In Department
I, where plant is bought as matter, the distribution matches
`surplus_if_margin_is_surplus` itself. The notional the ledgers have
printed since `docs/23` becomes a flow without changing its number.

6.8 **Silver conserves.** `cash_balance` at floating-point zero with
producer purses inside the identity, in every scenario.

## 7. What would make this wrong

If 6.2's price range is not exactly zero the rule has reached a price
through a path §4 says it does not, and the right response is to find the
path, not to loosen the check. If 6.4 ends in bankruptcy the price
response is slower than the purse's drain and the design's claim about
discipline is wrong for this sector. If 6.7 fails by more than noise, the
supply-share rule is paying someone other than the seller.

## 8. Non-goals

No credit. No interest. No producer-level inventory. No firm-posted
prices. No rent as a flow yet — the purse exists now, and `docs/43`'s
landlord can be paid from it in a later slice. No re-run of the sweep.
