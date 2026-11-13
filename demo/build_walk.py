#!/usr/bin/env python3
"""Fetch Wikipedia candidates for every stop of location/track.json -> demo/raw_walk.json."""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "btw"))
import nearby  # noqa: E402


def main():
    with open(os.path.join(ROOT, "location", "track.json")) as f:
        track = json.load(f)
    stops = []
    for i, p in enumerate(track["points"]):
        if i:
            time.sleep(3)
        cands = nearby.nearby(p["lat"], p["lon"], 500, 12)
        print(f"stop {p['seq']} {p['label']}: {len(cands)} candidates", file=sys.stderr)
        stops.append({**p, "candidates": cands})
    out = os.path.join(ROOT, "demo", "raw_walk.json")
    with open(out, "w") as f:
        json.dump({"city": track["city"], "radius_m": 500, "stops": stops}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
