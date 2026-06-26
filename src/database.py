import os
import json
import math
import hashlib
import logging
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from .config import OPENROUTER_EMBED_URL, EMBED_MODEL, EMBED_TIMEOUT, RAG_TOP_K, RAG_SIMILARITY_THRESHOLD

AUTH_SALT = "mlpg_salt_2026_xyz"

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
DB_DIR = PROJECT_ROOT / 'data'
DB_PATH = DB_DIR / 'mlpg_history.db'


def _get_api_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY non trovata per embeddings.")
    return key


def _get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            topic TEXT NOT NULL,
            level TEXT NOT NULL,
            created_at TEXT NOT NULL,
            riepilogo TEXT
        );

        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            module_index INTEGER NOT NULL,
            titolo TEXT NOT NULL,
            spiegazione TEXT NOT NULL,
            esercizio TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            archived INTEGER DEFAULT 0,
            embedding TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            soluzione TEXT,
            esito TEXT,
            feedback_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (module_id) REFERENCES modules(id)
        );

        CREATE INDEX IF NOT EXISTS idx_modules_session ON modules(session_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_module ON attempts(module_id);
    """)
    # Migrazione: aggiungi user_id a sessions se manca (DB pre-esistenti)
    cursor = conn.execute("PRAGMA table_info(sessions)")
    cols = [row[1] for row in cursor.fetchall()]
    if "user_id" not in cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")
    conn.commit()
    conn.close()


# ── embedding ──────────────────────────────────────────────

def compute_embedding(text: str) -> list[float]:
    api_key = _get_api_key()
    payload = {"model": EMBED_MODEL, "input": text}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_EMBED_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "MLPG-History/1.0",
        },
        method="POST",
    )
    logger.debug("Calcolo embedding per testo (%d caratteri)", len(text))
    try:
        with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.debug("Embedding calcolato con successo")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        logger.error("Embedding HTTP %s: %s", exc.code, body_text[:200])
        raise RuntimeError(f"Embedding HTTP {exc.code}: {body_text}") from exc

    try:
        return body["data"][0]["embedding"]
    except (KeyError, IndexError):
        raise RuntimeError("Risposta embedding non valida.")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── autenticazione ──────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256((password + AUTH_SALT).encode()).hexdigest()


def create_user(username: str, password: str) -> int | None:
    logger.info("Creazione utente: username=%s", username)
    conn = _get_conn()
    now = datetime.now().isoformat()
    hashed = _hash_password(password)
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed, now),
        )
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return uid
    except sqlite3.IntegrityError:
        logger.warning("Username già esistente: %s", username)
        conn.close()
        return None


def authenticate_user(username: str, password: str) -> dict | None:
    conn = _get_conn()
    hashed = _hash_password(password)
    row = conn.execute(
        "SELECT id, username FROM users WHERE username = ? AND password = ?",
        (username, hashed),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── salvataggio ────────────────────────────────────────────

def save_session(topic: str, level: str, modules_data: list[dict], user_id: int | None = None) -> int:
    logger.info("Salvataggio sessione: topic=%s, level=%s, moduli=%d", topic, level, len(modules_data))
    conn = _get_conn()
    now = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO sessions (topic, level, created_at, user_id) VALUES (?, ?, ?, ?)",
        (topic, level, now, user_id),
    )
    session_id = cur.lastrowid

    for i, mod in enumerate(modules_data):
        testo_embed = f"{mod.get('titolo_modulo', mod.get('titolo', ''))} {mod.get('spiegazione', '')}"
        titolo = mod.get("titolo_modulo") or mod.get("titolo", "")
        spiegazione = mod.get("spiegazione", "")
        esercizio = mod.get("esercizio_pratico") or mod.get("esercizio", "")
        try:
            emb = compute_embedding(testo_embed)
            emb_json = json.dumps(emb)
        except Exception:
            emb_json = None

        conn.execute(
            "INSERT INTO modules (session_id, module_index, titolo, spiegazione, esercizio, embedding) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, i, titolo, spiegazione, esercizio, emb_json),
        )

    conn.commit()
    conn.close()
    return session_id


def save_attempt(module_db_id: int, soluzione: str, esito: str, feedback_json: str):
    logger.info("Salvataggio tentativo: module_id=%s, esito=%s", module_db_id, esito)
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO attempts (module_id, soluzione, esito, feedback_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (module_db_id, soluzione, esito, feedback_json, now),
    )
    conn.commit()
    conn.close()


def update_module_state(module_db_id: int, completed: bool = False, archived: bool = False):
    conn = _get_conn()
    conn.execute(
        "UPDATE modules SET completed = ?, archived = ? WHERE id = ?",
        (1 if completed else 0, 1 if archived else 0, module_db_id),
    )
    conn.commit()
    conn.close()


def rename_module(module_db_id: int, new_title: str):
    logger.info("Rinomina modulo: id=%s, nuovo_titolo=%s", module_db_id, new_title)
    conn = _get_conn()
    conn.execute("UPDATE modules SET titolo = ? WHERE id = ?", (new_title, module_db_id))
    conn.commit()
    conn.close()


def delete_module(module_db_id: int):
    logger.info("Elimina modulo: id=%s", module_db_id)
    conn = _get_conn()
    session_id_row = conn.execute(
        "SELECT session_id FROM modules WHERE id = ?", (module_db_id,)
    ).fetchone()
    session_id = session_id_row["session_id"] if session_id_row else None
    conn.execute("DELETE FROM attempts WHERE module_id = ?", (module_db_id,))
    conn.execute("DELETE FROM modules WHERE id = ?", (module_db_id,))
    if session_id:
        remaining = conn.execute(
            "SELECT COUNT(*) as cnt FROM modules WHERE session_id = ?", (session_id,)
        ).fetchone()
        if remaining["cnt"] == 0:
            logger.info("Nessun modulo rimasto, elimino sessione: id=%s", session_id)
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def rename_session(session_id: int, new_topic: str):
    logger.info("Rinomina sessione: id=%s, nuovo_topic=%s", session_id, new_topic)
    conn = _get_conn()
    conn.execute("UPDATE sessions SET topic = ? WHERE id = ?", (new_topic, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: int):
    logger.info("Elimina sessione: id=%s", session_id)
    conn = _get_conn()
    conn.execute(
        "DELETE FROM attempts WHERE module_id IN (SELECT id FROM modules WHERE session_id = ?)",
        (session_id,),
    )
    conn.execute("DELETE FROM modules WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_riepilogo(session_id: int, riepilogo_text: str):
    conn = _get_conn()
    conn.execute("UPDATE sessions SET riepilogo = ? WHERE id = ?", (riepilogo_text, session_id))
    conn.commit()
    conn.close()


# ── lettura storico ────────────────────────────────────────

def get_all_sessions(user_id: int | None = None) -> list[dict]:
    conn = _get_conn()
    if user_id:
        rows = conn.execute(
            "SELECT id, topic, level, created_at, riepilogo FROM sessions WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, topic, level, created_at, riepilogo FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_modules(session_id: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, module_index, titolo, spiegazione, esercizio, completed, archived "
        "FROM modules WHERE session_id = ? ORDER BY module_index",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_module_attempts(module_db_id: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT soluzione, esito, feedback_json, created_at FROM attempts WHERE module_id = ? ORDER BY created_at",
        (module_db_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── RAG retrieval ──────────────────────────────────────────

def find_similar_modules(query: str, top_k: int = 5) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT m.id, m.titolo, m.spiegazione, m.esercizio, m.embedding, s.topic, s.level "
        "FROM modules m JOIN sessions s ON m.session_id = s.id "
        "WHERE m.embedding IS NOT NULL "
        "ORDER BY s.created_at DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return []

    try:
        q_emb = compute_embedding(query)
    except Exception:
        return []

    scored = []
    for r in rows:
        try:
            m_emb = json.loads(r["embedding"])
        except (TypeError, json.JSONDecodeError):
            continue
        sim = _cosine_similarity(q_emb, m_emb)
        scored.append((sim, dict(r)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k] if _ > RAG_SIMILARITY_THRESHOLD]
