# tierllm

**Route each task to the cheapest LLM tier that can actually do it.**

```
   local SLM (on-device, $0)  ──gate──▶  DeepSeek (cheap cloud)  ──▶  Claude (premium)
   narrow tasks: classify,             reasoning: analysis,          hardest cases +
   extract, tag                        writing, scoring             safety-net fallback
```

A small **3-tier router** that tries the cheapest model first, validates the output
with a deterministic **quality gate**, and transparently **escalates** to a stronger
tier only when needed. In production this routinely cuts LLM spend **~90%** versus
sending everything to a premium model — without sacrificing quality, because anything
the cheap tier can't do falls through to the one that can.

- **Tier 1 — local**: a small model on your machine via [Apple MLX](https://github.com/ml-explore/mlx) (e.g. Qwen-class). $0, offline, great at narrow/mechanical tasks.
- **Tier 2 — DeepSeek**: OpenAI-compatible, ~10× cheaper than premium APIs. Strong at reasoning/writing.
- **Tier 3 — Claude**: the premium tier / fallback for the hardest work.

Every tier is **optional** — missing a key or dependency just skips that tier. Nothing crashes.

---

## Install

```bash
pip install tierllm                 # core (DeepSeek + Claude tiers, requests-only)
pip install "tierllm[local]"        # + local on-device tier (Apple Silicon / MLX)
pip install "tierllm[claude]"       # + Anthropic SDK for the Claude tier
pip install "tierllm[all]"
```

## Configure (all via env — no secrets in code)

```bash
cp .env.example .env     # then fill in keys
export DEEPSEEK_API_KEY=sk-...        # tier 2
export ANTHROPIC_API_KEY=sk-ant-...   # tier 3 (optional)
# tier 1 is automatic if you installed [local] on Apple Silicon
```

## Use

```python
from tierllm import TierRouter

r = TierRouter()

# Narrow task → starts local ($0), escalates only if the gate fails
res = r.complete(
    "Classify this reply as one word — INTERESTED or UNSUBSCRIBE:\n'take me off your list'",
    tier="local",
    gate="label",
    labels=["INTERESTED", "UNSUBSCRIBE"],
)
print(res.text, "via", res.tier)        # -> UNSUBSCRIBE via local

# Reasoning task → starts at DeepSeek (cheap), falls back to Claude if it fails
res = r.complete("Write a 3-sentence cold email to a dentist about online booking.",
                 tier="deepseek")
print(res.text, "via", res.tier)

# See what it cost
print(r.usage())   # {'deepseek': {...}, 'claude': {...}, 'total_cost': 0.0021}
```

## Tiers & when to start where

| `tier=` | starts at | use for |
|---|---|---|
| `"local"` | on-device SLM | classification, extraction, tagging — narrow tasks |
| `"deepseek"` | cheap cloud | analysis, summarization, drafting — reasoning tasks |
| `"claude"` | premium | the hardest judgment, or when you want top quality |

Whatever tier you start at, the router escalates **downstream** through the chain on a
failed gate. Start `local` for max savings; start `deepseek` when you know a 2B can't do it.

## Quality gates (the safety mechanism)

A gate decides "trust this output or escalate." Built-ins (by name) or pass your own callable:

| gate | passes when | kwargs |
|---|---|---|
| `"nonempty"` | output is non-empty | — |
| `"label"` | a short token (optionally in a set) | `labels=[...]` |
| `"json"` | output parses as JSON | — |
| `"number"` | a number within a range | `lo=`, `hi=` |
| `"grounded"` | every token appears in a source (anti-hallucination) | `source=` |

```python
r.complete(prompt, tier="local", gate=lambda t, **k: t.strip().isdigit())
```

## Why this works
A small model is reliable on tasks where the answer is *in the text* or *clear-cut*,
but fails on judgment/knowledge. The **gate** catches those failures and escalates — so
you get cheap-tier economics with premium-tier correctness. Match the model to the task.

## Acknowledgments & credits

`tierllm` is glue around excellent work by others. Full credit to:

**The idea — LLM cascades / tiered routing**
- **FrugalGPT** — Chen, Zaharia & Zou (2023), *"FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance"* — the foundational work on cascading from cheap to expensive models. [arXiv:2305.05176](https://arxiv.org/abs/2305.05176)

**Tier 1 — local inference**
- **Apple MLX** — the on-device array/ML framework. [github.com/ml-explore/mlx](https://github.com/ml-explore/mlx)
- **mlx-lm** — LLM runners for MLX. [github.com/ml-explore/mlx-lm](https://github.com/ml-explore/mlx-lm)
- **Qwen** (Alibaba) — the default local model family. [github.com/QwenLM](https://github.com/QwenLM)
- **mlx-community** — community MLX model conversions on Hugging Face. [huggingface.co/mlx-community](https://huggingface.co/mlx-community)

**Tier 2 — cheap cloud**
- **DeepSeek** — DeepSeek-V3 and the OpenAI-compatible API. [github.com/deepseek-ai](https://github.com/deepseek-ai) · [deepseek.com](https://www.deepseek.com)

**Tier 3 — premium**
- **Anthropic Claude** and the `anthropic` Python SDK. [anthropic.com](https://www.anthropic.com)

All trademarks and models belong to their respective owners. `tierllm` is an independent
project and is not affiliated with or endorsed by Apple, Alibaba, DeepSeek, or Anthropic.
You are responsible for complying with each provider's terms of service and pricing.

See [NOTICE](NOTICE) for the full attribution list.

## License
MIT — see [LICENSE](LICENSE).
