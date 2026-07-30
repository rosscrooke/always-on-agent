"""
The DATA ADAPTER — the seam between the agent and the ad-ops data source.

This is the ONE piece that changes between the demo and production:
  - StubAdapter  → reads local JSON files in adops/            (demo, offline)
  - GAMAdapter   → calls the Google Ad Manager / SpringServe API (production)

The agent only ever talks to this interface, so swapping the data source
never touches the agent's brain. That is the whole point of the seam.
"""
from __future__ import annotations

import glob
import json
import os
from abc import ABC, abstractmethod


class AdOpsAdapter(ABC):
    """What any data source (stub or live GAM) must be able to answer."""

    @abstractmethod
    def list_campaigns(self) -> list[dict]: ...

    @abstractmethod
    def get_campaign(self, campaign_id: str) -> dict: ...

    @abstractmethod
    def get_recent_changes(self) -> list[dict]: ...

    @abstractmethod
    def list_runbooks(self) -> list[str]: ...

    @abstractmethod
    def get_runbook(self, name: str) -> str: ...

    @abstractmethod
    def get_ad_policy(self) -> str: ...


class StubAdapter(AdOpsAdapter):
    """Reads the offline synthetic ad-ops data under adops/. Demo only."""

    def __init__(self, root: str):
        self.root = root  # path to the adops/ directory

    def list_campaigns(self) -> list[dict]:
        files = sorted(glob.glob(os.path.join(self.root, "campaigns", "*.json")))
        campaigns = []
        for f in files:
            with open(f) as fh:
                campaigns.append(json.load(fh))
        return campaigns

    def get_campaign(self, campaign_id: str) -> dict:
        path = os.path.join(self.root, "campaigns", f"{campaign_id}.json")
        with open(path) as fh:
            return json.load(fh)

    def get_recent_changes(self) -> list[dict]:
        with open(os.path.join(self.root, "changes", "recent.json")) as fh:
            return json.load(fh)["changes"]

    def list_runbooks(self) -> list[str]:
        files = sorted(glob.glob(os.path.join(self.root, "runbooks", "*.md")))
        return [os.path.splitext(os.path.basename(f))[0] for f in files]

    def get_runbook(self, name: str) -> str:
        path = os.path.join(self.root, "runbooks", f"{name}.md")
        with open(path) as fh:
            return fh.read()

    def get_ad_policy(self) -> str:
        with open(os.path.join(self.root, "ad-policy.md")) as fh:
            return fh.read()


class GAMAdapter(AdOpsAdapter):
    """
    PRODUCTION adapter — placeholder. Same interface as StubAdapter.

    In production each method calls the Google Ad Manager API (delivery / fill /
    pacing reports, line-item configs, creative statuses) and SpringServe's API,
    authenticating with a service account. The agent code above it never changes.
    """

    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "GAMAdapter is the production swap: wire it to the GAM/SpringServe API. "
            "The agent works unchanged once this returns the same shapes as StubAdapter."
        )
