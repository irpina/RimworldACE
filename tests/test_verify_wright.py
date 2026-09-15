"""The verifier of ``docs/122`` must itself be honest."""

import unittest

from economy_lab import verify_wright


class TestCheckRecordsOutcomes(unittest.TestCase):
    def setUp(self):
        verify_wright.results.clear()

    def tearDown(self):
        verify_wright.results.clear()

    def test_a_failing_check_is_recorded_as_a_failure(self):
        verify_wright.check("x", "1", "2", False, "docs/0")
        self.assertEqual(verify_wright.results, [False])

    def test_a_passing_check_is_recorded_as_a_pass(self):
        verify_wright.check("x", "1", "1", True, "docs/0")
        self.assertEqual(verify_wright.results, [True])

    def test_close_rejects_a_missing_value_rather_than_throwing(self):
        self.assertFalse(verify_wright.close(None, 1.0, 0.1))

    def test_close_is_a_tolerance_and_not_equality(self):
        self.assertTrue(verify_wright.close(1.05, 1.0, 0.1))
        self.assertFalse(verify_wright.close(1.2, 1.0, 0.1))


class TestStructuralSectionActuallyChecks(unittest.TestCase):
    """The cheap section must fail loudly if the model stops conserving."""

    def setUp(self):
        verify_wright.results.clear()

    def tearDown(self):
        verify_wright.results.clear()

    def test_the_structural_section_passes_on_the_real_model(self):
        verify_wright.structural()
        self.assertTrue(all(verify_wright.results))
        self.assertGreaterEqual(len(verify_wright.results), 4)

    def test_the_instrument_section_passes_on_planted_data(self):
        verify_wright.instruments()
        self.assertTrue(all(verify_wright.results))


if __name__ == "__main__":
    unittest.main()
