"""Reproducible Stage 0 economies and benchmark shocks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .model import Commodity, Economy, Producer, Region, Route


DAYS_PER_YEAR = 60
DAYS_PER_QUADRUM = 15


@dataclass(frozen=True)
class ScenarioParameters:
    reference_price: float = 21.0
    labor_value: float = 11.4
    demand_elasticity: float = 1.35
    target_inventory_days: float = 20.0
    price_adjustment_speed: float = 0.22
    inventory_price_sensitivity: float = 1.05
    minimum_price_factor: float = 0.18
    maximum_price_factor: float = 5.0
    daily_demand: float = 10.0
    initial_cash: float = 100_000.0
    producer_capacity_per_day: float = 10.0
    dust_unit_cost: float = 14.0
    river_unit_cost: float = 14.5
    standard_route_capacity_per_day: float = 1.0
    standard_freight_per_unit: float = 3.5
    standard_travel_days: int = 6
    loss_route_capacity_per_day: float = 1.5
    loss_freight_per_unit: float = 7.0
    loss_travel_days: int = 10
    risk_markup: float = 0.10
    investment_interval_days: int = 15
    investment_lead_days: int = 45
    investment_margin_threshold: float = 0.18
    investment_fraction_of_shortfall: float = 0.45
    zero_utilization_price_ratio: float = 0.70
    full_utilization_price_ratio: float = 1.05
    unmet_demand_price_pressure: float = 2.0
    speculative_inventory_limit: float = 0.50
    expectation_alpha: float = 0.05
    glut_fraction_of_annual_demand: float = 0.25
    producer_loss_fraction: float = 0.60


def drug_commodity(parameters: ScenarioParameters | None = None) -> Commodity:
    parameters = parameters or ScenarioParameters()
    return Commodity(
        "yayo",
        reference_price=parameters.reference_price,
        labor_value=parameters.labor_value,
        demand_elasticity=parameters.demand_elasticity,
        target_inventory_days=parameters.target_inventory_days,
        price_adjustment_speed=parameters.price_adjustment_speed,
        inventory_price_sensitivity=parameters.inventory_price_sensitivity,
        minimum_price_factor=parameters.minimum_price_factor,
        maximum_price_factor=parameters.maximum_price_factor,
    )


def seeded_two_region_economy(
    *,
    route_capacity_per_day: float = 1.0,
    freight_per_unit: float = 3.5,
    travel_days: int = 6,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    parameters = parameters or ScenarioParameters()
    commodity = drug_commodity(parameters)
    daily_demand = parameters.daily_demand
    target = daily_demand * commodity.target_inventory_days
    regions = [
        Region(
            "Dust Basin",
            cash=parameters.initial_cash,
            base_daily_demand={commodity.name: daily_demand},
            inventory={commodity.name: target},
            prices={commodity.name: commodity.reference_price},
            producers=[
                Producer(
                    "Dust cooperative",
                    commodity.name,
                    parameters.producer_capacity_per_day,
                    parameters.dust_unit_cost,
                    parameters.zero_utilization_price_ratio,
                    parameters.full_utilization_price_ratio,
                )
            ],
        ),
        Region(
            "Green River",
            cash=parameters.initial_cash,
            base_daily_demand={commodity.name: daily_demand},
            inventory={commodity.name: target},
            prices={commodity.name: commodity.reference_price},
            producers=[
                Producer(
                    "River works",
                    commodity.name,
                    parameters.producer_capacity_per_day,
                    parameters.river_unit_cost,
                    parameters.zero_utilization_price_ratio,
                    parameters.full_utilization_price_ratio,
                )
            ],
        ),
    ]
    return Economy(
        [commodity],
        regions,
        [
            Route(
                "Dust Basin",
                "Green River",
                freight_per_unit,
                route_capacity_per_day,
                travel_days,
                risk_markup=parameters.risk_markup,
            )
        ],
        investment_interval_days=parameters.investment_interval_days,
        investment_lead_days=parameters.investment_lead_days,
        investment_margin_threshold=parameters.investment_margin_threshold,
        investment_fraction_of_shortfall=(
            parameters.investment_fraction_of_shortfall
        ),
        unmet_demand_price_pressure=parameters.unmet_demand_price_pressure,
        speculative_inventory_limit=parameters.speculative_inventory_limit,
        expectation_alpha=parameters.expectation_alpha,
        zero_utilization_price_ratio=parameters.zero_utilization_price_ratio,
        full_utilization_price_ratio=parameters.full_utilization_price_ratio,
    )


def equilibrium(
    days: int = 240, *, parameters: ScenarioParameters | None = None
) -> Economy:
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(days)
    return economy


def regional_glut(
    days_after_injection: int = 120,
    *,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    region = economy.regions["Dust Basin"]
    annual = region.base_daily_demand["yayo"] * DAYS_PER_YEAR
    economy.inject(
        region.name,
        "yayo",
        annual * parameters.glut_fraction_of_annual_demand,
    )
    economy.step(days_after_injection)
    return economy


def producer_loss(
    days_after_loss: int = 150,
    *,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.loss_route_capacity_per_day,
        freight_per_unit=parameters.loss_freight_per_unit,
        travel_days=parameters.loss_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    economy.destroy_capacity(
        "Dust Basin", "yayo", parameters.producer_loss_fraction
    )
    economy.step(days_after_loss)
    return economy


def arbitrage(
    days_after_shock: int = 90,
    *,
    route_capacity: float | None = None,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    parameters = parameters or ScenarioParameters()
    route_capacity = (
        parameters.standard_route_capacity_per_day
        if route_capacity is None
        else route_capacity
    )
    economy = seeded_two_region_economy(
        route_capacity_per_day=route_capacity,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(30)
    annual = economy.regions["Dust Basin"].base_daily_demand["yayo"] * DAYS_PER_YEAR
    economy.inject(
        "Dust Basin",
        "yayo",
        annual * parameters.glut_fraction_of_annual_demand,
    )
    economy.step(days_after_shock)
    return economy


def summary(economy: Economy) -> Dict[str, object]:
    commodity = economy.commodities["yayo"]
    regions: Dict[str, object] = {}
    for name, region in economy.regions.items():
        price_series = economy.series(name, "yayo")
        minimum_price = min(price_series)
        maximum_price = max(price_series)
        regions[name] = {
            "price": round(region.prices["yayo"], 3),
            "minimum_price": round(minimum_price, 3),
            "minimum_price_day": price_series.index(minimum_price),
            "maximum_price": round(maximum_price, 3),
            "maximum_price_day": price_series.index(maximum_price),
            "labor_value": commodity.labor_value,
            "price_to_labor_value": round(
                region.prices["yayo"] / commodity.labor_value, 3
            ),
            "inventory": round(region.inventory["yayo"], 3),
            "capacity_per_day": round(region.capacity("yayo"), 3),
            "imports": round(region.imported_total["yayo"], 3),
            "exports": round(region.exported_total["yayo"], 3),
        }
    return {
        "day": economy.day,
        "regions": regions,
        "shipments_in_transit": len(economy.shipments),
        "material_residual": round(economy.commodity_balance("yayo"), 9),
        "cash_residual": round(economy.cash_balance(), 9),
    }
