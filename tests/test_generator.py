"""Test per src/generator.py (unità che non richiedono API key)."""

import json
import pytest
from pydantic import ValidationError
from src.generator import _normalize_json_text
from src.models import FeedbackValutazione, RiepilogoFinale, TutorResponse, Modulo, Metadati, PercorsoStudio


class TestNormalizeJsonText:
    def test_clean_json(self):
        raw = '{"esito": "corretta"}'
        assert _normalize_json_text(raw) == raw

    def test_with_code_fence(self):
        raw = 'ecco il json:\n```json\n{"esito": "sbagliata"}\n```\n'
        assert _normalize_json_text(raw) == '{"esito": "sbagliata"}'

    def test_with_generic_fence(self):
        raw = '```\n{"esito": "parziale"}\n```\n'
        assert _normalize_json_text(raw) == '{"esito": "parziale"}'

    def test_surrounding_text(self):
        raw = 'ecco la risposta: {"esito": "corretta"} spero sia giusto'
        assert _normalize_json_text(raw) == '{"esito": "corretta"}'

    def test_multiple_json_blocks(self):
        raw = '{"a": 1} e poi {"b": 2}'
        result = _normalize_json_text(raw)
        assert result == raw

    def test_newlines_in_string(self):
        raw = '{"test": "linea uno\nlinea due"}'
        result = _normalize_json_text(raw)
        assert '\\n' in result
        parsed = json.loads(result)
        assert parsed["test"] == "linea uno\nlinea due"

    def test_carriage_return_newline(self):
        raw = '{"test": "linea uno\r\nlinea due"}'
        result = _normalize_json_text(raw)
        assert '\\n' in result
        assert '\\r' not in result
        parsed = json.loads(result)
        assert parsed["test"] == "linea uno\nlinea due"

    def test_escaped_characters_preserved(self):
        raw = '{"test": "linea1\\"continuo"}'
        assert _normalize_json_text(raw) == raw

    def test_empty_string(self):
        assert _normalize_json_text("") == ""

    def test_only_braces(self):
        assert _normalize_json_text("{}") == "{}"

    def test_json_with_extra_whitespace(self):
        raw = '  \n  {"esito": "corretta"}  \n  '
        assert _normalize_json_text(raw) == '{"esito": "corretta"}'


class TestFeedbackValutazione:
    def test_minimal_valid(self):
        fb = FeedbackValutazione(
            commento_costruttivo="Ben fatto!",
            suggerimento_miglioramento="Prova a fare X.",
        )
        assert fb.commento_costruttivo == "Ben fatto!"
        assert fb.esito is None

    def test_with_all_fields(self):
        fb = FeedbackValutazione(
            commento_costruttivo="Ottimo lavoro!",
            suggerimento_miglioramento="Puoi migliorare su Y.",
            punti_di_forza=["Chiarezza", "Precisione"],
            punti_migliorabili=["Velocità"],
            errors_comprensione=["Concetto base non chiaro"],
            esito="corretta",
        )
        assert fb.esito == "corretta"
        assert len(fb.punti_di_forza) == 2

    def test_partial_esito(self):
        fb = FeedbackValutazione(
            commento_costruttivo="Quasi giusto!",
            suggerimento_miglioramento="Controlla dettaglio Z.",
            esito="parziale",
        )
        assert fb.esito == "parziale"

    def test_sbagliata_esito(self):
        fb = FeedbackValutazione(
            commento_costruttivo="Non proprio.",
            suggerimento_miglioramento="Riprova con un altro approccio.",
            esito="sbagliata",
        )
        assert fb.esito == "sbagliata"


class TestRiepilogoFinale:
    def test_minimal_valid(self):
        r = RiepilogoFinale(
            punti_di_forza=["Chiarezza"],
            punti_da_migliorare=["Velocità"],
            diario_di_bordo="Buon progresso.",
            saluto_conclusivo="Continua così!",
        )
        assert r.saluto_conclusivo == "Continua così!"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            RiepilogoFinale(
                punti_di_forza=["A"],
                punti_da_migliorare=["B"],
                diario_di_bordo="C",
                saluto_conclusivo="D",
                extra_campo="non permesso",
            )

    def test_empty_lists_allowed(self):
        r = RiepilogoFinale(
            punti_di_forza=[],
            punti_da_migliorare=[],
            diario_di_bordo="Nessuna nota.",
            saluto_conclusivo="Ciao!",
        )
        assert r.punti_di_forza == []


class TestTutorResponse:
    def test_valid_full_response(self):
        data = {
            "percorso_studio": {
                "metadati": {
                    "difficolta_impostata": "base",
                    "objective_apprendimento": "Imparare Python",
                },
                "moduli": [
                    {
                        "id": 1,
                        "titolo_modulo": "Variabili",
                        "spiegazione": "Una variabile è...",
                        "esercizio_pratico": "Dichiara una variabile",
                    },
                    {
                        "id": 2,
                        "titolo_modulo": "Cicli",
                        "spiegazione": "I cicli servono a...",
                        "esercizio_pratico": "Scrivi un ciclo for",
                    },
                ],
            }
        }
        resp = TutorResponse(**data)
        assert len(resp.percorso_studio.moduli) == 2
        assert resp.percorso_studio.moduli[0].titolo_modulo == "Variabili"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            TutorResponse(
                percorso_studio={
                    "metadati": {
                        "difficolta_impostata": "base",
                        "objective_apprendimento": "X",
                    },
                    "moduli": [
                        {
                            "id": 1,
                            "titolo_modulo": "A",
                            "spiegazione": "B",
                            "esercizio_pratico": "C",
                        }
                    ],
                    "extra": "non permesso",
                }
            )

    def test_empty_moduli(self):
        data = {
            "percorso_studio": {
                "metadati": {
                    "difficolta_impostata": "base",
                    "objective_apprendimento": "X",
                },
                "moduli": [],
            }
        }
        resp = TutorResponse(**data)
        assert len(resp.percorso_studio.moduli) == 0

    def test_spiegazione_too_long(self):
        with pytest.raises(ValidationError):
            Modulo(
                id=1,
                titolo_modulo="Test",
                spiegazione="x" * 2600,
                esercizio_pratico="Prova",
            )


class TestModulo:
    def test_valid(self):
        m = Modulo(id=1, titolo_modulo="Intro", spiegazione="Contenuto.", esercizio_pratico="Fai X.")
        assert m.titolo_modulo == "Intro"

    def test_id_must_be_int(self):
        with pytest.raises(ValidationError):
            Modulo(id="uno", titolo_modulo="A", spiegazione="B", esercizio_pratico="C")
