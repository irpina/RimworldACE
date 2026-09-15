"""The M1 ablation harness of ``docs/115`` and ``docs/116``."""

import unittest

from economy_lab import m1_ablation as ablation
from economy_lab import social_architecture as sa


def tiny(rule, seed):
    """One short run, enough to exercise the record shape without the sweep."""
    economy = sa.Economy(seed=seed, market_rule=rule)
    economy.run(12)
    economy.start_recording()
    economy.run(12)
    return economy


class TestRunCell(unittest.TestCase):
    def test_every_rule_has_a_label(self):
        self.assertEqual(set(ablation.LABEL), set(sa.MARKET_RULES))

    def test_a_cell_records_every_field_the_report_reads(self):
        record = ablation.run_cell(("wright", 0))
        for field in ("rule", "seed", "firm_sizes", "demises", "gdp",
                      "firm_growth", "incomes", "profit_rates", "wage_shares",
                      "unemployment", "firms", "largest", "coins"):
            self.assertIn(field, record)

    def test_a_cell_conserves_money(self):
        record = ablation.run_cell(("wright", 3))
        self.assertAlmostEqual(record["coins"], 100000.0, places=5)

    def test_a_cell_is_reproducible(self):
        self.assertEqual(ablation.run_cell(("neutral", 7)),
                         ablation.run_cell(("neutral", 7)))


class TestDecompose(unittest.TestCase):
    def test_a_pure_l_effect_shows_no_r_effect_and_no_interaction(self):
        # L on adds 10; R does nothing.
        means = {"wright": 10.0, "fixed": 10.0, "neutral": 0.0, "fixed_neutral": 0.0}
        effects = ablation.decompose(means)
        self.assertAlmostEqual(effects["main_l"], 10.0)
        self.assertAlmostEqual(effects["main_r"], 0.0)
        self.assertAlmostEqual(effects["interaction"], 0.0)

    def test_a_pure_r_effect_shows_no_l_effect(self):
        means = {"wright": 4.0, "neutral": 4.0, "fixed": 0.0, "fixed_neutral": 0.0}
        effects = ablation.decompose(means)
        self.assertAlmostEqual(effects["main_l"], 0.0)
        self.assertAlmostEqual(effects["main_r"], 4.0)

    def test_an_effect_needing_both_is_all_interaction(self):
        # Only the cell with both switched on moves.
        means = {"wright": 8.0, "neutral": 0.0, "fixed": 0.0, "fixed_neutral": 0.0}
        effects = ablation.decompose(means)
        self.assertAlmostEqual(effects["interaction"], 4.0)
        self.assertAlmostEqual(effects["interaction_fraction"], 0.5)

    def test_a_flat_metric_reports_no_interaction_rather_than_dividing_by_zero(self):
        means = {rule: 2.0 for rule in sa.MARKET_RULES}
        self.assertEqual(ablation.decompose(means)["interaction_fraction"], 0.0)


class TestReadings(unittest.TestCase):
    def setUp(self):
        self.runs = [ablation.run_cell((rule, 0)) for rule in sa.MARKET_RULES]

    def test_pooled_reports_every_row_the_table_prints(self):
        row = ablation.pooled(self.runs, "wright")
        for field in ("largest", "firms", "unemployment", "alpha", "demises",
                      "growth_kurtosis", "wage_share"):
            self.assertIn(field, row)

    def test_per_seed_returns_one_reading_per_run_of_that_rule(self):
        self.assertEqual(len(ablation.per_seed(self.runs, "wright", "largest")), 1)

    def test_per_seed_reads_the_stored_terminal_snapshot(self):
        wright = [run for run in self.runs if run["rule"] == "wright"][0]
        self.assertEqual(ablation.per_seed(self.runs, "wright", "largest"),
                         [float(wright["largest"])])


if __name__ == "__main__":
    unittest.main()
