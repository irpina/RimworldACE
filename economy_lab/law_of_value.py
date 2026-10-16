"""Does the law of value emerge? (docs/147)

A self-contained economy built from three things only: a technique drawn
blind, a market whose prices move on excess demand alone, and producers
(arm SC) or capital (arm CAP) that move toward the higher return.  No
price is computed from a value or a cost, no agent sees a value, and
every price starts at 1.  The question is where prices go.

    python3.12 -m economy_lab.law_of_value out.json [seeds] [days] [second]

``second`` runs docs/149's experiment instead of docs/147's.

Stdlib only, deterministic under a seed, and money moves only between
agents, so it is conserved.  Nothing here touches ``model.py``.
"""

from __future__ import annotations

import json
import sys
from math import exp, log, sqrt
from multiprocessing import Pool
from typing import Dict, List, Sequence, Tuple

GOODS = 12
DEPTHS = 4
GAMMA = 0.02
SIGMA = 0.1
LAMBDA = 0.02
MU = 0.01
PHI = 0.1
DELTA = 0.02
PRODUCERS = 500
WORKERS = 500
FIRMS = 100
CASH = 100.0
DAYS = 6000
WINDOW = 1000
SHOCK_DAY = 3000
TRAIL = 100


class Random:
    """SplitMix64, as in ``scale._Random``, with a uniform float."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def below(self, limit: int) -> int:
        return self.next() % max(limit, 1)

    def uniform(self, low: float, high: float) -> float:
        return low + (high - low) * ((self.next() >> 11) / 9007199254740992.0)


# --------------------------------------------------------------------------
# The technique (docs/147 §3.1).  Its stream never sees a price.

class Technique:
    def __init__(self, seed: int) -> None:
        rng = Random(seed * 1_000_003 + 17)
        per = GOODS // DEPTHS
        self.depth = [i // per for i in range(GOODS)]
        #: A[i] is a list of (input j, units of j per unit of i).
        self.A: List[List[Tuple[int, float]]] = []
        for i in range(GOODS):
            d = self.depth[i]
            row: Dict[int, float] = {}
            if d > 0:
                for _ in range(1 + rng.below(3)):
                    j = rng.below(d * per)
                    row[j] = row.get(j, 0.0) + rng.uniform(0.1, 0.5)
            self.A.append(sorted(row.items()))
        self.labor = [rng.uniform(0.1, 1.0) for _ in range(GOODS)]
        raw = [rng.uniform(0.5, 1.5) for _ in range(GOODS)]
        total = sum(raw)
        self.shares = [x / total for x in raw]
        # The null's shuffle is a separate stream (docs/147 §3.6).
        shuffle = Random(seed * 1_000_003 + 29)
        order = list(range(GOODS))
        for k in range(GOODS - 1, 0, -1):
            m = shuffle.below(k + 1)
            order[k], order[m] = order[m], order[k]
        self.permutation = order

    def values(self, labor: Sequence[float] = None) -> List[float]:
        """Solve v = l + A v exactly: A is triangular in depth order."""
        labor = self.labor if labor is None else labor
        v = [0.0] * GOODS
        for i in range(GOODS):
            v[i] = labor[i] + sum(c * v[j] for j, c in self.A[i])
        return v

    def null_values(self) -> List[float]:
        return self.values([self.labor[self.permutation[i]] for i in range(GOODS)])

    def prices_of_production(self, r: float) -> List[float]:
        """p = (1 + r)(A p + l), the wage as numeraire."""
        p = [0.0] * GOODS
        for i in range(GOODS):
            p[i] = (1.0 + r) * (sum(c * p[j] for j, c in self.A[i]) + self.labor[i])
        return p

    def most_used_base(self) -> int:
        column = [0.0] * GOODS
        for row in self.A:
            for j, c in row:
                column[j] += c
        base = [i for i in range(GOODS) if self.depth[i] == 0]
        return max(base, key=lambda i: (column[i], -i))


# --------------------------------------------------------------------------
# The market (docs/147 §3.2).

# --------------------------------------------------------------------------
# Arm SC and SH (docs/147 §3.3, §3.4).

def run_simple(seed: int, days: int = DAYS, shock_day: int = None,
               explore: float = 0.0, buffer: float = 1.0) -> dict:
    """``explore`` and ``buffer`` are docs/149's switches; the defaults
    are docs/147's experiment, bit for bit."""
    tech = Technique(seed)
    rng = Random(seed * 1_000_003 + 41)
    labor = list(tech.labor)
    shocked = tech.most_used_base() if shock_day is not None else None
    n = PRODUCERS
    sector = [rng.below(GOODS) for _ in range(n)]
    cash = [CASH] * n
    held = [[0.0] * GOODS for _ in range(n)]
    forsale = [[0.0] * GOODS for _ in range(n)]
    income = [0.0] * n
    prices = [1.0] * GOODS
    money0 = sum(cash)
    worst_drift = 0.0
    log_prices: List[List[float]] = []
    window_income = [0.0] * GOODS
    window_days = [0] * GOODS
    # Diagnostics only (docs/148): none feeds back into the dynamics.
    window_output = [0.0] * GOODS
    window_capacity = [0.0] * GOODS
    empty_days = [0] * GOODS
    window_start = days - WINDOW

    for day in range(days):
        if shock_day is not None and day == shock_day:
            labor[shocked] *= 0.5
        # 1. Produce.
        for a in range(n):
            s = sector[a]
            y = 1.0 / labor[s]
            h = held[a]
            for j, c in tech.A[s]:
                y = min(y, h[j] / c)
            for j, c in tech.A[s]:
                h[j] -= c * y
            forsale[a][s] += y
            if day >= days - WINDOW:
                window_output[s] += y
                window_capacity[s] += 1.0 / labor[s]
        # 2. Order.
        input_orders = [[] for _ in range(GOODS)]
        consumer_orders = [[] for _ in range(GOODS)]
        demand = [0.0] * GOODS
        for a in range(n):
            s = sector[a]
            h = held[a]
            wants = []
            total = 0.0
            for j, c in tech.A[s]:
                need = buffer * c / labor[s] - h[j]
                if need > 0.0:
                    money = prices[j] * need
                    wants.append((j, money))
                    total += money
            scale = 1.0 if total <= cash[a] else cash[a] / total
            for j, money in wants:
                input_orders[j].append((a, money * scale))
                demand[j] += money * scale
            spend = SIGMA * (cash[a] - total * scale)
            if spend > 0.0:
                for j in range(GOODS):
                    money = spend * tech.shares[j]
                    consumer_orders[j].append((a, money))
                    demand[j] += money
        supply = [0.0] * GOODS
        stocks = [[] for _ in range(GOODS)]
        for a in range(n):
            f = forsale[a]
            for j in range(GOODS):
                if f[j] > 0.0:
                    stocks[j].append((a, f[j]))
                    supply[j] += f[j]
        # 3. Trade.
        received = [0.0] * n
        spent_inputs = [0.0] * n
        spent_other = [0.0] * n
        _trade(prices, demand, supply, input_orders, consumer_orders,
                      stocks, cash, received, spent_inputs, spent_other,
                      held, forsale)
        # 4. Income.
        for a in range(n):
            net = received[a] - spent_inputs[a]
            income[a] += LAMBDA * (net - income[a])
            if day >= window_start:
                window_income[sector[a]] += net
                window_days[sector[a]] += 1
        if day >= window_start:
            occupied = set(sector)
            for j in range(GOODS):
                if j not in occupied:
                    empty_days[j] += 1
        # 5. Move.
        if explore > 0.0:
            for a in range(n):
                if rng.uniform(0.0, 1.0) < explore:
                    sector[a] = rng.below(GOODS)
        for a in range(n):
            if rng.uniform(0.0, 1.0) < MU:
                b = rng.below(n)
                if income[b] > income[a]:
                    sector[a] = sector[b]
                    income[a] = income[b]
        drift = abs(sum(cash) - money0) / money0
        worst_drift = max(worst_drift, drift)
        log_prices.append([log(p) for p in prices])

    old_values = tech.values()
    out = _summary(tech, log_prices, days)
    out.update(
        arm="SH" if shock_day is not None else "SC",
        explore=explore,
        buffer=buffer,
        seed=seed,
        worst_money_drift=worst_drift,
        null=_stats(_window_mean(log_prices, days - WINDOW, days), tech.null_values()),
        income_cv=_income_cv(window_income, window_days),
        sector_income=[window_income[j] / window_days[j] if window_days[j] else None for j in range(GOODS)],
        producers_per_sector=[sector.count(j) for j in range(GOODS)],
        empty_days=empty_days,
        output_over_capacity=[window_output[j] / window_capacity[j] if window_capacity[j] else None for j in range(GOODS)],
    )
    if shock_day is not None:
        new_values = tech.values(labor)
        before = _window_mean(log_prices, shock_day - WINDOW, shock_day)
        after = _window_mean(log_prices, days - WINDOW, days)
        out["shocked_good"] = shocked
        out["pre_old"] = _stats(before, old_values)
        out["post_new"] = _stats(after, new_values)
        out["post_old"] = _stats(after, old_values)
        price_ratio = exp((after[shocked] - _mean(after)) - (before[shocked] - _mean(before)))
        lv_old = [log(x) for x in old_values]
        lv_new = [log(x) for x in new_values]
        value_ratio = exp((lv_new[shocked] - _mean(lv_new)) - (lv_old[shocked] - _mean(lv_old)))
        out["shock_price_ratio"] = price_ratio
        out["shock_value_ratio"] = value_ratio
        out["shock_trail_new"] = _trail(log_prices, new_values)
    return out


def _trade(prices, demand, supply, input_orders, consumer_orders,
                  stocks, cash, received, spent_inputs, spent_other,
                  held, forsale):
    for j in range(GOODS):
        p = prices[j]
        d, s = demand[j], supply[j]
        wanted = d / p
        traded = min(s, wanted)
        if traded > 0.0:
            buy_fraction = traded / wanted
            sell_fraction = traded / s
            for a, money in input_orders[j]:
                pay = money * buy_fraction
                cash[a] -= pay
                spent_inputs[a] += pay
                held[a][j] += pay / p
            for a, money in consumer_orders[j]:
                pay = money * buy_fraction
                cash[a] -= pay
                spent_other[a] += pay
            for a, units in stocks[j]:
                sold = units * sell_fraction
                forsale[a][j] -= sold
                cash[a] += sold * p
                received[a] += sold * p
        if wanted + s > 0.0:
            prices[j] = p * exp(GAMMA * (wanted - s) / (wanted + s))


# --------------------------------------------------------------------------
# Arm CAP (docs/147 §3.5).

def run_capitalist(seed: int, days: int = DAYS, explore: float = 0.0,
                   buffer: float = None) -> dict:
    tech = Technique(seed)
    rng = Random(seed * 1_000_003 + 53)
    m = FIRMS
    # Agents 0..m-1 are firms; agent m is the workers' household, whose
    # members are identical (equal shares of the wage bill, the same
    # spending rule), so it is exact to hold them as one purse.
    house = m
    sector = [rng.below(GOODS) for _ in range(m)]
    total_money = CASH * (WORKERS + FIRMS)
    cash = [0.5 * total_money / m] * m + [0.5 * total_money]
    held = [[0.0] * GOODS for _ in range(m + 1)]
    forsale = [[0.0] * GOODS for _ in range(m + 1)]
    revenue = [0.0] * m
    outlay = [0.0] * m
    prices = [1.0] * GOODS
    wage = 1.0
    money0 = sum(cash)
    worst_drift = 0.0
    log_prices: List[List[float]] = []
    window_start = days - WINDOW
    window_revenue = 0.0
    window_outlay = 0.0
    hired_total = []
    empty_days = [0] * GOODS

    for day in range(days):
        # 1. Order.
        input_orders = [[] for _ in range(GOODS)]
        consumer_orders = [[] for _ in range(GOODS)]
        demand = [0.0] * GOODS
        labor_orders = [0.0] * m
        for f in range(m):
            s = sector[f]
            unit = sum(c * prices[j] for j, c in tech.A[s]) + wage * tech.labor[s]
            plan = PHI * cash[f] / unit
            h = held[f]
            if buffer is None:
                for j, c in tech.A[s]:
                    need = c * plan - h[j]
                    if need > 0.0:
                        money = prices[j] * need
                        input_orders[j].append((f, money))
                        demand[j] += money
            else:
                # docs/149: hold ``buffer`` days of the plan's inputs, and
                # keep inputs and wages within (1 - DELTA) of the cash.
                wants = []
                total = 0.0
                for j, c in tech.A[s]:
                    need = buffer * c * plan - h[j]
                    if need > 0.0:
                        wants.append((j, prices[j] * need))
                        total += prices[j] * need
                room = (1.0 - DELTA) * cash[f] - wage * tech.labor[s] * plan
                scale = 1.0 if total <= room else max(room, 0.0) / total
                for j, money in wants:
                    input_orders[j].append((f, money * scale))
                    demand[j] += money * scale
            labor_orders[f] = tech.labor[s] * plan
            spend = DELTA * cash[f]
            for j in range(GOODS):
                money = spend * tech.shares[j]
                consumer_orders[j].append((f, money))
                demand[j] += money
        spend = SIGMA * cash[house]
        for j in range(GOODS):
            money = spend * tech.shares[j]
            consumer_orders[j].append((house, money))
            demand[j] += money
        # 2. Hire.
        wanted_labor = sum(labor_orders)
        hired_all = min(wanted_labor, float(WORKERS))
        fraction = hired_all / wanted_labor if wanted_labor > 0.0 else 0.0
        hired = [0.0] * m
        wages_paid = [0.0] * m
        for f in range(m):
            hired[f] = labor_orders[f] * fraction
            bill = hired[f] * wage
            wages_paid[f] = bill
            cash[f] -= bill
            cash[house] += bill
        if wanted_labor + WORKERS > 0.0:
            wage *= exp(GAMMA * (wanted_labor - WORKERS) / (wanted_labor + WORKERS))
        hired_total.append(hired_all)
        # 3. Trade.
        supply = [0.0] * GOODS
        stocks = [[] for _ in range(GOODS)]
        for f in range(m):
            fs = forsale[f]
            for j in range(GOODS):
                if fs[j] > 0.0:
                    stocks[j].append((f, fs[j]))
                    supply[j] += fs[j]
        received = [0.0] * (m + 1)
        spent_inputs = [0.0] * (m + 1)
        spent_other = [0.0] * (m + 1)
        _trade(prices, demand, supply, input_orders, consumer_orders,
                      stocks, cash, received, spent_inputs, spent_other,
                      held, forsale)
        # 4. Produce.
        for f in range(m):
            s = sector[f]
            y = hired[f] / tech.labor[s]
            h = held[f]
            for j, c in tech.A[s]:
                y = min(y, h[j] / c)
            for j, c in tech.A[s]:
                h[j] -= c * y
            forsale[f][s] += y
        # 5. Profit rate.
        for f in range(m):
            out = spent_inputs[f] + wages_paid[f]
            revenue[f] += LAMBDA * (received[f] - revenue[f])
            outlay[f] += LAMBDA * (out - outlay[f])
            if day >= window_start:
                window_revenue += received[f]
                window_outlay += out
        # 6. Move.
        if day >= window_start:
            occupied = set(sector)
            for j in range(GOODS):
                if j not in occupied:
                    empty_days[j] += 1
        if explore > 0.0:
            for f in range(m):
                if rng.uniform(0.0, 1.0) < explore:
                    sector[f] = rng.below(GOODS)
        rates = [revenue[f] / outlay[f] - 1.0 if outlay[f] > 0.0 else -1.0 for f in range(m)]
        for f in range(m):
            if rng.uniform(0.0, 1.0) < MU:
                g = rng.below(m)
                if rates[g] > rates[f]:
                    sector[f] = sector[g]
                    revenue[f] = revenue[g]
                    outlay[f] = outlay[g]
        drift = abs(sum(cash) - money0) / money0
        worst_drift = max(worst_drift, drift)
        log_prices.append([log(p) for p in prices])

    r_hat = window_revenue / window_outlay - 1.0 if window_outlay > 0.0 else 0.0
    window = _window_mean(log_prices, days - WINDOW, days)
    values = tech.values()
    composition = [log(v / l) for v, l in zip(values, tech.labor)]
    deviation = [lp - log(v) for lp, v in zip(window, values)]
    out = _summary(tech, log_prices, days)
    out.update(
        arm="CAP",
        explore=explore,
        buffer=buffer,
        empty_days=empty_days,
        seed=seed,
        worst_money_drift=worst_drift,
        r_hat=r_hat,
        # Prices of production exist only for r > -1 (docs/148 §1).
        pop=_stats(window, tech.prices_of_production(r_hat)) if -1.0 < r_hat < 1e6 else None,
        composition_corr=_corr(deviation, composition),
        employment=sum(hired_total[-WINDOW:]) / (WINDOW * WORKERS),
        firms_per_sector=[sector.count(i) for i in range(GOODS)],
    )
    return out


# --------------------------------------------------------------------------
# Statistics (docs/147 §3.6).

def _mean(xs):
    return sum(xs) / len(xs)


def _std(xs):
    mu = _mean(xs)
    return sqrt(sum((x - mu) ** 2 for x in xs) / len(xs))


def _corr(xs, ys):
    mx, my = _mean(xs), _mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / sqrt(sxx * syy) if sxx > 0.0 and syy > 0.0 else 0.0


def _window_mean(log_prices, start, stop):
    rows = log_prices[start:stop]
    return [sum(row[j] for row in rows) / len(rows) for j in range(GOODS)]


def _stats(window_log_prices, reference):
    lr = [log(x) for x in reference]
    return {
        "dispersion": _std([p - r for p, r in zip(window_log_prices, lr)]),
        "correlation": _corr(window_log_prices, lr),
    }


def _trail(log_prices, values):
    """The 100-day trailing dispersion against ``values``, every 10 days."""
    lv = [log(x) for x in values]
    out = []
    for day in range(TRAIL, len(log_prices) + 1, 10):
        mean = _window_mean(log_prices, day - TRAIL, day)
        out.append(_std([p - v for p, v in zip(mean, lv)]))
    return out


def _income_cv(income, days):
    per = [income[i] / days[i] for i in range(GOODS) if days[i] > 0]
    mu = _mean(per)
    return _std(per) / abs(mu) if mu != 0.0 else float("inf")


def _summary(tech, log_prices, days):
    values = tech.values()
    window = _window_mean(log_prices, days - WINDOW, days)
    trail = _trail(log_prices, values)
    initial = _std([log(v) for v in values])
    half = None
    for k, d in enumerate(trail):
        if d < 0.5 * initial:
            half = TRAIL + 10 * k
            break
    return {
        "values": values,
        "labor": tech.labor,
        "depth": tech.depth,
        "window_log_prices": window,
        "initial_dispersion": initial,
        "value": _stats(window, values),
        "half_day": half,
        "trail": trail[::10],
    }


# --------------------------------------------------------------------------

#: docs/149's second experiment: exploration and a five-day input buffer.
SECOND = dict(explore=0.001, buffer=5.0)


def _job(args):
    arm, seed, days, second = args
    switches = SECOND if second else {}
    if arm == "SC":
        return run_simple(seed, days, **switches)
    if arm == "SH":
        return run_simple(seed, days, shock_day=days // 2, **switches)
    return run_capitalist(seed, days, **switches)


def main(argv: Sequence[str]) -> None:
    out = argv[0]
    seeds = int(argv[1]) if len(argv) > 1 else 20
    days = int(argv[2]) if len(argv) > 2 else DAYS
    second = len(argv) > 3 and argv[3] == "second"
    jobs = [(arm, seed, days, second) for seed in range(seeds) for arm in ("SC", "SH", "CAP")]
    rows = []
    with Pool(4) as pool:
        for k, row in enumerate(pool.imap_unordered(_job, jobs), 1):
            rows.append(row)
            rows.sort(key=lambda r: (r["arm"], r["seed"]))
            with open(out, "w") as handle:
                json.dump(rows, handle, indent=1)
            print(f"{k}/{len(jobs)}: {row['arm']} seed {row['seed']}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
