"""The two ledger dicts of ``docs/126`` §2 and the battery knobs of §3."""

import unittest
from dataclasses import replace

from economy_lab import wright_battery as wb
from economy_lab.scenarios import ScenarioParameters, equilibrium


class TestSalesReceiptsAndPurchases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.with_cash = equilibrium(
            days=60, parameters=replace(ScenarioParameters(), producer_cash=True)
        )
        cls.bare = equilibrium(days=60)

    def test_empty_in_the_default_model(self):
        """Only booked where producers hold cash (docs/126 §2)."""
        self.assertEqual(self.bare.ledger.sales_receipts, {})
        self.assertEqual(self.bare.ledger.producer_purchases, {})

    def test_booked_by_region_where_producers_hold_cash(self):
        receipts = self.with_cash.ledger.sales_receipts
        purchases = self.with_cash.ledger.producer_purchases
        self.assertEqual(set(receipts), set(self.with_cash.regions))
        self.assertEqual(set(purchases), set(self.with_cash.regions))
        for region in self.with_cash.regions:
            self.assertGreater(receipts[region], 0.0)
            self.assertGreater(purchases[region], 0.0)

    def test_every_purchase_is_somebody_s_receipt(self):
        """A producer's purchase credits a producer, so receipts, which
        also carry what workers and the fund buy, are never the smaller."""
        ledger = self.with_cash.ledger
        for region in self.with_cash.regions:
            self.assertGreaterEqual(
                ledger.sales_receipts[region], ledger.producer_purchases[region]
            )

    def test_value_added_exceeds_wages_in_the_stationary_circuit(self):
        """The money wage share is a proper fraction where prices cover
        cash cost, which the seeded circuit's do (docs/55 s6.3)."""
        ledger = self.with_cash.ledger
        wages = sum(ledger.wages_paid.values())
        added = sum(ledger.sales_receipts.values()) - sum(
            ledger.producer_purchases.values()
        )
        self.assertGreater(wages, 0.0)
        self.assertGreater(added, wages)


class TestBatteryKnobs(unittest.TestCase):
    def test_demand_scales_the_labour_pool_and_the_endowments(self):
        small = wb.build_ours(1, demand=1.0)
        large = wb.build_ours(1, demand=4.0)
        for a, b in zip(small.regions.values(), large.regions.values()):
            self.assertAlmostEqual(b.labor_pool / a.labor_pool, 4.0)
            self.assertGreater(b.cash, a.cash)

    def test_the_quantum_knob_reaches_the_model(self):
        self.assertEqual(wb.build_ours(1, quantum=0.0).producer_employment_quantum, 0.0)
        self.assertEqual(wb.build_ours(1).producer_employment_quantum, 1.0)

    def test_the_battery_books_the_money_flows(self):
        economy = wb.build_ours(1, demand=1.0)
        economy.step(3)
        wages, receipts, purchases = wb.money_totals(economy)
        self.assertGreater(wages, 0.0)
        self.assertGreater(receipts, purchases)

    def test_the_control_s_money_share_is_its_wage_share(self):
        """docs/126 §3: the shared instrument compares like with like."""
        record = wb.measure_sa(0)
        self.assertEqual(record["money_wage_shares"], record["wage_shares"])
        facts = wb.facts(record)
        self.assertAlmostEqual(facts["money_wage_share"], facts["wage_share"])

    def test_facts_tolerates_a_record_without_money_shares(self):
        record = wb.measure_sa(0)
        del record["money_wage_shares"]
        del record["gross_wage_shares"]
        self.assertIsNone(wb.facts(record)["money_wage_share"])


class TestBasketInDemand(unittest.TestCase):
    """docs/128: the staple sector sized to feed the workforce."""

    def test_off_by_default_and_the_default_is_untouched(self):
        from economy_lab.scale import synthetic_economy
        off = synthetic_economy(commodities=40, regions=1, record_history=False, seed=1)
        self.assertNotIn("basket_iterations", off.scale_record)

    def test_on_raises_the_staple_capacity_and_nothing_upstream_of_it_falls(self):
        from economy_lab.scale import synthetic_economy
        off = synthetic_economy(commodities=40, regions=1, daily_demand=50.0,
                                record_history=False, seed=1)
        on = synthetic_economy(commodities=40, regions=1, daily_demand=50.0,
                               basket_in_demand=True, record_history=False, seed=1)
        region_off = next(iter(off.regions.values()))
        region_on = next(iter(on.regions.values()))
        staple = next(iter(region_on.subsistence_basket))
        cap = {p.commodity: p.capacity_per_day for p in region_off.producers}
        for producer in region_on.producers:
            self.assertGreaterEqual(producer.capacity_per_day, cap[producer.commodity] * (1 - 1e-12))
        staple_off = next(p for p in region_off.producers if p.commodity == staple)
        staple_on = next(p for p in region_on.producers if p.commodity == staple)
        self.assertGreater(staple_on.capacity_per_day, staple_off.capacity_per_day)
        self.assertGreaterEqual(on.scale_record["basket_iterations"], 2)

    def test_the_fixed_point_feeds_the_workforce_it_implies(self):
        """Capacity is headroom times the requirement, and the requirement
        is the graph's own use plus the basket of the workers at that
        requirement -- so at full capacity the basket demand is headroom
        times the basket part, and the identity closes to the bit."""
        from economy_lab.scale import synthetic_economy
        headroom = 1.25
        on = synthetic_economy(commodities=40, regions=1, daily_demand=50.0,
                               basket_in_demand=True, capacity_headroom=headroom,
                               record_history=False, seed=1)
        off = synthetic_economy(commodities=40, regions=1, daily_demand=50.0,
                                capacity_headroom=headroom, record_history=False, seed=1)
        region = next(iter(on.regions.values()))
        staple = next(iter(region.subsistence_basket))
        quantity = region.subsistence_basket[staple]
        workers = sum(
            p.process.runs_for(p.capacity_per_day) * p.process.direct_labor
            / region.ticks_per_worker_day
            for p in region.producers
        )
        graph_use = next(
            p for p in next(iter(off.regions.values())).producers if p.commodity == staple
        ).capacity_per_day / headroom
        expected = headroom * (graph_use + workers * quantity / headroom)
        got = next(p for p in region.producers if p.commodity == staple).capacity_per_day
        self.assertAlmostEqual(got / expected, 1.0, places=4)

    def test_the_battery_reaches_the_generator(self):
        with_fix = wb.build_ours(1, demand=4.0)
        without = wb.build_ours(1, demand=4.0, basket_in_demand=False)
        region_with = next(iter(with_fix.regions.values()))
        region_without = next(iter(without.regions.values()))
        staple = next(iter(region_with.subsistence_basket))
        a = next(p for p in region_with.producers if p.commodity == staple).capacity_per_day
        b = next(p for p in region_without.producers if p.commodity == staple).capacity_per_day
        self.assertGreater(a, b)


class TestProducersPerCommodity(unittest.TestCase):
    """docs/130: several firms per commodity, from a separate stream."""

    def test_one_per_commodity_is_the_default_and_is_untouched(self):
        from economy_lab.scale import synthetic_economy
        default = synthetic_economy(commodities=40, regions=1, record_history=False, seed=1)
        explicit = synthetic_economy(commodities=40, regions=1, record_history=False,
                                     seed=1, producers_per_commodity=1, cost_spread=0.5)
        a = [(p.name, p.capacity_per_day, p.unit_cost) for p in next(iter(default.regions.values())).producers]
        b = [(p.name, p.capacity_per_day, p.unit_cost) for p in next(iter(explicit.regions.values())).producers]
        self.assertEqual(a, b)

    def test_capacity_is_split_and_overhead_is_spread(self):
        from economy_lab.scale import synthetic_economy
        one = synthetic_economy(commodities=40, regions=1, record_history=False, seed=1)
        four = synthetic_economy(commodities=40, regions=1, record_history=False,
                                 seed=1, producers_per_commodity=4, cost_spread=0.1)
        base = {p.commodity: p for p in next(iter(one.regions.values())).producers}
        sectors = {}
        for producer in next(iter(four.regions.values())).producers:
            sectors.setdefault(producer.commodity, []).append(producer)
        for commodity, members in sectors.items():
            self.assertEqual(len(members), 4)
            self.assertAlmostEqual(sum(p.capacity_per_day for p in members),
                                   base[commodity].capacity_per_day)
            for producer in members:
                self.assertLessEqual(abs(producer.unit_cost - base[commodity].unit_cost),
                                     0.05 * base[commodity].unit_cost + 1e-12)
        self.assertEqual(len({p.name for p in next(iter(four.regions.values())).producers}),
                         4 * len(base))

    def test_zero_firms_is_refused(self):
        from economy_lab.scale import synthetic_economy
        with self.assertRaises(ValueError):
            synthetic_economy(commodities=40, regions=1, record_history=False,
                              producers_per_commodity=0)

    def test_sector_structure_reads_competition(self):
        economy = wb.build_ours(1, demand=4.0, producers_per_commodity=3)
        economy.step(5)
        structure = wb.sector_structure(economy, wb.employment(economy))
        self.assertIn("cost_rank", structure)
        self.assertIn("sector_cv", structure)
        self.assertIsNotNone(structure["sector_cv"])
