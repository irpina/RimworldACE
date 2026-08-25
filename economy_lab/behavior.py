"""Behavioral observations derived from existing Stage 0 scenario histories."""

from __future__ import annotations

from typing import Dict, Iterable

from .model import Economy

from .scenarios import (
    DAYS_PER_QUADRUM,
    MEALS,
    ScenarioParameters,
    arbitrage,
    CHEMFUEL,
    equilibrium,
    LEAVES,
    cost_competition,
    producer_loss,
    regional_glut,
    reserve_depletion,
    technique_change,
    YAYO,
)


SHOCK_DAY = 60
LOCAL_REGION = "Dust Basin"
DISTANT_REGION = "Green River"
COMMODITY = "yayo"
UPSTREAM_COMMODITIES = (LEAVES, CHEMFUEL)


def _metric(value: float, unit: str) -> Dict[str, object]:
    return {"value": round(value, 6), "unit": unit}


def _shock_extrema_metrics(
    *,
    scenario: str,
    economy: Economy,
    commodities: Iterable[str],
    terminal_label: str,
) -> Dict[str, Dict[str, object]]:
    """Observe upstream paths already retained in a scenario's history."""
    metrics: Dict[str, Dict[str, object]] = {}
    for commodity in commodities:
        prefix = f"{scenario}.local.{commodity}"
        prices = economy.series(LOCAL_REGION, commodity)
        inventories = economy.series(
            LOCAL_REGION, commodity, field="inventory"
        )
        shock_prices = prices[SHOCK_DAY + 1 :]
        shock_inventories = inventories[SHOCK_DAY + 1 :]

        price_trough = min(shock_prices)
        price_peak = max(shock_prices)
        inventory_trough = min(shock_inventories)
        inventory_peak = max(shock_inventories)

        metrics.update(
            {
                f"{prefix}.price_trough": _metric(price_trough, "silver"),
                f"{prefix}.price_trough_day": _metric(
                    SHOCK_DAY + 1 + shock_prices.index(price_trough), "day"
                ),
                f"{prefix}.price_peak": _metric(price_peak, "silver"),
                f"{prefix}.price_peak_day": _metric(
                    SHOCK_DAY + 1 + shock_prices.index(price_peak), "day"
                ),
                f"{prefix}.inventory_trough": _metric(
                    inventory_trough, "units"
                ),
                f"{prefix}.inventory_trough_day": _metric(
                    SHOCK_DAY
                    + 1
                    + shock_inventories.index(inventory_trough),
                    "day",
                ),
                f"{prefix}.inventory_peak": _metric(inventory_peak, "units"),
                f"{prefix}.inventory_peak_day": _metric(
                    SHOCK_DAY + 1 + shock_inventories.index(inventory_peak),
                    "day",
                ),
                f"{prefix}.{terminal_label}_price": _metric(
                    prices[-1], "silver"
                ),
                f"{prefix}.{terminal_label}_inventory": _metric(
                    inventories[-1], "units"
                ),
            }
        )
    return metrics


def collect_behavioral_metrics(
    parameters: ScenarioParameters | None = None,
) -> Dict[str, Dict[str, object]]:
    """Run the existing scenarios and return a flat, diff-friendly metric map."""
    parameters = parameters or ScenarioParameters()
    stable = equilibrium(parameters=parameters)
    glut = regional_glut(parameters=parameters)
    loss = producer_loss(parameters=parameters)
    trade = arbitrage(parameters=parameters)
    technique = technique_change(parameters=parameters)
    competition = cost_competition(parameters=parameters)
    depletion = reserve_depletion(parameters=parameters)

    stable_local = stable.series(LOCAL_REGION, COMMODITY)
    stable_distant = stable.series(DISTANT_REGION, COMMODITY)

    glut_local = glut.series(LOCAL_REGION, COMMODITY)
    glut_distant = glut.series(DISTANT_REGION, COMMODITY)
    local_shock = glut_local[SHOCK_DAY + 1 :]
    distant_shock = glut_distant[SHOCK_DAY + 1 :]
    local_trough = min(local_shock)
    distant_trough = min(distant_shock)
    local_trough_day = SHOCK_DAY + 1 + local_shock.index(local_trough)
    distant_trough_day = SHOCK_DAY + 1 + distant_shock.index(distant_trough)
    halfway_price = (
        local_trough + (parameters.reference_price - local_trough) / 2.0
    )
    half_recovery_day = next(
        day
        for day in range(local_trough_day, len(glut_local))
        if glut_local[day] >= halfway_price
    )
    half_recovery_days = half_recovery_day - local_trough_day

    loss_local = loss.series(LOCAL_REGION, COMMODITY)
    loss_capacity = loss.series(LOCAL_REGION, COMMODITY, field="capacity")
    loss_shock = loss_local[SHOCK_DAY + 1 :]
    loss_peak = max(loss_shock)
    loss_peak_day = SHOCK_DAY + 1 + loss_shock.index(loss_peak)
    capacity_recovery_day = next(
        day
        for day in range(SHOCK_DAY + 1, len(loss_capacity))
        if loss_capacity[day] >= parameters.producer_capacity_per_day * 0.80
    )
    capacity_recovery_days = capacity_recovery_day - SHOCK_DAY

    arbitrage_volume = trade.regions[LOCAL_REGION].exported_total[COMMODITY]

    metrics = {
        "arbitrage.export_volume": _metric(arbitrage_volume, "units"),
        "equilibrium.distant_price_range": _metric(
            max(stable_distant) - min(stable_distant), "silver"
        ),
        "equilibrium.local_price_range": _metric(
            max(stable_local) - min(stable_local), "silver"
        ),
        "glut.distant_trough_day": _metric(distant_trough_day, "day"),
        "glut.distant_trough_price": _metric(distant_trough, "silver"),
        "glut.local_half_recovery_days": _metric(half_recovery_days, "days"),
        "glut.local_half_recovery_quadrums": _metric(
            half_recovery_days / DAYS_PER_QUADRUM, "quadrums"
        ),
        "glut.local_trough_day": _metric(local_trough_day, "day"),
        "glut.local_trough_price": _metric(local_trough, "silver"),
        "producer_loss.capacity_recovery_days": _metric(
            capacity_recovery_days, "days"
        ),
        "producer_loss.capacity_recovery_quadrums": _metric(
            capacity_recovery_days / DAYS_PER_QUADRUM, "quadrums"
        ),
        "producer_loss.local_peak_day": _metric(loss_peak_day, "day"),
        "producer_loss.local_peak_price": _metric(loss_peak, "silver"),
    }
    metrics.update(
        _shock_extrema_metrics(
            scenario="glut",
            economy=glut,
            commodities=UPSTREAM_COMMODITIES,
            terminal_label="settled",
        )
    )
    metrics.update(
        _shock_extrema_metrics(
            scenario="producer_loss",
            economy=loss,
            commodities=UPSTREAM_COMMODITIES,
            terminal_label="terminal",
        )
    )
    metrics.update(
        _labor_metrics(
            stable=stable,
            glut=glut,
            loss=loss,
            technique=technique,
            competition=competition,
            depletion=depletion,
        )
    )
    metrics.update(
        _price_of_production_metrics(stable=stable, technique=technique)
    )
    return metrics


def _price_of_production_metrics(
    *, stable: Economy, technique: Economy
) -> Dict[str, Dict[str, object]]:
    """Observe the classical price system (docs/26).

    Newly observed quantities, not changed behavior: nothing here feeds
    back into prices.  Relative to the wage good, because the eigenvector
    fixes only relative prices.

    Two of these are the session's result rather than its bookkeeping.
    `yayo_over_authored_ratio` is how far a uniform profit rate carries a
    two-stage input chain away from RimWorld's authored price, and
    `total_profit_over_surplus` is how far Marx's second invariance
    postulate misses once the first is imposed.
    """
    system = stable.prices_of_production(numeraire=MEALS)
    aggregates = stable.production_price_aggregates()
    prices = system["prices"]
    values = stable.labor_values
    changed = technique.prices_of_production(numeraire=MEALS)

    def relative(commodity: str) -> float:
        return prices[commodity] / prices[MEALS]

    def value_ratio(commodity: str) -> float:
        return values[commodity] / values[MEALS]

    def authored_ratio(commodity: str) -> float:
        return (
            stable.commodities[commodity].reference_price
            / stable.commodities[MEALS].reference_price
        )

    return {
        "equilibrium.production.profit_rate": _metric(
            system["profit_rate"], "ratio"
        ),
        "equilibrium.production.basic_count": _metric(
            float(len(system["basics"])), "commodities"
        ),
        "equilibrium.production.iterations": _metric(
            float(system["iterations"]), "count"
        ),
        "equilibrium.production.wage_per_tick": _metric(
            system["wage"], "silver"
        ),
        "equilibrium.production.chemfuel_relative_to_meals": _metric(
            relative(CHEMFUEL), "ratio"
        ),
        "equilibrium.production.psychoid_leaves_relative_to_meals": _metric(
            relative(LEAVES), "ratio"
        ),
        "equilibrium.production.yayo_relative_to_meals": _metric(
            relative(YAYO), "ratio"
        ),
        "equilibrium.production.chemfuel_over_value_ratio": _metric(
            relative(CHEMFUEL) / value_ratio(CHEMFUEL), "ratio"
        ),
        "equilibrium.production.psychoid_leaves_over_value_ratio": _metric(
            relative(LEAVES) / value_ratio(LEAVES), "ratio"
        ),
        "equilibrium.production.yayo_over_value_ratio": _metric(
            relative(YAYO) / value_ratio(YAYO), "ratio"
        ),
        "equilibrium.production.yayo_over_authored_ratio": _metric(
            relative(YAYO) / authored_ratio(YAYO), "ratio"
        ),
        "equilibrium.production.total_profit_over_surplus": _metric(
            aggregates["total_profit"] / aggregates["total_surplus"], "ratio"
        ),
        # The wage good's technique is the only one that can move r, so a
        # cheaper meal raises the uniform profit rate exactly as it raises
        # the rate of surplus value (docs/20).
        "technique_change.production.profit_rate": _metric(
            changed["profit_rate"], "ratio"
        ),
        "technique_change.production.profit_rate_gain": _metric(
            changed["profit_rate"] / system["profit_rate"], "ratio"
        ),
    }


def _employment_series(economy: Economy, region: str) -> list:
    return [h["regions"][region]["employment"] for h in economy.history]


def _labor_metrics(
    *,
    stable: Economy,
    glut: Economy,
    loss: Economy,
    technique: Economy,
    competition: Economy,
    depletion: Economy,
) -> Dict[str, Dict[str, object]]:
    """Observe the wage relation (docs/17, docs/18).

    Frozen as newly observed quantities, not changed behavior.  The rate of
    surplus value is the labor-time ratio; the wage rate is the money form
    of variable capital — kept as separate observations, never combined.
    """
    stable_region = stable.regions[LOCAL_REGION]
    glut_employment = _employment_series(glut, LOCAL_REGION)[SHOCK_DAY + 1 :]
    glut_meal_prices = glut.series(LOCAL_REGION, MEALS)[SHOCK_DAY + 1 :]
    loss_employment = _employment_series(loss, LOCAL_REGION)[SHOCK_DAY + 1 :]
    loss_meal_prices = loss.series(LOCAL_REGION, MEALS)[SHOCK_DAY + 1 :]
    employment_trough = min(glut_employment)
    loss_employment_trough = min(loss_employment)
    return {
        "equilibrium.local.employment_worker_days": _metric(
            stable_region.worker_days_earned, "worker-days"
        ),
        "equilibrium.local.wage_rate": _metric(
            stable_region.wage_rate(), "silver"
        ),
        "equilibrium.rate_of_surplus_value": _metric(
            stable.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "equilibrium.local.meals.settled_price": _metric(
            stable_region.prices[MEALS], "silver"
        ),
        "equilibrium.local.meals.settled_inventory": _metric(
            stable_region.inventory[MEALS], "units"
        ),
        "glut.local.employment_trough": _metric(
            employment_trough, "worker-days"
        ),
        "glut.local.employment_trough_day": _metric(
            SHOCK_DAY + 1 + glut_employment.index(employment_trough), "day"
        ),
        "glut.local.meals.price_range": _metric(
            max(glut_meal_prices) - min(glut_meal_prices), "silver"
        ),
        "producer_loss.local.employment_trough": _metric(
            loss_employment_trough, "worker-days"
        ),
        "producer_loss.local.employment_trough_day": _metric(
            SHOCK_DAY + 1 + loss_employment.index(loss_employment_trough),
            "day",
        ),
        "producer_loss.local.meals.price_trough": _metric(
            min(loss_meal_prices), "silver"
        ),
        "producer_loss.local.meals.price_peak": _metric(
            max(loss_meal_prices), "silver"
        ),
        # --- endogenous labor values (docs/19) ---------------------------
        # Solved from the process graph, in work-ticks.  These are values,
        # not prices, and not the authored FINDINGS.md figures, which stay
        # untouched on the Commodity.
        "equilibrium.value.chemfuel_ticks": _metric(
            stable.labor_values[CHEMFUEL], "ticks"
        ),
        "equilibrium.value.meals_ticks": _metric(
            stable.labor_values[MEALS], "ticks"
        ),
        "equilibrium.value.psychoid_leaves_ticks": _metric(
            stable.labor_values[LEAVES], "ticks"
        ),
        "equilibrium.value.yayo_ticks": _metric(
            stable.labor_values[YAYO], "ticks"
        ),
        # Relative surplus value: the wage good gets cheaper, so the value
        # of labor-power falls and s/v rises, with the working day and the
        # basket held fixed.
        "technique_change.value.meals_social_ticks": _metric(
            technique.labor_values[MEALS], "ticks"
        ),
        "technique_change.value.meals_adopter_ticks": _metric(
            technique.regional_labor_values[LOCAL_REGION][MEALS], "ticks"
        ),
        "technique_change.value.meals_laggard_ticks": _metric(
            technique.regional_labor_values[DISTANT_REGION][MEALS], "ticks"
        ),
        "technique_change.local.rate_of_surplus_value": _metric(
            technique.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "technique_change.distant.rate_of_surplus_value": _metric(
            technique.rate_of_surplus_value(DISTANT_REGION), "ratio"
        ),
        "technique_change.local.wage_rate": _metric(
            technique.regions[LOCAL_REGION].wage_rate(), "silver"
        ),
        # --- competitive transmission (docs/21) --------------------------
        # How much of a cost change reaches the price, and how the order
        # book is shared out. The two scenarios are deliberate opposites:
        # technique-change saves labor (value moves, money barely does),
        # cost-competition saves overhead (money moves, value not at all).
        "technique_change.local.meals.price": _metric(
            technique.regions[LOCAL_REGION].prices[MEALS], "silver"
        ),
        "cost_competition.local.meals.price": _metric(
            competition.regions[LOCAL_REGION].prices[MEALS], "silver"
        ),
        "cost_competition.local.meals.cost_ratio": _metric(
            competition.regions[LOCAL_REGION].cost_ratio[MEALS], "ratio"
        ),
        "cost_competition.local.meals.cheap_producer_share": _metric(
            _cheapest_share(competition, LOCAL_REGION, MEALS), "fraction"
        ),
        "cost_competition.local.wage_rate": _metric(
            competition.regions[LOCAL_REGION].wage_rate(), "silver"
        ),
        "cost_competition.local.rate_of_surplus_value": _metric(
            competition.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "cost_competition.value.meals_ticks": _metric(
            competition.labor_values[MEALS], "ticks"
        ),
        # The docs/16 artifact: a reference-anchored price could only sit
        # above a doubled cost by starving the buffer.
        "depletion.local.chemfuel.inventory_fraction_of_target": _metric(
            _inventory_fraction_of_target(depletion, LOCAL_REGION, CHEMFUEL),
            "fraction",
        ),
        "depletion.local.chemfuel.settled_price": _metric(
            depletion.regions[LOCAL_REGION].prices[CHEMFUEL], "silver"
        ),
        # Downstream cost-push, which docs/16 recorded as exactly absent.
        "depletion.local.yayo.settled_price": _metric(
            depletion.regions[LOCAL_REGION].prices[YAYO], "silver"
        ),
        # --- the value ledger (docs/23) ----------------------------------
        # c, v and s in work-ticks, and the classical ratios built from
        # them. Value ratios only: the value rate of profit is not money
        # profitability and the two are never combined.
        "equilibrium.value_ledger.constant_capital": _metric(
            stable.ledger.constant_capital(LOCAL_REGION), "ticks"
        ),
        "equilibrium.value_ledger.fixed_capital_consumed": _metric(
            stable.ledger.fixed_capital_consumed[LOCAL_REGION], "ticks"
        ),
        "equilibrium.value_ledger.fixed_share_of_constant": _metric(
            stable.ledger.fixed_capital_consumed[LOCAL_REGION]
            / stable.ledger.constant_capital(LOCAL_REGION),
            "fraction",
        ),
        "equilibrium.value_ledger.variable_capital": _metric(
            stable.ledger.necessary_labor[LOCAL_REGION], "ticks"
        ),
        "equilibrium.value_ledger.surplus_labor": _metric(
            stable.ledger.surplus_labor(LOCAL_REGION), "ticks"
        ),
        "equilibrium.value_ledger.organic_composition": _metric(
            stable.organic_composition(LOCAL_REGION), "ratio"
        ),
        "equilibrium.value_ledger.value_rate_of_profit": _metric(
            stable.value_rate_of_profit(LOCAL_REGION), "ratio"
        ),
        # The wedge between RimWorld's authored price level and what the
        # model can account for. Reported, not explained.
        "equilibrium.wedge.meals_share_of_price": _metric(
            _wedge_share(stable, LOCAL_REGION, MEALS), "fraction"
        ),
        "equilibrium.wedge.chemfuel_share_of_price": _metric(
            _wedge_share(stable, LOCAL_REGION, CHEMFUEL), "fraction"
        ),
        "equilibrium.wedge.psychoid_leaves_share_of_price": _metric(
            _wedge_share(stable, LOCAL_REGION, LEAVES), "fraction"
        ),
        "equilibrium.wedge.yayo_share_of_price": _metric(
            _wedge_share(stable, LOCAL_REGION, YAYO), "fraction"
        ),
        # Surplus realized in money against surplus produced in labor.
        # They agree for the wage good by construction and diverge
        # elsewhere: the transformation problem, made arithmetic.
        "equilibrium.realized.meals_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, MEALS), "ratio"
        ),
        "equilibrium.realized.yayo_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, YAYO), "ratio"
        ),
        "equilibrium.realized.chemfuel_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, CHEMFUEL), "ratio"
        ),
        "equilibrium.realized.psychoid_leaves_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, LEAVES), "ratio"
        ),
    }


def _wedge_share(economy: Economy, region: str, commodity: str) -> float:
    parts = economy.price_decomposition(region, commodity)
    return parts["margin"] / parts["price"]


def _money_rate(economy: Economy, region: str, commodity: str) -> float:
    """Money surplus over money wages, reading the wedge as surplus."""
    parts = economy.price_decomposition(region, commodity)
    if parts["wages"] <= 0.0:
        return 0.0
    return parts["surplus_if_margin_is_surplus"] / parts["wages"]


def _cheapest_share(economy: Economy, region_name: str, commodity: str) -> float:
    """Realized output share of the lowest-cost producer of a commodity."""
    region = economy.regions[region_name]
    producers = [p for p in region.producers if p.commodity == commodity]
    total = sum(p.last_runs for p in producers)
    if total <= 0.0:
        return 0.0
    cheapest = min(
        producers, key=lambda p: p.effective_unit_cost(region.prices)
    )
    return cheapest.last_runs / total


def _inventory_fraction_of_target(
    economy: Economy, region_name: str, commodity: str
) -> float:
    region = economy.regions[region_name]
    target = (
        region.throughput_demand(commodity)
        * economy.commodities[commodity].target_inventory_days
    )
    if target <= 0.0:
        return 0.0
    return region.inventory[commodity] / target
