import os
import logging
from pathlib import Path
import json
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv
from pydantic import ValidationError

logger = logging.getLogger(__name__)
from .models import TutorResponse, FeedbackValutazione, RiepilogoFinale
from .config import (
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
    CHAT_TIMEOUT,
    CHAT_TEMPERATURE_DEFAULT,
    CHAT_TEMPERATURE_HINT,
    MAX_RETRIES,
    WAIT_SECONDS,
    ENABLE_SANITY_CHECK,
    SANITY_CHECK_TEMPERATURE,
    SANITY_CHECK_TIMEOUT,
    ENABLE_HEURISTIC_FILTER,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
SYSTEM_PROMPT_PATH = PROJECT_ROOT / 'Prompts' / 'system_mlpg.md'
if not SYSTEM_PROMPT_PATH.exists():
    SYSTEM_PROMPT_PATH = PROJECT_ROOT / 'prompts' / 'system_mlpg.md'


def _get_openrouter_api_key():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY non trovata. Assicurati che sia definita nel file .env.")
    return api_key


def _openrouter_chat_completion(messages, temperature: float = 0.2):
    api_key = _get_openrouter_api_key()
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    request_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=request_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "OpenRouterStreamlit/1.0",
        },
        method="POST",
    )

    logger.debug("Chiamata OpenRouter: model=%s, temperature=%s", OPENROUTER_MODEL, temperature)

    try:
        with urllib.request.urlopen(req, timeout=CHAT_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            logger.debug("Risposta OpenRouter ricevuta (token totali=%s)", result.get("usage", {}).get("total_tokens", "?"))
            return result
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("OpenRouter HTTP %s: %s", exc.code, exc.reason)
        raise RuntimeError(
            f"OpenRouter HTTP {exc.code}: {exc.reason}. Risposta: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Errore di rete OpenRouter: {exc.reason}") from exc


def _get_chat_response_text(messages, temperature: float = CHAT_TEMPERATURE_DEFAULT):
    response = _call_with_retries(lambda: _openrouter_chat_completion(messages, temperature))
    choices = response.get("choices")
    if not choices or not isinstance(choices, list):
        raise RuntimeError("OpenRouter response non valida: nessuna scelta trovata.")

    first_choice = choices[0]
    content = None
    if isinstance(first_choice, dict):
        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
        elif "text" in first_choice:
            content = first_choice.get("text")
    if not isinstance(content, str):
        raise RuntimeError("OpenRouter response non valida: contenuto testo mancante.")

    return content.strip()


def _call_with_retries(callable_fn, max_retries: int = MAX_RETRIES, wait_seconds: int = WAIT_SECONDS):
    """Esegue la callable che chiama l'API OpenRouter con retry su errori di rate limit.

    La callable deve essere una funzione senza argomenti che effettua la richiesta HTTP e ritorna la risposta JSON.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return callable_fn()
        except Exception as exc:
            msg = str(exc)
            is_rate = False
            logger.warning("Tentativo %d/%d fallito: %s", attempt, max_retries, msg)
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


# ─────────────────────────────────────────────────────────────
# Opzione A — Filtro euristico pre-LLM (nessun costo API)
# ─────────────────────────────────────────────────────────────

def valida_input_euristico(esercizio: str, risposta_utente: str):

    if not ENABLE_HEURISTIC_FILTER:
        return True, ""

    risposta = risposta_utente.strip()

    if not risposta or len(risposta) < 3:
        return False, "La risposta è troppo corta. Prova a scrivere una soluzione più articolata."

    risposta_lower = risposta.lower().strip("?.! ")

    nonsense_patterns = [
        "non lo so", "non saprei", "boh", "niente", "non capisco",
        "idk", "non ne ho idea", "non so", "???", "...", "....",
        "non ho capito", "mi arrendo", "ni", "meh", "forse",
    ]
    for pattern in nonsense_patterns:
        if risposta_lower == pattern:
            return False, (
                "Sembra che tu non abbia provato a rispondere. "
                "Usa il pulsante 'Chiedi chiarimenti' se hai bisogno di aiuto."
            )

    words = risposta.split()
    if len(words) >= 4:
        for i in range(len(words) - 3):
            if words[i].lower() == words[i+1].lower() == words[i+2].lower() == words[i+3].lower():
                return False, (
                    "La risposta contiene parole ripetute. "
                    "Prova a formulare una soluzione più strutturata."
                )

    alpha_chars = [c.lower() for c in risposta if c.isalpha()]
    if len(alpha_chars) > 8:
        unique_ratio = len(set(alpha_chars)) / len(alpha_chars)
        if unique_ratio < 0.3:
            return False, (
                "La risposta sembra composta da caratteri casuali. "
                "Riprova con parole di senso compiuto."
            )

    if len(words) <= 2 and len(risposta) < 15:
        return False, "La risposta è troppo breve per essere valutata. Prova a elaborare di più."

    exercise_keywords = set(
        w.lower().strip(".,;:!?()[]{}\"'")
        for w in esercizio.split()
        if len(w) > 3 and w.isalpha()
    )
    response_words_set = set(
        w.lower().strip(".,;:!?()[]{}\"'")
        for w in words
        if len(w) > 3 and w.isalpha()
    )
    if exercise_keywords and response_words_set:
        overlap = exercise_keywords & response_words_set
        if len(overlap) == 0:
            return False, (
                "La risposta non sembra pertinente all'esercizio. "
                "Prova a leggere meglio la domanda e rispondere in modo mirato."
            )

    return True, ""


# ─────────────────────────────────────────────────────────────
# Opzione C — Sanity check LLM (doppio passaggio)
# ─────────────────────────────────────────────────────────────

def sanity_check_risposta(esercizio: str, risposta_utente: str):

    if not ENABLE_SANITY_CHECK:
        return True, ""

    prompt = f"""Verifica se la seguente risposta è pertinente all'esercizio.

ESERCIZIO: {esercizio}

RISPOSTA UTENTE: {risposta_utente}

Rispondi SOLO con un JSON:
{{
  "pertinente": true/false,
  "motivo": "breve spiegazione se non pertinente, altrimenti stringa vuota"
}}

Considera NON pertinente se:
- La risposta è completamente fuori tema o parla di tutt'altro
- È composta da caratteri casuali o stringhe senza senso
- È un tentativo di bypassare l'esercizio (es. barzellette, testi copia-incolla non attinenti)
- Non dimostra alcuno sforzo di affrontare la domanda
"""

    messages = [
        {"role": "system", "content": "Sei un validatore di pertinenza. Rispondi solo in JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        response_text = _get_chat_response_text(messages, temperature=SANITY_CHECK_TEMPERATURE)
        result = json.loads(_normalize_json_text(response_text))
        is_pertinent = result.get('pertinente', True)
        motivo = result.get('motivo', '')
        return is_pertinent, motivo
    except Exception:
        return True, ""


def generate_microlearning_path(topic: str, level: str, context_modules: list | None = None) -> TutorResponse:
    user_prompt = (
        f"Argomento: {topic}\n"
        f"Livello: {level}\n"
        "Rispondi esclusivamente con un JSON valido che corrisponda esattamente alla struttura richiesta dal system prompt. "
        "Non aggiungere testo libero o commenti."
    )

    if context_modules:
        contesto = "\n\nModuli già creati su argomenti simili (NON ripetere gli stessi contenuti; copri aspetti DIVERSI):\n"
        for i, cm in enumerate(context_modules[:3], 1):
            contesto += f"{i}. [{cm['topic']}] {cm['titolo']}: {cm['spiegazione'][:200]}\n"
        user_prompt += contesto
    
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding='utf-8')
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response_text = _get_chat_response_text(messages)

    try:
        return TutorResponse.model_validate_json(_normalize_json_text(response_text))
    except (ValidationError, ValueError) as exc:
        raise RuntimeError(
            "Risposta non valida: il JSON generato non corrisponde al formato TutorResponse. "
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

    evaluation_prompt = f"""Sei un valutatore esperto di microlearning. Valuta la seguente risposta dell'utente.

ESERCIZIO: {esercizio}

RISPOSTA DELL'UTENTE: {risposta_utente}

Devi restituire ESCLUSIVAMENTE un JSON valido con questi campi:
{{
  "commento_costruttivo": "Commento caloroso, motivante e personale. Usa un tono entusiasta, fai sentire l'utente capace e riconosci lo sforzo. 2-3 frasi.",
  "punti_di_forza": ["Max 3 punti analitici estratti dalla risposta; non copiare il commento_costruttivo."],
  "punti_migliorabili": ["Elementi da correggere o approfondire, con breve motivo."],
  "suggerimento_miglioramento": "Suggerimento pratico, specifico e orientato al futuro. Un consiglio concreto su cosa fare dopo per migliorare. 1-2 frasi.",
  "esito": "corretta | parziale | sbagliata"
}}

REGOLE:
- `commento_costruttivo` e `suggerimento_miglioramento` devono essere DIVERSI tra loro per stile e contenuto: il primo elogia e motiva, il secondo indica un passo successivo concreto.
- Se la risposta dell'utente è sostanzialmente corretta, imposta `esito` a "corretta" e fornisci almeno 2 voci in `punti_di_forza` e 1-2 in `punti_migliorabili`.
- Se la risposta è parzialmente corretta o manca di dettagli, imposta `esito` a "parziale".
- Se la risposta è "non lo so", completamente sbagliata o molto imprecisa, imposta `esito` a "sbagliata", lascia `punti_di_forza` vuoto e concentra il feedback su `punti_migliorabili`.
- Se la risposta è totalmente fuori tema, senza senso, composta da caratteri casuali (keyboard smashing), barzellette, testi copia-incolla non attinenti o non dimostra alcuno sforzo di affrontare l'esercizio: imposta `esito` a "sbagliata", lascia `punti_di_forza` vuoto, e usa `commento_costruttivo` per spiegare gentilmente che la risposta non è pertinente, invitando l'utente a rileggere l'esercizio e riprovare con un approccio più focalizzato. Il `suggerimento_miglioramento` deve indicare un'azione concreta per rimettersi in carreggiata.
- Se la risposta non ha alcuna attinenza con l'esercizio, non cercare punti di forza forzatamente: `punti_di_forza` deve essere una lista vuota.
- `punti_di_forza` deve essere analitico, sintetico e non ripetere il `commento_costruttivo`.
- Non aggiungere il `commento_costruttivo` all'interno di `punti_di_forza`.
- Rispondi SOLO con il JSON richiesto.
"""
    
    messages = [
        {"role": "system", "content": "Sei un valutatore esperto di microlearning."},
        {"role": "user", "content": evaluation_prompt},
    ]
    response_text = _get_chat_response_text(messages)
    
    try:
        result = json.loads(_normalize_json_text(response_text))
        feedback = FeedbackValutazione(
            commento_costruttivo=result.get('commento_costruttivo', ''),
            suggerimento_miglioramento=result.get('suggerimento_miglioramento', ''),
            punti_di_forza=result.get('punti_di_forza', []) if isinstance(result.get('punti_di_forza', []), list) else [],
            punti_migliorabili=result.get('punti_migliorabili', []) if isinstance(result.get('punti_migliorabili', []), list) else [],
            esito=result.get('esito', '')
        )
        return feedback
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise RuntimeError(
            f"Errore nella valutazione: impossibile processare la risposta JSON. "
            f"Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_hint(esercizio: str, risposta_utente: str, livello: str, tentativo: int = 1) -> str:
    """
    Genera un hint per aiutare l'utente a correggere la propria risposta.

    Args:
        esercizio: Testo dell'esercizio
        risposta_utente: Risposta errata fornita dall'utente
        livello: Livello di difficoltà
        tentativo: Numero del tentativo (1 = primo errore)

    Returns:
        Testo dell'hint
    """
    hint_prompt = f"""L'utente ha sbagliato questo esercizio (livello {livello}, tentativo {tentativo}).

ESERCIZIO: {esercizio}

RISPOSTA DELL'UTENTE: {risposta_utente}

Genera un hint breve (max 60 parole) in italiano che:
- Non dia la risposta direttamente
- Faccia riflettere l'utente su cosa ha sbagliato
- Suggerisca una direzione o un concetto chiave da rivedere
- Abbia un tono incoraggiante

Rispondi SOLO con il testo dell'hint, senza formattazione JSON.
"""

    messages = [
        {"role": "system", "content": "Sei un tutor che guida l'utente a scoprire la risposta da solo."},
        {"role": "user", "content": hint_prompt},
    ]

    fallback_hints = {
        1: "Riprova! Rileggi attentamente la spiegazione del modulo e concentrati sui concetti chiave. Se serve, chiedi un chiarimento qui sotto.",
        2: "Non preoccuparti, succede! Prova a scomporre il problema in passaggi più piccoli. Usa la sezione 'Chiedi chiarimenti mirati' se un concetto non ti è chiaro.",
    }

    try:
        hint = _get_chat_response_text(messages, temperature=CHAT_TEMPERATURE_HINT)
        if hint and len(hint) > 5:
            return hint
    except Exception:
        pass

    return fallback_hints.get(tentativo, fallback_hints[1])


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

    messages = [
        {"role": "system", "content": "Sei un assistente che genera riepiloghi finali in italiano."},
        {"role": "user", "content": summary_prompt},
    ]
    response_text = _get_chat_response_text(messages)

    try:
        return RiepilogoFinale.model_validate_json(_normalize_json_text(response_text))
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
    
    messages = [
        {"role": "system", "content": "Sei un tutor che spiega concetti in modo semplice e chiaro."},
        {"role": "user", "content": alt_prompt},
    ]
    response_text = _get_chat_response_text(messages)

    try:
        result = json.loads(_normalize_json_text(response_text))
        return {
            'spiegazione_semplificata': result.get('spiegazione_semplificata', '').strip(),
            'esempio_pratico': result.get('esempio_pratico', '').strip(),
            'passaggi': result.get('passaggi', []) if isinstance(result.get('passaggi', []), list) else []
        }
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Errore nella generazione della spiegazione semplificata: risposta non valida. \nContenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_saluto_finale(nome_utente: str, livello: str, interruzione_per_dubbio: bool) -> str:
    if interruzione_per_dubbio:
        prompt = f"Hai appena aiutato {nome_utente}, livello {livello}, che ha bisogno di una chiusura rassicurante. "
        prompt += (
            "Genera un breve saluto finale in italiano che spieghi che è normale avere dubbi durante l'apprendimento "
            "e che riprenderete insieme i concetti quando tornerete a studiare. "
            "Sii caloroso, umano e motivante."
        )
    else:
        prompt = f"Hai appena concluso una sessione con {nome_utente}, livello {livello}. "
        prompt += (
            "Genera un breve saluto finale in italiano che lodi il progresso fatto oggi, sottolinei l'impegno e motivi a tornare. "
            "Sii positivo, personale e incoraggiante."
        )

    messages = [
        {"role": "system", "content": "Sei un tutor empatico e incoraggiante. Genera un messaggio di chiusura in italiano senza formato JSON."},
        {"role": "user", "content": prompt},
    ]
    return _get_chat_response_text(messages)


