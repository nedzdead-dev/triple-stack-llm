"""tierllm quickstart — run:  python examples/quickstart.py

Set DEEPSEEK_API_KEY (and optionally ANTHROPIC_API_KEY) first, and/or install the
local tier with: pip install "tierllm[local]" on Apple Silicon.
"""
import logging
from tierllm import TierRouter

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

r = TierRouter()
print("available tiers:", r.available_tiers())

# 1) Narrow task — starts local ($0), escalates only if the gate fails.
res = r.complete(
    "Reply with ONE word — INTERESTED or UNSUBSCRIBE:\n'please take me off your list'",
    tier="local", gate="label", labels=["INTERESTED", "UNSUBSCRIBE"], max_tokens=8)
print("\n[classify]", res.text, "via", res.tier)

# 2) Reasoning task — starts at DeepSeek (cheap), falls back to Claude if needed.
res = r.complete(
    "In 2 sentences, what does a tiered LLM router save a startup?",
    tier="deepseek", max_tokens=120)
print("\n[reason]", res.text, "via", res.tier)

# 3) Structured extraction with a JSON gate.
res = r.complete(
    'Extract name and email as JSON from: "Reach Dana at dana@acme.co". '
    'Output only {"name": "...", "email": "..."}',
    tier="deepseek", gate="json", max_tokens=60)
print("\n[extract]", res.text, "via", res.tier)

print("\nspend:", r.usage())
