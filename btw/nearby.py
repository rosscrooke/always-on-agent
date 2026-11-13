#!/usr/bin/env python3
"""Find Wikipedia articles near a coordinate, with a short intro extract.

Usage:
    python3 btw/nearby.py --lat 37.7955 --lon -122.3937 [--radius 500] [--limit 10] [--lang en]

Prints a JSON list sorted by distance:
    [{"title", "pageid", "lat", "lon", "distance_m", "bearing", "direction", "extract", "url"}]

Standard library only, so it runs in a bare Routine environment.
Exit codes: 0 ok (possibly empty list), 2 network/API error.
"""
import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "btw-agent-bootcamp/0.1 (educational demo)"
EARTH_RADIUS_M = 6371000.0
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
HERE_M = 15  # closer than this, a direction is meaningless
RETRIES = 3  # on HTTP 429/503 (Wikipedia rate limiting), with backoff


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in meters."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Initial bearing from point 1 to point 2, degrees in [0, 360)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass(deg):
    """8-point compass label for a bearing."""
    return COMPASS[int((deg + 22.5) // 45) % 8]


def parse_geosearch(data, lat, lon, lang="en"):
    """Turn a list=geosearch response into place dicts (no extracts yet)."""
    places = []
    for hit in data.get("query", {}).get("geosearch", []):
        if hit.get("ns", 0) != 0:
            continue
        b = bearing_deg(lat, lon, hit["lat"], hit["lon"])
        d = round(haversine_m(lat, lon, hit["lat"], hit["lon"]))
        title = hit["title"]
        places.append({
            "title": title,
            "pageid": hit["pageid"],
            "lat": hit["lat"],
            "lon": hit["lon"],
            "distance_m": d,
            "bearing": round(b),
            "direction": "here" if d < HERE_M else compass(b),
            "extract": "",
            "url": "https://%s.wikipedia.org/wiki/%s"
                   % (lang, urllib.parse.quote(title.replace(" ", "_"))),
        })
    places.sort(key=lambda p: p["distance_m"])
    return places


def merge_extracts(places, data):
    """Fill each place's extract from a prop=extracts response."""
    pages = data.get("query", {}).get("pages", {})
    by_id = {int(pid): page.get("extract", "") for pid, page in pages.items()}
    for p in places:
        p["extract"] = (by_id.get(p["pageid"]) or "").strip()
    return places


def _get(lang, params):
    params = dict(params, format="json", formatversion="1")
    url = "https://%s.wikipedia.org/w/api.php?%s" % (lang, urllib.parse.urlencode(params))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == RETRIES:
                raise
            retry_after = e.headers.get("Retry-After", "")
            wait = int(retry_after) if retry_after.isdigit() else 2 ** (attempt + 1)
            time.sleep(min(wait, 30))


def nearby(lat, lon, radius=500, limit=10, lang="en"):
    geo = _get(lang, {
        "action": "query", "list": "geosearch",
        "gscoord": "%f|%f" % (lat, lon), "gsradius": radius, "gslimit": limit,
    })
    places = parse_geosearch(geo, lat, lon, lang)
    if not places:
        return places
    ext = _get(lang, {
        "action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
        "exsentences": 3, "exlimit": "max",
        "pageids": "|".join(str(p["pageid"]) for p in places),
    })
    return merge_extracts(places, ext)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--radius", type=int, default=500, help="meters, max 10000")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--lang", default="en")
    a = ap.parse_args(argv)
    try:
        result = nearby(a.lat, a.lon, min(a.radius, 10000), a.limit, a.lang)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print("nearby: Wikipedia request failed: %s" % e, file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
