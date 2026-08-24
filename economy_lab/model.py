"""Small deterministic stock-flow model for Stage 0.

This deliberately models only the mechanisms needed to test topology and
calibration before any RimWorld assembly work:

* prices clear locally from inventory and unmet effective demand;
* regions produce, consume, hold stock and keep silver balances;
* production consumes accounted material inputs and can be input-constrained;
* costly, delayed, capacity-limited routes permit planetary arbitrage;
* persistent excess profit induces delayed capacity investment;
* every commodity and silver movement is recorded in an invariant ledger.

It is not yet the final economic model. In particular, there are no labor
markets, credit, resource reserves, capital-goods costs, or dynamic labor
values. The modelling choices behind input-output production are recorded in
`docs/08-accounted-input-design.md`; read that before changing them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Dict, Iterable, List, Optional, Tuple


EPSILON = 1e-9

#: How a producer behaves when it holds only part of its required inputs.
PROPORTIONAL = "proportional"
ALL_OR_NOTHING = "all_or_nothing"


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
    #: RimWorld's Mass stat. Only used to apportion joint-product costs.
    mass_per_unit: float = 1.0


@dataclass(frozen=True)
class Process:
    """One technology: what it consumes, what it yields, and at what cost.

    Quantities are per *run*. A producer's daily runs are its capacity divided
    by `capacity_per_run`, so a single-output process with unit capacity cost
    reduces exactly to the earlier "capacity is units per day" model.

    `outputs` is a mapping from the outset because joint production is normal
    in this domain rather than exceptional. When there is more than one output,
    `apportionment` decides how `direct_labor` and `unit_operating_cost` are
    split between them; see `share_of_cost`.
    """

    name: str
    outputs: Dict[str, float]
    inputs: Dict[str, float] = field(default_factory=dict)
    direct_labor: float = 0.0
    capacity_per_run: float = 1.0
    unit_operating_cost: float = 0.0
    apportionment: str = "mass"

    @property
    def primary(self) -> str:
        """The largest output by quantity; ties broken by name."""
        return max(sorted(self.outputs), key=lambda c: self.outputs[c])

    def runs_for(self, capacity_per_day: float) -> float:
        return capacity_per_day / max(self.capacity_per_run, EPSILON)

    def share_of_cost(
        self, commodity: str, commodities: Dict[str, Commodity]
    ) -> float:
        """Fraction of this process's joint cost borne by one output.

        Mass apportionment: physical, and therefore not circular in the price
        it is meant to help explain. It is a documented choice, not a truth;
        see `docs/08-accounted-input-design.md`.
        """
        if commodity not in self.outputs:
            return 0.0
        if len(self.outputs) == 1:
            return 1.0
        if self.apportionment != "mass":
            raise ValueError(f"unknown apportionment rule {self.apportionment!r}")

        def weight(name: str) -> float:
            mass = commodities[name].mass_per_unit if name in commodities else 1.0
            return mass * self.outputs[name]

        total = sum(weight(name) for name in self.outputs)
        if total <= EPSILON:
            # Massless outputs cannot be told apart by mass; split evenly and
            # say so rather than dividing by zero.
            return 1.0 / len(self.outputs)
        return weight(commodity) / total

    def labor_per_unit(
        self, commodity: str, commodities: Dict[str, Commodity]
    ) -> float:
        units = self.outputs.get(commodity, 0.0)
        if units <= EPSILON:
            return 0.0
        return self.direct_labor * self.share_of_cost(commodity, commodities) / units

    def operating_cost_per_unit(
        self, commodity: str, commodities: Dict[str, Commodity]
    ) -> float:
        units = self.outputs.get(commodity, 0.0)
        if units <= EPSILON:
            return 0.0
        share = self.share_of_cost(commodity, commodities)
        return self.unit_operating_cost * share / units

    def input_cost_per_run(self, prices: Dict[str, float]) -> float:
        """Silver cost of one run's inputs at the given regional prices."""
        return sum(
            qty * prices.get(name, 0.0) for name, qty in self.inputs.items()
        )


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
    #: Required. Production is no longer a free ledger source.
    process: Optional[Process] = None

    def __post_init__(self) -> None:
        if self.process is None:
            raise ValueError(
                f"producer {self.name!r} needs a Process; free production was "
                "removed when input-output accounting landed"
            )
        if self.commodity not in self.process.outputs:
            raise ValueError(
                f"producer {self.name!r} claims commodity {self.commodity!r} "
                f"which process {self.process.name!r} does not output"
            )

    def effective_unit_cost(self, prices: Dict[str, float]) -> float:
        """Operating overhead plus input cost at the given regional prices.

        This is the full per-unit cost used by the utilization curve. When
        input prices rise, the effective cost rises and the producer curtails
        earlier — a price-mediated feedback the demand-led control cannot
        provide on its own.
        """
        input_cost = self.process.input_cost_per_run(prices)
        output_per_run = self.process.outputs.get(self.commodity, 0.0)
        if output_per_run <= EPSILON:
            return self.unit_cost
        return self.unit_cost + input_cost / output_per_run

    def utilization(self, price: float, prices: Optional[Dict[str, float]] = None) -> float:
        """Smoothly curtail production when price falls below cash cost."""
        if not self.active or self.capacity_per_day <= 0:
            return 0.0
        cost = self.effective_unit_cost(prices) if prices is not None else self.unit_cost
        ratio = price / max(cost, EPSILON)
        if ratio <= self.zero_utilization_price_ratio:
            return 0.0
        if ratio >= self.full_utilization_price_ratio:
            return 1.0
        span = self.full_utilization_price_ratio - self.zero_utilization_price_ratio
        return (ratio - self.zero_utilization_price_ratio) / max(span, EPSILON)

    def desired_runs(self, price: float, prices: Optional[Dict[str, float]] = None) -> float:
        return self.process.runs_for(self.capacity_per_day) * self.utilization(price, prices)

    def input_per_day(self, commodity: str) -> float:
        """Input required per day at full capacity, ignoring price curtailment."""
        per_run = self.process.inputs.get(commodity, 0.0)
        if per_run <= 0 or not self.active:
            return 0.0
        return self.process.runs_for(self.capacity_per_day) * per_run


@dataclass
class CapacityProject:
    commodity: str
    capacity_per_day: float
    unit_cost: float
    completes_day: int
    name: str
    process: Optional[Process] = None


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

    def throughput_demand(self, commodity: str) -> float:
        """Final demand plus demand derived from local input requirements.

        Intermediate goods have no final demand, so scaling their inventory
        targets and price pressure by final demand alone would give them a
        target of zero and collapse them to the price floor. This is a strict
        generalization: a commodity nothing is made from has zero derived
        demand and behaves exactly as before.
        """
        derived = sum(p.input_per_day(commodity) for p in self.producers if p.active)
        return self.base_daily_demand.get(commodity, 0.0) + derived

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
    #: Material consumed as a production input, kept apart from final
    #: consumption so a unit used up making something else is still a
    #: declared sink rather than a leak.
    intermediate_consumption: Dict[str, float] = field(default_factory=dict)
    #: Silver spent on capacity investment (construction fund).
    investment_spending: float = 0.0
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
        replenishment_rate: float = 0.10,
        zero_utilization_price_ratio: float = 0.70,
        full_utilization_price_ratio: float = 1.05,
        input_rationing: str = PROPORTIONAL,
    ) -> None:
        if input_rationing not in (PROPORTIONAL, ALL_OR_NOTHING):
            raise ValueError(f"unknown input rationing rule {input_rationing!r}")
        self.commodities = {c.name: c for c in commodities}
        self.regions = {r.name: r for r in regions}
        self.routes = list(routes)
        self.shipments: List[Shipment] = []
        self.input_rationing = input_rationing
        self.day = 0
        self.investment_interval_days = investment_interval_days
        self.investment_lead_days = investment_lead_days
        self.investment_margin_threshold = investment_margin_threshold
        self.investment_fraction_of_shortfall = investment_fraction_of_shortfall
        self.unmet_demand_price_pressure = unmet_demand_price_pressure
        self.speculative_inventory_limit = speculative_inventory_limit
        self.expectation_alpha = expectation_alpha
        if not 0.0 <= replenishment_rate <= 1.0:
            raise ValueError("replenishment_rate must be between zero and one")
        self.replenishment_rate = replenishment_rate
        self.zero_utilization_price_ratio = zero_utilization_price_ratio
        self.full_utilization_price_ratio = full_utilization_price_ratio
        self.ledger = Ledger(initial_cash=sum(r.cash for r in self.regions.values()))
        self.history: List[dict] = []

        # Remembered so replacement capacity can be built for a commodity
        # whose every producer has since been destroyed.
        self.known_processes: Dict[str, Process] = {}
        for region in self.regions.values():
            for producer in region.producers:
                process = producer.process
                unknown = (
                    set(process.inputs) | set(process.outputs)
                ) - set(self.commodities)
                if unknown:
                    # An input or output outside the declared commodity set
                    # would enter or leave the material ledger untracked.
                    raise ValueError(
                        f"process {process.name!r} references undeclared "
                        f"commodities: {sorted(unknown)}"
                    )
                self.known_processes.setdefault(producer.commodity, process)

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
        """Return residual of the closed material accounting identity.

        Every unit must trace to a declared source (opening stock, production,
        external injection) and leave through a declared sink (final
        consumption, use as a production input, external destruction) or still
        be held somewhere.
        """
        initial = self.history[0]["system_inventory"][commodity]
        produced = self.ledger.production.get(commodity, 0.0)
        injected = self.ledger.external_injections.get(commodity, 0.0)
        destroyed = self.ledger.external_destruction.get(commodity, 0.0)
        consumed = self.ledger.consumption.get(commodity, 0.0)
        used_as_input = self.ledger.intermediate_consumption.get(commodity, 0.0)
        current = self.system_inventory(commodity)
        return (
            initial
            + produced
            + injected
            - destroyed
            - consumed
            - used_as_input
            - current
        )

    def commodity_balances(self) -> Dict[str, float]:
        """Material residual for every commodity, not just the headline one."""
        return {name: self.commodity_balance(name) for name in self.commodities}

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
                        process=project.process
                        or self.known_processes[project.commodity],
                    )
                )
            region.projects = pending

    def _produce(self) -> None:
        """Run every process against the region's opening inventory.

        Production is simultaneous: all producers draw on the stock the day
        opened with, and output lands only once every draw is done, so the
        result does not depend on the order producers sit in a list. A shock
        therefore takes one day per production stage to travel downstream,
        which is a visible property rather than a hidden one.
        """
        for region in self.regions.values():
            # Unmet demand is rebuilt from scratch each day. Production adds
            # input shortfalls, consumption adds final shortfalls.
            for name in self.commodities:
                region.unmet_demand[name] = 0.0

            opening = dict(region.inventory)
            active = sorted(
                (
                p
                for p in region.producers
                if p.active
                and p.capacity_per_day > 0
                and p.commodity in self.commodities
                ),
                key=lambda p: (p.name, p.commodity),
            )
            desired = {
                id(p): p.desired_runs(region.prices[p.commodity], region.prices) for p in active
            }
            planned = self._planned_runs(region, opening, active, desired)

            # Pro-rata by requirement, so contention for a scarce shared input
            # is order-independent. Single pass: a producer throttled by some
            # other input leaves its allocation unused, and that slack stays in
            # inventory for tomorrow rather than being reallocated today.
            required: Dict[str, float] = {}
            for producer in active:
                runs = planned[id(producer)]
                for name, per_run in producer.process.inputs.items():
                    required[name] = required.get(name, 0.0) + runs * per_run

            ration: Dict[str, float] = {}
            for name, need in required.items():
                if need <= EPSILON:
                    ration[name] = 1.0
                else:
                    ration[name] = min(1.0, opening.get(name, 0.0) / need)

            drawn: Dict[str, float] = {}
            produced: Dict[str, float] = {}
            for producer in active:
                runs = planned[id(producer)]
                if runs <= EPSILON:
                    continue
                inputs = producer.process.inputs
                # Liebig: inputs are complements, so the scarcest one binds.
                available = min((ration[n] for n in inputs), default=1.0)
                if self.input_rationing == ALL_OR_NOTHING:
                    available = 1.0 if available >= 1.0 - EPSILON else 0.0
                runs *= available
                if runs <= EPSILON:
                    continue
                for name, per_run in inputs.items():
                    drawn[name] = drawn.get(name, 0.0) + runs * per_run
                for name, per_run in producer.process.outputs.items():
                    if name not in self.commodities:
                        continue
                    produced[name] = produced.get(name, 0.0) + runs * per_run
                producer.output_total += runs * producer.process.outputs.get(
                    producer.commodity, 0.0
                )

            for name, amount in drawn.items():
                region.inventory[name] -= amount
                Ledger.add(self.ledger.intermediate_consumption, name, amount)
            for name, amount in produced.items():
                region.inventory[name] += amount
                Ledger.add(self.ledger.production, name, amount)

            # An input a producer could not source is real unmet demand for
            # that input. Without this an upstream shortage would cut
            # downstream output while never registering in the input's own
            # price, so scarcity would propagate as quantity but never as a
            # price signal.
            for name, need in required.items():
                # Only what this commodity's own scarcity denied. Measuring
                # `need - drawn` instead would book the unused slack of a
                # producer throttled by some *other* input as unmet demand
                # here, inventing a shortage in a commodity that was ample.
                shortfall = need * (1.0 - ration[name])
                if shortfall > EPSILON:
                    region.unmet_demand[name] += shortfall

    def _planned_runs(
        self,
        region: Region,
        opening: Dict[str, float],
        active: List[Producer],
        desired: Dict[int, float],
    ) -> Dict[int, float]:
        """Plan output from intended outflow and a damped stock correction.

        Every iteration reads the same opening inventory. Iteration only lets
        downstream run plans become today's upstream input orders; it does not
        make today's output available as today's input. Production therefore
        remains simultaneous and independent of producer list order.
        """
        planned = dict(desired)
        for _ in range(1000):
            intended_outflow = {
                name: region.daily_demand(commodity)
                for name, commodity in self.commodities.items()
            }
            for producer in active:
                runs = planned[id(producer)]
                for name, per_run in producer.process.inputs.items():
                    intended_outflow[name] += runs * per_run

            requested_output: Dict[str, float] = {}
            for name, commodity in self.commodities.items():
                target = (
                    region.throughput_demand(name)
                    * commodity.target_inventory_days
                )
                correction = self.replenishment_rate * (
                    target - opening.get(name, 0.0)
                )
                requested_output[name] = max(
                    0.0, intended_outflow[name] + correction
                )

            desired_output: Dict[str, float] = {
                name: 0.0 for name in self.commodities
            }
            for producer in active:
                units = producer.process.outputs[producer.commodity]
                desired_output[producer.commodity] += (
                    desired[id(producer)] * units
                )

            revised: Dict[int, float] = {}
            for producer in active:
                name = producer.commodity
                available_output = desired_output[name]
                if available_output <= EPSILON:
                    factor = 0.0
                else:
                    factor = min(1.0, requested_output[name] / available_output)
                revised[id(producer)] = desired[id(producer)] * factor
            if all(
                abs(revised[key] - planned[key]) <= EPSILON
                for key in revised
            ):
                return revised
            planned = revised
        raise RuntimeError("production-order plan did not converge")

    def _consume(self) -> None:
        for region in self.regions.values():
            for commodity in self.commodities.values():
                desired = region.daily_demand(commodity)
                available = region.inventory[commodity.name]
                consumed = min(desired, available)
                unmet = desired - consumed
                region.inventory[commodity.name] -= consumed
                region.unmet_demand[commodity.name] += unmet
                region.consumed_total[commodity.name] += consumed
                Ledger.add(self.ledger.consumption, commodity.name, consumed)

    def _update_prices(self) -> None:
        for region in self.regions.values():
            for commodity in self.commodities.values():
                name = commodity.name
                throughput = region.throughput_demand(name)
                if throughput <= EPSILON:
                    # Neither consumed nor used as an input here. That is "not
                    # traded in this region", not "infinitely oversupplied",
                    # so leave the price alone instead of driving it to the
                    # floor on a division by nothing.
                    continue
                base_demand = throughput
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
            a, b = self.regions[route.a], self.regions[route.b]
            freight = route.freight_per_unit * (1.0 + route.risk_markup)

            # Scarce freight goes to the widest spread first: arbitrageurs ship
            # the most profitable cargo, not the alphabetically first one. With
            # a single commodity this is an identity.
            candidates = []
            for name in sorted(self.commodities):
                spread = abs(a.prices[name] - b.prices[name]) - freight
                if spread > 0:
                    candidates.append((spread, name))
            candidates.sort(key=lambda item: (-item[0], item[1]))

            for _, name in candidates:
                if remaining_capacity <= EPSILON:
                    break
                if b.prices[name] > a.prices[name] + freight:
                    source, destination = a, b
                elif a.prices[name] > b.prices[name] + freight:
                    source, destination = b, a
                else:
                    continue

                commodity = self.commodities[name]
                source_target = (
                    source.throughput_demand(name) * commodity.target_inventory_days
                )
                destination_target = (
                    destination.throughput_demand(name)
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
                # Throughput, not final demand: otherwise an intermediate good
                # would never attract replacement capacity, because nobody
                # eats it.
                demand = region.throughput_demand(name)
                if demand <= 0 or name not in self.known_processes:
                    continue
                existing = region.capacity(name)
                pipeline = sum(
                    p.capacity_per_day for p in region.projects if p.commodity == name
                )
                shortfall = max(0.0, demand - existing - pipeline)
                if shortfall <= EPSILON:
                    continue
                # Use effective cost (overhead + inputs) for the margin test,
                # but store only the operating overhead on the new producer.
                active_effective = [
                    p.effective_unit_cost(region.prices)
                    for p in region.producers
                    if p.active and p.commodity == name
                ]
                active_overhead = [
                    p.unit_cost
                    for p in region.producers
                    if p.active and p.commodity == name
                ]
                assumed_effective = (
                    sum(active_effective) / len(active_effective)
                    if active_effective
                    else commodity.reference_price * 0.70
                )
                assumed_overhead = (
                    sum(active_overhead) / len(active_overhead)
                    if active_overhead
                    else max(0.0, commodity.reference_price * 0.70)
                )
                expected = region.expected_prices[name]
                margin = (expected - assumed_effective) / max(assumed_effective, EPSILON)
                inventory_days = region.inventory[name] / max(demand, EPSILON)
                if (
                    margin < self.investment_margin_threshold
                    or inventory_days >= commodity.target_inventory_days
                ):
                    continue
                amount = shortfall * self.investment_fraction_of_shortfall
                existing_process = next(
                    (
                        p.process
                        for p in region.producers
                        if p.active and p.commodity == name
                    ),
                    self.known_processes[name],
                )
                region.projects.append(
                    CapacityProject(
                        name,
                        amount,
                        assumed_overhead,
                        self.day + self.investment_lead_days,
                        f"entrant-{region.name}-{name}-{self.day}",
                        process=existing_process,
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
