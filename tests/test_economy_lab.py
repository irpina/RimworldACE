import unittest

from economy_lab.scenarios import (
    DAYS_PER_YEAR,
    arbitrage,
    equilibrium,
    producer_loss,
    seeded_two_region_economy,
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


if __name__ == "__main__":
    unittest.main()
