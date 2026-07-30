"""
Central config — models and the API client live in ONE place.

Model portfolio (from the workshop). Routing later uses the fast model to triage
severity cheaply and only escalates hard cases to the strong model.
"""
import os

import anthropic

# The strong model does the reasoning; the fast model does cheap triage/judging.
MODEL_STRONG = "claude-sonnet-5"
MODEL_FAST = "claude-haiku-4-5"

# Resolve the adops/ data directory relative to the repo root (…/always-on-agent/adops).
ADOPS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "adops")


def get_client():
    """The single place we build the Claude client.

    Reads ANTHROPIC_API_KEY from the environment. For Amazon Bedrock, swap this
    for anthropic.AnthropicBedrock() — nothing else in the agent changes.
    """
    return anthropic.Anthropic()
