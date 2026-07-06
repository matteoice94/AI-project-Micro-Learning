import os
import json
import math
import functools
import bcrypt
import hashlib
import logging
import sqlite3
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from .config import OPENROUTER_EMBED_URL, EMBED_MODEL, EMBED_TIMEOUT, RAG_TOP_K, RAG_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
DB_DIR = PROJECT_ROOT / 'data'
DB_PATH = DB_DIR / 'mlpg_history.db'

# ── Backend detection ──────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
IS_PG = bool(DATABASE_URL)

if IS_PG:
    try:
        import psycopg2
        import psycopg2.extras
        import psycopg2.errors
    except ImportError:
        IS_PG = False


def _adapt(sql: str) -> str:
    """Converte ? → %s per PostgreSQL"""
    if IS_PG:
        return sql.replace("?", "%s")
    return sql


class _DB:
    """Wrapper che unifica sqlite3 e psycopg2 sotto un'unica interfaccia."""

    def __init__(self, conn, backend: str):
        self._conn = conn
        self._backend = backend  # 'pg' or 'sqlite'

    def execute(self, sql: str, params=None):
        cur = self._conn.cursor()
        if params is not None:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def cursor(self):
        return self._conn.cursor()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _get_conn():
    if IS_PG:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return _DB(conn, "pg")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return _DB(conn, "sqlite")


def _insert_returning_id(conn, sql: str, params: tuple) -> int:
    """INSERT e ritorna l'ID generato (funziona su entrambi i backend)"""
    cur = conn.cursor()
    cur.execute(_adapt(sql + (" RETURNING id" if IS_PG else "")), params)
    if IS_PG:
        row = cur.fetchone()
        cur.close()
        return row["id"]
    cur.close()
    return cur.lastrowid


# ── DDL ─────────────────────────────────────────────────────

def _exec_ddl(conn, statements: list[str]):
    """Esegue una lista di statement DDL"""
    cur = conn.cursor()
    for stmt in statements:
        cur.execute(stmt)
    cur.close()


SCHEMA_SQLITE = """
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

CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_active_date TEXT,
    badges TEXT DEFAULT '[]',
    total_correct INTEGER DEFAULT 0,
    total_wrong INTEGER DEFAULT 0,
    total_modules_completed INTEGER DEFAULT 0,
    total_paths_completed INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    topics_studied TEXT DEFAULT '[]',
    consecutive_correct INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    topic TEXT NOT NULL,
    level TEXT NOT NULL,
    created_at TEXT NOT NULL,
    riepilogo TEXT
);

CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    module_index INTEGER NOT NULL,
    titolo TEXT NOT NULL,
    spiegazione TEXT NOT NULL,
    esercizio TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    archived INTEGER DEFAULT 0,
    embedding TEXT
);

CREATE TABLE IF NOT EXISTS attempts (
    id SERIAL PRIMARY KEY,
    module_id INTEGER NOT NULL REFERENCES modules(id),
    soluzione TEXT,
    esito TEXT,
    feedback_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_modules_session ON modules(session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_module ON attempts(module_id);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_active_date TEXT,
    badges TEXT DEFAULT '[]',
    total_correct INTEGER DEFAULT 0,
    total_wrong INTEGER DEFAULT 0,
    total_modules_completed INTEGER DEFAULT 0,
    total_paths_completed INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    topics_studied TEXT DEFAULT '[]',
    consecutive_correct INTEGER DEFAULT 0
);
"""


def init_db():
    conn = _get_conn()
    statements = (SCHEMA_PG if IS_PG else SCHEMA_SQLITE).strip().split(";")
    _exec_ddl(conn, [s.strip() + ";" for s in statements if s.strip()])
    if not IS_PG:
        cursor = conn.execute("PRAGMA table_info(sessions)")
        cols = [row[1] for row in cursor.fetchall()]
        if "user_id" not in cols:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")
    conn.commit()
    conn.close()


# ── embedding ──────────────────────────────────────────────

@functools.lru_cache(maxsize=128)
def compute_embedding(text: str) -> tuple[float, ...]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY non trovata per embeddings.")
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
        emb = body["data"][0]["embedding"]
        return tuple(emb)
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
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _is_legacy_sha256(hashed: str) -> bool:
    return len(hashed) == 64 and all(c in "0123456789abcdef" for c in hashed.lower())


def create_user(username: str, password: str) -> int | None:
    logger.info("Creazione utente: username=%s", username)
    conn = _get_conn()
    now = datetime.now().isoformat()
    hashed = _hash_password(password)
    try:
        uid = _insert_returning_id(
            conn,
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, hashed, now),
        )
        conn.commit()
        conn.close()
        return uid
    except Exception as exc:
        if IS_PG and isinstance(exc, psycopg2.errors.UniqueViolation):
            logger.warning("Username già esistente: %s", username)
        elif not IS_PG and "UNIQUE constraint" in str(exc):
            logger.warning("Username già esistente: %s", username)
        else:
            logger.error("Errore creazione utente: %s", exc, exc_info=True)
        conn.rollback()
        conn.close()
        return None


def authenticate_user(username: str, password: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        _adapt("SELECT id, username, password FROM users WHERE username = ?"),
        (username,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    stored = row["password"]

    # bcrypt
    if _verify_password(password, stored):
        return {"id": row["id"], "username": row["username"]}

    # legacy SHA-256 migration
    if _is_legacy_sha256(stored):
        legacy_hash = hashlib.sha256((password + "mlpg_salt_2026_xyz").encode()).hexdigest()
        if legacy_hash == stored:
            new_hash = _hash_password(password)
            conn2 = _get_conn()
            conn2.execute(_adapt("UPDATE users SET password = ? WHERE id = ?"), (new_hash, row["id"]))
            conn2.commit()
            conn2.close()
            logger.info("Password migrata a bcrypt per utente: %s", username)
            return {"id": row["id"], "username": row["username"]}

    return None


def get_user_by_id(user_id: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        _adapt("SELECT id, username FROM users WHERE id = ?"), (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── user_stats (gamification) ──────────────────────────────

def ensure_user_stats(user_id: int) -> dict:
    conn = _get_conn()
    row = conn.execute(
        _adapt("SELECT * FROM user_stats WHERE user_id = ?"), (user_id,)
    ).fetchone()
    if not row:
        conn.execute(
            _adapt("INSERT INTO user_stats (user_id) VALUES (?)"), (user_id,)
        )
        conn.commit()
        row = conn.execute(
            _adapt("SELECT * FROM user_stats WHERE user_id = ?"), (user_id,)
        ).fetchone()
    conn.close()
    return dict(row) if row else {}


def update_user_stats(user_id: int, updates: dict):
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]
    conn = _get_conn()
    conn.execute(
        _adapt(f"UPDATE user_stats SET {set_clause} WHERE user_id = ?"),
        tuple(values),
    )
    conn.commit()
    conn.close()


def get_user_stats(user_id: int) -> dict:
    return ensure_user_stats(user_id)


def get_leaderboard(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        _adapt(
            "SELECT u.username, s.xp, s.level, s.current_streak, s.total_modules_completed "
            "FROM user_stats s JOIN users u ON s.user_id = u.id "
            "ORDER BY s.xp DESC LIMIT ?"
        ),
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_topic_stats(user_id: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        _adapt(
            "SELECT topic, COUNT(*) as session_count FROM sessions "
            "WHERE user_id = ? GROUP BY topic ORDER BY session_count DESC"
        ),
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_accuracy(user_id: int) -> float:
    stats = get_user_stats(user_id)
    total = stats.get("total_correct", 0) + stats.get("total_wrong", 0)
    if total == 0:
        return 0.0
    return stats.get("total_correct", 0) / total * 100


def get_user_weekly_activity(user_id: int) -> list[dict]:
    from datetime import date, timedelta
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    conn = _get_conn()
    rows = conn.execute(
        _adapt(
            "SELECT DATE(a.created_at) as day, COUNT(*) as count "
            "FROM attempts a JOIN modules m ON a.module_id = m.id "
            "JOIN sessions s ON m.session_id = s.id "
            "WHERE s.user_id = ? "
            "AND a.created_at >= ? "
            "GROUP BY day ORDER BY day"
        ),
        (user_id, seven_days_ago),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def award_user_xp(user_id: int | None, reason: str, topic: str = "", is_first_try: bool = True) -> tuple[int, list[str]]:
    """Award XP and update stats. Returns (xp_awarded, new_badges)."""
    from .gamification import award_xp, check_badges, update_streak, level_from_xp
    from datetime import date
    import json

    if not user_id:
        return 0, []

    stats = ensure_user_stats(user_id)
    xp_gain = award_xp(reason)
    if xp_gain == 0:
        return 0, []

    current_xp = stats.get("xp", 0) + xp_gain
    new_level = level_from_xp(current_xp)
    new_streak, new_max = update_streak(stats)

    updates = {
        "xp": current_xp,
        "level": new_level,
        "current_streak": new_streak,
        "max_streak": max(stats.get("max_streak", 0), new_max),
        "last_active_date": date.today().isoformat(),
        "total_modules_completed": stats.get("total_modules_completed", 0) + 1,
        "total_correct": stats.get("total_correct", 0) + 1,
        "total_sessions": stats.get("total_sessions", 0) + 1,
    }

    if is_first_try:
        updates["consecutive_correct"] = stats.get("consecutive_correct", 0) + 1
    else:
        updates["consecutive_correct"] = 0

    if reason == "path_completed":
        updates["total_paths_completed"] = stats.get("total_paths_completed", 0) + 1

    if topic:
        topics = json.loads(stats.get("topics_studied", "[]")) if isinstance(stats.get("topics_studied"), str) else stats.get("topics_studied", [])
        if topic not in topics:
            topics.append(topic)
            updates["topics_studied"] = json.dumps(topics)

    update_user_stats(user_id, updates)

    updated_stats = {**stats, **updates}
    new_badges, all_badges = check_badges(updated_stats)
    if new_badges:
        update_user_stats(user_id, {"badges": json.dumps(all_badges)})

    return xp_gain, new_badges


def track_wrong_answer(user_id: int | None):
    """Track wrong answer for accuracy stats (no XP)."""
    from datetime import date
    from .gamification import update_streak
    if not user_id:
        return
    stats = ensure_user_stats(user_id)
    new_streak, new_max = update_streak(stats)
    updates = {
        "total_wrong": stats.get("total_wrong", 0) + 1,
        "consecutive_correct": 0,
        "last_active_date": date.today().isoformat(),
        "current_streak": new_streak,
        "max_streak": max(stats.get("max_streak", 0), new_max),
        "total_sessions": stats.get("total_sessions", 0) + 1,
    }
    update_user_stats(user_id, updates)


def backfill_user_stats():
    """Popola user_stats per tutti gli utenti esistenti usando i dati storici."""
    from .gamification import level_from_xp, check_badges
    import json
    from datetime import date

    conn = _get_conn()
    users = conn.execute("SELECT id, username FROM users").fetchall()
    if not users:
        conn.close()
        return

    for user in users:
        user_id = user["id"]

        completed = conn.execute(
            _adapt(
                "SELECT COUNT(*) as cnt FROM modules m "
                "JOIN sessions s ON m.session_id = s.id "
                "WHERE s.user_id = ? AND m.completed = 1"
            ), (user_id,),
        ).fetchone()["cnt"] or 0

        correct = conn.execute(
            _adapt(
                "SELECT COUNT(*) as cnt FROM attempts a "
                "JOIN modules m ON a.module_id = m.id "
                "JOIN sessions s ON m.session_id = s.id "
                "WHERE s.user_id = ? AND a.esito = 'corretta'"
            ), (user_id,),
        ).fetchone()["cnt"] or 0

        wrong = conn.execute(
            _adapt(
                "SELECT COUNT(*) as cnt FROM attempts a "
                "JOIN modules m ON a.module_id = m.id "
                "JOIN sessions s ON m.session_id = s.id "
                "WHERE s.user_id = ? AND a.esito != 'corretta'"
            ), (user_id,),
        ).fetchone()["cnt"] or 0

        sessions = conn.execute(
            _adapt("SELECT COUNT(*) as cnt FROM sessions WHERE user_id = ?"),
            (user_id,),
        ).fetchone()["cnt"] or 0

        paths = conn.execute(
            _adapt(
                "SELECT s.id FROM sessions s JOIN modules m ON m.session_id = s.id "
                "WHERE s.user_id = ? AND m.completed = 1 "
                "GROUP BY s.id HAVING COUNT(*) = 3"
            ), (user_id,),
        ).fetchall()
        path_count = len(paths)

        topics_rows = conn.execute(
            _adapt("SELECT DISTINCT topic FROM sessions WHERE user_id = ?"),
            (user_id,),
        ).fetchall()
        topics = [r["topic"] for r in topics_rows if r["topic"]]

        last_activity = conn.execute(
            _adapt(
                "SELECT MAX(a.created_at) as last_date FROM attempts a "
                "JOIN modules m ON a.module_id = m.id "
                "JOIN sessions s ON m.session_id = s.id "
                "WHERE s.user_id = ?"
            ), (user_id,),
        ).fetchone()["last_date"]

        # XP: 15 per modulo completato + 25 per percorso completato
        xp = completed * 15 + path_count * 25
        lvl = level_from_xp(xp)

        streak = 0
        if last_activity:
            try:
                ld = datetime.strptime(last_activity[:10], "%Y-%m-%d").date()
                if (date.today() - ld).days <= 1:
                    streak = 1
            except (ValueError, TypeError):
                pass

        stats_dict = {
            "total_correct": correct,
            "total_wrong": wrong,
            "total_modules_completed": completed,
            "total_paths_completed": path_count,
            "total_sessions": sessions,
            "topics_studied": json.dumps(topics),
            "badges": "[]",
            "level": lvl,
            "current_streak": streak,
            "max_streak": streak,
            "last_active_date": last_activity[:10] if last_activity else None,
            "xp": xp,
            "consecutive_correct": 0,
        }

        _, all_badges = check_badges(stats_dict)

        existing = conn.execute(
            _adapt("SELECT user_id FROM user_stats WHERE user_id = ?"),
            (user_id,),
        ).fetchone()

        if existing:
            conn.execute(_adapt(
                "UPDATE user_stats SET xp=?, level=?, current_streak=?, max_streak=?, "
                "last_active_date=?, badges=?, total_correct=?, total_wrong=?, "
                "total_modules_completed=?, total_paths_completed=?, total_sessions=?, "
                "topics_studied=? WHERE user_id=?"
            ), (xp, lvl, streak, streak, last_activity[:10] if last_activity else None,
                json.dumps(all_badges), correct, wrong, completed, path_count,
                sessions, json.dumps(topics), user_id))
        else:
            conn.execute(_adapt(
                "INSERT INTO user_stats (user_id, xp, level, current_streak, max_streak, "
                "last_active_date, badges, total_correct, total_wrong, "
                "total_modules_completed, total_paths_completed, total_sessions, "
                "topics_studied) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
            ), (user_id, xp, lvl, streak, streak,
                last_activity[:10] if last_activity else None,
                json.dumps(all_badges), correct, wrong, completed,
                path_count, sessions, json.dumps(topics)))

        logger.info("Backfill %s: %d mod, %d XP, lv%d, %d badge",
                     user["username"], completed, xp, lvl, len(all_badges))

    conn.commit()
    conn.close()
    logger.info("Backfill user_stats completato")


# ── salvataggio ────────────────────────────────────────────

def save_session(topic: str, level: str, modules_data: list[dict], user_id: int | None = None) -> int:
    logger.info("Salvataggio sessione: topic=%s, level=%s, moduli=%d", topic, level, len(modules_data))
    conn = _get_conn()
    now = datetime.now().isoformat()
    session_id = _insert_returning_id(
        conn,
        "INSERT INTO sessions (topic, level, created_at, user_id) VALUES (?, ?, ?, ?)",
        (topic, level, now, user_id),
    )

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
            _adapt("INSERT INTO modules (session_id, module_index, titolo, spiegazione, esercizio, embedding) "
                    "VALUES (?, ?, ?, ?, ?, ?)"),
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
        _adapt("INSERT INTO attempts (module_id, soluzione, esito, feedback_json, created_at) VALUES (?, ?, ?, ?, ?)"),
        (module_db_id, soluzione, esito, feedback_json, now),
    )
    conn.commit()
    conn.close()


def update_module_state(module_db_id: int, completed: bool = False, archived: bool = False):
    conn = _get_conn()
    conn.execute(
        _adapt("UPDATE modules SET completed = ?, archived = ? WHERE id = ?"),
        (1 if completed else 0, 1 if archived else 0, module_db_id),
    )
    conn.commit()
    conn.close()


def rename_module(module_db_id: int, new_title: str):
    logger.info("Rinomina modulo: id=%s, nuovo_titolo=%s", module_db_id, new_title)
    conn = _get_conn()
    conn.execute(_adapt("UPDATE modules SET titolo = ? WHERE id = ?"), (new_title, module_db_id))
    conn.commit()
    conn.close()


def delete_module(module_db_id: int):
    logger.info("Elimina modulo: id=%s", module_db_id)
    conn = _get_conn()
    session_id_row = conn.execute(
        _adapt("SELECT session_id FROM modules WHERE id = ?"), (module_db_id,)
    ).fetchone()
    session_id = session_id_row["session_id"] if session_id_row else None
    conn.execute(_adapt("DELETE FROM attempts WHERE module_id = ?"), (module_db_id,))
    conn.execute(_adapt("DELETE FROM modules WHERE id = ?"), (module_db_id,))
    if session_id:
        remaining = conn.execute(
            _adapt("SELECT COUNT(*) as cnt FROM modules WHERE session_id = ?"), (session_id,)
        ).fetchone()
        if remaining["cnt"] == 0:
            logger.info("Nessun modulo rimasto, elimino sessione: id=%s", session_id)
            conn.execute(_adapt("DELETE FROM sessions WHERE id = ?"), (session_id,))
    conn.commit()
    conn.close()


def rename_session(session_id: int, new_topic: str):
    logger.info("Rinomina sessione: id=%s, nuovo_topic=%s", session_id, new_topic)
    conn = _get_conn()
    conn.execute(_adapt("UPDATE sessions SET topic = ? WHERE id = ?"), (new_topic, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: int):
    logger.info("Elimina sessione: id=%s", session_id)
    conn = _get_conn()
    conn.execute(
        _adapt("DELETE FROM attempts WHERE module_id IN (SELECT id FROM modules WHERE session_id = ?)"),
        (session_id,),
    )
    conn.execute(_adapt("DELETE FROM modules WHERE session_id = ?"), (session_id,))
    conn.execute(_adapt("DELETE FROM sessions WHERE id = ?"), (session_id,))
    conn.commit()
    conn.close()


def save_riepilogo(session_id: int, riepilogo_text: str):
    conn = _get_conn()
    conn.execute(_adapt("UPDATE sessions SET riepilogo = ? WHERE id = ?"), (riepilogo_text, session_id))
    conn.commit()
    conn.close()


# ── lettura storico ────────────────────────────────────────

def get_all_sessions(user_id: int | None = None) -> list[dict]:
    conn = _get_conn()
    if user_id:
        rows = conn.execute(
            _adapt("SELECT id, topic, level, created_at, riepilogo FROM sessions WHERE user_id = ? ORDER BY created_at DESC"),
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
        _adapt("SELECT id, module_index, titolo, spiegazione, esercizio, completed, archived "
               "FROM modules WHERE session_id = ? ORDER BY module_index"),
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_module_attempts(module_db_id: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        _adapt("SELECT soluzione, esito, feedback_json, created_at FROM attempts WHERE module_id = ? ORDER BY created_at"),
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
        "ORDER BY s.created_at DESC "
        "LIMIT 200"
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
