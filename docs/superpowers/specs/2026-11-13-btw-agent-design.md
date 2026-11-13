# By the way agent — design

_Status: approved 2026-11-13. This is the source of truth for `btw/` and `location/`._

## Goal
This is an always-on agent for the bootcamp. It knows the user's GPS position, suggests nearby points of interest, and gives a short snippet about each one for context. It runs as a Claude Code **Routine** (a cloud agent) against this repo.

## Decisions
| Topic | Decision | Why |
|---|---|---|
| Location | A simulated track, `location/track.json` (12 stops, SF) | A routine can't read a phone's GPS. This matches how the repo fakes its other data, and the demo is repeatable. |
| Output | One GitHub issue labeled `btw-feed`, one comment per run | The issue is also the agent's state, so nothing gets committed. |
| POI source | Wikipedia geosearch + intro extracts | Free and needs no API key. Snippets come from real text, so nothing is invented. |
| City | San Francisco: Ferry Building → North Beach → Chinatown → Union Square | Chosen by Marco. Good Wikipedia coverage. |

Consumer apps already do this (Wexplo, Waytale, Wander). The point here is the agent pattern, not a competing product.

## One run
1. Find the open issue labeled `btw-feed`, or create it.
2. `count` = the number of comments with the marker `<!-- btw-stop:N -->`. The current stop is `points[count % len(points)]`. No other state.
3. `python3 btw/nearby.py --lat --lon --radius 500 --limit 10` returns JSON with `title, distance_m, direction, extract, url`, sorted by distance. `direction` is `here` when the place is closer than 15 m.
4. Drop the places whose URL already appears in earlier stop comments, and the places with no extract.
5. Claude picks up to 3 places and posts one comment: a stop header, an OSM map link, then for each place a linked title, the distance and direction, and a 2–3 sentence snippet that uses only facts from the extract. The comment ends with the marker.
6. If nothing new is left, or Wikipedia can't be reached, the agent still posts the stop so the walk keeps moving.

The full operating instructions are in `btw/ROUTINE_PROMPT.md`.

## Components
- `btw/nearby.py`: standard library only. It makes two API calls (`list=geosearch`, then `prop=extracts`), and computes haversine distance and 8-point compass direction. It sends a generic User-Agent with no personal data. It exits with 2 on network or API errors.
- `btw/config.json`: `radius_m`, `max_suggestions`, `feed_label`, `feed_title`, `wiki_lang`.
- `btw/test_nearby.py` + `btw/fixtures/`: offline tests for the geo math, parsing, extract merging, and track validity (it checks the points are in SF and that consecutive stops are less than 800 m apart).

## Routine setup
- Prompt: `Follow btw/ROUTINE_PROMPT.md`. Trigger: a schedule, plus Run now for demos.
- The network allowlist must include `en.wikipedia.org`. If it doesn't, the agent falls back to WebFetch.
- Permissions: read the repo, write issues and comments. The agent never commits.

## Verification
1. `python3 -m unittest discover btw`
2. `python3 btw/nearby.py --lat 37.7955 --lon -122.3937` returns the Ferry Building and its neighbours, with extracts.
3. A local dry run of the prompt against a test issue produces stop 1.
4. Two Run now runs of the routine produce stops 1 and 2, with no repeated places.

## Out of scope
Live phone GPS, OpenStreetMap places, push notifications, other languages. The `{lat, lon}` contract leaves room to add live GPS later.
