"""Configuration — everything is environment-driven. No secrets in code."""
import os


class Config:
    # ---- Tier 1: local SLM (MLX / Qwen-class) ----
    LOCAL_MODEL = os.getenv("TRIPLESTACK_LOCAL_MODEL", "mlx-community/Qwen3.5-2B-4bit")
    LOCAL_ENABLED = os.getenv("TRIPLESTACK_LOCAL", "1") == "1"

    # ---- Tier 2: cheap cloud (DeepSeek, OpenAI-compatible) ----
    DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ---- Tier 3: premium cloud (Anthropic Claude) ----
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    # ---- behaviour ----
    LOCAL_MAX_RETRIES = int(os.getenv("TRIPLESTACK_LOCAL_RETRIES", "1"))
    REQUEST_TIMEOUT = float(os.getenv("TRIPLESTACK_TIMEOUT", "60"))
    CLOUD_RETRIES = int(os.getenv("TRIPLESTACK_CLOUD_RETRIES", "3"))

    # ---- pricing ($/token, override to match current rates) ----
    PRICE_DEEPSEEK_IN = float(os.getenv("PRICE_DEEPSEEK_IN", "0.27e-6"))
    PRICE_DEEPSEEK_OUT = float(os.getenv("PRICE_DEEPSEEK_OUT", "1.10e-6"))
    PRICE_CLAUDE_IN = float(os.getenv("PRICE_CLAUDE_IN", "0.80e-6"))
    PRICE_CLAUDE_OUT = float(os.getenv("PRICE_CLAUDE_OUT", "4.0e-6"))
