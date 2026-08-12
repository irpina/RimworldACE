"""Small deterministic stock-flow model for Stage 0.

This deliberately models only the mechanisms needed to test topology and
calibration before any RimWorld assembly work:

* prices clear locally from inventory and unmet effective demand;
* regions produce, consume, hold stock and keep silver balances;
* costly, delayed, capacity-limited routes permit planetary arbitrage;
* persistent excess profit induces delayed capacity investment;
* every commodity and silver movement is recorded in an invariant ledger.

It is not yet the final economic model. In particular, there are no production
inputs, labor markets, credit, resource reserves, or dynamic labor values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Dict, Iterable, List, Optional, Tuple


EPSILON = 1e-9


@dataclass(frozen=True)
class Commodity:
    name: str
    reference_price: float
    labor_value: float
    demand_elasticity: float = 0.8
    target_inventory_days: float = 30.0
    price_adjustment_speed: float = 0.20
    inventory_price_sensitivity: float = 0.90
    minimum_price_factor: float = 0.10
    maximum_price_factor: float = 10.0


@dataclass
class Producer:
    name: str
    commodity: str
    capacity_per_day: float
    unit_cost: float
    zero_utilization_price_ratio: float = 0.70
    full_utilization_price_ratio: float = 1.05
    active: bool = True
    output_total: float = 0.0
    cash: float = 0.0

    def utilization(self, price: float) -> float:
        """Smoothly curtail production when price falls below cash cost."""
        if not self.active or self.capacity_per_day <= 0:
            return 0.0
        ratio = price / max(self.unit_cost, EPSILON)
        if ratio <= self.zero_utilization_price_ratio:
            return 0.0
        if ratio >= self.full_utilization_price_ratio:
            return 1.0
        span = self.full_utilization_price_ratio - self.zero_utilization_price_ratio
        return (ratio - self.zero_utilization_price_ratio) / max(span, EPSILON)


@dataclass
class CapacityProject:
    commodity: str
    capacity_per_day: float
    unit_cost: float
    completes_day: int
    name: str


@dataclass
class Region:
    name: str
    cash: float
    base_daily_demand: Dict[str, float]
    inventory: Dict[str, float]
    prices: Dict[str, float]
    producers: List[Producer] = field(default_factory=list)
    expected_prices: Dict[str, float] = field(default_factory=dict)
    unmet_demand: Dict[str, float] = field(default_factory=dict)
    consumed_total: Dict[str, float] = field(default_factory=dict)
    imported_total: Dict[str, float] = field(default_factory=dict)
    exported_total: Dict[str, float] = field(default_factory=dict)
    projects: List[CapacityProject] = field(default_factory=list)

    def capacity(self, commodity: str) -> float:
        return sum(
            p.capacity_per_day
            for p in self.producers
            if p.active and p.commodity == commodity
        )

    def daily_demand(self, commodity: Commodity) -> float:
        base = self.base_daily_demand.get(commodity.name, 0.0)
        if base <= 0:
            return 0.0
        price = max(self.prices[commodity.name], EPSILON)
        return base * (price / commodity.reference_price) ** (
            -commodity.demand_elasticity
        )


@dataclass(frozen=True)
class Route:
    a: str
    b: str
    freight_per_unit: float
    capacity_per_day: float
    travel_days: int
    risk_markup: float = 0.0

    def other(self, region: str) -> str:
        if region == self.a:
            return self.b
        if region == self.b:
            return self.a
        raise ValueError(f"{region!r} is not on route {self.a!r}-{self.b!r}")


@dataclass
class Shipment:
    commodity: str
    quantity: float
    source: str
    destination: str
    dispatch_day: int
    arrival_day: int
    source_unit_price: float
    freight_per_unit: float


@dataclass
class Ledger:
    external_injections: Dict[str, float] = field(default_factory=dict)
    external_destruction: Dict[str, float] = field(default_factory=dict)
    production: Dict[str, float] = field(default_factory=dict)
    consumption: Dict[str, float] = field(default_factory=dict)
    transport_cash: float = 0.0
    initial_cash: float = 0.0

    @staticmethod
    def add(bucket: Dict[str, float], commodity: str, amount: float) -> None:
        bucket[commodity] = bucket.get(commodity, 0.0) + amount


class Economy:
    def __init__(
        self,
        commodities: Iterable[Commodity],
        regions: Iterable[Region],
        routes: Iterable[Route],
        *,
        investment_interval_days: int = 15,
        investment_lead_days: int = 45,
        investment_margin_threshold: float = 0.18,
        investment_fraction_of_shortfall: float = 0.45,
        unmet_demand_price_pressure: float = 2.0,
        speculative_inventory_limit: float = 0.50,
        expectation_alpha: float = 0.05,
        zero_utilization_price_ratio: float = 0.70,
        full_utilization_price_ratio: float = 1.05,
    ) -> None:
        self.commodities = {c.name: c for c in commodities}
        self.regions = {r.name: r for r in regions}
        self.routes = list(routes)
        self.shipments: List[Shipment] = []
        self.day = 0
        self.investment_interval_days = investment_interval_days
        self.investment_lead_days = investment_lead_days
        self.investment_margin_threshold = investment_margin_threshold
        self.investment_fraction_of_shortfall = investment_fraction_of_shortfall
        self.unmet_demand_price_pressure = unmet_demand_price_pressure
        self.speculative_inventory_limit = speculative_inventory_limit
        self.expectation_alpha = expectation_alpha
        self.zero_utilization_price_ratio = zero_utilization_price_ratio
        self.full_utilization_price_ratio = full_utilization_price_ratio
        self.ledger = Ledger(initial_cash=sum(r.cash for r in self.regions.values()))
        self.history: List[dict] = []

        for region in self.regions.values():
            for commodity in self.commodities.values():
                region.inventory.setdefault(commodity.name, 0.0)
                region.prices.setdefault(commodity.name, commodity.reference_price)
                region.expected_prices.setdefault(
                    commodity.name, region.prices[commodity.name]
                )
                region.unmet_demand.setdefault(commodity.name, 0.0)
                region.consumed_total.setdefault(commodity.name, 0.0)
                region.imported_total.setdefault(commodity.name, 0.0)
                region.exported_total.setdefault(commodity.name, 0.0)
        self._record_history()

    # ------------------------------------------------------------- public API

    def step(self, days: int = 1) -> None:
        for _ in range(days):
            self.day += 1
            self._arrive_shipments()
            self._complete_projects()
            self._produce()
            self._consume()
            self._update_prices()
            self._dispatch_arbitrage()
            self._update_expectations()
            if self.day % self.investment_interval_days == 0:
                self._invest()
            self._record_history()

    def inject(self, region: str, commodity: str, quantity: float) -> None:
        if quantity < 0:
            raise ValueError("injection quantity must be non-negative")
        self.regions[region].inventory[commodity] += quantity
        Ledger.add(self.ledger.external_injections, commodity, quantity)

    def destroy_capacity(
        self, region: str, commodity: str, fraction: float
    ) -> float:
        """Remove a fraction of active capacity, smallest producers first."""
        if not 0 <= fraction <= 1:
            raise ValueError("fraction must be between zero and one")
        target = self.regions[region].capacity(commodity) * fraction
        remaining = target
        removed = 0.0
        candidates = sorted(
            (
                p
                for p in self.regions[region].producers
                if p.active and p.commodity == commodity
            ),
            key=lambda p: (p.capacity_per_day, p.name),
        )
        for producer in candidates:
            if remaining <= EPSILON:
                break
            take = min(producer.capacity_per_day, remaining)
            producer.capacity_per_day -= take
            removed += take
            remaining -= take
            if producer.capacity_per_day <= EPSILON:
                producer.capacity_per_day = 0.0
                producer.active = False
        return removed

    def commodity_balance(self, commodity: str) -> float:
        """Return residual of the closed material accounting identity."""
        initial = self.history[0]["system_inventory"][commodity]
        produced = self.ledger.production.get(commodity, 0.0)
        injected = self.ledger.external_injections.get(commodity, 0.0)
        destroyed = self.ledger.external_destruction.get(commodity, 0.0)
        consumed = self.ledger.consumption.get(commodity, 0.0)
        current = self.system_inventory(commodity)
        return initial + produced + injected - destroyed - consumed - current

    def cash_balance(self) -> float:
        """Return residual of the currently modelled silver accounts."""
        return (
            sum(r.cash for r in self.regions.values())
            + self.ledger.transport_cash
            - self.ledger.initial_cash
        )

    def system_inventory(self, commodity: str) -> float:
        held = sum(r.inventory.get(commodity, 0.0) for r in self.regions.values())
        in_transit = sum(
            s.quantity for s in self.shipments if s.commodity == commodity
        )
        return held + in_transit

    def series(self, region: str, commodity: str, field: str = "price") -> List[float]:
        return [h["regions"][region][field][commodity] for h in self.history]

    # ------------------------------------------------------------ daily flows

    def _arrive_shipments(self) -> None:
        pending: List[Shipment] = []
        for shipment in self.shipments:
            if shipment.arrival_day > self.day:
                pending.append(shipment)
                continue
            destination = self.regions[shipment.destination]
            destination.inventory[shipment.commodity] += shipment.quantity
            destination.imported_total[shipment.commodity] += shipment.quantity
        self.shipments = pending

    def _complete_projects(self) -> None:
        for region in self.regions.values():
            pending: List[CapacityProject] = []
            for project in region.projects:
                if project.completes_day > self.day:
                    pending.append(project)
                    continue
                region.producers.append(
                    Producer(
                        project.name,
                        project.commodity,
                        project.capacity_per_day,
                        project.unit_cost,
                        self.zero_utilization_price_ratio,
                        self.full_utilization_price_ratio,
                    )
                )
            region.projects = pending

    def _produce(self) -> None:
        for region in self.regions.values():
            for producer in region.producers:
                if producer.commodity not in self.commodities:
                    continue
                price = region.prices[producer.commodity]
                output = producer.capacity_per_day * producer.utilization(price)
                if output <= 0:
                    continue
                region.inventory[producer.commodity] += output
                producer.output_total += output
                Ledger.add(self.ledger.production, producer.commodity, output)

    def _consume(self) -> None:
        for region in self.regions.values():
            for commodity in self.commodities.values():
                desired = region.daily_demand(commodity)
                available = region.inventory[commodity.name]
                consumed = min(desired, available)
                unmet = desired - consumed
                region.inventory[commodity.name] -= consumed
                region.unmet_demand[commodity.name] = unmet
                region.consumed_total[commodity.name] += consumed
                Ledger.add(self.ledger.consumption, commodity.name, consumed)

    def _update_prices(self) -> None:
        for region in self.regions.values():
            for commodity in self.commodities.values():
                name = commodity.name
                base_demand = max(region.base_daily_demand.get(name, 0.0), EPSILON)
                target = base_demand * commodity.target_inventory_days
                coverage_gap = (target - region.inventory[name]) / max(target, EPSILON)
                unmet_ratio = region.unmet_demand[name] / base_demand
                pressure = (
                    commodity.inventory_price_sensitivity * coverage_gap
                    + self.unmet_demand_price_pressure * unmet_ratio
                )
                old = region.prices[name]
                low = commodity.reference_price * commodity.minimum_price_factor
                high = commodity.reference_price * commodity.maximum_price_factor
                desired = commodity.reference_price * exp(pressure)
                desired = min(high, max(low, desired))
                region.prices[name] = (
                    old
                    + commodity.price_adjustment_speed * (desired - old)
                )

    def _dispatch_arbitrage(self) -> None:
        """Dispatch in deterministic route and commodity order.

        The destination pays the source region's current price plus freight.
        Freight enters an explicit transport-sector cash account. Price
        convergence happens because source inventory falls and destination
        inventory rises after the travel delay.
        """
        for route in sorted(self.routes, key=lambda x: (x.a, x.b)):
            remaining_capacity = route.capacity_per_day
            for name in sorted(self.commodities):
                if remaining_capacity <= EPSILON:
                    break
                a, b = self.regions[route.a], self.regions[route.b]
                freight = route.freight_per_unit * (1.0 + route.risk_markup)
                if b.prices[name] > a.prices[name] + freight:
                    source, destination = a, b
                elif a.prices[name] > b.prices[name] + freight:
                    source, destination = b, a
                else:
                    continue

                commodity = self.commodities[name]
                source_target = (
                    source.base_daily_demand.get(name, 0.0)
                    * commodity.target_inventory_days
                )
                destination_target = (
                    destination.base_daily_demand.get(name, 0.0)
                    * commodity.target_inventory_days
                )
                exportable = max(0.0, source.inventory[name] - source_target)
                shortage = max(0.0, destination_target - destination.inventory[name])
                gross_spread = (
                    destination.prices[name] - source.prices[name] - freight
                )
                # Arbitrageurs can buy into a normally stocked destination
                # when the spread is large enough. Their speculative room
                # shrinks continuously as prices converge.
                speculative_room = destination_target * min(
                    self.speculative_inventory_limit,
                    gross_spread / max(destination.prices[name], EPSILON),
                )
                import_room = shortage + max(0.0, speculative_room)
                quantity = min(exportable, import_room, remaining_capacity)
                if quantity <= EPSILON:
                    continue

                unit_payment = source.prices[name] + freight
                affordable = destination.cash / max(unit_payment, EPSILON)
                quantity = min(quantity, affordable)
                if quantity <= EPSILON:
                    continue

                source.inventory[name] -= quantity
                source.exported_total[name] += quantity
                payment = source.prices[name] * quantity
                freight_payment = freight * quantity
                destination.cash -= payment + freight_payment
                source.cash += payment
                self.ledger.transport_cash += freight_payment
                self.shipments.append(
                    Shipment(
                        name,
                        quantity,
                        source.name,
                        destination.name,
                        self.day,
                        self.day + route.travel_days,
                        source.prices[name],
                        freight,
                    )
                )
                remaining_capacity -= quantity

    def _update_expectations(self) -> None:
        alpha = self.expectation_alpha
        for region in self.regions.values():
            for name in self.commodities:
                region.expected_prices[name] = (
                    (1.0 - alpha) * region.expected_prices[name]
                    + alpha * region.prices[name]
                )

    def _invest(self) -> None:
        for region in self.regions.values():
            for name, commodity in self.commodities.items():
                demand = region.base_daily_demand.get(name, 0.0)
                if demand <= 0:
                    continue
                existing = region.capacity(name)
                pipeline = sum(
                    p.capacity_per_day for p in region.projects if p.commodity == name
                )
                shortfall = max(0.0, demand - existing - pipeline)
                if shortfall <= EPSILON:
                    continue
                active_costs = [
                    p.unit_cost
                    for p in region.producers
                    if p.active and p.commodity == name
                ]
                assumed_cost = (
                    sum(active_costs) / len(active_costs)
                    if active_costs
                    else commodity.reference_price * 0.70
                )
                expected = region.expected_prices[name]
                margin = (expected - assumed_cost) / max(assumed_cost, EPSILON)
                inventory_days = region.inventory[name] / max(demand, EPSILON)
                if (
                    margin < self.investment_margin_threshold
                    or inventory_days >= commodity.target_inventory_days
                ):
                    continue
                amount = shortfall * self.investment_fraction_of_shortfall
                region.projects.append(
                    CapacityProject(
                        name,
                        amount,
                        assumed_cost,
                        self.day + self.investment_lead_days,
                        f"entrant-{region.name}-{name}-{self.day}",
                    )
                )

    # --------------------------------------------------------------- snapshots

    def _record_history(self) -> None:
        self.history.append(
            {
                "day": self.day,
                "system_inventory": {
                    name: self.system_inventory(name) for name in self.commodities
                },
                "regions": {
                    region.name: {
                        "price": dict(region.prices),
                        "inventory": dict(region.inventory),
                        "unmet": dict(region.unmet_demand),
                        "capacity": {
                            name: region.capacity(name) for name in self.commodities
                        },
                        "cash": region.cash,
                    }
                    for region in self.regions.values()
                },
            }
        )
