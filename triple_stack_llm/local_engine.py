"""Tier 1 — local SLM engine via Apple MLX (Qwen-class small models).

Runs entirely on-device at $0. Thread-safe lazy singleton. Degrades gracefully:
if `mlx-lm` isn't installed or the model can't load, is_available() returns False
and the router simply skips this tier.

Install the optional dependency to enable:  pip install "triple_stack_llm[local]"
"""
import logging
import threading

from .config import Config

log = logging.getLogger("triple_stack_llm.local")

_available = None
_avail_lock = threading.Lock()


def is_available() -> bool:
    """True if mlx-lm imports and the local tier is enabled. Never raises; cached."""
    global _available
    if _available is not None:
        return _available
    with _avail_lock:
        if _available is not None:
            return _available
        if not Config.LOCAL_ENABLED:
            _available = False
            return False
        try:
            import mlx_lm  # noqa: F401
            _available = True
        except Exception as e:
            log.info("local tier unavailable (mlx-lm not importable): %s", e)
            _available = False
        return _available


class _Engine:
    _inst = None
    _ctor_lock = threading.RLock()   # reentrant: instance() -> _load()
    _gen_lock = threading.Lock()     # MLX generation is not concurrent-safe

    def __init__(self):
        self._model = None
        self._tok = None
        self._loaded = False

    @classmethod
    def instance(cls):
        if cls._inst is None:
            with cls._ctor_lock:
                if cls._inst is None:
                    inst = cls()
                    inst._load()
                    cls._inst = inst
        return cls._inst

    def _load(self):
        if self._loaded:
            return
        with _Engine._ctor_lock:
            if self._loaded:
                return
            from mlx_lm import load
            log.info("loading local model %s ...", Config.LOCAL_MODEL)
            self._model, self._tok = load(Config.LOCAL_MODEL)
            self._loaded = True
            log.info("local model ready")

    def generate(self, prompt, max_tokens=512, enable_thinking=False) -> str:
        if not (isinstance(prompt, str) and prompt.strip()):
            raise ValueError("prompt must be a non-empty string")
        self._load()
        from mlx_lm import generate as mlx_generate
        messages = [{"role": "user", "content": prompt}]
        try:
            chat = self._tok.apply_chat_template(
                messages, add_generation_prompt=True, enable_thinking=enable_thinking)
        except TypeError:
            if not enable_thinking:
                messages[-1]["content"] += " /no_think"
            chat = self._tok.apply_chat_template(messages, add_generation_prompt=True)
        with self._gen_lock:
            out = mlx_generate(self._model, self._tok, prompt=chat,
                               max_tokens=max_tokens, verbose=False)
        return (out or "").strip()


def generate(prompt, max_tokens=512, enable_thinking=False):
    """Generate locally. Returns text, or None on any failure (router falls through)."""
    if not is_available():
        return None
    try:
        return _Engine.instance().generate(prompt, max_tokens=max_tokens,
                                            enable_thinking=enable_thinking)
    except Exception as e:
        log.warning("local generation failed: %s", e)
        return None


def warmup() -> bool:
    """Pre-load the model off the request path. Returns True on success."""
    if not is_available():
        return False
    try:
        _Engine.instance()
        return True
    except Exception as e:
        log.warning("warmup failed: %s", e)
        return False
