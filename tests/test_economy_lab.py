import unittest
from dataclasses import replace

from economy_lab.model import (
    ALL_OR_NOTHING,
    Commodity,
    Process,
    Producer,
    ResourceGrade,
    ResourceReserve,
)
from economy_lab.scenarios import (
    CHEMFUEL,
    DAYS_PER_YEAR,
    GARMENTS,
    LEAVES,
    MEALS,
    MEDICINE,
    YAYO,
    ScenarioParameters,
    arbitrage,
    circuit_processes,
    cost_competition,
    equilibrium,
    generous_basket,
    input_shortage,
    perishable_meals,
    producer_loss,
    regional_glut,
    reserve_depletion,
    seeded_two_region_economy,
    subsistence_shock,
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


if __name__ == "__main__":
    unittest.main()
