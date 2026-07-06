"""Configurazione centralizzata per il progetto MLPG."""

# ── OpenRouter Chat ────────────────────────────────────────
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "gpt-4o-mini"
CHAT_TIMEOUT = 60  # secondi per urlopen
CHAT_TEMPERATURE_DEFAULT = 0.7
CHAT_TEMPERATURE_HINT = 0.4

# ── Sanity Check (Opzione C) ────────────────────────────────
ENABLE_SANITY_CHECK = True
SANITY_CHECK_TEMPERATURE = 0.1
SANITY_CHECK_TIMEOUT = 20

# ── Heuristic Filter (Opzione A) ───────────────────────────
ENABLE_HEURISTIC_FILTER = True

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

# ── Lingua ─────────────────────────────────────────────────
DEFAULT_LANG = "it"

# ── Traduzione (modello veloce per cambio lingua UI) ──────────
TRANSLATION_MODEL = "google/gemini-flash-1.5"
TRANSLATION_TEMPERATURE = 0.2
TRANSLATION_TIMEOUT = 30
