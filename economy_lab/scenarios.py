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
from math import floor
from typing import Dict, List

from .model import (
    Commodity,
    Economy,
    Process,
    Producer,
    Region,
    ResourceGrade,
    ResourceReserve,
    Route,
)


DAYS_PER_YEAR = 60
DAYS_PER_QUADRUM = 15

YAYO = "yayo"
LEAVES = "psychoid_leaves"
CHEMFUEL = "chemfuel"
MEALS = "meals"


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
    buffer_refill_horizon_days: float = 60.0
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

    # --- labor-power and the subsistence basket (docs/17) --------------------
    # The wage relation: meals are the real subsistence commodity, workers
    # are paid the basket's cost at current prices, and employment follows
    # labor actually performed.  Reference price and embodied labor come
    # from MealSimple in RimWorld's defs / the closed analysis; the basket
    # quantity, working day, and capacities are calibration choices whose
    # power-of-two values are part of the exact-equilibrium engineering.
    meal_reference_price: float = 15.0
    meal_direct_labor: float = 305.0
    meal_labor_value: float = 305.0 * 11.4 / 720.0
    meal_mass: float = 0.44
    meal_capacity_per_day: float = 1.0
    meals_per_worker_day: float = 2.0
    ticks_per_worker_day: float = 24000.0
    labor_pool_worker_days: float = 1.0
    worker_initial_cash_days: float = 30.0
    labor_value_per_tick: float = 11.4 / 720.0
    employment_quantum: float = 2.0 ** -20
    subsistence_loss_fraction: float = 0.70

    # --- endogenous labor values (docs/19) -----------------------------------
    labor_value_tolerance: float = 1e-12
    labor_value_max_iterations: int = 1000
    #: A more productive provisioning technique: half the living labor per
    #: meal, same capacity.  Used by the technique-change scenario to make
    #: relative surplus value emerge without touching the wage, the basket,
    #: or the working day.
    meal_efficient_direct_labor: float = 152.5
    technique_change_day: int = 60

    # --- competitive transmission (docs/21) ----------------------------------
    #: How much of a relative cost change reaches the price anchor.  Zero
    #: reproduces the reference-anchored model bit-for-bit.
    competitive_price_intensity: float = 0.5
    #: How sharply the order book favours the cheaper producer.  Zero is a
    #: bit-exact no-op.
    competitive_share_elasticity: float = 2.0
    #: The cost-competition entrant's overhead, as a fraction of the
    #: incumbent's: a capital-saving technique rather than a labor-saving one.
    cheap_provisioner_overhead_fraction: float = 0.6
    cost_competition_day: int = 60

    # --- fixed capital (docs/23) ---------------------------------------------
    # Each sector's real RimWorld building, in money and in embodied labor,
    # from the closed analysis.  Machines are needed in proportion to the
    # labor performed at them: one machine occupied for a worker-day supports
    # `ticks_per_worker_day` of work, so a unit of daily output needs
    # `direct_labor / ticks_per_worker_day` machines.
    capital_service_life_days: float = 600.0
    drug_lab_capital_money: float = 445.0
    drug_lab_capital_labor: float = 41_607.5
    psychoid_field_capital_money: float = 230.0
    psychoid_field_capital_labor: float = 13_120.0
    refinery_capital_money: float = 390.0
    refinery_capital_labor: float = 25_835.0
    provisioner_capital_money: float = 225.0
    provisioner_capital_labor: float = 16_940.0

    # --- prices of production (docs/26) --------------------------------------
    # Same convergence discipline as the labor value solve, so the two
    # iterative systems fail on the same terms.
    production_price_tolerance: float = 1e-12
    production_price_max_iterations: int = 1000

    def machines_per_capacity(self, direct_labor: float) -> float:
        """Machines needed to support one unit of daily output."""
        return direct_labor / self.ticks_per_worker_day

    # --- resource reserves ---------------------------------------------------
    # Default: one large grade at the current operating overhead.  The reserve
    # is large enough that no existing scenario depletes it.  Override in the
    # depletion scenario to exercise grade transitions and differential rent.
    chemfuel_reserve_per_region: float = 100_000.0
    #: Second (expensive) grade quantity; zero disables it.
    chemfuel_expensive_reserve: float = 0.0
    #: Cost multiplier for the expensive grade, relative to the operating
    #: overhead at reference prices.
    chemfuel_expensive_cost_multiplier: float = 2.0

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
            MEALS: self.meal_reference_price,
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
        _commodity(
            parameters,
            MEALS,
            parameters.meal_reference_price,
            parameters.meal_labor_value,
            parameters.meal_mass,
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
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.chemfuel_direct_labor
                )
                * parameters.refinery_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.chemfuel_direct_labor
                )
                * parameters.refinery_capital_labor
            ),
        ),
        LEAVES: Process(
            "psychoid farming",
            outputs={LEAVES: 1.0},
            inputs={CHEMFUEL: parameters.chemfuel_per_leaf},
            direct_labor=parameters.leaves_direct_labor,
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.leaves_direct_labor
                )
                * parameters.psychoid_field_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.leaves_direct_labor
                )
                * parameters.psychoid_field_capital_labor
            ),
        ),
        YAYO: Process(
            "yayo refining",
            outputs={YAYO: 1.0},
            inputs={
                LEAVES: parameters.leaves_per_yayo,
                CHEMFUEL: parameters.chemfuel_per_yayo,
            },
            direct_labor=parameters.yayo_direct_labor,
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.yayo_direct_labor
                )
                * parameters.drug_lab_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.yayo_direct_labor
                )
                * parameters.drug_lab_capital_labor
            ),
        ),
        MEALS: Process(
            "provisioning",
            outputs={MEALS: 1.0},
            # Aggregated farming plus cooking.  The raw-food feedstock sits
            # outside the modelled boundary like chemfuel's organic inputs;
            # the excluded stages' labor is already inside the 305 embodied
            # ticks the closed analysis measured for MealSimple.
            inputs={},
            direct_labor=parameters.meal_direct_labor,
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.meal_direct_labor
                )
                * parameters.provisioner_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.meal_direct_labor
                )
                * parameters.provisioner_capital_labor
            ),
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
        MEALS: parameters.meal_capacity_per_day,
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
        for key in (YAYO, LEAVES, CHEMFUEL, MEALS)
    ]
    # Build chemfuel reserve: first grade at the operating overhead, optional
    # second grade at a higher cost for depletion scenarios.
    chemfuel_overhead = parameters.operating_overhead(CHEMFUEL, yayo_cost)
    grades = [ResourceGrade(parameters.chemfuel_reserve_per_region, chemfuel_overhead)]
    if parameters.chemfuel_expensive_reserve > 0:
        grades.append(
            ResourceGrade(
                parameters.chemfuel_expensive_reserve,
                chemfuel_overhead * parameters.chemfuel_expensive_cost_multiplier,
            )
        )

    region = Region(
        name,
        cash=parameters.initial_cash,
        base_daily_demand={YAYO: parameters.daily_demand},
        inventory={},
        prices={key: commodities[key].reference_price for key in commodities},
        producers=producers,
        reserves={CHEMFUEL: ResourceReserve(CHEMFUEL, grades)},
        subsistence_basket={MEALS: parameters.meals_per_worker_day},
        ticks_per_worker_day=parameters.ticks_per_worker_day,
        labor_pool=parameters.labor_pool_worker_days,
        worker_cash=(
            parameters.worker_initial_cash_days
            * parameters.meals_per_worker_day
            * parameters.meal_reference_price
        ),
    )
    # Seed employment at the quantized fixed point of the daily map, so the
    # wage circuit opens stationary to the bit (docs/17 section 7).
    equilibrium_days = _equilibrium_worker_days(region, parameters)
    region.worker_days_due = equilibrium_days
    region.worker_days_earned = equilibrium_days
    # Seed every stock at its own target, so the circuit opens stationary
    # rather than working off an arbitrary initial imbalance.
    for key in commodities:
        region.inventory[key] = (
            region.throughput_demand(key) * parameters.target_inventory_days
        )
    return region


def _equilibrium_worker_days(
    region: Region, parameters: ScenarioParameters
) -> float:
    """Solve the quantized employment fixed point the runtime will repeat.

    The daily map is: legacy producers run at capacity, the provisioners run
    at the basket demand earned yesterday, and the resulting labor is
    quantized to the employment grid.  The float operations and the
    producer summation order replicate the runtime exactly, so the seeded
    value reproduces itself from day one.  Refuses loudly rather than
    seeding an inexact equilibrium.
    """
    ordered = sorted(region.producers, key=lambda p: (p.name, p.commodity))
    quantum = parameters.employment_quantum
    basket_quantity = parameters.meals_per_worker_day
    worker_days = 0.0
    for _ in range(256):
        labor = 0.0
        for producer in ordered:
            if producer.commodity == MEALS:
                runs = basket_quantity * worker_days
            else:
                runs = producer.process.runs_for(producer.capacity_per_day)
            labor += runs * producer.process.direct_labor
        raw = labor / parameters.ticks_per_worker_day
        if quantum > 0.0:
            revised = floor(raw / quantum) * quantum
        else:
            revised = raw
        if revised == worker_days:
            meal_demand = basket_quantity * worker_days
            if meal_demand >= parameters.meal_capacity_per_day:
                raise ValueError(
                    "equilibrium meal demand exceeds provisioning capacity; "
                    "the seeded circuit would not be stationary"
                )
            return worker_days
        worker_days = revised
    raise ValueError(
        "employment fixed point did not converge exactly; the wage circuit "
        "cannot be seeded stationary with these parameters"
    )


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
                MEALS: "Dust provisioners",
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
                MEALS: "River provisioners",
            },
        ),
    ]
    economy = Economy(
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
        buffer_refill_horizon_days=parameters.buffer_refill_horizon_days,
        labor_value_per_tick=parameters.labor_value_per_tick,
        employment_quantum=parameters.employment_quantum,
        labor_value_tolerance=parameters.labor_value_tolerance,
        labor_value_max_iterations=parameters.labor_value_max_iterations,
        competitive_price_intensity=parameters.competitive_price_intensity,
        competitive_share_elasticity=parameters.competitive_share_elasticity,
        capital_service_life_days=parameters.capital_service_life_days,
        production_price_tolerance=parameters.production_price_tolerance,
        production_price_max_iterations=(
            parameters.production_price_max_iterations
        ),
    )
    _assert_reference_full_utilization(economy)
    return economy


def _assert_reference_full_utilization(economy: Economy) -> None:
    """Refuse loudly if the wage pushes any producer below full utilization.

    The hazard of an additive wage (docs/17 section 4) is a producer quietly
    dropped below its full-utilization ratio at reference prices, which
    would silently break the stationary equilibrium.  Checked at seeding,
    raised at seeding.
    """
    for region in economy.regions.values():
        wage_per_tick = region.wage_rate() / max(
            region.ticks_per_worker_day, 1e-9
        )
        for producer in region.producers:
            wage_cost = (
                producer.process.labor_per_unit(
                    producer.commodity, economy.commodities
                )
                * wage_per_tick
            )
            effective = (
                producer.effective_unit_cost(region.prices) + wage_cost
            )
            price = region.prices[producer.commodity]
            ratio = price / max(effective, 1e-9)
            if ratio < producer.full_utilization_price_ratio:
                raise ValueError(
                    f"producer {producer.name!r} falls below full "
                    f"utilization at reference prices once wages are paid "
                    f"(price {price:.4f} / effective cost {effective:.4f} "
                    f"= {ratio:.4f}); the seeded equilibrium would not be "
                    "stationary"
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


def reserve_depletion(
    days: int = 300,
    *,
    dust_cheap_reserve: float = 600.0,
    dust_expensive_reserve: float = 100_000.0,
    expensive_cost_multiplier: float = 2.0,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """One region's cheap chemfuel grade exhausts mid-run.

    Dust Basin starts with only 600 units in its cheap grade (≈100 days at
    6/day).  A second expensive grade at 2× cost takes over.  Green River
    keeps the default large single-grade reserve, so the two regions end up
    on different grades — the minimal setup that produces differential rent.
    """
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    # Replace Dust Basin's reserve with a small two-grade deposit.
    dust = economy.regions["Dust Basin"]
    cheap_cost = dust.reserves[CHEMFUEL].grades[0].extraction_cost
    dust.reserves[CHEMFUEL] = ResourceReserve(
        CHEMFUEL,
        [
            ResourceGrade(dust_cheap_reserve, cheap_cost),
            ResourceGrade(dust_expensive_reserve, cheap_cost * expensive_cost_multiplier),
        ],
    )
    economy.step(days)
    return economy


def subsistence_shock(
    days_after_loss: int = 150,
    *,
    loss_fraction: float | None = None,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """Destroy most of one region's provisioning capacity.

    The wage-push channel, exercised: meal scarcity raises the meal price,
    the wage is the basket at current prices so it rises with it, and every
    producer's effective unit cost climbs through the cost-floor machinery.
    Workers who cannot obtain the basket register as unmet demand and a
    ledger shortfall — labor-power paid below its reproduction cost.
    """
    parameters = parameters or ScenarioParameters()
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    economy.destroy_capacity(
        "Dust Basin",
        MEALS,
        parameters.subsistence_loss_fraction
        if loss_fraction is None
        else loss_fraction,
    )
    economy.step(days_after_loss)
    return economy


def technique_change(
    days_after_entry: int = 180,
    *,
    efficient_direct_labor: float | None = None,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """A more productive provisioning technique enters one region.

    Relative surplus value, made to emerge (docs/19 section 7).  Dust Basin
    gains a second provisioner whose process needs half the living labor per
    meal.  Nothing about the wage, the basket, or the working day is
    touched: the working day stays 24,000 ticks and the basket stays two
    meals throughout.

    Part of society's meal output is now made in half the time, so the
    social value of meals falls, the value of labor-power falls with it, and
    the rate of surplus value rises — in *both* regions, including the one
    that adopted nothing.
    """
    parameters = parameters or ScenarioParameters()
    efficient_labor = (
        parameters.meal_efficient_direct_labor
        if efficient_direct_labor is None
        else efficient_direct_labor
    )
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(parameters.technique_change_day)
    dust = economy.regions["Dust Basin"]
    incumbent = next(p for p in dust.producers if p.commodity == MEALS)
    dust.producers.append(
        Producer(
            "Dust provisioners (new technique)",
            MEALS,
            parameters.meal_capacity_per_day,
            incumbent.unit_cost,
            parameters.zero_utilization_price_ratio,
            parameters.full_utilization_price_ratio,
            process=Process(
                "provisioning (efficient)",
                outputs={MEALS: 1.0},
                inputs={},
                direct_labor=efficient_labor,
                # Same kind of plant, but less labor time is spent at it, so
                # fewer machines support a unit of daily output (docs/23).
                capital_money_per_capacity=(
                    parameters.machines_per_capacity(efficient_labor)
                    * parameters.provisioner_capital_money
                ),
                capital_labor_per_capacity=(
                    parameters.machines_per_capacity(efficient_labor)
                    * parameters.provisioner_capital_labor
                ),
            ),
        )
    )
    economy.step(days_after_entry)
    return economy


def cost_competition(
    days_after_entry: int = 180,
    *,
    overhead_fraction: float | None = None,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """A cheaper provisioner enters, and undercuts the incumbent.

    The companion to `technique_change`, and its deliberate contrast. The
    entrant here saves *overhead*, not labor: same process, same living
    labor per meal, 60% of the incumbent's operating cost. Read it as
    better equipment or a better site — a capital-saving technique.

    Because the living labor per meal is untouched, the labor value of
    meals does not move at all, which makes this a clean instrument for
    the money-side mechanism: the order book tilts toward the cheaper
    producer, the sector's average cost falls, the anchor falls with it,
    and the meal price follows. The labor-time rate of surplus value
    should not budge (docs/21 section 4).
    """
    parameters = parameters or ScenarioParameters()
    fraction = (
        parameters.cheap_provisioner_overhead_fraction
        if overhead_fraction is None
        else overhead_fraction
    )
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(parameters.cost_competition_day)
    dust = economy.regions["Dust Basin"]
    incumbent = next(p for p in dust.producers if p.commodity == MEALS)
    dust.producers.append(
        Producer(
            "Dust provisioners (low overhead)",
            MEALS,
            parameters.meal_capacity_per_day,
            incumbent.unit_cost * fraction,
            parameters.zero_utilization_price_ratio,
            parameters.full_utilization_price_ratio,
            process=incumbent.process,
        )
    )
    economy.step(days_after_entry)
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
            # Two distinct quantities, deliberately named apart: the frozen
            # FINDINGS.md import, and the model's own solve from the process
            # graph (docs/19).  They differ by exactly the stylized chemfuel
            # link, which is the point of keeping both visible.
            "authored_labor_value": commodity.labor_value,
            "labor_value_ticks": round(economy.labor_values["yayo"], 4),
            "labor_value_silver": round(
                economy.labor_values["yayo"] * economy.labor_value_per_tick, 4
            ),
            "price_to_labor_value": round(
                region.prices["yayo"]
                / (
                    economy.labor_values["yayo"] * economy.labor_value_per_tick
                ),
                3,
            ),
            "individual_labor_value_ticks": {
                key: round(value, 4)
                for key, value in sorted(
                    economy.regional_labor_values.get(name, {}).items()
                )
            },
            "inventory": round(region.inventory["yayo"], 3),
            "capacity_per_day": round(region.capacity("yayo"), 3),
            "imports": round(region.imported_total["yayo"], 3),
            "exports": round(region.exported_total["yayo"], 3),
            "employment_worker_days": round(region.worker_days_earned, 6),
            "wage_rate": round(region.wage_rate(), 3),
            "worker_cash": round(region.worker_cash, 3),
            "wages_paid": round(
                economy.ledger.wages_paid.get(name, 0.0), 3
            ),
            "basket_shortfall": round(
                economy.ledger.basket_shortfall.get(name, 0.0), 3
            ),
            "rate_of_surplus_value": (
                None
                if economy.rate_of_surplus_value(name) is None
                else round(economy.rate_of_surplus_value(name), 3)
            ),
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
        # The classical magnitudes, in work-ticks (docs/23). Value ratios,
        # never money ones: the value rate of profit and money
        # profitability are different quantities.
        "value_ledger": {
            "constant_capital": round(
                sum(economy.ledger.constant_capital(r) for r in economy.regions), 3
            ),
            "circulating_capital": round(
                sum(
                    economy.ledger.circulating_capital.get(r, 0.0)
                    for r in economy.regions
                ),
                3,
            ),
            "fixed_capital_consumed": round(
                sum(
                    economy.ledger.fixed_capital_consumed.get(r, 0.0)
                    for r in economy.regions
                ),
                3,
            ),
            "variable_capital": round(
                sum(
                    economy.ledger.necessary_labor.get(r, 0.0)
                    for r in economy.regions
                ),
                3,
            ),
            "surplus_labor": round(
                sum(economy.ledger.surplus_labor(r) for r in economy.regions), 3
            ),
            "organic_composition": (
                None
                if economy.organic_composition() is None
                else round(economy.organic_composition(), 4)
            ),
            "value_rate_of_profit": (
                None
                if economy.value_rate_of_profit() is None
                else round(economy.value_rate_of_profit(), 4)
            ),
        },
        "value_residual": round(economy.value_balance(), 6),
        # What the model can and cannot account for in a unit's price. The
        # margin is reported, not explained: the laboratory cannot tell
        # whether it is surplus or a cost it does not represent.
        "price_decomposition": {
            region_name: {
                key: {
                    part: round(value, 5)
                    for part, value in economy.price_decomposition(
                        region_name, key
                    ).items()
                }
                for key in sorted(economy.commodities)
            }
            for region_name in sorted(economy.regions)
        },
        "social_labor_values_ticks": {
            key: round(value, 4)
            for key, value in sorted(economy.labor_values.items())
        },
        "stale_labor_values": sorted(economy.stale_labor_values),
        # The classical price system, computed but not adopted (docs/26).
        # An observation beside the authored prices, never an input to them.
        "prices_of_production": _production_price_report(economy),
    }


def _production_price_report(economy: Economy) -> Dict[str, object] | None:
    """Prices of production beside labor values and authored prices.

    Reported relative to the wage good, because the eigenvector fixes only
    relative prices and a table of ratios is the readable form.  The
    aggregates use the labor-value normalization, under which total price
    equals total value by construction and total profit then does not
    (docs/26 section 3.6).
    """
    system = economy.prices_of_production(numeraire=MEALS)
    if system is None:
        return None
    aggregates = economy.production_price_aggregates()
    prices = system["prices"]
    base_price = prices.get(MEALS, 0.0)
    base_value = economy.labor_values.get(MEALS, 0.0)
    base_reference = economy.commodities[MEALS].reference_price
    return {
        "profit_rate": round(system["profit_rate"], 6),
        "basics": system["basics"],
        "iterations": system["iterations"],
        "wage_per_tick": round(system["wage"], 8),
        "relative_to_meals": {
            key: {
                "labor_value": round(
                    economy.labor_values.get(key, 0.0) / base_value, 5
                ),
                "price_of_production": round(prices[key] / base_price, 5),
                "authored_price": round(
                    economy.commodities[key].reference_price / base_reference, 5
                ),
            }
            for key in sorted(prices)
            if base_price > 0.0 and base_value > 0.0
        },
        "aggregates": {
            key: round(value, 4) for key, value in sorted(aggregates.items())
        },
        # Marx's two invariance postulates cannot both hold.  The first is
        # imposed by the normalization; this is how far the second misses.
        "profit_over_surplus": round(
            aggregates["total_profit"] / aggregates["total_surplus"], 5
        ),
    }
