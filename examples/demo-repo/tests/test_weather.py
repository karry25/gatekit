import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from weather import summarize


class WeatherTests(unittest.TestCase):
    def test_known_city(self):
        self.assertEqual(summarize("pune"), "Pune: 29C, sunny")

    def test_case_insensitive(self):
        self.assertEqual(summarize("LONDON"), "London: 11C, rain")


if __name__ == "__main__":
    unittest.main()
