"""The ablation grid's three findings (docs/109, docs/110).

The grid crossed the gated rules over every combination the model
permits and found that the rules are not independent, that procurement
switches off the wage-bill death mechanism, and that worker mobility
reverses sign under exit.  Each is pinned here against the committed
cells rather than re-run, so the suite stays fast.
"""

import json
import os
import unittest

from economy_lab import grid

RESULTS = os.path.join(os.path.dirname(grid.__file__), "grid_results.json")
INDEX = {name: position for position, name in enumerate(grid.NAMES)}
STACK = ("producer_cash", "posted_prices", "procurement", "exit_on_return")
REGIMES = {
    (0, 0, 0, 0): "bare",
    (1, 0, 0, 0): "cash",
    (0, 1, 0, 0): "posted",
    (1, 1, 0, 0): "cash+posted",
    (1, 1, 1, 0): "+procurement",
    (1, 1, 1, 1): "+exit",
}


def _regime(mask):
    return REGIMES[tuple(1 if mask >> INDEX[rule] & 1 else 0 for rule in STACK)]


def _on(mask, rule):
    return bool(mask >> INDEX[rule] & 1)


class TheGridIsCompleteOnItsTrueShapeTest(unittest.TestCase):
    """docs/110 section 1: the switches are a dependency stack, not a cube."""

    @classmethod
    def setUpClass(cls):
        with open(RESULTS) as handle:
            cls.cells = json.load(handle)["cells"]
        cls.ok = [cell for cell in cls.cells if "metrics" in cell]

    def test_the_permitted_lattice_is_384_cells(self):
        # 6 market-stack levels x 2 entry x 2**5 others.
        self.assertEqual(len(self.ok), 384)
        self.assertEqual(len(self.cells), 1024)

    def test_every_failure_is_a_prerequisite_not_a_crash(self):
        for cell in self.cells:
            if "error" in cell:
                self.assertIn("switched on", cell["error"])

    def test_procurement_requires_cash_and_posted_prices(self):
        for cell in self.ok:
            if _on(cell["mask"], "procurement"):
                self.assertTrue(_on(cell["mask"], "producer_cash"))
                self.assertTrue(_on(cell["mask"], "posted_prices"))

    def test_exit_requires_procurement(self):
        for cell in self.ok:
            if _on(cell["mask"], "exit_on_return"):
                self.assertTrue(_on(cell["mask"], "procurement"))

    def test_money_is_conserved_in_every_permitted_cell(self):
        # docs/110 section 2: A1 tested 384 times instead of five.
        for cell in self.ok:
            self.assertLess(abs(cell["metrics"]["cash_residual"]), 1e-6)


class ProcurementDisablesTheDeathMechanismTest(unittest.TestCase):
    """docs/110 section 3: the largest interaction is a rule switching
    another rule's mechanism off."""

    @classmethod
    def setUpClass(cls):
        with open(RESULTS) as handle:
            cells = json.load(handle)["cells"]
        cls.joint = [
            cell
            for cell in cells
            if "metrics" in cell
            and _on(cell["mask"], "producer_employment_quantum")
            and _on(cell["mask"], "sales_follow_production")
        ]

    def _deaths(self, regime):
        return [
            cell["metrics"]["bankruptcies"]
            for cell in self.joint
            if _regime(cell["mask"]) == regime
        ]

    def test_the_cascade_is_large_without_procurement(self):
        self.assertGreaterEqual(max(self._deaths("cash+posted")), 51)

    def test_procurement_flattens_it(self):
        deaths = self._deaths("+procurement")
        self.assertEqual(min(deaths), 1)
        self.assertEqual(max(deaths), 1)

    def test_posted_prices_is_what_scales_docs_105s_two_deaths(self):
        # docs/105 ran the `cash` regime alone and reported 2 deaths.
        self.assertLessEqual(max(self._deaths("cash")), 10)
        self.assertGreater(
            max(self._deaths("cash+posted")), 5 * max(self._deaths("cash"))
        )

    def test_the_bare_regime_kills_nobody(self):
        self.assertEqual(max(self._deaths("bare")), 0)


class MigrationReversesSignUnderExitTest(unittest.TestCase):
    """docs/110 section 5: docs/107's prediction 5 is scoped, not general."""

    @classmethod
    def setUpClass(cls):
        with open(RESULTS) as handle:
            cells = json.load(handle)["cells"]
        cls.mobile = [
            cell
            for cell in cells
            if "metrics" in cell
            and _on(cell["mask"], "worker_mobility_strength")
        ]

    def _migrated(self, regime):
        return [
            cell["metrics"]["labor_migrated"]
            for cell in self.mobile
            if _regime(cell["mask"]) == regime
        ]

    def test_docs_107_holds_in_the_regime_it_measured(self):
        self.assertGreater(min(self._migrated("bare")), 0.0)

    def test_labour_leaves_the_boom_under_exit(self):
        self.assertLess(max(self._migrated("+exit")), 0.0)

    def test_the_boom_loses_labour_in_a_third_of_all_cells(self):
        losing = sum(
            1 for cell in self.mobile if cell["metrics"]["labor_migrated"] < 0.0
        )
        self.assertEqual(losing, 62)
        self.assertEqual(len(self.mobile), 192)


if __name__ == "__main__":
    unittest.main()
