"""Reproducible Stage 0 economies and benchmark shocks.

The circuit is three commodities deep and forks:

    chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
               └────────────────────────────────────────────^

Chemfuel is consumed by *two* producers, so a chemfuel shortage forces a
contention decision; psychoid leaves sit between two stages, so a shortage has
to travel. A pure linear chain would exercise neither.

Per-unit ratios and reference prices come from RimWorld's own defs; the one
stylized link (chemfuel as an operating input) is flagged in
`docs/08-accounted-input-design.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .model import Commodity, Economy, Process, Producer, Region, Route


DAYS_PER_YEAR = 60
DAYS_PER_QUADRUM = 15

YAYO = "yayo"
LEAVES = "psychoid_leaves"
CHEMFUEL = "chemfuel"


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
    replenishment_rate: float = 0.10
    construction_cost_multiplier: float = 60.0
    min_investment_capacity: float = 0.1
    glut_fraction_of_annual_demand: float = 0.25
    producer_loss_fraction: float = 0.60

    # --- accounted input-output production ---------------------------------
    # Reference prices are RimWorld MarketValue; masses are the Mass stat;
    # leaves-per-yayo is Yayo's costList. Direct labor is work-ticks from
    # out/embodied_labor.csv. The chemfuel input ratios are stylized.
    leaves_reference_price: float = 1.9
    chemfuel_reference_price: float = 2.3
    leaves_per_yayo: float = 8.0
    chemfuel_per_yayo: float = 0.2
    chemfuel_per_leaf: float = 0.05
    yayo_direct_labor: float = 350.0
    leaves_direct_labor: float = 46.2
    chemfuel_direct_labor: float = 25.0
    yayo_mass: float = 0.05
    leaves_mass: float = 0.03
    chemfuel_mass: float = 0.05
    # Labor values are display-only in this slice. They are the yayo
    # placeholder's own scale (11.4 silver per 720 embodied ticks) applied to
    # each commodity's embodied ticks, so the three are at least mutually
    # consistent. Propagating labor value through processes is a later slice.
    leaves_labor_value: float = 0.7315
    chemfuel_labor_value: float = 0.395833

    @property
    def leaves_capacity_per_day(self) -> float:
        return self.producer_capacity_per_day * self.leaves_per_yayo

    @property
    def chemfuel_capacity_per_day(self) -> float:
        return (
            self.leaves_capacity_per_day * self.chemfuel_per_leaf
            + self.producer_capacity_per_day * self.chemfuel_per_yayo
        )

    def total_unit_cost(self, reference_price: float, region_cost: float) -> float:
        """Full unit cost (operating overhead + inputs) at reference prices.

        Every producer runs at full utilization at reference prices and starts
        curtailing at the same *relative* price, which is what keeps the
        seeded circuit exactly stationary and the frozen yayo baseline
        comparable.
        """
        return reference_price * region_cost / self.reference_price

    def operating_overhead(
        self, commodity: str, region_cost: float
    ) -> float:
        """Operating overhead: the total unit cost minus input costs at ref.

        With input costs now explicit, the old ``unit_cost`` (which assumed
        free inputs) has to be split. The operating overhead is what remains
        after input prices at reference are subtracted.  For the drug lab this
        goes to zero because the entire prior margin was consumed by the
        implicit input cost.
        """
        ref_prices = {
            YAYO: self.reference_price,
            LEAVES: self.leaves_reference_price,
            CHEMFUEL: self.chemfuel_reference_price,
        }
        processes = circuit_processes(self)
        process = processes[commodity]
        input_cost_per_run = process.input_cost_per_run(ref_prices)
        output_per_run = process.outputs.get(commodity, 1.0)
        input_cost_per_unit = input_cost_per_run / max(output_per_run, 1e-9)
        total = self.total_unit_cost(ref_prices[commodity], region_cost)
        return max(0.0, total - input_cost_per_unit)


def drug_commodity(parameters: ScenarioParameters | None = None) -> Commodity:
    parameters = parameters or ScenarioParameters()
    return _commodity(
        parameters,
        YAYO,
        parameters.reference_price,
        parameters.labor_value,
        parameters.yayo_mass,
    )


def _commodity(
    parameters: ScenarioParameters,
    name: str,
    reference_price: float,
    labor_value: float,
    mass: float,
) -> Commodity:
    return Commodity(
        name,
        reference_price=reference_price,
        labor_value=labor_value,
        demand_elasticity=parameters.demand_elasticity,
        target_inventory_days=parameters.target_inventory_days,
        price_adjustment_speed=parameters.price_adjustment_speed,
        inventory_price_sensitivity=parameters.inventory_price_sensitivity,
        minimum_price_factor=parameters.minimum_price_factor,
        maximum_price_factor=parameters.maximum_price_factor,
        mass_per_unit=mass,
    )


def circuit_commodities(
    parameters: ScenarioParameters | None = None,
) -> List[Commodity]:
    parameters = parameters or ScenarioParameters()
    return [
        drug_commodity(parameters),
        _commodity(
            parameters,
            LEAVES,
            parameters.leaves_reference_price,
            parameters.leaves_labor_value,
            parameters.leaves_mass,
        ),
        _commodity(
            parameters,
            CHEMFUEL,
            parameters.chemfuel_reference_price,
            parameters.chemfuel_labor_value,
            parameters.chemfuel_mass,
        ),
    ]


def circuit_processes(
    parameters: ScenarioParameters | None = None,
) -> Dict[str, Process]:
    """The three technologies, keyed by their primary output."""
    parameters = parameters or ScenarioParameters()
    return {
        CHEMFUEL: Process(
            "chemfuel synthesis",
            outputs={CHEMFUEL: 1.0},
            # The organic feedstock sits outside the modelled boundary, which
            # is where every model has to stop. Its labor is already inside
            # the 25 ticks the closed analysis measured for chemfuel.
            inputs={},
            direct_labor=parameters.chemfuel_direct_labor,
        ),
        LEAVES: Process(
            "psychoid farming",
            outputs={LEAVES: 1.0},
            inputs={CHEMFUEL: parameters.chemfuel_per_leaf},
            direct_labor=parameters.leaves_direct_labor,
        ),
        YAYO: Process(
            "yayo refining",
            outputs={YAYO: 1.0},
            inputs={
                LEAVES: parameters.leaves_per_yayo,
                CHEMFUEL: parameters.chemfuel_per_yayo,
            },
            direct_labor=parameters.yayo_direct_labor,
        ),
    }


def _region(
    parameters: ScenarioParameters,
    name: str,
    yayo_cost: float,
    producer_names: Dict[str, str],
) -> Region:
    processes = circuit_processes(parameters)
    commodities = {c.name: c for c in circuit_commodities(parameters)}
    capacity = {
        YAYO: parameters.producer_capacity_per_day,
        LEAVES: parameters.leaves_capacity_per_day,
        CHEMFUEL: parameters.chemfuel_capacity_per_day,
    }
    producers = [
        Producer(
            producer_names[key],
            key,
            capacity[key],
            parameters.operating_overhead(key, yayo_cost),
            parameters.zero_utilization_price_ratio,
            parameters.full_utilization_price_ratio,
            process=processes[key],
        )
        for key in (YAYO, LEAVES, CHEMFUEL)
    ]
    region = Region(
        name,
        cash=parameters.initial_cash,
        base_daily_demand={YAYO: parameters.daily_demand},
        inventory={},
        prices={key: commodities[key].reference_price for key in commodities},
        producers=producers,
    )
    # Seed every stock at its own target, so the circuit opens stationary
    # rather than working off an arbitrary initial imbalance.
    for key in commodities:
        region.inventory[key] = (
            region.throughput_demand(key) * parameters.target_inventory_days
        )
    return region


def seeded_two_region_economy(
    *,
    route_capacity_per_day: float = 1.0,
    freight_per_unit: float = 3.5,
    travel_days: int = 6,
    parameters: ScenarioParameters | None = None,
    input_rationing: str = "proportional",
) -> Economy:
    parameters = parameters or ScenarioParameters()
    regions = [
        _region(
            parameters,
            "Dust Basin",
            parameters.dust_unit_cost,
            {
                YAYO: "Dust cooperative",
                LEAVES: "Dust psychoid fields",
                CHEMFUEL: "Dust refinery",
            },
        ),
        _region(
            parameters,
            "Green River",
            parameters.river_unit_cost,
            {
                YAYO: "River works",
                LEAVES: "River psychoid fields",
                CHEMFUEL: "River refinery",
            },
        ),
    ]
    return Economy(
        circuit_commodities(parameters),
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
        replenishment_rate=parameters.replenishment_rate,
        zero_utilization_price_ratio=parameters.zero_utilization_price_ratio,
        full_utilization_price_ratio=parameters.full_utilization_price_ratio,
        input_rationing=input_rationing,
        construction_cost_multiplier=parameters.construction_cost_multiplier,
        min_investment_capacity=parameters.min_investment_capacity,
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


def input_shortage(
    days_after_loss: int = 150,
    *,
    upstream_commodity: str = LEAVES,
    loss_fraction: float = 0.70,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """Destroy upstream capacity and watch the constraint travel downstream.

    This is the scenario the free-production model could not express at all:
    with no material inputs, wrecking the psychoid fields had no effect
    whatsoever on the drug lab.
    """
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    economy.destroy_capacity("Dust Basin", upstream_commodity, loss_fraction)
    economy.step(days_after_loss)
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
            "commodities": {
                key: {
                    "price": round(region.prices[key], 3),
                    "inventory": round(region.inventory[key], 3),
                    "capacity_per_day": round(region.capacity(key), 3),
                    "throughput_demand": round(region.throughput_demand(key), 3),
                    "unmet_demand": round(region.unmet_demand[key], 3),
                }
                for key in sorted(economy.commodities)
            },
        }
    return {
        "day": economy.day,
        "regions": regions,
        "shipments_in_transit": len(economy.shipments),
        "material_residual": round(economy.commodity_balance("yayo"), 9),
        "material_residuals": {
            key: round(value, 9)
            for key, value in sorted(economy.commodity_balances().items())
        },
        "cash_residual": round(economy.cash_balance(), 9),
    }
