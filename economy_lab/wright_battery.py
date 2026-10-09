"""Wright's measures, run over our model with his model as the control.

Design in ``docs/124``, results in ``docs/125``.

    python -m economy_lab.wright_battery out.json 20

The point of this module is that :func:`facts` is the **only** place the
distributions are fitted, and both models feed it the same record shape.
A difference between them therefore cannot be a difference in measurement
code, which is the one confound that would make the comparison worthless.

``docs/124`` §2 records what cannot be measured: our model has no
individuals, so Wright's income distribution is not attempted.
"""

import json
import math
import statistics as st
import sys
from multiprocessing import Pool

from economy_lab import distributions as D
from economy_lab import social_architecture as sa
from economy_lab.model import Economy
from economy_lab.scale import population, synthetic_economy

MONTH = 30
BURN_IN_MONTHS = 6
WINDOW_MONTHS = 24

#: docs/124 §3, each justified there by a measurement made at design time.
COMMODITIES = 200
REGIONS = 2
#: docs/126 §1: final demand per deep commodity.  At the generator's
#: shipped 1.0 the median producer needs 0.019 of a worker, and the
#: one-worker quantum floors 326 of 400 producers to nothing on day one.
#: At 200 the median needs ~3.7 whole workers.  Silver endowments and the
#: labour pool scale with it -- money is nominal, and the pool-to-demand
#: ratio is what docs/124 §3 chose.
DEMAND = 200.0
LABOR_POOL_PER_DEMAND = 400.0
CASH_MULTIPLIER = 10.0
PURSE_FLOOR_PER_DEMAND = 50.0
BASKET_FRACTION = 0.02
#: Investment is slowed almost to a stop.  Measured during design: at the
#: shipped 15-day interval the regions spend 15.7M silver on construction
#: and cannot make payroll by day ~250.  Cash is *conserved* throughout
#: (``cash_balance`` is 0 to 1e-8) -- the silver goes to capacity, it does
#: not leak.  Wright's model has no investment at all, so slowing ours
#: makes the comparison more like-for-like rather than less.
INVESTMENT_INTERVAL = 180


def facts(record):
    """Every fitted number, for either model. The shared instrument."""
    sizes = [int(round(v)) for v in record["firm_sizes"] if v >= 1]
    growth = record["firm_growth"]
    gdp = record["gdp"]
    history = sa.History(gdp=gdp)
    gdp_growth = history.gdp_growth()
    mle = D.power_law_fit(sizes, discrete=True, min_tail=200) if len(sizes) > 200 else None
    ols = D.ols_histogram_fit(sizes) if len(sizes) > 20 else None
    return {
        "firms": len(set(record.get("firm_ids", []))) or None,
        "size_n": len(sizes),
        "size_alpha_mle": mle.get("alpha_wright") if mle else None,
        "size_x_min": mle.get("x_min") if mle else None,
        "size_alpha_ols": ols.get("alpha_wright") if ols else None,
        "largest": max(sizes) if sizes else 0,
        "growth_kurtosis": D.excess_kurtosis(growth) if len(growth) > 3 else None,
        "gdp_kurtosis": D.excess_kurtosis(gdp_growth) if len(gdp_growth) > 3 else None,
        "demise_rate": record["demise_rate"],
        "wage_share": st.mean(record["wage_shares"]) if record["wage_shares"] else None,
        # docs/126 §2: wages over value added, Wright's basis.  For the
        # SA model this is the same series as ``wage_share``.
        "money_wage_share": (st.mean(record["money_wage_shares"])
                             if record.get("money_wage_shares") else None),
        "gross_wage_share": (st.mean(record["gross_wage_shares"])
                             if record.get("gross_wage_shares") else None),
        "growth_std": st.pstdev(growth) if len(growth) > 1 else None,
        "gdp_growth_std": st.pstdev(gdp_growth) if len(gdp_growth) > 1 else None,
        "total_wage_share": (st.mean(record["total_wage_shares"])
                             if record.get("total_wage_shares") else None),
        "profit_skew": (D.skewness(record["profit_rates"])
                        if len(record["profit_rates"]) > 3 else None),
        "unemployment": record.get("unemployment"),
    }


def _growth(previous, current):
    """Log growth for firms present in both periods, as Wright measures it."""
    out = []
    for key, now in current.items():
        then = previous.get(key)
        if then and then > 0 and now > 0:
            out.append(math.log(now / then))
    return out


def measure_sa(seed, beta=1.0):
    """The control: Wright's own model, through the same instrument."""
    economy = sa.Economy(seed=seed, market_rule="scaled", size_exponent=beta)
    economy.run(120)
    economy.start_recording()
    economy.run(180)
    history = economy.history
    return {
        "model": "social_architecture",
        "seed": seed,
        "firm_sizes": [float(v) for v in history.firm_sizes],
        "firm_growth": history.firm_growth,
        "gdp": history.gdp,
        "demise_rate": st.mean(history.demises_per_month) / max(1, len(economy.firm_sizes())),
        "wage_shares": history.wage_shares,
        "money_wage_shares": history.wage_shares,
        "gross_wage_shares": history.wage_shares,
        "profit_rates": history.profit_rates,
        "unemployment": economy.unemployment_rate(),
    }


#: The size at which the docking calibrated the money stock against the
#: flow (docs/137, docs/138): the battery's 200 commodities.  With
#: ``scale_stocks`` the fund, the workers' seed and the labour pool keep
#: that calibration's ratio to the authored final demand at any size
#: (docs/145).
FUND_BASIS_COMMODITIES = 200


def authored_value(commodities, demand):
    """The authored final demand's value a day at reference prices: each
    deepest commodity's demand times its price, summed in population order,
    exactly as ``build_ours`` reads it off the first region."""
    rows = population(commodities)
    deepest = max(row["depth"] for row in rows)
    return sum(demand * row["price"] for row in rows if row["depth"] == deepest)


def build_ours(seed, *, demand=DEMAND, basket_fraction=BASKET_FRACTION,
               quantum=1.0, basket_in_demand=True, producers_per_commodity=1,
               fund_spending=False, accumulate=False, retention_rate=0.5,
               cash_multiplier=CASH_MULTIPLIER, cost_spread=0.1,
               construction_cost_multiplier=60.0, investment=True,
               commodities=COMMODITIES, regions=REGIONS, scale_stocks=False):
    """Our laboratory at a size where a distribution exists (docs/124 §3),
    rescaled so that most producers can employ a whole worker (docs/126),
    with the staple sector sized to feed that workforce (docs/128).

    The knobs are the designs' experiments: ``demand`` is docs/126
    prediction 1, ``quantum`` its prediction 2, ``basket_fraction`` its 3
    and 4; ``basket_in_demand=False`` reproduces docs/127's spiral.

    ``scale_stocks`` (docs/145) multiplies the fund, the workers' seed and
    the labour pool by the authored final demand's value against the
    battery's, so the stocks keep the ratio to the flow the docking
    calibrated at any number of commodities.  The factor is exactly one at
    200.
    """
    base = synthetic_economy(commodities=commodities, regions=regions,
                             daily_demand=demand, basket_fraction=basket_fraction,
                             basket_in_demand=basket_in_demand,
                             producers_per_commodity=producers_per_commodity,
                             cost_spread=cost_spread,
                             record_history=False, seed=seed)
    regions = list(base.regions.values())
    scale = 1.0
    if scale_stocks:
        first = regions[0]
        scale = (sum(amount * first.prices[name]
                     for name, amount in first.base_daily_demand.items())
                 / authored_value(FUND_BASIS_COMMODITIES, demand))
    for region in regions:
        region.labor_pool = LABOR_POOL_PER_DEMAND * demand * scale
        region.cash *= cash_multiplier * demand * scale
        # docs/137 §2: the workers' seed scales with the fund's, so that
        # a smaller fund does not leave a quarter of the money stock in
        # a purse that only ever buys the basket.  At the shipped
        # multiplier the factor is exactly one.
        region.worker_cash *= demand * (cash_multiplier / CASH_MULTIPLIER) * scale
        for producer in region.producers:
            producer.cash = max(producer.cash, PURSE_FLOOR_PER_DEMAND * demand)
    economy = Economy(
        list(base.commodities.values()), regions, base.routes,
        record_history=False,
        producer_cash=True,
        posted_prices=True,
        producer_employment_quantum=quantum,
        # docs/137 §2: with the fund small, an investment event scales to
        # the fund and empties it; Wright's model has no investment.
        investment_interval_days=INVESTMENT_INTERVAL if investment else 10 ** 6,
        accumulate=accumulate,
        retention_rate=retention_rate,
        construction_cost_multiplier=construction_cost_multiplier,
    )
    if fund_spending:
        # docs/132 §2: seeded so that day one's demand is the authored
        # one -- from the fund as it stands *after* the purses were seeded
        # out of it, which is the silver the rule will read.
        first = regions[0]
        authored = sum(base * first.prices[name]
                       for name, base in first.base_daily_demand.items())
        if first.cash <= 0.0:
            # Seeding the purses took the whole fund (docs/135 sweep A):
            # a refusal of the same kind as a payroll it cannot cover.
            raise RuntimeError(
                f"region {first.name!r} has no silver left after seeding purses"
            )
        economy.fund_spending_rate = authored / first.cash
    return economy


#: The configuration docked with Wright in docs/138 and carried into the
#: game by docs/141 §2: ``build_ours(seed, **DOCKED)``.
DOCKED = dict(
    demand=800.0,
    basket_in_demand=True,
    producers_per_commodity=4,
    cost_spread=1.0,
    fund_spending=True,
    cash_multiplier=0.3,
    accumulate=True,
    retention_rate=0.5,
    construction_cost_multiplier=20.0,
    quantum=1.0,
    investment=False,
    scale_stocks=True,
)


def employment(economy):
    """Whole workers employed by each producer, Wright's firm-size measure."""
    out = {}
    for region in economy.regions.values():
        for producer in region.producers:
            if not producer.active or producer.process is None:
                continue
            labor = producer.process.direct_labor
            if labor <= 0.0:
                continue
            workers = producer.last_runs * labor / region.ticks_per_worker_day
            if workers > 0.0:
                out[(region.name, producer.name)] = workers
    return out


def money_totals(economy):
    """Wages paid, sales receipts, producer purchases and construction
    wages, all silver."""
    ledger = economy.ledger
    return (sum(ledger.wages_paid.values()),
            sum(ledger.sales_receipts.values()),
            sum(ledger.producer_purchases.values()),
            sum(ledger.construction_wages.values()))


def measure_ours(seed, **knobs):
    """Our model, through the identical instrument.  A run the model
    refuses (payroll it cannot cover) is returned as a record with
    ``error`` set and nothing else, so a sweep can score the refusal."""
    try:
        economy = build_ours(seed, **knobs)
        economy.step(MONTH * BURN_IN_MONTHS)
    except RuntimeError as failure:
        return {"model": "ours", "seed": seed, "error": str(failure),
                "day": getattr(economy, "day", 0) if "economy" in locals() else 0}

    def totals():
        living = sum(economy.ledger.living_labor.values())
        necessary = sum(economy.ledger.necessary_labor.values())
        value = sum(economy.ledger.value_produced.values())
        return living, necessary, value

    sizes, growth, gdp, shares, profits = [], [], [], [], []
    money_shares, gross_shares, total_shares = [], [], []
    previous_sizes = employment(economy)
    last_living, last_necessary, last_value = totals()
    last_wages, last_receipts, last_purchases, last_construction = money_totals(economy)
    money_stock = economy.ledger.initial_cash
    deaths_at_start = len(economy.ledger.bankruptcies)
    active_seen = []

    for _ in range(WINDOW_MONTHS):
        try:
            economy.step(MONTH)
        except RuntimeError as failure:
            return {"model": "ours", "seed": seed, "error": str(failure), "day": economy.day}
        current = employment(economy)
        sizes.extend(current.values())
        growth.extend(_growth(previous_sizes, current))
        previous_sizes = current
        living, necessary, value = totals()
        gdp.append(value - last_value)
        if living - last_living > 0:
            shares.append((necessary - last_necessary) / (living - last_living))
        last_living, last_necessary, last_value = living, necessary, value
        wages, receipts, purchases, construction = money_totals(economy)
        d_wages, d_receipts = wages - last_wages, receipts - last_receipts
        d_added = d_receipts - (purchases - last_purchases)
        if d_added > 0:
            money_shares.append(d_wages / d_added)
            total_shares.append((d_wages + construction - last_construction) / d_added)
        if d_receipts > 0:
            gross_shares.append(d_wages / d_receipts)
        last_wages, last_receipts, last_purchases, last_construction = (
            wages, receipts, purchases, construction)
        rate = economy.value_rate_of_profit()
        if rate is not None:
            profits.append(rate)
        active_seen.append(len(current))

    deaths = len(economy.ledger.bankruptcies) - deaths_at_start
    mean_active = st.mean(active_seen) if active_seen else 1
    employed = sum(previous_sizes.values())
    return {
        "model": "ours",
        "seed": seed,
        "firm_sizes": list(sizes),
        "firm_growth": growth,
        "gdp": gdp,
        "demise_rate": (deaths / WINDOW_MONTHS) / max(1.0, mean_active),
        "wage_shares": shares,
        "money_wage_shares": money_shares,
        "gross_wage_shares": gross_shares,
        "total_wage_shares": total_shares,
        "profit_rates": profits,
        # docs/132 predictions 2 and 3.
        "cash_balance": economy.cash_balance() / money_stock,
        "fund_share": sum(r.cash for r in economy.regions.values()) / money_stock,
        # The pool the economy has, not the default one (docs/145).
        "unemployment": max(0.0, 1.0 - employed / sum(r.labor_pool for r in economy.regions.values())),
        "capacity_rank": capacity_correlation(economy, previous_sizes),
        "employing": len(previous_sizes),
        "bankruptcies": deaths,
        **sector_structure(economy, previous_sizes),
    }


def _spearman(pairs):
    if len(pairs) < 10:
        return None

    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, index in enumerate(order):
            out[index] = float(rank)
        return out

    a = ranks([p[0] for p in pairs])
    b = ranks([p[1] for p in pairs])
    n = len(a)
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    var_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    return cov / (var_a * var_b) if var_a and var_b else None


def sector_structure(economy, sizes):
    """docs/130 §2: what competition did *within* sectors.

    ``cost_rank``: Spearman rho, pooled over sectors with at least two
    employing producers, between within-sector overhead rank and
    within-sector employment rank.  ``sector_cv``: the median over those
    sectors of the coefficient of variation of employment.
    """
    pairs, cvs = [], []
    for region in economy.regions.values():
        sectors = {}
        for producer in region.producers:
            key = (region.name, producer.name)
            if key in sizes:
                sectors.setdefault(producer.commodity, []).append(
                    (producer.unit_cost, sizes[key]))
        for members in sectors.values():
            if len(members) < 2:
                continue
            by_cost = sorted(range(len(members)), key=lambda i: members[i][0])
            by_size = sorted(range(len(members)), key=lambda i: members[i][1])
            cost_rank = {i: r for r, i in enumerate(by_cost)}
            size_rank = {i: r for r, i in enumerate(by_size)}
            pairs.extend((cost_rank[i], size_rank[i]) for i in range(len(members)))
            values = [m[1] for m in members]
            mean = sum(values) / len(values)
            if mean > 0:
                cvs.append(st.pstdev(values) / mean)
    return {"cost_rank": _spearman(pairs),
            "sector_cv": st.median(cvs) if cvs else None}


def capacity_correlation(economy, sizes):
    """Spearman rho between realised employment and *authored* capacity.

    ``docs/124`` §5: our producers do not grow by winning a lottery, so a
    high correlation means the firm-size reading is largely the scenario
    author's input-output graph rather than an emergent fact.
    """
    pairs = []
    for region in economy.regions.values():
        for producer in region.producers:
            key = (region.name, producer.name)
            if key in sizes:
                pairs.append((producer.capacity_per_day, sizes[key]))
    if len(pairs) < 10:
        return None

    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        out = [0.0] * len(values)
        for rank, index in enumerate(order):
            out[index] = float(rank)
        return out

    a = ranks([p[0] for p in pairs])
    b = ranks([p[1] for p in pairs])
    n = len(a)
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = math.sqrt(sum((x - mean_a) ** 2 for x in a))
    var_b = math.sqrt(sum((y - mean_b) ** 2 for y in b))
    return cov / (var_a * var_b) if var_a and var_b else None


STRUCTURAL = ("capacity_rank", "cost_rank", "sector_cv", "employing",
              "bankruptcies", "cash_balance", "fund_share")


def _job(job):
    which, seed, knobs = job
    return measure_ours(seed, **knobs) if which == "ours" else measure_sa(seed)


def sweep(seeds=20, processes=4, **knobs):
    jobs = [(which, seed, knobs) for which in ("ours", "sa") for seed in range(seeds)]
    with Pool(processes) as pool:
        return pool.map(_job, jobs)


def main(argv):
    """``python -m economy_lab.wright_battery out.json 20 [knob=value ...]``;
    knobs are :func:`build_ours`'s keyword arguments."""
    seeds = int(argv[2]) if len(argv) > 2 else 20
    knobs = {}
    for arg in argv[3:]:
        key, value = arg.split("=", 1)
        if key == "producers_per_commodity":
            knobs[key] = int(value)
        elif key in ("commodities", "regions"):
            knobs[key] = int(value)
        elif key in ("fund_spending", "accumulate", "investment", "scale_stocks"):
            knobs[key] = value.lower() in ("1", "true", "on", "yes")
        else:
            knobs[key] = float(value)
    runs = sweep(seeds=seeds, **knobs)
    rows = [dict(facts(run), model=run["model"], seed=run["seed"],
                 **{key: run.get(key) for key in STRUCTURAL}) for run in runs]
    with open(argv[1], "w") as handle:
        json.dump(rows, handle)
    print("runs:", len(rows))


if __name__ == "__main__":
    main(sys.argv)
