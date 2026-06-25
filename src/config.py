"""Configurazione centralizzata per il progetto MLPG."""

# ── OpenRouter Chat ────────────────────────────────────────
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "gpt-4o-mini"
CHAT_TIMEOUT = 60  # secondi per urlopen
CHAT_TEMPERATURE_DEFAULT = 0.7
CHAT_TEMPERATURE_HINT = 0.4

# ── Retry ──────────────────────────────────────────────────
MAX_RETRIES = 3
WAIT_SECONDS = 30

# ── OpenRouter Embedding ───────────────────────────────────
OPENROUTER_EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
EMBED_MODEL = "openai/text-embedding-3-small"
EMBED_TIMEOUT = 30

# ── RAG ────────────────────────────────────────────────────
RAG_TOP_K = 3
RAG_SIMILARITY_THRESHOLD = 0.3
