import unittest

from economy_lab.model import ALL_OR_NOTHING, Commodity, Process, Producer
from economy_lab.scenarios import (
    CHEMFUEL,
    DAYS_PER_YEAR,
    LEAVES,
    YAYO,
    arbitrage,
    circuit_processes,
    equilibrium,
    input_shortage,
    producer_loss,
    regional_glut,
    seeded_two_region_economy,
    summary,
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
        unmet = [h["regions"][local]["unmet"][LEAVES] for h in history]

        # The shortage reaches the input market first...
        self.assertLess(min(leaves[61:]), leaves[60])
        self.assertGreater(max(unmet[61:]), 0.0)
        # ...then the output market.
        self.assertGreater(max(yayo_price[61:]), yayo_price[60] * 1.50)

        # Yayo capacity is untouched throughout: the drug lab is constrained
        # by materials, not by its own capacity.
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
        proportional = seeded_two_region_economy()
        cliff = seeded_two_region_economy(input_rationing=ALL_OR_NOTHING)
        for economy in (proportional, cliff):
            economy.step(60)
            economy.destroy_capacity("Dust Basin", LEAVES, 0.70)
            economy.step(60)
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

    def test_scarcity_of_an_input_registers_as_unmet_demand_for_that_input(self):
        economy = input_shortage()
        # Leaves ran short; chemfuel never did. The drug lab was throttled by
        # the leaf shortage and so drew less chemfuel than it was allocated,
        # and that slack must not be booked as a chemfuel shortage.
        unmet_leaves = max(
            h["regions"]["Dust Basin"]["unmet"][LEAVES] for h in economy.history
        )
        unmet_chemfuel = max(
            h["regions"]["Dust Basin"]["unmet"][CHEMFUEL] for h in economy.history
        )
        self.assertGreater(unmet_leaves, 0.0)
        self.assertAlmostEqual(unmet_chemfuel, 0.0, places=9)


if __name__ == "__main__":
    unittest.main()
