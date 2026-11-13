# Synthetic Enterprise Repo

This is the working environment for the Always-On Ops Agent. Fork or clone this into a GitHub repo on your own account, then point your routine at it.

## What's in here

- `issues/` — Open production incidents (JSON). Realistic but synthetic.
- `runbooks/` — Operational playbooks the agent can reference.
- `deploys/` — Recent deploy log (`recent.json`), used for correlating incidents with deploys.
- `contracts/` — Vendor contracts (for Card C — Compliance Drift).
- `compliance-policy.md` — The policy the compliance agent enforces.

All data is fictional. Companies, names, error messages, contract terms — none of it maps to real systems.

## How to use

```bash
# Clone (or fork) this into your own GitHub
gh repo create my-hackathon-repo --private --clone
cd my-hackathon-repo
cp -r ../partner-basecamp-hackathon/01-always-on-ops-agent/synthetic-repo/* .
git add . && git commit -m "Seed synthetic enterprise data" && git push

# Then point your routine at this repo via the Routines UI
```

## By the way agent

An always-on agent that knows where you are and tells you, *by the way*, about the interesting places close by, each with a short snippet for context. Location is simulated: every run moves one stop along a walk through San Francisco.

- `location/track.json`: the simulated GPS track (12 stops, Ferry Building → Union Square).
- `btw/nearby.py`: finds Wikipedia articles near a coordinate, with distance, direction and intro text. Standard library only.
- `btw/config.json`: search radius, number of suggestions, feed label.
- `btw/ROUTINE_PROMPT.md`: what the routine does on each run.
- `btw/test_nearby.py`: offline tests (`python3 -m unittest discover btw`).

Each run posts one comment to an issue labeled `btw-feed`. That issue is also the agent's memory: the number of stop comments tells it where you are, and the links already posted keep it from suggesting the same place twice.

**Set up the routine:** repo = this one. Prompt = `Follow btw/ROUTINE_PROMPT.md`. Trigger = a schedule, plus **Run now** for demos. The cloud environment has to allow network access to `en.wikipedia.org`. If it doesn't, the agent falls back to WebFetch. The routine needs permission to write issues and comments.

Try it locally: `python3 btw/nearby.py --lat 37.7955 --lon -122.3937`
