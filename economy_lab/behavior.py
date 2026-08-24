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
    producer_loss,
    regional_glut,
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
    metrics.update(_labor_metrics(stable=stable, glut=glut, loss=loss))
    return metrics


def _employment_series(economy: Economy, region: str) -> list:
    return [h["regions"][region]["employment"] for h in economy.history]


def _labor_metrics(
    *, stable: Economy, glut: Economy, loss: Economy
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
    }
