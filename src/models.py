from pydantic import BaseModel, Field
from typing import List, Optional

class Metadati(BaseModel):
    difficolta_impostata: str
    objective_apprendimento: str

class Modulo(BaseModel):
    id: int
    titolo_modulo: str
    spiegazione: str = Field(..., max_length=1500) # Controllo flessibile per le ~150 parole
    esercizio_pratico: str

class FeedbackValutazione(BaseModel):
    commento_costruttivo: str
    suggerimento_miglioramento: str
    punti_di_forza: Optional[List[str]] = None
    punti_migliorabili: Optional[List[str]] = None
    errors_comprensione: Optional[List[str]] = None

class PercorsoStudio(BaseModel):
    metadati: Metadati
    moduli: List[Modulo]

class TutorResponse(BaseModel):
    percorso_studio: PercorsoStudio
    feedback_valutazione: FeedbackValutazione
