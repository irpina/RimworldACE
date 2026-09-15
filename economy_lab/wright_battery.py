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
from economy_lab.scale import synthetic_economy

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


def build_ours(seed, *, demand=DEMAND, basket_fraction=BASKET_FRACTION,
               quantum=1.0, basket_in_demand=True, producers_per_commodity=1):
    """Our laboratory at a size where a distribution exists (docs/124 §3),
    rescaled so that most producers can employ a whole worker (docs/126),
    with the staple sector sized to feed that workforce (docs/128).

    The knobs are the designs' experiments: ``demand`` is docs/126
    prediction 1, ``quantum`` its prediction 2, ``basket_fraction`` its 3
    and 4; ``basket_in_demand=False`` reproduces docs/127's spiral.
    """
    base = synthetic_economy(commodities=COMMODITIES, regions=REGIONS,
                             daily_demand=demand, basket_fraction=basket_fraction,
                             basket_in_demand=basket_in_demand,
                             producers_per_commodity=producers_per_commodity,
                             record_history=False, seed=seed)
    regions = list(base.regions.values())
    for region in regions:
        region.labor_pool = LABOR_POOL_PER_DEMAND * demand
        region.cash *= CASH_MULTIPLIER * demand
        region.worker_cash *= demand
        for producer in region.producers:
            producer.cash = max(producer.cash, PURSE_FLOOR_PER_DEMAND * demand)
    return Economy(
        list(base.commodities.values()), regions, base.routes,
        record_history=False,
        producer_cash=True,
        posted_prices=True,
        producer_employment_quantum=quantum,
        investment_interval_days=INVESTMENT_INTERVAL,
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
    """Wages paid, sales receipts and producer purchases, all silver."""
    ledger = economy.ledger
    return (sum(ledger.wages_paid.values()),
            sum(ledger.sales_receipts.values()),
            sum(ledger.producer_purchases.values()))


def measure_ours(seed, **knobs):
    """Our model, through the identical instrument."""
    economy = build_ours(seed, **knobs)
    economy.step(MONTH * BURN_IN_MONTHS)
    labor_pool = LABOR_POOL_PER_DEMAND * knobs.get("demand", DEMAND)

    def totals():
        living = sum(economy.ledger.living_labor.values())
        necessary = sum(economy.ledger.necessary_labor.values())
        value = sum(economy.ledger.value_produced.values())
        return living, necessary, value

    sizes, growth, gdp, shares, profits = [], [], [], [], []
    money_shares, gross_shares = [], []
    previous_sizes = employment(economy)
    last_living, last_necessary, last_value = totals()
    last_wages, last_receipts, last_purchases = money_totals(economy)
    deaths_at_start = len(economy.ledger.bankruptcies)
    active_seen = []

    for _ in range(WINDOW_MONTHS):
        economy.step(MONTH)
        current = employment(economy)
        sizes.extend(current.values())
        growth.extend(_growth(previous_sizes, current))
        previous_sizes = current
        living, necessary, value = totals()
        gdp.append(value - last_value)
        if living - last_living > 0:
            shares.append((necessary - last_necessary) / (living - last_living))
        last_living, last_necessary, last_value = living, necessary, value
        wages, receipts, purchases = money_totals(economy)
        d_wages, d_receipts = wages - last_wages, receipts - last_receipts
        d_added = d_receipts - (purchases - last_purchases)
        if d_added > 0:
            money_shares.append(d_wages / d_added)
        if d_receipts > 0:
            gross_shares.append(d_wages / d_receipts)
        last_wages, last_receipts, last_purchases = wages, receipts, purchases
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
        "profit_rates": profits,
        "unemployment": max(0.0, 1.0 - employed / (labor_pool * REGIONS)),
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
              "bankruptcies")


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
        knobs[key] = int(value) if key == "producers_per_commodity" else float(value)
    runs = sweep(seeds=seeds, **knobs)
    rows = [dict(facts(run), model=run["model"], seed=run["seed"],
                 **{key: run.get(key) for key in STRUCTURAL}) for run in runs]
    with open(argv[1], "w") as handle:
        json.dump(rows, handle)
    print("runs:", len(rows))


if __name__ == "__main__":
    main(sys.argv)
