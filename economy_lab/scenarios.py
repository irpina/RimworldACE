"""Reproducible Stage 0 economies and benchmark shocks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .model import Commodity, Economy, Producer, Region, Route


DAYS_PER_YEAR = 60
DAYS_PER_QUADRUM = 15


def drug_commodity() -> Commodity:
    return Commodity(
        "yayo",
        reference_price=21.0,
        labor_value=11.4,
        demand_elasticity=1.35,
        target_inventory_days=20.0,
        price_adjustment_speed=0.22,
        inventory_price_sensitivity=1.05,
        minimum_price_factor=0.18,
        maximum_price_factor=5.0,
    )


def seeded_two_region_economy(
    *,
    route_capacity_per_day: float = 1.0,
    freight_per_unit: float = 3.5,
    travel_days: int = 6,
) -> Economy:
    commodity = drug_commodity()
    daily_demand = 10.0
    target = daily_demand * commodity.target_inventory_days
    regions = [
        Region(
            "Dust Basin",
            cash=100_000.0,
            base_daily_demand={commodity.name: daily_demand},
            inventory={commodity.name: target},
            prices={commodity.name: commodity.reference_price},
            producers=[
                Producer("Dust cooperative", commodity.name, 10.0, 14.0)
            ],
        ),
        Region(
            "Green River",
            cash=100_000.0,
            base_daily_demand={commodity.name: daily_demand},
            inventory={commodity.name: target},
            prices={commodity.name: commodity.reference_price},
            producers=[
                Producer("River works", commodity.name, 10.0, 14.5)
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
                risk_markup=0.10,
            )
        ],
    )


def equilibrium(days: int = 240) -> Economy:
    economy = seeded_two_region_economy()
    economy.step(days)
    return economy


def regional_glut(days_after_injection: int = 120) -> Economy:
    economy = seeded_two_region_economy()
    economy.step(60)
    region = economy.regions["Dust Basin"]
    annual = region.base_daily_demand["yayo"] * DAYS_PER_YEAR
    economy.inject(region.name, "yayo", annual * 0.25)
    economy.step(days_after_injection)
    return economy


def producer_loss(days_after_loss: int = 150) -> Economy:
    economy = seeded_two_region_economy(
        route_capacity_per_day=1.5,
        freight_per_unit=7.0,
        travel_days=10,
    )
    economy.step(60)
    economy.destroy_capacity("Dust Basin", "yayo", 0.60)
    economy.step(days_after_loss)
    return economy


def arbitrage(days_after_shock: int = 90, *, route_capacity: float = 1.0) -> Economy:
    economy = seeded_two_region_economy(route_capacity_per_day=route_capacity)
    economy.step(30)
    annual = economy.regions["Dust Basin"].base_daily_demand["yayo"] * DAYS_PER_YEAR
    economy.inject("Dust Basin", "yayo", annual * 0.25)
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
