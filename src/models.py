from pydantic import BaseModel, Field
from typing import List, Optional

class Metadati(BaseModel):
    difficolta_impostata: str
    objective_apprendimento: str

class Modulo(BaseModel):
    id: int
    titolo_modulo: str
    spiegazione: str = Field(..., max_length=2500)
    esercizio_pratico: str

    model_config = {
        "extra": "forbid"
    }

class FeedbackValutazione(BaseModel):
    commento_costruttivo: str
    suggerimento_miglioramento: str
    punti_di_forza: Optional[List[str]] = None
    punti_migliorabili: Optional[List[str]] = None
    errors_comprensione: Optional[List[str]] = None
    esito: Optional[str] = None  # "corretta", "parziale", "sbagliata"

class RiepilogoFinale(BaseModel):
    punti_di_forza: List[str]
    punti_da_migliorare: List[str]
    diario_di_bordo: str
    saluto_conclusivo: str

    model_config = {
        "extra": "forbid"
    }

class PercorsoStudio(BaseModel):
    metadati: Metadati
    moduli: List[Modulo]

    model_config = {
        "extra": "forbid"
    }

class TutorResponse(BaseModel):
    percorso_studio: PercorsoStudio

    model_config = {
        "extra": "forbid"
    }
