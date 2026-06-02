"""TierRouter — route each task to the cheapest tier that can do it, escalating
on a failed quality gate.

    local (on-device, $0) ──gate──▶ deepseek (cheap cloud) ──▶ claude (premium)

You pick a *starting* tier per task; the router tries it, validates with a gate,
and falls through to the next tier on failure or unavailability. Any tier whose
key/dependency is missing is simply skipped — nothing crashes.
"""
import logging

from . import local_engine, deepseek_provider, claude_provider
from . import gates as _gates

log = logging.getLogger("tierllm.router")

# Ordered escalation chain. Starting at tier X tries X, then everything after it.
_CHAIN = ["local", "deepseek", "claude"]

_PROVIDERS = {
    "local": local_engine,
    "deepseek": deepseek_provider,
    "claude": claude_provider,
}


class Result:
    def __init__(self, text, tier, escalations):
        self.text = text            # str | None
        self.tier = tier            # which tier produced it ('local'|'deepseek'|'claude'|None)
        self.escalations = escalations  # tiers that were tried and failed before success

    def __repr__(self):
        return f"Result(tier={self.tier!r}, text={ (self.text or '')[:60]!r})"


class TierRouter:
    """Stateless orchestrator over the three tiers."""

    def available_tiers(self):
        return {name: prov.is_available() for name, prov in _PROVIDERS.items()}

    def complete(self, prompt, tier="local", gate=None, max_tokens=1024,
                 temperature=0.3, system=None, **gate_kwargs) -> Result:
        """Run `prompt`, starting at `tier` and escalating on gate failure.

        Args:
            tier:  starting tier — 'local' (narrow tasks), 'deepseek' (reasoning),
                   or 'claude' (premium). Cheaper tiers below the start are skipped.
            gate:  a callable, a gate name ('label'|'json'|'number'|'grounded'|
                   'nonempty'), or None (-> nonempty). Output must pass or it escalates.
            gate_kwargs: passed to the gate (e.g. labels=[...], lo=0, hi=100, source=...).
        Returns:
            Result(text, tier, escalations). text is None only if every tier failed.
        """
        if tier not in _CHAIN:
            raise ValueError(f"unknown tier {tier!r}; choose from {_CHAIN}")
        check = _gates.resolve(gate)
        start = _CHAIN.index(tier)
        escalations = []

        for name in _CHAIN[start:]:
            prov = _PROVIDERS[name]
            if not prov.is_available():
                continue
            retries = local_engine_retries() if name == "local" else 1
            for _ in range(retries):
                if name == "local":
                    out = prov.generate(prompt, max_tokens=max_tokens)
                else:
                    out = prov.generate(prompt, max_tokens=max_tokens,
                                        temperature=temperature, system=system)
                if out and check(out, **gate_kwargs):
                    return Result(out, name, escalations)
            escalations.append(name)
            log.info("tier %r failed gate -> escalating", name)

        return Result(None, None, escalations)

    def usage(self):
        """Aggregate spend across cloud tiers (local is always $0)."""
        ds, cl = deepseek_provider.get_usage(), claude_provider.get_usage()
        return {
            "deepseek": ds, "claude": cl, "local": {"calls": "n/a", "cost": 0.0},
            "total_cost": round(ds["cost"] + cl["cost"], 5),
        }


def local_engine_retries():
    from .config import Config
    return Config.LOCAL_MAX_RETRIES + 1
