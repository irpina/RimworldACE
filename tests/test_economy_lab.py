import unittest
from dataclasses import replace

from economy_lab.model import (
    ALL_OR_NOTHING,
    EPSILON,
    Commodity,
    Process,
    Producer,
    ResourceGrade,
    ResourceReserve,
)
from economy_lab.scale import population, synthetic_economy
from economy_lab.scenarios import (
    CHEMFUEL,
    COMPONENTS,
    DAYS_PER_YEAR,
    GARMENTS,
    LEAVES,
    MEALS,
    MEDICINE,
    STEEL,
    WOOD,
    YAYO,
    ScenarioParameters,
    arbitrage,
    boom_reversal,
    capacity_exit,
    cash_circuit,
    capital_goods,
    circuit_processes,
    cost_competition,
    gravitation,
    demand_boom,
    equilibrium,
    generous_basket,
    input_shortage,
    perishable_meals,
    producer_loss,
    regional_glut,
    recreation_basket,
    recreation_sweep,
    reserve_army_sweep,
    reserve_depletion,
    seeded_two_region_economy,
    subsistence_shock,
    wage_slump,
    summary,
    technique_change,
)


class EconomyInvariantTests(unittest.TestCase):
    def assert_balances_close(self, economy):
        self.assertAlmostEqual(economy.commodity_balance("yayo"), 0.0, places=7)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)
        for snapshot in economy.history:
            for state in snapshot["regions"].values():
                self.assertGreaterEqual(state["inventory"]["yayo"], -1e-8)
                self.assertGreaterEqual(state["cash"], -1e-8)

    def test_seeded_economy_is_stable_for_four_years(self):
        economy = equilibrium(days=240)
        for region in economy.regions.values():
            self.assertAlmostEqual(region.prices["yayo"], 21.0, places=6)
            self.assertAlmostEqual(region.inventory["yayo"], 200.0, places=6)
        self.assert_balances_close(economy)

    def test_same_inputs_are_exactly_reproducible(self):
        first = arbitrage(days_after_shock=90)
        second = arbitrage(days_after_shock=90)
        self.assertEqual(first.history, second.history)
        self.assertEqual(first.shipments, second.shipments)

    def test_scenario_summary_exposes_shock_extrema(self):
        report = summary(arbitrage(days_after_shock=90))
        affected = report["regions"]["Dust Basin"]
        self.assertLess(affected["minimum_price"], affected["price"])
        self.assertGreater(affected["minimum_price_day"], 30)

    def test_all_benchmark_scenarios_close_the_ledgers(self):
        for economy in (arbitrage(), producer_loss()):
            with self.subTest(day=economy.day):
                self.assert_balances_close(economy)


class RegionalGlutTests(unittest.TestCase):
    def make_glut(self, route_capacity=1.0):
        economy = seeded_two_region_economy(
            route_capacity_per_day=route_capacity
        )
        economy.step(60)
        annual_consumption = (
            economy.regions["Dust Basin"].base_daily_demand["yayo"]
            * DAYS_PER_YEAR
        )
        economy.inject("Dust Basin", "yayo", annual_consumption * 0.25)
        economy.step(90)
        return economy

    def test_quarter_year_injection_crashes_local_not_distant_price(self):
        economy = self.make_glut()
        local = economy.series("Dust Basin", "yayo")[61:]
        distant = economy.series("Green River", "yayo")[61:]
        self.assertLessEqual(min(local), 21.0 * 0.80)
        self.assertGreaterEqual(min(distant), 21.0 * 0.95)

    def test_half_the_price_gap_recovers_within_four_quadrums(self):
        economy = self.make_glut()
        local = economy.series("Dust Basin", "yayo")
        shock = local[61:]
        minimum = min(shock)
        minimum_day = 61 + shock.index(minimum)
        halfway = minimum + (21.0 - minimum) / 2.0
        recovered = next(
            day
            for day in range(minimum_day, min(minimum_day + 61, len(local)))
            if local[day] >= halfway
        )
        self.assertLessEqual(recovered - minimum_day, 60)

    def test_profitable_planetary_arbitrage_moves_real_stock(self):
        connected = self.make_glut(route_capacity=1.0)
        isolated = self.make_glut(route_capacity=0.0)
        exports = connected.regions["Dust Basin"].exported_total["yayo"]
        self.assertGreater(exports, 0.0)
        self.assertAlmostEqual(
            exports,
            connected.regions["Green River"].imported_total["yayo"],
            places=7,
        )
        self.assertLess(
            connected.regions["Dust Basin"].consumed_total["yayo"],
            isolated.regions["Dust Basin"].consumed_total["yayo"],
        )


class ProducerLossTests(unittest.TestCase):
    def test_loss_of_sixty_percent_capacity_causes_shortage_and_entry(self):
        economy = producer_loss(days_after_loss=150)
        history = economy.history
        affected = [h["regions"]["Dust Basin"] for h in history[61:]]
        scarce = [
            state
            for state in affected
            if state["inventory"]["yayo"] < 100.0  # ten baseline days
        ]
        self.assertTrue(scarce)
        self.assertGreaterEqual(
            max(state["price"]["yayo"] for state in scarce), 21.0 * 1.50
        )

        # Four to eight quadrums after destruction (days 120–180 overall),
        # entry must restore at least 80% of baseline regional supply.
        restored = max(
            history[day]["regions"]["Dust Basin"]["capacity"]["yayo"]
            for day in range(120, 181)
        )
        self.assertGreaterEqual(restored, 8.0)


class ProcessAccountingTests(unittest.TestCase):
    """Process-level material balance: sources and sinks must be declared."""

    def test_every_commodity_traces_to_declared_sources_and_sinks(self):
        for economy in (
            equilibrium(days=120),
            regional_glut(),
            producer_loss(),
            arbitrage(),
            input_shortage(),
        ):
            for name, residual in economy.commodity_balances().items():
                with self.subTest(day=economy.day, commodity=name):
                    self.assertAlmostEqual(residual, 0.0, places=7)

    def test_no_commodity_stock_goes_negative(self):
        economy = input_shortage()
        for snapshot in economy.history:
            for state in snapshot["regions"].values():
                for name, held in state["inventory"].items():
                    with self.subTest(day=snapshot["day"], commodity=name):
                        self.assertGreaterEqual(held, -1e-8)

    def test_intermediate_use_is_booked_separately_from_consumption(self):
        economy = equilibrium(days=30)
        # Leaves and chemfuel have no final demand at all, so every unit that
        # left inventory did so as a production input. If the two buckets were
        # conflated the ledger would still close and the distinction between
        # final and productive consumption would be lost.
        for name in (LEAVES, CHEMFUEL):
            self.assertEqual(economy.ledger.consumption.get(name, 0.0), 0.0)
            self.assertGreater(economy.ledger.intermediate_consumption[name], 0.0)
        self.assertGreater(economy.ledger.consumption[YAYO], 0.0)
        self.assertEqual(economy.ledger.intermediate_consumption.get(YAYO, 0.0), 0.0)

    def test_input_use_matches_output_at_the_declared_ratio(self):
        """Material in must equal material out at the ratio the Process declares.

        At equilibrium the drug lab is the only consumer of leaves, so total
        leaf draw has to be exactly `leaves_per_yayo` times total yayo made.
        """
        economy = equilibrium(days=30)
        recipe = circuit_processes()[YAYO]
        produced = economy.ledger.production[YAYO]
        self.assertAlmostEqual(
            economy.ledger.intermediate_consumption[LEAVES],
            produced * recipe.inputs[LEAVES],
            places=6,
        )
        # Chemfuel is shared, so its draw is the sum over every consumer.
        # Since docs/28 that includes the tailors, whose bench is powered —
        # which is what makes chemfuel a basic commodity.
        farming = circuit_processes()[LEAVES]
        tailoring = circuit_processes()[GARMENTS]
        expected_chemfuel = (
            produced * recipe.inputs[CHEMFUEL]
            + economy.ledger.production[LEAVES] * farming.inputs[CHEMFUEL]
            + economy.ledger.production[GARMENTS] * tailoring.inputs[CHEMFUEL]
        )
        self.assertAlmostEqual(
            economy.ledger.intermediate_consumption[CHEMFUEL],
            expected_chemfuel,
            places=6,
        )

    def test_production_is_order_independent(self):
        """Reversing producer order must not change a single day's result."""
        forward = seeded_two_region_economy()
        reversed_order = seeded_two_region_economy()
        for region in reversed_order.regions.values():
            region.producers.reverse()
        forward.step(90)
        reversed_order.step(90)
        for name, region in forward.regions.items():
            other = reversed_order.regions[name]
            for commodity in forward.commodities:
                self.assertAlmostEqual(
                    region.inventory[commodity],
                    other.inventory[commodity],
                    places=9,
                )

    def test_glut_overhang_drains_toward_upstream_targets(self):
        economy = regional_glut(days_after_injection=240)
        local = economy.regions["Dust Basin"]
        for name in (LEAVES, CHEMFUEL):
            target = (
                local.throughput_demand(name)
                * economy.commodities[name].target_inventory_days
            )
            self.assertAlmostEqual(local.inventory[name], target, places=6)

    def test_equilibrium_is_exactly_stationary_for_every_commodity(self):
        economy = equilibrium(days=240)
        for region_name in economy.regions:
            for name in economy.commodities:
                prices = economy.series(region_name, name)
                stocks = economy.series(region_name, name, field="inventory")
                self.assertEqual(min(prices), max(prices))
                self.assertEqual(min(stocks), max(stocks))


class JointProductApportionmentTests(unittest.TestCase):
    """Mass apportionment is a documented choice; this pins the arithmetic."""

    def setUp(self):
        self.commodities = {
            "meat": Commodity("meat", 2.0, 1.0, mass_per_unit=0.03),
            "leather": Commodity("leather", 4.0, 1.0, mass_per_unit=0.02),
        }
        self.process = Process(
            "butchery",
            outputs={"meat": 50.0, "leather": 25.0},
            direct_labor=450.0,
            unit_operating_cost=10.0,
        )

    def test_shares_are_mass_weighted_and_sum_to_one(self):
        meat = self.process.share_of_cost("meat", self.commodities)
        leather = self.process.share_of_cost("leather", self.commodities)
        # meat 50 * 0.03 = 1.5, leather 25 * 0.02 = 0.5, total 2.0
        self.assertAlmostEqual(meat, 0.75, places=9)
        self.assertAlmostEqual(leather, 0.25, places=9)
        self.assertAlmostEqual(meat + leather, 1.0, places=9)

    def test_apportionment_is_not_driven_by_price(self):
        """Leather is the dearer good and still bears the smaller share."""
        self.assertGreater(
            self.commodities["leather"].reference_price,
            self.commodities["meat"].reference_price,
        )
        self.assertLess(
            self.process.share_of_cost("leather", self.commodities),
            self.process.share_of_cost("meat", self.commodities),
        )

    def test_per_unit_labor_divides_the_apportioned_share(self):
        self.assertAlmostEqual(
            self.process.labor_per_unit("meat", self.commodities),
            450.0 * 0.75 / 50.0,
            places=9,
        )
        self.assertAlmostEqual(
            self.process.operating_cost_per_unit("leather", self.commodities),
            10.0 * 0.25 / 25.0,
            places=9,
        )

    def test_single_output_process_bears_its_whole_cost(self):
        single = Process("farming", outputs={"meat": 4.0}, direct_labor=100.0)
        self.assertEqual(single.share_of_cost("meat", self.commodities), 1.0)
        self.assertAlmostEqual(
            single.labor_per_unit("meat", self.commodities), 25.0, places=9
        )


class InputConstraintTests(unittest.TestCase):
    def test_producer_without_a_process_is_rejected(self):
        with self.assertRaises(ValueError):
            Producer("free lunch", YAYO, 10.0, 14.0)

    def test_upstream_loss_propagates_downstream_rather_than_zeroing(self):
        economy = input_shortage()
        local = "Dust Basin"
        history = economy.history
        leaves = [h["regions"][local]["inventory"][LEAVES] for h in history]
        yayo_price = [h["regions"][local]["price"][YAYO] for h in history]
        leaf_price = [h["regions"][local]["price"][LEAVES] for h in history]

        # The shortage reaches the input market first...
        self.assertLess(min(leaves[61:]), leaves[60])
        # ...and the leaf price rises.
        self.assertGreater(max(leaf_price[61:]), leaf_price[60] * 1.50)
        # The cost channel propagates the signal downstream: the drug lab's
        # effective cost rises with leaf prices, curtailing yayo output and
        # raising the yayo price.
        self.assertGreater(max(yayo_price[61:]), yayo_price[60] * 1.50)

        # Yayo capacity is untouched throughout: the drug lab is constrained
        # by input cost (or material), not by its own installed capacity.
        capacity = [h["regions"][local]["capacity"][YAYO] for h in history]
        self.assertEqual(min(capacity), max(capacity))

    def test_constrained_output_degrades_rather_than_collapsing(self):
        """The point of proportional rationing: partial inputs, partial output.

        A cliff to zero would be the all-or-nothing rule, which is available
        but is not the default. This walks the shortage a day at a time and
        reads yayo production straight off the ledger.
        """
        economy = seeded_two_region_economy()
        economy.step(60)
        economy.destroy_capacity("Dust Basin", LEAVES, 0.70)

        capacity = economy.regions["Dust Basin"].capacity(YAYO)
        previous = economy.ledger.production[YAYO]
        constrained_days = 0
        for _ in range(150):
            economy.step(1)
            current = economy.ledger.production[YAYO]
            both_regions = current - previous
            previous = current
            # Green River is unaffected and keeps making its full 10/day, so
            # Dust Basin's own output is the remainder.
            local_output = both_regions - capacity
            self.assertGreaterEqual(local_output, -1e-9)
            if local_output < capacity - 1e-9:
                constrained_days += 1
                # Constrained, but never shut: the lab runs on what arrives.
                self.assertGreater(local_output, 0.0)

        self.assertGreater(constrained_days, 20)

    def test_all_or_nothing_is_available_and_differs(self):
        # Use a severe input-shortage scenario (90% leaf destruction) so
        # material actually binds despite the cost channel. The two rationing
        # modes must then produce different yayo inventories.
        proportional = seeded_two_region_economy()
        cliff = seeded_two_region_economy(input_rationing=ALL_OR_NOTHING)
        for economy in (proportional, cliff):
            economy.step(60)
            economy.destroy_capacity("Dust Basin", LEAVES, 0.90)
            economy.step(90)
        self.assertNotEqual(
            round(proportional.regions["Dust Basin"].inventory[YAYO], 6),
            round(cliff.regions["Dust Basin"].inventory[YAYO], 6),
        )
        for economy in (proportional, cliff):
            for residual in economy.commodity_balances().values():
                self.assertAlmostEqual(residual, 0.0, places=7)

    def test_shared_input_is_rationed_pro_rata_between_producers(self):
        """The fork: two producers, one scarce input, deterministic split."""
        chemfuel = Commodity(CHEMFUEL, 2.3, 0.4, target_inventory_days=20.0)
        widget = Commodity("widget", 10.0, 1.0, target_inventory_days=20.0)
        gadget = Commodity("gadget", 10.0, 1.0, target_inventory_days=20.0)
        processes = {
            "widget": Process("w", outputs={"widget": 1.0}, inputs={CHEMFUEL: 1.0}),
            "gadget": Process("g", outputs={"gadget": 1.0}, inputs={CHEMFUEL: 3.0}),
            CHEMFUEL: Process("c", outputs={CHEMFUEL: 1.0}),
        }
        from economy_lab.model import Economy, Region

        region = Region(
            "Solo",
            cash=1000.0,
            base_daily_demand={"widget": 1.0, "gadget": 1.0},
            # Only 2 of the 4 chemfuel wanted: every producer gets half.
            inventory={CHEMFUEL: 2.0, "widget": 0.0, "gadget": 0.0},
            prices={CHEMFUEL: 2.3, "widget": 10.0, "gadget": 10.0},
            producers=[
                Producer("w", "widget", 1.0, 1.0, process=processes["widget"]),
                Producer("g", "gadget", 1.0, 1.0, process=processes["gadget"]),
                Producer("c", CHEMFUEL, 0.0, 1.0, process=processes[CHEMFUEL]),
            ],
        )
        economy = Economy([chemfuel, widget, gadget], [region], [])
        economy.step(1)
        # Widget asked for 1 chemfuel, gadget for 3, and only 2 exist. Pro-rata
        # gives each producer half of what it asked, so each runs at half rate:
        # widget draws 0.5, gadget draws 1.5.
        self.assertAlmostEqual(economy.ledger.production["widget"], 0.5, places=9)
        self.assertAlmostEqual(economy.ledger.production["gadget"], 0.5, places=9)
        self.assertAlmostEqual(
            economy.ledger.intermediate_consumption[CHEMFUEL], 2.0, places=9
        )
        self.assertAlmostEqual(region.inventory[CHEMFUEL], 0.0, places=9)
        self.assertAlmostEqual(economy.commodity_balance(CHEMFUEL), 0.0, places=9)
        # The larger claim is rationed harder in absolute terms and identically
        # in relative terms; that is what makes the split order-independent.
        self.assertAlmostEqual(region.unmet_demand[CHEMFUEL], 2.0, places=9)

    def test_scarcity_of_an_input_registers_as_price_signal_not_false_chemfuel_shortage(self):
        economy = input_shortage()
        # Destroying psychoid fields causes leaf scarcity. The cost channel
        # may pre-empt the material channel (the drug lab curtails on cost
        # before running out of leaves), but either way the chemfuel market
        # must not register a false shortage: only leaves were attacked.
        unmet_chemfuel = max(
            h["regions"]["Dust Basin"]["unmet"][CHEMFUEL] for h in economy.history
        )
        self.assertAlmostEqual(unmet_chemfuel, 0.0, places=9)
        # The leaf price must rise significantly — the signal propagates
        # whether through material rationing or cost-driven curtailment.
        leaf_prices = economy.series("Dust Basin", LEAVES)
        self.assertGreater(max(leaf_prices[61:]), 1.9 * 2.0)


class CostFloorTests(unittest.TestCase):
    """The cost floor: input prices drive the utilization curve."""

    def test_effective_cost_includes_input_prices(self):
        """A producer's effective cost rises when its input price rises."""
        processes = circuit_processes()
        p = Producer(
            "lab", YAYO, 10.0, 0.0,
            process=processes[YAYO],
        )
        ref_prices = {YAYO: 21.0, LEAVES: 1.9, CHEMFUEL: 2.3}
        high_prices = {YAYO: 21.0, LEAVES: 5.0, CHEMFUEL: 2.3}
        self.assertGreater(
            p.effective_unit_cost(high_prices),
            p.effective_unit_cost(ref_prices),
        )

    def test_cost_floor_curtails_before_material_runs_out(self):
        """When input prices rise, utilization drops even with ample stock."""
        processes = circuit_processes()
        p = Producer(
            "lab", YAYO, 10.0, 0.0,
            process=processes[YAYO],
        )
        ref_prices = {YAYO: 21.0, LEAVES: 1.9, CHEMFUEL: 2.3}
        # Leaf price 3.0 gives effective_cost ~24.46, ratio ~0.86 — partial.
        squeezed = {YAYO: 21.0, LEAVES: 3.0, CHEMFUEL: 2.3}
        full = p.utilization(21.0, ref_prices)
        curtailed = p.utilization(21.0, squeezed)
        self.assertAlmostEqual(full, 1.0, places=6)
        self.assertLess(curtailed, full)
        self.assertGreater(curtailed, 0.0)

    def test_silver_balances_with_cost_floor(self):
        for economy in (equilibrium(), regional_glut(), producer_loss(),
                        arbitrage(), input_shortage()):
            with self.subTest(day=economy.day):
                self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)

    def test_investment_consumes_silver(self):
        """Capacity investment draws from the regional cash pool."""
        economy = producer_loss()
        # Producer-loss triggers investment; silver must have been spent.
        self.assertGreater(economy.ledger.investment_spending, 0.0)
        # And the books still close.
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)

    def test_buffer_deficit_triggers_investment_and_resolves(self):
        """The post-shock buffer scar resolves rather than persisting."""
        economy = producer_loss(days_after_loss=600)
        local = economy.regions["Dust Basin"]
        # Upstream prices should converge to reference, not a displaced value.
        self.assertAlmostEqual(local.prices[LEAVES], 1.9, places=4)
        self.assertAlmostEqual(local.prices[CHEMFUEL], 2.3, places=4)
        # Stock should be at the (potentially new) target, not below it.
        for name in (LEAVES, CHEMFUEL):
            target = (
                local.throughput_demand(name)
                * economy.commodities[name].target_inventory_days
            )
            self.assertAlmostEqual(
                local.inventory[name], target, places=2,
                msg=f"{name} stock should match its target",
            )


class ResourceReserveTests(unittest.TestCase):
    """Finite reserves, grade depletion, marginal cost, and differential rent."""

    def test_reserve_depletes_and_tracks_in_ledger(self):
        """Extraction draws from the reserve; depletion equals production."""
        economy = equilibrium(days=120)
        depletion = economy.ledger.reserve_depletion.get(CHEMFUEL, 0.0)
        production = economy.ledger.production.get(CHEMFUEL, 0.0)
        self.assertGreater(depletion, 0.0)
        self.assertAlmostEqual(depletion, production, places=7)

    def test_grade_transition_raises_marginal_cost(self):
        """When the cheap grade exhausts, marginal cost jumps to the next."""
        economy = reserve_depletion(days=200)
        dust = economy.regions["Dust Basin"]
        reserve = dust.reserves[CHEMFUEL]
        # Grade 0 should be exhausted, grade 1 active.
        self.assertAlmostEqual(reserve.grades[0].quantity, 0.0, places=6)
        self.assertGreater(reserve.grades[1].quantity, 0.0)
        # Marginal cost is grade 1's cost (2× the original).
        self.assertGreater(
            reserve.marginal_cost(),
            reserve.grades[1].extraction_cost - 1e-6,
        )

    def test_grade_transition_raises_chemfuel_price(self):
        """Depletion of the cheap grade raises the market price."""
        economy = reserve_depletion(days=200)
        dust = economy.regions["Dust Basin"]
        chemfuel_ref = economy.commodities[CHEMFUEL].reference_price
        # Chemfuel price must be above the original reference.
        self.assertGreater(dust.prices[CHEMFUEL], chemfuel_ref * 1.3)

    def test_differential_rent_appears_after_grade_divergence(self):
        """Green River earns rent when Dust Basin moves to an expensive grade."""
        economy = reserve_depletion(days=200)
        rent = economy.ledger.differential_rent.get(CHEMFUEL, 0.0)
        # Before day 100, rent is minimal (small cost diff between regions).
        # After day 100, the cost gap widens to ~1.48/unit and rent grows.
        self.assertGreater(rent, 100.0)

    def test_depletion_scenario_closes_all_ledgers(self):
        """Material and silver balance after grade transition."""
        economy = reserve_depletion(days=300)
        for name, residual in economy.commodity_balances().items():
            with self.subTest(commodity=name):
                self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)

    def test_reserve_limits_production_when_exhausted(self):
        """A fully exhausted reserve stops extraction entirely."""
        reserve = ResourceReserve(
            CHEMFUEL, [ResourceGrade(10.0, 1.0)]
        )
        taken = reserve.extract(10.0)
        self.assertAlmostEqual(taken, 10.0, places=9)
        self.assertAlmostEqual(reserve.remaining, 0.0, places=9)
        # Marginal cost is infinite when exhausted.
        self.assertEqual(reserve.marginal_cost(), float("inf"))
        # Further extraction yields nothing.
        taken2 = reserve.extract(5.0)
        self.assertAlmostEqual(taken2, 0.0, places=9)

    def test_extract_spans_grades(self):
        """Extraction that crosses a grade boundary draws from both."""
        reserve = ResourceReserve(
            CHEMFUEL,
            [ResourceGrade(3.0, 1.0), ResourceGrade(100.0, 2.0)],
        )
        taken = reserve.extract(5.0)
        self.assertAlmostEqual(taken, 5.0, places=9)
        self.assertAlmostEqual(reserve.grades[0].quantity, 0.0, places=9)
        self.assertAlmostEqual(reserve.grades[1].quantity, 98.0, places=9)
        self.assertAlmostEqual(reserve.marginal_cost(), 2.0, places=9)

    def test_existing_scenarios_unaffected_by_large_reserves(self):
        """The 100,000-unit default reserve must not change any existing metric."""
        for economy in (equilibrium(), regional_glut(), producer_loss(),
                        arbitrage(), input_shortage()):
            with self.subTest(day=economy.day):
                for name, residual in economy.commodity_balances().items():
                    self.assertAlmostEqual(residual, 0.0, places=7)
                self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)
                # Reserve remaining should be large (barely touched).
                for region in economy.regions.values():
                    for cname, reserve in region.reserves.items():
                        self.assertGreater(reserve.remaining, 90_000)


class LaborPowerTests(unittest.TestCase):
    """The wage relation: labor-power, the subsistence basket, and surplus.

    Labor value, market price, surplus value, and rent stay distinct; money
    profit is not surplus value.  The wage circuit is the first place silver
    cycles rather than flows one way, so leaks are asserted against hard.
    """

    def test_equilibrium_is_exactly_stationary_with_wages(self):
        """Four commodities, both regions, four years, price range exactly 0."""
        economy = equilibrium(days=4 * DAYS_PER_YEAR)
        for rname in economy.regions:
            for cname in economy.commodities:
                series = economy.series(rname, cname)
                self.assertEqual(
                    max(series) - min(series),
                    0.0,
                    f"{rname}/{cname} price moved at equilibrium",
                )

    def test_wage_circuit_closes_the_silver_ledger(self):
        """producer -> wage -> worker -> basket purchase -> producer revenue."""
        for economy in (equilibrium(days=240), subsistence_shock()):
            with self.subTest(day=economy.day):
                self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)
                for name, residual in economy.commodity_balances().items():
                    self.assertAlmostEqual(residual, 0.0, places=7)

    def test_wages_flow_to_workers_and_return_through_the_basket(self):
        economy = equilibrium(days=240)
        for rname, region in economy.regions.items():
            paid = economy.ledger.wages_paid.get(rname, 0.0)
            spent = economy.ledger.worker_spending.get(rname, 0.0)
            self.assertGreater(paid, 0.0)
            # At equilibrium workers spend exactly what they earn (the seeded
            # day-zero basket demand equals the daily wage), so the worker
            # cash pool ends where it started.
            self.assertAlmostEqual(paid, spent, places=6)
            parameters = ScenarioParameters()
            self.assertAlmostEqual(
                region.worker_cash,
                parameters.worker_initial_cash_days * parameters.basket_cost(),
                places=9,
            )

    def test_workers_consume_real_meals(self):
        economy = equilibrium(days=120)
        consumed = economy.ledger.consumption.get(MEALS, 0.0)
        produced = economy.ledger.production.get(MEALS, 0.0)
        self.assertGreater(consumed, 0.0)
        self.assertAlmostEqual(consumed, produced, places=6)

    def test_rate_of_surplus_value_matches_the_closed_form(self):
        """s/v = (working day - basket labor) / basket labor, per docs/17.

        Since docs/23 the basket's labor content is the *endogenous* value
        of each good, which includes the fixed capital consumed making it,
        so the closed form reads that rather than the raw direct-labor
        figure.  Since docs/28 it reads all three basket goods.
        """
        parameters = ScenarioParameters()
        economy = equilibrium(days=240)
        basket_ticks = sum(
            quantity * economy.labor_values[name]
            for name, quantity in sorted(
                parameters.subsistence_basket.items()
            )
        )
        self.assertAlmostEqual(
            basket_ticks,
            economy.basket_labor_value(economy.regions["Dust Basin"]),
            places=9,
        )
        expected = (
            parameters.ticks_per_worker_day - basket_ticks
        ) / basket_ticks
        for rname in economy.regions:
            actual = economy.rate_of_surplus_value(rname)
            self.assertIsNotNone(actual)
            self.assertAlmostEqual(actual, expected, delta=expected * 1e-3)

    def test_surplus_ledger_identity_holds(self):
        economy = equilibrium(days=240)
        for rname in economy.regions:
            living = economy.ledger.living_labor[rname]
            necessary = economy.ledger.necessary_labor[rname]
            surplus = economy.ledger.surplus_labor(rname)
            self.assertGreater(necessary, 0.0)
            self.assertGreater(surplus, 0.0)
            self.assertAlmostEqual(living, necessary + surplus, places=6)

    def test_labor_pool_rations_production_pro_rata(self):
        """A binding pool scales every producer, proportionally, not to zero."""
        constrained = equilibrium(
            days=60,
            parameters=ScenarioParameters(labor_pool_worker_days=0.125),
        )
        free = equilibrium(days=60)
        for rname, region in constrained.regions.items():
            self.assertLessEqual(region.worker_days_earned, 0.125 + 1e-9)
            # Compare the seeded producers; the constrained run may also
            # contain investment entrants responding to the shortage.
            for unconstrained in free.regions[rname].producers:
                producer = next(
                    p for p in region.producers if p.name == unconstrained.name
                )
                self.assertGreater(producer.output_total, 0.0)
                self.assertLess(producer.output_total, unconstrained.output_total)
        for name, residual in constrained.commodity_balances().items():
            self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertAlmostEqual(constrained.cash_balance(), 0.0, places=7)

    def test_subsistence_shock_raises_meal_price_and_the_wage(self):
        """The wage-push channel: meal scarcity raises every producer's cost.

        Read at the peak rather than at the terminal day.  With the
        enlarged basket (docs/28) the meal buffer is larger, so the run has
        recovered further by day 240 — but the shock itself is deeper, not
        shallower, and the peak is where the claim lives.
        """
        parameters = ScenarioParameters()
        economy = subsistence_shock()
        dust = economy.regions["Dust Basin"]
        meal_prices = economy.series("Dust Basin", MEALS)
        self.assertGreater(max(meal_prices), 15.0 * 1.15)
        wages = [
            sum(
                quantity * snapshot["regions"]["Dust Basin"]["price"][name]
                for name, quantity in sorted(
                    parameters.subsistence_basket.items()
                )
            )
            for snapshot in economy.history
        ]
        self.assertGreater(max(wages), parameters.basket_cost() * 1.15)
        # The wage push reaches the *other* wage goods, which only became
        # observable when the basket grew past one commodity.
        self.assertGreater(
            max(economy.series("Dust Basin", GARMENTS)),
            parameters.garment_reference_price,
        )
        lab = next(p for p in dust.producers if p.commodity == YAYO)
        self.assertGreater(
            lab.wage_cost_per_unit,
            350.0 * (parameters.basket_cost() / 24000.0),
        )
        # Workers who could not obtain the basket are visible, both as a
        # ledger shortfall and as unmet demand at some point in the history.
        self.assertGreater(
            economy.ledger.basket_shortfall.get("Dust Basin", 0.0), 0.0
        )
        shocked_days = [
            snapshot["regions"]["Dust Basin"]["unmet"][MEALS]
            for snapshot in economy.history
        ]
        self.assertGreater(max(shocked_days), 0.0)
        # The distant region's meal market stays quiet: the spread never
        # covers freight in this calibration.
        self.assertEqual(
            economy.regions["Green River"].imported_total[MEALS], 0.0
        )

    def test_subsistence_shock_is_reproducible(self):
        first = subsistence_shock()
        second = subsistence_shock()
        self.assertEqual(first.history, second.history)

    def test_unpayable_wage_bill_refuses_loudly(self):
        economy = equilibrium(days=1)
        economy.regions["Dust Basin"].cash = 0.0
        with self.assertRaises(RuntimeError):
            economy.step(1)

    def test_wage_that_breaks_full_utilization_refuses_loudly(self):
        """A basket so dear the drug lab cannot run at reference must raise."""
        with self.assertRaises(ValueError):
            equilibrium(
                days=1,
                parameters=ScenarioParameters(meal_reference_price=150.0),
            )

    def test_undersized_provisioning_capacity_refuses_loudly(self):
        with self.assertRaises(ValueError):
            equilibrium(
                days=1,
                parameters=ScenarioParameters(meal_capacity_per_day=0.5),
            )

    def test_bare_regions_without_a_basket_pay_no_wages(self):
        """The wage machinery must be inert when no basket is configured."""
        chemfuel = Commodity(CHEMFUEL, 2.3, 0.4)
        processes = circuit_processes()
        from economy_lab.model import Economy, Region

        region = Region(
            "Plain",
            cash=1000.0,
            base_daily_demand={CHEMFUEL: 1.0},
            inventory={CHEMFUEL: 30.0},
            prices={CHEMFUEL: 2.3},
            producers=[
                Producer("plain refinery", CHEMFUEL, 2.0, 1.5,
                         process=processes[CHEMFUEL]),
            ],
        )
        economy = Economy([chemfuel], [region], [])
        economy.step(30)
        self.assertEqual(economy.ledger.wages_paid, {})
        self.assertEqual(region.worker_cash, 0.0)
        self.assertEqual(region.cash, 1000.0)
        self.assertIsNone(economy.rate_of_surplus_value())


class EndogenousLaborValueTests(unittest.TestCase):
    """The process graph produces values instead of importing them.

    The validation that matters is against `FINDINGS.md`: the closed
    analysis solved 653 defs from extraction outward without reference to
    price, and this circuit uses the same ratios and direct-labor figures.
    A correct solve must reproduce it exactly, except for the one link
    docs/08 flagged as stylized, which must account for the whole of any
    discrepancy.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = equilibrium(240)

    def _capital_labor(self, commodity):
        """Fixed capital labor transferred per unit (docs/23)."""
        process = circuit_processes()[commodity]
        _, labor = process.capital_consumed_per_unit(
            commodity,
            self.economy.capital_service_life_days,
            self.economy.commodities,
        )
        return labor

    def test_input_free_commodities_exceed_the_closed_analysis_by_capital(self):
        # Chemfuel and meals have no modelled inputs, so their value is
        # their direct labor plus the labor embodied in the plant that
        # makes them. RimWorld's own formula transfers nothing from fixed
        # capital (FINDINGS.md), so the model must now differ from the
        # closed analysis by exactly that transfer and nothing else.
        parameters = ScenarioParameters()
        self.assertAlmostEqual(
            self.economy.labor_values[CHEMFUEL],
            parameters.chemfuel_direct_labor + self._capital_labor(CHEMFUEL),
            places=10,
        )
        self.assertAlmostEqual(
            self.economy.labor_values[MEALS],
            parameters.meal_direct_labor + self._capital_labor(MEALS),
            places=10,
        )

    def test_the_fixed_capital_transfer_is_a_negligible_share_of_value(self):
        # The measured answer to "is the vanilla omission serious?" — no.
        # RimWorld's buildings are cheap relative to their lifetime output.
        for commodity in (CHEMFUEL, MEALS, LEAVES, YAYO):
            share = (
                self._capital_labor(commodity)
                / self.economy.labor_values[commodity]
            )
            self.assertLess(share, 0.005)

    def test_downstream_values_differ_only_by_the_stylized_link(self):
        parameters = ScenarioParameters()
        # Vanilla RimWorld: leaves carry their own labor and nothing else;
        # yayo carries its own plus eight leaves.
        vanilla_leaves = parameters.leaves_direct_labor
        vanilla_yayo = (
            parameters.yayo_direct_labor
            + parameters.leaves_per_yayo * vanilla_leaves
        )
        # The lab knowingly adds chemfuel as an operating input in two
        # places (docs/08). That stylization, and only it, should explain
        # the gap from the closed analysis.
        stylized_leaves = parameters.chemfuel_per_leaf * 25.0
        stylized_yayo = (
            parameters.chemfuel_per_yayo * 25.0
            + parameters.leaves_per_yayo * stylized_leaves
        )
        # Since docs/23 there is a third, named term: the labor embodied
        # in each stage's plant, which vanilla transfers not at all.
        chemfuel_value = self.economy.labor_values[CHEMFUEL]
        leaves_capital = self._capital_labor(LEAVES)
        yayo_capital = self._capital_labor(YAYO)
        expected_leaves = (
            vanilla_leaves
            + parameters.chemfuel_per_leaf * chemfuel_value
            + leaves_capital
        )
        expected_yayo = (
            parameters.yayo_direct_labor
            + parameters.leaves_per_yayo * expected_leaves
            + parameters.chemfuel_per_yayo * chemfuel_value
            + yayo_capital
        )
        self.assertAlmostEqual(
            self.economy.labor_values[LEAVES], expected_leaves, places=10
        )
        self.assertAlmostEqual(
            self.economy.labor_values[YAYO], expected_yayo, places=10
        )
        # And the gap from vanilla stays small and fully accounted for.
        self.assertLess(
            abs(self.economy.labor_values[YAYO] - vanilla_yayo) / vanilla_yayo,
            0.03,
        )
        del stylized_leaves, stylized_yayo

    def test_value_is_transferred_labor_plus_living_labor(self):
        values = self.economy.labor_values
        process = circuit_processes()[YAYO]
        transferred = sum(
            quantity * values[name]
            for name, quantity in process.inputs.items()
        )
        # Constant capital now has two parts: circulating inputs, and the
        # fixed capital consumed making the product (docs/23).
        fixed = self._capital_labor(YAYO)
        self.assertAlmostEqual(
            values[YAYO],
            transferred + fixed + process.direct_labor,
            places=10,
        )

    def test_authored_figures_are_not_overwritten(self):
        # FINDINGS.md is closed analysis. The solve sits beside it.
        parameters = ScenarioParameters()
        self.assertEqual(
            self.economy.commodities[YAYO].labor_value, parameters.labor_value
        )
        self.assertNotAlmostEqual(
            self.economy.commodities[YAYO].labor_value,
            self.economy.labor_values[YAYO] * self.economy.labor_value_per_tick,
            places=3,
        )

    def test_values_are_stationary_and_reproducible_at_equilibrium(self):
        series = [h["labor_values"][YAYO] for h in self.economy.history]
        self.assertEqual(min(series), max(series))
        repeat = equilibrium(240)
        self.assertEqual(repeat.labor_values, self.economy.labor_values)

    def test_joint_products_split_value_by_mass(self):
        from economy_lab.model import Economy, Region

        heavy = Commodity(
            "heavy", reference_price=10.0, labor_value=1.0, mass_per_unit=3.0
        )
        light = Commodity(
            "light", reference_price=10.0, labor_value=1.0, mass_per_unit=1.0
        )
        joint = Process(
            "joint", outputs={"heavy": 1.0, "light": 1.0}, direct_labor=80.0
        )
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"heavy": 1.0, "light": 1.0},
            inventory={"heavy": 30.0, "light": 30.0},
            prices={"heavy": 10.0, "light": 10.0},
            producers=[
                Producer("both", "heavy", 2.0, 1.0, process=joint),
            ],
        )
        economy = Economy([heavy, light], [region], [])
        economy.step(5)
        # Mass shares are 3:1, so the 80 ticks split 60/20.
        self.assertAlmostEqual(economy.labor_values["heavy"], 60.0, places=9)
        self.assertAlmostEqual(economy.labor_values["light"], 20.0, places=9)
        self.assertAlmostEqual(
            economy.labor_values["heavy"] + economy.labor_values["light"],
            joint.direct_labor,
            places=9,
        )

    def test_a_non_productive_system_refuses_rather_than_returning(self):
        from economy_lab.model import Economy, Region

        # A commodity that eats more of itself than it makes has no finite
        # value. The solve must say so instead of returning a number.
        widget = Commodity("widget", reference_price=10.0, labor_value=1.0)
        devouring = Process(
            "devouring",
            outputs={"widget": 1.0},
            inputs={"widget": 1.5},
            direct_labor=10.0,
        )
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"widget": 1.0},
            inventory={"widget": 500.0},
            prices={"widget": 10.0},
            producers=[
                Producer("mill", "widget", 4.0, 1.0, process=devouring),
            ],
        )
        with self.assertRaises(RuntimeError) as raised:
            Economy([widget], [region], [])
        self.assertIn("not productive", str(raised.exception))

    def test_a_self_consuming_but_productive_system_still_solves(self):
        from economy_lab.model import Economy, Region

        # The same cycle, but productive: 0.5 widget in, 1 out. A
        # topological pass has no answer here at all; the iteration does.
        widget = Commodity("widget", reference_price=10.0, labor_value=1.0)
        cyclic = Process(
            "cyclic",
            outputs={"widget": 1.0},
            inputs={"widget": 0.5},
            direct_labor=10.0,
        )
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"widget": 1.0},
            inventory={"widget": 500.0},
            prices={"widget": 10.0},
            producers=[
                Producer("mill", "widget", 4.0, 1.0, process=cyclic),
            ],
        )
        economy = Economy([widget], [region], [])
        # v = 0.5v + 10  =>  v = 20
        self.assertAlmostEqual(economy.labor_values["widget"], 20.0, places=6)

    def test_zero_output_holds_the_last_value_instead_of_dropping_it(self):
        # The glut idles the drug lab completely. Value describes conditions
        # of production, which do not evaporate because nobody produced, so
        # the yayo value must hold rather than vanish or jump.
        economy = regional_glut(120)
        idled = [
            snapshot["day"]
            for snapshot in economy.history
            if snapshot["day"] > 60
            and "yayo" not in snapshot["regional_labor_values"].get(
                "Dust Basin", {}
            )
        ]
        self.assertTrue(idled, "expected the glut to idle the drug lab")
        series = [h["labor_values"][YAYO] for h in economy.history]
        # Not bit-exact, deliberately: the value is an aggregate ratio, and
        # (r1*A + r2*A) / (r1*B + r2*B) does not round to exactly A/B when
        # producers run at differing levels. The claim under test is that
        # the value holds rather than collapsing or jumping when output
        # stops, so the tolerance is tight but not zero.
        self.assertLess(max(series) - min(series), 1e-9)
        self.assertAlmostEqual(
            min(series), economy.labor_values[YAYO], places=9
        )


class RelativeSurplusValueTests(unittest.TestCase):
    """A productivity gain in the wage-goods sector, and what follows.

    The working day and the basket are fixed throughout, so any movement in
    the rate of surplus value is relative surplus value: surplus rises
    because the goods that reproduce labor got cheaper, not because the day
    got longer or the basket got smaller.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = technique_change(180)
        cls.before = equilibrium(240)

    def test_the_working_day_and_the_basket_are_untouched(self):
        parameters = ScenarioParameters()
        for region in self.economy.regions.values():
            self.assertEqual(
                region.ticks_per_worker_day, parameters.ticks_per_worker_day
            )
            self.assertEqual(
                region.subsistence_basket[MEALS],
                parameters.meals_per_worker_day,
            )

    def test_the_social_value_of_the_wage_good_falls(self):
        self.assertGreater(self.before.labor_values[MEALS], 305.0)
        self.assertLess(self.economy.labor_values[MEALS], 280.0)
        self.assertGreater(self.economy.labor_values[MEALS], 228.75)

    def test_social_value_lies_between_the_individual_values(self):
        dust = self.economy.regional_labor_values["Dust Basin"][MEALS]
        river = self.economy.regional_labor_values["Green River"][MEALS]
        social = self.economy.labor_values[MEALS]
        # The adopter produces below social value, the laggard above it.
        self.assertLess(dust, social)
        self.assertLess(social, river)
        # The laggard runs only the old technique, so its individual value
        # is exactly the undisturbed equilibrium value of a meal.
        stable = equilibrium(240)
        self.assertAlmostEqual(river, stable.labor_values[MEALS], places=6)
        # The adopter's own value lies between the two techniques it runs
        # (152.5 and 305). Since docs/21 the order book tilts toward the
        # cheaper producer, so the mix is no longer the 228.75 midpoint —
        # it sits below it, and moves further as the cost gap widens.
        self.assertLess(152.5, dust)
        self.assertLess(dust, 228.75)

    def test_the_rate_of_surplus_value_rises_in_both_regions(self):
        base = self.before.rate_of_surplus_value()
        for name in self.economy.regions:
            self.assertGreater(self.economy.rate_of_surplus_value(name), base)

    def test_it_rises_where_nothing_was_adopted(self):
        # Green River adopts no new technique, yet the value of labor-power
        # it faces falls, because value is social.
        river_before = self.before.rate_of_surplus_value("Green River")
        river_after = self.economy.rate_of_surplus_value("Green River")
        self.assertGreater(river_after, river_before)

    def test_the_value_of_labor_power_falls_much_further_than_its_price(self):
        # Value and price are distinct quantities and must not be collapsed.
        # Since docs/21 the price *does* respond to cost, so the claim is no
        # longer that it stays put — it is that the two move by very
        # different amounts. Labor is only a few percent of money cost
        # (docs/21 section 1), so a labor-saving technique moves value by an
        # order of magnitude more than it moves price.
        region = self.economy.regions["Dust Basin"]
        before = self.before.regions["Dust Basin"]
        base_value = self.before.basket_labor_value(before)
        base_wage = before.wage_rate()
        value_fall = (
            base_value - self.economy.basket_labor_value(region)
        ) / base_value
        price_fall = (base_wage - region.wage_rate()) / base_wage
        # Diluted since docs/28: only the meals part of the basket is
        # cheapened by a provisioning technique, so the absolute fall is
        # smaller than under a meals-only basket. The claim under test is
        # the *ratio*, which is if anything sharper.
        self.assertGreater(value_fall, 0.05)
        self.assertGreater(price_fall, 0.0)
        self.assertLess(price_fall, 0.05)
        self.assertGreater(value_fall, 5.0 * price_fall)

    def test_the_scenario_closes_every_ledger(self):
        for residual in self.economy.commodity_balances().values():
            self.assertAlmostEqual(residual, 0.0, places=9)
        self.assertAlmostEqual(self.economy.cash_balance(), 0.0, places=9)

    def test_the_scenario_is_reproducible(self):
        repeat = technique_change(180)
        self.assertEqual(repeat.labor_values, self.economy.labor_values)
        self.assertEqual(
            repeat.rate_of_surplus_value(), self.economy.rate_of_surplus_value()
        )


class CompetitiveTransmissionTests(unittest.TestCase):
    """Cost reaches price, and the cheaper producer wins custom.

    Two mechanisms, deliberately measurable one at a time: the price
    anchor reads the sector's cost (`competitive_price_intensity`), and the
    order book is shared out by cost (`competitive_share_elasticity`).
    Each has a setting that reproduces the previous model exactly.
    """

    def test_zero_intensity_leaves_the_anchor_on_the_reference_price(self):
        # kappa = 0 is the pre-docs/21 model: the anchor is the authored
        # reference price and no cost change can reach it.
        parameters = replace(
            ScenarioParameters(), competitive_price_intensity=0.0
        )
        economy = reserve_depletion(300, parameters=parameters)
        region = economy.regions["Dust Basin"]
        producer = next(
            p for p in region.producers if p.commodity == CHEMFUEL
        )
        # Cost has doubled, and the price sits above it only because the
        # buffer is starved — the artifact docs/16 recorded.
        self.assertGreater(producer.effective_unit_cost(region.prices), 3.0)
        target = region.throughput_demand(CHEMFUEL) * 20.0
        self.assertLess(region.inventory[CHEMFUEL] / target, 0.70)

    def test_cost_aware_anchor_refills_the_starved_buffer(self):
        # With the anchor reading cost, the price rises because cost rose,
        # so the inventory no longer has to stay depleted to hold it up.
        economy = reserve_depletion(300)
        region = economy.regions["Dust Basin"]
        target = region.throughput_demand(CHEMFUEL) * 20.0
        self.assertAlmostEqual(region.inventory[CHEMFUEL] / target, 1.0, places=3)
        producer = next(
            p for p in region.producers if p.commodity == CHEMFUEL
        )
        # And the price still covers the higher cost.
        self.assertGreater(
            region.prices[CHEMFUEL],
            producer.effective_unit_cost(region.prices),
        )

    def test_upstream_cost_now_reaches_the_downstream_price(self):
        # docs/16 recorded exactly zero downstream movement when chemfuel
        # doubled: the anchor could not see cost at all. It can now.
        economy = reserve_depletion(300)
        local = economy.regions["Dust Basin"]
        distant = economy.regions["Green River"]
        self.assertGreater(local.prices[YAYO], 21.0)
        # Only the region whose deposits ran out is affected.
        self.assertAlmostEqual(distant.prices[YAYO], 21.0, places=6)

    def test_zero_elasticity_is_a_bit_exact_no_op(self):
        parameters = replace(
            ScenarioParameters(), competitive_share_elasticity=0.0
        )
        flat = producer_loss(150, parameters=parameters)
        weighted = producer_loss(150)
        # Every producer of a commodity currently shares a cost, so cost
        # weighting changes nothing at all here — and with the elasticity
        # off it must be identical to the bit regardless.
        self.assertEqual(
            [h["regions"]["Dust Basin"]["price"][YAYO] for h in flat.history],
            [h["regions"]["Dust Basin"]["price"][YAYO] for h in weighted.history],
        )

    def test_allocation_respects_each_producer_capacity_ceiling(self):
        economy = cost_competition(180)
        region = economy.regions["Dust Basin"]
        for producer in region.producers:
            ceiling = producer.process.runs_for(producer.capacity_per_day)
            self.assertLessEqual(producer.last_runs, ceiling + 1e-9)

    def test_equilibrium_is_still_exactly_stationary(self):
        economy = equilibrium(240)
        for name in economy.commodities:
            for region in economy.regions:
                series = economy.series(region, name)
                self.assertEqual(min(series), max(series))

    def test_prices_stay_within_the_clamps_in_every_scenario(self):
        # The anchor now depends on input prices, which are themselves
        # prices. The loop is damped (docs/21 section 2), but that is a
        # property to check rather than assert.
        for build in (
            equilibrium,
            regional_glut,
            producer_loss,
            reserve_depletion,
            subsistence_shock,
            technique_change,
            cost_competition,
        ):
            economy = build()
            for snapshot in economy.history:
                for region in snapshot["regions"].values():
                    for name, price in region["price"].items():
                        commodity = economy.commodities[name]
                        self.assertGreater(price, 0.0)
                        self.assertLessEqual(
                            price,
                            commodity.reference_price
                            * commodity.maximum_price_factor
                            + 1e-9,
                        )


class CostCompetitionTests(unittest.TestCase):
    """A cheaper producer enters and undercuts the incumbent.

    The entrant saves overhead, not labor, so the labor value of a meal
    does not move. That makes this the clean contrast to
    `technique_change`, where value moves and money barely does.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = cost_competition(180)
        cls.region = cls.economy.regions["Dust Basin"]

    def test_the_cheaper_producer_takes_the_larger_share(self):
        meals = sorted(
            (p for p in self.region.producers if p.commodity == MEALS),
            key=lambda p: p.effective_unit_cost(self.region.prices),
        )
        self.assertEqual(len(meals), 2)
        cheap, dear = meals
        self.assertLess(
            cheap.effective_unit_cost(self.region.prices),
            dear.effective_unit_cost(self.region.prices),
        )
        self.assertGreater(cheap.last_runs, dear.last_runs)
        share = cheap.last_runs / (cheap.last_runs + dear.last_runs)
        self.assertGreater(share, 0.5)

    def test_the_price_falls_with_the_sector_cost(self):
        self.assertLess(self.region.cost_ratio[MEALS], 1.0)
        self.assertLess(self.region.prices[MEALS], 15.0)

    def test_the_labor_value_of_the_wage_good_does_not_move(self):
        # No technique changed how much labor a meal takes, so the value
        # must sit exactly where the undisturbed equilibrium leaves it.
        stable = equilibrium(240)
        self.assertEqual(
            self.economy.labor_values[MEALS], stable.labor_values[MEALS]
        )

    def test_money_wages_fall_while_the_value_of_labor_power_does_not(self):
        # The distinction the four ledgers exist to keep: the money form
        # of variable capital falls, its value does not.
        stable = equilibrium(240)
        self.assertLess(
            self.region.wage_rate(),
            stable.regions["Dust Basin"].wage_rate(),
        )
        self.assertAlmostEqual(
            self.economy.basket_labor_value(self.region),
            stable.basket_labor_value(stable.regions["Dust Basin"]),
            places=6,
        )

    def test_the_rate_of_surplus_value_is_unchanged(self):
        # Cheapening a wage good by saving *overhead* does not cheapen
        # labor-power in value terms, so s/v must not move. Contrast
        # technique_change, where saving labor does move it.
        stable = equilibrium(240)
        self.assertAlmostEqual(
            self.economy.rate_of_surplus_value(),
            stable.rate_of_surplus_value(),
            places=4,
        )

    def test_value_and_price_respond_to_different_things(self):
        # The headline contrast, asserted directly.
        labor_saving = technique_change(180)
        capital_saving = self.economy

        value_move_labor = (
            abs(labor_saving.labor_values[MEALS] - 305.0) / 305.0
        )
        price_move_labor = abs(
            labor_saving.regions["Dust Basin"].prices[MEALS] - 15.0
        ) / 15.0
        stable = equilibrium(240)
        base_meal_value = stable.labor_values[MEALS]
        value_move_capital = (
            abs(capital_saving.labor_values[MEALS] - base_meal_value)
            / base_meal_value
        )
        price_move_capital = abs(self.region.prices[MEALS] - 15.0) / 15.0

        # Labor-saving: value moves a lot, price barely.
        self.assertGreater(value_move_labor, 10.0 * price_move_labor)
        # Capital-saving: price moves, value not at all.
        self.assertEqual(value_move_capital, 0.0)
        self.assertGreater(price_move_capital, 0.05)

    def test_the_scenario_closes_every_ledger(self):
        for residual in self.economy.commodity_balances().values():
            self.assertAlmostEqual(residual, 0.0, places=9)
        self.assertAlmostEqual(self.economy.cash_balance(), 0.0, places=9)

    def test_the_scenario_is_reproducible(self):
        repeat = cost_competition(180)
        self.assertEqual(
            repeat.regions["Dust Basin"].prices[MEALS],
            self.region.prices[MEALS],
        )


class ValueLedgerTests(unittest.TestCase):
    """c, v, s in work-ticks, and what the price cannot account for.

    The classical magnitudes the project has been assembling toward. All
    in labor time: the value rate of profit is not money profitability and
    the two are never combined.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = equilibrium(240)
        cls.region = "Dust Basin"

    def test_the_value_ledger_closes_to_floating_point_zero(self):
        # A third closing ledger beside material and silver: the value of
        # everything produced equals what was transferred into it plus the
        # living labor added. Three independently accumulated paths.
        for economy in (
            self.economy,
            regional_glut(),
            producer_loss(),
            input_shortage(),
            cost_competition(),
        ):
            with self.subTest(day=economy.day):
                produced = sum(
                    economy.ledger.value_produced.get(name, 0.0)
                    for name in economy.regions
                )
                self.assertGreater(produced, 0.0)
                self.assertLess(
                    abs(economy.value_balance()) / produced, 1e-12
                )

    def test_a_moving_technique_mix_leaves_a_small_transient_residual(self):
        """The identity closes exactly only while the technique mix holds.

        Values are solved from the *previous* day's output weights
        (docs/19), so on days when the mix is shifting, output valued at
        the social value does not quite equal the individual costs behind
        it. The gap is a transient of the one-day lag, not a leak: it is
        bounded and it does not accumulate.
        """
        economy = technique_change()
        produced = sum(
            economy.ledger.value_produced.get(name, 0.0)
            for name in economy.regions
        )
        relative = abs(economy.value_balance()) / produced
        self.assertLess(relative, 1e-4)
        self.assertGreater(relative, 0.0)

    def test_constant_capital_splits_into_circulating_and_fixed(self):
        ledger = self.economy.ledger
        for name in self.economy.regions:
            self.assertAlmostEqual(
                ledger.constant_capital(name),
                ledger.circulating_capital[name]
                + ledger.fixed_capital_consumed[name],
                places=6,
            )

    def test_fixed_capital_is_a_negligible_part_of_constant_capital(self):
        # The measured answer to whether vanilla's omission matters.
        ledger = self.economy.ledger
        for name in self.economy.regions:
            share = ledger.fixed_capital_consumed[name] / ledger.constant_capital(
                name
            )
            self.assertGreater(share, 0.0)
            self.assertLess(share, 0.005)

    def test_the_classical_ratios_are_defined_and_consistent(self):
        economy = self.economy
        ledger = economy.ledger
        for name in economy.regions:
            c = ledger.constant_capital(name)
            v = ledger.necessary_labor[name]
            s = ledger.surplus_labor(name)
            self.assertAlmostEqual(
                economy.organic_composition(name), c / v, places=9
            )
            self.assertAlmostEqual(
                economy.value_rate_of_profit(name), s / (c + v), places=9
            )
            self.assertAlmostEqual(
                economy.rate_of_surplus_value(name), s / v, places=9
            )

    def test_a_bare_model_has_no_value_ledger_to_report(self):
        from economy_lab.model import Economy, Region

        processes = circuit_processes()
        chemfuel = Commodity(CHEMFUEL, reference_price=2.3, labor_value=0.4)
        region = Region(
            "Plain",
            cash=1000.0,
            base_daily_demand={CHEMFUEL: 1.0},
            inventory={CHEMFUEL: 30.0},
            prices={CHEMFUEL: 2.3},
            producers=[
                Producer("plain refinery", CHEMFUEL, 2.0, 1.5,
                         process=processes[CHEMFUEL]),
            ],
        )
        economy = Economy([chemfuel], [region], [])
        economy.step(30)
        self.assertIsNone(economy.organic_composition())
        self.assertIsNone(economy.value_rate_of_profit())


class PriceDecompositionTests(unittest.TestCase):
    """What a unit's price is made of, and what the model cannot explain.

    The wedge between RimWorld's authored price level and inputs plus
    wages plus capital consumption is reported under its own name. The
    laboratory cannot tell whether it is surplus or a cost it does not
    represent, so surplus is reported as a band and never as a number.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = equilibrium(240)
        cls.region = "Dust Basin"

    def decomposition(self, commodity):
        return self.economy.price_decomposition(self.region, commodity)

    def test_the_parts_add_up_to_the_price(self):
        for commodity in (CHEMFUEL, LEAVES, MEALS, YAYO):
            with self.subTest(commodity=commodity):
                d = self.decomposition(commodity)
                self.assertAlmostEqual(
                    d["attributable_cost"],
                    d["inputs"] + d["wages"] + d["capital_consumed"],
                    places=9,
                )
                self.assertAlmostEqual(
                    d["price"],
                    d["attributable_cost"] + d["margin"] + d["surplus_if_margin_is_cost"],
                    places=9,
                )

    def test_the_surplus_band_brackets_rather_than_asserts(self):
        for commodity in (CHEMFUEL, LEAVES, MEALS, YAYO):
            with self.subTest(commodity=commodity):
                d = self.decomposition(commodity)
                # The two readings differ by exactly the wedge, signed.
                # They are deliberately not ordered: a negative wedge means
                # the authored price does not cover attributable cost, and
                # treating it as surplus then gives the smaller figure.
                self.assertAlmostEqual(
                    d["surplus_if_margin_is_surplus"]
                    - d["surplus_if_margin_is_cost"],
                    d["margin"],
                    places=9,
                )

    def test_the_wedge_dominates_the_input_free_sectors(self):
        # The finding that motivated docs/23: for goods the model builds
        # from labor alone, most of RimWorld's authored price is neither
        # inputs, nor wages, nor capital consumption.
        for commodity in (CHEMFUEL, MEALS):
            with self.subTest(commodity=commodity):
                d = self.decomposition(commodity)
                self.assertGreater(d["margin"] / d["price"], 0.55)

    def test_wages_are_a_small_share_of_money_cost(self):
        # Why labor-saving change moves price so little (docs/22).
        for commodity in (CHEMFUEL, LEAVES, MEALS, YAYO):
            with self.subTest(commodity=commodity):
                d = self.decomposition(commodity)
                self.assertLess(d["wages"] / d["price"], 0.05)

    def test_capital_consumption_is_smaller_still(self):
        for commodity in (CHEMFUEL, LEAVES, MEALS, YAYO):
            with self.subTest(commodity=commodity):
                d = self.decomposition(commodity)
                self.assertLess(d["capital_consumed"], d["wages"])

    def test_a_negative_wedge_is_reported_not_clamped(self):
        # RimWorld's yayo price does not quite cover inputs, wages and
        # capital consumption at reference. That is a finding about the
        # authored price, so it must survive into the report.
        d = self.decomposition(YAYO)
        self.assertLess(d["margin"], 0.0)
        self.assertGreater(d["attributable_cost"], 16.0)

    def test_realized_and_produced_surplus_differ_by_sector(self):
        # Money s/v against the uniform labor-time s/v: a sector buying
        # inputs whose prices contain surplus realizes less than it made.
        labor_rate = self.economy.rate_of_surplus_value(self.region)
        yayo = self.decomposition(YAYO)
        yayo_money_rate = yayo["surplus_if_margin_is_surplus"] / yayo["wages"]
        self.assertLess(yayo_money_rate, labor_rate / 2.0)

    def test_the_wage_goods_money_rate_is_no_longer_an_identity(self):
        """docs/24's caveat, dissolved by docs/28.

        Under a meals-only basket the money and labor rates of surplus
        value agreed for meals *by construction* — both were the same
        expression in the same wage and the same basket — so the agreement
        was evidence of nothing. With three goods in the basket that
        derivation no longer closes, and the three wage goods disagree with
        the labor rate in both directions.
        """
        labor_rate = self.economy.rate_of_surplus_value(self.region)
        rates = {}
        for commodity in (MEALS, GARMENTS, MEDICINE):
            parts = self.decomposition(commodity)
            rates[commodity] = (
                parts["surplus_if_margin_is_surplus"] / parts["wages"]
            )
        self.assertGreater(rates[GARMENTS], labor_rate)
        self.assertLess(rates[MEDICINE], labor_rate)
        # Meals no longer land on the labor rate exactly, and the residual
        # gap is a real (small) difference rather than a tautology.
        self.assertNotAlmostEqual(rates[MEALS], labor_rate, places=6)
        self.assertAlmostEqual(rates[MEALS], labor_rate, delta=0.6)


class PriceOfProductionTests(unittest.TestCase):
    """The classical price system, computed but deliberately not adopted.

    Prices of production come from the technique and the real wage alone,
    with no authored price anywhere in the derivation. The profit rate is
    therefore an outcome, and — this being the point of the exercise —
    Sraffa's basics/non-basics structure decides which sector's technique
    can move it.
    """

    @classmethod
    def setUpClass(cls):
        cls.economy = equilibrium(240)
        cls.system = cls.economy.prices_of_production(numeraire=MEALS)
        cls.parameters = ScenarioParameters()

    def relative(self, commodity):
        prices = self.system["prices"]
        return prices[commodity] / prices[MEALS]

    def test_the_basics_are_the_wage_goods_and_what_feeds_them(self):
        """Sraffa's basics, after the basket grew (docs/28).

        Every wage good is basic because every sector employs labor. What
        changed is chemfuel: the tailors' bench is powered, so chemfuel now
        enters a wage good, and through it every sector. Psychoid leaves
        and yayo still enter nothing that enters everything.
        """
        self.assertEqual(
            self.system["basics"], [CHEMFUEL, GARMENTS, MEDICINE, MEALS]
        )
        self.assertNotIn(LEAVES, self.system["basics"])
        self.assertNotIn(YAYO, self.system["basics"])

    def rank_one_gross_markup(self, economy):
        """`T / Σ(b·l) − 1`: the markup if no wage good had material inputs.

        With pure-labor wage goods the augmented matrix restricted to the
        basket is the outer product `(l/T)·bᵀ`, whose only non-zero
        eigenvalue is `Σ b·l / T`. That rank-one structure is why `r` was
        exactly the rate of surplus value however many wage goods there
        were.
        """
        _, labor, _ = economy.social_technique()
        basket = economy.regions["Dust Basin"].subsistence_basket
        embodied = sum(
            quantity * labor[name] for name, quantity in sorted(basket.items())
        )
        return self.parameters.ticks_per_worker_day / embodied - 1.0

    def test_a_material_input_to_a_wage_good_breaks_the_rank_one_identity(self):
        """The general Sraffa case, reached for the first time (docs/28).

        One material input into one wage good is enough. The price system
        marks that input up by `1 + r` and the value system does not, so
        the profit rate falls below the rank-one figure — by 8%, not by a
        rounding error.
        """
        rank_one = self.rank_one_gross_markup(self.economy)
        self.assertAlmostEqual(rank_one, 26.826086956521738, places=9)
        self.assertLess(self.system["gross_markup"], rank_one)
        gap = (rank_one - self.system["gross_markup"]) / rank_one
        self.assertGreater(gap, 0.07)
        self.assertLess(gap, 0.09)

    def test_removing_that_input_restores_the_identity_exactly(self):
        """The control: the break is the chemfuel link and nothing else."""
        control = equilibrium(
            240,
            parameters=replace(ScenarioParameters(), chemfuel_per_garment=0.0),
        )
        system = control.prices_of_production(numeraire=MEALS)
        self.assertNotIn(CHEMFUEL, system["basics"])
        self.assertAlmostEqual(
            system["gross_markup"],
            self.rank_one_gross_markup(control),
            places=9,
        )
        # And with the identity back, the markup sits *above* s/v again by
        # the fixed-capital term the price system omits (docs/27).
        self.assertGreater(
            system["gross_markup"], control.rate_of_surplus_value()
        )

    def test_the_profit_rate_now_falls_below_the_rate_of_surplus_value(self):
        """Two magnitudes that were the same number, prised apart.

        Until docs/28 the only thing separating `r` from s/v was the fixed
        capital the price system omits — 0.12%, and in the direction that
        made `r` the larger. A material input into a wage good reverses the
        sign and multiplies the size: `r` is now nearly 8% *below* s/v, and
        the omission is no longer the dominant term.
        """
        cumulative = self.economy.rate_of_surplus_value()
        self.assertLess(self.system["gross_markup"], cumulative)
        gap = (cumulative - self.system["gross_markup"]) / cumulative
        self.assertGreater(gap, 0.06)
        self.assertLess(gap, 0.09)

    def test_the_basket_carries_plant_and_inputs_the_price_system_does_not(self):
        """What separates the two baskets, itemized.

        The value system's basket exceeds its direct-labor content by two
        terms: the plant worn out making each good, which the price system
        omits entirely (docs/26 section 3.5), and the material inputs
        transferred into it, which the price system carries at a *marked
        up* price instead. The second term now dominates the first.
        """
        region = self.economy.regions["Dust Basin"]
        _, labor, _ = self.economy.social_technique()
        processes = circuit_processes()
        basket = region.subsistence_basket

        def capital(commodity):
            _, ticks = processes[commodity].capital_consumed_per_unit(
                commodity,
                self.economy.capital_service_life_days,
                self.economy.commodities,
            )
            return ticks

        with_capital = self.economy.basket_labor_value(region)
        without_capital = sum(
            quantity * labor[name] for name, quantity in sorted(basket.items())
        )
        plant = sum(
            quantity * capital(name)
            for name, quantity in sorted(basket.items())
        )
        transferred = sum(
            quantity
            * sum(
                per_unit * self.economy.labor_values[other]
                for other, per_unit in sorted(processes[name].inputs.items())
            )
            for name, quantity in sorted(basket.items())
        )
        self.assertAlmostEqual(
            with_capital - without_capital, plant + transferred, places=9
        )
        self.assertGreater(transferred, plant)

    def test_a_pure_labor_good_prices_at_its_direct_labor_ratio(self):
        # Chemfuel and meals both have no modelled inputs, so each is
        # (1 + r) * w * l and the markup cancels in the ratio.
        _, labor, _ = self.economy.social_technique()
        self.assertAlmostEqual(
            self.relative(CHEMFUEL),
            labor[CHEMFUEL] / labor[MEALS],
            places=12,
        )

    def test_the_value_ratio_and_the_price_ratio_part_by_exactly_that_omission(self):
        """Not identical, and the difference is named.

        The prediction in docs/26 section 7.5 said these two ratios would
        agree exactly. They do not, because labor values carry the plant's
        embodied labor and the price system leaves fixed capital out. The
        gap is small, one-directional, and fully explained.
        """
        process = circuit_processes()
        _, labor, _ = self.economy.social_technique()

        def capital(commodity):
            _, ticks = process[commodity].capital_consumed_per_unit(
                commodity,
                self.economy.capital_service_life_days,
                self.economy.commodities,
            )
            return ticks

        value_ratio = (
            self.economy.labor_values[CHEMFUEL]
            / self.economy.labor_values[MEALS]
        )
        self.assertAlmostEqual(
            value_ratio,
            (labor[CHEMFUEL] + capital(CHEMFUEL))
            / (labor[MEALS] + capital(MEALS)),
            places=12,
        )
        self.assertNotAlmostEqual(value_ratio, self.relative(CHEMFUEL), places=12)
        self.assertLess(
            abs(value_ratio - self.relative(CHEMFUEL)) / value_ratio, 0.001
        )

    def test_the_markup_compounds_through_the_input_chain(self):
        """The headline negative result: these prices are worse than authored.

        Yayo takes eight leaves, and the gross markup applies to the leaves
        and again to the yayo, so a two-stage chain meets a 39-fold markup
        twice. Nothing is wrong with the arithmetic; the meals-only basket
        makes `r` absurd and the chain amplifies it.
        """
        authored = (
            self.parameters.reference_price / self.parameters.meal_reference_price
        )
        # Down from 71.6x under the meals-only basket (docs/27) and still
        # nowhere a price system could be used.
        self.assertGreater(self.relative(YAYO) / authored, 30.0)
        # Leaves are one stage up and overshoot by about two thirds.
        self.assertGreater(self.relative(LEAVES), 1.5 * self.economy.labor_values[
            LEAVES
        ] / self.economy.labor_values[MEALS])

    def test_total_price_equals_total_value_under_that_normalization(self):
        aggregates = self.economy.production_price_aggregates()
        self.assertAlmostEqual(
            aggregates["total_price"], aggregates["total_value"], places=6
        )

    def test_total_profit_does_not_equal_total_surplus(self):
        """Marx's two invariance postulates, and the one that has to give.

        Imposing total price = total value leaves total profit well above
        total surplus. Asserted as a positive claim about the size of the
        gap rather than tolerated as slack: if this ever came out near 1.0
        the normalization would be doing something the model does not
        intend.
        """
        aggregates = self.economy.production_price_aggregates()
        ratio = aggregates["total_profit"] / aggregates["total_surplus"]
        self.assertGreater(ratio, 1.4)
        self.assertLess(ratio, 1.7)

    # -- Sraffa's basics theorem, on a purpose-built three-good economy ------

    def three_good_economy(
        self, *, bread_labor=500.0, tool_labor=30.0, inventory_days=30.0
    ):
        """Bread feeds the workers; ore makes tools; tools feed nobody.

        Bread is the only basic commodity, so the profit rate must answer
        to bread's technique and to nothing else.
        """
        from economy_lab.model import Economy, Region

        commodities = [
            Commodity(
                name,
                reference_price=10.0,
                labor_value=1.0,
                target_inventory_days=inventory_days,
            )
            for name in ("bread", "ore", "tool")
        ]
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"bread": 0.0, "ore": 0.0, "tool": 1.0},
            inventory={"bread": 100.0, "ore": 100.0, "tool": 100.0},
            prices={"bread": 10.0, "ore": 10.0, "tool": 10.0},
            producers=[
                Producer(
                    "bakery", "bread", 1.0, 1.0,
                    process=Process(
                        "baking",
                        outputs={"bread": 1.0},
                        direct_labor=bread_labor,
                    ),
                ),
                Producer(
                    "mine", "ore", 2.0, 1.0,
                    process=Process(
                        "mining", outputs={"ore": 1.0}, direct_labor=20.0
                    ),
                ),
                Producer(
                    "smithy", "tool", 1.0, 1.0,
                    process=Process(
                        "smithing",
                        outputs={"tool": 1.0},
                        inputs={"ore": 2.0},
                        direct_labor=tool_labor,
                    ),
                ),
            ],
            subsistence_basket={"bread": 1.0},
            ticks_per_worker_day=1000.0,
        )
        economy = Economy(commodities, [region], [])
        return economy.prices_of_production(
            numeraire="bread", use_capacity=True
        )

    def test_the_three_good_system_solves_to_the_hand_computed_prices(self):
        system = self.three_good_economy()
        self.assertEqual(system["basics"], ["bread"])
        # markup = 1000 ticks per worker-day / 500 ticks of bread - 1.
        self.assertAlmostEqual(system["gross_markup"], 1.0, places=9)
        # And the rate is that markup spread over the turnover time: one
        # production period plus the bare Commodity's 30-day inventory life.
        self.assertAlmostEqual(system["profit_rate"], 1.0 / 31.0, places=9)
        # w = 10 silver of bread / 1000 ticks; ore is 2 * (0.01 * 20).
        self.assertAlmostEqual(system["wage"], 0.01, places=12)
        self.assertAlmostEqual(system["prices"]["ore"], 0.4, places=9)
        # tool = 2 * (2 ore + 0.01 * 30)
        self.assertAlmostEqual(system["prices"]["tool"], 2.2, places=9)

    def test_instant_turnover_reduces_to_the_pre_turnover_system(self):
        """The compatibility property of docs/30 section 2.1.

        With one production period and no inventory life, capital is
        advanced for exactly one period and the rate *is* the markup. This
        is the boundary case the turnover term has to reproduce exactly, or
        it is not a generalization.
        """
        system = self.three_good_economy(inventory_days=0.0)
        self.assertEqual(system["turnover_days"]["bread"], 1.0)
        self.assertEqual(system["profit_rate"], system["gross_markup"])
        self.assertAlmostEqual(system["profit_rate"], 1.0, places=9)

    def test_a_non_basic_technique_change_leaves_the_profit_rate_untouched(self):
        base = self.three_good_economy()
        doubled = self.three_good_economy(tool_labor=60.0)
        self.assertEqual(doubled["gross_markup"], base["gross_markup"])
        self.assertEqual(doubled["profit_rate"], base["profit_rate"])
        self.assertEqual(doubled["prices"]["ore"], base["prices"]["ore"])
        self.assertEqual(doubled["prices"]["bread"], base["prices"]["bread"])
        # Only the changed sector's own price moves.
        self.assertAlmostEqual(doubled["prices"]["tool"], 2.8, places=9)

    def test_a_basic_technique_change_moves_the_profit_rate(self):
        cheaper = self.three_good_economy(bread_labor=400.0)
        self.assertAlmostEqual(cheaper["gross_markup"], 1.5, places=9)
        # And it moves every price with it, the wage good's included.
        self.assertAlmostEqual(cheaper["prices"]["ore"], 0.5, places=9)
        self.assertAlmostEqual(cheaper["prices"]["tool"], 3.25, places=9)

    # -- undefined and impossible systems ------------------------------------

    def test_a_model_without_a_wage_relation_has_no_price_system(self):
        from economy_lab.model import Economy, Region

        widget = Commodity("widget", reference_price=10.0, labor_value=1.0)
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"widget": 1.0},
            inventory={"widget": 5.0},
            prices={"widget": 10.0},
            producers=[
                Producer(
                    "mill", "widget", 4.0, 1.0,
                    process=Process(
                        "milling", outputs={"widget": 1.0}, direct_labor=10.0
                    ),
                ),
            ],
        )
        economy = Economy([widget], [region], [])
        economy.step(5)
        # Produced, priced, and still undefined: without a basket the wage
        # is zero and every pure-labor good would price at zero.
        self.assertGreater(economy.ledger.production["widget"], 0.0)
        self.assertIsNone(economy.prices_of_production())
        self.assertIsNone(economy.production_price_aggregates())

    def test_a_closed_exchange_cycle_refuses_rather_than_returning(self):
        """Two goods that only make each other have no settled relative price.

        The iteration oscillates instead of converging, and that must be an
        explicit error like the value solve's, not a number pulled from
        whichever iteration the loop happened to stop on.
        """
        from economy_lab.model import Economy, Region

        commodities = [
            Commodity("bread", reference_price=10.0, labor_value=1.0),
            Commodity("alpha", reference_price=10.0, labor_value=1.0),
            Commodity("beta", reference_price=10.0, labor_value=1.0),
        ]
        region = Region(
            "Plain",
            cash=10_000.0,
            base_daily_demand={"bread": 0.0, "alpha": 0.0, "beta": 0.0},
            inventory={"bread": 100.0, "alpha": 100.0, "beta": 100.0},
            prices={"bread": 10.0, "alpha": 10.0, "beta": 10.0},
            producers=[
                Producer(
                    "bakery", "bread", 1.0, 1.0,
                    process=Process(
                        "baking", outputs={"bread": 1.0}, direct_labor=500.0
                    ),
                ),
                Producer(
                    "alpha works", "alpha", 1.0, 1.0,
                    process=Process(
                        "alpha", outputs={"alpha": 1.0}, inputs={"beta": 2.0}
                    ),
                ),
                Producer(
                    "beta works", "beta", 1.0, 1.0,
                    process=Process(
                        "beta", outputs={"beta": 1.0}, inputs={"alpha": 0.5}
                    ),
                ),
            ],
            subsistence_basket={"bread": 1.0},
            ticks_per_worker_day=1000.0,
        )
        economy = Economy(commodities, [region], [])
        with self.assertRaises(RuntimeError) as raised:
            economy.prices_of_production(use_capacity=True)
        self.assertIn("closed cycle", str(raised.exception))

    def test_querying_the_price_system_does_not_perturb_the_economy(self):
        """An observation, not a step. Bit-identical histories or nothing."""
        quiet = equilibrium(0)
        noisy = equilibrium(0)
        for _ in range(60):
            quiet.step(1)
            noisy.step(1)
            noisy.prices_of_production()
            noisy.production_price_aggregates()
        for name, region in quiet.regions.items():
            other = noisy.regions[name]
            for commodity in quiet.commodities:
                with self.subTest(region=name, commodity=commodity):
                    self.assertEqual(
                        region.prices[commodity], other.prices[commodity]
                    )
                    self.assertEqual(
                        region.inventory[commodity], other.inventory[commodity]
                    )
            self.assertEqual(region.cash, other.cash)
            self.assertEqual(region.worker_cash, other.worker_cash)


class EnlargedBasketTests(unittest.TestCase):
    """Clothing and medicine join meals, and what that does to the ratios.

    Every quantity comes from the closed analysis and RimWorld's own
    MarketValue (docs/28). The measurement this class protects is not that
    the ratios improve — they do — but *how far*, because the answer is the
    session's result: not far enough, and for a reason no basket can fix.
    """

    @classmethod
    def setUpClass(cls):
        cls.parameters = ScenarioParameters()
        cls.economy = equilibrium(240)
        # The model as it stood before this session, reachable as a
        # parameter override rather than as a memory. It is the control for
        # every comparison below and a regression anchor on docs/24 and
        # docs/27.
        cls.meals_only = equilibrium(
            240,
            parameters=replace(
                ScenarioParameters(),
                garments_per_worker_day=0.0,
                medicine_per_worker_day=0.0,
            ),
        )

    def test_the_meals_only_control_reproduces_the_published_figures(self):
        # docs/24 and docs/27, to the digits those documents printed.
        self.assertAlmostEqual(
            self.meals_only.rate_of_surplus_value(), 38.29814, places=5
        )
        self.assertAlmostEqual(
            self.meals_only.organic_composition(), 20.66573, places=5
        )
        self.assertAlmostEqual(
            self.meals_only.value_rate_of_profit(), 1.76768, places=5
        )
        # Read as the gross markup since docs/30: the same number under
        # the name that survives turnover.
        self.assertAlmostEqual(
            self.meals_only.prices_of_production()["gross_markup"],
            38.344262,
            places=6,
        )

    def test_the_wage_is_the_whole_basket_at_current_prices(self):
        for region in self.economy.regions.values():
            expected = sum(
                quantity * region.prices[name]
                for name, quantity in sorted(region.subsistence_basket.items())
            )
            self.assertAlmostEqual(region.wage_rate(), expected, places=12)
            self.assertAlmostEqual(
                region.wage_rate(), self.parameters.basket_cost(), places=12
            )
            self.assertEqual(len(region.subsistence_basket), 3)

    def test_workers_actually_consume_clothing_and_medicine(self):
        for commodity in (MEALS, GARMENTS, MEDICINE):
            with self.subTest(commodity=commodity):
                consumed = self.economy.ledger.consumption.get(commodity, 0.0)
                produced = self.economy.ledger.production.get(commodity, 0.0)
                self.assertGreater(consumed, 0.0)
                # Nothing accumulates and nothing appears: the basket is
                # made and eaten in the same period at equilibrium.
                self.assertAlmostEqual(consumed, produced, places=6)
        self.assertEqual(self.economy.ledger.basket_shortfall, {})

    def test_the_basket_labor_value_is_its_three_components(self):
        for region in self.economy.regions.values():
            expected = sum(
                quantity * self.economy.labor_values[name]
                for name, quantity in sorted(region.subsistence_basket.items())
            )
            self.assertAlmostEqual(
                self.economy.basket_labor_value(region), expected, places=9
            )
        # Necessary labor rises from 2.5% of the working day to 3.6%. That
        # is the whole of what an honest basket buys, and it is the reason
        # for the conclusion in docs/29.
        share = self.economy.basket_labor_value(
            self.economy.regions["Dust Basin"]
        ) / self.parameters.ticks_per_worker_day
        self.assertGreater(share, 0.035)
        self.assertLess(share, 0.037)

    def test_every_ratio_built_on_variable_capital_falls(self):
        self.assertLess(
            self.economy.rate_of_surplus_value(),
            self.meals_only.rate_of_surplus_value(),
        )
        self.assertLess(
            self.economy.organic_composition(),
            self.meals_only.organic_composition(),
        )
        self.assertLess(
            self.economy.value_rate_of_profit(),
            self.meals_only.value_rate_of_profit(),
        )

    def test_the_value_rate_of_profit_barely_moves(self):
        """The structurally interesting part of the result.

        s/v and c/v are ratios *to* variable capital and fall with it. The
        value rate of profit has constant capital in the denominator too,
        and c is fourteen times v even after the enlargement, so a 42%
        larger basket moves it by about 2%. Enlarging the basket fixes two
        of the three headline ratios and does almost nothing to the third.
        """

        def move(current, before):
            return abs(current - before) / before

        surplus_move = move(
            self.economy.rate_of_surplus_value(),
            self.meals_only.rate_of_surplus_value(),
        )
        composition_move = move(
            self.economy.organic_composition(),
            self.meals_only.organic_composition(),
        )
        profit_move = move(
            self.economy.value_rate_of_profit(),
            self.meals_only.value_rate_of_profit(),
        )
        self.assertGreater(surplus_move, 0.25)
        self.assertGreater(composition_move, 0.25)
        self.assertLess(profit_move, 0.05)

    def test_a_generous_basket_still_leaves_the_rate_an_order_of_magnitude_high(self):
        """The bound from above (docs/28 section 3.5).

        Three meals, half a garment and half a dose a day is a bundle
        nobody could call stingy, and the rate of surplus value is still
        above ten. No defensible basket brings it near the magnitudes the
        literature works with, because the constraint is RimWorld's own
        productivity and not the bundle.
        """
        generous = generous_basket(240)
        self.assertLess(
            generous.rate_of_surplus_value(),
            self.economy.rate_of_surplus_value(),
        )
        self.assertGreater(generous.rate_of_surplus_value(), 10.0)
        self.assertLess(generous.rate_of_surplus_value(), 12.0)
        # And it is still exactly stationary, which is what makes it a
        # measurement rather than a shortage.
        for region_name in generous.regions:
            for name in generous.commodities:
                prices = generous.series(region_name, name)
                self.assertEqual(min(prices), max(prices))

    def test_the_working_day_is_what_actually_constrains_it(self):
        """One provisioner feeds thirty-nine workers, on RimWorld's numbers.

        This is the sentence the whole session comes down to. A rate of
        surplus value near 1 needs a basket embodying half a working day;
        in meals alone that is thirty-nine meals a worker a day.
        """
        parameters = self.parameters
        meals_fed = parameters.ticks_per_worker_day / (
            parameters.meals_per_worker_day * self.economy.labor_values[MEALS]
        )
        self.assertGreater(meals_fed, 39.0)
        self.assertLess(meals_fed, 40.0)
        half_a_day = parameters.ticks_per_worker_day / 2.0
        meals_for_parity = half_a_day / self.economy.labor_values[MEALS]
        self.assertGreater(meals_for_parity, 39.0)

    def test_an_under_provisioned_basket_good_is_named_at_seeding(self):
        with self.assertRaises(ValueError) as raised:
            equilibrium(
                1,
                parameters=replace(
                    ScenarioParameters(), garment_capacity_per_day=0.001
                ),
            )
        message = str(raised.exception)
        self.assertIn(GARMENTS, message)
        self.assertIn("exceeds capacity", message)

    def test_the_enlarged_circuit_still_closes_every_ledger(self):
        for name, residual in self.economy.commodity_balances().items():
            with self.subTest(commodity=name):
                self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertAlmostEqual(self.economy.cash_balance(), 0.0, places=7)
        self.assertAlmostEqual(self.economy.value_balance(), 0.0, places=3)


class TurnoverTests(unittest.TestCase):
    """Profit charged against capital advanced rather than capital consumed.

    Two quantities the project printed as rates of profit were not rates:
    the price system's was per production period with the period a day, and
    the ledger's divided by capital consumed. Both are fixed here, and the
    fix is mostly a matter of dividing by a number the model already knew
    (docs/30).
    """

    @classmethod
    def setUpClass(cls):
        cls.parameters = ScenarioParameters()
        cls.economy = equilibrium(240)
        cls.system = cls.economy.prices_of_production(numeraire=MEALS)
        cls.perishable = perishable_meals(240)

    # -- the price system ----------------------------------------------------

    def test_turnover_is_the_production_period_plus_the_inventory_life(self):
        for name, days in self.system["turnover_days"].items():
            with self.subTest(commodity=name):
                self.assertEqual(
                    days,
                    self.parameters.production_period_days
                    + self.economy.commodities[name].target_inventory_days,
                )

    def test_the_rate_is_the_markup_spread_over_the_turnover(self):
        # Exact to floating point, because uniform turnover is solved in
        # closed form rather than searched for.
        self.assertAlmostEqual(
            self.system["profit_rate"] * 21.0,
            self.system["gross_markup"],
            places=9,
        )
        self.assertAlmostEqual(self.system["profit_rate"], 1.1725658, places=6)
        self.assertAlmostEqual(self.system["gross_markup"], 24.623882, places=6)

    def test_uniform_turnover_moves_no_relative_price(self):
        """The invariance of docs/30 section 3.2, asserted bit-exactly.

        `1 + r*tau` is one constant when turnover is uniform, so the price
        vector is the pre-turnover one and only the reported rate changes.
        These are the docs/29 figures, unrounded.
        """
        prices = self.system["prices"]
        inputs, labor, _ = self.economy.social_technique()
        bundle = self.economy.social_wage_bundle()
        wage = sum(per_tick * prices[name] for name, per_tick in bundle.items())

        # Every sector's price over its own cost is the same constant, which
        # is exactly what "the diagonal factors out" means. Asserted rather
        # than compared against remembered digits.
        markups = {}
        for name in prices:
            cost = (
                sum(
                    quantity * prices[other]
                    for other, quantity in inputs.get(name, {}).items()
                )
                + labor[name] * wage
            )
            markups[name] = prices[name] / cost
        for name, markup in sorted(markups.items()):
            with self.subTest(commodity=name):
                self.assertAlmostEqual(
                    markup, 1.0 + self.system["gross_markup"], places=9
                )

        # And the price vector is still the one docs/29 published, to the
        # decimals that document printed.
        base = prices[MEALS]
        for name, expected in (
            (CHEMFUEL, 0.08197),
            (MEDICINE, 1.31148),
            (GARMENTS, 7.25577),
            (LEAVES, 0.25649),
            (YAYO, 54.14603),
        ):
            with self.subTest(commodity=name, published=expected):
                self.assertAlmostEqual(prices[name] / base, expected, places=5)

    # -- the ledger ----------------------------------------------------------

    def test_capital_advanced_itemizes_into_positive_parts(self):
        advanced = self.economy.capital_advanced()
        self.assertGreater(advanced["commodity_capital"], 0.0)
        self.assertGreater(advanced["fixed_capital"], 0.0)
        self.assertGreater(advanced["wage_advance"], 0.0)
        self.assertGreaterEqual(advanced["in_transit"], 0.0)
        self.assertAlmostEqual(
            advanced["total"],
            advanced["commodity_capital"]
            + advanced["in_transit"]
            + advanced["fixed_capital"]
            + advanced["wage_advance"],
            places=9,
        )
        # The wage advance is what the pre-turnover system effectively
        # charged profit against for a pure-labor good. It is a thousandth
        # of the capital actually tied up.
        self.assertLess(
            advanced["wage_advance"] / advanced["total"], 0.002
        )

    def test_the_advance_is_dominated_by_the_final_product_awaiting_sale(self):
        """Why realized turnover is three times what the price system assumes.

        Yayo is nobody's input, so its inventory never appears in any cost
        flow — and it is the largest single block of capital in the circuit.
        """
        held = {
            name: sum(
                region.inventory[name] for region in self.economy.regions.values()
            )
            * self.economy.labor_values[name]
            for name in self.economy.commodities
        }
        total = sum(held.values())
        self.assertGreater(held[YAYO] / total, 0.60)
        self.assertGreater((held[YAYO] + held[LEAVES]) / total, 0.95)

    def test_realized_turnover_far_exceeds_the_assumed_turnover(self):
        realized = self.economy.realized_turnover_days()
        self.assertGreater(realized, 50.0)
        self.assertLess(realized, 60.0)
        # And the excess is the final product's stock: take yayo out of the
        # advance and the figure lands near the 21 days the price system
        # assumes.
        yayo_stock = (
            sum(
                region.inventory[YAYO]
                for region in self.economy.regions.values()
            )
            * self.economy.labor_values[YAYO]
        )
        advanced = self.economy.capital_advanced()["total"]
        consumed = advanced / realized
        self.assertLess((advanced - yayo_stock) / consumed, 25.0)
        self.assertGreater((advanced - yayo_stock) / consumed, 18.0)

    def test_the_rate_of_profit_is_far_below_the_flow_ratio(self):
        """The two quantities, kept apart and both reported.

        `value_rate_of_profit` divides by capital consumed and is profit per
        unit of throughput; the rate of profit divides by capital advanced.
        They differ by the realized turnover time, which is what makes one
        of them a rate.
        """
        flow = self.economy.value_rate_of_profit()
        rate = self.economy.value_rate_of_profit_on_advances()
        self.assertLess(rate, flow / 40.0)
        self.assertAlmostEqual(rate, 0.030479, places=6)
        self.assertAlmostEqual(
            flow / rate, self.economy.realized_turnover_days(), delta=0.5
        )

    def test_a_model_that_has_not_run_has_no_rate_on_advances(self):
        self.assertIsNone(equilibrium(0).value_rate_of_profit_on_advances())
        self.assertIsNone(equilibrium(0).realized_turnover_days())

    # -- differential turnover -----------------------------------------------

    def test_perishable_meals_turn_over_faster_than_everything_else(self):
        turnover = self.perishable.prices_of_production()["turnover_days"]
        self.assertEqual(turnover[MEALS], 5.0)
        for name in (CHEMFUEL, GARMENTS, MEDICINE, LEAVES, YAYO):
            with self.subTest(commodity=name):
                self.assertEqual(turnover[name], 21.0)

    def test_a_faster_wage_good_raises_the_uniform_rate(self):
        # Capital released from the meal circuit has to earn the same rate
        # somewhere, and there is less of it tied up in total.
        system = self.perishable.prices_of_production(numeraire=MEALS)
        self.assertGreater(system["profit_rate"], self.system["profit_rate"])
        self.assertAlmostEqual(system["profit_rate"], 2.079222, places=6)

    def test_differential_turnover_widens_the_price_deviations(self):
        """The result differential turnover was added to test.

        Uniform turnover is a scalar and moves nothing. Non-uniform
        turnover redistributes: meals carry five periods of markup while
        everything else carries twenty-one, at a rate that is itself higher.
        """
        system = self.perishable.prices_of_production(numeraire=MEALS)
        base = system["prices"][MEALS]
        self.assertGreater(
            system["prices"][YAYO] / base,
            8.0 * self.system["prices"][YAYO] / self.system["prices"][MEALS],
        )
        for name in (CHEMFUEL, GARMENTS, MEDICINE, LEAVES):
            with self.subTest(commodity=name):
                self.assertGreater(
                    system["prices"][name] / base,
                    self.system["prices"][name]
                    / self.system["prices"][MEALS],
                )

    def test_perishable_meals_is_still_exactly_stationary(self):
        # The seeded stock has to be the commodity's own inventory life, not
        # the global default; they were the same number until meals rotted.
        for region_name in self.perishable.regions:
            for name in self.perishable.commodities:
                with self.subTest(region=region_name, commodity=name):
                    prices = self.perishable.series(region_name, name)
                    stocks = self.perishable.series(
                        region_name, name, field="inventory"
                    )
                    self.assertEqual(min(prices), max(prices))
                    self.assertEqual(min(stocks), max(stocks))
        dust = self.perishable.regions["Dust Basin"]
        self.assertAlmostEqual(
            dust.inventory[MEALS],
            dust.throughput_demand(MEALS)
            * self.parameters.perishable_meal_days,
            places=9,
        )

    def test_the_perishable_circuit_still_closes_every_ledger(self):
        for name, residual in self.perishable.commodity_balances().items():
            with self.subTest(commodity=name):
                self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertAlmostEqual(self.perishable.cash_balance(), 0.0, places=7)


class ThroughputBatchTests(unittest.TestCase):
    """The one optimization docs/33 permitted, held to bit-equality.

    `throughput_demands` computes in one pass what `throughput_demand`
    computed once per commodity. The claim is not "close enough" — it is
    that the two produce the identical float, because the derived terms
    accumulate in the same producer order and the producers the batch skips
    contribute exactly 0.0.
    """

    def assert_batch_matches(self, economy):
        for name, region in economy.regions.items():
            batch = region.throughput_demands()
            self.assertEqual(sorted(batch), sorted(economy.commodities))
            for commodity in sorted(economy.commodities):
                with self.subTest(region=name, commodity=commodity):
                    self.assertEqual(
                        batch[commodity], region.throughput_demand(commodity)
                    )

    def test_it_matches_across_every_scenario(self):
        for economy in (
            equilibrium(240),
            regional_glut(),
            producer_loss(),
            reserve_depletion(),
            technique_change(180),
            perishable_meals(120),
        ):
            with self.subTest(day=economy.day):
                self.assert_batch_matches(economy)

    def test_it_matches_after_capacity_is_destroyed(self):
        # The invalidation case: capacity moves between steps, and the
        # daily rebuild has to pick it up.
        economy = seeded_two_region_economy()
        economy.step(30)
        economy.destroy_capacity("Dust Basin", LEAVES, 0.60)
        economy.step(1)
        self.assert_batch_matches(economy)

    def test_the_daily_rebuild_agrees_with_the_regions(self):
        economy = equilibrium(120)
        for name, region in economy.regions.items():
            for commodity in sorted(economy.commodities):
                with self.subTest(region=name, commodity=commodity):
                    self.assertEqual(
                        economy.throughput(name, commodity),
                        region.throughput_demand(commodity),
                    )


class ScaleHarnessTests(unittest.TestCase):
    """The generator that answers the size question (docs/32, docs/33).

    Sizes here are deliberately small — the harness itself is measured by
    `python -m economy_lab.scale`, and these tests protect the properties
    the measurement rests on rather than repeating it.
    """

    def test_the_generator_is_deterministic(self):
        first = synthetic_economy(commodities=80, regions=3)
        second = synthetic_economy(commodities=80, regions=3)
        first.step(5)
        second.step(5)
        self.assertEqual(first.history, second.history)

    def test_a_generated_economy_closes_its_ledgers(self):
        economy = synthetic_economy(commodities=120, regions=2)
        economy.step(20)
        for name, residual in economy.commodity_balances().items():
            with self.subTest(commodity=name):
                # Relative rather than absolute: these are RimWorld's own
                # magnitudes, and a 400,000-tick commodity does not close
                # to 1e-9 in absolute terms just because a 25-tick one does.
                produced = max(economy.ledger.production.get(name, 0.0), 1.0)
                self.assertLess(abs(residual) / produced, 1e-9)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=4)

    def test_no_stock_goes_negative_at_width(self):
        economy = synthetic_economy(commodities=120, regions=2)
        economy.step(30)
        for region in economy.regions.values():
            for name, held in region.inventory.items():
                with self.subTest(commodity=name):
                    self.assertGreaterEqual(held, -1e-6)

    def test_the_value_solve_reproduces_the_closed_analysis_at_width(self):
        """The docs/20 validation, six hundred commodities wide.

        `docs/20` checked the solver against `FINDINGS.md` on four
        commodities. Here it is checked on 611, and every commodity whose
        synthetic wiring did not contradict the real figures — where the
        inputs already carried more labor than the def does, so direct
        labor floored at one tick — reproduces the closed analysis's
        embodied labor exactly.
        """
        economy = synthetic_economy(commodities=653, regions=2)
        economy.step(1)
        record = economy.scale_record
        floored = set(record["floored"])
        processes = {
            producer.commodity: producer.process
            for producer in economy.regions["region_000"].producers
        }

        def tainted(name, seen=None):
            seen = set() if seen is None else seen
            if name in seen:
                return False
            seen.add(name)
            return any(
                other in floored or tainted(other, seen)
                for other in processes[name].inputs
            )

        exact = 0
        for name, authored in sorted(record["labor"].items()):
            if name in floored or authored <= 0.0:
                continue
            error = abs(economy.labor_values[name] - authored) / authored
            if tainted(name):
                continue
            with self.subTest(commodity=name):
                self.assertLess(error, 1e-9)
            exact += 1
        self.assertGreater(exact, 400)

    def test_iteration_counts_do_not_grow_with_width(self):
        """Depth 3, so the fixed points settle in a handful of passes.

        If this ever fails, the generator has produced cycles the real
        data does not have — a bug in the harness rather than a finding
        about the model.
        """
        narrow = synthetic_economy(commodities=60, regions=2)
        wide = synthetic_economy(commodities=480, regions=2)
        narrow.step(2)
        wide.step(2)
        narrow_iterations = narrow.prices_of_production()["iterations"]
        wide_iterations = wide.prices_of_production()["iterations"]
        self.assertLess(wide_iterations, 3 * narrow_iterations + 5)

    def test_the_population_is_the_real_one(self):
        rows = population(40)
        self.assertEqual(len(rows), 40)
        self.assertEqual(len(population()), 647)
        # Sampled with a stride so a small run keeps the depth mix rather
        # than taking every shallow def first.
        self.assertGreater(len({row["depth"] for row in rows}), 2)


class HistoryDetailTests(unittest.TestCase):
    """History is an output, and the runtime cannot afford it (docs/34).

    At 647 commodities and a hundred regions a full snapshot costs ~16 MiB
    a day. The laboratory needs every field; the runtime needs none. The
    property that makes opting out safe is that nothing in the simulation
    reads history back — which this class asserts rather than assumes,
    because the design document asserted it and was wrong.
    """

    def run_pair(self, days=90, **kwargs):
        full = equilibrium(days)
        sparse = equilibrium(
            days, parameters=replace(ScenarioParameters(), **kwargs)
        )
        return full, sparse

    def test_opting_out_leaves_the_simulation_bit_identical(self):
        full, bare = self.run_pair(record_history=False)
        for name, region in full.regions.items():
            other = bare.regions[name]
            for commodity in sorted(full.commodities):
                with self.subTest(region=name, commodity=commodity):
                    self.assertEqual(
                        region.prices[commodity], other.prices[commodity]
                    )
                    self.assertEqual(
                        region.inventory[commodity], other.inventory[commodity]
                    )
            self.assertEqual(region.cash, other.cash)
            self.assertEqual(region.worker_cash, other.worker_cash)
        self.assertEqual(full.labor_values, bare.labor_values)
        self.assertEqual(
            full.rate_of_surplus_value(), bare.rate_of_surplus_value()
        )

    def test_the_material_ledger_still_closes_without_history(self):
        """The dependency docs/34 section 3.3 missed.

        `commodity_balance` read its opening stock out of `history[0]`, so
        opting out of history broke the material ledger. The opening stock
        is state now, and this is the test that says so.
        """
        _, bare = self.run_pair(days=60, record_history=False)
        for name, residual in bare.commodity_balances().items():
            with self.subTest(commodity=name):
                self.assertAlmostEqual(residual, 0.0, places=7)
        self.assertAlmostEqual(bare.cash_balance(), 0.0, places=7)

    def test_the_opening_stock_is_what_history_recorded(self):
        economy = equilibrium(0)
        self.assertEqual(
            economy.opening_inventory,
            economy.history[0]["system_inventory"],
        )

    def test_opting_out_leaves_only_day_markers(self):
        _, bare = self.run_pair(days=30, record_history=False)
        self.assertEqual(len(bare.history), 31)
        self.assertEqual(
            [snapshot["day"] for snapshot in bare.history], list(range(31))
        )
        for snapshot in bare.history:
            self.assertEqual(set(snapshot), {"day"})

    def test_sampling_keeps_the_days_it_promises(self):
        _, sparse = self.run_pair(days=30, history_every=7)
        detailed = [
            snapshot["day"]
            for snapshot in sparse.history
            if "system_inventory" in snapshot
        ]
        # Day zero, every seventh day, and the last day of the run, so a
        # sampled history brackets its own range.
        self.assertEqual(detailed, [0, 7, 14, 21, 28, 30])
        self.assertEqual(len(sparse.history), 31)

    def test_series_refuses_rather_than_mis_indexing(self):
        # Callers read the index as a day number. A shorter list would
        # corrupt every shock metric in the reference and fail nothing.
        _, bare = self.run_pair(days=10, record_history=False)
        with self.assertRaises(RuntimeError) as raised:
            bare.series("Dust Basin", YAYO)
        self.assertIn("record_history=False", str(raised.exception))

        _, sparse = self.run_pair(days=10, history_every=5)
        with self.assertRaises(RuntimeError) as raised:
            sparse.series("Dust Basin", YAYO)
        self.assertIn("samples history", str(raised.exception))

    def test_history_every_must_be_a_real_interval(self):
        from economy_lab.model import Economy

        with self.assertRaises(ValueError):
            Economy([], [], [], history_every=0)


if __name__ == "__main__":
    unittest.main()


class CapitalGoodsTests(unittest.TestCase):
    """Department I: machines that are produced rather than assumed (docs/36).

    The circuit's fixed capital had been six authored constants.  They are
    bills of materials in three commodities plus construction work, and the
    tests below are the arithmetic of docs/36 section 2 made executable, so
    the table in that document cannot rot without something going red.
    """

    #: The closed analysis's embodied labor for the three capital goods.
    AUTHORED = {STEEL: 47.5, WOOD: 22.5, COMPONENTS: 5570.0}

    def test_every_bill_reproduces_its_authored_machine_to_the_tick(self):
        """docs/36 section 2: six machines and a machining table, exactly."""
        parameters = ScenarioParameters(capital_goods=True)
        expected = {
            YAYO: parameters.drug_lab_capital_labor,
            LEAVES: parameters.psychoid_field_capital_labor,
            CHEMFUEL: parameters.refinery_capital_labor,
            MEALS: parameters.provisioner_capital_labor,
            GARMENTS: parameters.tailoring_bench_capital_labor,
            MEDICINE: parameters.plant_pot_capital_labor,
            # TableMachining: 150 steel, 5 components, 3000 work.
            COMPONENTS: 37_975.0,
        }
        for sector, (bill, work) in parameters.machine_bills.items():
            if sector not in expected:
                continue
            with self.subTest(sector=sector):
                self.assertEqual(
                    sum(
                        quantity * self.AUTHORED[name]
                        for name, quantity in bill.items()
                    )
                    + work,
                    expected[sector],
                )

    def test_a_bill_free_process_is_untouched(self):
        """An empty bill must change nothing, which is how docs/23 shipped."""
        for process in circuit_processes(ScenarioParameters()).values():
            self.assertEqual(process.capital_bill, {})
            self.assertEqual(process.capital_bill_per_capacity(), {})
            self.assertEqual(process.machines_per_capacity, 0.0)

    def test_the_capital_goods_equilibrium_is_exactly_stationary(self):
        """Nine commodities, both regions, four years, price range exactly 0."""
        economy = capital_goods(days=4 * DAYS_PER_YEAR)
        self.assertEqual(len(economy.commodities), 9)
        for rname in economy.regions:
            for cname in economy.commodities:
                series = economy.series(rname, cname)
                self.assertEqual(
                    max(series) - min(series),
                    0.0,
                    f"{rname}/{cname} price moved at equilibrium",
                )

    def test_matter_is_conserved_through_the_plant(self):
        """Steel drawn to rebuild machines is a declared sink, not a leak."""
        economy = capital_goods(days=120)
        for name, residual in economy.commodity_balances().items():
            self.assertAlmostEqual(residual, 0.0, places=7, msg=name)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)
        # The value side closes too: plant consumed transfers K/L to the
        # product, plant rebuilt takes materials as circulating capital and
        # construction labor as living labor, and the two cancel.
        self.assertAlmostEqual(economy.value_balance(), 0.0, places=6)
        for name in (STEEL, WOOD, COMPONENTS):
            self.assertGreater(
                economy.ledger.capital_replacement.get(name, 0.0), 0.0
            )

    def test_department_one_has_a_positive_stationary_output(self):
        """Without this, nothing in the price system's plant term is defined."""
        economy = capital_goods(days=120)
        output = economy.department_one_output()
        draw = economy.capital_bill_draw()
        self.assertEqual(sorted(output), sorted([COMPONENTS, STEEL, WOOD]))
        for name in (STEEL, WOOD, COMPONENTS):
            self.assertGreater(output[name], 0.0)
            self.assertGreater(draw[name], 0.0)
        # Wood and components are used for nothing but plant, so in a
        # stationary state their output *is* the replacement draw.
        for name in (WOOD, COMPONENTS):
            self.assertAlmostEqual(output[name], draw[name], places=12)
        # Steel is also a component input, so its output exceeds the draw.
        self.assertGreater(output[STEEL], draw[STEEL])

    def test_the_value_solve_closes_the_machining_table_cycle(self):
        """Components need components, and the solve has to survive it."""
        economy = capital_goods(days=120)
        # Pure labor with nothing behind it: the closed analysis, to within
        # the last bit of an output-weighted average over two regions.  The
        # tolerance is twelve orders below the smallest leak that could
        # matter — the least fixed capital any sector carries is 0.65% —
        # so it still fails loudly if plant reaches a sector that has none.
        for name, authored in ((STEEL, 47.5), (WOOD, 22.5)):
            with self.subTest(commodity=name):
                self.assertLess(
                    abs(economy.labor_values[name] - authored) / authored, 1e-12
                )
        # Components carry the fixed capital RimWorld's formula omits, so
        # they must come out *above* the authored 5570 and not far above.
        solved = economy.labor_values[COMPONENTS]
        self.assertGreater(solved, 5570.0)
        self.assertLess(solved, 5570.0 * 1.05)

    def test_the_price_of_production_identity_holds_sector_by_sector(self):
        """p = cost + r * advance, with the plant counted once in each.

        The failure this guards against is the one docs/36 section 7 named:
        charging the rate of profit on the standing plant *and* again on a
        turnover-inflated depreciation flow.  Checking the aggregate would
        not catch it, because an aggregate can be made to balance by a
        compensating error; every sector separately cannot.
        """
        economy = capital_goods(days=120)
        result = economy.prices_of_production()
        prices = result["prices"]
        rate = result["profit_rate"]
        life = economy.capital_service_life_days
        inputs, labor, output = economy.social_technique()
        bundle = economy.social_wage_bundle()
        plant_bill, plant_labor = economy.social_fixed_capital()
        wage = sum(per * prices[name] for name, per in bundle.items())
        self.assertTrue(plant_bill, "no plant means this proves nothing")
        for name in sorted(output):
            with self.subTest(commodity=name):
                circulating = (
                    sum(
                        quantity * prices[other]
                        for other, quantity in inputs.get(name, {}).items()
                    )
                    + labor[name] * wage
                )
                plant = (
                    sum(
                        quantity * prices[other]
                        for other, quantity in plant_bill.get(name, {}).items()
                    )
                    + plant_labor.get(name, 0.0) * wage
                )
                cost = circulating + plant / life
                advance = result["turnover_days"][name] * cost + plant
                self.assertAlmostEqual(
                    (cost + rate * advance) / prices[name], 1.0, places=10
                )

    def test_fixed_capital_makes_the_capital_goods_basic(self):
        """Sraffa's distinction, and the reason the profit rate moves.

        Steel does not enter herbal medicine directly - the plant pot is
        wood - so it is basic only through the wage bundle: steel enters
        the provisioner's stove, the stove enters meals, and meals enter
        every sector that employs labor.
        """
        basics = capital_goods(days=120).prices_of_production()["basics"]
        for name in (STEEL, WOOD, COMPONENTS):
            self.assertIn(name, basics)
        # Nothing consumes leaves or yayo but yayo and final demand.
        self.assertNotIn(LEAVES, basics)
        self.assertNotIn(YAYO, basics)

    def test_capacity_is_not_built_out_of_nothing(self):
        """A region short of the bill cannot rebuild, and loses what it has.

        Stated as a difference rather than an absence.  Checking only that a
        stripped region builds nothing would pass even if investment were
        blocked for some unrelated reason, so the same shock is run twice
        and the stocked region has to rebuild.

        The stripped region does not merely fail to rebuild: it sheds the
        wear it could not replace, at 1/L a day, which is the debt docs/37
        section 7 named and docs/38 pays.
        """

        def rebuild(strip_bill):
            economy = capital_goods(days=60)
            region = economy.regions["Dust Basin"]
            economy.destroy_capacity("Dust Basin", MEALS, 0.6)
            for _ in range(60):
                if strip_bill:
                    for name in (STEEL, WOOD, COMPONENTS):
                        region.inventory[name] = 0.0
                economy.step(1)
            return region.capacity(MEALS), len(region.projects)

        stocked_capacity, stocked_projects = rebuild(False)
        stripped_capacity, stripped_projects = rebuild(True)
        # The provisioner is 80 steel and 2 components a machine, so with
        # the materials the region rebuilds and without them it cannot.
        self.assertGreater(stocked_capacity, 0.4)
        self.assertGreater(stocked_projects, 0)
        self.assertEqual(stripped_projects, 0)
        # Sixty days of unreplaced wear on 0.4 of capacity: the closed form
        # is 0.4 * (1 - 1/600) ** 60, and the model must land on it.
        self.assertAlmostEqual(
            stripped_capacity, 0.4 * (1.0 - 1.0 / 600.0) ** 60, places=9
        )

    def test_capacity_lost_is_proportional_to_the_shortfall(self):
        """Half the supply must lose part of the wear, not all of it or none.

        The rule docs/38 works under is proportional and damped; a threshold
        would show up here as a step, and a step is what this excludes.

        The stock is set to a share of the day's *requirement*, not a share
        of the inventory: inventory is twenty days of throughput, so halving
        it still covers a day's draw and rations nothing.  Getting that wrong
        is what the first version of this test did.
        """
        goods = (STEEL, WOOD, COMPONENTS)

        def daily_requirement():
            economy = capital_goods(days=60)
            before = {
                name: economy.ledger.intermediate_consumption.get(name, 0.0)
                for name in goods
            }
            economy.step(1)
            return {
                name: (
                    economy.ledger.intermediate_consumption.get(name, 0.0)
                    - before[name]
                )
                # Two regions draw on the ledger; one region's share is half.
                / 2.0
                for name in goods
            }

        need = daily_requirement()
        losses = {}
        for share in (0.0, 0.5, 1.0):
            economy = capital_goods(days=60)
            region = economy.regions["Dust Basin"]
            before = region.capacity(MEALS)
            for _ in range(30):
                for name in goods:
                    region.inventory[name] = need[name] * share
                economy.step(1)
            losses[share] = before - region.capacity(MEALS)
        self.assertGreater(losses[0.0], 0.0)
        self.assertGreater(losses[0.5], 0.0)
        self.assertLess(losses[0.5], losses[0.0])

    def test_steel_and_wood_can_never_lose_capacity(self):
        """They have no plant, so there is no wear for matter to refuse.

        Asserted on the ledger rather than on the capacity, because a steel
        shortage raises the steel price and `_invest` may well *build* steel
        capacity in response.  What must never happen is a loss.
        """
        economy = capital_goods(days=60)
        region = economy.regions["Dust Basin"]
        for _ in range(60):
            for name in (STEEL, WOOD, COMPONENTS):
                region.inventory[name] = 0.0
            economy.step(1)
        for name in (STEEL, WOOD):
            self.assertNotIn(name, economy.ledger.capacity_lost)
        # And the sectors that do carry plant must have lost some, or this
        # proves nothing about the sectors that do not.
        self.assertGreater(economy.ledger.capacity_lost.get(MEALS, 0.0), 0.0)


class CapacityExitTests(unittest.TestCase):
    """Competition for survival, not only for orders (docs/38).

    Capacity falls by exactly the part of a day's wear that was not made
    good, and nothing else moves it.  The money rule is off by default
    because turning it on shrinks the component sector by a factor of
    thirty, which is a consequence of RimWorld pricing a component below
    what one costs to make (docs/37 section 6).
    """

    def test_the_rule_is_off_by_default(self):
        """Off must mean bit-identical, not merely inactive."""
        economy = capital_goods(days=240)
        self.assertFalse(economy.capacity_exit)
        self.assertEqual(economy.ledger.capacity_lost, {})
        for region in economy.regions.values():
            for producer in region.producers:
                self.assertEqual(
                    economy.maintenance_coverage(region, producer), 1.0
                )

    def test_a_loss_making_sector_decays_at_exactly_one_over_the_life(self):
        """No margin covers no maintenance, so none of the wear is replaced.

        Components lose 6.12 silver on a 32-silver product (docs/37 section
        6), so their coverage is zero and their capacity follows the closed
        form exactly while that stays true.
        """
        economy = capacity_exit(days=250)
        region = economy.regions["Dust Basin"]
        self.assertAlmostEqual(
            region.capacity(COMPONENTS),
            0.0625 * (1.0 - 1.0 / 600.0) ** 250,
            places=9,
        )
        # And nothing else moved: every other sector covers its maintenance
        # many times over, so its plant is replaced and its capacity holds.
        self.assertEqual(sorted(economy.ledger.capacity_lost), [COMPONENTS])

    def test_exit_stops_when_the_price_makes_the_survivor_viable(self):
        """The sector is disciplined, not deleted.

        Capacity contracts, utilization rises, the price rises with it, and
        the decay stops at the point where the margin covers the day's
        maintenance.  This is the whole result of docs/39 and the design
        predicted the opposite — a cascade — so it is pinned here.
        """
        economy = capacity_exit(days=4000)
        region = economy.regions["Dust Basin"]
        machinists = [
            producer
            for producer in region.producers
            if producer.commodity == COMPONENTS
        ]
        self.assertEqual(len(machinists), 1)
        producer = machinists[0]
        self.assertTrue(producer.active)
        # Shrunk by roughly thirty times, not to zero.
        self.assertLess(producer.capacity_per_day, 0.0625 / 20.0)
        self.assertGreater(producer.capacity_per_day, 0.0)
        # Still producing what the circuit asks of it.
        self.assertGreater(producer.last_runs, 0.0)
        # The price rose above the cost that had been sinking it.
        self.assertGreater(
            region.prices[COMPONENTS],
            producer.effective_unit_cost(region.prices),
        )
        # And that is exactly why it stopped.
        self.assertEqual(economy.maintenance_coverage(region, producer), 1.0)

    def test_the_end_state_is_a_stationary_equilibrium(self):
        """The economy finds a rest point it was not seeded at."""
        economy = capacity_exit(days=4000)
        region = economy.regions["Dust Basin"]
        prices = dict(region.prices)
        capacity = {name: region.capacity(name) for name in economy.commodities}
        economy.step(400)
        for name in sorted(economy.commodities):
            with self.subTest(commodity=name):
                self.assertAlmostEqual(
                    region.prices[name], prices[name], places=12
                )
                self.assertAlmostEqual(
                    region.capacity(name), capacity[name], places=12
                )

    def test_the_ledgers_still_close_after_four_thousand_days(self):
        economy = capacity_exit(days=4000)
        for name, residual in economy.commodity_balances().items():
            self.assertAlmostEqual(residual, 0.0, places=6, msg=name)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=6)
        produced = sum(
            economy.ledger.value_produced.get(name, 0.0)
            for name in economy.regions
        )
        # Relative, because four thousand days of double-precision addition
        # accumulates: 2e-13 of the value produced is rounding, not a leak.
        self.assertLess(abs(economy.value_balance()) / produced, 1e-11)


class RecreationBasketTests(unittest.TestCase):
    """The workers' basket includes the good the workers make (docs/40).

    The scenario exists to fire the standing prediction docs/37 section 8
    left in writing.  It fired, and the prediction was half right: the
    fixed capital in yayo and psychoid leaves does stop being inert, and it
    does not move the rate of profit anywhere near "a long way" (docs/41).
    """

    def test_off_by_default(self):
        self.assertNotIn(YAYO, ScenarioParameters().subsistence_basket)
        self.assertIn(YAYO, ScenarioParameters(recreation_basket=True).subsistence_basket)

    def test_every_commodity_becomes_basic(self):
        """Yayo through the wage bundle, leaves through yayo."""
        economy = recreation_basket(days=120)
        basics = economy.prices_of_production()["basics"]
        self.assertEqual(sorted(basics), sorted(economy.commodities))
        # And the comparison case still has two non-basics, or this proves
        # nothing about what changed.
        self.assertEqual(
            len(capital_goods(days=120).prices_of_production()["basics"]), 7
        )

    def test_the_equilibrium_is_exactly_stationary(self):
        """The first self-referential price in the model, and still exact."""
        economy = recreation_basket(days=2 * DAYS_PER_YEAR)
        for rname in economy.regions:
            for cname in economy.commodities:
                series = economy.series(rname, cname)
                self.assertEqual(
                    max(series) - min(series),
                    0.0,
                    f"{rname}/{cname} price moved at equilibrium",
                )

    def test_the_ledgers_close(self):
        economy = recreation_basket(days=240)
        for name, residual in economy.commodity_balances().items():
            self.assertAlmostEqual(residual, 0.0, places=7, msg=name)
        self.assertAlmostEqual(economy.cash_balance(), 0.0, places=7)
        self.assertAlmostEqual(economy.value_balance(), 0.0, places=5)

    def test_the_value_of_labor_power_rises_and_the_rate_of_surplus_falls(self):
        """A more expensive basket against an unchanged working day.

        Written the wrong way round in docs/40 section 6 - as `s/v` rising -
        and corrected in the same document's predictions before the code
        existed.  Necessary labor is the basket at *labor values*, so adding
        yayo at 736 ticks makes labor-power dearer, not cheaper.
        """
        before = capital_goods(days=240).rate_of_surplus_value()
        after = recreation_basket(days=240).rate_of_surplus_value()
        self.assertLess(after, before)
        self.assertAlmostEqual(after, 25.31, places=1)

    def test_the_profit_rate_slides_rather_than_stepping(self):
        """The result of docs/41, and the thing that decides the mechanism.

        Basicness flips at the first positive quantity; the wage rises
        continuously with it.  A step at the bottom of the sweep would mean
        basicness was doing the work.  It is not: at one part in four
        thousand of a yayo per worker-day, every commodity is already basic
        and the rate of profit has moved by less than a tenth of a percent.
        """
        rows = recreation_sweep(quantities=[2.0 ** -12, 2.0 ** -6, 2.0 ** -2])
        for row in rows:
            self.assertEqual(row["basics"], 9)
        without = capital_goods(days=120).prices_of_production()["profit_rate"]
        # Basic everywhere, and yet barely moved.
        self.assertLess(
            abs(rows[0]["profit_rate"] - without) / without, 0.001
        )
        # And then it keeps sliding, which is the wage and not the category.
        self.assertLess(rows[1]["profit_rate"], rows[0]["profit_rate"])
        self.assertLess(rows[2]["profit_rate"], rows[1]["profit_rate"])
        # A quarter of a yayo a worker-day takes a third off the rate of
        # profit, where making every commodity basic took a tenth of a
        # percent.  That contrast is the finding.
        self.assertLess(rows[2]["profit_rate"], 0.75 * without)

    def test_the_inert_fixed_capital_stops_being_inert(self):
        """docs/37 section 8's standing prediction, fired.

        In the capital-goods circuit, stripping the plant out of yayo and
        psychoid leaves - 89.6% of the economy's fixed capital - moves the
        rate of profit by 6e-13.  Once they are basic it moves it for real,
        and the point of this test is that the effect is *small*: basicness
        is what lets a sector's plant matter, and the plant-to-cost ratio is
        what decides how much.
        """
        economy = recreation_basket(days=120)
        full = economy.prices_of_production()["profit_rate"]
        original = economy.social_fixed_capital

        def stripped(*, use_capacity=False):
            bill, labor = original(use_capacity=use_capacity)
            drop = {YAYO, LEAVES}
            return (
                {k: v for k, v in bill.items() if k not in drop},
                {k: v for k, v in labor.items() if k not in drop},
            )

        economy.social_fixed_capital = stripped
        try:
            without = economy.prices_of_production()["profit_rate"]
        finally:
            del economy.social_fixed_capital
        # It matters now, where before it did not at all.
        self.assertGreater(without, full)
        # But by a few percent, not "a long way".
        self.assertLess((without - full) / full, 0.10)


class AbsoluteRentTests(unittest.TestCase):
    """Marx's condition for absolute rent, tested rather than assumed (docs/42).

    Absolute rent is the part of a low-composition sector's surplus value
    that landed property stops the price system redistributing away.  Its
    ceiling is what the price system is taking, so the whole account rests
    on a below-average organic composition implying a value above the price
    of production.  These check that implication rather than granting it.
    """

    def test_the_deviations_sum_to_zero(self):
        """Redistribution through prices creates no value (docs/42 s5.4).

        Under the labor-value numeraire total price equals total value by
        construction, so the positives and negatives must cancel exactly.
        This is the quantitative form of rent being a deduction from surplus
        value rather than an addition to it.
        """
        for economy in (equilibrium(days=240), capital_goods(days=240)):
            with self.subTest(commodities=len(economy.commodities)):
                deviation = economy.price_value_deviation()
                _, _, output = economy.social_technique()
                total = sum(output[n] * deviation[n] for n in deviation)
                value = sum(
                    output[n] * economy.labor_values[n] for n in deviation
                )
                self.assertLess(abs(total) / value, 1e-12)

    def test_composition_ranks_the_deviation_without_fixed_capital(self):
        """Marx's step 2, and it holds exactly in a circulating economy."""
        economy = equilibrium(days=240)
        composition = economy.sector_organic_composition()
        prices = economy.prices_of_production()["prices"]
        rows = sorted(
            (composition[n], prices[n] / economy.labor_values[n])
            for n in composition
        )
        for lower, higher in zip(rows, rows[1:]):
            self.assertLessEqual(lower[1], higher[1])

    def test_fixed_capital_breaks_that_ranking(self):
        """And it is the result of docs/43, so it is pinned.

        A sector's markup over cost depends on its plant-to-cost ratio,
        which is a different ratio from its organic composition.  Sectors
        heavy in plant relative to their circulating cost move up the
        ranking - chemfuel at 56 days of it against a 21-day turnover - and
        sectors light in it move down, which is garments at 0.6 days.
        """
        economy = capital_goods(days=240)
        composition = economy.sector_organic_composition()
        prices = economy.prices_of_production()["prices"]
        deviation = {
            n: prices[n] / economy.labor_values[n] for n in composition
        }
        rows = sorted((composition[n], deviation[n]) for n in composition)
        self.assertFalse(
            all(a[1] <= b[1] for a, b in zip(rows, rows[1:])),
            "fixed capital no longer breaks the ranking; docs/43 is stale",
        )
        # Chemfuel is the clearest case: a fifteenth of garments' organic
        # composition and a twentieth of psychoid leaves', and it sells
        # further above its cost than either.
        self.assertLess(composition[CHEMFUEL], composition[GARMENTS])
        self.assertLess(composition[CHEMFUEL], composition[LEAVES])
        self.assertGreater(deviation[CHEMFUEL], deviation[GARMENTS])
        self.assertGreater(deviation[CHEMFUEL], deviation[LEAVES])
        # And garments is the mirror image: the highest composition of the
        # three and the lowest deviation, because its plant is a wooden
        # bench worth 0.6 days of its own cost.
        self.assertLess(deviation[GARMENTS], deviation[MEALS])

    def test_the_bound_needs_a_landlord_and_a_deduction(self):
        """Only reserve-holding commodities, and only where value exceeds price."""
        economy = capital_goods(days=240)
        bound = economy.absolute_rent_bound()
        deviation = economy.price_value_deviation()
        # A landlord is a reserve; chemfuel is the only one in this circuit.
        self.assertEqual(sorted(bound), [CHEMFUEL])
        self.assertGreater(bound[CHEMFUEL], 0.0)
        # And a sector selling above its value has nothing withheld from it.
        self.assertGreater(deviation[YAYO], 0.0)
        self.assertNotIn(YAYO, bound)

    def test_the_chemfuel_bound_is_three_quarters_of_its_value(self):
        """docs/42 s5.2 predicted roughly 75%; this pins what it turned out to be."""
        economy = capital_goods(days=240)
        prices = economy.prices_of_production()["prices"]
        share = 1.0 - prices[CHEMFUEL] / economy.labor_values[CHEMFUEL]
        self.assertAlmostEqual(share, 0.757, places=2)

    def test_variable_capital_is_the_value_of_labor_power(self):
        """Not the money wage, which would be a price wearing a value's name.

        docs/42 s7 named this as the fourth place the project could make a
        substitution it has already made three times.  A composition built
        on the silver wage would move when prices moved; this one must not.
        """
        economy = capital_goods(days=240)
        before = economy.sector_organic_composition()
        for region in economy.regions.values():
            for name in region.prices:
                region.prices[name] *= 2.0
        after = economy.sector_organic_composition()
        for name in before:
            with self.subTest(commodity=name):
                self.assertEqual(before[name], after[name])


class WageDeviationTests(unittest.TestCase):
    """Wages off the value of labor-power, regulated by the reserve army (docs/46).

    The wage has been the basket at current prices since docs/17; the value
    of labor-power is the same basket at social labor values.  The rule lets
    the first move with the employment rate while the second stays put, and
    every test here is some form of "the wage moved and the value did not".
    """

    def test_off_by_default(self):
        """The default is wages at value, and the paid wage is the basket."""
        self.assertEqual(ScenarioParameters().wage_bargaining_strength, 0.0)
        economy = demand_boom(days_after_boom=30)
        for region in economy.regions.values():
            with self.subTest(region=region.name):
                self.assertEqual(region.wage_premium, 0.0)
                self.assertEqual(region.wage_rate(), region.basket_cost())
        self.assertEqual(economy.ledger.wage_premium_paid, {})
        self.assertEqual(
            economy.realized_rate_of_surplus_value("Dust Basin"),
            economy.rate_of_surplus_value("Dust Basin"),
        )

    def test_the_rule_is_exactly_stationary_where_the_circuit_is(self):
        """docs/46 s2: the reference is the seeded rate on the identical float.

        The equilibrium scenario must keep its exactly-zero price range with
        bargaining switched on.  If this ever fails the rule has an
        asymmetry and the check is not to be loosened.
        """
        parameters = replace(ScenarioParameters(), wage_bargaining_strength=1.0)
        economy = equilibrium(days=240, parameters=parameters)
        for entry in economy.history:
            for name, region in entry["regions"].items():
                self.assertEqual(region["wage_premium"], 0.0, name)
        prices = economy.series("Dust Basin", YAYO)
        self.assertEqual(max(prices) - min(prices), 0.0)

    def test_an_infinite_reserve_army_pins_the_wage_to_value(self):
        """Marx's limiting case, and it is the arithmetic of the rate."""
        economy = demand_boom(bargaining=True, labor_pool=float("inf"))
        for entry in economy.history:
            self.assertEqual(entry["regions"]["Dust Basin"]["wage_premium"], 0.0)

    def test_the_boom_lifts_the_wage_and_not_the_value(self):
        """docs/46 s5.2 and s5.3.

        The premium is positive and lags the employment it follows.  The
        value of labor-power is read in both runs: docs/46 predicted
        identity to the bit and docs/47 measured one ulp, because the value
        solve's output weights differ between two runs whose investment
        differs.  The bound here is float noise, not equality, and the
        difference is recorded there rather than hidden here.
        """
        without = demand_boom()
        with_rule = demand_boom(bargaining=True)
        premium = [h["regions"]["Dust Basin"]["wage_premium"] for h in with_rule.history]
        employment = [h["regions"]["Dust Basin"]["employment"] for h in with_rule.history]
        self.assertGreater(max(premium), 0.05)
        self.assertGreaterEqual(premium.index(max(premium)), employment.index(max(employment)))
        value_off = without.basket_labor_value(without.regions["Dust Basin"])
        value_on = with_rule.basket_labor_value(with_rule.regions["Dust Basin"])
        self.assertLess(abs(value_on - value_off) / value_off, 1e-12)

    def test_the_premium_is_a_deduction_from_surplus_value(self):
        """docs/46 s3: the living labor is what it was; the line moved.

        Above value the realized rate sits below the value rate; below
        value it sits above it.  The value rate itself is a ratio of two
        labor-time quantities the premium never touches.
        """
        boom = demand_boom(bargaining=True)
        self.assertLess(
            boom.realized_rate_of_surplus_value("Dust Basin"),
            boom.rate_of_surplus_value("Dust Basin"),
        )
        self.assertGreater(boom.ledger.wage_deviation_labor["Dust Basin"], 0.0)
        slump = wage_slump()
        self.assertGreater(
            slump.realized_rate_of_surplus_value("Dust Basin"),
            slump.rate_of_surplus_value("Dust Basin"),
        )
        self.assertLess(slump.ledger.wage_deviation_labor["Dust Basin"], 0.0)

    def test_the_slump_pushes_the_wage_below_value_and_lets_it_back(self):
        """docs/46 s5.6: negative, brief, and gone within a hundred days."""
        economy = wage_slump()
        premium = [h["regions"]["Dust Basin"]["wage_premium"] for h in economy.history]
        trough = min(premium)
        self.assertLess(trough, -0.05)
        trough_day = premium.index(trough)
        self.assertLess(abs(premium[trough_day + 100]), 0.01)

    def test_the_ledgers_close_with_a_premium(self):
        """docs/46 s5.8: the premium is spent, not hoarded."""
        for economy in (demand_boom(bargaining=True), wage_slump()):
            with self.subTest(day=economy.day):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-6)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)

    def test_the_reserve_army_sets_the_magnitude(self):
        """docs/46 s5.5: half the pool, roughly twice the premium."""
        sweep = reserve_army_sweep(pools=(1.0, 0.5))
        peaks = {
            pool: max(
                h["regions"]["Dust Basin"]["wage_premium"] for h in economy.history
            )
            for pool, economy in sweep.items()
        }
        ratio = peaks[0.5] / peaks[1.0]
        self.assertGreater(ratio, 1.7)
        self.assertLessEqual(ratio, 2.0)


class HabituationTests(unittest.TestCase):
    """A sustained premium becomes the value of labor-power (docs/51).

    The paid wage is the reserve army's business and this rule never touches
    it.  What moves is the habitual standard the value of labor-power is
    read against, so every test here is some form of "the value moved and
    the wage did not" -- the mirror of docs/46.
    """

    @classmethod
    def setUpClass(cls):
        cls.pinned = demand_boom()
        cls.bargaining = demand_boom(bargaining=True)
        cls.habituated = demand_boom(habituation=True)

    def test_off_by_default(self):
        """No standard forms, and every reading is the bargaining reading."""
        self.assertEqual(ScenarioParameters().habituation_speed, 0.0)
        for entry in self.bargaining.history:
            for name, region in entry["regions"].items():
                self.assertEqual(region["habitual_scale"], 1.0, name)
                self.assertEqual(
                    region["premium_over_value"], region["wage_premium"], name
                )
        dust = self.bargaining.regions["Dust Basin"]
        self.assertEqual(
            self.bargaining.value_of_labor_power(dust),
            self.bargaining.basket_labor_value(dust),
        )

    def test_both_rules_are_exactly_stationary_where_the_circuit_is(self):
        """docs/51 s5.2: the gap is exactly zero, so the standard never moves."""
        parameters = replace(
            ScenarioParameters(),
            wage_bargaining_strength=1.0,
            habituation_speed=0.02,
        )
        economy = equilibrium(days=240, parameters=parameters)
        for entry in economy.history:
            for name, region in entry["regions"].items():
                self.assertEqual(region["habitual_scale"], 1.0, name)
        prices = economy.series("Dust Basin", YAYO)
        self.assertEqual(max(prices) - min(prices), 0.0)

    def test_the_standard_follows_the_premium_without_overshoot(self):
        """docs/51 s5.3: a lag behind the premium, never above it."""
        scale = [h["regions"]["Dust Basin"]["habitual_scale"] for h in self.habituated.history]
        premium = [h["regions"]["Dust Basin"]["wage_premium"] for h in self.habituated.history]
        self.assertGreater(scale[-1], 1.05)
        self.assertLessEqual(max(scale), 1.0 + max(premium))
        for earlier, later in zip(scale, scale[1:]):
            self.assertGreaterEqual(later, earlier)

    def test_the_premium_over_value_is_absorbed(self):
        """docs/51 s5.4: what the paid wage still carries above the standard."""
        dust = self.habituated.regions["Dust Basin"]
        self.assertGreater(dust.wage_premium, 0.05)
        self.assertLess(dust.premium_over_value(), 0.015)
        self.assertGreater(dust.premium_over_value(), 0.0)

    def test_the_value_moved_and_the_premium_did_not(self):
        """docs/51 s5.5, the mirror of docs/46's claim -- and docs/52 s3.

        The rule never touches the premium, and the premium is the same to
        within a percent.  The *money* wage is not: docs/51 predicted it
        within 1% and it moved 3%, because the buffer target following the
        standard takes most of docs/47's demand-channel price rise out of
        the wage goods.  The meal price lands between the wage-at-value run
        and the bargaining-only run, and that ordering is the finding.
        """
        habit = self.habituated.regions["Dust Basin"]
        bargained = self.bargaining.regions["Dust Basin"]
        pinned = self.pinned.regions["Dust Basin"]
        value_ratio = self.habituated.value_of_labor_power(habit) / (
            self.bargaining.value_of_labor_power(bargained)
        )
        self.assertGreater(value_ratio, 1.05)
        self.assertLess(value_ratio, 1.08)
        self.assertLess(
            abs(habit.wage_premium / bargained.wage_premium - 1.0), 0.02
        )
        wage_ratio = habit.wage_rate() / bargained.wage_rate()
        self.assertLess(abs(wage_ratio - 1.0), value_ratio - 1.0)
        self.assertLess(pinned.prices[MEALS], habit.prices[MEALS])
        self.assertLess(habit.prices[MEALS], bargained.prices[MEALS])

    def test_the_value_rate_falls_toward_the_realized_rate(self):
        """docs/51 s5.6: the line moved the other way; the wage as paid is the same."""
        self.assertLess(
            self.habituated.rate_of_surplus_value("Dust Basin"),
            self.bargaining.rate_of_surplus_value("Dust Basin"),
        )
        realized = self.habituated.realized_rate_of_surplus_value("Dust Basin")
        reference = self.bargaining.realized_rate_of_surplus_value("Dust Basin")
        self.assertLess(abs(realized - reference) / reference, 0.005)
        # v + s is the living labor whatever the split.
        self.assertLess(abs(self.habituated.value_balance()), 1e-6)

    def test_the_general_rate_of_profit_falls(self):
        """docs/51 s5.7: the standard is the long-run real wage the price system reads."""
        with_habit = self.habituated.prices_of_production()["profit_rate"]
        without = self.bargaining.prices_of_production()["profit_rate"]
        self.assertLess(with_habit, without)
        self.assertGreater(with_habit / without, 0.90)

    def test_the_reversal_leaves_the_wage_below_value(self):
        """docs/51 s5.9: the standard stays, the wage falls back, and the
        slump ordering appears in a region that is not in crisis."""
        economy = boom_reversal(habituation=True)
        scale = [h["regions"]["Dust Basin"]["habitual_scale"] for h in economy.history]
        premium = [h["regions"]["Dust Basin"]["wage_premium"] for h in economy.history]
        reversal = ScenarioParameters().boom_reversal_day
        self.assertGreater(scale[reversal], 1.015)
        # Upward only: the standard keeps forming for the few days the
        # premium is still above it after demand reverses, then stops.
        for earlier, later in zip(scale, scale[1:]):
            self.assertGreaterEqual(later, earlier)
        self.assertLess(scale[-1] - scale[reversal], 0.005)
        settled = next(
            day for day in range(reversal, len(scale))
            if 1.0 + premium[day] <= scale[day]
        )
        self.assertEqual(scale[-1], scale[settled])
        dust = economy.regions["Dust Basin"]
        self.assertLess(abs(dust.wage_premium), 1e-3)
        self.assertLess(dust.premium_over_value(), -0.015)
        self.assertGreater(
            economy.realized_rate_of_surplus_value("Dust Basin"),
            economy.rate_of_surplus_value("Dust Basin"),
        )
        # Without the rule the wage is back at value: the premium is gone
        # and there is no standard for it to sit below.
        without = boom_reversal(habituation=False)
        other = without.regions["Dust Basin"]
        self.assertLess(abs(other.wage_premium), 1e-3)
        self.assertEqual(other.premium_over_value(), other.wage_premium)

    def test_the_ledgers_close_with_a_standard(self):
        """docs/51 s5.10."""
        for economy in (self.habituated, boom_reversal(habituation=True)):
            with self.subTest(day=economy.day):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-6)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)


class ProducerCashTests(unittest.TestCase):
    """Producers hold silver, pay from it, and can fail (docs/55).

    The purse reaches prices only through what is produced, so the seeded
    circuit is exactly as stationary with purses as without; what the rule
    adds is a flow where there was a notional, and a discipline for the one
    sector that sells below its cash cost.
    """

    @classmethod
    def setUpClass(cls):
        cls.with_cash = replace(ScenarioParameters(), producer_cash=True)
        cls.stationary = equilibrium(days=240, parameters=cls.with_cash)
        cls.circuit = cash_circuit()

    def test_off_by_default(self):
        """No purse holds anything and no purse is ever read."""
        self.assertFalse(ScenarioParameters().producer_cash)
        economy = equilibrium(days=30)
        for region in economy.regions.values():
            for producer in region.producers:
                self.assertEqual(producer.cash, 0.0)
        self.assertEqual(economy.ledger.distributions, {})
        self.assertEqual(economy.ledger.bankruptcies, [])

    def test_the_circuit_is_exactly_stationary_with_purses(self):
        """docs/55 s6.2: prices see none of it; a purse is set, not subtracted to."""
        prices = self.stationary.series("Dust Basin", YAYO)
        self.assertEqual(max(prices) - min(prices), 0.0)
        purses = [h["regions"]["Dust Basin"]["producer_cash"] for h in self.stationary.history]
        self.assertGreater(purses[1], 0.0)
        self.assertEqual(len(set(purses[1:])), 1)
        fund = [h["regions"]["Dust Basin"]["cash"] for h in self.stationary.history]
        self.assertLess(abs(fund[-1] - fund[0]), 1.0)

    def test_nobody_is_rationed_where_every_price_covers_cash_cost(self):
        """docs/55 s6.3."""
        self.assertEqual(self.stationary.ledger.liquidity_curtailment, {})
        self.assertEqual(self.stationary.ledger.fund_wage_support, {})
        self.assertEqual(self.stationary.ledger.bankruptcies, [])

    def test_money_profit_is_a_flow_that_matches_the_notional(self):
        """docs/55 s6.7, to the employment quantum: the distribution per day
        is output times price less inputs and wages per unit."""
        region = self.stationary.regions["Dust Basin"]
        for producer in region.producers:
            parts = self.stationary.price_decomposition("Dust Basin", producer.commodity)
            output = producer.last_runs * producer.process.outputs[producer.commodity]
            notional = output * (parts["price"] - parts["inputs"] - parts["wages"])
            flow = producer.distributed_total / self.stationary.day
            with self.subTest(sector=producer.commodity):
                self.assertLess(abs(flow - notional), 1e-4)
                self.assertGreater(flow, 0.0)

    def test_the_sector_that_does_not_pay_is_rationed_not_bankrupted(self):
        """docs/55 s6.4, on a longer clock than the design expected."""
        region = self.circuit.regions["Dust Basin"]
        machinist = next(p for p in region.producers if p.commodity == COMPONENTS)
        prices = self.circuit.series("Dust Basin", COMPONENTS)
        self.assertGreater(sum(self.circuit.ledger.liquidity_curtailment.values()), 0.0)
        self.assertEqual(self.circuit.ledger.bankruptcies, [])
        self.assertTrue(machinist.active)
        self.assertGreater(prices[-1] / 32.0, 1.1)
        self.assertLess(prices[-1] / 32.0, 1.5)
        # A rest point: the price stops moving once yesterday's revenue
        # funds today's runs.
        self.assertLess(abs(prices[-1] - prices[-100]), 1e-6)
        self.assertLess(machinist.cash, machinist.cash_target)

    def test_the_rest_of_department_one_is_untouched(self):
        """docs/55 s6.5."""
        region = self.circuit.regions["Dust Basin"]
        self.assertEqual(self.circuit.ledger.capacity_lost, {})
        for producer in region.producers:
            if producer.commodity == COMPONENTS:
                continue
            with self.subTest(sector=producer.commodity):
                self.assertEqual(producer.cash, producer.cash_target)
                self.assertNotIn(producer.commodity, self.circuit.ledger.liquidity_curtailment)

    def test_the_boom_is_funded(self):
        """docs/55 s6.6."""
        with_cash = demand_boom(parameters=self.with_cash)
        without = demand_boom()
        gap = abs(
            with_cash.regions["Dust Basin"].worker_days_earned
            - without.regions["Dust Basin"].worker_days_earned
        )
        self.assertLess(gap / without.regions["Dust Basin"].worker_days_earned, 0.02)
        fund = [h["regions"]["Dust Basin"]["cash"] for h in with_cash.history]
        self.assertGreater(min(fund), 0.0)

    def test_silver_conserves_with_purses_inside_the_identity(self):
        """docs/55 s6.8."""
        for economy in (self.stationary, self.circuit, demand_boom(parameters=self.with_cash)):
            with self.subTest(day=economy.day):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-5)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)


class PostedPriceTests(unittest.TestCase):
    """Firm-posted prices (docs/57), experimental and off by default.

    docs/58 found the rule sound where a sector has one producer -- it is
    exactly stationary and passes cost through in full -- and unsound where
    a sector shares one pool, which is why docs/59 comes next.  The tests
    assert both halves, so that fixing the second cannot quietly change the
    first.
    """

    @classmethod
    def setUpClass(cls):
        cls.posted = replace(ScenarioParameters(), posted_prices=True)
        cls.stationary = equilibrium(days=240, parameters=cls.posted)

    def test_off_by_default(self):
        self.assertFalse(ScenarioParameters().posted_prices)
        economy = equilibrium(days=30)
        for region in economy.regions.values():
            for producer in region.producers:
                self.assertEqual(producer.posted_price, 0.0)

    def test_exactly_stationary_with_posted_prices(self):
        """docs/57 s6.2: identical cost and zero pressure is a factor of exactly one."""
        prices = self.stationary.series("Dust Basin", YAYO)
        self.assertEqual(max(prices) - min(prices), 0.0)
        region = self.stationary.regions["Dust Basin"]
        for producer in region.producers:
            self.assertEqual(producer.posted_price, region.prices[producer.commodity])

    def test_cost_passes_through_in_full(self):
        """docs/58 s3: after the subsistence shock every unshocked sector asks
        the markup it was seeded at, to four decimals."""
        shocked = subsistence_shock(parameters=self.posted)
        seeded_region = self.stationary.regions["Dust Basin"]
        region = shocked.regions["Dust Basin"]
        seeded = {
            p.commodity: p.posted_price / p.effective_unit_cost(seeded_region.prices)
            for p in seeded_region.producers
        }
        for producer in region.producers:
            if producer.commodity == MEALS or not producer.active:
                continue
            markup = producer.posted_price / producer.effective_unit_cost(region.prices)
            with self.subTest(sector=producer.commodity):
                # The two other basket goods drift by 0.0016: their own
                # stock moves when the wage does.  Everything else is exact
                # to four decimals.
                self.assertLess(abs(markup - seeded[producer.commodity]), 5e-3)
        self.assertGreater(region.prices[YAYO], seeded_region.prices[YAYO] * 1.1)

    def test_a_shock_leaves_its_level_behind(self):
        """docs/58 s4: an integrated pressure rests where the stock reaches
        target, which is not where the price started."""
        glut = regional_glut(parameters=self.posted)
        prices = glut.series("Dust Basin", YAYO)
        self.assertLess(min(prices), 21.0 * 0.9)
        self.assertGreater(prices[-1], 21.0 * 1.1)

    def test_a_contested_sector_converges_once_the_entrant_asks_the_going_price(self):
        """docs/58 s5a: the divergence s5 reported was an entrant clamped to
        18% of its cost; asking the going price from its first day, the two
        provisioners end within a hundredth of a percent of each other."""
        economy = technique_change(parameters=self.posted)
        asked = [
            p.posted_price
            for p in economy.regions["Dust Basin"].producers
            if p.active and p.commodity == MEALS
        ]
        self.assertLess(max(asked) / min(asked) - 1.0, 1e-3)

    def test_the_ledgers_close(self):
        for economy in (self.stationary, regional_glut(parameters=self.posted), producer_loss(parameters=self.posted)):
            with self.subTest(day=economy.day):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-5)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)


class ProcurementTests(unittest.TestCase):
    """Producers own their output and buy their inputs (docs/59).

    No sector request and no fixed point: each producer plans from its own
    sales and stock, buys from the cheapest sellers it can afford with
    custom split continuously by price, and asks a price that answers its
    own excess and its own sell-outs.  Off by default; needs purses and
    posted prices.
    """

    @classmethod
    def setUpClass(cls):
        cls.market = replace(
            ScenarioParameters(), producer_cash=True, posted_prices=True, procurement=True
        )
        cls.stationary = equilibrium(days=240, parameters=cls.market)

    def test_off_by_default_and_needs_its_prerequisites(self):
        self.assertFalse(ScenarioParameters().procurement)
        economy = equilibrium(days=10)
        for region in economy.regions.values():
            for producer in region.producers:
                self.assertEqual(producer.stock, 0.0)
        with self.assertRaises(ValueError):
            equilibrium(days=1, parameters=replace(ScenarioParameters(), procurement=True))

    def test_exactly_stationary_from_the_reseeded_state(self):
        """docs/59 s3 and s6.2; every commodity, not only yayo, since
        docs/62 seeded each producer at its own target."""
        region = self.stationary.regions["Dust Basin"]
        for name, commodity in self.stationary.commodities.items():
            with self.subTest(commodity=name):
                prices = self.stationary.series("Dust Basin", name)
                self.assertEqual(max(prices) - min(prices), 0.0)
                stock = self.stationary.series("Dust Basin", name, field="inventory")
                self.assertEqual(max(stock) - min(stock), 0.0)
        for producer in region.producers:
            self.assertEqual(producer.stock, region.inventory[producer.commodity])
            days = self.stationary.commodities[producer.commodity].target_inventory_days
            self.assertEqual(producer.stock, days * producer.expected_demand)
            for name, held in producer.inputs_on_hand.items():
                self.assertEqual(held, 0.0, name)

    def test_the_identities_close_with_producer_stock_inside_them(self):
        """docs/59 s6.5, in every scenario the readings use."""
        runs = {
            "equilibrium": self.stationary,
            "glut": regional_glut(parameters=self.market),
            "loss": producer_loss(parameters=self.market),
            "boom": demand_boom(parameters=self.market),
            "competition": cost_competition(parameters=self.market),
            "subsistence": subsistence_shock(parameters=self.market),
            "arbitrage": arbitrage(parameters=self.market),
        }
        for label, economy in runs.items():
            with self.subTest(scenario=label):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-5)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)

    def test_a_technique_change_opens_the_value_identity_as_it_always_did(self):
        """Output is valued at the day's opening values (docs/23), so a
        technique mix that moves day to day leaves a residual in the planned
        model too; the market's is the same residual, not a new one."""
        planned = technique_change().value_balance()
        market = technique_change(parameters=self.market).value_balance()
        self.assertGreater(abs(planned), 10.0)
        # The same sign and the same order: the market's mix moves on a
        # different path (docs/62), so the residual is not the same number.
        self.assertGreater(market / planned, 0.5)
        self.assertLess(market / planned, 3.0)

    def test_the_glut_is_a_trough_the_chain_feels_and_the_level_returns(self):
        """docs/62 s4: with every stock target the inventory life of its
        producer's own expected demand, a glut is a trough every stage
        upstream feels, and the sell-outs after it bring the price back
        to within five percent of the reference."""
        prices = regional_glut(parameters=self.market).series("Dust Basin", YAYO)
        self.assertLess(min(prices), 21.0 * 0.8)
        self.assertLess(abs(prices[-1] - 21.0), 21.0 * 0.05)

    def test_a_sector_that_ran_dry_restarts(self):
        """docs/62 s2: a sell-out is noted for every seller with nothing
        left, so a sector every buyer found empty sees the demand that
        restarts it.  Under docs/60 the producer-loss run ended with every
        yayo producer idle, its stock and its sales both zero."""
        economy = producer_loss(parameters=self.market)
        region = economy.regions["Dust Basin"]
        sellers = [p for p in region.producers if p.active and p.commodity == YAYO]
        self.assertGreater(len(sellers), 1)
        for producer in sellers:
            with self.subTest(producer=producer.name):
                self.assertGreater(producer.last_runs, 0.0)
                self.assertGreater(producer.sales_yesterday, 0.0)

    def test_a_cost_advantage_above_the_going_margin_is_used(self):
        """docs/62 s4: the provisioner whose cost leaves it a margin above
        the going one cuts on its idle capacity, asks less than its rival,
        holds the larger share, and the meal price ends at its cost plus
        the going margin.  A two-percent cost advantage (technique_change)
        leaves both below the going margin, and the spread between them
        persists: custom split by a constant elasticity rewards it."""
        economy = cost_competition(parameters=self.market)
        region = economy.regions["Dust Basin"]
        sellers = [p for p in region.producers if p.active and p.commodity == MEALS]
        self.assertEqual(len(sellers), 2)
        cheapest = min(sellers, key=lambda p: p.effective_unit_cost(region.prices))
        other = next(p for p in sellers if p is not cheapest)
        self.assertLess(cheapest.posted_price, other.posted_price)
        self.assertGreater(cheapest.sales_yesterday, other.sales_yesterday)
        floor = cheapest.effective_unit_cost(region.prices) * (1.0 + economy.going_margin)
        self.assertLess(abs(cheapest.posted_price - floor) / floor, 0.02)
        economy = technique_change(parameters=self.market)
        region = economy.regions["Dust Basin"]
        sellers = [p for p in region.producers if p.active and p.commodity == MEALS]
        for producer in sellers:
            self.assertGreater(producer.sales_yesterday, 0.0)

    def test_a_sell_out_raises_and_idle_capacity_brings_the_level_back(self):
        """docs/62 s4: a shortage is priced by the sellers who ran out;
        once capacity is rebuilt and idle, a margin above the going one
        is cut, and the level comes back toward cost plus that margin."""
        prices = producer_loss(parameters=self.market).series("Dust Basin", YAYO)
        self.assertGreater(max(prices), 21.0 * 1.3)
        self.assertLess(prices[-1], max(prices) * 0.85)
        self.assertLess(prices[-1], 21.0 * 1.25)

    def test_an_appended_producer_asks_the_going_price(self):
        """docs/58 s5a: no producer starts at a price of zero."""
        economy = technique_change(days_after_entry=1, parameters=self.market)
        for producer in economy.regions["Dust Basin"].producers:
            if producer.commodity == MEALS:
                self.assertGreater(producer.posted_price, 10.0)


class EntryOnMarginTests(unittest.TestCase):
    """Capital enters a sector because it is profitable, not because it is
    short (docs/61, docs/63), on the corrected market (docs/62).  Off by
    default and bit-identical off; at the default going margin nothing
    seeded fires it.
    """

    @classmethod
    def setUpClass(cls):
        cls.market = replace(
            ScenarioParameters(), producer_cash=True, posted_prices=True, procurement=True
        )
        cls.entry = replace(cls.market, entry_on_margin=True)

    def test_off_by_default_and_silent_where_no_margin_exceeds_the_going_one(self):
        """docs/61 s6.1 and s6.2: the seeded circuit and the glut are the
        market's own runs, to the bit."""
        self.assertFalse(ScenarioParameters().entry_on_margin)
        for fn in (equilibrium, regional_glut):
            with self.subTest(scenario=fn.__name__):
                market = fn(parameters=self.market)
                entry = fn(parameters=self.entry)
                for name in market.commodities:
                    self.assertEqual(
                        market.series("Dust Basin", name), entry.series("Dust Basin", name)
                    )
                self.assertFalse(any(entry.regions["Dust Basin"].entry_backlog.values()))

    def test_a_shortage_draws_entry_that_brings_the_level_below_the_market(self):
        """docs/61 s6.3 at the horizon it set; docs/63 s3 for what the
        pipeline does beyond it.

        The crossing moved out past that horizon when docs/68 let a seller
        emptied by an order see the demand it missed: the market *without*
        entry now answers the shortage through its own producers' plans,
        so at 150 days it is briefly the cheaper of the two and entry has
        only the capacity to show for itself.  By 200 days the claim holds
        again, and the capacity was there the whole time.
        """
        market = producer_loss(parameters=self.market)
        entry = producer_loss(parameters=self.entry)
        prices = entry.series("Dust Basin", YAYO)
        self.assertGreater(
            entry.regions["Dust Basin"].capacity(YAYO), market.regions["Dust Basin"].capacity(YAYO)
        )
        self.assertGreater(prices[-1], 21.0 * 1.05)
        self.assertLess(prices[-1], 21.0 * 1.28)
        later_market = producer_loss(200, parameters=self.market)
        later_entry = producer_loss(200, parameters=self.entry)
        self.assertLess(
            later_entry.series("Dust Basin", YAYO)[-1],
            later_market.series("Dust Basin", YAYO)[-1],
        )

    def test_a_cost_advantage_draws_an_entrant_that_copies_it(self):
        """docs/61 s6.5: the entrant uses the best technique in the sector."""
        economy = cost_competition(parameters=self.entry)
        region = economy.regions["Dust Basin"]
        sellers = [p for p in region.producers if p.active and p.commodity == MEALS]
        self.assertEqual(len(sellers), 3)
        cheapest = min(sellers, key=lambda p: p.effective_unit_cost(region.prices))
        entrant = next(p for p in sellers if p.name.startswith("entrant-"))
        self.assertEqual(entrant.unit_cost, cheapest.unit_cost)
        self.assertIs(entrant.process, cheapest.process)
        cheap_cost = cheapest.effective_unit_cost(region.prices)
        cheap_sales = sum(
            p.sales_yesterday
            for p in sellers
            if abs(p.effective_unit_cost(region.prices) - cheap_cost) < 1e-6
        )
        self.assertGreater(cheap_sales / sum(p.sales_yesterday for p in sellers), 0.6)
        self.assertLess(region.prices[MEALS], 11.0)
        self.assertLess(
            region.prices[MEALS], cost_competition(parameters=self.market).regions["Dust Basin"].prices[MEALS]
        )

    def test_entry_accrues_to_a_project_in_a_small_sector(self):
        """docs/63 s1: a sector of two-thirds of a unit a day, with no
        shortfall, is not barred by the minimum project size; one
        interval's term is below it and the intention accrues."""
        economy = cost_competition(parameters=self.entry)
        region = economy.regions["Dust Basin"]
        provisioners = [p for p in region.producers if p.active and p.commodity == MEALS]
        entrants = [p for p in provisioners if p.name.startswith("entrant-")]
        self.assertEqual(len(entrants), 1)
        incumbents = [p for p in provisioners if p not in entrants]
        self.assertGreaterEqual(
            sum(p.capacity_per_day for p in incumbents), economy.throughput("Dust Basin", MEALS)
        )
        best = min(p.effective_unit_cost(region.prices) for p in incumbents)
        margin = (region.expected_prices[MEALS] - best) / best
        one_interval = (
            economy.entry_gain
            * economy.throughput("Dust Basin", MEALS)
            * max(0.0, margin - economy.going_margin)
            / economy.going_margin
        )
        self.assertLess(one_interval, economy.min_investment_capacity)
        self.assertGreaterEqual(entrants[0].capacity_per_day, economy.min_investment_capacity)

    def test_gravitation_to_the_going_margin(self):
        """docs/61 s6.7: with the going margin inside the authored band,
        every sector in both regions ends near it -- the full-capacity
        sectors by entry, the idle ones by their own cut -- and the
        prices are still."""
        economy = gravitation()
        going = economy.going_margin
        for region in economy.regions.values():
            for name in economy.commodities:
                active = [p for p in region.producers if p.active and p.commodity == name]
                best = min(p.effective_unit_cost(region.prices) for p in active)
                with self.subTest(region=region.name, commodity=name):
                    self.assertLess(abs((region.prices[name] - best) / best - going), 0.07)
                    prices = economy.series(region.name, name)
                    self.assertLess(
                        (max(prices[-60:]) - min(prices[-60:])) / prices[-1], 0.01
                    )
        region = economy.regions["Dust Basin"]
        self.assertGreater(sum(1 for p in region.producers if p.active and p.commodity == YAYO), 1)
        self.assertEqual(sum(1 for p in region.producers if p.active and p.commodity == MEALS), 1)

    def test_the_identities_close(self):
        """docs/61 s6.8."""
        runs = {
            "loss": producer_loss(parameters=self.entry),
            "competition": cost_competition(parameters=self.entry),
            "gravitation": gravitation(),
        }
        for label, economy in runs.items():
            with self.subTest(scenario=label):
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-5)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)


class ExitOnReturnTests(unittest.TestCase):
    """Capital leaves a sector that cannot earn the going return (docs/64,
    docs/65), on the market with entry.

    The retirement clause that deleted the seed's tailors and herbalists
    is fixed (`docs/66`): the withdrawal is floored at the larger of the
    reserve target and the smallest plant the fund would build.  One
    defect remains and one test asserts it as current behaviour rather
    than as intent -- a seller emptied by the order it is answering sees
    no sell-out (`docs/67` s5), and `docs/68` is that fix.
    """

    @classmethod
    def setUpClass(cls):
        cls.market = replace(
            ScenarioParameters(),
            producer_cash=True,
            posted_prices=True,
            procurement=True,
        )
        cls.entry = replace(cls.market, entry_on_margin=True)
        cls.leaving = replace(cls.entry, exit_on_return=True)

    def test_off_by_default_and_needs_procurement(self):
        """docs/64 s2 and s6.1: the flag refuses without procurement, as
        procurement refuses without purses."""
        self.assertFalse(ScenarioParameters().exit_on_return)
        with self.assertRaises(ValueError):
            seeded_two_region_economy(
                parameters=replace(
                    ScenarioParameters(), exit_on_return=True, procurement=False
                )
            )

    def test_a_sector_at_full_utilization_has_no_surplus_to_withdraw(self):
        """docs/64 s3: the cooperative, the fields and the refinery expect
        their whole output, so nothing leaves them and their capacity is
        unchanged to the bit."""
        economy = equilibrium(parameters=self.leaving)
        region = economy.regions["Dust Basin"]
        self.assertEqual(region.capacity(YAYO), 10.0)
        self.assertEqual(region.capacity(LEAVES), 80.0)
        self.assertEqual(economy.regions["Green River"].capacity(YAYO), 10.0)

    def test_the_first_withdrawal_is_on_the_lead_time(self):
        """docs/64 s2: capital leaves on the horizon on which it arrives,
        so no producer withdraws before `investment_lead_days`."""
        economy = equilibrium(parameters=self.leaving)
        self.assertTrue(economy.ledger.exits)
        self.assertEqual(
            min(day for day, _, _, _ in economy.ledger.exits),
            economy.investment_lead_days,
        )

    def test_a_sector_smaller_than_the_minimum_plant_rests_on_the_floor(self):
        """docs/66 s2 and s4.2, replacing the defect this test asserted.

        The tailors want 0.0437 units of plant against a
        `min_investment_capacity` of 0.1, so their reserve target is below
        the smallest plant the fund would build.  The withdrawal stops at
        that floor and the sector survives; before docs/66 the whole plant
        went and nothing could rebuild it.
        """
        economy = equilibrium(parameters=self.leaving)
        for region in economy.regions.values():
            for commodity in (GARMENTS, MEDICINE):
                with self.subTest(region=region.name, commodity=commodity):
                    self.assertEqual(
                        region.capacity(commodity), economy.min_investment_capacity
                    )
                    seller = next(
                        p
                        for p in region.producers
                        if p.active and p.commodity == commodity
                    )
                    # Alive and working, not a husk left on the books.
                    self.assertGreater(seller.last_runs, 0.0)
        # The arithmetic the floor exists for: the reserve target is below
        # the minimum plant, so only the floor keeps the sector alive.
        seed = seeded_two_region_economy(parameters=self.leaving)
        tailors = next(
            p for p in seed.regions["Dust Basin"].producers if p.commodity == GARMENTS
        )
        self.assertLess(
            (1.0 + seed.capacity_reserve) * 0.0397, seed.min_investment_capacity
        )
        self.assertEqual(tailors.capacity_per_day, 0.25)

    def test_a_seller_emptied_by_an_order_sees_the_demand_it_missed(self):
        """docs/68 s2: the note reads the stock the order leaves behind.

        The opposite of the test this replaces.  While the glut's
        provisioner is empty at the close of the day it now records the
        demand it could not serve, so its expectation runs ahead of its
        own supply, the sector grows instead of shrinking, and the
        workers' shortfall stops accruing (docs/68 s4.4).
        """
        # Day 136 of the glut: the sector is still short, and the seller
        # emptied by the basket's own order is the one that must see it.
        early = regional_glut(136, parameters=self.leaving)
        sellers = [
            p
            for p in early.regions["Dust Basin"].producers
            if p.active and p.commodity == MEALS
        ]
        emptied = [p for p in sellers if p.stock <= EPSILON and p.sales_yesterday > 0.0]
        self.assertTrue(emptied)
        # Sold out and counted as such, which is the whole correction.
        self.assertGreater(sum(p.sellouts_yesterday for p in emptied), 0.0)
        # And the expectation that reads it is above what the sector managed.
        self.assertGreater(
            sum(p.expected_demand for p in sellers),
            sum(p.sales_yesterday for p in sellers),
        )
        # By the close the sector has grown past the supply it was stuck at
        # and the workers are served: no shortfall accrues over the last
        # sixty days.
        late = regional_glut(240, parameters=self.leaving)
        self.assertGreater(
            late.regions["Dust Basin"].capacity(MEALS),
            early.regions["Dust Basin"].capacity(MEALS),
        )
        self.assertAlmostEqual(
            sum(late.ledger.basket_shortfall.values()),
            sum(regional_glut(180, parameters=self.leaving).ledger.basket_shortfall.values()),
            places=3,
        )

    def test_the_investment_rule_reads_the_markets_demand(self):
        """docs/64 s1 and docs/65 s2: with the sector's expected demand in
        place of the plan's full-capacity throughput, the 66-unit leaves
        entrant of the entry run does not appear."""
        loss = producer_loss(440, parameters=self.leaving)
        entry = producer_loss(440, parameters=self.entry)

        def biggest(economy, commodity):
            return max(
                (
                    p.capacity_per_day
                    for p in economy.regions["Dust Basin"].producers
                    if p.active
                    and p.commodity == commodity
                    and p.name.startswith("entrant-")
                ),
                default=0.0,
            )

        for commodity in (LEAVES, CHEMFUEL):
            with self.subTest(commodity=commodity):
                expected = sum(
                    p.expected_demand
                    for p in loss.regions["Dust Basin"].producers
                    if p.active and p.commodity == commodity
                )
                self.assertLess(biggest(loss, commodity), biggest(entry, commodity))
                self.assertLessEqual(biggest(loss, commodity), expected)
        # An order of magnitude, which is the claim; the exact size moved
        # 21% when docs/66 kept the basket sectors alive and the wage with
        # them (docs/67 s4), and again when docs/68 let the sell-out be
        # seen and the entry run's oversized entrant fell 66 -> 50, so the
        # bound is on the order and not the value.
        self.assertGreater(biggest(entry, LEAVES), 40.0)
        self.assertLess(biggest(loss, LEAVES), 20.0)

    def test_a_cost_advantage_draws_the_incumbent_down_to_the_reserve(self):
        """docs/64 s6.6: the incumbent at a third of the custom and a
        return below the going one withdraws to its custom plus the
        reserve, and the split is by price so its price does not move."""
        economy = cost_competition(parameters=self.leaving)
        region = economy.regions["Dust Basin"]
        incumbent = next(p for p in region.producers if p.name == "Dust provisioners")
        self.assertTrue(incumbent.active)
        self.assertLess(incumbent.capacity_per_day, 0.5)
        # Down to the reserve and never through it: the floor is the one
        # thing that must hold exactly (docs/66 s2).  Where it lands
        # within the reserve moved 1.5% when the basket sectors survived
        # and the wage changed with them (docs/67 s4), so the bound above
        # is on the neighbourhood and the bound below is on the invariant.
        ratio = incumbent.capacity_per_day / incumbent.expected_demand
        self.assertGreaterEqual(ratio, 1.0 + economy.capacity_reserve)
        self.assertLess(ratio, 1.0 + economy.capacity_reserve + 0.05)
        entry_price = cost_competition(parameters=self.entry).regions["Dust Basin"].prices[MEALS]
        # The same neighbourhood, which is the claim: withdrawing idle
        # plant does not move a price the split settles.  The gap widened
        # from 1.6% to 2.3% for the wage reason in docs/67 s4.
        self.assertLess(abs(region.prices[MEALS] / entry_price - 1.0), 0.03)

    def test_what_left_equals_what_capacity_lost_gained(self):
        """docs/64 s6.9: the `exits` ledger reconciles to `capacity_lost`,
        and the three identities close at procurement's tolerances."""
        runs = {
            "equilibrium": equilibrium(parameters=self.leaving),
            "loss": producer_loss(440, parameters=self.leaving),
            "glut": regional_glut(240, parameters=self.leaving),
        }
        for label, economy in runs.items():
            with self.subTest(scenario=label):
                base = {
                    "equilibrium": equilibrium,
                    "loss": lambda **k: producer_loss(440, **k),
                    "glut": lambda **k: regional_glut(240, **k),
                }[label](parameters=self.entry)
                withdrawn = sum(a for _, _, _, a in economy.ledger.exits)
                gained = sum(economy.ledger.capacity_lost.values()) - sum(
                    base.ledger.capacity_lost.values()
                )
                self.assertGreater(withdrawn, 0.0)
                self.assertAlmostEqual(withdrawn, gained, places=9)
                self.assertLess(abs(economy.cash_balance()), 1e-6)
                self.assertLess(abs(economy.value_balance()), 1e-5)
                for name, residual in economy.commodity_balances().items():
                    self.assertLess(abs(residual), 1e-6, name)

