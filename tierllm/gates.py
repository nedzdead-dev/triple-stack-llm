"""Quality gates — cheap, deterministic validators that decide whether a tier's
output can be trusted or must escalate to the next tier.

A gate is a callable: (text: str, **kwargs) -> bool. True = trust, False = escalate.
This is the mechanism that lets a small/cheap model do work *safely*: if its output
doesn't pass the gate, it transparently falls through to a stronger tier.
"""
import json
import re


def nonempty(text, **_):
    return bool(text and text.strip())


def short_label(text, labels=None, **_):
    """Output must be a short token; if `labels` given, must be one of them."""
    if not (text and text.strip()):
        return False
    token = re.sub(r"[^A-Za-z0-9_]", "", text.strip().split()[0]).upper()
    if labels:
        return token in {l.upper() for l in labels}
    return len(text.strip().split()) <= 3


def valid_json(text, **_):
    if not text:
        return False
    m = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if not m:
        return False
    try:
        json.loads(m.group())
        return True
    except Exception:
        return False


def number_in_range(text, lo=0.0, hi=100.0, **_):
    try:
        return lo <= float(str(text).strip().rstrip(".")) <= hi
    except Exception:
        return False


def grounded_in(text, source="", **_):
    """Every alphanumeric run of length>=4 in `text` must appear in `source`
    (guards against fabricated values when extracting from a document)."""
    src = (source or "").lower()
    for tok in re.findall(r"[A-Za-z0-9@._-]{4,}", (text or "").lower()):
        if tok not in src:
            return False
    return True


# registry so gates can be named by string in route()
GATES = {
    "nonempty": nonempty,
    "label": short_label,
    "json": valid_json,
    "number": number_in_range,
    "grounded": grounded_in,
}


def resolve(gate):
    """Accept a callable, a registry name, or None (-> nonempty)."""
    if gate is None:
        return nonempty
    if callable(gate):
        return gate
    if gate in GATES:
        return GATES[gate]
    raise ValueError(f"unknown gate {gate!r}; known: {list(GATES)}")
