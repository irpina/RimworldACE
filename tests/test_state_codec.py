"""docs/141 §4: the full-state codec the port's fixtures are written in."""
import json
import unittest

from economy_lab import state_codec
from economy_lab.wright_battery import DOCKED, build_ours


def small(seed=0, regions=2):
    return build_ours(seed, commodities=24, regions=regions, **DOCKED)


class StateCodecTests(unittest.TestCase):
    def test_the_text_round_trips(self):
        economy = small()
        economy.step(12)
        text = state_codec.dumps(economy)
        self.assertEqual(state_codec.dumps(state_codec.loads(text)), text)

    def test_a_decoded_economy_steps_identically(self):
        # The completeness claim: nothing the step reads lives outside the
        # encoding.  Checked from day 0 and from mid-run, on three regions
        # so that more than one route exists.
        for start in (0, 15):
            economy = small(seed=3, regions=3)
            economy.step(start)
            copy = state_codec.loads(state_codec.dumps(economy))
            economy.step(20)
            copy.step(20)
            self.assertEqual(state_codec.dumps(copy), state_codec.dumps(economy),
                             f"diverged after decoding at day {start}")

    def test_floats_are_written_exactly(self):
        economy = small()
        economy.step(5)
        data = json.loads(state_codec.dumps(economy))
        producer = economy.regions["region_000"].producers[0]
        self.assertEqual(data["regions"][0]["producers"][0]["cash"].hex(),
                         producer.cash.hex())

    def test_an_unknown_attribute_is_refused(self):
        economy = small()
        economy.some_new_state = [1, 2]
        with self.assertRaises(TypeError):
            state_codec.encode(economy)

    def test_a_producer_attribute_outside_its_dataclass_is_refused(self):
        economy = small()
        economy.regions["region_000"].producers[0].stray = 1.0
        with self.assertRaises(TypeError):
            state_codec.encode(economy)


if __name__ == "__main__":
    unittest.main()
