"""Test per src/database.py (usa temp DB per non sporcare il DB reale)."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import src.database as db


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test_mlpg.db")
    db.init_db()
    yield
    # cleanup after test
    db_path = tmp_path / "test_mlpg.db"
    if db_path.exists():
        db_path.unlink()


class TestInitDb:
    def test_init_creates_db(self, temp_db):
        assert db.DB_PATH.exists()

    def test_init_is_idempotent(self, temp_db):
        db.init_db()  # second call should not crash


class TestSaveAndRetrieve:
    def test_save_session(self, temp_db):
        mods = [
            {"id": 1, "titolo_modulo": "A", "spiegazione": "Test A", "esercizio_pratico": "Ex A"},
            {"id": 2, "titolo_modulo": "B", "spiegazione": "Test B", "esercizio_pratico": "Ex B"},
        ]
        sid = db.save_session("python", "base", mods)
        assert sid > 0

    def test_get_session_modules(self, temp_db):
        mods = [
            {"id": 1, "titolo_modulo": "A", "spiegazione": "Test A", "esercizio_pratico": "Ex A"},
        ]
        sid = db.save_session("python", "base", mods)
        rows = db.get_session_modules(sid)
        assert len(rows) == 1
        assert rows[0]["titolo"] == "A"
        assert rows[0]["module_index"] == 0

    def test_session_not_found_returns_empty(self, temp_db):
        rows = db.get_session_modules(999)
        assert rows == []

    def test_multiple_sessions(self, temp_db):
        db.save_session("topic1", "base", [{"id": 1, "titolo_modulo": "A", "spiegazione": "X", "esercizio_pratico": "Y"}])
        db.save_session("topic2", "avanzato", [{"id": 1, "titolo_modulo": "B", "spiegazione": "Z", "esercizio_pratico": "W"}])
        sessions = db.get_all_sessions()
        assert len(sessions) == 2

    def test_get_all_sessions_empty(self, temp_db):
        sessions = db.get_all_sessions()
        assert sessions == []

    def test_save_attempt(self, temp_db):
        mods = [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}]
        sid = db.save_session("python", "base", mods)
        rows = db.get_session_modules(sid)
        module_db_id = rows[0]["id"]

        fb = json.dumps({"commento": "Ben fatto!"})
        db.save_attempt(module_db_id, "mia soluzione", "corretta", fb)

        attempts = db.get_module_attempts(module_db_id)
        assert len(attempts) == 1
        assert attempts[0]["esito"] == "corretta"

    def test_multiple_attempts(self, temp_db):
        mods = [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}]
        sid = db.save_session("python", "base", mods)
        module_db_id = db.get_session_modules(sid)[0]["id"]

        db.save_attempt(module_db_id, "tentativo1", "sbagliata", "{}")
        db.save_attempt(module_db_id, "tentativo2", "corretta", "{}")

        attempts = db.get_module_attempts(module_db_id)
        assert len(attempts) == 2

    def test_get_module_attempts_empty(self, temp_db):
        mods = [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}]
        sid = db.save_session("python", "base", mods)
        module_db_id = db.get_session_modules(sid)[0]["id"]
        assert db.get_module_attempts(module_db_id) == []


class TestUpdateModuleState:
    def test_archive_module(self, temp_db):
        mods = [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}]
        sid = db.save_session("python", "base", mods)
        module_db_id = db.get_session_modules(sid)[0]["id"]

        db.update_module_state(module_db_id, archived=True)
        rows = db.get_session_modules(sid)
        assert rows[0]["archived"] == 1
        assert rows[0]["completed"] == 0

    def test_complete_module(self, temp_db):
        mods = [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}]
        sid = db.save_session("python", "base", mods)
        module_db_id = db.get_session_modules(sid)[0]["id"]

        db.update_module_state(module_db_id, completed=True)
        rows = db.get_session_modules(sid)
        assert rows[0]["completed"] == 1
        assert rows[0]["archived"] == 0


class TestSaveRiepilogo:
    def test_save_and_retrieve(self, temp_db):
        sid = db.save_session("python", "base", [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}])
        db.save_riepilogo(sid, '{"punti": []}')

        sessions = db.get_all_sessions()
        target = [s for s in sessions if s["id"] == sid]
        assert len(target) == 1
        assert target[0]["riepilogo"] == '{"punti": []}'


class TestFindSimilarModules:
    """Solo test strutturali (non chiama API reali)."""

    def test_returns_empty_when_no_data(self, temp_db):
        result = db.find_similar_modules("python", top_k=3)
        assert result == []

    def test_returns_empty_when_embedding_fails(self, temp_db, monkeypatch):
        def fake_embedding(text):
            raise RuntimeError("API error")
        monkeypatch.setattr(db, "compute_embedding", fake_embedding)

        sid = db.save_session("python", "base", [{"id": 1, "titolo_modulo": "A", "spiegazione": "Test", "esercizio_pratico": "Ex"}])
        result = db.find_similar_modules("python", top_k=3)
        assert result == []


class TestCosineSimilarity:
    def test_identical(self):
        assert db._cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0

    def test_orthogonal(self):
        assert db._cosine_similarity([1, 0], [0, 1]) == 0.0

    def test_opposite(self):
        assert db._cosine_similarity([1, 0], [-1, 0]) == -1.0

    def test_zero_vector(self):
        assert db._cosine_similarity([0, 0], [1, 0]) == 0.0
