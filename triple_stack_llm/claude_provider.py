"""Tier 3 — Anthropic Claude. The premium tier / safety net.

Used only when the cheaper tiers can't (or for tasks you explicitly route here).
Requires the `anthropic` SDK:  pip install "triple_stack_llm[claude]"
"""
import time
import logging

from .config import Config

log = logging.getLogger("triple_stack_llm.claude")

_usage = {"calls": 0, "in_tok": 0, "out_tok": 0, "errors": 0, "cost": 0.0}
_client = None


def is_available() -> bool:
    if not Config.ANTHROPIC_KEY:
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic
        _client = Anthropic(api_key=Config.ANTHROPIC_KEY)
    return _client


def generate(prompt, model=None, max_tokens=2048, temperature=0.3, system=None) -> str:
    """Returns text, or None on any failure."""
    if not is_available():
        return None
    model = model or Config.CLAUDE_MODEL
    t0 = time.time()
    try:
        kwargs = {"model": model, "max_tokens": max_tokens, "temperature": temperature,
                  "messages": [{"role": "user", "content": prompt}]}
        if system:
            kwargs["system"] = system
        resp = _get_client().messages.create(**kwargs)
        text = resp.content[0].text.strip()
        cost = (resp.usage.input_tokens * Config.PRICE_CLAUDE_IN
                + resp.usage.output_tokens * Config.PRICE_CLAUDE_OUT)
        _usage["calls"] += 1
        _usage["in_tok"] += resp.usage.input_tokens
        _usage["out_tok"] += resp.usage.output_tokens
        _usage["cost"] += cost
        log.info("claude %s: %d+%d tok, %dms, ~$%.5f", model,
                 resp.usage.input_tokens, resp.usage.output_tokens,
                 int((time.time() - t0) * 1000), cost)
        return text
    except Exception as e:
        log.warning("claude failed: %s", e)
        _usage["errors"] += 1
        return None


def get_usage():
    return {**_usage, "cost": round(_usage["cost"], 5)}
