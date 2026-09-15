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
