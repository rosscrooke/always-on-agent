# demo/walk.json — the contract between the data builder and the demo UI

The demo UI (`demo/index.html`) plays the walk from `demo/walk.json`. Nothing in the UI needs
the network except map tiles and the optional live mode, so a bad venue connection can't break
the walk itself.

```json
{
  "generated_at": "2026-11-13T16:00:00Z",
  "city": "San Francisco",
  "radius_m": 500,
  "stops": [
    {
      "seq": 7,
      "label": "City Lights Bookstore",
      "lat": 37.7976,
      "lon": -122.4066,
      "time": "3:55 PM",
      "notification": {
        "title": "By the way, you're standing at City Lights",
        "body": "Lawrence Ferlinghetti co-founded this bookstore-publisher in 1953. And the alley next to it is named after Jack Kerouac."
      },
      "places": [
        {
          "title": "City Lights Bookstore",
          "url": "https://en.wikipedia.org/wiki/City_Lights_Bookstore",
          "lat": 37.79757,
          "lon": -122.40651,
          "distance_m": 4,
          "direction": "here",
          "snippet": "Look up: you're standing at the bookstore poet Lawrence Ferlinghetti co-founded in 1953. It's still a bookshop and a publisher, focused on world literature, the arts and progressive politics."
        }
      ],
      "skipped": [
        { "title": "Big Al's", "reason": "not family-friendly" }
      ]
    }
  ]
}
```

Rules:
- `stops` is in walk order, one entry per point in `location/track.json`. `seq`, `label`, `lat`, `lon` are copied from the track.
- `time`: a simulated clock. Stop 0 is 1:00 PM and each stop adds 25 minutes, written like `3:55 PM`.
- `places`: 1–3 entries, closest and most interesting first, never repeating a URL from an earlier stop. `direction` is `here` or an 8-point compass label (`N`, `NE`, …). It is the same as `nearby.py` prints.
- `snippet`: 2–3 sentences, using only facts from the Wikipedia extract. It opens with a hook ("Look up…", "Hard to believe, but…").
- `notification.title`: at most 60 characters and starts with "By the way". `notification.body`: at most 140 characters. Both come from the same facts.
- `skipped`: what the agent filtered out at this stop and why (`"not family-friendly"`, `"already suggested"`, `"no extract"`). It may be empty. The UI can show it in a trace.
