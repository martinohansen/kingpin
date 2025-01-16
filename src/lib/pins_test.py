import unittest

from lib import pins


class TestPins(unittest.TestCase):
    def test_within(self):
        new_york = (40.7128, -74.0060)
        test_pins = [
            pins.Pin(
                lst="test",
                name="New York",
                address="123 Main St",
                latitude=new_york[0],
                longitude=new_york[1],
                categorizes=["food"],
                operational=True,
            ),
            pins.Pin(
                lst="test",
                name="Los Angeles",
                address="456 State St",
                latitude=34.0522,
                longitude=-118.2437,
                categorizes=["shopping"],
                operational=True,
            ),
            pins.Pin(
                lst="test",
                name="Near New York",
                address="789 Market St",
                latitude=40.7829,
                longitude=-73.9654,
                categorizes=["entertainment"],
                operational=True,
            ),
        ]
        nearby_pins = pins.within(1, new_york, test_pins)
        self.assertEqual(len(nearby_pins), 1)
        self.assertEqual(nearby_pins[0].name, "New York")

        nearby_pins = pins.within(50, new_york, test_pins)
        self.assertEqual(len(nearby_pins), 2)
        self.assertEqual(nearby_pins[0].name, "New York")
        self.assertEqual(nearby_pins[1].name, "Near New York")

        # Empty list should return empty result
        self.assertEqual(pins.within(10, new_york, []), [])


if __name__ == "__main__":
    unittest.main()
