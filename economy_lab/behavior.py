"""Behavioral observations derived from existing Stage 0 scenario histories."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Iterable

from .model import Economy

from .scenarios import (
    DAYS_PER_QUADRUM,
    MEALS,
    ScenarioParameters,
    arbitrage,
    boom_reversal,
    cash_circuit,
    CHEMFUEL,
    COMPONENTS,
    equilibrium,
    LEAVES,
    cost_competition,
    demand_boom,
    GARMENTS,
    generous_basket,
    input_shortage,
    MEDICINE,
    perishable_meals,
    producer_loss,
    regional_glut,
    reserve_army_sweep,
    reserve_depletion,
    subsistence_shock,
    technique_change,
    wage_slump,
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
    metrics.update(
        _subsistence_basket_metrics(stable=stable, parameters=parameters)
    )
    metrics.update(_turnover_metrics(stable=stable, parameters=parameters))
    metrics.update(_uncovered_scenario_metrics(parameters))
    metrics.update(_capital_goods_metrics(parameters))
    metrics.update(_capacity_exit_metrics(parameters))
    metrics.update(_recreation_basket_metrics(parameters))
    metrics.update(_absolute_rent_metrics(parameters))
    metrics.update(_wage_deviation_metrics(parameters))
    metrics.update(_habituation_metrics(parameters))
    metrics.update(_producer_cash_metrics(parameters))
    metrics.update(_posted_price_metrics(parameters))
    metrics.update(_scale_metrics())
    return metrics


def _capital_goods_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """What Department I changes when the machines become produced (docs/36).

    The headline is `profit_rate`.  Fixed capital had been left out of the
    price system because the machines were exogenous, and docs/30 could only
    report the size of the omission from the *value ledger*, where it was
    3.54% of the advance.  In the price system it is 13.05%, and the rate of
    profit it was hiding is not 3% but 56%.

    Frozen beside it are the two facts that make the number believable: the
    three new sectors move `r` by nothing at all on their own (they are
    non-basic until the plant makes them basic), and Department I is under
    two parts in a thousand of the labor performed.  A change in either
    would mean the fall came from somewhere other than the plant.
    """
    from .scenarios import COMPONENTS, STEEL, WOOD, capital_goods

    economy = capital_goods(parameters=parameters)
    system = economy.prices_of_production()
    region = economy.regions["Dust Basin"]
    direct = sum(
        producer.last_runs * producer.process.direct_labor
        for producer in region.producers
    )
    department_one = sum(
        producer.last_runs * producer.process.direct_labor
        for producer in region.producers
        if producer.commodity in (STEEL, WOOD, COMPONENTS)
    )
    construction = (
        economy.ledger.construction_labor[region.name] / economy.day
    )
    return {
        "capital_goods.production.profit_rate": _metric(
            system["profit_rate"], "ratio"
        ),
        "capital_goods.production.gross_markup": _metric(
            system["gross_markup"], "ratio"
        ),
        "capital_goods.production.fixed_capital_share": _metric(
            system["fixed_capital_share"], "fraction"
        ),
        "capital_goods.production.basics": _metric(
            float(len(system["basics"])), "commodities"
        ),
        # The closed analysis puts components at 5570 embodied ticks and
        # omits the machining table that makes them.  This is that omission,
        # measured one level deeper than docs/23 measured it.
        "capital_goods.value.components": _metric(
            economy.labor_values[COMPONENTS], "ticks"
        ),
        # Pure labor with nothing behind it: these must stay exact, and if
        # they move, fixed capital has leaked into a sector that has none.
        "capital_goods.value.steel": _metric(
            economy.labor_values[STEEL], "ticks"
        ),
        "capital_goods.value.wood": _metric(economy.labor_values[WOOD], "ticks"),
        "capital_goods.department_one.labor_share": _metric(
            (department_one + construction) / direct, "fraction"
        ),
        "capital_goods.department_one.steel_per_day": _metric(
            economy.department_one_output()[STEEL], "units"
        ),
        "capital_goods.advance.fixed_share": _metric(
            economy.capital_advanced()["fixed_capital"]
            / economy.capital_advanced()["total"],
            "fraction",
        ),
    }


def _capacity_exit_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """What competition for survival does to a loss-making sector (docs/38).

    The headline is that it does *not* delete it.  Components lose 6.12
    silver on a 32-silver product, cover none of their maintenance, and shed
    capacity at 1/L a day for about 2,200 days — and then stop, because the
    contraction raised the price until the surviving plant paid for itself.
    The design predicted a cascade that took the rest of Department I with
    it, and the opposite happened.

    `final_capacity` and `final_price` are the rest point.  `coverage` is 1.0
    there by construction and is frozen because it is *why* the decay
    stopped; if it ever drops below 1.0 the sector is decaying again and the
    rest point was not one.
    """
    from .scenarios import COMPONENTS, capacity_exit

    economy = capacity_exit(parameters=parameters)
    region = economy.regions["Dust Basin"]
    machinist = next(
        producer
        for producer in region.producers
        if producer.commodity == COMPONENTS
    )
    return {
        "capacity_exit.components.final_capacity": _metric(
            machinist.capacity_per_day, "units/day"
        ),
        "capacity_exit.components.final_price": _metric(
            region.prices[COMPONENTS], "silver"
        ),
        "capacity_exit.components.coverage": _metric(
            economy.maintenance_coverage(region, machinist), "fraction"
        ),
        # Everything else must be untouched: a sector covering its
        # maintenance replaces its plant and keeps its capacity.
        "capacity_exit.sectors_that_lost_capacity": _metric(
            float(len(economy.ledger.capacity_lost)), "commodities"
        ),
        # The rate of profit is read from the *technique*, which idle
        # capacity does not enter, so shedding it should move nothing.
        "capacity_exit.production.profit_rate": _metric(
            economy.prices_of_production()["profit_rate"], "ratio"
        ),
    }


def _recreation_basket_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """What happens when the workers' basket holds the workers' own product.

    docs/37 section 8 left a standing prediction: if anything ever consumes
    yayo as an input, 89.6% of the fixed capital stops being inert and the
    rate of profit moves a long way.  Half of it was right.  Every commodity
    becomes basic, the inert plant does start to matter — and the rate of
    profit barely notices, because a sector's plant weighs on `r` through
    its plant-to-cost ratio and not through the size of its stock.

    `profit_rate_at_epsilon` is the metric that carries the finding.  At one
    part in four thousand of a yayo per worker-day, every commodity is
    already basic and `r` has moved 0.07%.  Basicness is binary; its
    economic weight is not.  If that number ever moves far from 0.5179 the
    mechanism has changed and docs/41 needs re-deriving.
    """
    from .scenarios import capital_goods, recreation_basket, recreation_sweep

    economy = recreation_basket(parameters=parameters)
    system = economy.prices_of_production()
    epsilon = recreation_sweep(
        quantities=[2.0 ** -12], parameters=parameters
    )[0]
    return {
        "recreation.production.profit_rate": _metric(
            system["profit_rate"], "ratio"
        ),
        "recreation.production.basics": _metric(
            float(len(system["basics"])), "commodities"
        ),
        # The whole argument in one number: every commodity basic, and the
        # rate of profit essentially where it was.
        "recreation.production.profit_rate_at_epsilon": _metric(
            epsilon["profit_rate"], "ratio"
        ),
        "recreation.production.basics_at_epsilon": _metric(
            float(epsilon["basics"]), "commodities"
        ),
        "recreation.wage_per_worker_day": _metric(
            economy.regions["Dust Basin"].wage_rate(), "silver"
        ),
        # Labor-power got dearer against an unchanged working day.
        "recreation.rate_of_surplus_value": _metric(
            economy.rate_of_surplus_value(), "ratio"
        ),
        # For the comparison the two above are only meaningful against.
        "recreation.baseline_profit_rate": _metric(
            capital_goods(parameters=parameters)
            .prices_of_production()["profit_rate"],
            "ratio",
        ),
    }


def _absolute_rent_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """Marx's condition for absolute rent, measured (docs/42, docs/43).

    The account rests on a below-average organic composition implying a
    value above the price of production.  In a circulating-capital economy
    that holds exactly; fixed capital breaks it, and
    `deviation_monotone_without_plant` against
    `deviation_monotone_with_plant` is that result in two bits.

    `deviations_sum` is the invariant behind all of it: redistribution
    through the price system creates no value, so the output-weighted
    deviations cancel.  If that ever leaves float noise, the two systems are
    not being read in one numeraire and every comparison here is void.
    """
    from .scenarios import CHEMFUEL, capital_goods, equilibrium

    def monotone(economy):
        composition = economy.sector_organic_composition()
        prices = economy.prices_of_production()["prices"]
        rows = sorted(
            (composition[name], prices[name] / economy.labor_values[name])
            for name in composition
        )
        return all(a[1] <= b[1] for a, b in zip(rows, rows[1:]))

    plain = equilibrium(parameters=parameters)
    plant = capital_goods(parameters=parameters)
    deviation = plant.price_value_deviation()
    _, _, output = plant.social_technique()
    total = sum(output[name] * deviation[name] for name in deviation)
    value = sum(output[name] * plant.labor_values[name] for name in deviation)
    prices = plant.prices_of_production()["prices"]
    return {
        "rent.deviation_monotone_without_plant": _metric(
            1.0 if monotone(plain) else 0.0, "boolean"
        ),
        "rent.deviation_monotone_with_plant": _metric(
            1.0 if monotone(plant) else 0.0, "boolean"
        ),
        "rent.deviations_sum_over_value": _metric(total / value, "fraction"),
        # The ceiling on absolute rent: what the price system takes away
        # from the one sector that has a landlord.
        "rent.chemfuel_bound_share_of_value": _metric(
            1.0 - prices[CHEMFUEL] / plant.labor_values[CHEMFUEL], "fraction"
        ),
        "rent.chemfuel_bound_ticks_per_day": _metric(
            plant.absolute_rent_bound()[CHEMFUEL], "ticks/day"
        ),
        "rent.chemfuel_organic_composition": _metric(
            plant.sector_organic_composition()[CHEMFUEL], "ratio"
        ),
    }


def _premium_series(economy: Economy, region: str) -> list:
    return [h["regions"][region]["wage_premium"] for h in economy.history]


def _wage_deviation_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """Wages off the value of labor-power (docs/46, docs/47).

    The reserve-army rule is off by default, so nothing here is a change to
    existing behavior; these are the readings the rule exists to produce,
    each a difference between the same shock run with and without it.  The
    value of labor-power is read in both runs and the *gap* is frozen,
    because the whole account rests on the wage moving while the value does
    not: if that gap ever grows past float noise, the premium has reached
    the value solve and docs/46 section 7 says what that means.
    """
    without = demand_boom(parameters=parameters)
    with_rule = demand_boom(bargaining=True, parameters=parameters)
    slump = wage_slump(parameters=parameters)
    sweep = reserve_army_sweep(pools=(0.5, float("inf")), parameters=parameters)
    stationary = equilibrium(
        parameters=replace(
            parameters,
            wage_bargaining_strength=parameters.bargaining_scenario_strength,
        )
    )

    off_region = without.regions[LOCAL_REGION]
    on_region = with_rule.regions[LOCAL_REGION]
    premium = _premium_series(with_rule, LOCAL_REGION)
    employment = _employment_series(with_rule, LOCAL_REGION)
    slump_premium = _premium_series(slump, LOCAL_REGION)
    value_off = without.basket_labor_value(off_region)
    value_on = with_rule.basket_labor_value(on_region)
    half = max(_premium_series(sweep[0.5], LOCAL_REGION))
    stationary_prices = stationary.series(LOCAL_REGION, YAYO)

    def wage_cost(economy: Economy, commodity: str) -> float:
        region = economy.regions[LOCAL_REGION]
        producers = [
            p for p in region.producers if p.active and p.commodity == commodity
        ]
        return producers[0].wage_cost_per_unit

    return {
        # The rule on, and the seeded circuit still exactly stationary.
        "bargaining.equilibrium.premium_max_abs": _metric(
            max(abs(x) for x in _premium_series(stationary, LOCAL_REGION)),
            "fraction",
        ),
        "bargaining.equilibrium.price_range": _metric(
            max(stationary_prices) - min(stationary_prices), "silver"
        ),
        # --- the boom: wages above value ---------------------------------
        "bargaining.boom.premium_peak": _metric(max(premium), "fraction"),
        "bargaining.boom.premium_peak_day": _metric(
            premium.index(max(premium)), "day"
        ),
        "bargaining.boom.employment_peak_day": _metric(
            employment.index(max(employment)), "day"
        ),
        "bargaining.boom.employment_end_with_rule": _metric(
            on_region.worker_days_earned, "worker-days"
        ),
        "bargaining.boom.employment_end_without_rule": _metric(
            off_region.worker_days_earned, "worker-days"
        ),
        # The wage moved; the value did not.  Frozen as the relative gap.
        "bargaining.boom.value_of_labor_power_gap": _metric(
            abs(value_on - value_off) / value_off, "fraction"
        ),
        "bargaining.boom.rate_of_surplus_value": _metric(
            with_rule.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "bargaining.boom.realized_rate_of_surplus_value": _metric(
            with_rule.realized_rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        # Cost-push against the price actually reached: the premium's
        # effect on the meal's *wage cost* is a fraction of a percent, and
        # the meal price moves by far more, because workers paid above
        # value eat more meals (docs/47).
        "bargaining.boom.meals_price_end_with_rule": _metric(
            on_region.prices[MEALS], "silver"
        ),
        "bargaining.boom.meals_price_end_without_rule": _metric(
            off_region.prices[MEALS], "silver"
        ),
        "bargaining.boom.meals_wage_cost_gain": _metric(
            wage_cost(with_rule, MEALS) - wage_cost(without, MEALS), "silver"
        ),
        "bargaining.boom.worker_cash_ratio": _metric(
            on_region.worker_cash / off_region.worker_cash, "ratio"
        ),
        # --- the slump: wages below value --------------------------------
        "bargaining.slump.premium_trough": _metric(
            min(slump_premium), "fraction"
        ),
        "bargaining.slump.premium_trough_day": _metric(
            slump_premium.index(min(slump_premium)), "day"
        ),
        "bargaining.slump.premium_end": _metric(
            slump_premium[-1], "fraction"
        ),
        "bargaining.slump.deviation_labor": _metric(
            slump.ledger.wage_deviation_labor.get(LOCAL_REGION, 0.0), "ticks"
        ),
        "bargaining.slump.realized_rate_of_surplus_value": _metric(
            slump.realized_rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        # --- the reserve army sets the magnitude -------------------------
        "bargaining.reserve_army.premium_peak_at_half_pool": _metric(
            half, "fraction"
        ),
        "bargaining.reserve_army.premium_ratio_half_to_full": _metric(
            half / max(premium), "ratio"
        ),
        "bargaining.reserve_army.premium_peak_at_infinite_pool": _metric(
            max(abs(x) for x in _premium_series(sweep[float("inf")], LOCAL_REGION)),
            "fraction",
        ),
    }


def _scale_series(economy: Economy, region: str) -> list:
    return [h["regions"][region]["habitual_scale"] for h in economy.history]


def _habituation_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """A sustained premium becoming the value of labor-power (docs/51).

    Off by default, so every reading here is the rule's own.  Each boom
    figure is read against the bargaining-only run of the same shock: the
    claim is that the wage as paid is the same wage and the value moved,
    which is the mirror of docs/46's claim, and the reversal readings
    freeze the ordering the upward-only rule produces -- a wage below value
    in a region that is not in crisis.
    """
    bargaining = demand_boom(bargaining=True, parameters=parameters)
    habituated = demand_boom(habituation=True, parameters=parameters)
    reversal = boom_reversal(habituation=True, parameters=parameters)
    reversal_without = boom_reversal(habituation=False, parameters=parameters)
    stationary = equilibrium(
        parameters=replace(
            parameters,
            wage_bargaining_strength=parameters.bargaining_scenario_strength,
            habituation_speed=parameters.habituation_scenario_speed,
        )
    )

    bargained = bargaining.regions[LOCAL_REGION]
    habit = habituated.regions[LOCAL_REGION]
    scale = _scale_series(habituated, LOCAL_REGION)
    premium = _premium_series(habituated, LOCAL_REGION)
    reversal_scale = _scale_series(reversal, LOCAL_REGION)
    reversal_day = parameters.boom_reversal_day
    stationary_prices = stationary.series(LOCAL_REGION, YAYO)
    without_region = reversal_without.regions[LOCAL_REGION]

    return {
        # Both rules on, and the seeded circuit still exactly stationary.
        "habituation.equilibrium.scale_max_deviation": _metric(
            max(abs(x - 1.0) for x in _scale_series(stationary, LOCAL_REGION)),
            "fraction",
        ),
        "habituation.equilibrium.price_range": _metric(
            max(stationary_prices) - min(stationary_prices), "silver"
        ),
        # --- the boom: the standard follows the premium -------------------
        "habituation.boom.scale_end": _metric(scale[-1], "ratio"),
        # Never above one plus the highest premium seen: zero or negative.
        "habituation.boom.scale_overshoot": _metric(
            max(scale) - (1.0 + max(premium)), "fraction"
        ),
        "habituation.boom.premium_end": _metric(premium[-1], "fraction"),
        "habituation.boom.premium_over_value_end": _metric(
            habit.premium_over_value(), "fraction"
        ),
        # The value moved and the wage did not, each as a ratio to the
        # bargaining-only run of the same shock.
        "habituation.boom.value_of_labor_power_ratio": _metric(
            habituated.value_of_labor_power(habit)
            / bargaining.value_of_labor_power(bargained),
            "ratio",
        ),
        "habituation.boom.wage_rate_ratio": _metric(
            habit.wage_rate() / bargained.wage_rate(), "ratio"
        ),
        "habituation.boom.rate_of_surplus_value": _metric(
            habituated.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "habituation.boom.realized_rate_of_surplus_value": _metric(
            habituated.realized_rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        # The standard is the long-run real wage the price system reads.
        "habituation.boom.production.profit_rate": _metric(
            habituated.prices_of_production()["profit_rate"], "ratio"
        ),
        "habituation.boom.meals_price_end": _metric(
            habit.prices[MEALS], "silver"
        ),
        # --- the reversal: the wage falls back and the standard does not --
        "habituation.reversal.scale_end": _metric(reversal_scale[-1], "ratio"),
        "habituation.reversal.scale_moved_after_reversal": _metric(
            reversal_scale[-1] - reversal_scale[reversal_day], "fraction"
        ),
        "habituation.reversal.premium_end": _metric(
            reversal.regions[LOCAL_REGION].wage_premium, "fraction"
        ),
        "habituation.reversal.premium_over_value_end": _metric(
            reversal.regions[LOCAL_REGION].premium_over_value(), "fraction"
        ),
        "habituation.reversal.rate_of_surplus_value": _metric(
            reversal.rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        "habituation.reversal.realized_rate_of_surplus_value": _metric(
            reversal.realized_rate_of_surplus_value(LOCAL_REGION), "ratio"
        ),
        # Without the rule the two rates meet again once the premium is
        # gone; frozen so the contrast is a number.
        "habituation.reversal.rate_gap_without_rule": _metric(
            abs(
                reversal_without.realized_rate_of_surplus_value(LOCAL_REGION)
                - reversal_without.rate_of_surplus_value(LOCAL_REGION)
            ),
            "ratio",
        ),
        "habituation.reversal.premium_end_without_rule": _metric(
            without_region.wage_premium, "fraction"
        ),
    }


def _producer_cash_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """Producers hold silver, pay from it, and can fail (docs/55).

    Off by default, so every reading here is the rule's own.  The
    equilibrium readings freeze that a purse is exactly stationary and
    that the money profit which now flows is the notional the price
    decomposition has printed since docs/23.  The cash-circuit readings
    freeze what the liquidity ration does to the one sector that sells
    below its cash cost, and that it does nothing to anyone else.
    """
    with_cash = replace(parameters, producer_cash=True)
    stationary = equilibrium(parameters=with_cash)
    circuit = cash_circuit(parameters=parameters)
    boom_with = demand_boom(parameters=with_cash)
    boom_without = demand_boom(parameters=parameters)

    region = stationary.regions[LOCAL_REGION]
    purses = [h["regions"][LOCAL_REGION]["producer_cash"] for h in stationary.history]
    fund = [h["regions"][LOCAL_REGION]["cash"] for h in stationary.history]
    prices = stationary.series(LOCAL_REGION, YAYO)
    days = stationary.day

    def notional_gap() -> float:
        worst = 0.0
        for producer in region.producers:
            parts = stationary.price_decomposition(LOCAL_REGION, producer.commodity)
            output = producer.last_runs * producer.process.outputs[producer.commodity]
            notional = output * (parts["price"] - parts["inputs"] - parts["wages"])
            flow = producer.distributed_total / days
            worst = max(worst, abs(flow - notional))
        return worst

    circuit_region = circuit.regions[LOCAL_REGION]
    machinist = next(p for p in circuit_region.producers if p.commodity == COMPONENTS)
    component_prices = circuit.series(LOCAL_REGION, COMPONENTS)
    authored = circuit.commodities[COMPONENTS].reference_price
    first_move = next(
        (day for day, price in enumerate(component_prices) if price != authored),
        -1,
    )
    others_below_target = sum(
        1
        for p in circuit_region.producers
        if p.active and p.commodity != COMPONENTS and p.cash < p.cash_target
    )
    circuit_yayo = circuit.series(LOCAL_REGION, YAYO)

    return {
        # --- the seeded circuit with purses: exactly stationary ----------
        "producer_cash.equilibrium.price_range": _metric(
            max(prices) - min(prices), "silver"
        ),
        "producer_cash.equilibrium.purse_max_deviation": _metric(
            max(abs(x - purses[1]) for x in purses[1:]), "silver"
        ),
        "producer_cash.equilibrium.fund_drift": _metric(fund[-1] - fund[0], "silver"),
        "producer_cash.equilibrium.liquidity_curtailment": _metric(
            sum(stationary.ledger.liquidity_curtailment.values()), "runs"
        ),
        # Money profit as a flow against the notional per-unit margin.
        "producer_cash.equilibrium.distribution_gap_to_notional": _metric(
            notional_gap(), "silver/day"
        ),
        "producer_cash.equilibrium.distributed_per_day": _metric(
            stationary.ledger.distributions.get(LOCAL_REGION, 0.0) / days, "silver"
        ),
        # --- Department I with purses: the sector that does not pay ------
        "producer_cash.circuit.components.price_first_move_day": _metric(
            first_move, "day"
        ),
        "producer_cash.circuit.components.price_end_over_authored": _metric(
            component_prices[-1] / authored, "ratio"
        ),
        "producer_cash.circuit.components.price_peak_over_authored": _metric(
            max(component_prices) / authored, "ratio"
        ),
        "producer_cash.circuit.components.purse_end": _metric(machinist.cash, "silver"),
        "producer_cash.circuit.components.utilization_end": _metric(
            machinist.last_runs / machinist.process.runs_for(machinist.capacity_per_day),
            "fraction",
        ),
        "producer_cash.circuit.components.capacity_end": _metric(
            machinist.capacity_per_day, "units/day"
        ),
        "producer_cash.circuit.liquidity_curtailment": _metric(
            sum(circuit.ledger.liquidity_curtailment.values()), "runs"
        ),
        "producer_cash.circuit.bankruptcies": _metric(
            float(len(circuit.ledger.bankruptcies)), "producers"
        ),
        "producer_cash.circuit.sectors_that_lost_capacity": _metric(
            float(len(circuit.ledger.capacity_lost)), "commodities"
        ),
        "producer_cash.circuit.other_purses_below_target": _metric(
            float(others_below_target), "producers"
        ),
        "producer_cash.circuit.yayo_price_range": _metric(
            max(circuit_yayo) - min(circuit_yayo), "silver"
        ),
        "producer_cash.circuit.employment_end": _metric(
            circuit_region.worker_days_earned, "worker-days"
        ),
        # --- the boom, funded by the owners' fund --------------------------
        "producer_cash.boom.employment_gap": _metric(
            boom_with.regions[LOCAL_REGION].worker_days_earned
            - boom_without.regions[LOCAL_REGION].worker_days_earned,
            "worker-days",
        ),
        "producer_cash.boom.fund_min": _metric(
            min(h["regions"][LOCAL_REGION]["cash"] for h in boom_with.history),
            "silver",
        ),
    }


def _posted_price_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """Firm-posted prices, off by default and experimental (docs/57, docs/58).

    What is frozen is what the rule does and does not do: it is exactly
    stationary, it passes cost through in full with every sector's markup
    preserved, and it leaves every shock's price level where the shock put
    it, because an integrated pressure has no restoring force and a shared
    pool gives a contested sector the wrong signal.  docs/58 records why
    the second and third are findings about the pool, and docs/59 is the
    consequence.
    """
    posted = replace(parameters, posted_prices=True)
    stationary = equilibrium(parameters=posted)
    glut = regional_glut(parameters=posted)
    loss = producer_loss(parameters=posted)
    shock = subsistence_shock(parameters=posted)
    technique = technique_change(parameters=posted)
    competition = cost_competition(parameters=posted)

    def markups(economy: Economy) -> Dict[str, float]:
        region = economy.regions[LOCAL_REGION]
        return {
            p.commodity: p.posted_price / p.effective_unit_cost(region.prices)
            for p in region.producers
            if p.active
        }

    seeded = markups(stationary)
    shocked = markups(shock)
    preserved = max(
        abs(shocked[name] - seeded[name])
        for name in seeded
        if name != MEALS
    )
    stationary_prices = stationary.series(LOCAL_REGION, YAYO)
    reference = parameters.reference_price

    def spread(economy: Economy) -> float:
        asked = [
            p.posted_price
            for p in economy.regions[LOCAL_REGION].producers
            if p.active and p.commodity == MEALS
        ]
        return max(asked) / min(asked) - 1.0

    return {
        "posted.equilibrium.price_range": _metric(
            max(stationary_prices) - min(stationary_prices), "silver"
        ),
        "posted.equilibrium.yayo_markup": _metric(seeded[YAYO], "ratio"),
        # Cost passes through in full: after the subsistence shock every
        # sector but the shocked one asks the same markup it was seeded at.
        "posted.subsistence.markup_max_drift": _metric(preserved, "ratio"),
        "posted.subsistence.meals_markup_end": _metric(shocked[MEALS], "ratio"),
        "posted.subsistence.yayo_price_end": _metric(
            shock.regions[LOCAL_REGION].prices[YAYO], "silver"
        ),
        # A shock's level is permanent: an integrated pressure rests where
        # the stock reaches its target, not where it started.
        "posted.glut.trough_over_reference": _metric(
            min(glut.series(LOCAL_REGION, YAYO)) / reference, "ratio"
        ),
        "posted.glut.end_over_reference": _metric(
            glut.series(LOCAL_REGION, YAYO)[-1] / reference, "ratio"
        ),
        "posted.producer_loss.peak_over_reference": _metric(
            max(loss.series(LOCAL_REGION, YAYO)) / reference, "ratio"
        ),
        "posted.producer_loss.end_over_reference": _metric(
            loss.series(LOCAL_REGION, YAYO)[-1] / reference, "ratio"
        ),
        # A contested sector on one pool does not converge.
        "posted.technique_change.meals_posted_spread": _metric(
            spread(technique), "ratio"
        ),
        "posted.cost_competition.meals_posted_spread": _metric(
            spread(competition), "ratio"
        ),
        "posted.cost_competition.meals_price_end": _metric(
            competition.regions[LOCAL_REGION].prices[MEALS], "silver"
        ),
    }


def _uncovered_scenario_metrics(
    parameters: ScenarioParameters,
) -> Dict[str, Dict[str, object]]:
    """Cover the two scenarios no metric had been reading.

    The sensitivity sweep reports a parameter that moves nothing as inert,
    and that is a claim about the model.  It is only true if some metric
    could have seen the parameter move.  `subsistence_shock` and
    `input_shortage` were never collected, so `subsistence_loss_fraction`
    scored zero because nothing was looking — a false zero wearing the same
    clothes as a finding.

    Two readings each, chosen as the thing the scenario exists to show:
    the wage-push channel for the subsistence shock, and the downstream
    propagation of an upstream loss for the input shortage.
    """
    shock = subsistence_shock(parameters=parameters)
    shortage = input_shortage(parameters=parameters)

    shock_region = shock.regions[LOCAL_REGION]
    meal_prices = shock.series(LOCAL_REGION, MEALS)
    after = meal_prices[SHOCK_DAY + 1 :]
    basket_shortfall = sum(shock.ledger.basket_shortfall.values())

    yayo_prices = shortage.series(LOCAL_REGION, COMMODITY)
    leaf_prices = shortage.series(LOCAL_REGION, LEAVES)

    return {
        # Meal scarcity raises the meal price; the wage is the basket at
        # current prices, so it follows.
        "subsistence_shock.local.meals.price_peak": _metric(
            max(after), "silver"
        ),
        "subsistence_shock.local.wage_rate": _metric(
            shock_region.wage_rate(), "silver"
        ),
        # Labor-power paid below its reproduction cost, made visible.
        "subsistence_shock.basket_shortfall": _metric(
            basket_shortfall, "units"
        ),
        "subsistence_shock.terminal_meal_price": _metric(
            meal_prices[-1], "silver"
        ),
        # An upstream loss has to reach the downstream price or the
        # propagation the scenario exists to show is not happening.
        "input_shortage.local.psychoid_leaves.price_peak": _metric(
            max(leaf_prices[SHOCK_DAY + 1 :]), "silver"
        ),
        "input_shortage.local.yayo.price_peak": _metric(
            max(yayo_prices[SHOCK_DAY + 1 :]), "silver"
        ),
        "input_shortage.terminal_yayo_price": _metric(
            yayo_prices[-1], "silver"
        ),
    }


def _scale_metrics() -> Dict[str, Dict[str, object]]:
    """Structural facts about the scale harness (docs/32, docs/33).

    Timings are deliberately *not* frozen: they are machine-dependent and a
    reference that moves with the hardware is a reference nobody trusts.
    What is frozen is what the harness proves — that the value solve, run
    at six hundred commodities rather than four, still reproduces the
    closed analysis exactly wherever the generator did not contradict it.
    """
    from .scale import population, synthetic_economy

    economy = synthetic_economy(commodities=653, regions=2)
    economy.step(1)
    record = economy.scale_record
    floored = set(record["floored"])
    processes = {
        producer.commodity: producer.process
        for producer in economy.regions["region_000"].producers
    }

    def tainted(name, seen=None):
        seen = set() if seen is None else seen
        if name in seen:
            return False
        seen.add(name)
        return any(
            other in floored or tainted(other, seen)
            for other in processes[name].inputs
        )

    exact = comparable = 0
    for name, authored in sorted(record["labor"].items()):
        if name in floored or authored <= 0.0 or tainted(name):
            continue
        comparable += 1
        if abs(economy.labor_values[name] - authored) / authored < 1e-9:
            exact += 1
    return {
        "scale.population_commodities": _metric(
            float(len(population())), "commodities"
        ),
        "scale.floored_direct_labor": _metric(float(len(floored)), "commodities"),
        "scale.value_solve_comparable": _metric(float(comparable), "commodities"),
        "scale.value_solve_exact": _metric(float(exact), "commodities"),
        "scale.value_solve_exact_share": _metric(
            exact / max(comparable, 1), "fraction"
        ),
    }


def _turnover_metrics(
    *, stable: Economy, parameters: ScenarioParameters
) -> Dict[str, Dict[str, object]]:
    """Observe capital advanced against capital consumed (docs/30).

    The two that carry the session's result are `realized_days` — how long
    the circuit actually ties its capital up, against the 21 the price
    system assumes — and `rate_of_profit_on_advances`, which is the rate of
    profit the flow ratio beside it is not.
    """
    advanced = stable.capital_advanced()
    held = {
        name: sum(region.inventory[name] for region in stable.regions.values())
        * stable.labor_values[name]
        for name in stable.commodities
    }
    perishable = perishable_meals(parameters=parameters)
    system = perishable.prices_of_production(numeraire=MEALS)
    base = system["prices"][MEALS]
    return {
        "equilibrium.turnover.realized_days": _metric(
            stable.realized_turnover_days(), "days"
        ),
        "equilibrium.advance.total_ticks": _metric(advanced["total"], "ticks"),
        "equilibrium.advance.commodity_share": _metric(
            advanced["commodity_capital"] / advanced["total"], "fraction"
        ),
        "equilibrium.advance.fixed_share": _metric(
            advanced["fixed_capital"] / advanced["total"], "fraction"
        ),
        "equilibrium.advance.wage_share": _metric(
            advanced["wage_advance"] / advanced["total"], "fraction"
        ),
        # Yayo is nobody's input, so its stock is capital advanced that no
        # cost flow ever sees. It is also the largest block of it.
        "equilibrium.advance.yayo_share_of_stock": _metric(
            held[YAYO] / sum(held.values()), "fraction"
        ),
        "equilibrium.value_ledger.rate_of_profit_on_advances": _metric(
            stable.value_rate_of_profit_on_advances(), "ratio"
        ),
        # Differential turnover, which is the only kind that moves a price.
        "perishable_meals.production.profit_rate_per_period": _metric(
            system["profit_rate"], "ratio"
        ),
        "perishable_meals.production.gross_markup": _metric(
            system["gross_markup"], "ratio"
        ),
        "perishable_meals.production.yayo_relative_to_meals": _metric(
            system["prices"][YAYO] / base, "ratio"
        ),
        "perishable_meals.production.garments_relative_to_meals": _metric(
            system["prices"][GARMENTS] / base, "ratio"
        ),
        "perishable_meals.local.meals.settled_inventory": _metric(
            perishable.regions[LOCAL_REGION].inventory[MEALS], "units"
        ),
        "perishable_meals.value_ledger.rate_of_profit_on_advances": _metric(
            perishable.value_rate_of_profit_on_advances(), "ratio"
        ),
    }


def _subsistence_basket_metrics(
    *, stable: Economy, parameters: ScenarioParameters
) -> Dict[str, Dict[str, object]]:
    """Observe the enlarged subsistence basket (docs/28).

    The two that carry the session's result are
    `basket.share_of_working_day` — necessary labor as a fraction of the
    day, which is what every ratio built on `v` inverts — and
    `generous_basket.rate_of_surplus_value`, which bounds from above what
    any defensible bundle could achieve.
    """
    region = stable.regions[LOCAL_REGION]
    basket = region.subsistence_basket
    embodied = stable.basket_labor_value(region)
    generous = generous_basket(parameters=parameters)
    return {
        "equilibrium.basket.commodities": _metric(float(len(basket)), "count"),
        "equilibrium.basket.labor_ticks": _metric(embodied, "ticks"),
        "equilibrium.basket.share_of_working_day": _metric(
            embodied / region.ticks_per_worker_day, "fraction"
        ),
        "equilibrium.basket.money_cost": _metric(region.wage_rate(), "silver"),
        "equilibrium.basket.meals_share_of_money": _metric(
            basket[MEALS] * region.prices[MEALS] / region.wage_rate(), "fraction"
        ),
        "equilibrium.basket.meals_share_of_labor": _metric(
            basket[MEALS] * stable.labor_values[MEALS] / embodied, "fraction"
        ),
        # How many workers one provisioner's day feeds. The sentence the
        # whole session reduces to, as a number.
        "equilibrium.basket.workers_fed_per_provisioner_day": _metric(
            region.ticks_per_worker_day
            / (basket[MEALS] * stable.labor_values[MEALS]),
            "workers",
        ),
        "generous_basket.rate_of_surplus_value": _metric(
            generous.rate_of_surplus_value(), "ratio"
        ),
        "generous_basket.organic_composition": _metric(
            generous.organic_composition(), "ratio"
        ),
        "generous_basket.value_rate_of_profit": _metric(
            generous.value_rate_of_profit(), "ratio"
        ),
        "generous_basket.production.gross_markup": _metric(
            generous.prices_of_production()["gross_markup"], "ratio"
        ),
        "generous_basket.basket.share_of_working_day": _metric(
            generous.basket_labor_value(generous.regions[LOCAL_REGION])
            / generous.regions[LOCAL_REGION].ticks_per_worker_day,
            "fraction",
        ),
    }


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
        # Renamed at docs/30: this is the factor by which price exceeds
        # cost, not a rate of profit. The rate is the markup spread over
        # the turnover time, and is reported beside it.
        "equilibrium.production.gross_markup": _metric(
            system["gross_markup"], "ratio"
        ),
        "equilibrium.production.profit_rate_per_period": _metric(
            system["profit_rate"], "ratio"
        ),
        "equilibrium.production.assumed_turnover_days": _metric(
            system["turnover_days"][MEALS], "days"
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
        "equilibrium.production.garments_relative_to_meals": _metric(
            relative(GARMENTS), "ratio"
        ),
        "equilibrium.production.herbal_medicine_relative_to_meals": _metric(
            relative(MEDICINE), "ratio"
        ),
        "equilibrium.production.garments_over_value_ratio": _metric(
            relative(GARMENTS) / value_ratio(GARMENTS), "ratio"
        ),
        "equilibrium.production.herbal_medicine_over_value_ratio": _metric(
            relative(MEDICINE) / value_ratio(MEDICINE), "ratio"
        ),
        # The rank-one rate: what r would be if no wage good had material
        # inputs. It did until docs/28, which is why r was exactly s/v.
        "equilibrium.production.rank_one_gross_markup": _metric(
            _rank_one_gross_markup(stable), "ratio"
        ),
        "equilibrium.production.markup_over_rank_one": _metric(
            system["gross_markup"] / _rank_one_gross_markup(stable), "ratio"
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
        "technique_change.production.gross_markup": _metric(
            changed["gross_markup"], "ratio"
        ),
        "technique_change.production.gross_markup_gain": _metric(
            changed["gross_markup"] / system["gross_markup"], "ratio"
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
        # The two new wage goods straddle the labor-time rate, which is
        # what dissolves docs/24's "agreement by construction" for meals.
        "equilibrium.realized.garments_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, GARMENTS), "ratio"
        ),
        "equilibrium.realized.herbal_medicine_money_rate": _metric(
            _money_rate(stable, LOCAL_REGION, MEDICINE), "ratio"
        ),
    }


def _rank_one_gross_markup(economy: Economy) -> float:
    """`T / sum(b*l) - 1`: the gross markup with pure-labor wage goods.

    With no material inputs to any wage good the augmented matrix
    restricted to the basket is the outer product `(l/T) . b`, whose only
    non-zero eigenvalue is `sum(b*l)/T`.  That is why `r` was exactly the
    rate of surplus value before docs/28, and the distance from it is how
    much the general Sraffa case departs from the corn model.
    """
    region = economy.regions[LOCAL_REGION]
    _, labor, _ = economy.social_technique()
    embodied = sum(
        quantity * labor[name]
        for name, quantity in sorted(region.subsistence_basket.items())
        if quantity > 0.0
    )
    return region.ticks_per_worker_day / embodied - 1.0


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
