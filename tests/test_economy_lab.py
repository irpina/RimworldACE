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
    LEAVES,
    MEALS,
    YAYO,
    ScenarioParameters,
    arbitrage,
    circuit_processes,
    cost_competition,
    equilibrium,
    input_shortage,
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
        # Chemfuel is shared, so its draw is the sum over both consumers.
        farming = circuit_processes()[LEAVES]
        expected_chemfuel = (
            produced * recipe.inputs[CHEMFUEL]
            + economy.ledger.production[LEAVES] * farming.inputs[CHEMFUEL]
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
            self.assertAlmostEqual(region.worker_cash, 900.0, places=9)

    def test_workers_consume_real_meals(self):
        economy = equilibrium(days=120)
        consumed = economy.ledger.consumption.get(MEALS, 0.0)
        produced = economy.ledger.production.get(MEALS, 0.0)
        self.assertGreater(consumed, 0.0)
        self.assertAlmostEqual(consumed, produced, places=6)

    def test_rate_of_surplus_value_matches_the_closed_form(self):
        """s/v = (working day - basket labor) / basket labor, per docs/17."""
        parameters = ScenarioParameters()
        basket_ticks = (
            parameters.meals_per_worker_day * parameters.meal_direct_labor
        )
        expected = (
            parameters.ticks_per_worker_day - basket_ticks
        ) / basket_ticks
        economy = equilibrium(days=240)
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
        """The wage-push channel: meal scarcity raises every producer's cost."""
        economy = subsistence_shock()
        dust = economy.regions["Dust Basin"]
        self.assertGreater(dust.prices[MEALS], 15.0 * 1.15)
        self.assertGreater(dust.wage_rate(), 30.0 * 1.15)
        lab = next(p for p in dust.producers if p.commodity == YAYO)
        self.assertGreater(lab.wage_cost_per_unit, 350.0 * (30.0 / 24000.0) / 1.0)
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

    def test_input_free_commodities_reproduce_the_closed_analysis(self):
        # Chemfuel and meals have no modelled inputs, so their value is
        # their direct labor and must match the closed analysis to the bit.
        self.assertEqual(self.economy.labor_values[CHEMFUEL], 25.0)
        self.assertEqual(self.economy.labor_values[MEALS], 305.0)

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
        self.assertAlmostEqual(
            self.economy.labor_values[LEAVES],
            vanilla_leaves + stylized_leaves,
            places=10,
        )
        self.assertAlmostEqual(
            self.economy.labor_values[YAYO],
            vanilla_yayo + stylized_yayo,
            places=10,
        )

    def test_value_is_transferred_labor_plus_living_labor(self):
        values = self.economy.labor_values
        process = circuit_processes()[YAYO]
        transferred = sum(
            quantity * values[name]
            for name, quantity in process.inputs.items()
        )
        self.assertAlmostEqual(
            values[YAYO], transferred + process.direct_labor, places=10
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
        self.assertAlmostEqual(min(series), 734.6, places=9)


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
        self.assertEqual(self.before.labor_values[MEALS], 305.0)
        self.assertLess(self.economy.labor_values[MEALS], 280.0)
        self.assertGreater(self.economy.labor_values[MEALS], 228.75)

    def test_social_value_lies_between_the_individual_values(self):
        dust = self.economy.regional_labor_values["Dust Basin"][MEALS]
        river = self.economy.regional_labor_values["Green River"][MEALS]
        social = self.economy.labor_values[MEALS]
        # The adopter produces below social value, the laggard above it.
        self.assertLess(dust, social)
        self.assertLess(social, river)
        self.assertAlmostEqual(river, 305.0, places=6)
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
        value_fall = (610.0 - self.economy.basket_labor_value(region)) / 610.0
        price_fall = (30.0 - region.wage_rate()) / 30.0
        self.assertGreater(value_fall, 0.10)
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
        # No technique changed how much labor a meal takes.
        self.assertEqual(self.economy.labor_values[MEALS], 305.0)

    def test_money_wages_fall_while_the_value_of_labor_power_does_not(self):
        # The distinction the four ledgers exist to keep: the money form
        # of variable capital falls, its value does not.
        self.assertLess(self.region.wage_rate(), 30.0)
        self.assertAlmostEqual(
            self.economy.basket_labor_value(self.region), 610.0, places=6
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

        value_move_labor = abs(labor_saving.labor_values[MEALS] - 305.0) / 305.0
        price_move_labor = abs(
            labor_saving.regions["Dust Basin"].prices[MEALS] - 15.0
        ) / 15.0
        value_move_capital = (
            abs(capital_saving.labor_values[MEALS] - 305.0) / 305.0
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


if __name__ == "__main__":
    unittest.main()
