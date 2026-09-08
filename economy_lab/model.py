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
    #: Department I (docs/36).  Where this bill is non-empty the two scalars
    #: above stop being authored and become *derived*: ``capital_bill`` is
    #: what one machine is made of, ``capital_construction_labor`` the ticks
    #: it takes to build one, and ``machines_per_capacity`` how many machines
    #: support one unit of daily output.  An empty bill leaves every existing
    #: model bit-identical, which is the same compatibility rule fixed
    #: capital itself shipped under (docs/23).
    capital_bill: Dict[str, float] = field(default_factory=dict)
    capital_construction_labor: float = 0.0
    machines_per_capacity: float = 0.0

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

    def capital_bill_per_capacity(self) -> Dict[str, float]:
        """Commodities needed to build the plant behind one unit of daily output.

        The bill for one machine times the machines a unit of capacity needs.
        Empty where the process carries no bill, which is how every model
        before docs/36 behaves.
        """
        return {
            name: quantity * self.machines_per_capacity
            for name, quantity in sorted(self.capital_bill.items())
        }

    def capital_consumed_per_unit(
        self,
        commodity: str,
        service_life_days: float,
        commodities: Optional[Dict[str, "Commodity"]] = None,
        money_per_capacity: Optional[float] = None,
        labor_per_capacity: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Fixed capital transferred to one unit of output: (silver, ticks).

        Use-based rather than time-based: one unit of daily capacity makes
        one unit a day, so it makes ``service_life_days`` units across the
        life of the capital that supports it.  Unit cost is therefore
        independent of utilization, which keeps idle plant from feeding a
        rising unit cost back into the price anchor (docs/23).

        ``money_per_capacity`` and ``labor_per_capacity`` override the
        authored scalars.  Department I passes the figures it derives from
        the bill of materials, which are prices and values rather than
        constants and so cannot live on a frozen process (docs/36 section
        3.2).  Omitted, the authored scalars are used and nothing moves.
        """
        if service_life_days <= EPSILON:
            return 0.0, 0.0
        share = self.share_of_cost(commodity, commodities or {})
        units = self.outputs.get(commodity, 0.0)
        if units <= EPSILON:
            return 0.0, 0.0
        money = (
            self.capital_money_per_capacity
            if money_per_capacity is None
            else money_per_capacity
        )
        labor = (
            self.capital_labor_per_capacity
            if labor_per_capacity is None
            else labor_per_capacity
        )
        return (
            money * share / service_life_days,
            labor * share / service_life_days,
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
    #: Fraction of the day's plant wear that was actually replaced
    #: (docs/38).  One while the bill is in stock and the producer can
    #: carry the maintenance; less when either fails, and the shortfall
    #: is what capacity is lost by.
    replacement_supplied: float = 1.0
    #: Producer cash (docs/55).  The working capital target is the purse a
    #: producer keeps before distributing the rest to the owners' fund,
    #: recomputed daily from current prices; the idle count is consecutive
    #: days on which runs were planned and none could be paid for, and
    #: reaching ``bankruptcy_idle_days`` removes the producer.
    cash_target: float = 0.0
    liquidity_idle_days: int = 0
    distributed_total: float = 0.0
    #: Firm-posted prices (docs/57): what this producer asks, seeded at
    #: the authored price and moved by its own cost and the pool's
    #: pressure from then on; and the cost it last priced from, so a cost
    #: change passes through in full.  Unread while the rule is off.
    posted_price: float = 0.0
    last_cost: float = 0.0
    #: How much of what this producer offered the order book took today
    #: (docs/58): one when it was allotted everything it wanted to make,
    #: less when custom went elsewhere.  A producer below its sector's
    #: average fill cuts what it asks.
    order_fill: float = 1.0
    #: Procurement (docs/59): the producer's own stock of its output, what
    #: it sold today and yesterday, and sales taken in a market pass but
    #: not yet applied to the stock, so a day's sales come off in one
    #: subtraction the way the pool's did.
    stock: float = 0.0
    sales_today: float = 0.0
    sales_yesterday: float = 0.0
    pending_out: float = 0.0
    #: Demand a buyer brought to this seller after its stock ran out
    #: today: the sell-out that tells a producer to ask more (docs/60).
    #: Yesterday's is kept because it is demand the producer saw and
    #: could not serve, which its plan and its target read (docs/62).
    sellouts_today: float = 0.0
    sellouts_yesterday: float = 0.0
    #: The most this producer was willing to run today at the price it
    #: asked: capacity times the utilization curve.  A sell-out at the
    #: ceiling is scarcity; one below it is a plan that was too small.
    last_ceiling: float = 0.0

    #: The producer's expectation of its demand: an exponential average
    #: of what it saw, formed the way the region forms its expectation
    #: of price (docs/62).  Its plan and its stock target read this, not
    #: one day's sales, so a day a rival took its custom is a day and not
    #: a layoff.
    expected_demand: float = 0.0

    def demand_seen(self) -> float:
        """What this producer sold yesterday plus what it was asked for
        after it ran out: the demand it saw (docs/62)."""
        return self.sales_yesterday + self.sellouts_yesterday
    #: Consecutive days on which this producer's return on its capacity
    #: has been below the going one with a surplus to withdraw (docs/64).
    #: Exit begins when it reaches the investment lead time.  Zero and
    #: unread while the rule is off.
    below_going_days: int = 0
    #: Inputs bought and not yet used.  Production draws exactly what it
    #: uses from here, so a purchase a later input made surplus carries
    #: over rather than being booked as consumed (docs/60).
    inputs_on_hand: Dict[str, float] = field(default_factory=dict)

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

    def capital_draw_per_day(
        self, commodity: str, service_life_days: float
    ) -> float:
        """Matter drawn per day to replace plant, at full capacity.

        The full-capacity convention the derived-input term already uses,
        for the same reason: an idled producer still owns its machines and
        will still need to replace them.  Zero for a process without a bill
        of materials, which is every process before docs/36.
        """
        quantity = self.process.capital_bill_per_capacity().get(commodity, 0.0)
        if quantity <= 0.0:
            return 0.0
        # Associated exactly as `Region.throughput_demands` associates it:
        # capacity times the per-capacity bill, then divided by the service
        # life.  Multiplying the machine count in separately gives a
        # different last bit and the equivalence test would say so.
        return (
            self.capacity_per_day * quantity / max(service_life_days, EPSILON)
        )

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
    #: Service life of fixed capital, mirrored from the economy so the
    #: full-capacity replacement draw can be sized without reaching back
    #: out of the region (docs/36).  Set by ``Economy.__init__``; the
    #: default matches the economy's own so a bare Region is consistent.
    capital_service_life_days: float = 600.0
    #: Fixed daily labor supply in worker-days; infinite means never binding.
    labor_pool: float = float("inf")
    #: Workers' silver.  Wages flow in, basket purchases flow out.
    worker_cash: float = 0.0
    #: Worker-days earned yesterday, whose basket demand is due today
    #: (wages today, bread tomorrow — docs/17 section 6).
    worker_days_due: float = 0.0
    #: Worker-days earned today, stored for tomorrow's basket demand.
    worker_days_earned: float = 0.0
    #: The wage premium (docs/46): the paid wage's deviation from the
    #: basket at current prices, as a fraction.  Zero is wages at the value
    #: of labor-power; it is driven by the employment rate against the
    #: seeded reference and can go negative in a slump.
    wage_premium: float = 0.0
    #: The premium the wages now being spent carried (wages today, bread
    #: tomorrow), so that consumption scales with what was actually paid.
    wage_premium_due: float = 0.0
    #: Employment rate at seeding.  Measured state, like ``seed_unit_cost``,
    #: not a coefficient: it is whatever the seeded circuit repeats.
    reference_employment_rate: float = 0.0
    #: The habitual standard (docs/51): a scale on the basket that a
    #: sustained premium raises and nothing lowers.  The value of
    #: labor-power is the basket times this at social values; the paid
    #: wage is untouched by it.  One at seeding, and every place it enters
    #: is skipped rather than multiplied by one while it stays there.
    habitual_scale: float = 1.0
    #: Procurement (docs/59): stock the owners' fund holds -- imports, and
    #: what a scenario injects -- and sells on at the regional price.
    fund_stock: Dict[str, float] = field(default_factory=dict)
    fund_pending: Dict[str, float] = field(default_factory=dict)
    #: What the fund asks for what it holds, and what it sold today.  The
    #: fund wants to hold nothing, so its price falls while it has stock
    #: and resets to the going price when it has none (docs/60).
    fund_price: Dict[str, float] = field(default_factory=dict)
    fund_sales_today: Dict[str, float] = field(default_factory=dict)
    #: Entry on margin accrued and not yet placed, per commodity
    #: (docs/61, docs/63).  Empty unless the rule is on.
    entry_backlog: Dict[str, float] = field(default_factory=dict)

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
        # Input draw and plant replacement, interleaved producer by
        # producer.  Department I's plant wears out in proportion to output,
        # so replacing it is throughput demand exactly as an input draw is;
        # without it steel would carry a target inventory of zero and sit on
        # the price floor, the same collapse the derived-input term was
        # written to prevent (docs/36).
        #
        # The interleaving is not cosmetic.  `throughput_demands` walks each
        # producer once and appends both terms together, and the two must
        # agree to the bit: summing all the input draws and then all the
        # replacement draws gives a different last bit wherever a commodity
        # is both an input and a means of building plant, which steel is.
        terms: List[float] = []
        for producer in self.producers:
            if not producer.active:
                continue
            terms.append(producer.input_per_day(commodity))
            terms.append(
                producer.capital_draw_per_day(
                    commodity, self.capital_service_life_days
                )
            )
        derived = sum(terms)
        total = self.base_daily_demand.get(commodity, 0.0) + derived
        basket_quantity = self.subsistence_basket.get(commodity, 0.0)
        if basket_quantity > 0.0:
            # Worker demand for a basket good, at full-capacity employment —
            # the same full-capacity convention the derived-input component
            # uses, so targets do not collapse when a shock idles labor.
            # At the habitual standard, where one has formed (docs/51).
            if self.habitual_scale != 1.0:
                basket_quantity = basket_quantity * self.habitual_scale
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
            for name, quantity in (
                producer.process.capital_bill_per_capacity().items()
            ):
                if quantity > 0:
                    terms.setdefault(name, []).append(
                        producer.capacity_per_day
                        * quantity
                        / max(self.capital_service_life_days, EPSILON)
                    )
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
                if self.habitual_scale != 1.0:
                    quantity = quantity * self.habitual_scale
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

    def basket_cost(self) -> float:
        """Silver per worker-day: the subsistence basket at current prices.

        The money form of the value of labor-power -- what reproducing a
        day of labor-power costs at today's prices, with no premium on it.
        """
        return sum(
            quantity * self.prices.get(name, 0.0)
            for name, quantity in sorted(self.subsistence_basket.items())
        )

    def wage_rate(self) -> float:
        """Silver per worker-day actually paid: the basket times one plus
        the wage premium (docs/46).

        Skipped rather than multiplied by one when there is no premium, so
        a model without bargaining is bit-identical to what it was.
        """
        basket = self.basket_cost()
        if self.wage_premium != 0.0:
            return basket * (1.0 + self.wage_premium)
        return basket

    def employment_rate(self) -> float:
        """Yesterday's employment as a fraction of the labor pool.

        Zero when the pool is infinite: an unbounded reserve army means no
        tightening of the labor market is possible, which is the limiting
        case in which the wage stays pinned to value (docs/46 section 2).
        """
        if self.labor_pool == float("inf"):
            return 0.0
        return self.worker_days_earned / self.labor_pool

    def premium_over_value(self) -> float:
        """What the paid wage carries above the *habitual* standard (docs/51).

        ``(1 + π) / h − 1``: the whole premium while the standard is where
        it was seeded, and what habituation has not yet absorbed once it
        has moved.  Returned as the premium itself while ``h`` is one, so
        the reading is identical to ``wage_premium`` for a model without
        the rule.
        """
        if self.habitual_scale == 1.0:
            return self.wage_premium
        return (1.0 + self.wage_premium) / self.habitual_scale - 1.0

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
    #: The part of the wage bill that is premium over the basket, in silver
    #: (docs/46).  Signed: negative when wages are below value.
    wage_premium_paid: Dict[str, float] = field(default_factory=dict)
    #: The labor value workers appropriate beyond -- or short of -- the
    #: reproduction of their labor-power, in work-ticks (docs/46).  Part of
    #: the surplus the wage deviation redistributes; ``necessary_labor``
    #: stays the value of labor-power and this sits beside it.
    wage_deviation_labor: Dict[str, float] = field(default_factory=dict)
    #: Silver workers spent on the basket.
    worker_spending: Dict[str, float] = field(default_factory=dict)
    #: Basket units workers could not obtain — labor-power paid below its
    #: reproduction cost, made visible even though nothing yet acts on it.
    basket_shortfall: Dict[str, float] = field(default_factory=dict)
    #: Matter drawn to rebuild worn plant, by commodity (docs/36).  Also
    #: booked as intermediate consumption, which is what closes the material
    #: identity; this bucket exists so Department I's draw can be read
    #: apart from ordinary input use.
    capital_replacement: Dict[str, float] = field(default_factory=dict)
    #: Matter consumed building *new* plant, by commodity (docs/36 3.4).
    #: Also booked as intermediate consumption, for the same reason as
    #: ``capital_replacement``.
    capital_construction: Dict[str, float] = field(default_factory=dict)
    #: Daily capacity lost to a replacement that did not happen, by
    #: commodity (docs/38).  Not a decay rate: this is only ever the part
    #: of a day's wear that matter or margin refused to make good.
    capacity_lost: Dict[str, float] = field(default_factory=dict)
    #: Living labor spent rebuilding plant, by region.  Part of
    #: ``living_labor``, not additional to it: it is broken out because it
    #: is the one kind of living labor that reaches a product only through
    #: depreciation.
    construction_labor: Dict[str, float] = field(default_factory=dict)
    transport_cash: float = 0.0
    initial_cash: float = 0.0
    #: Producer cash (docs/55).  Silver distributed to each region's owners'
    #: fund; runs a purse could not pay for, by commodity; wages the fund
    #: covered where a purse fell short of its share; and the producers
    #: that failed, as (day, region, name).
    distributions: Dict[str, float] = field(default_factory=dict)
    liquidity_curtailment: Dict[str, float] = field(default_factory=dict)
    fund_wage_support: Dict[str, float] = field(default_factory=dict)
    bankruptcies: List[Tuple[int, str, str]] = field(default_factory=list)
    #: Exit (docs/64): capacity withdrawn because its return was below
    #: the going one, as (day, region, producer, capacity).  Also booked
    #: to ``capacity_lost``.  Empty unless the rule is on.
    exits: List[Tuple[int, str, str, float]] = field(default_factory=list)

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
        capacity_exit: bool = False,
        production_price_tolerance: float = 1e-12,
        production_price_max_iterations: int = 1000,
        production_period_days: float = 1.0,
        record_history: bool = True,
        history_every: int = 1,
        wage_bargaining_strength: float = 0.0,
        wage_bargaining_speed: float = 0.1,
        habituation_speed: float = 0.0,
        producer_cash: bool = False,
        working_capital_days: float = 5.0,
        bankruptcy_idle_days: int = 30,
        posted_prices: bool = False,
        posted_price_speed: float = 0.02,
        posted_share_gain: float = 1.0,
        procurement: bool = False,
        going_margin: float = 0.50,
        idle_capacity_gain: float = 1.0,
        entry_on_margin: bool = False,
        entry_gain: float = 0.05,
        exit_on_return: bool = False,
        capacity_reserve: float = 0.10,
        exit_gain: float = 1.0,
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
        #: Whether a producer that cannot carry its maintenance sheds
        #: capacity (docs/38 section 2.2).  Off by default: turning it
        #: on deletes the component sector, which is a real consequence
        #: of a real RimWorld price and is the scenario's whole point.
        self.capacity_exit = capacity_exit
        #: The reserve-army wage rule (docs/46).  ``strength`` is how far
        #: the wage premium moves per unit change in the employment rate;
        #: ``speed`` is the fraction of the gap to that target closed each
        #: day.  Zero strength is wages at value, and bit-identical.
        if wage_bargaining_strength < 0.0:
            raise ValueError("wage_bargaining_strength must be non-negative")
        if not 0.0 <= wage_bargaining_speed <= 1.0:
            raise ValueError("wage_bargaining_speed must be between zero and one")
        self.wage_bargaining_strength = wage_bargaining_strength
        self.wage_bargaining_speed = wage_bargaining_speed
        if not 0.0 <= habituation_speed <= 1.0:
            raise ValueError("habituation_speed must be between zero and one")
        #: How fast a sustained premium becomes the habitual standard
        #: (docs/51).  Zero, the default, is bit-identical to no rule.
        self.habituation_speed = habituation_speed
        #: Whether producers hold silver and pay from it (docs/55).  Off by
        #: default: every purse stays empty and every payment path is the
        #: regional one, bit-identical.
        self.producer_cash = producer_cash
        if working_capital_days < 0.0:
            raise ValueError("working_capital_days must be non-negative")
        self.working_capital_days = working_capital_days
        self.bankruptcy_idle_days = bankruptcy_idle_days
        #: Whether producers post their own prices and the authored price
        #: is only where they start (docs/57).  Off by default, and the
        #: anchored rule of docs/21 is bit-identical.
        self.posted_prices = posted_prices
        #: The integral gain on the pool's pressure, and the weight on a
        #: producer's own order fill against its sector's (docs/58).  The
        #: anchored rule's speed is a proportional gain on a level and
        #: cannot be reused as an integral gain: docs/58 section 2 records
        #: what happened when it was.
        if posted_price_speed < 0.0:
            raise ValueError("posted_price_speed must be non-negative")
        self.posted_price_speed = posted_price_speed
        self.posted_share_gain = posted_share_gain
        #: Whether producers own their output and buy their inputs from
        #: each other at posted prices (docs/59).  Needs purses to pay
        #: from and prices to ask; off by default and bit-identical off.
        if procurement and not (producer_cash and posted_prices):
            raise ValueError(
                "procurement needs producer_cash and posted_prices switched on"
            )
        self.procurement = procurement
        #: The going margin over cost (docs/62): a producer with capacity
        #: idle and a margin above it cuts to sell more, in proportion to
        #: both.  Above every seeded margin by default, so the seeded
        #: circuit is stationary and the rule speaks only after a shock.
        if going_margin <= 0.0:
            raise ValueError("going_margin must be positive")
        if idle_capacity_gain < 0.0:
            raise ValueError("idle_capacity_gain must be non-negative")
        self.going_margin = going_margin
        self.idle_capacity_gain = idle_capacity_gain
        #: Whether capital enters a sector because its expected price
        #: clears the best technique's cost by more than the same going
        #: margin, with no shortfall asked for (docs/61).  Off by default
        #: and bit-identical off: the shortfall term is left exactly as
        #: it is and the entry term is not computed.
        if entry_gain < 0.0:
            raise ValueError("entry_gain must be non-negative")
        self.entry_on_margin = entry_on_margin
        self.entry_gain = entry_gain
        #: Whether a producer whose return on its capacity -- margin times
        #: utilization, against the going margin -- has been below the
        #: going one for the lead time withdraws the capacity beyond a
        #: reserve over the demand it expects (docs/64).  Needs
        #: procurement; off by default and bit-identical off.
        if exit_on_return and not procurement:
            raise ValueError("exit_on_return needs procurement switched on")
        if capacity_reserve < 0.0:
            raise ValueError("capacity_reserve must be non-negative")
        if exit_gain < 0.0:
            raise ValueError("exit_gain must be non-negative")
        self.exit_on_return = exit_on_return
        self.capacity_reserve = capacity_reserve
        self.exit_gain = exit_gain
        # Mirrored onto every region so the full-capacity replacement
        # draw can be sized inside `throughput_demand` without the
        # region reaching back out to the economy (docs/36).
        for region in self.regions.values():
            region.capital_service_life_days = capital_service_life_days
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
                self._set_capital_consumption(producer, region)
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
        if self.producer_cash:
            self._seed_purses()
        if self.posted_prices:
            self._seed_posted_prices()
        if self.procurement:
            # Reseeds each producer's stock at its own target (docs/62),
            # so the opening inventory is read after it.
            self._seed_stocks()
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
            if self.procurement:
                # The fund and the workers buy from producers' own stocks
                # (docs/59), in place of the pool's two consumption passes.
                self._final_market()
            else:
                self._consume()
                self._workers_consume()
            self._update_prices()
            self._dispatch_arbitrage()
            # Purses above their working capital hand the rest to the
            # owners' fund, before the fund is asked to invest (docs/55).
            self._settle_purses()
            self._update_expectations()
            if self.day % self.investment_interval_days == 0:
                if self.exit_on_return:
                    self._exit()
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
        if self.procurement:
            # What arrives from outside is the fund's to sell (docs/59).
            target = self.regions[region]
            target.fund_stock[commodity] = target.fund_stock.get(commodity, 0.0) + quantity
            self._sync_inventory(target)
        else:
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
            + sum(p.cash for r in self.regions.values() for p in r.producers)
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

    def realized_rate_of_surplus_value(
        self, region: Optional[str] = None
    ) -> Optional[float]:
        """Cumulative s/v with wages as actually paid (docs/46).

        ``rate_of_surplus_value`` takes the wage at the value of labor-power.
        This one moves the line by the labor value the wage premium bought:
        ``(L - v - d) / (v + d)`` with ``d`` the signed
        ``wage_deviation_labor``.  A premium is a deduction from surplus
        value, never a creation of it -- the living labor is what it was --
        which is the same shape as absolute rent in docs/43.  Identical to
        the value rate when there is no premium.
        """
        names = [region] if region is not None else list(self.regions)
        necessary = sum(self.ledger.necessary_labor.get(n, 0.0) for n in names)
        if necessary <= EPSILON:
            return None
        deviation = sum(
            self.ledger.wage_deviation_labor.get(n, 0.0) for n in names
        )
        living = sum(self.ledger.living_labor.get(n, 0.0) for n in names)
        paid = necessary + deviation
        if paid <= EPSILON:
            return None
        return (living - paid) / paid

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

    def social_fixed_capital(
        self, *, use_capacity: bool = False
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
        """The plant behind one unit of output: its bill, and its build labor.

        A *stock*, not a flow: what stands behind a unit of daily output,
        which is ``machines_per_capacity`` machines because a unit of daily
        capacity makes one unit a day.  Divide by the service life for the
        depreciation flow; do not multiply by it, which is the error
        docs/30 section 7.3 made in the other direction.

        Weighted and apportioned exactly as ``social_technique`` weights and
        apportions, so the price system and the value system see one
        technology rather than two.  Empty for every process without a bill
        of materials, which is what keeps the pre-docs/36 price system
        reachable and bit-exact.

        **This is the technique's plant, not the installed stock.**  The
        coefficient is machines per unit of daily output *at full
        utilization*, so an idle producer's plant enters here at what it
        would need if it ran rather than at what it owns.  Prices of
        production are long-period prices for a technique operated normally,
        and Sraffa's system has no notion of utilization at all; charging
        idle plant into them would make a long-period price depend on a
        short-period fact, which is the objection docs/23 raised against
        use-based depreciation in the price anchor.

        The consequence is that this does not equal
        ``capital_advanced()["fixed_capital"]``, which reads the stock the
        model actually holds.  The gap is the idle capacity: 6.8% in the
        capital-goods equilibrium, and small only because the two sectors
        holding 89.6% of the plant both run at capacity (docs/39).
        """

        def weight(producer: Producer) -> float:
            if use_capacity:
                return producer.process.runs_for(producer.capacity_per_day)
            return producer.last_runs

        bill: Dict[str, Dict[str, float]] = {}
        construction: Dict[str, float] = {}
        output: Dict[str, float] = {}
        for region in sorted(self.regions):
            for producer in self.regions[region].producers:
                if not producer.active:
                    continue
                runs = weight(producer)
                if runs <= EPSILON:
                    continue
                process = producer.process
                if not process.capital_bill:
                    for name, per_run in sorted(process.outputs.items()):
                        if name in self.commodities:
                            output[name] = output.get(name, 0.0) + runs * per_run
                    continue
                per_capacity = process.capital_bill_per_capacity()
                for name, per_run in sorted(process.outputs.items()):
                    if name not in self.commodities:
                        continue
                    share = process.share_of_cost(name, self.commodities)
                    units = runs * per_run
                    output[name] = output.get(name, 0.0) + units
                    row = bill.setdefault(name, {})
                    for other, quantity in per_capacity.items():
                        row[other] = row.get(other, 0.0) + units * quantity * share
                    construction[name] = construction.get(name, 0.0) + (
                        units
                        * process.machines_per_capacity
                        * process.capital_construction_labor
                        * share
                    )
        return (
            {
                name: {
                    other: total / output[name]
                    for other, total in sorted(row.items())
                    if total > EPSILON
                }
                for name, row in sorted(bill.items())
                if output.get(name, 0.0) > EPSILON
            },
            {
                name: total / output[name]
                for name, total in sorted(construction.items())
                if output.get(name, 0.0) > EPSILON and total > EPSILON
            },
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
                    # The long-run real wage is the *habitual* standard
                    # (docs/51 section 3); the premium stays out.
                    if region.habitual_scale != 1.0:
                        quantity = quantity * region.habitual_scale
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

        # Fixed capital, where the machines are produced (docs/36 3.5).  The
        # stock standing behind a unit of output: its bill of materials, plus
        # the construction labor folded into the wage bundle exactly as
        # direct labor is, so no money wage leaks into a system whose whole
        # point is to be free of one.  Empty before docs/36, and the branch
        # below keeps that case on the original code path bit for bit.
        plant_bill, plant_labor = self.social_fixed_capital(
            use_capacity=use_capacity
        )
        fixed: Dict[str, Dict[str, float]] = {}
        for name in priced:
            row = dict(plant_bill.get(name, {}))
            build = plant_labor.get(name, 0.0)
            if build > 0.0:
                for commodity, per_tick in bundle.items():
                    row[commodity] = row.get(commodity, 0.0) + build * per_tick
            if row:
                fixed[name] = row
        life = max(self.capital_service_life_days, EPSILON)
        # Cost carries depreciation; the advance carries the whole
        # undepreciated stock.  Combined here so `combined` is exactly
        # `matrix` when there is no plant, which is what makes the
        # no-plant path reduce to the pre-docs/36 one.
        combined: Dict[str, Dict[str, float]] = {}
        for name in priced:
            row = dict(matrix[name])
            for other, quantity in fixed.get(name, {}).items():
                row[other] = row.get(other, 0.0) + quantity / life
            combined[name] = row

        # A priced good may not depend on a good nobody produced: its price
        # would be an invention.  Loud, like the value solve's convergence
        # failure, rather than a silent zero.
        for name in priced:
            missing = sorted(
                other
                for other, quantity in combined[name].items()
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
            if not fixed:
                return self._perron_root(matrix, output, priced, seed, factor)
            # With plant in the advance the system is no longer a scalar
            # times one matrix, because K_i / c_i differs by sector.  The
            # effective row is (1 + r*tau_i)(A_i + F_i/L) + r*F_i:
            # depreciation inside the turnover-inflated cost, the standing
            # stock charged once.  Still non-decreasing in r entry by
            # entry, so the bisection's root is still unique.
            effective: Dict[str, Dict[str, float]] = {}
            for name in priced:
                row = {
                    other: factor[name] * quantity
                    for other, quantity in combined[name].items()
                }
                for other, quantity in fixed.get(name, {}).items():
                    row[other] = row.get(other, 0.0) + rate * quantity
                effective[name] = row
            return self._perron_root(
                effective, output, priced, seed, {name: 1.0 for name in priced}
            )

        # Bisect on the rate at which the system exactly reproduces itself:
        # the Perron root of diag(1 + r*tau) M is non-decreasing in r, since
        # every entry is, so the root is unique where it exists.
        if not fixed and longest == min(turnover.values()):
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
                for other, quantity in combined[name].items()
            )
            for name in priced
        )
        revenue = sum(output[name] * prices[name] for name in priced)
        # What share of the advance is standing plant.  The number docs/30
        # section 3.3 had to report as an omission and could not put in the
        # system; it is in the system now, so it is reported as a share of
        # it.  Zero where nothing carries a bill.
        plant_advance = sum(
            output[name]
            * sum(
                quantity * prices[other]
                for other, quantity in fixed.get(name, {}).items()
            )
            for name in priced
        )
        circulating_advance = sum(
            output[name]
            * turnover[name]
            * sum(
                quantity * prices[other]
                for other, quantity in combined[name].items()
            )
            for name in priced
        )
        advance = circulating_advance + plant_advance

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
            "basics": self._basic_commodities(combined, priced),
            "fixed_capital_share": (
                plant_advance / advance if advance > EPSILON else 0.0
            ),
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
            self.capital_labor_per_capacity(producer.process)
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

    def department_one_output(
        self, region: Optional[str] = None
    ) -> Dict[str, float]:
        """Gross daily output of the commodities that build plant (docs/36).

        The commodities that appear in some process's bill of materials,
        and what was produced of them on the last day.  Empty where no
        process carries a bill, which is the honest answer for a model in
        which the machines are exogenous: there is no Department I.
        """
        makes_plant = {
            name
            for r in self.regions.values()
            for producer in r.producers
            if producer.active
            for name in producer.process.capital_bill
        }
        names = [region] if region is not None else sorted(self.regions)
        output: Dict[str, float] = {}
        for name in names:
            for producer in self.regions[name].producers:
                if not producer.active or producer.commodity not in makes_plant:
                    continue
                output[producer.commodity] = output.get(
                    producer.commodity, 0.0
                ) + producer.last_runs * producer.process.outputs.get(
                    producer.commodity, 0.0
                )
        return output

    def capital_bill_draw(self, region: Optional[str] = None) -> Dict[str, float]:
        """Matter drawn per day to replace worn plant, at the last day's runs.

        The flow side of Department I, against which
        ``department_one_output`` is the supply side.  In a stationary
        state the two agree up to whatever else consumes the same goods.

        Taken at capacity rather than at output, because plant wears on the
        calendar (docs/38 section 2.1) — and because that is the basis
        ``Region.throughput_demand`` has always sized this draw on.
        """
        names = [region] if region is not None else sorted(self.regions)
        draw: Dict[str, float] = {}
        for name in names:
            for producer in self.regions[name].producers:
                if not producer.active or producer.capacity_per_day <= EPSILON:
                    continue
                per_capacity = (
                    producer.capacity_per_day / self.capital_service_life_days
                )
                for other, quantity in (
                    producer.process.capital_bill_per_capacity().items()
                ):
                    draw[other] = draw.get(other, 0.0) + per_capacity * quantity
        return draw

    def sector_organic_composition(
        self, *, use_capacity: bool = False
    ) -> Dict[str, float]:
        """c / v per sector, in work-ticks (docs/42).

        Constant capital per unit of output is the material inputs at their
        own social labor values plus the plant worn out making it; variable
        capital is the living labor times the **value of labor-power** per
        tick, not the money wage.  That distinction is the whole point: an
        organic composition built from the wage in silver would be a price
        ratio wearing a value's name, which is the substitution this project
        has caught itself making three times already.

        The average of these, weighted by output, is what
        ``organic_composition`` reports for a region.  Sectors with no living
        labor are omitted rather than returned as infinity.
        """
        inputs, labor, output = self.social_technique(use_capacity=use_capacity)
        plant_bill, plant_labor = self.social_fixed_capital(
            use_capacity=use_capacity
        )
        life = max(self.capital_service_life_days, EPSILON)
        necessary = 0.0
        weight = 0.0
        for region in self.regions.values():
            if not region.subsistence_basket:
                continue
            ticks = max(region.ticks_per_worker_day, EPSILON)
            necessary += self.value_of_labor_power(region) / ticks
            weight += 1.0
        if weight <= 0.0:
            return {}
        necessary /= weight

        composition: Dict[str, float] = {}
        for name in sorted(output):
            constant = sum(
                quantity * self.labor_values.get(other, 0.0)
                for other, quantity in sorted(inputs.get(name, {}).items())
            )
            constant += (
                sum(
                    quantity * self.labor_values.get(other, 0.0)
                    for other, quantity in sorted(
                        plant_bill.get(name, {}).items()
                    )
                )
                + plant_labor.get(name, 0.0)
            ) / life
            variable = labor[name] * necessary
            if variable <= EPSILON:
                continue
            composition[name] = constant / variable
        return composition

    def price_value_deviation(
        self, *, use_capacity: bool = False
    ) -> Optional[Dict[str, float]]:
        """Production price minus labor value, per unit, in one numeraire.

        Positive where a sector sells above its value under an equalized
        rate of profit, negative where it sells below.  Under the
        ``labor_value`` numeraire the output-weighted sum of these is
        exactly zero by construction, which is the quantitative form of the
        proposition that redistribution through the price system creates no
        value (docs/42 section 5.4).

        ``None`` where the price system is undefined.
        """
        system = self.prices_of_production(use_capacity=use_capacity)
        if system is None:
            return None
        prices = system["prices"]
        return {
            name: prices[name] - self.labor_values.get(name, 0.0)
            for name in sorted(prices)
        }

    def absolute_rent_bound(
        self, *, use_capacity: bool = False
    ) -> Optional[Dict[str, float]]:
        """The most absolute rent could take, per day, by commodity (docs/42).

        Marx's absolute rent is the part of a low-composition sector's
        surplus value that landed property stops the price system from
        redistributing away.  Its ceiling is therefore the amount the price
        system *is* redistributing away — value minus price of production —
        and only where that is positive.  A sector already selling above its
        value has nothing being taken from it and so nothing to withhold.

        Restricted to commodities some region holds a reserve in, because
        absolute rent needs a landlord and only a reserve gives one.

        This is a bound and not a flow.  Nothing collects it: the model has
        no producer-level cash for rent to be paid out of, and no landowner
        class to pay it to (docs/42 section 2).
        """
        deviation = self.price_value_deviation(use_capacity=use_capacity)
        if deviation is None:
            return None
        owned = {
            name
            for region in self.regions.values()
            for name in region.reserves
        }
        _, _, output = self.social_technique(use_capacity=use_capacity)
        return {
            name: max(0.0, -deviation[name]) * output.get(name, 0.0)
            for name in sorted(deviation)
            if name in owned
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
            if self.procurement:
                # An import is the fund's stock, sold on at the regional
                # price (docs/59).
                destination.fund_stock[shipment.commodity] = (
                    destination.fund_stock.get(shipment.commodity, 0.0)
                    + shipment.quantity
                )
                self._sync_inventory(destination)
            else:
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
                self._set_capital_consumption(entrant, region)
                if self.posted_prices:
                    # An entrant posts the going price and prices from its
                    # own cost thereafter (docs/57).
                    entrant.posted_price = region.prices[entrant.commodity]
                    entrant.last_cost = entrant.effective_unit_cost(region.prices)
                if self.producer_cash:
                    # Capitalised from the fund, or with what the fund has
                    # (docs/55).
                    seed = min(
                        max(region.cash, 0.0),
                        self.working_capital_days
                        * self._daily_outlay(entrant, region),
                    )
                    region.cash -= seed
                    entrant.cash += seed
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

        if self.procurement:
            for region in self.regions.values():
                self._produce_procurement(region)
            return

        for region in self.regions.values():
            active = self._open_region_day(region)
            opening = dict(region.inventory)
            desired = {
                id(p): p.desired_runs(region.prices[p.commodity], region.prices) for p in active
            }
            planned = self._planned_runs(region, opening, active, desired)
            if self.posted_prices:
                # What the order book took of what each producer offered
                # (docs/58); read by the posted-price rule tonight.
                for p in active:
                    offered = desired[id(p)]
                    p.order_fill = (
                        planned[id(p)] / offered if offered > EPSILON else 1.0
                    )

            # Pro-rata by requirement, so contention for a scarce shared input
            # is order-independent. Single pass: a producer throttled by some
            # other input leaves its allocation unused, and that slack stays in
            # inventory for tomorrow rather than being reallocated today.
            required: Dict[str, float] = {}
            for producer in active:
                runs = planned[id(producer)]
                for name, per_run in producer.process.inputs.items():
                    required[name] = required.get(name, 0.0) + runs * per_run

            # Department I (docs/36), on the calendar rather than on output
            # (docs/38).  A second pass, not a term inside the first: the
            # actual draw is applied in its own pass too, and the two have to
            # accumulate in the same order or they differ in the last bits
            # wherever a commodity is both an input and a means of building
            # plant, which steel is.
            for producer in active:
                per_capacity = (
                    producer.capacity_per_day / self.capital_service_life_days
                )
                for name, quantity in (
                    producer.process.capital_bill_per_capacity().items()
                ):
                    required[name] = required.get(name, 0.0) + per_capacity * quantity

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

            # Liquidity rationing (docs/55): a producer pays for its inputs,
            # its plant matter and its wages from its own purse, and runs
            # only what it can pay for.  Proportional, like the reserve and
            # labor rations; skipped entirely when producers hold no cash.
            # Yesterday's supply shares say who is paid for today's draws,
            # and are read before today's runs overwrite them.
            yesterday: Dict[str, List[Tuple[Producer, float]]] = {}
            if self.producer_cash:
                yesterday = self._supply_shares(region)
                for p in active:
                    wanted = planned[id(p)]
                    if wanted <= EPSILON:
                        continue
                    per_run = self._outlay_per_run(p, region)
                    spendable = p.cash - self._plant_matter_cost(p, region)
                    if per_run <= EPSILON:
                        continue
                    affordable = max(0.0, spendable) / per_run
                    if affordable < wanted:
                        Ledger.add(
                            self.ledger.liquidity_curtailment,
                            p.commodity,
                            wanted - affordable,
                        )
                        planned[id(p)] = affordable
                    if affordable <= EPSILON:
                        p.liquidity_idle_days += 1
                    else:
                        p.liquidity_idle_days = 0

            drawn: Dict[str, float] = {}
            produced: Dict[str, float] = {}
            labor_by_producer: Dict[int, float] = {}
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
                labor_by_producer[id(producer)] = runs * producer.process.direct_labor
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

            # Plant, in its own pass over every active producer — including
            # producers that made nothing today, because idle plant wears
            # out too.  A shortfall is not throttled and never was; it is
            # taken out of capacity instead (docs/38 section 2.2).
            for producer in active:
                construction = self._replace_plant(
                    region, producer, ration, drawn
                )
                labor_performed += construction
                if construction > 0.0:
                    labor_by_producer[id(producer)] = (
                        labor_by_producer.get(id(producer), 0.0) + construction
                    )
            # Inputs and plant matter are paid for out of the purse before
            # anything is shed, because plant a producer cannot pay for is
            # plant it does not get back (docs/55).
            if self.producer_cash:
                self._pay_for_draws(region, active, ration, yesterday)
            self._shed_capacity(region, active)

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

            self._settle_labor(region, active, labor_by_producer, labor_performed)

    def _open_region_day(self, region: Region) -> List[Producer]:
        """The steps every day opens with, whichever path produces.

        Unmet demand is rebuilt from scratch each day; extraction costs read
        the marginal grade; every producer's capital consumption is
        refreshed; yesterday's employment moves the premium and the
        standard; and the day's labor is priced.  Returns the active
        producers in the order every pass over them uses.
        """
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
                self._set_capital_consumption(producer, region)

        # Yesterday's employment moves today's wage premium, and only
        # then is the day's labor priced (docs/46).  A sustained premium
        # then moves the habitual standard, which prices nothing today
        # but is what the value of labor-power reads (docs/51).
        self._bargain(region)
        self._habituate(region)
        self._update_wage_costs(region)

        if self.posted_prices:
            # A producer that arrived without a price -- an entrant, or one
            # a scenario appended -- asks the going price from its first
            # day.  Before this it was clamped to 18% of its cost, which is
            # the defect docs/58 section 5 mistook for a finding.
            for producer in region.producers:
                if producer.active and producer.posted_price <= 0.0:
                    producer.posted_price = region.prices[producer.commodity]
                    producer.last_cost = producer.effective_unit_cost(region.prices)

        if self.procurement:
            # A producer that arrived without a history expects its
            # capacity share of what its sector expects (docs/62): the
            # plan it makes before it has sold anything.  Its price target
            # is that expectation's inventory life, so what it makes is
            # not excess until it fails to sell, and it raises on nothing
            # until it is making all it would.
            for producer in region.producers:
                if (
                    producer.active
                    and producer.expected_demand == 0.0
                    and producer.stock == 0.0
                    and producer.last_runs == 0.0
                    and producer.sales_yesterday == 0.0
                ):
                    name = producer.commodity
                    peers = [
                        p for p in region.producers if p.active and p.commodity == name
                    ]
                    total = sum(p.capacity_per_day for p in peers)
                    sector = sum(p.expected_demand for p in peers)
                    if sector <= EPSILON:
                        sector = self._throughput[region.name].get(name, 0.0)
                    if total > EPSILON:
                        producer.expected_demand = sector * (
                            producer.capacity_per_day / total
                        )

        return sorted(
            (
                p
                for p in region.producers
                if p.active
                and p.capacity_per_day > 0
                and p.commodity in self.commodities
            ),
            key=lambda p: (p.name, p.commodity),
        )

    def _settle_labor(
        self,
        region: Region,
        active: List[Producer],
        labor_by_producer: Dict[int, float],
        labor_performed: float,
    ) -> None:
        """The wage relation (docs/17), after the day's labor is known.

        Employment is quantized to an exact binary grid so that the daily
        basket flow adds to and subtracts from inventory without rounding —
        the equilibrium must stay exact to the bit.  Wages are paid on labor
        actually performed, at the basket's cost at current prices.
        """
        if True:
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
                if self.producer_cash:
                    # Each producer pays the labor it used (docs/55).
                    self._pay_wages(
                        region, active, labor_by_producer, labor_performed, wage_bill
                    )
                else:
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
                # ... times the habitual standard, where one has formed
                # (docs/51).  The basket at value is what the standard
                # scales; the two are kept as separate readings.
                Ledger.add(
                    self.ledger.necessary_labor,
                    region.name,
                    worker_days * self.value_of_labor_power(region),
                )
                # The deviation of the wage from that value (docs/46), in
                # silver and in the labor value of what the premium buys.
                # Booked apart from ``necessary_labor`` so the value of
                # labor-power never absorbs a bargained premium -- except
                # through habituation, which moves the line deliberately
                # and leaves the two summing to the wage as paid.
                if region.wage_premium != 0.0 or region.habitual_scale != 1.0:
                    Ledger.add(
                        self.ledger.wage_premium_paid,
                        region.name,
                        worker_days * region.basket_cost() * region.wage_premium,
                    )
                    if region.habitual_scale == 1.0:
                        deviation = necessary_per_day * region.wage_premium
                    else:
                        deviation = necessary_per_day * (
                            1.0 + region.wage_premium - region.habitual_scale
                        )
                    Ledger.add(
                        self.ledger.wage_deviation_labor,
                        region.name,
                        worker_days * deviation,
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
                basket_shares = (
                    self._supply_shares(region) if self.producer_cash else {}
                )
                purchases: List[Tuple[str, float, float]] = []
                total_cost = 0.0
                for name, quantity in sorted(region.subsistence_basket.items()):
                    if name not in self.commodities:
                        continue
                    desired = quantity * worker_days
                    # Wages above value buy more than the basket and wages
                    # below it buy less (docs/46 section 3): the premium is
                    # spent, not hoarded, so the silver returns to
                    # producers and the circuit stays closed.
                    if region.wage_premium_due != 0.0:
                        desired *= 1.0 + region.wage_premium_due
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
                    if self.producer_cash:
                        # The basket's sellers are paid (docs/55).
                        spend = self._pay_sellers(
                            region,
                            name,
                            spend,
                            basket_shares,
                            buyer_is_fund=False,
                            units=bought,
                        )
                        region.worker_cash -= spend
                    else:
                        region.worker_cash -= spend
                        region.cash += spend
                    Ledger.add(
                        self.ledger.worker_spending, region.name, spend
                    )
            region.worker_days_due = region.worker_days_earned
            region.wage_premium_due = region.wage_premium

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
                        name,
                        self.capital_service_life_days,
                        self.commodities,
                        labor_per_capacity=self.capital_labor_per_capacity(
                            process, values
                        ),
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
                        name,
                        self.capital_service_life_days,
                        self.commodities,
                        labor_per_capacity=self.capital_labor_per_capacity(
                            process
                        ),
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

    def capital_labor_per_capacity(
        self,
        process: Process,
        values: Optional[Dict[str, float]] = None,
    ) -> float:
        """Embodied labor of the plant behind one unit of daily capacity.

        Authored where the process carries no bill of materials, which is
        every model before docs/36.  Where it carries one, this is the bill
        at prevailing social labor values plus the construction labor —
        endogenous, and circular where a capital good needs capital goods
        to make.  ``values`` lets the value solve pass its current iterate
        instead of the last committed one, which is what makes that circle
        converge rather than lag a day behind.
        """
        if not process.capital_bill:
            return process.capital_labor_per_capacity
        prevailing = self.labor_values if values is None else values
        return process.machines_per_capacity * (
            sum(
                quantity * prevailing.get(name, 0.0)
                for name, quantity in sorted(process.capital_bill.items())
            )
            + process.capital_construction_labor
        )

    def capital_money_per_capacity(
        self, process: Process, region: Optional[Region] = None
    ) -> float:
        """Silver cost of the plant behind one unit of daily capacity.

        The bill at the region's own prices plus the construction labor at
        the region's own wage, so a machine costs what machines cost
        *there*.  Before docs/36 there was no such thing as a regional
        capital cost; the authored MarketValue was the same everywhere, and
        it carried the authored-price wedge docs/24 named.
        """
        if not process.capital_bill or region is None:
            return process.capital_money_per_capacity
        materials = sum(
            quantity * region.prices.get(name, 0.0)
            for name, quantity in sorted(process.capital_bill.items())
        )
        wage_per_tick = (
            region.wage_rate() / max(region.ticks_per_worker_day, EPSILON)
            if region.subsistence_basket
            else 0.0
        )
        return process.machines_per_capacity * (
            materials + process.capital_construction_labor * wage_per_tick
        )

    def _replace_plant(
        self,
        region: Region,
        producer: Producer,
        ration: Dict[str, float],
        drawn: Dict[str, float],
    ) -> float:
        """Rebuild the day's wear on this producer's plant; return its labor.

        **Time-based** (docs/38 section 2.1).  A refinery standing idle rusts
        at the same rate as one running flat out, so the wear is
        ``capacity / L`` and not ``output / L``.  It is also the basis
        ``Region.throughput_demand`` has always used to *size* this draw, so
        before docs/38 the target and the draw were computed on different
        bases; this is the consistency fix as much as the physics.

        The value transferred to the *product* stays use-based, for the
        reason docs/23 gave and which has not changed: idle plant must not
        feed a rising unit cost into the price anchor.  The two bases coexist
        without double counting, because they account for different things.
        The plant consumed transfers ``K/L`` at output; the plant rebuilt is
        new value whose materials come out of stock as circulating capital
        and whose construction labor is living labor performed today.  Sum
        the two identities and every term appears once on each side.

        The gap between them is the fixed cost of idle capacity: plant that
        costs matter to maintain and transfers nothing, because it made
        nothing.  What happens to a producer that cannot carry that cost is
        ``_shed_capacity``.

        Returns zero, and touches nothing, for a process without a bill.
        """
        bill = producer.process.capital_bill_per_capacity()
        if not bill or producer.capacity_per_day <= EPSILON:
            return 0.0
        per_capacity = producer.capacity_per_day / self.capital_service_life_days
        rebuilt = 0.0
        supplied = 1.0
        for name, quantity in bill.items():
            share = ration.get(name, 1.0)
            supplied = min(supplied, share)
            take = per_capacity * quantity * share
            drawn[name] = drawn.get(name, 0.0) + take
            Ledger.add(self.ledger.capital_replacement, name, take)
            rebuilt += take * self.labor_values.get(name, 0.0)
        # Scaled by what actually arrived.  You cannot put up the part of
        # a machine whose steel never came, and booking the full
        # construction labor against a partial delivery would claim plant
        # value that no capacity corresponds to — the flow identity would
        # still close and the stock story would not.
        construction = (
            per_capacity
            * producer.process.machines_per_capacity
            * producer.process.capital_construction_labor
            * supplied
        )
        rebuilt += construction
        Ledger.add(self.ledger.value_produced, region.name, rebuilt)
        Ledger.add(self.ledger.construction_labor, region.name, construction)
        producer.replacement_supplied = supplied
        return construction

    def maintenance_coverage(
        self, region: Region, producer: Producer
    ) -> float:
        """How much of today's maintenance this producer's margin covers.

        The mirror image of the entry rule (docs/38 section 2.2).  `_invest`
        builds where expected revenue clears cost by a margin; this maintains
        in proportion to whether it does.  Continuous and damped, with no
        threshold anywhere: a producer keeping its orders covers maintenance
        many times over and returns exactly 1.0, so nothing moves in a
        stationary state.

        Returns 1.0 unconditionally where the rule is off, which is the
        default and is bit-identical to the model before docs/38.
        """
        if not self.capacity_exit:
            return 1.0
        maintenance = (
            producer.capacity_per_day
            / max(self.capital_service_life_days, EPSILON)
            * self.capital_money_per_capacity(producer.process, region)
        )
        if maintenance <= EPSILON:
            # No plant, nothing to maintain, nothing that can be lost.
            return 1.0
        price = region.prices.get(producer.commodity, 0.0)
        output = producer.last_runs * producer.process.outputs.get(
            producer.commodity, 0.0
        )
        margin = output * (price - producer.effective_unit_cost(region.prices))
        if margin <= 0.0:
            return 0.0
        return min(1.0, margin / maintenance)

    def _shed_capacity(self, region: Region, active: List[Producer]) -> None:
        """Lose the fraction of today's wear that was not made good.

        There is no decay rule here and no exit rule.  Capacity is constant
        while the plant is replaced and falls by exactly the part of the
        day's wear that was not, which is the only honest thing to do with a
        replacement the model has already refused to supply.  Two things can
        refuse it and both are proportional:

        *Matter* — the region could not supply the bill.  This is the debt
        docs/37 section 7 named: before this, a region short of components
        drew what it could, booked the shortfall as unmet demand, and kept
        its capacity anyway.

        *Money* — the producer could not carry the maintenance.  Off by
        default; see ``maintenance_coverage``.

        A producer whose plant is fully replaced loses nothing, so the
        stationary equilibrium is untouched and stays exact to the bit.
        Retirement below 1e-9 is housekeeping and not economics: exponential
        decay never reaches zero, and a list of ten-thousandth-of-a-machine
        producers is a performance problem rather than a market outcome.
        """
        for producer in active:
            if not producer.process.capital_bill:
                # No bill, no wear that matter could fail to replace.  Steel
                # and wood can never lose capacity, and a test says so.
                continue
            supplied = min(
                producer.replacement_supplied,
                self.maintenance_coverage(region, producer),
            )
            if supplied >= 1.0:
                continue
            lost = (
                producer.capacity_per_day
                * (1.0 - supplied)
                / max(self.capital_service_life_days, EPSILON)
            )
            if lost <= 0.0:
                continue
            producer.capacity_per_day -= lost
            Ledger.add(self.ledger.capacity_lost, producer.commodity, lost)
            if producer.capacity_per_day < 1e-9:
                producer.capacity_per_day = 0.0
                producer.active = False

    def _set_capital_consumption(
        self, producer: Producer, region: Optional[Region] = None
    ) -> None:
        """Record what fixed capital this producer's technique consumes."""
        money, labor = producer.process.capital_consumed_per_unit(
            producer.commodity,
            self.capital_service_life_days,
            self.commodities,
            money_per_capacity=self.capital_money_per_capacity(
                producer.process, region
            ),
            labor_per_capacity=self.capital_labor_per_capacity(producer.process),
        )
        producer.capital_cost_per_unit = money
        producer.capital_labor_per_unit = labor

    def _bargain(self, region: Region) -> None:
        """Move the wage premium toward what the reserve army allows (docs/46).

        The target premium is proportional to how far yesterday's
        employment rate sits from the seeded reference, and the premium
        closes a fixed fraction of the gap to it each day.  At the seeded
        equilibrium the rate equals the reference to the bit, so the target
        is exactly zero and the premium never leaves it: the rule is
        exactly stationary where the circuit is.

        Zero strength returns before touching anything, which keeps a
        model without bargaining bit-identical rather than merely close.
        """
        if self.wage_bargaining_strength == 0.0 or not region.subsistence_basket:
            return
        target = self.wage_bargaining_strength * (
            region.employment_rate() - region.reference_employment_rate
        )
        region.wage_premium += self.wage_bargaining_speed * (
            target - region.wage_premium
        )

    def _habituate(self, region: Region) -> None:
        """Let a sustained premium become the habitual standard (docs/51).

        The standard closes a fixed fraction of the gap to the paid real
        wage each day, and only upward: a standard that has risen does not
        fall when the premium goes, so a wage that falls back afterwards is
        a wage below the value of labor-power, reported and not prevented.

        Zero speed returns before touching anything.  At the seeded
        equilibrium the premium is exactly zero, so the gap is exactly zero
        and the standard stays at one to the bit.
        """
        if self.habituation_speed == 0.0 or not region.subsistence_basket:
            return
        gap = (1.0 + region.wage_premium) - region.habitual_scale
        if gap > 0.0:
            region.habitual_scale += self.habituation_speed * gap

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

    def value_of_labor_power(self, region: Region) -> float:
        """The basket at social values, times the habitual standard (docs/51).

        Identical to ``basket_labor_value`` while the standard is one; the
        multiply is skipped rather than done by one so that a model without
        habituation reads the same bits it always has.
        """
        basket = self.basket_labor_value(region)
        if region.habitual_scale == 1.0:
            return basket
        return basket * region.habitual_scale

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

        Convergence is exact equality, not a tolerance.  It used to stop
        once no run moved by more than ``EPSILON``, which left the returned
        plan differing from the plan its own input orders were computed
        from — by up to 1e-9, though in practice 1e-12.  That was invisible
        while the input graph was shallow enough to land on the fixed point
        in one step.  Fixed capital makes it cyclic, the loop started
        stopping one iterate early, and the gap showed up as steel stock
        climbing 9e-13 a day in a supposedly exact equilibrium.  The plan
        is a fixed point or it is an error; there is no third state.
        """
        planned = dict(desired)
        # The same answer on every iteration, so it is computed once.
        grouped = self._grouped_by_commodity(active)
        for _ in range(1000):
            intended_outflow = {
                name: region.daily_demand(commodity)
                for name, commodity in self.commodities.items()
            }
            for producer in active:
                runs = planned[id(producer)]
                for name, per_run in producer.process.inputs.items():
                    intended_outflow[name] += runs * per_run
            # Plant replacement is intended outflow exactly as an input draw
            # is (docs/36), taken on the calendar rather than on output
            # (docs/38) — so it is a constant within this fixed point, and a
            # second pass in the same producer order the actual draw uses.
            for producer in active:
                per_capacity = (
                    producer.capacity_per_day / self.capital_service_life_days
                )
                for name, quantity in (
                    producer.process.capital_bill_per_capacity().items()
                ):
                    if name in intended_outflow:
                        intended_outflow[name] += per_capacity * quantity

            # Worker basket demand due today is a known constant within the
            # plan (wages today, bread tomorrow — docs/17), so it adds no
            # new coupling to the fixed point.
            for name, quantity in sorted(region.subsistence_basket.items()):
                if name in intended_outflow:
                    if region.habitual_scale != 1.0:
                        quantity = quantity * region.habitual_scale
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
                region, active, desired, desired_output, requested_output, grouped
            )
            if revised == planned:
                return revised
            planned = revised
        raise RuntimeError("production-order plan did not converge")

    @staticmethod
    def _grouped_by_commodity(
        active: List[Producer],
    ) -> List[Tuple[str, List[Producer]]]:
        """Producers by commodity, in a deterministic order.

        Sorted by commodity, and each sector's producers sorted by name, so
        the arithmetic cannot depend on the order the producer list happens
        to be in.  Hoisted out of `_allocate_orders` because that runs once
        per iteration of a fixed point while this answer is the same every
        time (docs/36).
        """
        by_commodity: Dict[str, List[Producer]] = {}
        for producer in active:
            by_commodity.setdefault(producer.commodity, []).append(producer)
        return [
            (
                name,
                producers
                if len(producers) == 1
                else sorted(producers, key=lambda p: (p.name, p.commodity)),
            )
            for name, producers in sorted(by_commodity.items())
        ]

    def _allocate_orders(
        self,
        region: Region,
        active: List[Producer],
        desired: Dict[int, float],
        desired_output: Dict[str, float],
        requested_output: Dict[str, float],
        grouped: Optional[List[Tuple[str, List[Producer]]]] = None,
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
        by_commodity = (
            self._grouped_by_commodity(active) if grouped is None else grouped
        )

        revised: Dict[int, float] = {}
        for name, producers in by_commodity:
            keys = [id(p) for p in producers]
            available_output = desired_output[name]
            if available_output <= EPSILON:
                for key in keys:
                    revised[key] = 0.0
                continue
            wanted = min(requested_output[name], available_output)
            if wanted <= EPSILON:
                for key in keys:
                    revised[key] = 0.0
                continue

            ceilings = {
                key: desired[key] * p.process.outputs[p.commodity]
                for key, p in zip(keys, producers)
            }
            if epsilon_share <= 0.0:
                weights = dict(ceilings)
            else:
                # Custom goes to the cheaper producer: by cost under the
                # anchored rule (docs/21), by what it asks under posted
                # prices (docs/57), which is the only force that pulls a
                # sector's posted prices together.
                if self.posted_prices:
                    costs = {
                        key: max(p.posted_price, EPSILON)
                        for key, p in zip(keys, producers)
                    }
                else:
                    costs = {
                        key: max(p.effective_unit_cost(region.prices), EPSILON)
                        for key, p in zip(keys, producers)
                    }
                cheapest = min(costs.values())
                weights = {
                    key: ceilings[key]
                    * (costs[key] / cheapest) ** -epsilon_share
                    for key in keys
                }

            allotted = {key: 0.0 for key in keys}
            remaining = wanted
            open_ids = [key for key in keys if ceilings[key] > EPSILON]
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
            shares = self._supply_shares(region) if self.producer_cash else {}
            for commodity in self.commodities.values():
                desired = region.daily_demand(commodity)
                available = region.inventory[commodity.name]
                consumed = min(desired, available)
                if self.producer_cash:
                    # Final consumption is paid for by the owners' fund
                    # (docs/55), and what the fund cannot pay for is not
                    # consumed -- the same rule workers already face.
                    price = region.prices[commodity.name]
                    affordable = region.cash / max(price, EPSILON)
                    if consumed > affordable:
                        consumed = max(0.0, affordable)
                    credited = self._pay_sellers(
                        region,
                        commodity.name,
                        consumed * price,
                        shares,
                        buyer_is_fund=True,
                        units=consumed,
                    )
                    region.cash -= credited
                unmet = desired - consumed
                region.inventory[commodity.name] -= consumed
                region.unmet_demand[commodity.name] += unmet
                region.consumed_total[commodity.name] += consumed
                Ledger.add(self.ledger.consumption, commodity.name, consumed)

    # ------------------------------------------------------ producer cash

    def _seed_purses(self) -> None:
        """Give every producer its working capital out of the region's
        silver (docs/55).  The economy's silver is what it was; the region
        keeps the rest as the owners' fund."""
        for region in self.regions.values():
            for producer in region.producers:
                if not producer.active:
                    continue
                producer.cash_target = (
                    self.working_capital_days * self._daily_outlay(producer, region)
                )
                seed = min(max(region.cash, 0.0), producer.cash_target)
                region.cash -= seed
                producer.cash = seed

    def _outlay_per_run(self, producer: Producer, region: Region) -> float:
        """Silver one run costs in cash: inputs at regional prices and wages."""
        wage_per_tick = (
            region.wage_rate() / max(region.ticks_per_worker_day, EPSILON)
            if region.subsistence_basket
            else 0.0
        )
        return (
            producer.process.input_cost_per_run(region.prices)
            + producer.process.direct_labor * wage_per_tick
        )

    def _plant_matter_cost(self, producer: Producer, region: Region) -> float:
        """Silver a day's plant replacement costs: the bill at regional
        prices plus the construction labor at the regional wage.  Zero for
        a process without a bill, which pays nothing in cash for the plant
        the ledger charges it for."""
        bill = producer.process.capital_bill_per_capacity()
        if not bill or producer.capacity_per_day <= EPSILON:
            return 0.0
        per_capacity = producer.capacity_per_day / max(
            self.capital_service_life_days, EPSILON
        )
        materials = sum(
            per_capacity * quantity * region.prices.get(name, 0.0)
            for name, quantity in bill.items()
        )
        wage_per_tick = (
            region.wage_rate() / max(region.ticks_per_worker_day, EPSILON)
            if region.subsistence_basket
            else 0.0
        )
        construction = (
            per_capacity
            * producer.process.machines_per_capacity
            * producer.process.capital_construction_labor
            * wage_per_tick
        )
        return materials + construction

    def _daily_outlay(self, producer: Producer, region: Region) -> float:
        """What a day at full capacity costs in cash (docs/55)."""
        runs = producer.process.runs_for(producer.capacity_per_day)
        return runs * self._outlay_per_run(producer, region) + self._plant_matter_cost(
            producer, region
        )

    def _supply_shares(
        self, region: Region
    ) -> Dict[str, List[Tuple[Producer, float]]]:
        """Who is paid for a unit sold out of the region's pool (docs/55).

        Each commodity's producers, weighted by their realized output --
        the share the order book gave them (docs/21) -- or by capacity
        where nobody ran.  A commodity nobody here makes has no sellers,
        and the pool's owner, the fund, is paid instead.
        """
        shares: Dict[str, List[Tuple[Producer, float]]] = {}
        for name in self.commodities:
            producers = [
                p for p in region.producers if p.active and p.commodity == name
            ]
            if not producers:
                continue
            weights = [
                p.last_runs * p.process.outputs.get(name, 0.0) for p in producers
            ]
            total = sum(weights)
            if total <= EPSILON:
                weights = [p.capacity_per_day for p in producers]
                total = sum(weights)
            if total <= EPSILON:
                continue
            shares[name] = [
                (p, w / total) for p, w in zip(producers, weights) if w > 0.0
            ]
        return shares

    def _pay_sellers(
        self,
        region: Region,
        commodity: str,
        amount: float,
        shares: Dict[str, List[Tuple[Producer, float]]],
        *,
        buyer_is_fund: bool,
        units: Optional[float] = None,
    ) -> float:
        """Credit a commodity's sellers with a sale; return what was credited.

        The buyer debits exactly what this returns, so every transfer
        conserves silver to the bit.  With no local sellers the fund is
        paid -- unless the fund is the buyer, in which case nothing moves.
        """
        if amount <= 0.0:
            return 0.0
        sellers = shares.get(commodity)
        if not sellers:
            if buyer_is_fund:
                return 0.0
            region.cash += amount
            return amount
        credited = 0.0
        if self.posted_prices and units is not None:
            # Each seller is paid what it posted, on its share of the
            # units (docs/57); the buyer pays the sum.
            for producer, share in sellers:
                paid = units * share * producer.posted_price
                producer.cash += paid
                credited += paid
            return credited
        for producer, share in sellers:
            paid = amount * share
            producer.cash += paid
            credited += paid
        return credited

    def _pay_for_draws(
        self,
        region: Region,
        active: List[Producer],
        ration: Dict[str, float],
        shares: Dict[str, List[Tuple[Producer, float]]],
    ) -> None:
        """Each producer pays for today's inputs and plant matter (docs/55).

        Inputs were paid for in the liquidity ration, so a purse covers
        them.  Plant matter is taken on the calendar whether or not the
        purse can pay; what it cannot pay for it does not get back, and
        ``replacement_supplied`` says so to ``_shed_capacity``.
        """
        for producer in active:
            runs = producer.last_runs
            if runs > EPSILON:
                for name, per_run in producer.process.inputs.items():
                    credited = self._pay_sellers(
                        region,
                        name,
                        runs * per_run * region.prices.get(name, 0.0),
                        shares,
                        buyer_is_fund=False,
                        units=runs * per_run,
                    )
                    producer.cash -= credited
            bill = producer.process.capital_bill_per_capacity()
            if not bill or producer.capacity_per_day <= EPSILON:
                continue
            per_capacity = producer.capacity_per_day / max(
                self.capital_service_life_days, EPSILON
            )
            cost = 0.0
            for name, quantity in bill.items():
                cost += (
                    per_capacity
                    * quantity
                    * ration.get(name, 1.0)
                    * region.prices.get(name, 0.0)
                )
            if cost <= EPSILON:
                continue
            paid_fraction = min(1.0, max(producer.cash, 0.0) / cost)
            for name, quantity in bill.items():
                taken = per_capacity * quantity * ration.get(name, 1.0) * paid_fraction
                amount = taken * region.prices.get(name, 0.0)
                credited = self._pay_sellers(
                    region, name, amount, shares, buyer_is_fund=False, units=taken
                )
                producer.cash -= credited
            if paid_fraction < 1.0:
                producer.replacement_supplied = min(
                    producer.replacement_supplied, paid_fraction
                )

    def _pay_wages(
        self,
        region: Region,
        active: List[Producer],
        labor_by_producer: Dict[int, float],
        labor_performed: float,
        wage_bill: float,
    ) -> None:
        """Split the day's wage bill by the labor each producer used (docs/55).

        A purse that cannot cover its share -- the employment quantum's
        rounding, or a purse emptied by the day's inputs -- is topped up
        by the fund, and the top-up is booked so that it can be seen.
        """
        if wage_bill <= 0.0:
            return
        credited = 0.0
        if labor_performed > EPSILON:
            for producer in active:
                labor = labor_by_producer.get(id(producer), 0.0)
                if labor <= 0.0:
                    continue
                share = wage_bill * labor / labor_performed
                paid = min(share, max(producer.cash, 0.0))
                if paid <= 0.0:
                    continue
                producer.cash -= paid
                region.worker_cash += paid
                credited += paid
        residual = wage_bill - credited
        if residual > 0.0:
            if residual > region.cash:
                raise RuntimeError(
                    f"region {region.name!r} cannot cover its wage bill "
                    f"({residual:.3f} silver against {region.cash:.3f})"
                )
            region.cash -= residual
            region.worker_cash += residual
            Ledger.add(self.ledger.fund_wage_support, region.name, residual)

    def _settle_purses(self) -> None:
        """Distribute what a purse holds above its working capital, and
        remove producers that have been unable to pay for long enough
        (docs/55).  The target is *set*, not subtracted to, so a
        stationary producer's purse is the same float every day."""
        if not self.producer_cash:
            return
        for region in self.regions.values():
            for producer in region.producers:
                if not producer.active:
                    continue
                if (
                    self.bankruptcy_idle_days > 0
                    and producer.liquidity_idle_days >= self.bankruptcy_idle_days
                ):
                    self._bankrupt(region, producer)
                    continue
                producer.cash_target = (
                    self.working_capital_days * self._daily_outlay(producer, region)
                )
                if producer.cash > producer.cash_target:
                    excess = producer.cash - producer.cash_target
                    producer.cash = producer.cash_target
                    region.cash += excess
                    producer.distributed_total += excess
                    Ledger.add(self.ledger.distributions, region.name, excess)

    def _bankrupt(self, region: Region, producer: Producer) -> None:
        """No credit, no rescue: capacity is lost and the residual purse
        returns to the fund."""
        Ledger.add(
            self.ledger.capacity_lost, producer.commodity, producer.capacity_per_day
        )
        self.ledger.bankruptcies.append((self.day, region.name, producer.name))
        self._retire(region, producer)

    def _retire(self, region: Region, producer: Producer) -> None:
        """Take a producer out: no capacity, no purse, and what it held
        is the fund's to sell.  Shared by bankruptcy (docs/55) and exit
        (docs/64)."""
        producer.capacity_per_day = 0.0
        producer.active = False
        region.cash += producer.cash
        producer.cash = 0.0
        if self.procurement:
            # What it held is the fund's to sell.
            if producer.stock > 0.0:
                region.fund_stock[producer.commodity] = (
                    region.fund_stock.get(producer.commodity, 0.0) + producer.stock
                )
                producer.stock = 0.0
            for name, held in list(producer.inputs_on_hand.items()):
                if held > 0.0:
                    region.fund_stock[name] = region.fund_stock.get(name, 0.0) + held
                producer.inputs_on_hand[name] = 0.0

    # --------------------------------------------------------------- exit

    def _return_and_surplus(
        self, producer: Producer, cost: float
    ) -> Tuple[float, float]:
        """A producer's return on its capacity relative to the going one,
        and the capacity it holds beyond a reserve over the demand it
        expects (docs/64).

        The return is the posted margin times the utilization the
        producer's expected demand implies, over the going margin: a
        producer earning the going margin on half its capacity earns half
        the going return, because capital is advanced per unit of capacity
        and the margin is earned per unit sold (docs/61 section 3).
        """
        process = producer.process
        units = process.outputs.get(producer.commodity, 0.0)
        full = process.runs_for(producer.capacity_per_day) * units
        if full <= EPSILON or cost <= EPSILON or units <= EPSILON:
            return 1.0, 0.0
        utilization = min(1.0, producer.expected_demand / full)
        margin = (producer.posted_price - cost) / cost
        relative = utilization * margin / self.going_margin
        wanted = (
            producer.expected_demand
            * (1.0 + self.capacity_reserve)
            * process.capacity_per_run
            / units
        )
        return relative, producer.capacity_per_day - wanted

    def _exit(self) -> None:
        """Capital leaves a sector that cannot earn the going return
        (docs/64).

        Every investment interval, a producer whose return has been below
        the going one, with a surplus to withdraw, for the investment lead
        time takes out ``exit_gain × (1 − r)`` of its surplus: proportional
        to how far below, geometric toward the reserve, and nothing at the
        going return.  A plant the withdrawal would leave smaller than the
        smallest the fund would build is retired entirely, its purse and
        stock returning to the fund as a bankrupt's do.  Nothing comes
        back: construction was a sink and exit returns no silver.
        """
        for region in self.regions.values():
            for producer in region.producers:
                if not producer.active:
                    continue
                if producer.below_going_days < self.investment_lead_days:
                    continue
                relative, surplus = self._return_and_surplus(
                    producer, producer.effective_unit_cost(region.prices)
                )
                if relative >= 1.0 or surplus <= EPSILON:
                    continue
                withdrawn = min(surplus, self.exit_gain * (1.0 - relative) * surplus)
                if withdrawn <= 0.0:
                    continue
                remaining = producer.capacity_per_day - withdrawn
                if remaining < self.min_investment_capacity:
                    withdrawn = producer.capacity_per_day
                    remaining = 0.0
                Ledger.add(self.ledger.capacity_lost, producer.commodity, withdrawn)
                self.ledger.exits.append(
                    (self.day, region.name, producer.name, withdrawn)
                )
                if remaining <= 0.0:
                    self._retire(region, producer)
                else:
                    producer.capacity_per_day = remaining

    # -------------------------------------------------------- procurement

    class _WorkerPurse:
        """The workers' silver, addressed like any other purse."""

        def __init__(self, region: Region) -> None:
            self.region = region

        @property
        def cash(self) -> float:
            return self.region.worker_cash

        @cash.setter
        def cash(self, value: float) -> None:
            self.region.worker_cash = value

    def _seed_stocks(self) -> None:
        """Place the seeded stock in producers' hands (docs/59 section 3).

        Each producer opens with its own target: the inventory life of
        the sales it was seeded with (docs/62).  The plan's pool was the
        inventory life of the sector's *throughput*, which is larger
        wherever capacity exceeds the seeded draw; a producer opening
        with that would hold an excess and cut.  Anything nobody here
        makes is the fund's, and the region's inventory reads the sum.
        """
        for region in self.regions.values():
            for name in self.commodities:
                held = region.inventory.get(name, 0.0)
                producers = [
                    p for p in region.producers if p.active and p.commodity == name
                ]
                if not producers:
                    region.fund_stock[name] = held
                    continue
                days = self.commodities[name].target_inventory_days
                for producer in producers:
                    producer.expected_demand = producer.demand_seen()
                    producer.stock = days * producer.expected_demand
            self._sync_inventory(region)

    def _sync_inventory(self, region: Region) -> None:
        """The region's inventory is what its producers and its fund hold."""
        for name in self.commodities:
            total = 0.0
            for producer in region.producers:
                # A destroyed producer's stock is still stock, and so is
                # an input bought and not yet used.
                if producer.commodity == name and producer.stock != 0.0:
                    total += producer.stock
                held = producer.inputs_on_hand.get(name, 0.0)
                if held != 0.0:
                    total += held
            fund = region.fund_stock.get(name, 0.0)
            if fund != 0.0:
                total += fund
            region.inventory[name] = total

    def _offers(self, region: Region, name: str) -> List[Tuple[float, int, str, object]]:
        """Who is selling a commodity here, cheapest first.

        Producers at what they ask, the fund at the regional price, ties
        broken by name so the walk is the same walk every day.  A seller is
        listed with what it still has after the sales already taken in this
        pass.
        """
        offers: List[Tuple[float, int, str, object]] = []
        for producer in region.producers:
            if producer.commodity != name:
                continue
            # A producer that has stopped still sells what it holds.
            if producer.stock - producer.pending_out > EPSILON:
                offers.append((producer.posted_price, 0, producer.name, producer))
        held = region.fund_stock.get(name, 0.0) - region.fund_pending.get(name, 0.0)
        if held > EPSILON:
            offers.append(
                (region.fund_price.get(name, region.prices[name]), 1, "", None)
            )
        offers.sort(key=lambda offer: (offer[0], offer[1], offer[2]))
        return offers

    def _available(self, region: Region, name: str) -> float:
        total = 0.0
        for _, kind, _, seller in self._offers(region, name):
            if kind == 0:
                total += seller.stock - seller.pending_out
            else:
                total += region.fund_stock.get(name, 0.0) - region.fund_pending.get(name, 0.0)
        return total

    def _quote(self, region: Region, name: str, units: float) -> float:
        """What buying this many units would cost, cheapest first, before
        any purse is consulted."""
        remaining = units
        cost = 0.0
        for price, kind, _, seller in self._offers(region, name):
            if remaining <= EPSILON:
                break
            held = (
                seller.stock - seller.pending_out
                if kind == 0
                else region.fund_stock.get(name, 0.0) - region.fund_pending.get(name, 0.0)
            )
            take = min(remaining, held)
            cost += take * price
            remaining -= take
        return cost

    def _buy(
        self, region: Region, name: str, units: float, payer: object
    ) -> Tuple[float, float]:
        """Buy up to ``units`` from the cheapest sellers the payer can afford.

        The sale is taken -- the seller's pending outflow and the silver
        move now -- and applied to the seller's stock in one subtraction at
        the end of the pass.  Returns what was bought and what was paid.
        A fund buying its own stock moves no silver.
        """
        remaining = units
        bought = 0.0
        paid = 0.0
        if units <= EPSILON:
            return 0.0, 0.0
        offers = self._offers(region, name)
        if not offers:
            return 0.0, 0.0
        # Custom goes to the cheaper seller *continuously* (docs/21's rule,
        # applied to what is asked rather than to cost): each seller's
        # share is what it holds, weighted by its price against the
        # cheapest to a constant elasticity, capped by what it holds, with
        # what a capped seller cannot take redistributed among the rest.
        # One seller takes everything; a seller asking a hair less does not.
        cheapest = offers[0][0]
        epsilon_share = self.competitive_share_elasticity
        held: List[float] = []
        weights: List[float] = []
        for price, kind, _, seller in offers:
            have = (
                seller.stock - seller.pending_out
                if kind == 0
                else region.fund_stock.get(name, 0.0) - region.fund_pending.get(name, 0.0)
            )
            held.append(have)
            # By what a seller can put toward *this* order, not by the
            # size of its warehouse (docs/62): two sellers who can each
            # fill it split it by price alone, and one that cannot gets
            # only what it can serve.
            serve = min(have, units)
            if epsilon_share == 0.0 or cheapest <= EPSILON or price <= EPSILON:
                weights.append(serve)
            else:
                weights.append(serve * (price / cheapest) ** (-epsilon_share))
        takes = [0.0] * len(offers)
        open_sellers = list(range(len(offers)))
        left = min(remaining, sum(held))
        for _ in range(len(offers)):
            if left <= EPSILON or not open_sellers:
                break
            total_weight = sum(weights[i] for i in open_sellers)
            if total_weight <= EPSILON:
                break
            capped: List[int] = []
            placed = 0.0
            for i in open_sellers:
                share = left * weights[i] / total_weight if len(open_sellers) > 1 else left
                room = held[i] - takes[i]
                if share >= room:
                    takes[i] += room
                    placed += room
                    capped.append(i)
                else:
                    takes[i] += share
                    placed += share
            left -= placed
            if not capped:
                break
            open_sellers = [i for i in open_sellers if i not in capped]
        for (price, kind, _, seller), take, have in zip(offers, takes, held):
            if take <= EPSILON:
                continue
            take = min(take, have, remaining)
            own_stock = kind == 1 and payer is region
            if not own_stock and price > EPSILON:
                affordable = max(payer.cash, 0.0) / price
                if take > affordable:
                    take = affordable
            if take <= EPSILON:
                continue
            cost = take * price
            if kind == 0:
                seller.pending_out += take
                seller.sales_today += take
                if not own_stock:
                    seller.cash += cost
                if have - take <= EPSILON and units - bought - take > EPSILON:
                    # Sold out with the buyer still wanting more.
                    seller.sellouts_today += units - bought - take
            else:
                region.fund_pending[name] = region.fund_pending.get(name, 0.0) + take
                region.fund_sales_today[name] = (
                    region.fund_sales_today.get(name, 0.0) + take
                )
                if not own_stock:
                    region.cash += cost
            if not own_stock:
                payer.cash -= cost
                paid += cost
            bought += take
            remaining -= take
        return bought, paid

    def _note_sellouts(self, region: Region, name: str, unfilled: float) -> None:
        """Demand that found every seller empty is a sell-out for each
        active seller with nothing left: demand it saw and could not
        serve, which its plan reads tomorrow and its price answers as far
        as it was already making all it would (docs/62).  docs/60 noted
        it only for sellers that had sold today, so a sector that ran dry
        could never see the demand that would restart it."""
        if unfilled <= EPSILON:
            return
        for producer in region.producers:
            if (
                producer.active
                and producer.commodity == name
                and producer.stock - producer.pending_out <= EPSILON
            ):
                producer.sellouts_today += unfilled

    def _apply_pending(self, region: Region) -> None:
        """Take the pass's sales off each seller's stock, once."""
        for producer in region.producers:
            if producer.pending_out != 0.0:
                producer.stock -= producer.pending_out
                producer.pending_out = 0.0
        for name, pending in list(region.fund_pending.items()):
            if pending != 0.0:
                region.fund_stock[name] = region.fund_stock.get(name, 0.0) - pending
                region.fund_pending[name] = 0.0

    def _reprice_fund(self, region: Region, commodity: Commodity) -> None:
        """The fund wants to hold nothing: its price falls while it has
        stock, by the same gain producers cut on excess, and resets to the
        going price when it has sold out (docs/60)."""
        name = commodity.name
        held = region.fund_stock.get(name, 0.0)
        if held <= EPSILON:
            region.fund_price[name] = region.prices[name]
            return
        pool = self._throughput[region.name][name] * commodity.target_inventory_days
        excess = -held / pool if pool > EPSILON else -1.0
        current = region.fund_price.get(name, region.prices[name])
        region.fund_price[name] = current * exp(
            self.posted_price_speed * commodity.inventory_price_sensitivity * excess
        )

    def _price_target(self, region: Region, producer: Producer) -> float:
        """The stock a producer's *price* reads its own against: the
        commodity's inventory life of the demand it saw (docs/62).  A
        producer selling nothing holds nothing but excess, and cuts until
        it sells; one whose custom has gone elsewhere sees its stock in
        excess of what it now sells, and cuts; and one at the seed sees
        exactly the pool, because the pool was that many days of its
        sales.  Nothing in it reads the sector's capacity, which is what
        docs/60's target did, and what let a sector hold twenty days of
        a demand it no longer had."""
        commodity = self.commodities[producer.commodity]
        return commodity.target_inventory_days * producer.expected_demand

    def _own_target(self, region: Region, producer: Producer) -> float:
        """The stock a producer plans around: the inventory life of the
        demand it expects (docs/62).  The same number its price reads its
        stock against; an entrant's expectation is seeded on its first
        morning (`_open_region_day`), which is what lets it make anything
        before it has sold anything."""
        return self._price_target(region, producer)

    def _produce_procurement(self, region: Region) -> None:
        """One region's day when producers own their output (docs/59).

        Each producer plans from its own sales and its own stock, buys the
        inputs and plant matter for that plan from the cheapest sellers it
        can afford, and makes what it bought inputs for.  Output goes into
        its own stock.  No sector request and no fixed point; the reserve
        and the labor pool still ration, because they are physical.
        """
        active = self._open_region_day(region)
        life = max(self.capital_service_life_days, EPSILON)

        # --- 1. each producer's plan -----------------------------------
        planned: Dict[int, float] = {}
        for producer in active:
            units = producer.process.outputs[producer.commodity]
            target = self._own_target(region, producer)
            wanted_output = producer.expected_demand + self.replenishment_rate * (
                target - producer.stock
            )
            wanted = max(0.0, wanted_output / units)
            ceiling = producer.process.runs_for(
                producer.capacity_per_day
            ) * producer.utilization(producer.posted_price, region.prices)
            producer.last_ceiling = ceiling
            planned[id(producer)] = min(wanted, ceiling)

        # Reserve rationing, pro rata across producers sharing a reserve.
        for rname, reserve in region.reserves.items():
            if reserve.remaining <= EPSILON:
                for p in active:
                    if p.commodity == rname:
                        planned[id(p)] = 0.0
                continue
            total_wanted = 0.0
            for p in active:
                if p.commodity == rname:
                    total_wanted += planned[id(p)] * p.process.outputs.get(rname, 0.0)
            if total_wanted > reserve.remaining:
                reserve_ration = reserve.remaining / total_wanted
                for p in active:
                    if p.commodity == rname:
                        planned[id(p)] *= reserve_ration

        # Labor-pool rationing, the same proportional rule as the plan's.
        if region.labor_pool != float("inf"):
            available_ticks = region.labor_pool * region.ticks_per_worker_day
            planned_ticks = sum(planned[id(p)] * p.process.direct_labor for p in active)
            if planned_ticks > available_ticks:
                labor_ration = available_ticks / planned_ticks
                for p in active:
                    planned[id(p)] *= labor_ration

        # --- 2. the morning market: inputs and plant matter -------------
        drawn: Dict[str, float] = {}
        plant_rations: Dict[int, Dict[str, float]] = {}
        for producer in active:
            runs = planned[id(producer)]
            inputs = producer.process.inputs
            on_hand = producer.inputs_on_hand
            if runs > EPSILON:
                # What each input's sellers can supply, beyond what is
                # already on hand, bounds the runs; what they cannot is
                # unmet demand for that input alone.
                for name, per_run in sorted(inputs.items()):
                    have = on_hand.get(name, 0.0)
                    need = runs * per_run - have
                    if need <= EPSILON:
                        continue
                    can_buy = min(need, self._available(region, name))
                    if can_buy < need:
                        region.unmet_demand[name] += need - can_buy
                        self._note_sellouts(region, name, need - can_buy)
                        runs = (have + can_buy) / per_run
            if runs > EPSILON:
                # What the purse can pay for, at the prices actually asked,
                # after the plant matter it owes on the calendar.
                cost = 0.0
                for name, per_run in sorted(inputs.items()):
                    need = runs * per_run - on_hand.get(name, 0.0)
                    if need > EPSILON:
                        cost += self._quote(region, name, need)
                spendable = max(0.0, producer.cash - self._plant_matter_cost(producer, region))
                if cost > spendable and cost > EPSILON:
                    scale = spendable / cost
                    Ledger.add(
                        self.ledger.liquidity_curtailment,
                        producer.commodity,
                        runs * (1.0 - scale),
                    )
                    runs *= scale
                    producer.liquidity_idle_days = (
                        producer.liquidity_idle_days + 1 if runs <= EPSILON else 0
                    )
                else:
                    producer.liquidity_idle_days = 0
            if runs > EPSILON:
                for name, per_run in sorted(inputs.items()):
                    need = runs * per_run - on_hand.get(name, 0.0)
                    if need <= EPSILON:
                        continue
                    bought, _ = self._buy(region, name, need, producer)
                    if bought > 0.0:
                        on_hand[name] = on_hand.get(name, 0.0) + bought
                # Liebig, on what is actually on hand.
                for name, per_run in sorted(inputs.items()):
                    runs = min(runs, on_hand.get(name, 0.0) / per_run)
            planned[id(producer)] = max(0.0, runs)
            # Plant matter, on the calendar whether or not the producer ran.
            ration: Dict[str, float] = {}
            bill = producer.process.capital_bill_per_capacity()
            if bill and producer.capacity_per_day > EPSILON:
                per_capacity = producer.capacity_per_day / life
                for name, quantity in bill.items():
                    need = per_capacity * quantity
                    bought, _ = self._buy(region, name, need, producer)
                    ration[name] = bought / need if need > EPSILON else 1.0
            plant_rations[id(producer)] = ration
        self._apply_pending(region)

        # --- 3. production, into each producer's own stock --------------
        produced: Dict[str, float] = {}
        labor_by_producer: Dict[int, float] = {}
        labor_performed = 0.0
        for producer in region.producers:
            producer.last_runs = 0.0
        for producer in active:
            runs = planned[id(producer)]
            if runs <= EPSILON:
                continue
            producer.last_runs = runs
            labor_performed += runs * producer.process.direct_labor
            labor_by_producer[id(producer)] = runs * producer.process.direct_labor
            # Exactly what these runs use comes off what is on hand and
            # is what the ledger calls consumed.
            for name, per_run in producer.process.inputs.items():
                used = runs * per_run
                producer.inputs_on_hand[name] = producer.inputs_on_hand.get(name, 0.0) - used
                drawn[name] = drawn.get(name, 0.0) + used
            own_output = runs * producer.process.outputs.get(producer.commodity, 0.0)
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
            for name, per_run in producer.process.outputs.items():
                if name not in self.commodities:
                    continue
                produced[name] = produced.get(name, 0.0) + runs * per_run
            producer.output_total += own_output
            producer.stock += own_output
        for producer in active:
            construction = self._replace_plant(
                region, producer, plant_rations.get(id(producer), {}), drawn
            )
            labor_performed += construction
            if construction > 0.0:
                labor_by_producer[id(producer)] = (
                    labor_by_producer.get(id(producer), 0.0) + construction
                )
        self._shed_capacity(region, active)

        for name, amount in drawn.items():
            Ledger.add(self.ledger.intermediate_consumption, name, amount)
            Ledger.add(
                self.ledger.circulating_capital,
                region.name,
                amount * self.labor_values.get(name, 0.0),
            )
        for name, amount in produced.items():
            Ledger.add(self.ledger.production, name, amount)
            Ledger.add(
                self.ledger.value_produced,
                region.name,
                amount * self.labor_values.get(name, 0.0),
            )
        for rname, reserve in region.reserves.items():
            extracted = produced.get(rname, 0.0)
            if extracted > EPSILON:
                reserve.extract(extracted)
                Ledger.add(self.ledger.reserve_depletion, rname, extracted)
                self._daily_extraction[(region.name, rname)] = extracted

        self._settle_labor(region, active, labor_by_producer, labor_performed)
        self._sync_inventory(region)

    def _final_market(self) -> None:
        """The fund buys the final good and the workers buy the basket, from
        producers' own stocks, cheapest first (docs/59)."""
        for region in self.regions.values():
            for commodity in self.commodities.values():
                name = commodity.name
                desired = region.daily_demand(commodity)
                if desired <= 0.0:
                    continue
                wanted = min(desired, self._available(region, name))
                bought, _ = self._buy(region, name, wanted, region)
                region.unmet_demand[name] += desired - bought
                self._note_sellouts(region, name, desired - bought)
                region.consumed_total[name] += bought
                Ledger.add(self.ledger.consumption, name, bought)
            self._apply_pending(region)

            if region.subsistence_basket:
                worker_days = region.worker_days_due
                purse = Economy._WorkerPurse(region)
                purchases: List[Tuple[str, float]] = []
                total_cost = 0.0
                for name, quantity in sorted(region.subsistence_basket.items()):
                    if name not in self.commodities:
                        continue
                    desired = quantity * worker_days
                    if region.wage_premium_due != 0.0:
                        desired *= 1.0 + region.wage_premium_due
                    if desired <= 0.0:
                        continue
                    bought = min(desired, self._available(region, name))
                    inventory_shortfall = desired - bought
                    if inventory_shortfall > EPSILON:
                        region.unmet_demand[name] += inventory_shortfall
                        Ledger.add(self.ledger.basket_shortfall, region.name, inventory_shortfall)
                        self._note_sellouts(region, name, inventory_shortfall)
                    if bought <= 0.0:
                        continue
                    purchases.append((name, bought))
                    total_cost += self._quote(region, name, bought)
                cash_factor = 1.0
                if total_cost > region.worker_cash:
                    cash_factor = region.worker_cash / total_cost
                for name, bought in purchases:
                    if cash_factor < 1.0:
                        affordable = bought * cash_factor
                        denied = bought - affordable
                        region.unmet_demand[name] += denied
                        Ledger.add(self.ledger.basket_shortfall, region.name, denied)
                        bought = affordable
                    if bought <= 0.0:
                        continue
                    got, spend = self._buy(region, name, bought, purse)
                    region.consumed_total[name] += got
                    Ledger.add(self.ledger.consumption, name, got)
                    Ledger.add(self.ledger.worker_spending, region.name, spend)
                self._apply_pending(region)
            region.worker_days_due = region.worker_days_earned
            region.wage_premium_due = region.wage_premium
            self._sync_inventory(region)

    # ------------------------------------------------------ posted prices

    def _seed_posted_prices(self) -> None:
        """Every producer starts by asking the going price and remembers
        the cost it asked it at (docs/57)."""
        for region in self.regions.values():
            for producer in region.producers:
                if not producer.active:
                    continue
                producer.posted_price = region.prices[producer.commodity]
                producer.last_cost = producer.effective_unit_cost(region.prices)

    def _pool_pressure(self, region: Region, commodity: Commodity) -> Optional[float]:
        """The pool's signal: stock against target and orders unfilled --
        the same expression the anchored rule pushes against.  None where
        the commodity is not traded here."""
        name = commodity.name
        throughput = self._throughput[region.name][name]
        if throughput <= EPSILON:
            return None
        target = throughput * commodity.target_inventory_days
        coverage_gap = (target - region.inventory[name]) / max(target, EPSILON)
        unmet_ratio = region.unmet_demand[name] / throughput
        return (
            commodity.inventory_price_sensitivity * coverage_gap
            + self.unmet_demand_price_pressure * unmet_ratio
        )

    def _update_posted_prices(self) -> None:
        """Each producer moves what it asks by its own cost and the pool's
        pressure; the regional price is what was paid (docs/57).

        Multiplicative, so that on a stationary day -- identical cost,
        zero pressure -- the factor is exactly one and the price is the
        same float.  Costs are read at the day's opening prices for every
        producer before any price moves, so the order of commodities
        cannot enter the answer.
        """
        for region in self.regions.values():
            opening = dict(region.prices)
            costs = {
                id(p): p.effective_unit_cost(opening)
                for p in region.producers
                if p.active
            }
            for commodity in self.commodities.values():
                name = commodity.name
                pressure = self._pool_pressure(region, commodity)
                if pressure is None:
                    continue
                producers = [
                    p for p in region.producers if p.active and p.commodity == name
                ]
                if not producers:
                    continue
                # A producer's own signal beside the pool's: its order fill
                # against its sector's average (docs/58).  Exactly zero for
                # a lone producer, so a seeded sector stays stationary; in
                # a contested sector the one losing custom cuts.  Under
                # procurement the signal is the producer's *own* stock
                # against its own target (docs/59), and the pool's stock
                # term is not read at all.
                mean_fill = sum(p.order_fill for p in producers) / len(producers)
                unmet_term = (
                    self.unmet_demand_price_pressure
                    * region.unmet_demand[name]
                    / max(self._throughput[region.name][name], EPSILON)
                )
                for producer in producers:
                    cost = costs[id(producer)]
                    posted = producer.posted_price
                    if producer.last_cost > EPSILON and cost != producer.last_cost:
                        posted *= cost / producer.last_cost
                    if self.procurement:
                        # Excess stock cuts; a sell-out raises.  A stock
                        # merely below target is not scarcity: a producer
                        # filling its warehouse toward the demand it
                        # expects must not read the gap as one (docs/60,
                        # kept in docs/62 with the target now the
                        # inventory life of the producer's own expected
                        # demand rather than its share of the plan's pool).
                        target = self._price_target(region, producer)
                        if target > EPSILON:
                            excess = min(0.0, (target - producer.stock) / target)
                        elif producer.stock > EPSILON:
                            excess = -1.0
                        else:
                            excess = 0.0
                        served = producer.sales_today + producer.sellouts_today
                        sellout = (
                            producer.sellouts_today / served if served > EPSILON else 0.0
                        )
                        # A producer that made all it was willing to at
                        # its price answers a sell-out with its price; one
                        # that planned less than that answers it with its
                        # plan, and raises only in proportion (docs/62).
                        # At a price where it would make nothing, a
                        # sell-out is scarcity and raises in full.
                        if sellout > 0.0 and producer.last_ceiling > EPSILON:
                            sellout *= min(
                                1.0, producer.last_runs / producer.last_ceiling
                            )
                        own = (
                            commodity.inventory_price_sensitivity * excess
                            + self.unmet_demand_price_pressure * sellout
                        )
                        # Capacity idle and a margin above the going one:
                        # each unit more would pay, so the producer cuts
                        # to sell more (docs/62).  This is the supply
                        # response of the producers already there; entry
                        # on margin (docs/61) is the same signal read by
                        # capital that is not there yet.
                        full = producer.process.runs_for(producer.capacity_per_day)
                        if full > EPSILON and cost > EPSILON:
                            idle = max(0.0, 1.0 - producer.last_runs / full)
                            above = (posted - cost) / cost - self.going_margin
                            if idle > 0.0 and above > 0.0:
                                own -= (
                                    self.idle_capacity_gain
                                    * idle
                                    * above
                                    / self.going_margin
                                )
                    else:
                        own = pressure + self.posted_share_gain * (
                            producer.order_fill - mean_fill
                        )
                    if own != 0.0:
                        posted *= exp(self.posted_price_speed * own)
                    # A producer does not ask less than the price at which
                    # it would make nothing (docs/60): the floor is where
                    # its own utilization curve reaches zero, not the
                    # market's clamp.
                    low = cost * max(
                        commodity.minimum_price_factor,
                        producer.zero_utilization_price_ratio if self.procurement else 0.0,
                    )
                    high = cost * commodity.maximum_price_factor
                    if cost > EPSILON:
                        posted = min(high, max(low, posted))
                    producer.posted_price = posted
                    producer.last_cost = cost
                # What was paid: the supply-weighted mean of what was
                # asked, by today's realized output -- by today's sales
                # under procurement -- or by capacity where nobody ran.
                if self.procurement:
                    weights = [p.sales_today for p in producers]
                    asked = [p.posted_price for p in producers]
                    fund_sold = region.fund_sales_today.get(name, 0.0)
                    if fund_sold > EPSILON:
                        weights.append(fund_sold)
                        asked.append(region.fund_price.get(name, region.prices[name]))
                    for p in producers:
                        # In the form that is exact when nothing moved:
                        # a stationary day adds alpha times zero.
                        p.expected_demand += self.expectation_alpha * (
                            p.sales_today + p.sellouts_today - p.expected_demand
                        )
                        p.sales_yesterday = p.sales_today
                        p.sales_today = 0.0
                        p.sellouts_yesterday = p.sellouts_today
                        p.sellouts_today = 0.0
                        if self.exit_on_return:
                            # A day below the going return with a surplus
                            # to withdraw counts toward exit (docs/64).
                            below, surplus = self._return_and_surplus(
                                p, costs[id(p)]
                            )
                            if below < 1.0 and surplus > EPSILON:
                                p.below_going_days += 1
                            else:
                                p.below_going_days = 0
                    region.fund_sales_today[name] = 0.0
                    self._reprice_fund(region, commodity)
                else:
                    weights = [
                        p.last_runs * p.process.outputs.get(name, 0.0) for p in producers
                    ]
                    asked = [p.posted_price for p in producers]
                total = sum(weights)
                if total <= EPSILON:
                    weights = [p.capacity_per_day for p in producers]
                    asked = [p.posted_price for p in producers]
                    total = sum(weights)
                if total <= EPSILON:
                    continue
                if len(weights) == 1:
                    region.prices[name] = asked[0]
                else:
                    region.prices[name] = sum(
                        w * a for a, w in zip(asked, weights)
                    ) / total

    def _update_prices(self) -> None:
        if self.posted_prices:
            self._update_posted_prices()
            return
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

                if self.procurement:
                    # Bought from the source's cheapest sellers, by the
                    # destination's fund (docs/59).
                    quantity, payment = self._buy(source, name, quantity, destination)
                    self._apply_pending(source)
                    self._sync_inventory(source)
                    if quantity <= EPSILON:
                        continue
                    source.exported_total[name] += quantity
                    freight_payment = freight * quantity
                    destination.cash -= freight_payment
                    self.ledger.transport_cash += freight_payment
                    self.shipments.append(
                        Shipment(
                            name,
                            quantity,
                            source.name,
                            destination.name,
                            self.day,
                            self.day + route.travel_days,
                            payment / quantity,
                            freight,
                        )
                    )
                    remaining_capacity -= quantity
                    continue

                source.inventory[name] -= quantity
                source.exported_total[name] += quantity
                payment = source.prices[name] * quantity
                freight_payment = freight * quantity
                if self.producer_cash:
                    # The exporting producers are paid (docs/55); the
                    # importing region's fund pays, as it always has.
                    payment = self._pay_sellers(
                        source,
                        name,
                        payment,
                        self._supply_shares(source),
                        buyer_is_fund=False,
                        units=quantity,
                    )
                    destination.cash -= payment + freight_payment
                else:
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
                if self.exit_on_return:
                    # The market's demand, not the plan's throughput: the
                    # sum of what the sector's producers expect.  The
                    # plan's number is every input draw at full capacity,
                    # and it rebuilds whatever exit withdraws wherever the
                    # price is above the reference (docs/64 section 1).
                    seen = sum(
                        p.expected_demand
                        for p in region.producers
                        if p.active and p.commodity == name
                    )
                    if seen > EPSILON:
                        demand = seen
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
                if shortfall <= EPSILON and not self.entry_on_margin:
                    continue

                # Use effective cost (overhead + inputs) for the margin test,
                # but store only the operating overhead on the new producer.
                active = [
                    p for p in region.producers if p.active and p.commodity == name
                ]
                active_effective = [p.effective_unit_cost(region.prices) for p in active]
                active_overhead = [p.unit_cost for p in active]
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
                # Which technique the new capacity would use decides what it
                # is made of, so it has to be settled before the size is.
                # The first active producer's, as it always was; with entry
                # on margin, the cheapest active producer's and its overhead
                # (docs/61 section 2).
                existing_process = next(
                    (p.process for p in active), self.known_processes[name]
                )
                amount = 0.0
                if (
                    shortfall > EPSILON
                    and margin >= self.investment_margin_threshold
                    and inventory_days < commodity.target_inventory_days
                ):
                    amount = shortfall * self.investment_fraction_of_shortfall
                if self.entry_on_margin:
                    if active:
                        best = min(
                            range(len(active)), key=lambda i: active_effective[i]
                        )
                        best_effective = active_effective[best]
                        assumed_overhead = active_overhead[best]
                        existing_process = active[best].process
                    else:
                        best_effective = assumed_effective
                    entry_margin = (expected - best_effective) / max(
                        best_effective, EPSILON
                    )
                    if entry_margin > self.going_margin:
                        # Capital goes where the price clears cost, in
                        # proportion to how far it clears it, and asks
                        # for no shortfall (docs/61).  It accrues until
                        # it is a project's worth: a sector of half a
                        # unit a day is not barred from entry by the
                        # minimum project size (docs/63).
                        region.entry_backlog[name] = region.entry_backlog.get(
                            name, 0.0
                        ) + (
                            self.entry_gain
                            * demand
                            * (entry_margin - self.going_margin)
                            / self.going_margin
                        )
                        amount += region.entry_backlog[name]
                    else:
                        # The intention lapses with the margin.
                        region.entry_backlog[name] = 0.0
                if amount <= 0.0:
                    continue
                bill = existing_process.capital_bill_per_capacity()
                if bill:
                    # Department I (docs/36 3.4): what a unit of capacity
                    # costs is what its plant is made of, at this region's
                    # prices, plus the labor to put it up at this region's
                    # wage.  `construction_cost_multiplier` stops governing
                    # anything here; it still governs every bill-free
                    # process, which is every scenario that does not opt in.
                    construction_unit = self.capital_money_per_capacity(
                        existing_process, region
                    )
                else:
                    # Construction costs silver: days of effective cost per
                    # unit of daily capacity.
                    construction_unit = (
                        assumed_effective * self.construction_cost_multiplier
                    )
                total_cost = amount * construction_unit
                if total_cost > region.cash:
                    # Scale down to what the region can afford.
                    amount = region.cash / max(construction_unit, EPSILON)
                # And to what it can build out of.  A region short of
                # components does not get a refinery, which is the entire
                # point of making the machines produced.
                for material, quantity in bill.items():
                    if quantity > 0.0:
                        amount = min(
                            amount,
                            region.inventory.get(material, 0.0) / quantity,
                        )
                if amount < self.min_investment_capacity:
                    continue
                total_cost = amount * construction_unit
                if not self.procurement:
                    region.cash -= total_cost
                # The matter, out of stock.  Booked as a declared sink so
                # the material identity closes, and deliberately *not* as
                # circulating capital: the value it becomes is plant, and
                # the model keeps no plant stock account for the value side
                # to close against.  Named in docs/37 rather than hidden.
                material_shares = (
                    self._supply_shares(region) if self.producer_cash else {}
                )
                credited = 0.0
                for material, quantity in bill.items():
                    take = amount * quantity
                    if take <= 0.0:
                        continue
                    if self.procurement:
                        # Bought from whoever holds it (docs/59): the fund
                        # pays the sellers here and the construction sink
                        # below, and the two sum to the bill.
                        got, paid = self._buy(region, material, take, region)
                        take = got
                        credited += paid
                        self._apply_pending(region)
                        self._sync_inventory(region)
                    else:
                        region.inventory[material] = (
                            region.inventory.get(material, 0.0) - take
                        )
                    Ledger.add(
                        self.ledger.intermediate_consumption, material, take
                    )
                    Ledger.add(self.ledger.capital_construction, material, take)
                    if self.producer_cash and not self.procurement:
                        # The fund buys the matter from whoever made it
                        # (docs/55); the rest of the bill is construction.
                        credited += self._pay_sellers(
                            region,
                            material,
                            take * region.prices.get(material, 0.0),
                            material_shares,
                            buyer_is_fund=True,
                            units=take,
                        )
                self.ledger.investment_spending += total_cost - credited
                if self.procurement:
                    # The construction part of the bill, out of the fund;
                    # the matter was paid to its sellers above.
                    region.cash -= total_cost - credited
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
                if self.entry_on_margin:
                    region.entry_backlog[name] = 0.0

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
                        "producer_cash": sum(p.cash for p in region.producers),
                        "cost_ratio": dict(region.cost_ratio),
                        "employment": region.worker_days_earned,
                        "wage_rate": region.wage_rate(),
                        "wage_premium": region.wage_premium,
                        "habitual_scale": region.habitual_scale,
                        "premium_over_value": region.premium_over_value(),
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
