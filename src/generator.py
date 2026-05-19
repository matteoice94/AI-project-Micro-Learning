import os
from pathlib import Path
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError
from .models import TutorResponse, FeedbackValutazione

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
PROMPT_PATH = PROJECT_ROOT / 'prompts' / 'system_mlpg.md'

def _get_configured_model():
    """Configura e ritorna un modello Gemini configurato."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY non trovata. Assicurati che sia definita nel file .env.")
    genai.configure(api_key=api_key)
    system_prompt = PROMPT_PATH.read_text(encoding='utf-8')
    return genai.GenerativeModel(
        'models/gemini-2.5-flash',
        system_instruction=system_prompt,
    )

def generate_microlearning_path(topic: str, level: str) -> TutorResponse:
    model = _get_configured_model()
    
    # Concatenazione dell'argomento e del livello al prompt utente
    user_prompt = f"Argomento: {topic}\nLivello: {level}"
    
    response = model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    try:
        return TutorResponse.model_validate_json(response.text)
    except ValidationError as exc:
        raise RuntimeError(
            "Risposta Gemini non valida: il JSON generato non corrisponde al formato TutorResponse. "
            f"Contenuto ricevuto: {response.text[:500]}"
        ) from exc
    except ValueError as exc:
        raise RuntimeError(
            "Risposta Gemini non valida: impossibile interpretare il JSON restituito. "
            f"Contenuto ricevuto: {response.text[:500]}"
        ) from exc


def evaluate_solution(topic: str, module_explanation: str, exercise: str, user_solution: str) -> FeedbackValutazione:
    """
    Valuta la soluzione dell'utente per un esercizio, agendo come Valutatore esperto.
    
    Args:
        topic: Argomento di studio
        module_explanation: Spiegazione del modulo (per contesto)
        exercise: Testo dell'esercizio
        user_solution: Soluzione proposta dall'utente
    
    Returns:
        FeedbackValutazione con commento_costruttivo e suggerimento_miglioramento
    """
    model = _get_configured_model()
    
    evaluation_prompt = f"""
In qualità di Valutatore esperto, analizza questa risposta a un esercizio di microlearning e fornisci un feedback costruttivo e motivante.

ARGOMENTO: {topic}

SPIEGAZIONE DEL MODULO:
{module_explanation}

ESERCIZIO:
{exercise}

SOLUZIONE DELL'UTENTE:
{user_solution}

Fornisci una valutazione motivante e incoraggiante in formato JSON con i seguenti campi:
- commento_costruttivo: Un commento sulla correttezza e qualità della risposta. Sii sempre incoraggiante, riconosci i punti corretti anche se la risposta non è perfetta. Non generare frustrazione.
- suggerimento_miglioramento: Un suggerimento specifico e costruttivo per migliorare la risposta o approfondire il concetto. Se la risposta è corretta, suggerisci un'estensione o un approfondimento.

Ricorda: il tono deve essere motivante, supportivo e mai critico o frustrante.
"""
    
    response = model.generate_content(
        evaluation_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        result = json.loads(response.text)
        # Valida con FeedbackValutazione
        feedback = FeedbackValutazione(
            commento_costruttivo=result.get('commento_costruttivo', ''),
            suggerimento_miglioramento=result.get('suggerimento_miglioramento', '')
        )
        return feedback
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise RuntimeError(
            f"Errore nella valutazione: impossibile processare la risposta. "
            f"Contenuto: {response.text[:300]}"
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

Devi restituire ESCLUSIVAMENTE un JSON valido con questa struttura esatta:
{{
  "commento_costruttivo": "Scrivi un commento motivante e incoraggiante sulla risposta. Riconosci i punti corretti anche se la risposta non è perfetta. Sii sempre supportivo e mai frustrante.",
  "suggerimento_miglioramento": "Fornisci un suggerimento specifico e costruttivo per migliorare la risposta o approfondire il concetto."
}}

IMPORTANTE: Rispondi SOLO con il JSON, niente altro."""
    
    response = model.generate_content(
        evaluation_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        # Pulisci la risposta
        response_text = response.text.strip()
        # Se contiene markdown code blocks, estrai il JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        # Valida con FeedbackValutazione
        feedback = FeedbackValutazione(
            commento_costruttivo=result.get('commento_costruttivo', ''),
            suggerimento_miglioramento=result.get('suggerimento_miglioramento', '')
        )
        return feedback
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise RuntimeError(
            f"Errore nella valutazione: impossibile processare la risposta JSON. "
            f"Contenuto ricevuto: {response.text[:500]}"
        ) from exc


def genera_spiegazione_alternativa(argomento: str, spiegazione_originale: str, difficolta_utente: str, livello: str) -> dict:
    """
    Genera una spiegazione alternativa quando l'utente non capisce.
    
    Args:
        argomento: Argomento che l'utente non ha capito
        spiegazione_originale: La spiegazione che il tutor aveva fornito
        difficolta_utente: Descrizione della difficoltà dell'utente
        livello: Livello di difficoltà dell'utente (base/intermedio/avanzato)
    
    Returns:
        dict con spiegazione semplificata, esempio pratico e passaggi consigliati
    """
    model = _get_configured_model()
    
    alt_prompt = f"""L'utente non ha capito questo argomento a livello {livello}.

ARGOMENTO: {argomento}

SPIEGAZIONE ORIGINALE: {spiegazione_originale}

DIFFICOLTA' DELL'UTENTE: {difficolta_utente}

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
    
    response = model.generate_content(
        alt_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    response_text = response.text.strip()
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

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

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "text/plain"}
    )

    return response.text.strip()
