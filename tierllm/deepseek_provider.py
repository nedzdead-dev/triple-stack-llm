"""Tier 2 — DeepSeek (OpenAI-compatible HTTP API). The cheap-but-capable middle tier.

Strong enough for reasoning/analysis/writing that a small local model can't do,
at a fraction of premium-tier cost. Zero heavy dependencies (uses `requests`).
"""
import time
import logging

from .config import Config

log = logging.getLogger("tierllm.deepseek")

_usage = {"calls": 0, "in_tok": 0, "out_tok": 0, "errors": 0, "cost": 0.0}


def is_available() -> bool:
    return bool(Config.DEEPSEEK_KEY)


def generate(prompt, model=None, max_tokens=2048, temperature=0.3, system=None) -> str:
    """Returns text, or None on any failure (router falls through to next tier)."""
    if not is_available():
        return None
    import requests

    model = model or Config.DEEPSEEK_MODEL
    messages = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "stream": False}
    headers = {"Authorization": f"Bearer {Config.DEEPSEEK_KEY}", "Content-Type": "application/json"}

    for attempt in range(Config.CLOUD_RETRIES):
        t0 = time.time()
        try:
            r = requests.post(f"{Config.DEEPSEEK_BASE_URL}/chat/completions",
                              json=body, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                text = data["choices"][0]["message"]["content"].strip()
                u = data.get("usage", {})
                cost = (u.get("prompt_tokens", 0) * Config.PRICE_DEEPSEEK_IN
                        + u.get("completion_tokens", 0) * Config.PRICE_DEEPSEEK_OUT)
                _usage["calls"] += 1
                _usage["in_tok"] += u.get("prompt_tokens", 0)
                _usage["out_tok"] += u.get("completion_tokens", 0)
                _usage["cost"] += cost
                log.info("deepseek %s: %d+%d tok, %dms, ~$%.5f", model,
                         u.get("prompt_tokens", 0), u.get("completion_tokens", 0),
                         int((time.time() - t0) * 1000), cost)
                return text
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            log.warning("deepseek HTTP %s: %s", r.status_code, r.text[:200])
            _usage["errors"] += 1
            return None
        except Exception as e:
            log.warning("deepseek attempt %d failed: %s", attempt, e)
            time.sleep(2 ** attempt)
    _usage["errors"] += 1
    return None


def get_usage():
    return {**_usage, "cost": round(_usage["cost"], 5)}
