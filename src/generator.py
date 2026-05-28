import os
from pathlib import Path
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError
from .models import TutorResponse, FeedbackValutazione, RiepilogoFinale

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
SYSTEM_PROMPT_PATH = PROJECT_ROOT / 'Prompts' / 'system_mlpg.md'
if not SYSTEM_PROMPT_PATH.exists():
    SYSTEM_PROMPT_PATH = PROJECT_ROOT / 'prompts' / 'system_mlpg.md'


def _get_configured_model():
    """Configura e ritorna un modello Gemini configurato."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY non trovata. Assicurati che sia definita nel file .env.")
    genai.configure(api_key=api_key)
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding='utf-8')
    return genai.GenerativeModel(
        'models/gemini-2.5-flash',
        system_instruction=system_prompt,
    )


def _call_with_retries(callable_fn, max_retries: int = 3, wait_seconds: int = 30):
    """Esegue la callable che chiama l'API Gemini con retry su errori di rate limit (429/ResourceExhausted).

    La callable deve essere una funzione senza argomenti che esegue la chiamata a `model.generate_content(...)`
    e ritorna l'oggetto risposta.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return callable_fn()
        except Exception as exc:
            msg = str(exc)
            is_rate = False
            # riconosci possibili indicatori di quota esaurita
            if '429' in msg or 'ResourceExhausted' in msg or 'rate limit' in msg.lower() or 'quota' in msg.lower():
                is_rate = True

            if is_rate and attempt < max_retries:
                time.sleep(wait_seconds)
                continue
            # non è un errore di rate limit o abbiamo esaurito i retry
            raise

def _normalize_json_text(response_text: str) -> str:
    """Pulizia base del testo restituito dal modello per renderlo JSON parsabile."""
    text = response_text.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}")
        if end > start:
            text = text[start:end + 1]

    normalized_chars = []
    in_string = False
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' and not escaped:
            in_string = not in_string
            normalized_chars.append(ch)
        elif ch == '\\' and not escaped:
            normalized_chars.append(ch)
            escaped = True
        elif in_string and ch in ['\n', '\r']:
            normalized_chars.append('\\n')
            if ch == '\r' and i + 1 < len(text) and text[i + 1] == '\n':
                i += 1
        else:
            normalized_chars.append(ch)
            escaped = False
        i += 1

    return ''.join(normalized_chars)


def generate_microlearning_path(topic: str, level: str) -> TutorResponse:
    model = _get_configured_model()
    
    user_prompt = (
        f"Argomento: {topic}\n"
        f"Livello: {level}\n"
        "Rispondi esclusivamente con un JSON valido che corrisponda esattamente alla struttura richiesta dal system prompt. "
        "Non aggiungere testo libero o commenti."
    )
    
    response = _call_with_retries(lambda: model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"}
    ))

    response_text = _normalize_json_text(response.text)

    try:
        return TutorResponse.model_validate_json(response_text)
    except (ValidationError, ValueError) as exc:
        raise RuntimeError(
            "Risposta Gemini non valida: il JSON generato non corrisponde al formato TutorResponse. "
            f"Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def valuta_risposta(esercizio: str, risposta_utente: str) -> FeedbackValutazione:
    """
    Valuta la risposta dell'utente a un esercizio, agendo come Valutatore.
    
    Args:
        esercizio: Testo dell'esercizio
        risposta_utente: Risposta fornita dall'utente
    
    Returns:
        FeedbackValutazione con commento_costruttivo e suggerimento_miglioramento
    """
    model = _get_configured_model()

    evaluation_prompt = f"""Sei un valutatore esperto di microlearning. Valuta la seguente risposta dell'utente.

ESERCIZIO: {esercizio}

RISPOSTA DELL'UTENTE: {risposta_utente}

Devi restituire ESCLUSIVAMENTE un JSON valido con questi campi:
{{
  "commento_costruttivo": "Commento motivante e incoraggiante.",
  "punti_di_forza": ["Max 3 punti analitici estratti dalla risposta; non copiare il commento_costruttivo."],
  "punti_migliorabili": ["Elementi da correggere o approfondire, con breve motivo."],
  "suggerimento_miglioramento": "Suggerimento pratico e specifico."
}}

REGOLE:
- Se la risposta dell'utente è sostanzialmente corretta, fornisci almeno 2 voci in `punti_di_forza` e almeno 2 voci in `punti_migliorabili`.
- `punti_di_forza` deve essere analitico, sintetico e non ripetere il `commento_costruttivo`.
- Se la risposta è "non lo so", completamente sbagliata o molto imprecisa, lascia `punti_di_forza` vuoto e concentra il feedback su `punti_migliorabili`.
- Non aggiungere il `commento_costruttivo` all'interno di `punti_di_forza`.
- Rispondi SOLO con il JSON richiesto.
"""
    
    response = _call_with_retries(lambda: model.generate_content(
        evaluation_prompt,
        generation_config={"response_mime_type": "application/json"}
    ))
    
    try:
        response_text = _normalize_json_text(response.text)
        result = json.loads(response_text)
        feedback = FeedbackValutazione(
            commento_costruttivo=result.get('commento_costruttivo', ''),
            suggerimento_miglioramento=result.get('suggerimento_miglioramento', ''),
            punti_di_forza=result.get('punti_di_forza', []) if isinstance(result.get('punti_di_forza', []), list) else [],
            punti_migliorabili=result.get('punti_migliorabili', []) if isinstance(result.get('punti_migliorabili', []), list) else []
        )
        return feedback
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise RuntimeError(
            f"Errore nella valutazione: impossibile processare la risposta JSON. "
            f"Contenuto ricevuto: {response.text[:500]}"
        ) from exc


def genera_riepilogo_finale(storico_risposte: list[dict], diario_note: list[str], livello: str) -> RiepilogoFinale:
    """
    Genera un riepilogo finale cumulativo basato sulla cronologia delle risposte dell'utente.

    Args:
        storico_risposte: lista di dizionari con campi `esercizio` e `soluzione`
        diario_note: note o dubbi raccolti durante il percorso
        livello: livello dell'utente (base, intermedio, avanzato)

    Returns:
        RiepilogoFinale con punti di forza, punti da migliorare, diario di bordo e saluto conclusivo.
    """
    model = _get_configured_model()

    if not storico_risposte:
        raise ValueError("Lo storico delle risposte è vuoto. Impossibile generare il riepilogo finale.")

    storico_testo = []
    for idx, item in enumerate(storico_risposte, start=1):
        esercizio = item.get('esercizio', '').strip()
        soluzione = item.get('soluzione', '').strip()
        storico_testo.append(
            f"{idx}. Esercizio: {esercizio}\n   Risposta utente: {soluzione}"
        )
    storico_section = "\n".join(storico_testo)
    diario_section = "\n".join([f"- {nota.strip()}" for nota in diario_note if nota.strip()]) if diario_note else "- Nessuna nota aggiuntiva."

    summary_prompt = f"""Genera un riepilogo finale cumulativo in italiano per un percorso di microlearning.

Hai a disposizione la cronologia delle risposte dell'utente e le note di bordo raccolte durante il percorso.

LIVELLO UTENTE: {livello}

CRONISTORIA DELLE RISPOSTE:
{storico_section}

DIARIO DI BORDO:
{diario_section}

Devi rispondere ESCLUSIVAMENTE con un JSON valido nel formato:
{{
  "punti_di_forza": ["string"],
  "punti_da_migliorare": ["string"],
  "diario_di_bordo": "string",
  "saluto_conclusivo": "string"
}}

REGOLE:
- Il riepilogo deve essere basato sulle risposte reali fornite dall'utente.
- Non includere un commento costruttivo generico.
- Fornisci almeno un punto concreto in `punti_di_forza` e almeno un punto concreto in `punti_da_migliorare`.
- `diario_di_bordo` deve contenere una sintesi delle osservazioni del percorso, non la ripetizione parola-per-parola dei dati.
- `saluto_conclusivo` deve essere una chiusura motivante, breve, e orientata al proseguimento dell'apprendimento.
- Rispondi SOLO con il JSON richiesto, senza testo aggiuntivo.
"""

    response = _call_with_retries(lambda: model.generate_content(
        summary_prompt,
        generation_config={"response_mime_type": "application/json"}
    ))
    response_text = _normalize_json_text(response.text)

    try:
        return RiepilogoFinale.model_validate_json(response_text)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Errore nella generazione del riepilogo finale: risposta JSON non valida. "
            f"Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_spiegazione_alternativa(argomento: str, spiegazione_originale: str, dubbio_utente: str, livello: str) -> dict:
    """
    Genera una spiegazione alternativa quando l'utente non capisce.
    
    Args:
        argomento: Argomento che l'utente non ha capito
        spiegazione_originale: La spiegazione che il tutor aveva fornito
        dubbio_utente: Il dubbio specifico espresso dall'utente
        livello: Livello di difficoltà dell'utente (base/intermedio/avanzato)
    
    Returns:
        dict con spiegazione semplificata, esempio pratico e passaggi consigliati
    """
    model = _get_configured_model()
    
    alt_prompt = f"""L'utente non ha capito questo argomento a livello {livello}.

ARGOMENTO: {argomento}

SPIEGAZIONE ORIGINALE: {spiegazione_originale}

DUBBIO DELL'UTENTE: {dubbio_utente}

Devi rispondere ESCLUSIVAMENTE con un oggetto JSON valido nel formato:
{{
  "spiegazione_semplificata": "Testo della spiegazione semplificata",
  "esempio_pratico": "Un breve esempio concreto che illustra il concetto",
  "passaggi": ["Primo passaggio chiaro", "Secondo passaggio", "Terzo passaggio"]
}}

La spiegazione deve essere:
- più chiara e diretta rispetto all'originale
- indicata per un utente di livello {livello}
- collegata ai concetti fondamentali se sei intermedio
- se sei avanzato, includi un motivo pratico e un mini-caso d'uso
- con un esempio concreto e passaggi pratici
- orientata a risolvere il dubbio specifico dell'utente
- non più lunga di 130 parole per la spiegazione
"""
    
    response = _call_with_retries(lambda: model.generate_content(
        alt_prompt,
        generation_config={"response_mime_type": "application/json"}
    ))
    
    response_text = _normalize_json_text(response.text)

    try:
        result = json.loads(response_text)
        return {
            'spiegazione_semplificata': result.get('spiegazione_semplificata', '').strip(),
            'esempio_pratico': result.get('esempio_pratico', '').strip(),
            'passaggi': result.get('passaggi', []) if isinstance(result.get('passaggi', []), list) else []
        }
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Errore nella generazione della spiegazione semplificata: risposta non valida. \nContenuto ricevuto: {response.text[:500]}"
        ) from exc


def _get_saluto_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY non trovata. Assicurati che sia definita nel file .env.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        'models/gemini-2.5-flash',
        system_instruction=(
            "Sei un tutor empatico e incoraggiante. "
            "Genera un breve saluto finale personalizzato in italiano. "
            "Usa un tono rassicurante, motivante e umano. "
            "Non rispondere in formato JSON."
        ),
    )


def genera_saluto_finale(nome_utente: str, livello: str, interruzione_per_dubbio: bool) -> str:
    model = _get_saluto_model()
    if interruzione_per_dubbio:
        prompt = f"""Hai appena aiutato {nome_utente}, livello {livello}, che ha bisogno di una chiusura rassicurante. """
        prompt += (
            "Genera un breve saluto finale in italiano che spieghi che è normale avere dubbi durante l'apprendimento "
            "e che riprenderete insieme i concetti quando tornerete a studiare. "
            "Sii caloroso, umano e motivante."
        )
    else:
        prompt = f"""Hai appena concluso una sessione con {nome_utente}, livello {livello}. """
        prompt += (
            "Genera un breve saluto finale in italiano che lodi il progresso fatto oggi, sottolinei l'impegno e motivi a tornare. "
            "Sii positivo, personale e incoraggiante."
        )

    response = _call_with_retries(lambda: model.generate_content(
        prompt,
        generation_config={"response_mime_type": "text/plain"}
    ))

    return response.text.strip()


