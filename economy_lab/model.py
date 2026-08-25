"""Small deterministic stock-flow model for Stage 0.

This deliberately models only the mechanisms needed to test topology and
calibration before any RimWorld assembly work:

* prices clear locally from inventory and unmet effective demand;
* regions produce, consume, hold stock and keep silver balances;
* production consumes accounted material inputs and can be input-constrained;
* costly, delayed, capacity-limited routes permit planetary arbitrage;
* persistent excess profit induces delayed capacity investment;
* every commodity and silver movement is recorded in an invariant ledger.

It is not yet the final economic model. In particular, there is no credit
and labor values remain static. The modelling choices behind input-output
production are recorded in `docs/08-accounted-input-design.md`; the resource
reserve and rent decisions are in `docs/15-resource-reserves-design.md`; the
wage relation, subsistence basket, and surplus ledger decisions are in
`docs/17-labor-power-and-surplus-design.md`; read them before changing any
of it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, floor
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


@dataclass
class ResourceGrade:
    """One extractable tranche: a finite quantity at a given cost.

    Grades are ordered cheapest first within a ``ResourceReserve``.  The
    ``extraction_cost`` is a natural property of the deposit, not a market
    outcome — it never changes.  ``quantity`` decreases as material is
    extracted.
    """

    quantity: float
    extraction_cost: float


@dataclass
class ResourceReserve:
    """Ordered grades for a commodity in a region, cheapest first.

    All extraction producers in a region share the same reserve.  When the
    cheapest grade exhausts, the next grade becomes marginal and extraction
    cost rises — the classical extensive margin.
    """

    commodity: str
    grades: List[ResourceGrade]

    @property
    def remaining(self) -> float:
        """Total extractable quantity across all grades."""
        return sum(g.quantity for g in self.grades)

    def marginal_cost(self) -> float:
        """Extraction cost of the cheapest non-exhausted grade."""
        for grade in self.grades:
            if grade.quantity > EPSILON:
                return grade.extraction_cost
        return float("inf")

    def extract(self, amount: float) -> float:
        """Draw from cheapest grade first; return the amount actually taken."""
        remaining = amount
        for grade in self.grades:
            if remaining <= EPSILON:
                break
            take = min(grade.quantity, remaining)
            grade.quantity -= take
            remaining -= take
        return amount - remaining


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
    #: Fixed capital supporting one unit of daily output, in silver and in
    #: work-ticks (docs/23).  Exogenous, like ``direct_labor``: the buildings
    #: are not in the modelled circuit, so their values come from the closed
    #: analysis rather than from the value solve.  Zero leaves bare models
    #: bit-identical.
    capital_money_per_capacity: float = 0.0
    capital_labor_per_capacity: float = 0.0

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

    def capital_consumed_per_unit(
        self,
        commodity: str,
        service_life_days: float,
        commodities: Optional[Dict[str, "Commodity"]] = None,
    ) -> Tuple[float, float]:
        """Fixed capital transferred to one unit of output: (silver, ticks).

        Use-based rather than time-based: one unit of daily capacity makes
        one unit a day, so it makes ``service_life_days`` units across the
        life of the capital that supports it.  Unit cost is therefore
        independent of utilization, which keeps idle plant from feeding a
        rising unit cost back into the price anchor (docs/23).
        """
        if service_life_days <= EPSILON:
            return 0.0, 0.0
        share = self.share_of_cost(commodity, commodities or {})
        units = self.outputs.get(commodity, 0.0)
        if units <= EPSILON:
            return 0.0, 0.0
        return (
            self.capital_money_per_capacity * share / service_life_days,
            self.capital_labor_per_capacity * share / service_life_days,
        )

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
    #: Wage cost per unit of output, updated daily by the economy from the
    #: current regional basket cost (see docs/17).  Zero when the region has
    #: no subsistence basket, which keeps bare-model tests bit-identical.
    wage_cost_per_unit: float = 0.0
    #: Runs actually completed on the most recent day, after every rationing
    #: stage.  The output weights for the social labor value solve are these
    #: realized runs, not capacity (see docs/19).
    last_runs: float = 0.0
    #: Fixed capital consumed per unit of output, in silver and in
    #: work-ticks (docs/23).  Set once from the process and the service
    #: life; carved out of ``unit_cost`` rather than added to it.
    capital_cost_per_unit: float = 0.0
    capital_labor_per_unit: float = 0.0

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

    def attributable_unit_cost(self, prices: Dict[str, float]) -> float:
        """Cost the model can actually account for: c + v, per unit.

        Circulating inputs at current regional prices, wages, and fixed
        capital consumed.  This is what the surplus ledger treats as cost;
        it deliberately excludes ``unattributed_margin`` (docs/23).
        """
        input_cost = self.process.input_cost_per_run(prices)
        output_per_run = self.process.outputs.get(self.commodity, 0.0)
        per_unit_inputs = (
            0.0 if output_per_run <= EPSILON else input_cost / output_per_run
        )
        return (
            per_unit_inputs
            + self.wage_cost_per_unit
            + self.capital_cost_per_unit
        )

    def effective_unit_cost(self, prices: Dict[str, float]) -> float:
        """The reservation price the utilization curve compares against.

        Attributable cost plus the unattributed wedge.  A producer curtails
        when the market price falls toward this, not toward bare c + v: the
        wedge behaves like a required margin whether it is surplus or an
        unmodelled cost, and the model cannot tell which (docs/23).

        Deliberately still computed as ``unit_cost + inputs + wages``, the
        same expression and the same float as before the reclassification,
        so that splitting the overhead moves no behavior at all.  Capital
        consumption is carved *out of* ``unit_cost`` for the ledger, not
        added on top of it.
        """
        input_cost = self.process.input_cost_per_run(prices)
        output_per_run = self.process.outputs.get(self.commodity, 0.0)
        if output_per_run <= EPSILON:
            return self.unit_cost + self.wage_cost_per_unit
        return self.unit_cost + input_cost / output_per_run + self.wage_cost_per_unit

    @property
    def unattributed_margin(self) -> float:
        """The old operating overhead, less what capital consumption claims.

        Negative when the authored price does not cover attributable cost,
        which is a finding about that price rather than an error, so it is
        reported rather than clamped (docs/23).
        """
        return self.unit_cost - self.capital_cost_per_unit

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
    #: Finite natural endowments keyed by commodity name.  Extraction
    #: producers draw from these; a missing entry means unlimited.
    reserves: Dict[str, ResourceReserve] = field(default_factory=dict)
    #: The wage relation (docs/17).  ``subsistence_basket`` maps commodity ->
    #: units per worker-day; the wage equals the basket at current regional
    #: prices.  An empty basket disables the whole wage circuit, which keeps
    #: bare-model tests bit-identical.
    subsistence_basket: Dict[str, float] = field(default_factory=dict)
    #: Output-weighted average effective unit cost per commodity as seeded,
    #: and the ratio of the current cost to it.  The price anchor moves with
    #: that ratio (docs/21).  Held over when no producer is active.
    seed_unit_cost: Dict[str, float] = field(default_factory=dict)
    cost_ratio: Dict[str, float] = field(default_factory=dict)
    ticks_per_worker_day: float = 24000.0
    #: Fixed daily labor supply in worker-days; infinite means never binding.
    labor_pool: float = float("inf")
    #: Workers' silver.  Wages flow in, basket purchases flow out.
    worker_cash: float = 0.0
    #: Worker-days earned yesterday, whose basket demand is due today
    #: (wages today, bread tomorrow — docs/17 section 6).
    worker_days_due: float = 0.0
    #: Worker-days earned today, stored for tomorrow's basket demand.
    worker_days_earned: float = 0.0

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
        total = self.base_daily_demand.get(commodity, 0.0) + derived
        basket_quantity = self.subsistence_basket.get(commodity, 0.0)
        if basket_quantity > 0.0:
            # Worker demand for a basket good, at full-capacity employment —
            # the same full-capacity convention the derived-input component
            # uses, so targets do not collapse when a shock idles labor.
            total += basket_quantity * (
                self.full_capacity_labor_ticks() / max(self.ticks_per_worker_day, EPSILON)
            )
        return total

    def throughput_demands(self) -> Dict[str, float]:
        """Every commodity's throughput demand, in one pass over producers.

        `throughput_demand` is O(producers) and was being called once per
        commodity, inside a fixed point — O(commodities x producers) per
        iteration, which the scale test measured at 84% of a simulated day
        (docs/33).  This computes the same numbers by walking each
        producer's *inputs* instead of scanning every producer for each
        commodity, which is O(producers x inputs).

        Bit-identical to calling `throughput_demand` for each commodity.
        The terms are collected in producer order and handed to `sum`, not
        accumulated with `+=`: CPython's `sum` compensates its float error
        and a running total does not, so the two disagree in the last bit
        wherever a commodity has several consumers.  The equivalence test
        found that; the argument had missed it.
        """
        terms: Dict[str, List[float]] = {}
        for producer in self.producers:
            if not producer.active:
                continue
            runs = producer.process.runs_for(producer.capacity_per_day)
            for name, per_run in producer.process.inputs.items():
                if per_run > 0:
                    terms.setdefault(name, []).append(runs * per_run)
        workers = self.full_capacity_labor_ticks() / max(
            self.ticks_per_worker_day, EPSILON
        )
        totals: Dict[str, float] = {}
        for name in self.prices:
            total = self.base_daily_demand.get(name, 0.0) + sum(
                terms.get(name, ())
            )
            quantity = self.subsistence_basket.get(name, 0.0)
            if quantity > 0.0:
                total += quantity * workers
            totals[name] = total
        return totals

    def full_capacity_labor_ticks(self) -> float:
        """Work-ticks demanded per day if every producer ran at capacity."""
        return sum(
            p.process.runs_for(p.capacity_per_day) * p.process.direct_labor
            for p in self.producers
            if p.active
        )

    def wage_rate(self) -> float:
        """Silver per worker-day: the subsistence basket at current prices."""
        return sum(
            quantity * self.prices.get(name, 0.0)
            for name, quantity in sorted(self.subsistence_basket.items())
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
    #: Material consumed as a production input, kept apart from final
    #: consumption so a unit used up making something else is still a
    #: declared sink rather than a leak.
    intermediate_consumption: Dict[str, float] = field(default_factory=dict)
    #: Silver spent on capacity investment (construction fund).
    investment_spending: float = 0.0
    #: Total commodity extracted from finite reserves.
    reserve_depletion: Dict[str, float] = field(default_factory=dict)
    #: Differential rent: the cost advantage of infra-marginal extractors
    #: over the most expensive active extractor, accumulated per commodity.
    differential_rent: Dict[str, float] = field(default_factory=dict)
    #: The surplus ledger (docs/17), keyed by region, denominated in
    #: work-ticks.  Observational: nothing reads these back.  Money profit
    #: is *not* surplus value; the wage bill in silver sits beside the
    #: labor-time quantities, never mixed into them.
    living_labor: Dict[str, float] = field(default_factory=dict)
    necessary_labor: Dict[str, float] = field(default_factory=dict)
    #: Value of output in work-ticks, accumulated as it is produced and at
    #: the values then prevailing.  A flow, deliberately: revaluing a whole
    #: run at final values would not close when a technique changes
    #: mid-run, and the closing identity is the point (docs/23).
    value_produced: Dict[str, float] = field(default_factory=dict)
    #: Constant capital in work-ticks (docs/23), split into its circulating
    #: and fixed parts.  Circulating is inputs consumed at their own social
    #: labor values; fixed is the capital worn out making the output.
    circulating_capital: Dict[str, float] = field(default_factory=dict)
    fixed_capital_consumed: Dict[str, float] = field(default_factory=dict)
    #: Silver value of the fixed capital consumed, kept beside the labor
    #: figure and never mixed with it.
    fixed_capital_money: Dict[str, float] = field(default_factory=dict)
    #: The unattributed wedge, accumulated in silver.  Either surplus or a
    #: cost the model does not represent; nothing inside the laboratory
    #: distinguishes them, so it is carried under its own name and the
    #: surplus is reported as a band (docs/23).
    unattributed_margin: Dict[str, float] = field(default_factory=dict)
    #: Silver actually paid as wages (money form of variable capital).
    wages_paid: Dict[str, float] = field(default_factory=dict)
    #: Silver workers spent on the basket.
    worker_spending: Dict[str, float] = field(default_factory=dict)
    #: Basket units workers could not obtain — labor-power paid below its
    #: reproduction cost, made visible even though nothing yet acts on it.
    basket_shortfall: Dict[str, float] = field(default_factory=dict)
    transport_cash: float = 0.0
    initial_cash: float = 0.0

    def surplus_labor(self, region: str) -> float:
        """Living labor performed beyond the reproduction cost of labor-power."""
        return self.living_labor.get(region, 0.0) - self.necessary_labor.get(
            region, 0.0
        )

    def constant_capital(self, region: str) -> float:
        """c in work-ticks: circulating inputs plus fixed capital consumed."""
        return self.circulating_capital.get(
            region, 0.0
        ) + self.fixed_capital_consumed.get(region, 0.0)

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
        construction_cost_multiplier: float = 60.0,
        min_investment_capacity: float = 0.1,
        buffer_refill_horizon_days: float = 60.0,
        labor_value_per_tick: float = 11.4 / 720.0,
        employment_quantum: float = 2.0 ** -20,
        labor_value_tolerance: float = 1e-12,
        labor_value_max_iterations: int = 1000,
        competitive_price_intensity: float = 0.5,
        competitive_share_elasticity: float = 2.0,
        capital_service_life_days: float = 600.0,
        production_price_tolerance: float = 1e-12,
        production_price_max_iterations: int = 1000,
        production_period_days: float = 1.0,
        record_history: bool = True,
        history_every: int = 1,
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
        self.construction_cost_multiplier = construction_cost_multiplier
        self.min_investment_capacity = min_investment_capacity
        self.buffer_refill_horizon_days = buffer_refill_horizon_days
        self.zero_utilization_price_ratio = zero_utilization_price_ratio
        self.full_utilization_price_ratio = full_utilization_price_ratio
        self.labor_value_per_tick = labor_value_per_tick
        self.employment_quantum = employment_quantum
        self.labor_value_tolerance = labor_value_tolerance
        self.labor_value_max_iterations = labor_value_max_iterations
        if competitive_price_intensity < 0.0:
            raise ValueError("competitive_price_intensity must be non-negative")
        if competitive_share_elasticity < 0.0:
            raise ValueError("competitive_share_elasticity must be non-negative")
        self.competitive_price_intensity = competitive_price_intensity
        self.competitive_share_elasticity = competitive_share_elasticity
        self.capital_service_life_days = capital_service_life_days
        self.production_price_tolerance = production_price_tolerance
        self.production_price_max_iterations = production_price_max_iterations
        if production_period_days <= 0.0:
            raise ValueError("production_period_days must be positive")
        #: How long one run occupies its capital before the product
        #: exists.  One `step()`, which is what the runtime does.
        self.production_period_days = production_period_days
        if history_every < 1:
            raise ValueError("history_every must be at least one day")
        #: History is an *output*: nothing in the simulation reads it.
        #: At 647 commodities and 100 regions a full snapshot costs
        #: ~16 MiB a day, which the runtime cannot carry (docs/33).
        self.record_history = record_history
        self.history_every = history_every
        #: Social labor values in work-ticks, solved from the process graph.
        #: Distinct from ``Commodity.labor_value``, which stays the authored
        #: FINDINGS.md figure.  See docs/19.
        self.labor_values: Dict[str, float] = {}
        #: Individual per-region values: own living labor plus inputs at
        #: *social* value.  The gap from the social value is where a region
        #: with better-than-average conditions shows up.
        self.regional_labor_values: Dict[str, Dict[str, float]] = {}
        #: Commodities whose value is held over from an earlier day because
        #: nothing was produced (docs/19 section 4).
        self.stale_labor_values: set = set()
        self.ledger = Ledger(
            initial_cash=sum(
                r.cash + r.worker_cash for r in self.regions.values()
            )
        )
        self.history: List[dict] = []
        #: Throughput demand per region, refreshed once a day.  Capacity
        #: cannot change between the refresh and the end of the day — only
        #: `_complete_projects` and `destroy_capacity` move it, and both
        #: run before it — so this is a rebuild rather than a cache with
        #: an invalidation rule to get wrong.
        self._throughput: Dict[str, Dict[str, float]] = {}

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
        # Nothing has been produced yet, so the first solve weights the
        # installed structure rather than realized output (docs/19).
        self._refresh_throughput()
        self._update_labor_values(use_capacity=True)
        # The seeded sector cost each price anchor is measured against
        # (docs/21).  Recorded once, from the same capacity weights.
        for region in self.regions.values():
            for producer in region.producers:
                self._set_capital_consumption(producer)
        for region in self.regions.values():
            self._update_wage_costs(region)
            for name in self.commodities:
                cost = self._sector_unit_cost(region, name, use_capacity=True)
                if cost is not None:
                    region.seed_unit_cost[name] = cost
                region.cost_ratio.setdefault(name, 1.0)
        #: Opening stock, for the material ledger.  Held as state rather
        #: than read back out of `history[0]`, which was a dependency on an
        #: *output* — and the one docs/34 section 3.3 wrongly asserted did
        #: not exist.
        self.opening_inventory = {
            name: self.system_inventory(name) for name in self.commodities
        }
        self._record_history()

    # ------------------------------------------------------------- public API

    def step(self, days: int = 1) -> None:
        for index in range(days):
            self.day += 1
            self._arrive_shipments()
            self._complete_projects()
            self._refresh_throughput()
            self._produce()
            # Solved from the day's realized runs.  The wage just paid used
            # the value prevailing when the day opened, which keeps the
            # model's one-day propagation rhythm (docs/19 section 6).
            self._update_labor_values()
            # Measured from the same realized runs, and read by the price
            # anchor below (docs/21).
            self._update_cost_ratios()
            self._track_differential_rent()
            self._consume()
            self._workers_consume()
            self._update_prices()
            self._dispatch_arbitrage()
            self._update_expectations()
            if self.day % self.investment_interval_days == 0:
                self._invest()
            self._record_history(final=index == days - 1)

    def _refresh_throughput(self) -> None:
        """Recompute every region's throughput demand for the day."""
        self._throughput = {
            name: region.throughput_demands()
            for name, region in self.regions.items()
        }

    def throughput(self, region: str, commodity: str) -> float:
        """Today's throughput demand, from the daily rebuild."""
        return self._throughput[region][commodity]

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
        initial = self.opening_inventory[commodity]
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
        """Return residual of the currently modelled silver accounts.

        Silver starts in regional pools. It can leave via freight payments
        (to the transport sector) or construction spending (consumed by
        investment). Both are tracked in the ledger.
        """
        return (
            sum(r.cash for r in self.regions.values())
            + sum(r.worker_cash for r in self.regions.values())
            + self.ledger.transport_cash
            + self.ledger.investment_spending
            - self.ledger.initial_cash
        )

    def value_balance(self) -> float:
        """Residual of the value accounting identity, in work-ticks.

        Every unit of value in the period's output either was transferred
        from something consumed making it, or was added by living labor:

            value of output  =  c  +  v  +  s

        A third closing ledger beside material and silver (docs/23).  It is
        a genuine check rather than a tautology: ``c`` is accumulated from
        the material draw and the capital worn out, ``v`` and ``s`` from
        employment and the basket, and the output value from the solved
        labor values — three independent paths that have to agree.
        """
        produced = sum(
            self.ledger.value_produced.get(name, 0.0) for name in self.regions
        )
        constant = sum(
            self.ledger.constant_capital(name) for name in self.regions
        )
        living = sum(
            self.ledger.living_labor.get(name, 0.0) for name in self.regions
        )
        return produced - constant - living

    def organic_composition(self, region: Optional[str] = None) -> Optional[float]:
        """c / v in work-ticks: constant capital over variable capital.

        A value ratio, never a money one.  ``None`` before any waged labor.
        """
        names = [region] if region is not None else list(self.regions)
        variable = sum(self.ledger.necessary_labor.get(n, 0.0) for n in names)
        if variable <= EPSILON:
            return None
        constant = sum(self.ledger.constant_capital(n) for n in names)
        return constant / variable

    def value_rate_of_profit(self, region: Optional[str] = None) -> Optional[float]:
        """s / (c + v) in work-ticks.

        The rate of profit in value terms, which is not money profitability
        and must not be reported as though it were.
        """
        names = [region] if region is not None else list(self.regions)
        variable = sum(self.ledger.necessary_labor.get(n, 0.0) for n in names)
        # Guarded on v, not on c + v: without a wage relation there is no
        # split between necessary and surplus labor, so the rate is
        # undefined rather than zero, even where capital is consumed.
        if variable <= EPSILON:
            return None
        constant = sum(self.ledger.constant_capital(n) for n in names)
        surplus = sum(self.ledger.surplus_labor(n) for n in names)
        return surplus / (constant + variable)

    def price_decomposition(
        self, region_name: str, commodity: str
    ) -> Dict[str, float]:
        """Split a unit's price into what the model can and cannot account for.

        The diagnostic that motivated docs/23.  ``margin`` is the wedge
        between RimWorld's authored price level and inputs + wages +
        capital consumption; it is reported, not explained, because the
        model cannot tell whether it is surplus or an unmodelled cost.

        The two surplus readings name their assumption rather than an
        ordering, because the wedge can be negative — RimWorld's yayo price
        does not quite cover its inputs, wages, and capital consumption —
        and a "lower bound" above an "upper bound" would be nonsense. The
        truth lies between them and the laboratory cannot narrow it.
        """
        region = self.regions[region_name]
        producers = [
            p
            for p in region.producers
            if p.active and p.commodity == commodity
        ]
        if not producers:
            return {}
        weight = sum(p.last_runs for p in producers)
        if weight <= EPSILON:
            weight = float(len(producers))
            shares = {id(p): 1.0 / weight for p in producers}
        else:
            shares = {id(p): p.last_runs / weight for p in producers}

        price = region.prices[commodity]
        inputs = wages = capital = margin = 0.0
        for producer in producers:
            share = shares[id(producer)]
            per_run = producer.process.input_cost_per_run(region.prices)
            units = producer.process.outputs.get(commodity, 0.0)
            inputs += share * (per_run / units if units > EPSILON else 0.0)
            wages += share * producer.wage_cost_per_unit
            capital += share * producer.capital_cost_per_unit
            margin += share * producer.unattributed_margin
        attributable = inputs + wages + capital
        return {
            "price": price,
            "inputs": inputs,
            "wages": wages,
            "capital_consumed": capital,
            "attributable_cost": attributable,
            "margin": margin,
            "surplus_if_margin_is_cost": price - attributable - margin,
            "surplus_if_margin_is_surplus": price - attributable,
        }

    def rate_of_surplus_value(self, region: Optional[str] = None) -> Optional[float]:
        """Cumulative s/v in labor time; ``None`` before any waged labor.

        This is the labor-time ratio (surplus over necessary work-ticks),
        not the money ratio of profit to wages — the two must never be
        presented as one number (docs/17).
        """
        names = [region] if region is not None else list(self.regions)
        necessary = sum(self.ledger.necessary_labor.get(n, 0.0) for n in names)
        if necessary <= EPSILON:
            return None
        living = sum(self.ledger.living_labor.get(n, 0.0) for n in names)
        return (living - necessary) / necessary

    def social_technique(
        self, *, use_capacity: bool = False
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], Dict[str, float]]:
        """Output-weighted input coefficients, direct labor, and gross output.

        The same weighting the labor value solve uses (docs/19): total input
        over total output and total labor over total output, across every
        active producer in every region.  One social technique per commodity,
        so the value system and the price system see the identical
        technology.

        Joint outputs apportion both inputs and labor by ``share_of_cost``,
        which is again what the value solve does.

        Returns ``(inputs, labor, output)`` keyed by commodity; only
        commodities with positive output appear.
        """

        def weight(producer: Producer) -> float:
            if use_capacity:
                return producer.process.runs_for(producer.capacity_per_day)
            return producer.last_runs

        inputs: Dict[str, Dict[str, float]] = {}
        labor: Dict[str, float] = {}
        output: Dict[str, float] = {}
        for region in sorted(self.regions):
            for producer in self.regions[region].producers:
                if not producer.active:
                    continue
                runs = weight(producer)
                if runs <= EPSILON:
                    continue
                process = producer.process
                for name, per_run in sorted(process.outputs.items()):
                    if name not in self.commodities:
                        continue
                    share = process.share_of_cost(name, self.commodities)
                    output[name] = output.get(name, 0.0) + runs * per_run
                    labor[name] = (
                        labor.get(name, 0.0) + runs * process.direct_labor * share
                    )
                    row = inputs.setdefault(name, {})
                    for other, quantity in sorted(process.inputs.items()):
                        row[other] = row.get(other, 0.0) + runs * quantity * share

        priced = {name for name, total in output.items() if total > EPSILON}
        return (
            {
                name: {
                    other: total / output[name]
                    for other, total in sorted(inputs.get(name, {}).items())
                    if total > EPSILON
                }
                for name in sorted(priced)
            },
            {name: labor.get(name, 0.0) / output[name] for name in sorted(priced)},
            {name: output[name] for name in sorted(priced)},
        )

    def social_wage_bundle(self, *, use_capacity: bool = False) -> Dict[str, float]:
        """The subsistence basket per work-tick, averaged over regions.

        ``b / T`` is what enters the augmented input matrix, and both the
        basket and the working day are regional.  Regions are weighted by the
        labor they actually perform, which is the same run-weighting used
        everywhere else and reduces exactly to the common value when they
        agree.  A region that works without a basket contributes a zero
        bundle and correctly pulls the social wage down.

        An empty result means there is no wage relation anywhere.
        """

        def weight(producer: Producer) -> float:
            if use_capacity:
                return producer.process.runs_for(producer.capacity_per_day)
            return producer.last_runs

        bundle: Dict[str, float] = {}
        total_labor = 0.0
        for name in sorted(self.regions):
            region = self.regions[name]
            performed = sum(
                weight(producer) * producer.process.direct_labor
                for producer in region.producers
                if producer.active
            )
            if performed <= EPSILON:
                continue
            total_labor += performed
            ticks = max(region.ticks_per_worker_day, EPSILON)
            for commodity, quantity in sorted(region.subsistence_basket.items()):
                if commodity in self.commodities:
                    bundle[commodity] = (
                        bundle.get(commodity, 0.0)
                        + performed * quantity / ticks
                    )
        if total_labor <= EPSILON:
            return {}
        return {
            name: total / total_labor
            for name, total in sorted(bundle.items())
            if total > EPSILON
        }

    @staticmethod
    def _basic_commodities(
        matrix: Dict[str, Dict[str, float]], priced: List[str]
    ) -> List[str]:
        """Commodities entering the production of every commodity, directly
        or indirectly.

        Sraffa's distinction, and the reason the profit rate comes out where
        it does: ``r`` is fixed by the basic subsystem alone, so a change in a
        non-basic sector's technique moves that sector's price and nothing
        else.
        """
        users: Dict[str, List[str]] = {name: [] for name in priced}
        for consumer in priced:
            for supplier, quantity in matrix[consumer].items():
                if quantity > EPSILON and supplier in users:
                    users[supplier].append(consumer)
        basics: List[str] = []
        for start in priced:
            seen: set = set()
            frontier = [start]
            while frontier:
                current = frontier.pop()
                for consumer in users[current]:
                    if consumer not in seen:
                        seen.add(consumer)
                        frontier.append(consumer)
            if seen >= set(priced):
                basics.append(start)
        return basics

    def prices_of_production(
        self,
        *,
        numeraire: str = "labor_value",
        use_capacity: bool = False,
    ) -> Optional[Dict[str, object]]:
        """Solve the classical price system (docs/26).

        Fold the subsistence basket into the input matrix, so that a unit of
        output advances means of production *and* means of subsistence::

            M[i][j] = a[i][j] + (l[i] / T) * b[j]
            p       = (1 + r) * M * p

        Every sector then earns the same rate on its advances.  This is a
        homogeneous eigen-system: ``1/(1+r)`` is the dominant eigenvalue of
        ``M`` and ``p`` its right eigenvector, fixed only up to scale.

        The wage enters as a physical bundle rather than as money, so no
        authored price can leak into a computation whose whole purpose is to
        be free of one; the money wage is an output, ``p . b / T``.

        **Fixed capital is omitted.** The model's machines are exogenous —
        their money price and embodied labor are imported from the closed
        analysis because buildings are not produced inside the circuit — and
        a price system has nowhere to put such a thing without mixing an
        authored magnitude or a second numeraire into the answer.  docs/24
        bounds what this costs: 0.353% of constant capital.  A capital-goods
        sector is the proper fix and is the next item behind this one.

        This is an observation.  Nothing here feeds back into prices, costs,
        or the order book.

        ``numeraire`` may be ``"labor_value"`` (total price of gross output
        equals its total labor value — Marx's first invariance postulate),
        ``"reference_price"`` (total price equals the authored total), or a
        commodity name (that commodity prices at its reference price).

        Returns ``None`` where the system is undefined: no wage relation
        means the wage cost is zero and every pure-labor good would price at
        zero, which is a degenerate vector rather than an answer.

        A *negative* profit rate is returned rather than refused.  It means
        the technique cannot both pay the basket and replace its means of
        production, which is a finding about the technique and not an error
        in the solve.
        """
        inputs, labor, output = self.social_technique(use_capacity=use_capacity)
        bundle = self.social_wage_bundle(use_capacity=use_capacity)
        priced = sorted(output)
        if not priced or not bundle:
            return None

        matrix: Dict[str, Dict[str, float]] = {}
        for name in priced:
            row = dict(inputs.get(name, {}))
            for commodity, per_tick in bundle.items():
                row[commodity] = row.get(commodity, 0.0) + labor[name] * per_tick
            matrix[name] = row

        # A priced good may not depend on a good nobody produced: its price
        # would be an invention.  Loud, like the value solve's convergence
        # failure, rather than a silent zero.
        for name in priced:
            missing = sorted(
                other
                for other, quantity in matrix[name].items()
                if quantity > EPSILON and other not in output
            )
            if missing:
                raise RuntimeError(
                    f"cannot price {name!r}: its technique requires "
                    f"{missing}, which nothing produced"
                )

        # Turnover: capital is advanced for one production period plus the
        # commodity's own inventory life, not for a single day (docs/30).
        turnover = {
            name: self.production_period_days
            + self.commodities[name].target_inventory_days
            for name in priced
        }
        longest = max(turnover.values())

        seed = {
            name: max(self.labor_values.get(name, 0.0), EPSILON)
            for name in priced
        }
        scale = sum(output[name] * seed[name] for name in priced)
        seed = {name: value / scale for name, value in seed.items()}

        def root(rate: float) -> Tuple[float, Dict[str, float], int]:
            factor = {name: 1.0 + rate * turnover[name] for name in priced}
            return self._perron_root(matrix, output, priced, seed, factor)

        # Bisect on the rate at which the system exactly reproduces itself:
        # the Perron root of diag(1 + r*tau) M is non-decreasing in r, since
        # every entry is, so the root is unique where it exists.
        if longest == min(turnover.values()):
            # Uniform turnover is a scalar, not a diagonal: diag(1 + r*tau)
            # factors out and the system is exactly the pre-turnover
            # eigenproblem with r = (k - 1)/tau (docs/30 section 3.2).
            # Solved in closed form rather than searched for, so that the
            # invariance is bit-exact instead of bisection-exact.
            eigenvalue, prices, iterations = self._perron_root(
                matrix, output, priced, seed, {name: 1.0 for name in priced}
            )
            profit_rate = (1.0 / eigenvalue - 1.0) / longest
            low = high = profit_rate
        else:
            low, high = 0.0, 1.0
        if low != high and root(0.0)[0] > 1.0:
            # The system cannot replace its advances even for nothing, so
            # the rate is negative.  Searched for rather than refused: a
            # negative rate is a finding about the technique.  The floor
            # keeps every sector's outlay at half its cost, well clear of
            # the point where the markup would turn an advance into a
            # rebate.
            low, high = -0.5 / longest, 0.0
            if root(low)[0] > 1.0:
                raise RuntimeError(
                    "no rate of profit reproduces this technique: the "
                    "system cannot replace its advances even at the lowest "
                    "rate that keeps every sector's outlay positive"
                )
        elif low != high:
            for _ in range(64):
                if root(high)[0] >= 1.0:
                    break
                high *= 2.0
            else:
                raise RuntimeError(
                    "no rate of profit reproduces this technique: the "
                    "Perron root stays below one at every rate tried"
                )
        if low != high:
            for _ in range(200):
                middle = 0.5 * (low + high)
                if root(middle)[0] < 1.0:
                    low = middle
                else:
                    high = middle
                if high - low <= self.production_price_tolerance * max(
                    1.0, abs(high)
                ):
                    break
            profit_rate = 0.5 * (low + high)
            eigenvalue, prices, iterations = root(profit_rate)

        if numeraire == "labor_value":
            target = sum(
                output[name] * self.labor_values.get(name, 0.0) for name in priced
            )
        elif numeraire == "reference_price":
            target = sum(
                output[name] * self.commodities[name].reference_price
                for name in priced
            )
        elif numeraire in self.commodities:
            if prices.get(numeraire, 0.0) <= EPSILON:
                raise ValueError(
                    f"cannot normalize on {numeraire!r}: its price of "
                    "production is zero"
                )
            target = (
                self.commodities[numeraire].reference_price
                / prices[numeraire]
            )
        else:
            raise ValueError(f"unknown numeraire {numeraire!r}")
        prices = {name: value * target for name, value in prices.items()}

        # The aggregate markup of the solved system: gross output at its
        # production price over gross output at cost.  Scale-invariant, and
        # exactly ``r * turnover`` where the turnover time is uniform.
        cost = sum(
            output[name]
            * sum(
                quantity * prices[other]
                for other, quantity in matrix[name].items()
            )
            for name in priced
        )
        revenue = sum(output[name] * prices[name] for name in priced)

        return {
            # Profit per period on capital *advanced* (docs/30).
            "profit_rate": profit_rate,
            # The factor by which price exceeds cost: the quantity docs/26
            # through docs/29 reported as the profit rate, kept under an
            # honest name.  Equal to r times the turnover time where that
            # time is uniform.
            "gross_markup": revenue / cost - 1.0 if cost > EPSILON else 0.0,
            "turnover_days": turnover,
            "prices": prices,
            "wage": sum(
                per_tick * prices[name]
                for name, per_tick in bundle.items()
                if name in prices
            ),
            "basics": self._basic_commodities(matrix, priced),
            "iterations": iterations,
        }

    def _perron_root(
        self,
        matrix: Dict[str, Dict[str, float]],
        output: Dict[str, float],
        priced: List[str],
        seed: Dict[str, float],
        factor: Dict[str, float],
    ) -> Tuple[float, Dict[str, float], int]:
        """Dominant eigenvalue and eigenvector of ``diag(factor) . matrix``.

        Power iteration normalized by gross output, so the scale factor is
        the eigenvalue directly.  Always started from the same seed, so the
        answer does not depend on how many times it has been called.
        """
        prices = dict(seed)
        eigenvalue = 0.0
        for iterations in range(1, self.production_price_max_iterations + 1):
            advanced = {
                name: factor[name]
                * sum(
                    quantity * prices[other]
                    for other, quantity in matrix[name].items()
                )
                for name in priced
            }
            step = sum(output[name] * advanced[name] for name in priced)
            if step <= EPSILON:
                raise RuntimeError(
                    "price of production solve degenerated: nothing is "
                    "advanced to produce anything, so no rate of profit is "
                    "defined"
                )
            revised = {name: advanced[name] / step for name in priced}
            converged = abs(
                step - eigenvalue
            ) <= self.production_price_tolerance and all(
                abs(revised[name] - prices[name])
                <= self.production_price_tolerance
                for name in priced
            )
            prices, eigenvalue = revised, step
            if converged:
                return eigenvalue, prices, iterations
        raise RuntimeError(
            "price of production solve did not converge; the augmented "
            "input matrix has no single dominant price vector, which "
            "happens when a subsystem exchanges in a closed cycle that "
            "nothing else enters, so its relative prices oscillate "
            "instead of settling"
        )

    def capital_advanced(self, region: Optional[str] = None) -> Dict[str, float]:
        """Capital tied up in the circuit, in work-ticks (docs/30).

        Measured rather than assumed: the model holds the stock, so this
        reads it.  Three parts, itemized because their sizes are the
        result — commodity capital dominates, and the wage advance the old
        formulation effectively charged profit against is a rounding error
        beside it.

        Commodity capital is attributed once, to whichever region holds it,
        which is also how the price system avoids double counting: each
        unit is somebody's unsold output for exactly its inventory life
        (docs/30 section 2.3).
        """
        names = [region] if region is not None else sorted(self.regions)
        commodity_capital = sum(
            self.regions[name].inventory.get(commodity, 0.0)
            * self.labor_values.get(commodity, 0.0)
            for name in names
            for commodity in sorted(self.commodities)
        )
        in_transit = sum(
            shipment.quantity * self.labor_values.get(shipment.commodity, 0.0)
            for shipment in self.shipments
            if region is None or shipment.destination == region
        )
        # Installed plant, not depreciation times service life: the machines
        # exist whether or not they ran today.
        fixed = sum(
            producer.process.capital_labor_per_capacity
            * producer.capacity_per_day
            for name in names
            for producer in self.regions[name].producers
            if producer.active
        )
        wage_advance = self.production_period_days * sum(
            self.ledger.necessary_labor.get(name, 0.0) for name in names
        ) / max(float(self.day), 1.0)
        return {
            "commodity_capital": commodity_capital,
            "in_transit": in_transit,
            "fixed_capital": fixed,
            "wage_advance": wage_advance,
            "total": commodity_capital + in_transit + fixed + wage_advance,
        }

    def value_rate_of_profit_on_advances(
        self, region: Optional[str] = None
    ) -> Optional[float]:
        """Surplus per period over capital advanced: the rate of profit.

        Distinct from ``value_rate_of_profit``, which divides by capital
        *consumed* and is therefore profit per unit of throughput rather
        than a rate.  The two differ by the turnover time, and in this model
        that is a factor of nearly sixty (docs/30).
        """
        if self.day <= 0:
            return None
        names = [region] if region is not None else sorted(self.regions)
        necessary = sum(
            self.ledger.necessary_labor.get(name, 0.0) for name in names
        )
        if necessary <= EPSILON:
            return None
        surplus = sum(self.ledger.surplus_labor(name) for name in names)
        advanced = self.capital_advanced(region)["total"]
        if advanced <= EPSILON:
            return None
        return (surplus / float(self.day)) / advanced

    def realized_turnover_days(
        self, region: Optional[str] = None
    ) -> Optional[float]:
        """Capital advanced divided by capital consumed per period.

        How long the circuit actually ties its capital up, against the
        ``1 + target_inventory_days`` the price system assumes.  The gap is
        the finished-goods stock of anything nobody uses as an input, which
        no cost flow accounts for.
        """
        if self.day <= 0:
            return None
        names = [region] if region is not None else sorted(self.regions)
        consumed = sum(
            self.ledger.constant_capital(name)
            + self.ledger.necessary_labor.get(name, 0.0)
            for name in names
        ) / float(self.day)
        if consumed <= EPSILON:
            return None
        return self.capital_advanced(region)["total"] / consumed

    def production_price_aggregates(
        self, *, use_capacity: bool = False
    ) -> Optional[Dict[str, float]]:
        """Marx's two aggregate equalities, measured rather than assumed.

        Normalized so that total price equals total value, the first
        postulate holds by construction.  The second — total profit equals
        total surplus value — then does not, and the gap is reported as a
        positive result rather than absorbed by choosing a kinder
        normalization (docs/26 section 3.6).

        Surplus is the daily flow implied by the same social technique, not
        the ledger's cumulative figure, so that both sides describe the same
        period.
        """
        system = self.prices_of_production(
            numeraire="labor_value", use_capacity=use_capacity
        )
        if system is None:
            return None
        _, labor, output = self.social_technique(use_capacity=use_capacity)
        bundle = self.social_wage_bundle(use_capacity=use_capacity)
        prices = system["prices"]

        total_price = sum(output[name] * prices[name] for name in output)
        total_value = sum(
            output[name] * self.labor_values.get(name, 0.0) for name in output
        )
        # Profit is what price exceeds cost.  Read off the gross markup
        # rather than the profit rate, since with turnover the two differ
        # by the turnover time and only the markup is per unit of cost.
        markup = system["gross_markup"]
        total_profit = total_price - total_price / (1.0 + markup)

        living = sum(output[name] * labor[name] for name in output)
        basket_value = sum(
            per_tick * self.labor_values.get(name, 0.0)
            for name, per_tick in bundle.items()
        )
        necessary = living * basket_value
        return {
            "total_price": total_price,
            "total_value": total_value,
            "total_profit": total_profit,
            "total_surplus": living - necessary,
            "living_labor": living,
            "necessary_labor": necessary,
        }

    def system_inventory(self, commodity: str) -> float:
        held = sum(r.inventory.get(commodity, 0.0) for r in self.regions.values())
        in_transit = sum(
            s.quantity for s in self.shipments if s.commodity == commodity
        )
        return held + in_transit

    def series(self, region: str, commodity: str, field: str = "price") -> List[float]:
        """One value per day, indexed by day.

        Callers index this positionally and read the index as a day number.
        A sampled or disabled history cannot honour that, so it refuses
        rather than returning a shorter list that would be silently
        mis-indexed — which would corrupt every shock metric in the frozen
        reference without failing anything (docs/34 section 3.2).
        """
        if not self.record_history:
            raise RuntimeError(
                "no series: this economy was built with record_history=False"
            )
        if self.history_every != 1:
            raise RuntimeError(
                "no series: this economy samples history every "
                f"{self.history_every} days, so a positional index is not a "
                "day; read `history` directly, where each snapshot carries "
                "its own day"
            )
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
                entrant = Producer(
                    project.name,
                    project.commodity,
                    project.capacity_per_day,
                    project.unit_cost,
                    self.zero_utilization_price_ratio,
                    self.full_utilization_price_ratio,
                    process=project.process
                    or self.known_processes[project.commodity],
                )
                self._set_capital_consumption(entrant)
                region.producers.append(entrant)
            region.projects = pending

    def _produce(self) -> None:
        """Run every process against the region's opening inventory.

        Production is simultaneous: all producers draw on the stock the day
        opened with, and output lands only once every draw is done, so the
        result does not depend on the order producers sit in a list. A shock
        therefore takes one day per production stage to travel downstream,
        which is a visible property rather than a hidden one.
        """
        # Per-region daily extraction, keyed by (region_name, commodity).
        # Read by _track_differential_rent after all regions have produced.
        self._daily_extraction: Dict[Tuple[str, str], float] = {}

        for region in self.regions.values():
            # Unmet demand is rebuilt from scratch each day. Production adds
            # input shortfalls, consumption adds final shortfalls.
            for name in self.commodities:
                region.unmet_demand[name] = 0.0

            # Update extraction unit costs from current marginal grade.
            for name, reserve in region.reserves.items():
                marginal = reserve.marginal_cost()
                for producer in region.producers:
                    if producer.active and producer.commodity == name:
                        producer.unit_cost = marginal

            # Refreshed daily for every producer, so a producer added by any
            # path — seeding, an investment project, or a scenario reaching
            # in directly — always carries the capital its technique implies.
            for producer in region.producers:
                if producer.active:
                    self._set_capital_consumption(producer)

            self._update_wage_costs(region)

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

            # Reserve rationing: limit extraction to remaining reserve,
            # pro-rata across producers sharing the same reserve.
            for rname, reserve in region.reserves.items():
                if reserve.remaining <= EPSILON:
                    for p in active:
                        if p.commodity == rname:
                            planned[id(p)] = 0.0
                    continue
                total_wanted = 0.0
                for p in active:
                    if p.commodity == rname:
                        out_per_run = p.process.outputs.get(rname, 0.0)
                        total_wanted += planned[id(p)] * out_per_run
                if total_wanted > reserve.remaining:
                    reserve_ration = reserve.remaining / total_wanted
                    for p in active:
                        if p.commodity == rname:
                            planned[id(p)] *= reserve_ration

            # Labor-pool rationing: when planned labor exceeds the regional
            # pool, all producers scale by the same factor — pro-rata and
            # proportional, the same pattern as reserve rationing.  When the
            # pool does not bind this is an exact no-op (skipped, not
            # multiplied by 1.0).
            if region.labor_pool != float("inf"):
                available_ticks = region.labor_pool * region.ticks_per_worker_day
                planned_ticks = sum(
                    planned[id(p)] * p.process.direct_labor for p in active
                )
                if planned_ticks > available_ticks:
                    labor_ration = available_ticks / planned_ticks
                    for p in active:
                        planned[id(p)] *= labor_ration

            drawn: Dict[str, float] = {}
            produced: Dict[str, float] = {}
            labor_performed = 0.0
            for producer in region.producers:
                producer.last_runs = 0.0
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
                producer.last_runs = runs
                labor_performed += runs * producer.process.direct_labor
                # Constant capital, in ticks and in silver (docs/23).  The
                # circulating part is booked below from the material draw;
                # the fixed part is the plant worn out making this output.
                own_output = runs * producer.process.outputs.get(
                    producer.commodity, 0.0
                )
                if own_output > EPSILON:
                    Ledger.add(
                        self.ledger.fixed_capital_consumed,
                        region.name,
                        own_output * producer.capital_labor_per_unit,
                    )
                    Ledger.add(
                        self.ledger.fixed_capital_money,
                        region.name,
                        own_output * producer.capital_cost_per_unit,
                    )
                    Ledger.add(
                        self.ledger.unattributed_margin,
                        region.name,
                        own_output * producer.unattributed_margin,
                    )
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
                # Circulating constant capital: inputs consumed, valued at
                # their own social labor values.
                Ledger.add(
                    self.ledger.circulating_capital,
                    region.name,
                    amount * self.labor_values.get(name, 0.0),
                )
            for name, amount in produced.items():
                region.inventory[name] += amount
                Ledger.add(self.ledger.production, name, amount)
                # Valued at the labor values the day opened with, the same
                # prevailing values the inputs above were charged at, so the
                # two sides of the identity are measured on one basis.
                Ledger.add(
                    self.ledger.value_produced,
                    region.name,
                    amount * self.labor_values.get(name, 0.0),
                )

            # Deduct from reserves and track depletion.
            for rname, reserve in region.reserves.items():
                extracted = produced.get(rname, 0.0)
                if extracted > EPSILON:
                    reserve.extract(extracted)
                    Ledger.add(self.ledger.reserve_depletion, rname, extracted)
                    self._daily_extraction[(region.name, rname)] = extracted

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

            # The wage relation (docs/17).  Employment is quantized to an
            # exact binary grid so that the daily basket flow adds to and
            # subtracts from inventory without rounding — the equilibrium
            # must stay exact to the bit.  Wages are paid on labor actually
            # performed, at the basket's cost at current prices.
            if self.employment_quantum > 0.0:
                worker_days = (
                    floor(
                        (labor_performed / region.ticks_per_worker_day)
                        / self.employment_quantum
                    )
                    * self.employment_quantum
                )
            else:
                worker_days = labor_performed / region.ticks_per_worker_day
            region.worker_days_earned = worker_days
            if region.subsistence_basket:
                wage_bill = worker_days * region.wage_rate()
                if wage_bill > region.cash:
                    # Credit and bankruptcy are deliberately absent.  A
                    # scenario that bankrupts a region must fail loudly,
                    # not silently stop paying workers.
                    raise RuntimeError(
                        f"region {region.name!r} cannot cover its wage bill "
                        f"({wage_bill:.3f} silver against {region.cash:.3f})"
                    )
                region.cash -= wage_bill
                region.worker_cash += wage_bill
                Ledger.add(self.ledger.wages_paid, region.name, wage_bill)
                Ledger.add(
                    self.ledger.living_labor, region.name, labor_performed
                )
                # The value of labor-power: the basket at endogenous social
                # labor values, so it moves when the conditions of producing
                # wage goods move.  This is what makes s/v an outcome rather
                # than a coefficient (docs/19 section 6).
                necessary_per_day = self.basket_labor_value(region)
                Ledger.add(
                    self.ledger.necessary_labor,
                    region.name,
                    worker_days * necessary_per_day,
                )

    def _workers_consume(self) -> None:
        """Workers spend yesterday's wages on the subsistence basket.

        Purchases are capped by inventory per good and jointly by worker
        cash, scaled proportionally when either binds.  A shortfall is real
        unmet demand for the basket good — labor-power paid below its
        reproduction cost must register as a price signal — and is also
        accumulated in the ledger so tests can see it directly.  The silver
        leg returns worker cash to the regional pool, closing the circuit
        producer -> wage -> worker -> basket purchase -> producer revenue.
        """
        for region in self.regions.values():
            if region.subsistence_basket:
                worker_days = region.worker_days_due
                purchases: List[Tuple[str, float, float]] = []
                total_cost = 0.0
                for name, quantity in sorted(region.subsistence_basket.items()):
                    if name not in self.commodities:
                        continue
                    desired = quantity * worker_days
                    if desired <= 0.0:
                        continue
                    bought = min(desired, region.inventory.get(name, 0.0))
                    inventory_shortfall = desired - bought
                    if inventory_shortfall > EPSILON:
                        region.unmet_demand[name] += inventory_shortfall
                        Ledger.add(
                            self.ledger.basket_shortfall,
                            region.name,
                            inventory_shortfall,
                        )
                    if bought <= 0.0:
                        continue
                    purchases.append((name, bought, region.prices[name]))
                    total_cost += bought * region.prices[name]
                cash_factor = 1.0
                if total_cost > region.worker_cash:
                    cash_factor = region.worker_cash / total_cost
                for name, bought, price in purchases:
                    if cash_factor < 1.0:
                        affordable = bought * cash_factor
                        denied = bought - affordable
                        region.unmet_demand[name] += denied
                        Ledger.add(
                            self.ledger.basket_shortfall, region.name, denied
                        )
                        bought = affordable
                    if bought <= 0.0:
                        continue
                    spend = bought * price
                    region.inventory[name] -= bought
                    region.consumed_total[name] += bought
                    Ledger.add(self.ledger.consumption, name, bought)
                    region.worker_cash -= spend
                    region.cash += spend
                    Ledger.add(
                        self.ledger.worker_spending, region.name, spend
                    )
            region.worker_days_due = region.worker_days_earned

    def _track_differential_rent(self) -> None:
        """Compute Ricardian differential rent across regions.

        For each extraction commodity with reserves, the most expensive active
        extractor sets the reference marginal cost. Every region with a lower
        marginal cost earns rent on the amount it extracted today.

        Must be called after ``_produce()`` so that ``_daily_extraction`` is
        populated for the current step.
        """
        commodity_marginals: Dict[str, List[Tuple[str, float, float]]] = {}
        for rname, region in self.regions.items():
            for cname, reserve in region.reserves.items():
                mc = reserve.marginal_cost()
                extracted = self._daily_extraction.get((rname, cname), 0.0)
                if mc < float("inf") and extracted > EPSILON:
                    commodity_marginals.setdefault(cname, []).append(
                        (rname, mc, extracted)
                    )

        for cname, entries in commodity_marginals.items():
            if len(entries) < 2:
                continue
            global_marginal = max(mc for _, mc, _ in entries)
            for _rname, local_mc, extracted in entries:
                advantage = global_marginal - local_mc
                if advantage > EPSILON:
                    Ledger.add(
                        self.ledger.differential_rent,
                        cname,
                        advantage * extracted,
                    )

    def _update_labor_values(self, *, use_capacity: bool = False) -> None:
        """Solve labor values from the process graph (docs/19).

        Value in work-ticks is transferred value (inputs at their own social
        values) plus living labor, per unit of output, aggregated over all
        active producers in every region: total labor over total output, so
        a producer's weight is its realized share of supply.

        This is a fixed point in ``v`` and is iterated rather than inverted:
        iteration converges exactly when the input matrix is productive,
        which is the same condition under which the economy can reproduce
        itself, and it survives a cyclic graph that no topological pass
        could answer at all.  Failure to converge is an explicit error, not
        a returned number.

        ``use_capacity`` seeds the very first solve, before anything has
        been produced, from installed capacity instead of realized runs.
        """

        def weight(producer: Producer) -> float:
            if use_capacity:
                return producer.process.runs_for(producer.capacity_per_day)
            return producer.last_runs

        contributors: List[Producer] = [
            producer
            for region in self.regions.values()
            for producer in region.producers
            if producer.active and weight(producer) > EPSILON
        ]

        # Total output per commodity fixes which values this solve can
        # determine.  Anything else keeps the value it already had: value
        # describes conditions of production, which do not evaporate because
        # nobody produced today (docs/19 section 4).
        output: Dict[str, float] = {}
        for producer in contributors:
            runs = weight(producer)
            for name, per_run in producer.process.outputs.items():
                if name in self.commodities:
                    output[name] = output.get(name, 0.0) + runs * per_run
        solvable = sorted(
            name for name, total in output.items() if total > EPSILON
        )
        self.stale_labor_values = {
            name for name in self.commodities if name not in solvable
        }

        values = dict(self.labor_values)
        for name in self.commodities:
            values.setdefault(name, 0.0)

        for _ in range(self.labor_value_max_iterations):
            labor: Dict[str, float] = {name: 0.0 for name in solvable}
            for producer in contributors:
                runs = weight(producer)
                process = producer.process
                per_run_total = process.direct_labor + sum(
                    quantity * values.get(name, 0.0)
                    for name, quantity in sorted(process.inputs.items())
                )
                for name in sorted(process.outputs):
                    if name not in labor:
                        continue
                    contributed = (
                        runs
                        * per_run_total
                        * process.share_of_cost(name, self.commodities)
                    )
                    # Fixed capital transfers its own embodied labor to the
                    # product — the part RimWorld's formula omits entirely
                    # (FINDINGS.md; docs/23).  Already apportioned per unit
                    # of output, so it scales with output, not with runs.
                    _, capital_labor = process.capital_consumed_per_unit(
                        name, self.capital_service_life_days, self.commodities
                    )
                    contributed += (
                        runs * process.outputs[name] * capital_labor
                    )
                    labor[name] += contributed
            revised = dict(values)
            for name in solvable:
                revised[name] = labor[name] / output[name]
            if all(
                abs(revised[name] - values[name]) <= self.labor_value_tolerance
                for name in solvable
            ):
                values = revised
                break
            values = revised
        else:
            raise RuntimeError(
                "labor value solve did not converge; the input matrix is "
                "not productive (some commodity consumes more of itself, "
                "directly or indirectly, than it produces)"
            )

        self.labor_values = values

        # Individual values: a region's own living labor plus its inputs at
        # prevailing *social* values.  One pass, no fixed point needed.
        self.regional_labor_values = {}
        for region_name, region in sorted(self.regions.items()):
            region_labor: Dict[str, float] = {}
            region_output: Dict[str, float] = {}
            for producer in region.producers:
                if not producer.active or weight(producer) <= EPSILON:
                    continue
                runs = weight(producer)
                process = producer.process
                per_run_total = process.direct_labor + sum(
                    quantity * self.labor_values.get(name, 0.0)
                    for name, quantity in sorted(process.inputs.items())
                )
                for name, per_run in sorted(process.outputs.items()):
                    if name not in self.commodities:
                        continue
                    _, capital_labor = process.capital_consumed_per_unit(
                        name, self.capital_service_life_days, self.commodities
                    )
                    region_labor[name] = (
                        region_labor.get(name, 0.0)
                        + runs
                        * per_run_total
                        * process.share_of_cost(name, self.commodities)
                        + runs * per_run * capital_labor
                    )
                    region_output[name] = (
                        region_output.get(name, 0.0) + runs * per_run
                    )
            self.regional_labor_values[region_name] = {
                name: region_labor[name] / total
                for name, total in sorted(region_output.items())
                if total > EPSILON
            }

    def _set_capital_consumption(self, producer: Producer) -> None:
        """Record what fixed capital this producer's technique consumes."""
        money, labor = producer.process.capital_consumed_per_unit(
            producer.commodity,
            self.capital_service_life_days,
            self.commodities,
        )
        producer.capital_cost_per_unit = money
        producer.capital_labor_per_unit = labor

    def _update_wage_costs(self, region: Region) -> None:
        """Price each producer's living labor at the current basket cost.

        Mirrors the marginal-grade update on extraction costs: a daily
        refresh of one component of effective unit cost.  With no
        subsistence basket the rate is zero and every wage cost stays 0.0,
        which keeps bare models bit-identical.

        Called both from ``_produce`` and once at construction, so that the
        seeded sector cost the price anchor is measured against includes
        wages exactly as the daily measurement does.
        """
        if not region.subsistence_basket:
            return
        wage_per_tick = region.wage_rate() / max(
            region.ticks_per_worker_day, EPSILON
        )
        for producer in region.producers:
            if producer.active:
                producer.wage_cost_per_unit = (
                    producer.process.labor_per_unit(
                        producer.commodity, self.commodities
                    )
                    * wage_per_tick
                )

    def _sector_unit_cost(
        self, region: Region, commodity: str, *, use_capacity: bool = False
    ) -> Optional[float]:
        """Output-weighted average effective unit cost of a commodity's sector.

        The same output weighting the social labor value uses (docs/19), for
        the same reason: what the market faces is the cost of the producers
        actually supplying it.  ``use_capacity`` seeds the very first
        measurement, before anything has been produced.  Returns ``None``
        when no producer is active, so the caller can hold the last ratio
        rather than inventing one.
        """
        total_cost = 0.0
        total_output = 0.0
        for producer in region.producers:
            if not producer.active or producer.commodity != commodity:
                continue
            runs = (
                producer.process.runs_for(producer.capacity_per_day)
                if use_capacity
                else producer.last_runs
            )
            if runs <= EPSILON:
                continue
            output = runs * producer.process.outputs.get(commodity, 0.0)
            if output <= EPSILON:
                continue
            total_cost += output * producer.effective_unit_cost(region.prices)
            total_output += output
        if total_output <= EPSILON:
            return None
        return total_cost / total_output

    def _update_cost_ratios(self, *, use_capacity: bool = False) -> None:
        """Refresh each region's cost ratio against its seeded sector cost."""
        for region in self.regions.values():
            for name in self.commodities:
                cost = self._sector_unit_cost(
                    region, name, use_capacity=use_capacity
                )
                seed = region.seed_unit_cost.get(name)
                if cost is None or seed is None or seed <= EPSILON:
                    # Hold the last ratio: cost describes conditions of
                    # production, which do not vanish because nobody
                    # produced today.
                    region.cost_ratio.setdefault(name, 1.0)
                    continue
                region.cost_ratio[name] = cost / seed

    def basket_labor_value(self, region: Region) -> float:
        """Work-ticks needed to reproduce one worker-day of labor-power.

        The subsistence basket at *social* labor values: the value of
        labor-power is a social magnitude, not a regional one.
        """
        return sum(
            quantity * self.labor_values.get(name, 0.0)
            for name, quantity in sorted(region.subsistence_basket.items())
            if name in self.commodities
        )

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
            # Worker basket demand due today is a known constant within the
            # plan (wages today, bread tomorrow — docs/17), so it adds no
            # new coupling to the fixed point.
            for name, quantity in sorted(region.subsistence_basket.items()):
                if name in intended_outflow:
                    intended_outflow[name] += quantity * region.worker_days_due

            requested_output: Dict[str, float] = {}
            for name, commodity in self.commodities.items():
                target = (
                    self._throughput[region.name][name]
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

            revised = self._allocate_orders(
                region, active, desired, desired_output, requested_output
            )
            if all(
                abs(revised[key] - planned[key]) <= EPSILON
                for key in revised
            ):
                return revised
            planned = revised
        raise RuntimeError("production-order plan did not converge")

    def _allocate_orders(
        self,
        region: Region,
        active: List[Producer],
        desired: Dict[int, float],
        desired_output: Dict[str, float],
        requested_output: Dict[str, float],
    ) -> Dict[int, float]:
        """Share a commodity's order book among its producers by cost.

        Weights are `desired_output * (cost / cheapest)^-epsilon`, so a
        cheaper producer wins more custom, continuously: a small cost
        advantage wins a small amount of extra business rather than the
        whole book (docs/21).  Each producer is still capped by its own
        price-and-capacity-limited output, and what a capped producer
        cannot take is redistributed among the rest.

        With `epsilon = 0` every weight collapses to `desired_output`, the
        shares become proportional to desired output, and this reduces
        exactly to the uniform factor it replaces — bit-for-bit.
        """
        epsilon_share = self.competitive_share_elasticity
        by_commodity: Dict[str, List[Producer]] = {}
        for producer in active:
            by_commodity.setdefault(producer.commodity, []).append(producer)

        revised: Dict[int, float] = {}
        for name, producers in sorted(by_commodity.items()):
            available_output = desired_output[name]
            if available_output <= EPSILON:
                for producer in producers:
                    revised[id(producer)] = 0.0
                continue
            wanted = min(requested_output[name], available_output)
            if wanted <= EPSILON:
                for producer in producers:
                    revised[id(producer)] = 0.0
                continue

            # Sorted so the arithmetic cannot depend on producer list order.
            producers = sorted(producers, key=lambda p: (p.name, p.commodity))
            ceilings = {
                id(p): desired[id(p)] * p.process.outputs[p.commodity]
                for p in producers
            }
            if epsilon_share <= 0.0:
                weights = {id(p): ceilings[id(p)] for p in producers}
            else:
                costs = {
                    id(p): max(p.effective_unit_cost(region.prices), EPSILON)
                    for p in producers
                }
                cheapest = min(costs.values())
                weights = {
                    id(p): ceilings[id(p)]
                    * (costs[id(p)] / cheapest) ** -epsilon_share
                    for p in producers
                }

            allotted = {id(p): 0.0 for p in producers}
            remaining = wanted
            open_ids = [id(p) for p in producers if ceilings[id(p)] > EPSILON]
            # Water-filling: place what is left among producers still below
            # their own ceiling, until nothing remains or everyone is full.
            for _ in range(len(producers) + 1):
                if remaining <= EPSILON or not open_ids:
                    break
                total_weight = sum(weights[key] for key in open_ids)
                if total_weight <= EPSILON:
                    break
                capped: List[int] = []
                placed = 0.0
                for key in open_ids:
                    share = remaining * weights[key] / total_weight
                    room = ceilings[key] - allotted[key]
                    take = min(share, room)
                    allotted[key] += take
                    placed += take
                    if room - take <= EPSILON:
                        capped.append(key)
                remaining -= placed
                if not capped:
                    break
                open_ids = [key for key in open_ids if key not in capped]

            for producer in producers:
                units = producer.process.outputs[producer.commodity]
                revised[id(producer)] = allotted[id(producer)] / units
        return revised

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
                throughput = self._throughput[region.name][name]
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
                # The anchor moves with the sector's cost relative to its
                # seeded cost (docs/21).  Written in this form because
                # `1 + kappa * (ratio - 1)` is exactly 1.0 when the ratio is
                # exactly 1.0, for any kappa, which is what keeps the
                # four-year equilibrium price range at exactly zero.
                anchor = commodity.reference_price * (
                    1.0
                    + self.competitive_price_intensity
                    * (region.cost_ratio.get(name, 1.0) - 1.0)
                )
                anchor = max(anchor, low)
                desired = anchor * exp(pressure)
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
                    self._throughput[source.name][name]
                    * commodity.target_inventory_days
                )
                destination_target = (
                    self._throughput[destination.name][name]
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
                demand = self._throughput[region.name][name]
                if demand <= 0 or name not in self.known_processes:
                    continue
                existing = region.capacity(name)
                pipeline = sum(
                    p.capacity_per_day for p in region.projects if p.commodity == name
                )

                # --- flow-shortfall investment --------------------------
                flow_shortfall = max(0.0, demand - existing - pipeline)

                # --- buffer-deficit investment --------------------------
                # When stock is below target and existing surplus capacity
                # cannot close the gap within the planning horizon, build
                # enough extra to refill. This is proportional: a larger
                # deficit requests more capacity; a zero deficit requests
                # nothing.
                target_stock = demand * commodity.target_inventory_days
                buffer_deficit = max(0.0, target_stock - region.inventory[name])
                surplus_capacity = max(0.0, existing + pipeline - demand)
                if surplus_capacity > EPSILON:
                    days_to_refill = buffer_deficit / surplus_capacity
                else:
                    days_to_refill = float("inf") if buffer_deficit > EPSILON else 0.0
                if days_to_refill > self.buffer_refill_horizon_days:
                    buffer_need = buffer_deficit / self.buffer_refill_horizon_days
                else:
                    buffer_need = 0.0

                shortfall = flow_shortfall + buffer_need
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
                # Construction costs silver: days of effective cost per unit
                # of daily capacity. Deducted when the project is commissioned.
                construction_unit = (
                    assumed_effective * self.construction_cost_multiplier
                )
                total_cost = amount * construction_unit
                if total_cost > region.cash:
                    # Scale down to what the region can afford.
                    amount = region.cash / max(construction_unit, EPSILON)
                if amount < self.min_investment_capacity:
                    continue
                total_cost = amount * construction_unit
                region.cash -= total_cost
                self.ledger.investment_spending += total_cost
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

    def _record_history(self, *, final: bool = False) -> None:
        """Append a snapshot, in as much detail as this economy records.

        A sampled or disabled history still records the day, so a run can
        say which days it covered.  Day zero and the last day of every
        `step()` are always kept, so a sampled history brackets its own
        range rather than ending somewhere arbitrary.
        """
        if not self.record_history:
            self.history.append({"day": self.day})
            return
        if not (final or self.day % self.history_every == 0):
            self.history.append({"day": self.day})
            return
        self.history.append(
            {
                "day": self.day,
                "system_inventory": {
                    name: self.system_inventory(name) for name in self.commodities
                },
                "labor_values": dict(self.labor_values),
                "regional_labor_values": {
                    name: dict(values)
                    for name, values in self.regional_labor_values.items()
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
                        "worker_cash": region.worker_cash,
                        "cost_ratio": dict(region.cost_ratio),
                        "employment": region.worker_days_earned,
                        "wage_rate": region.wage_rate(),
                        "reserves": {
                            cname: {
                                "remaining": reserve.remaining,
                                "marginal_cost": reserve.marginal_cost(),
                            }
                            for cname, reserve in region.reserves.items()
                        },
                    }
                    for region in self.regions.values()
                },
            }
        )
