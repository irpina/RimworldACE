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

from dataclasses import dataclass, replace
from math import floor
from typing import Dict, List, Tuple

from .model import (
    Commodity,
    EPSILON,
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
GARMENTS = "garments"
MEDICINE = "herbal_medicine"
STEEL = "steel"
WOOD = "wood"
COMPONENTS = "components"


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
    #: The smallest employable unit of labor at a producer, in
    #: worker-days (docs/102).  Zero is off.  There is no defensible
    #: single value at the laboratory's scale -- Dust Basin employs 0.318
    #: worker-days in total -- so it is swept rather than set.
    producer_employment_quantum: float = 0.0
    subsistence_loss_fraction: float = 0.70

    # --- wages off the value of labor-power (docs/46) -----------------------
    #: The reserve-army rule.  Strength is the wage premium per unit change
    #: in the employment rate; speed is the fraction of the gap closed a
    #: day.  Zero strength -- the default -- is wages at value and is
    #: bit-identical.  The bargaining scenarios switch it to
    #: ``bargaining_scenario_strength`` so the same shock can be run with
    #: and without the rule.
    wage_bargaining_strength: float = 0.0
    wage_bargaining_speed: float = 0.1
    bargaining_scenario_strength: float = 1.0
    #: Final demand for yayo in the local region rises by this factor on
    #: the shock day; investment meets it and employment climbs.
    boom_demand_multiplier: float = 1.25

    # --- habituation (docs/51) ----------------------------------------------
    #: How fast a sustained premium becomes the habitual standard: the
    #: fraction of the gap between the standard and the paid real wage
    #: that becomes habit each day, upward only.  Zero, the default, is
    #: bit-identical to no rule; the scenarios use
    #: ``habituation_scenario_speed``, a fifty-day time constant against
    #: the reserve army's ten, so habits form more slowly than wages move.
    habituation_speed: float = 0.0
    habituation_scenario_speed: float = 0.02
    #: The day the boom's final demand returns to its seeded level in the
    #: reversal scenario.
    boom_reversal_day: int = 210

    # --- producer cash (docs/55) --------------------------------------------
    #: Whether producers hold silver, pay inputs, plant matter and wages
    #: from it, and are removed when they cannot.  Off by default and
    #: bit-identical off.  The working capital target is days of
    #: full-capacity outlay a purse keeps before distributing the rest to
    #: the owners' fund; the idle count is how many consecutive days a
    #: producer may plan runs it cannot pay for before it is removed.
    producer_cash: bool = False
    working_capital_days: float = 5.0
    bankruptcy_idle_days: int = 30

    # --- firm-posted prices (docs/57) ---------------------------------------
    #: Whether producers post their own prices, moved by their own cost
    #: and the pool's pressure, with the authored price only where they
    #: start.  Off by default and bit-identical off: the anchored rule of
    #: docs/21 stands.
    posted_prices: bool = False
    #: The integral gain on the pool's pressure -- a fiftieth of the
    #: anchored rule's proportional speed, for the reason docs/58 section
    #: 2 records -- and the weight on a producer's own order fill against
    #: its sector's.
    posted_price_speed: float = 0.02
    posted_share_gain: float = 1.0

    # --- procurement (docs/59) ----------------------------------------------
    #: Whether producers own their output and buy their inputs from each
    #: other at posted prices, with no sector plan and no fixed point.
    #: Needs producer cash and posted prices; off by default and
    #: bit-identical off.
    procurement: bool = False
    #: The going margin over cost (docs/62), and how hard idle capacity
    #: with a margin above it cuts.  The default sits above every seeded
    #: margin, so the seeded circuit is stationary; the gravitation
    #: scenario lowers it to ``gravitation_margin``.
    going_margin: float = 0.50
    idle_capacity_gain: float = 1.0
    gravitation_margin: float = 0.30

    # --- entry on margin (docs/61) --------------------------------------------
    #: Whether capital enters a sector because its expected price clears
    #: the best technique's cost by more than ``going_margin``, with no
    #: shortfall asked for.  Off by default and bit-identical off.
    entry_on_margin: bool = False
    entry_gain: float = 0.05

    # --- exit on return (docs/64) ---------------------------------------------
    #: Whether a producer whose return on its capacity -- margin times
    #: utilization -- has been below the going one for the lead time
    #: withdraws the capacity beyond ``capacity_reserve`` over the demand
    #: it expects, ``exit_gain`` times how far below per interval.  Needs
    #: procurement; off by default and bit-identical off.
    exit_on_return: bool = False
    capacity_reserve: float = 0.10
    exit_gain: float = 1.0

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

    # --- the enlarged subsistence basket (docs/28) ---------------------------
    # Clothing and medicine join meals.  Reference prices are RimWorld
    # MarketValue and direct labor is embodied work-ticks, both from the
    # closed analysis: Apparel_BasicShirt at 1620 ticks and MedicineHerbal
    # at 400.  The basket quantities come from a cold-biome wardrobe
    # (shirt, pants, tuque, parka = 8.16 shirt-equivalents) replaced
    # annually over a 60-day year, and from 7.5 doses a year, each rounded
    # down to an exact binary fraction for the same floating-point reasons
    # as the rest of the calibration.
    garment_reference_price: float = 85.76
    garment_direct_labor: float = 1620.0
    garment_labor_value: float = 1620.0 * 11.4 / 720.0
    garment_mass: float = 0.6
    garment_capacity_per_day: float = 0.25
    garments_per_worker_day: float = 0.125
    medicine_reference_price: float = 10.0
    medicine_direct_labor: float = 400.0
    medicine_labor_value: float = 400.0 * 11.4 / 720.0
    medicine_mass: float = 0.35
    medicine_capacity_per_day: float = 0.25
    medicine_per_worker_day: float = 0.125
    #: The tailoring bench is powered.  Derived, not chosen: the drug lab
    #: draws 0.2 chemfuel per 350 ticks of work, so the same energy per tick
    #: of bench time gives 1620 * 0.2 / 350.  The third use of the docs/08
    #: stylization, and the one that makes chemfuel a *basic* commodity.
    chemfuel_per_garment: float = 0.2 * 1620.0 / 350.0
    #: Hand bench and plant pot, from the closed analysis, on the docs/23
    #: rule: machines in proportion to the labor performed at them.
    tailoring_bench_capital_money: float = 157.2
    tailoring_bench_capital_labor: float = 3_687.5
    plant_pot_capital_money: float = 40.9
    plant_pot_capital_labor: float = 700.0
    #: An indefensibly large bundle, to bound the answer from above rather
    #: than resting the conclusion on one point estimate (docs/28 s3.5).
    generous_meals_per_worker_day: float = 3.0
    generous_garments_per_worker_day: float = 0.5
    generous_medicine_per_worker_day: float = 0.5

    # --- turnover (docs/30) ---------------------------------------------------
    #: How long one run occupies its capital before the product exists.  One
    #: `step()`, which is what the runtime does.  Capital is advanced for
    #: this plus the commodity's own inventory life.
    production_period_days: float = 1.0
    #: Meals keep as long as everything else by default.  They do not, in
    #: RimWorld: a simple meal starts to rot after four days, which is the
    #: only differential turnover the current commodity set justifies.
    meal_target_inventory_days: float = 20.0
    perishable_meal_days: float = 4.0

    # --- history detail (docs/34) ---------------------------------------------
    #: History is an output; nothing in the simulation reads it.  At 647
    #: commodities and 100 regions a full snapshot costs ~16 MiB a day,
    #: which the runtime cannot carry.  Defaults reproduce today exactly.
    record_history: bool = True
    history_every: int = 1

    # --- Department I (docs/36) ----------------------------------------------
    # The six machines the model already used are bills of materials in three
    # commodities plus construction work, and each decomposes to the tick:
    # DrugLab, HydroponicsBasin, BiofuelRefinery, ElectricStove,
    # HandTailoringBench and PlantPot.  Nothing here is invented; it is the
    # closed analysis read one level deeper.  Off by default, because turning
    # it on changes the commodity set.
    capital_goods: bool = False
    steel_reference_price: float = 1.9
    steel_direct_labor: float = 47.5
    steel_labor_value: float = 47.5 * 11.4 / 720.0
    steel_mass: float = 0.5
    steel_capacity_per_day: float = 1.0
    wood_reference_price: float = 1.2
    wood_direct_labor: float = 22.5
    wood_labor_value: float = 22.5 * 11.4 / 720.0
    wood_mass: float = 0.4
    wood_capacity_per_day: float = 1.0
    #: `Make_ComponentIndustrial`: 12 steel and 5000 ticks for one component
    #: worth 32 silver.  The authored labor value is the closed analysis's
    #: 5570 embodied ticks, which omits fixed capital; the solved one will
    #: not, and the gap is the point.
    component_reference_price: float = 32.0
    component_direct_labor: float = 5000.0
    component_labor_value: float = 5570.0 * 11.4 / 720.0
    component_mass: float = 0.6
    component_capacity_per_day: float = 0.0625
    steel_per_component: float = 12.0
    #: The fourth use of the docs/08 power stylization, on the same terms as
    #: the tailoring bench: 0.2 chemfuel per 350 ticks of bench time.  It is
    #: applied rather than exempted, and docs/37 reports what it costs a
    #: 5000-tick recipe.
    chemfuel_per_component: float = 0.2 * 5000.0 / 350.0

    # --- capacity depreciation and exit (docs/38) ----------------------------
    #: Whether a producer that cannot carry its plant's maintenance sheds
    #: capacity.  Off by default, and not because it is unfinished: turning
    #: it on deletes the component sector, because RimWorld prices a
    #: component below what it costs to make one (docs/37 section 6).  That
    #: is the scenario's finding rather than an obstacle to it.
    capacity_exit: bool = False

    # --- recreation in the basket (docs/40) ----------------------------------
    #: Whether the workers' basket includes the model's own final good.
    #: Off by default: it makes yayo *basic*, and basicness is binary, so
    #: 0.2% more demand is a change of regime rather than a sensitivity.
    recreation_basket: bool = False
    #: Deliberately not calibrated from `Need_Joy` — RimWorld's recreation
    #: is met mostly for free and no colony lives on drugs, so a single
    #: "true" quantity would be an invention.  Reported over a sweep.  An
    #: exact binary fraction, for the docs/17 section 7 reason.
    yayo_per_worker_day: float = 0.0625
    #: Yayo runs at exactly full capacity in the seeded circuit, so the
    #: basket entry has nowhere to come from.  The scenario raises
    #: `producer_capacity_per_day` to this, rather than taking the room out
    #: of final demand, so the comparison is the same economy plus a basket
    #: entry and not a smaller economy.  It has to be the *base* parameter:
    #: leaves and chemfuel capacity are derived from it, and raising yayo's
    #: alone leaves the psychoid fields 4 units a day short — which is
    #: exactly what the first attempt did.
    recreation_capacity_per_day: float = 10.5

    # --- prices of production (docs/26) --------------------------------------
    # Same convergence discipline as the labor value solve, so the two
    # iterative systems fail on the same terms.
    production_price_tolerance: float = 1e-12
    production_price_max_iterations: int = 1000

    def machines_per_capacity(self, direct_labor: float) -> float:
        """Machines needed to support one unit of daily output."""
        return direct_labor / self.ticks_per_worker_day

    #: What each machine is made of, and the ticks to put it up.  Read off
    #: the game (docs/36 section 2); each reproduces the authored
    #: `*_capital_labor` exactly at Steel = 47.5, WoodLog = 22.5 and
    #: ComponentIndustrial = 5570 embodied ticks.
    @property
    def machine_bills(self) -> Dict[str, Tuple[Dict[str, float], float]]:
        return {
            YAYO: ({STEEL: 75.0, WOOD: 50.0, COMPONENTS: 6.0}, 3500.0),
            LEAVES: ({STEEL: 100.0, COMPONENTS: 1.0}, 2800.0),
            CHEMFUEL: ({STEEL: 150.0, COMPONENTS: 3.0}, 2000.0),
            MEALS: ({STEEL: 80.0, COMPONENTS: 2.0}, 2000.0),
            GARMENTS: ({WOOD: 75.0}, 2000.0),
            MEDICINE: ({WOOD: 20.0}, 250.0),
            # Department I owns its own means of production: a machining
            # table, itself 150 steel and 5 components.  This is the cycle
            # that makes the value solve circular, and it is the property
            # that makes this Department I rather than a third consumer
            # sector.
            COMPONENTS: ({STEEL: 150.0, COMPONENTS: 5.0}, 3000.0),
            # Mining and chopping need no building, which is true of the
            # game and keeps these two at the bottom of the value graph
            # where a productive matrix needs them.
            STEEL: ({}, 0.0),
            WOOD: ({}, 0.0),
        }

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
        """Enough for every consumer at *its* full capacity.

        Production is demand-led (`Economy._planned_runs`), so this is
        headroom rather than a target: the refinery runs at the day's draw
        and the surplus capacity only widens the inventory target.  The
        garment term is at full garment capacity, which is well above the
        basket's equilibrium call on it.
        """
        return (
            self.leaves_capacity_per_day * self.chemfuel_per_leaf
            + self.producer_capacity_per_day * self.chemfuel_per_yayo
            + self.garment_capacity_per_day * self.chemfuel_per_garment
        )

    @property
    def subsistence_basket(self) -> Dict[str, float]:
        """Units of each commodity reproducing one worker-day of labor-power."""
        basket = {
            MEALS: self.meals_per_worker_day,
            GARMENTS: self.garments_per_worker_day,
            MEDICINE: self.medicine_per_worker_day,
        }
        if self.recreation_basket:
            basket[YAYO] = self.yayo_per_worker_day
        return basket

    def basket_cost(self) -> float:
        """The basket at reference prices: the money wage per worker-day."""
        reference = {
            MEALS: self.meal_reference_price,
            GARMENTS: self.garment_reference_price,
            MEDICINE: self.medicine_reference_price,
            YAYO: self.reference_price,
        }
        return sum(
            quantity * reference[name]
            for name, quantity in sorted(self.subsistence_basket.items())
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
            GARMENTS: self.garment_reference_price,
            MEDICINE: self.medicine_reference_price,
            STEEL: self.steel_reference_price,
            WOOD: self.wood_reference_price,
            COMPONENTS: self.component_reference_price,
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
    target_inventory_days: float | None = None,
) -> Commodity:
    return Commodity(
        name,
        reference_price=reference_price,
        labor_value=labor_value,
        demand_elasticity=parameters.demand_elasticity,
        target_inventory_days=(
            parameters.target_inventory_days
            if target_inventory_days is None
            else target_inventory_days
        ),
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
            parameters.meal_target_inventory_days,
        ),
        _commodity(
            parameters,
            GARMENTS,
            parameters.garment_reference_price,
            parameters.garment_labor_value,
            parameters.garment_mass,
        ),
        _commodity(
            parameters,
            MEDICINE,
            parameters.medicine_reference_price,
            parameters.medicine_labor_value,
            parameters.medicine_mass,
        ),
    ] + (
        [
            _commodity(
                parameters,
                STEEL,
                parameters.steel_reference_price,
                parameters.steel_labor_value,
                parameters.steel_mass,
            ),
            _commodity(
                parameters,
                WOOD,
                parameters.wood_reference_price,
                parameters.wood_labor_value,
                parameters.wood_mass,
            ),
            _commodity(
                parameters,
                COMPONENTS,
                parameters.component_reference_price,
                parameters.component_labor_value,
                parameters.component_mass,
            ),
        ]
        if parameters.capital_goods
        else []
    )


def circuit_processes(
    parameters: ScenarioParameters | None = None,
) -> Dict[str, Process]:
    """The three technologies, keyed by their primary output."""
    parameters = parameters or ScenarioParameters()
    processes = {
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
        GARMENTS: Process(
            "tailoring",
            outputs={GARMENTS: 1.0},
            # The bench is powered.  Same energy per tick of bench time as
            # the drug lab, which is where the coefficient comes from; the
            # cloth itself sits outside the boundary like the raw food and
            # the organic feedstock, its labor already inside the 1620
            # embodied ticks the closed analysis measured.
            inputs={CHEMFUEL: parameters.chemfuel_per_garment},
            direct_labor=parameters.garment_direct_labor,
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.garment_direct_labor
                )
                * parameters.tailoring_bench_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.garment_direct_labor
                )
                * parameters.tailoring_bench_capital_labor
            ),
        ),
        MEDICINE: Process(
            "herb gathering",
            outputs={MEDICINE: 1.0},
            # Grown in soil and harvested by hand: no energy draw, and the
            # only plant is the pot it grows in.
            inputs={},
            direct_labor=parameters.medicine_direct_labor,
            capital_money_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.medicine_direct_labor
                )
                * parameters.plant_pot_capital_money
            ),
            capital_labor_per_capacity=(
                parameters.machines_per_capacity(
                    parameters.medicine_direct_labor
                )
                * parameters.plant_pot_capital_labor
            ),
        ),
    }
    if parameters.capital_goods:
        return _capital_goods_processes(parameters, processes)
    return processes


def _capital_goods_processes(
    parameters: ScenarioParameters, processes: Dict[str, Process]
) -> Dict[str, Process]:
    """Attach the bills of materials, and add Department I itself (docs/36).

    The six existing processes keep their authored `*_capital_*` scalars as
    a fallback and gain the bill that supersedes them, so the two can be
    compared rather than conflated — the same choice `Commodity.labor_value`
    made in docs/19.

    Steel and wood are extraction with no plant behind them.  Components are
    manufactured at a machining table which is itself 150 steel and 5
    components, which is the cycle the value solve has to close.
    """
    bills = parameters.machine_bills
    revised = {
        name: replace(
            process,
            capital_bill=bills[name][0],
            capital_construction_labor=bills[name][1],
            machines_per_capacity=parameters.machines_per_capacity(
                process.direct_labor
            ),
        )
        for name, process in processes.items()
    }
    revised[STEEL] = Process(
        "steel mining",
        outputs={STEEL: 1.0},
        inputs={},
        direct_labor=parameters.steel_direct_labor,
    )
    revised[WOOD] = Process(
        "wood cutting",
        outputs={WOOD: 1.0},
        inputs={},
        direct_labor=parameters.wood_direct_labor,
    )
    revised[COMPONENTS] = Process(
        "component fabrication",
        outputs={COMPONENTS: 1.0},
        inputs={
            STEEL: parameters.steel_per_component,
            CHEMFUEL: parameters.chemfuel_per_component,
        },
        direct_labor=parameters.component_direct_labor,
        capital_bill=bills[COMPONENTS][0],
        capital_construction_labor=bills[COMPONENTS][1],
        machines_per_capacity=parameters.machines_per_capacity(
            parameters.component_direct_labor
        ),
    )
    return revised


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
        GARMENTS: parameters.garment_capacity_per_day,
        MEDICINE: parameters.medicine_capacity_per_day,
        STEEL: parameters.steel_capacity_per_day,
        WOOD: parameters.wood_capacity_per_day,
        COMPONENTS: parameters.component_capacity_per_day,
    }
    sectors = (YAYO, LEAVES, CHEMFUEL, MEALS, GARMENTS, MEDICINE)
    if parameters.capital_goods:
        sectors += (STEEL, WOOD, COMPONENTS)
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
        for key in sectors
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
        subsistence_basket=parameters.subsistence_basket,
        ticks_per_worker_day=parameters.ticks_per_worker_day,
        labor_pool=parameters.labor_pool_worker_days,
        worker_cash=(
            parameters.worker_initial_cash_days * parameters.basket_cost()
        ),
    )
    # Seed employment at the quantized fixed point of the daily map, so the
    # wage circuit opens stationary to the bit (docs/17 section 7).
    equilibrium_days = _equilibrium_worker_days(region, parameters)
    region.worker_days_due = equilibrium_days
    region.worker_days_earned = equilibrium_days
    # The employment rate the wage rule measures against (docs/46), taken
    # with the same expression the rule uses so the two agree to the bit.
    region.reference_employment_rate = region.employment_rate()
    if parameters.procurement:
        # Each producer plans from yesterday's sales (docs/59); seeded at
        # the stationary outflow so the first day repeats the seed.
        ordered = sorted(region.producers, key=lambda p: (p.name, p.commodity))
        runs = _stationary_runs(region, ordered, equilibrium_days)
        for producer in ordered:
            producer.sales_yesterday = (
                runs[id(producer)] * producer.process.outputs[producer.commodity]
            )
    # Seed every stock at its own target, so the circuit opens stationary
    # rather than working off an arbitrary initial imbalance.  The target is
    # the *commodity's* inventory life, not the global default: they were
    # the same number until meals started rotting (docs/30).
    for key in commodities:
        region.inventory[key] = (
            region.throughput_demand(key)
            * commodities[key].target_inventory_days
        )
    return region


def _stationary_runs(
    region: Region, ordered: List[Producer], worker_days: float
) -> Dict[int, float]:
    """Runs that exactly replace a day's outflow, capped by capacity.

    This is `Economy._planned_runs` evaluated at the stationary point:
    with every stock already at its target the replenishment correction is
    zero, so requested output *is* the day's intended outflow — final
    demand, the workers' basket, and every producer's input draw.

    Generalized from the earlier "non-basket producers run at capacity"
    rule, which was true only while every intermediate sector's capacity
    happened to equal its draw.  It stopped being true when a wage good
    acquired a material input (docs/28).
    """
    runs = {id(producer): 0.0 for producer in ordered}
    # One pass per stage, plus one to observe that nothing moved.  That bound
    # was right while the input graph was a chain; fixed capital makes it
    # cyclic — components need a machining table, which needs components —
    # and a pass no longer buys a whole stage.  Measured rather than
    # guessed: the docs/36 circuit settles on the eleventh pass against an
    # old bound of eleven, so the bound is widened with room and still
    # refuses loudly rather than returning an inexact plan.
    for _ in range(4 * len(ordered) + 2):
        outflow = {
            name: region.base_daily_demand.get(name, 0.0)
            for name in region.prices
        }
        for name, quantity in sorted(region.subsistence_basket.items()):
            if name in outflow:
                outflow[name] += quantity * worker_days
        for producer in ordered:
            for name, per_run in producer.process.inputs.items():
                outflow[name] += runs[id(producer)] * per_run
        # Plant replacement, on the calendar (docs/38): a second pass in the
        # same producer order `Economy._planned_runs` uses, because the seed
        # has to reproduce the runtime to the bit.
        for producer in ordered:
            per_capacity = (
                producer.capacity_per_day / region.capital_service_life_days
            )
            for name, quantity in (
                producer.process.capital_bill_per_capacity().items()
            ):
                if name in outflow:
                    outflow[name] += per_capacity * quantity
        revised = {}
        for producer in ordered:
            units = producer.process.outputs[producer.commodity]
            revised[id(producer)] = min(
                outflow.get(producer.commodity, 0.0) / units,
                producer.process.runs_for(producer.capacity_per_day),
            )
        if revised == runs:
            return revised
        runs = revised
    raise ValueError(
        "stationary production plan did not converge; the input matrix is "
        "not productive at these capacities"
    )


def _equilibrium_worker_days(
    region: Region, parameters: ScenarioParameters
) -> float:
    """Solve the quantized employment fixed point the runtime will repeat.

    The daily map is: every producer replaces the day's outflow (capped by
    its capacity), the basket sectors' outflow is the demand earned
    yesterday, and the resulting labor is quantized to the employment grid.
    The float operations replicate the runtime, so the seeded value
    reproduces itself from day one.  Refuses loudly rather than seeding an
    inexact equilibrium.
    """
    ordered = sorted(region.producers, key=lambda p: (p.name, p.commodity))
    quantum = parameters.employment_quantum
    worker_days = 0.0
    for _ in range(256):
        runs = _stationary_runs(region, ordered, worker_days)
        labor = 0.0
        for producer in ordered:
            labor += runs[id(producer)] * producer.process.direct_labor
        # Construction labor rebuilding worn plant is living labor and is
        # employed like any other (docs/36 3.3), taken on the calendar
        # (docs/38).  Its own pass, in the same order `_produce` uses, so the
        # quantized employment fixed point sees the identical float.
        for producer in ordered:
            if (
                producer.process.capital_bill
                and producer.capacity_per_day > EPSILON
            ):
                labor += (
                    producer.capacity_per_day
                    / region.capital_service_life_days
                    * producer.process.machines_per_capacity
                    * producer.process.capital_construction_labor
                )
        raw = labor / parameters.ticks_per_worker_day
        if quantum > 0.0:
            revised = floor(raw / quantum) * quantum
        else:
            revised = raw
        if revised == worker_days:
            _assert_basket_provisioned(region, worker_days)
            return worker_days
        worker_days = revised
    raise ValueError(
        "employment fixed point did not converge exactly; the wage circuit "
        "cannot be seeded stationary with these parameters"
    )


def _assert_basket_provisioned(region: Region, worker_days: float) -> None:
    """Every basket good must have capacity to spare, and be named if not.

    An under-provisioned basket would otherwise show up as a permanent
    shortfall in the ledger rather than as an error at seeding.
    """
    for name, quantity in sorted(region.subsistence_basket.items()):
        demand = quantity * worker_days
        capacity = region.capacity(name)
        if demand >= capacity:
            raise ValueError(
                f"equilibrium {name!r} demand ({demand:.6f}/day) meets or "
                f"exceeds capacity ({capacity:.6f}/day) in region "
                f"{region.name!r}; the seeded circuit would not be stationary"
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
                GARMENTS: "Dust tailors",
                MEDICINE: "Dust herbalists",
                STEEL: "Dust steelworks",
                WOOD: "Dust woodcutters",
                COMPONENTS: "Dust machinists",
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
                GARMENTS: "River tailors",
                MEDICINE: "River herbalists",
                STEEL: "River steelworks",
                WOOD: "River woodcutters",
                COMPONENTS: "River machinists",
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
        producer_employment_quantum=parameters.producer_employment_quantum,
        labor_value_tolerance=parameters.labor_value_tolerance,
        labor_value_max_iterations=parameters.labor_value_max_iterations,
        competitive_price_intensity=parameters.competitive_price_intensity,
        competitive_share_elasticity=parameters.competitive_share_elasticity,
        capital_service_life_days=parameters.capital_service_life_days,
        capacity_exit=parameters.capacity_exit,
        production_price_tolerance=parameters.production_price_tolerance,
        production_price_max_iterations=(
            parameters.production_price_max_iterations
        ),
        production_period_days=parameters.production_period_days,
        record_history=parameters.record_history,
        history_every=parameters.history_every,
        wage_bargaining_strength=parameters.wage_bargaining_strength,
        wage_bargaining_speed=parameters.wage_bargaining_speed,
        habituation_speed=parameters.habituation_speed,
        producer_cash=parameters.producer_cash,
        working_capital_days=parameters.working_capital_days,
        bankruptcy_idle_days=parameters.bankruptcy_idle_days,
        posted_prices=parameters.posted_prices,
        posted_price_speed=parameters.posted_price_speed,
        posted_share_gain=parameters.posted_share_gain,
        procurement=parameters.procurement,
        going_margin=parameters.going_margin,
        idle_capacity_gain=parameters.idle_capacity_gain,
        entry_on_margin=parameters.entry_on_margin,
        entry_gain=parameters.entry_gain,
        exit_on_return=parameters.exit_on_return,
        capacity_reserve=parameters.capacity_reserve,
        exit_gain=parameters.exit_gain,
    )
    _assert_reference_full_utilization(economy)
    return economy


def _assert_reference_full_utilization(economy: Economy) -> None:
    """Refuse loudly if a producer cannot supply what the circuit asks of it.

    The hazard of an additive wage (docs/17 section 4) is a producer quietly
    curtailed at reference prices, which would silently break the stationary
    equilibrium.  That was checked by a proxy — full utilization — and the
    proxy is wrong in both directions.

    It over-refuses.  A sector priced below the full-utilization ratio is
    curtailed but not stopped, and if what it is curtailed *to* still clears
    the circuit's stationary call on it by a wide margin, the equilibrium is
    exactly as stationary as before.  Department I found this: components
    clear their cost by 1.45% before power and lose 19% after it, so the
    proxy refuses a sector whose desired output is fourteen times the draw
    (docs/37).

    So this checks the property the proxy stood for: the runs a producer's
    utilization permits must cover the runs the stationary circuit asks of
    it.  Full utilization is still reported in the message, because it is
    still the diagnosis in the usual case, but it is no longer the test.

    What this does *not* catch is a producer whose capacity is below its
    own stationary draw, because `_stationary_runs` caps at capacity and so
    never asks for more than a producer can give.  The old check did not
    catch it either.  Naming it here rather than claiming an improvement
    that was not made.
    """
    for region in economy.regions.values():
        ordered = sorted(
            region.producers, key=lambda p: (p.name, p.commodity)
        )
        stationary = _stationary_runs(
            region, ordered, region.worker_days_due
        )
        for producer in ordered:
            effective = producer.effective_unit_cost(region.prices)
            price = region.prices[producer.commodity]
            ratio = price / max(effective, 1e-9)
            permitted = producer.desired_runs(price, region.prices)
            asked = stationary[id(producer)]
            if permitted >= asked:
                continue
            raise ValueError(
                f"producer {producer.name!r} cannot supply the stationary "
                f"circuit at reference prices once wages are paid: it is "
                f"asked for {asked:.6f} runs a day and its price/effective "
                f"cost of {price:.4f}/{effective:.4f} = {ratio:.4f} permits "
                f"only {permitted:.6f}; the seeded equilibrium would not be "
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


def generous_basket(
    days: int = 240, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The equilibrium circuit with an indefensibly generous basket.

    Three meals, half a garment and half a dose a day: a bundle nobody
    could call stingy.  Its job is to bound the rate of surplus value from
    above, so the conclusion in docs/29 is a range rather than one point
    estimate (docs/28 section 3.5).

    Capacities double alongside, because the point is to measure the
    ratios under a larger basket rather than to measure a shortage.
    """
    parameters = parameters or ScenarioParameters()
    generous = replace(
        parameters,
        meals_per_worker_day=parameters.generous_meals_per_worker_day,
        garments_per_worker_day=parameters.generous_garments_per_worker_day,
        medicine_per_worker_day=parameters.generous_medicine_per_worker_day,
        meal_capacity_per_day=parameters.meal_capacity_per_day * 2.0,
        garment_capacity_per_day=parameters.garment_capacity_per_day * 2.0,
        medicine_capacity_per_day=parameters.medicine_capacity_per_day * 2.0,
    )
    return equilibrium(days, parameters=generous)


def perishable_meals(
    days: int = 240, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The wage good rots, so the circuit cannot hold twenty days of it.

    RimWorld's simple meals start to rot after four days. That is a fact
    about the game rather than a knob, and it is the only *differential*
    turnover the current commodity set justifies — which makes it the one
    scenario that can show turnover moving relative prices, since a uniform
    turnover time only rescales the profit rate (docs/30 section 3.2).

    It changes two things at once: the price system's turnover for meals,
    and the model's actual meal buffer. Both are real and the results
    document reports them apart.
    """
    parameters = parameters or ScenarioParameters()
    perishable = replace(
        parameters,
        meal_target_inventory_days=parameters.perishable_meal_days,
    )
    return equilibrium(days, parameters=perishable)


def capital_goods(
    days: int = 240, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The circuit with its own means of production (docs/36).

    Nine commodities instead of six.  Steel and wood are extracted, components
    are made from steel at a machining table which is itself made of steel and
    components, and every sector's plant is rebuilt out of that stock at the
    rate the ledger has always said it wears out.

    Stationary to the bit, like the six-commodity equilibrium it extends, and
    for the same reason: a constant capacity implies a constant replacement
    draw, which is an ordinary constant input flow.
    """
    parameters = replace(
        parameters or ScenarioParameters(), capital_goods=True
    )
    return equilibrium(days, parameters=parameters)


def cash_circuit(
    days: int = 1200, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """Department I with producer cash (docs/55).

    Every producer holds a purse, pays inputs, plant matter and wages from
    it, and distributes what it holds above its working capital to the
    owners' fund, which buys the final good.  docs/37 section 6 found the
    component sector loses silver on every unit once the power stylization
    is applied; here that loss is a draining purse, and the scenario says
    what the rule does to a sector that does not pay.

    Twelve hundred days, because the sector runs at three percent of
    capacity and loses two hundredths of a silver a day: five days of
    working capital take five hundred and fifty days to drain, and the
    result is what happens after that (docs/56).
    """
    parameters = replace(
        parameters or ScenarioParameters(),
        capital_goods=True,
        producer_cash=True,
    )
    return equilibrium(days, parameters=parameters)


def gravitation(
    days: int = 720, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The market economy with entry on margin and the going margin set
    inside the band the authored prices give (docs/61 section 5).

    No shock.  At the seed every sector's margin over its best cost lies
    between 0.29 (yayo) and 0.46 (chemfuel); with the threshold at
    ``gravitation_margin`` capital enters every sector above it, prices
    fall toward cost times one plus the margin, and the scenario asks
    where the authored price structure goes when it is not a rest point.
    """
    parameters = parameters or ScenarioParameters()
    parameters = replace(
        parameters,
        producer_cash=True,
        posted_prices=True,
        procurement=True,
        entry_on_margin=True,
        going_margin=parameters.gravitation_margin,
    )
    return equilibrium(days, parameters=parameters)


def complete_market(parameters: ScenarioParameters | None = None) -> ScenarioParameters:
    """The market economy with entry and exit both on (docs/64): purses,
    posted prices, procurement, entry on margin and exit on return, at
    the default going margin."""
    parameters = parameters or ScenarioParameters()
    return replace(
        parameters,
        producer_cash=True,
        posted_prices=True,
        procurement=True,
        entry_on_margin=True,
        exit_on_return=True,
    )


def overshoot(
    days_after_loss: int = 440, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The 60% capacity loss on the complete market, 500 days (docs/64
    section 5): entry's pipeline overshoots the demand on its lead time,
    and exit takes the surplus out."""
    return producer_loss(days_after_loss, parameters=complete_market(parameters))


def capacity_exit(
    days: int = 4000, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """Plant that cannot pay for its own upkeep is not replaced (docs/38).

    The capital-goods circuit with the money rule on: a producer maintains
    plant in proportion to how much of the day's maintenance its margin
    covers, so competition is for survival and not only for orders.

    Four thousand days, which is sixty-six years and much longer than the
    design expected to need.  A sector shedding `1/L` a day takes about
    2,200 days to fall from headroom to the point where its price starts to
    respond, and the whole result of docs/39 is what happens *after* that.
    Ten years shows a decay in progress and no rest point, which is a
    misleading picture rather than a shorter one.
    """
    parameters = replace(
        parameters or ScenarioParameters(),
        capital_goods=True,
        capacity_exit=True,
    )
    return equilibrium(days, parameters=parameters)


def recreation_basket(
    days: int = 240, *, parameters: ScenarioParameters | None = None
) -> Economy:
    """The workers' basket includes the good the workers make (docs/40).

    Yayo becomes basic, psychoid leaves become basic through it, and the
    89.6% of the economy's fixed capital that docs/39 measured as inert
    stops being inert.  docs/37 section 8 left this as a standing
    prediction; this is what fires it.
    """
    parameters = parameters or ScenarioParameters()
    parameters = replace(
        parameters,
        capital_goods=True,
        recreation_basket=True,
        producer_capacity_per_day=parameters.recreation_capacity_per_day,
    )
    return equilibrium(days, parameters=parameters)


def recreation_sweep(
    quantities: List[float] | None = None,
    days: int = 120,
    *,
    parameters: ScenarioParameters | None = None,
) -> List[Dict[str, object]]:
    """The recreation basket as a curve rather than a point (docs/40 s1).

    The quantity is not calibrated and cannot honestly be: RimWorld's
    recreation need is met mostly for free.  So the answer is reported over
    a range, the same discipline docs/28 s3.5 used for the generous basket.

    The curve is what separates the two candidate mechanisms.  Basicness
    flips at the first positive quantity; the wage rises continuously with
    it.  If the rate of profit steps, basicness is doing the work; if it
    slides, the wage is.  It slides (docs/41).
    """
    base = parameters or ScenarioParameters()
    if quantities is None:
        quantities = [2.0 ** -12, 2.0 ** -8, 2.0 ** -6, 2.0 ** -4, 2.0 ** -2]
    rows: List[Dict[str, object]] = []
    for quantity in quantities:
        economy = equilibrium(
            days,
            parameters=replace(
                base,
                capital_goods=True,
                recreation_basket=True,
                yayo_per_worker_day=quantity,
                producer_capacity_per_day=base.recreation_capacity_per_day,
            ),
        )
        system = economy.prices_of_production()
        rows.append(
            {
                "yayo_per_worker_day": quantity,
                "profit_rate": system["profit_rate"],
                "basics": len(system["basics"]),
                "wage": economy.regions["Dust Basin"].wage_rate(),
                "rate_of_surplus_value": economy.rate_of_surplus_value(),
            }
        )
    return rows


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


def _bargaining(parameters: ScenarioParameters) -> ScenarioParameters:
    """The same parameters with the reserve-army wage rule switched on."""
    return replace(
        parameters,
        wage_bargaining_strength=parameters.bargaining_scenario_strength,
    )


def _habituating(parameters: ScenarioParameters) -> ScenarioParameters:
    """The same parameters with both wage rules switched on (docs/51)."""
    return replace(
        _bargaining(parameters),
        habituation_speed=parameters.habituation_scenario_speed,
    )


def demand_boom(
    days_after_boom: int = 300,
    *,
    bargaining: bool = False,
    habituation: bool = False,
    labor_pool: float | None = None,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """Raise the local region's final demand and let investment meet it.

    Yayo is already at capacity, so the extra demand is met by building
    plant, and employment climbs with it.  With ``bargaining`` the tighter
    labor market lifts the wage above the value of labor-power (docs/46);
    without it the same shock runs with the wage pinned to the basket, so
    every effect of the rule is a difference between the two runs.
    With ``habituation`` the sustained premium becomes the habitual
    standard as well (docs/51); it implies bargaining, since there is
    nothing to habituate to without it.  ``labor_pool`` overrides the
    reserve army's size for the sweep.
    """
    parameters = parameters or ScenarioParameters()
    if labor_pool is not None:
        parameters = replace(parameters, labor_pool_worker_days=labor_pool)
    if habituation:
        parameters = _habituating(parameters)
    elif bargaining:
        parameters = _bargaining(parameters)
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    region = economy.regions["Dust Basin"]
    region.base_daily_demand[YAYO] *= parameters.boom_demand_multiplier
    economy.step(days_after_boom)
    return economy


def boom_reversal(
    days_after_boom: int = 300,
    *,
    habituation: bool = True,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """The boom, and then final demand returns to where it was (docs/51).

    Bargaining is on either way.  Without habituation the premium falls
    back and the accounting returns to where it started; with it the
    standard stays where the boom left it and the paid wage does not, so
    the wage is below value for the rest of the run in a region that is
    not in crisis.  The scenario the upward-only rule exists for.
    """
    parameters = parameters or ScenarioParameters()
    parameters = (
        _habituating(parameters) if habituation else _bargaining(parameters)
    )
    economy = seeded_two_region_economy(
        route_capacity_per_day=parameters.standard_route_capacity_per_day,
        freight_per_unit=parameters.standard_freight_per_unit,
        travel_days=parameters.standard_travel_days,
        parameters=parameters,
    )
    economy.step(60)
    region = economy.regions["Dust Basin"]
    seeded_demand = region.base_daily_demand[YAYO]
    region.base_daily_demand[YAYO] = seeded_demand * parameters.boom_demand_multiplier
    reversal = parameters.boom_reversal_day
    economy.step(reversal - 60)
    # Restored to the identical float, not divided back.
    region.base_daily_demand[YAYO] = seeded_demand
    economy.step(60 + days_after_boom - reversal)
    return economy


def wage_slump(
    days_after_injection: int = 300,
    *,
    parameters: ScenarioParameters | None = None,
) -> Economy:
    """The regional glut with the wage rule on: a crisis throws the yayo
    sector's workers out, and the wage falls below value (docs/46)."""
    parameters = _bargaining(parameters or ScenarioParameters())
    return regional_glut(days_after_injection, parameters=parameters)


def reserve_army_sweep(
    pools: Tuple[float, ...] = (1.0, 0.5, float("inf")),
    *,
    parameters: ScenarioParameters | None = None,
) -> Dict[float, Economy]:
    """The boom, with bargaining, against reserve armies of different size.

    Marx's claim is that the reserve army regulates the wage's movement;
    the same shock against a smaller pool should move the wage further,
    and against an unbounded one not at all.
    """
    parameters = parameters or ScenarioParameters()
    return {
        pool: demand_boom(bargaining=True, labor_pool=pool, parameters=parameters)
        for pool in pools
    }


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
            "wage_premium": round(region.wage_premium, 6),
            # The habitual standard and what the premium still carries
            # above it (docs/51); the premium itself while no habit formed.
            "habitual_scale": round(region.habitual_scale, 6),
            "premium_over_value": round(region.premium_over_value(), 6),
            "value_of_labor_power_ticks": round(
                economy.value_of_labor_power(region), 4
            ),
            "worker_cash": round(region.worker_cash, 3),
            # Producer cash (docs/55): the purses, what they distributed
            # to the fund, and what the fund had to cover.  Zero throughout
            # while the rule is off.
            "producer_cash": round(sum(p.cash for p in region.producers), 3),
            "distributed": round(
                economy.ledger.distributions.get(name, 0.0), 3
            ),
            "fund_wage_support": round(
                economy.ledger.fund_wage_support.get(name, 0.0), 3
            ),
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
            # Wages as paid rather than at value (docs/46); equal to the
            # line above whenever there is no premium.
            "realized_rate_of_surplus_value": (
                None
                if economy.realized_rate_of_surplus_value(name) is None
                else round(economy.realized_rate_of_surplus_value(name), 3)
            ),
            "commodities": {
                key: {
                    "price": round(region.prices[key], 3),
                    "inventory": round(region.inventory[key], 3),
                    "capacity_per_day": round(region.capacity(key), 3),
                    "throughput_demand": round(region.throughput_demand(key), 3),
                    "unmet_demand": round(region.unmet_demand[key], 3),
                    **_posted_report(economy, region, key),
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
        "liquidity_curtailment_runs": {
            key: round(value, 6)
            for key, value in sorted(economy.ledger.liquidity_curtailment.items())
        },
        "bankruptcies": [
            list(entry) for entry in economy.ledger.bankruptcies
        ],
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


def _posted_report(economy: Economy, region: Region, commodity: str) -> Dict[str, object]:
    """What each producer asks and its markup on its own cost (docs/57);
    nothing while the anchored rule is in force."""
    if not economy.posted_prices:
        return {}
    posted = {}
    for producer in region.producers:
        if producer.active and producer.commodity == commodity:
            cost = producer.effective_unit_cost(region.prices)
            posted[producer.name] = {
                "posted_price": round(producer.posted_price, 4),
                "markup_on_cost": (
                    None if cost <= EPSILON else round(producer.posted_price / cost, 4)
                ),
            }
    return {"posted": posted}


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
