"""tierllm — route each task to the cheapest capable LLM tier.

    local (on-device SLM, $0) -> deepseek (cheap cloud) -> claude (premium)

Quick start:
    from tierllm import TierRouter
    r = TierRouter()
    res = r.complete("Say hi in 3 words", tier="deepseek")
    print(res.text, res.tier)
"""
from .router import TierRouter, Result
from . import local_engine, deepseek_provider, claude_provider, gates
from .config import Config

__version__ = "0.1.0"
__all__ = ["TierRouter", "Result", "Config", "gates",
           "local_engine", "deepseek_provider", "claude_provider", "warmup"]


def warmup():
    """Pre-load the local model off the request path (no-op if unavailable)."""
    return local_engine.warmup()
