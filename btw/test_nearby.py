"""Offline tests for btw/nearby.py. Run: python3 -m unittest discover btw"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import nearby  # noqa: E402

FERRY = (37.7955, -122.3937)


def load(name):
    with open(os.path.join(HERE, "fixtures", name)) as f:
        return json.load(f)


class GeoMath(unittest.TestCase):
    def test_haversine_zero(self):
        self.assertEqual(nearby.haversine_m(*FERRY, *FERRY), 0)

    def test_haversine_ferry_to_coit_tower(self):
        # Ferry Building -> Coit Tower is roughly 1.3 km as the crow flies
        d = nearby.haversine_m(*FERRY, 37.8024, -122.4058)
        self.assertTrue(1200 < d < 1400, d)

    def test_one_degree_latitude(self):
        d = nearby.haversine_m(0, 0, 1, 0)
        self.assertAlmostEqual(d, 111195, delta=50)

    def test_bearing_cardinals(self):
        self.assertAlmostEqual(nearby.bearing_deg(0, 0, 1, 0), 0, delta=0.01)
        self.assertAlmostEqual(nearby.bearing_deg(0, 0, 0, 1), 90, delta=0.01)
        self.assertAlmostEqual(nearby.bearing_deg(0, 0, -1, 0), 180, delta=0.01)
        self.assertAlmostEqual(nearby.bearing_deg(0, 0, 0, -1), 270, delta=0.01)

    def test_compass(self):
        cases = {0: "N", 22: "N", 23: "NE", 90: "E", 200: "S", 220: "SW",
                 271: "W", 330: "NW", 359: "N"}
        for deg, label in cases.items():
            self.assertEqual(nearby.compass(deg), label, deg)


class Parsing(unittest.TestCase):
    def setUp(self):
        self.places = nearby.parse_geosearch(load("geosearch_ferry_building.json"), *FERRY)

    def test_sorted_by_distance(self):
        dists = [p["distance_m"] for p in self.places]
        self.assertEqual(dists, sorted(dists))
        self.assertEqual(len(self.places), 3)

    def test_place_at_origin_is_here(self):
        first = self.places[0]
        self.assertEqual(first["title"], "San Francisco Ferry Building")
        self.assertEqual(first["distance_m"], 0)
        self.assertEqual(first["direction"], "here")

    def test_url_is_escaped(self):
        urls = {p["title"]: p["url"] for p in self.places}
        self.assertEqual(urls["R-Evolution (Cochrane)"],
                         "https://en.wikipedia.org/wiki/R-Evolution_%28Cochrane%29")

    def test_merge_extracts(self):
        merged = nearby.merge_extracts(self.places, load("extracts_ferry_building.json"))
        for p in merged:
            self.assertTrue(p["extract"], p["title"])
        self.assertIn("ferries", merged[0]["extract"])

    def test_empty_response(self):
        self.assertEqual(nearby.parse_geosearch({"batchcomplete": ""}, *FERRY), [])


class Track(unittest.TestCase):
    def test_track_is_valid_and_in_san_francisco(self):
        with open(os.path.join(HERE, "..", "location", "track.json")) as f:
            track = json.load(f)
        points = track["points"]
        self.assertGreaterEqual(len(points), 10)
        self.assertEqual([p["seq"] for p in points], list(range(len(points))))
        for p in points:
            self.assertTrue(37.70 < p["lat"] < 37.83, p)
            self.assertTrue(-122.52 < p["lon"] < -122.35, p)
            self.assertTrue(p["label"])
        # consecutive stops should be a short walk apart (< 800 m)
        for a, b in zip(points, points[1:]):
            d = nearby.haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])
            self.assertLess(d, 800, (a["label"], b["label"], d))


if __name__ == "__main__":
    unittest.main()
