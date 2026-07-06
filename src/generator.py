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
    TRANSLATION_MODEL,
    TRANSLATION_TEMPERATURE,
    TRANSLATION_TIMEOUT,
)
from .i18n import tr, get_system_prompt_path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')


def _get_openrouter_api_key():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(tr("gen_api_key_not_found"))
    return api_key


def _openrouter_chat_completion(messages, temperature: float = 0.2, model: str | None = None, timeout: int = CHAT_TIMEOUT):
    api_key = _get_openrouter_api_key()
    payload = {
        "model": model or OPENROUTER_MODEL,
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

    logger.debug("Chiamata OpenRouter: model=%s, temperature=%s", model or OPENROUTER_MODEL, temperature)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
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
        raise RuntimeError(f"{tr('gen_network_error')}: {exc.reason}") from exc


def _get_chat_response_text(messages, temperature: float = CHAT_TEMPERATURE_DEFAULT, model: str | None = None, timeout: int = CHAT_TIMEOUT):
    response = _call_with_retries(lambda: _openrouter_chat_completion(messages, temperature, model, timeout))
    choices = response.get("choices")
    if not choices or not isinstance(choices, list):
        raise RuntimeError(tr("gen_no_choices"))

    first_choice = choices[0]
    content = None
    if isinstance(first_choice, dict):
        message = first_choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
        elif "text" in first_choice:
            content = first_choice.get("text")
    if not isinstance(content, str):
        raise RuntimeError(tr("gen_no_content"))

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
            if '429' in msg or 'ResourceExhausted' in msg or 'rate limit' in msg.lower() or 'quota' in msg.lower():
                is_rate = True

            if is_rate and attempt < max_retries:
                time.sleep(wait_seconds)
                continue
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

def valida_input_euristico(esercizio: str, risposta_utente: str, lang: str = "it"):

    if not ENABLE_HEURISTIC_FILTER:
        return True, ""

    risposta = risposta_utente.strip()

    if not risposta or len(risposta) < 3:
        return False, tr("heuristic_too_short", lang)

    risposta_lower = risposta.lower().strip("?.! ")

    encouragement_patterns = [
        "non lo so", "non saprei", "boh", "niente", "non capisco",
        "idk", "non ne ho idea", "non so", "???", "...", "....",
        "non ho capito", "mi arrendo", "ni", "meh", "forse",
        "i don't know", "i dont know", "i have no idea", "i give up",
        "no idea", "i don't understand", "i do not know",
    ]
    for pattern in encouragement_patterns:
        if pattern in risposta_lower or risposta_lower == pattern:
            return True, tr("heuristic_encouragement", lang)

    words = risposta.split()
    if len(words) >= 4:
        for i in range(len(words) - 3):
            if words[i].lower() == words[i+1].lower() == words[i+2].lower() == words[i+3].lower():
                return False, tr("heuristic_repeated_words", lang)

    alpha_chars = [c.lower() for c in risposta if c.isalpha()]
    if len(alpha_chars) > 80:
        unique_ratio = len(set(alpha_chars)) / len(alpha_chars)
        if unique_ratio < 0.3:
            return False, tr("heuristic_random_chars", lang)

    if len(words) <= 2 and len(risposta) < 15:
        return False, tr("heuristic_too_short_eval", lang)

    _code_indicators = ("print(", "def ", "import ", "class ", " = ", "==",
                        "{", "}", "for ", "while ", "if ", "elif ", "else:")
    looks_like_code = any(c in risposta for c in _code_indicators)

    if not looks_like_code:
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
                return False, tr("heuristic_irrelevant", lang)

    return True, ""


# ─────────────────────────────────────────────────────────────
# Prompt templates multilingua
# ─────────────────────────────────────────────────────────────

def _get_sanity_prompt(esercizio: str, risposta_utente: str, lang: str) -> str:
    if lang == "en":
        return f"""Check if the following answer is relevant to the exercise.

EXERCISE: {esercizio}

USER ANSWER: {risposta_utente}

Respond ONLY with a JSON:
{{
  "pertinente": true/false,
  "motivo": "brief explanation if not relevant, otherwise empty string"
}}

Consider NOT relevant if:
- The answer is completely off-topic or talks about something else entirely
- It consists of random characters or meaningless strings
- It is an attempt to bypass the exercise (e.g. jokes, unrelated copy-paste texts)
- It shows no effort to address the question

IMPORTANT: If the user admits they don't know (e.g. "I don't know", "I don't understand", "no idea"), consider the answer RELEVANT (it's honest). Set pertinente=true.
"""
    return f"""Verifica se la seguente risposta è pertinente all'esercizio.

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

IMPORTANTE: Se l'utente ammette di non sapere (es. "non lo so", "non capisco", "non ne ho idea"), considera la risposta PERTINENTE (è onesta). Imposta pertinente=true.
"""


def _get_evaluation_prompt(esercizio: str, risposta_utente: str, lang: str) -> str:
    if lang == "en":
        return f"""You are an expert microlearning evaluator. Evaluate the following user answer.

EXERCISE: {esercizio}

USER ANSWER: {risposta_utente}

You must return EXCLUSIVELY a valid JSON with these fields:
{{
  "commento_costruttivo": "Warm, motivating, personal comment. Use an enthusiastic tone, make the user feel capable and acknowledge the effort. 2-3 sentences.",
  "punti_di_forza": ["Up to 3 analytical points extracted from the answer; do not copy the commento_costruttivo."],
  "punti_migliorabili": ["Elements to correct or explore further, with brief reason."],
  "suggerimento_miglioramento": "Practical, specific, future-oriented suggestion. A concrete tip on what to do next to improve. 1-2 sentences.",
  "esito": "correct | partial | wrong"
}}

RULES:
- `commento_costruttivo` and `suggerimento_miglioramento` must be DIFFERENT in style and content: the first praises and motivates, the second indicates a concrete next step.
- If the user's answer is substantially correct and addresses the exercise accurately, set `esito` to "corretta". Provide at least 2 entries in `punti_di_forza` and 1-2 in `punti_migliorabili`.
- If the answer is partly right but misses key elements or contains significant errors, set `esito` to "parziale".
- If the answer is WRONG, INCOMPLETE, IMPRECISE, or does not address the exercise asked: set `esito` to "sbagliata". Be strict: an answer that talks vaguely about the topic without addressing the specific question is SBAGLIATA.
- If the answer expresses difficulty (e.g. "I don't know", "I don't understand", "I give up"): set `esito` to "parziale". Praise the honesty in `commento_costruttivo`. In `suggerimento_miglioramento` warmly invite them to use the "Ask for clarifications" button.
- If the answer is completely off-topic, meaningless, random characters, jokes, or shows no effort: set `esito` to "sbagliata". Leave `punti_di_forza` empty. Gently explain the issue in `commento_costruttivo`.
- IMPORTANT: "parziale" means the user GOT SOMETHING RIGHT. If the answer is wrong or misses the point entirely, use "sbagliata", NOT "parziale". The encouraging tone goes in `commento_costruttivo`, NOT in the esito field.
- `punti_di_forza` must be analytical, concise and not repeat `commento_costruttivo`.
- Do not add `commento_costruttivo` inside `punti_di_forza`.
- Respond ONLY with the requested JSON.
"""
    return f"""Sei un valutatore esperto di microlearning. Valuta la seguente risposta dell'utente.

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
- Se la risposta dell'utente è sostanzialmente corretta e affronta l'esercizio in modo accurato, imposta `esito` a "corretta". Fornisci almeno 2 voci in `punti_di_forza` e 1-2 in `punti_migliorabili`.
- Se la risposta è in parte giusta ma manca di elementi chiave o contiene errori significativi, imposta `esito` a "parziale".
- Se la risposta è SBAGLIATA, INCOMPLETA, IMPRECISA, o non risponde alla domanda specifica dell'esercizio: imposta `esito` a "sbagliata". Sii severo: una risposta che parla vagamente del tema senza affrontare la domanda specifica è SBAGLIATA.
- Se la risposta esprime difficoltà (es. "non lo so", "non capisco", "mi arrendo"): imposta `esito` a "parziale". Elogia l'onestà in `commento_costruttivo`. In `suggerimento_miglioramento` invita calorosamente a usare il pulsante "Chiedi chiarimenti".
- Se la risposta è totalmente fuori tema, senza senso, caratteri casuali, barzellette, o non dimostra alcuno sforzo: imposta `esito` a "sbagliata". Lascia `punti_di_forza` vuoto. Spiega gentilmente in `commento_costruttivo`.
- IMPORTANTE: "parziale" significa che l'utente ha AZZECCATO QUALCOSA. Se la risposta è sbagliata o fuori punto, usa "sbagliata", NON "parziale". Il tono incoraggiante va nel `commento_costruttivo`, NON nel campo `esito`.
- `punti_di_forza` deve essere analitico, sintetico e non ripetere il `commento_costruttivo`.
- Non aggiungere il `commento_costruttivo` all'interno di `punti_di_forza`.
- Rispondi SOLO con il JSON richiesto.
"""


def _get_hint_prompt(esercizio: str, risposta_utente: str, livello: str, tentativo: int, lang: str) -> str:
    if lang == "en":
        return f"""The user got this exercise wrong (level {livello}, attempt {tentativo}).

EXERCISE: {esercizio}

USER ANSWER: {risposta_utente}

Generate a short hint (max 60 words) in English that:
- Does not give the answer directly
- Makes the user reflect on what they got wrong
- Suggests a direction or key concept to review
- Has an encouraging tone

Respond ONLY with the hint text, without JSON formatting.
"""
    return f"""L'utente ha sbagliato questo esercizio (livello {livello}, tentativo {tentativo}).

ESERCIZIO: {esercizio}

RISPOSTA DELL'UTENTE: {risposta_utente}

Genera un hint breve (max 60 parole) in italiano che:
- Non dia la risposta direttamente
- Faccia riflettere l'utente su cosa ha sbagliato
- Suggerisca una direzione o un concetto chiave da rivedere
- Abbia un tono incoraggiante

Rispondi SOLO con il testo dell'hint, senza formattazione JSON.
"""


def _get_summary_prompt(storico_section: str, diario_section: str, livello: str, lang: str) -> str:
    if lang == "en":
        return f"""Generate a cumulative final summary in English for a microlearning path.

You have the user's answer history and logbook notes collected during the path.

USER LEVEL: {livello}

ANSWER HISTORY:
{storico_section}

LOGBOOK:
{diario_section}

You must respond EXCLUSIVELY with a valid JSON in the format:
{{
  "punti_di_forza": ["string"],
  "punti_da_migliorare": ["string"],
  "diario_di_bordo": "string",
  "saluto_conclusivo": "string"
}}

RULES:
- The summary must be based on the user's actual answers.
- Do not include a generic constructive comment.
- Provide at least one concrete point in `punti_di_forza` and at least one in `punti_da_migliorare`.
- `diario_di_bordo` must contain a synthesis of the path observations, not a word-for-word repetition.
- `saluto_conclusivo` must be a motivating, short closing oriented toward continuing learning.
- Respond ONLY with the requested JSON, without additional text.
"""
    return f"""Genera un riepilogo finale cumulativo in italiano per un percorso di microlearning.

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


def _get_alternative_explanation_prompt(argomento: str, spiegazione_originale: str, dubbio_utente: str, livello: str, lang: str) -> str:
    if lang == "en":
        return f"""The user did not understand this topic at {livello} level.

TOPIC: {argomento}

ORIGINAL EXPLANATION: {spiegazione_originale}

USER'S DOUBT: {dubbio_utente}

You must respond EXCLUSIVELY with a valid JSON object in the format:
{{
  "spiegazione_semplificata": "Simplified explanation text",
  "esempio_pratico": "A short concrete example illustrating the concept",
  "passaggi": ["First clear step", "Second step", "Third step"]
}}

The explanation must be:
- clearer and more direct than the original
- appropriate for a {livello} level user
- linked to fundamental concepts if intermediate
- if advanced, include a practical reason and a mini use-case
- with a concrete example and practical steps
- focused on resolving the user's specific doubt
- no longer than 130 words for the explanation
"""
    return f"""L'utente non ha capito questo argomento a livello {livello}.

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


def _get_farewell_prompt(nome_utente: str, livello: str, interruzione: bool, lang: str) -> tuple[str, str]:
    if interruzione:
        if lang == "en":
            system = "You are an empathetic and encouraging tutor. Generate a closing message in English without JSON format."
            prompt = (
                f"You just helped {nome_utente}, level {livello}, who needs a reassuring closing. "
                "Generate a short farewell in English explaining that it's normal to have doubts during learning "
                "and that you will resume the concepts together when they come back to study. "
                "Be warm, human, and motivating."
            )
        else:
            system = "Sei un tutor empatico e incoraggiante. Genera un messaggio di chiusura in italiano senza formato JSON."
            prompt = (
                f"Hai appena aiutato {nome_utente}, livello {livello}, che ha bisogno di una chiusura rassicurante. "
                "Genera un breve saluto finale in italiano che spieghi che è normale avere dubbi durante l'apprendimento "
                "e che riprenderete insieme i concetti quando tornerete a studiare. "
                "Sii caloroso, umano e motivante."
            )
    else:
        if lang == "en":
            system = "You are an empathetic and encouraging tutor. Generate a closing message in English without JSON format."
            prompt = (
                f"You just concluded a session with {nome_utente}, level {livello}. "
                "Generate a short farewell in English that praises the progress made today, "
                "highlights the effort and motivates to come back. "
                "Be positive, personal, and encouraging."
            )
        else:
            system = "Sei un tutor empatico e incoraggiante. Genera un messaggio di chiusura in italiano senza formato JSON."
            prompt = (
                f"Hai appena concluso una sessione con {nome_utente}, livello {livello}. "
                "Genera un breve saluto finale in italiano che lodi il progresso fatto oggi, "
                "sottolinei l'impegno e motivi a tornare. "
                "Sii positivo, personale e incoraggiante."
            )
    return system, prompt


def _get_generation_user_prompt(topic: str, level: str, lang: str, num_modules: int = 3) -> str:
    if lang == "en":
        base = (
            f"Topic: {topic}\n"
            f"Level: {level}\n"
            f"Number of modules: {num_modules}\n"
            "Respond exclusively with a valid JSON that matches exactly the structure requested in the system prompt. "
            "Do not add free text or comments."
        )
    else:
        base = (
            f"Argomento: {topic}\n"
            f"Livello: {level}\n"
            f"Numero di moduli: {num_modules}\n"
            "Rispondi esclusivamente con un JSON valido che corrisponda esattamente alla struttura richiesta dal system prompt. "
            "Non aggiungere testo libero o commenti."
        )
    return base


def _get_generation_context_prefix(lang: str) -> str:
    if lang == "en":
        return "\n\nModules already created on similar topics (DO NOT repeat the same content; cover DIFFERENT aspects):\n"
    return "\n\nModuli già creati su argomenti simili (NON ripetere gli stessi contenuti; copri aspetti DIVERSI):\n"


# ─────────────────────────────────────────────────────────────
# Opzione C — Sanity check LLM (doppio passaggio)
# ─────────────────────────────────────────────────────────────

def sanity_check_risposta(esercizio: str, risposta_utente: str, lang: str = "it"):

    if not ENABLE_SANITY_CHECK:
        return True, ""

    prompt = _get_sanity_prompt(esercizio, risposta_utente, lang)

    system_content = (
        "You are a relevance validator. Respond only in JSON."
        if lang == "en"
        else "Sei un validatore di pertinenza. Rispondi solo in JSON."
    )

    messages = [
        {"role": "system", "content": system_content},
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


# ─────────────────────────────────────────────────────────────
# Pipeline valutazione condivisa (heuristic → sanity → LLM → hint)
# ─────────────────────────────────────────────────────────────

def valuta_con_pipeline(
    esercizio: str,
    soluzione: str,
    livello: str,
    lang: str = "it",
    tentativi: int = 0,
) -> dict:
    """Pipeline completa di valutazione usata da Streamlit, Flask e CLI.

    Returns dict con:
        valido: bool - se la risposta ha passato i filtri
        esito: str | None - "corretta" / "parziale" / "sbagliata"
        feedback: FeedbackValutazione | None
        hint: str | None - hint per risposte sbagliate
        message: str | None - messaggio di errore da mostrare all'utente
        archive: bool - se il modulo va archiviato (>=2 tentativi)
    """
    result = {
        "valido": True,
        "esito": None,
        "feedback": None,
        "hint": None,
        "message": None,
        "archive": False,
    }

    # 1. Heuristic filter
    valido_eur, motivo_eur = valida_input_euristico(esercizio, soluzione, lang)
    if not valido_eur:
        result["valido"] = False
        result["message"] = motivo_eur
        return result

    # 2. Sanity check
    pertinente, motivo_sc = sanity_check_risposta(esercizio, soluzione, lang)
    if not pertinente:
        result["valido"] = False
        msg = tr("not_pertinent", lang)
        if motivo_sc:
            msg += f": {motivo_sc}"
        result["message"] = msg
        return result

    # 3. LLM evaluation
    feedback = valuta_risposta(esercizio, soluzione, lang)
    result["feedback"] = feedback
    result["esito"] = feedback.esito

    # 4. Hint + archive check for wrong/partial
    if feedback.esito in ("sbagliata", "parziale"):
        nuovi_tentativi = tentativi + 1
        hint = genera_hint(esercizio, soluzione, livello, nuovi_tentativi, lang)
        result["hint"] = hint
        if nuovi_tentativi >= 2:
            result["archive"] = True

    return result

def generate_microlearning_path(topic: str, level: str, context_modules: list | None = None, lang: str = "it", num_modules: int = 3) -> TutorResponse:
    user_prompt = _get_generation_user_prompt(topic, level, lang, num_modules)

    if context_modules:
        contesto = _get_generation_context_prefix(lang)
        for i, cm in enumerate(context_modules[:3], 1):
            contesto += f"{i}. [{cm['topic']}] {cm['titolo']}: {cm['spiegazione'][:200]}\n"
        user_prompt += contesto

    system_prompt_path = get_system_prompt_path(lang)
    system_prompt = system_prompt_path.read_text(encoding='utf-8')
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response_text = _get_chat_response_text(messages)

    try:
        return TutorResponse.model_validate_json(_normalize_json_text(response_text))
    except (ValidationError, ValueError) as exc:
        raise RuntimeError(
            tr("invalid_json_response", lang)
            + f" Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def valuta_risposta(esercizio: str, risposta_utente: str, lang: str = "it") -> FeedbackValutazione:
    evaluation_prompt = _get_evaluation_prompt(esercizio, risposta_utente, lang)

    system_content = (
        "You are an expert microlearning evaluator."
        if lang == "en"
        else "Sei un valutatore esperto di microlearning."
    )

    messages = [
        {"role": "system", "content": system_content},
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
            tr("eval_parse_error", lang)
            + f" Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_hint(esercizio: str, risposta_utente: str, livello: str, tentativo: int = 1, lang: str = "it") -> str:
    hint_prompt = _get_hint_prompt(esercizio, risposta_utente, livello, tentativo, lang)

    system_content = (
        "You are a tutor that guides the user to discover the answer on their own."
        if lang == "en"
        else "Sei un tutor che guida l'utente a scoprire la risposta da solo."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": hint_prompt},
    ]

    fallback_hints = {
        1: tr("fallback_hint_1", lang),
        2: tr("fallback_hint_2", lang),
    }

    try:
        hint = _get_chat_response_text(messages, temperature=CHAT_TEMPERATURE_HINT)
        if hint and len(hint) > 5:
            return hint
    except Exception:
        pass

    return fallback_hints.get(tentativo, fallback_hints[1])


def genera_riepilogo_finale(storico_risposte: list[dict], diario_note: list[str], livello: str, lang: str = "it") -> RiepilogoFinale:

    if not storico_risposte:
        raise ValueError(tr("empty_history", lang))

    storico_testo = []
    for idx, item in enumerate(storico_risposte, start=1):
        esercizio = item.get('esercizio', '').strip()
        soluzione = item.get('soluzione', '').strip()
        storico_testo.append(
            f"{idx}. Esercizio: {esercizio}\n   Risposta utente: {soluzione}"
        )
    storico_section = "\n".join(storico_testo)
    diario_section = "\n".join([f"- {nota.strip()}" for nota in diario_note if nota.strip()]) if diario_note else "- Nessuna nota aggiuntiva."

    summary_prompt = _get_summary_prompt(storico_section, diario_section, livello, lang)

    system_content = (
        "You are an assistant that generates final summaries in English."
        if lang == "en"
        else "Sei un assistente che genera riepiloghi finali in italiano."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": summary_prompt},
    ]
    response_text = _get_chat_response_text(messages)

    try:
        return RiepilogoFinale.model_validate_json(_normalize_json_text(response_text))
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            tr("summary_error", lang)
            + f" Contenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_spiegazione_alternativa(argomento: str, spiegazione_originale: str, dubbio_utente: str, livello: str, lang: str = "it") -> dict:

    alt_prompt = _get_alternative_explanation_prompt(argomento, spiegazione_originale, dubbio_utente, livello, lang)

    system_content = (
        "You are a tutor that explains concepts in a simple and clear way."
        if lang == "en"
        else "Sei un tutor che spiega concetti in modo semplice e chiaro."
    )

    messages = [
        {"role": "system", "content": system_content},
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
            tr("clarification_parse_error", lang) + f"\nContenuto ricevuto: {response_text[:500]}"
        ) from exc


def genera_saluto_finale(nome_utente: str, livello: str, interruzione_per_dubbio: bool, lang: str = "it") -> str:
    system, prompt = _get_farewell_prompt(nome_utente, livello, interruzione_per_dubbio, lang)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    return _get_chat_response_text(messages)


# ─────────────────────────────────────────────────────────────
# Traduzione moduli (per cambio lingua lato UI)
# ─────────────────────────────────────────────────────────────

def traduci_percorso_completo(
    moduli_data: list[dict],
    objective: str | None,
    target_lang: str,
) -> tuple[list[dict], str | None]:
    """Traduce moduli + objective in una singola chiamata LLM.

    Args:
        moduli_data: lista di dict con chiavi titolo_modulo/titolo, spiegazione,
                     esercizio_pratico/esercizio (più eventuali chiavi extra)
        objective: testo dell'objective (o None)
        target_lang: lingua target ("it" o "en")

    Returns:
        (moduli_tradotti, objective_tradotto)
        In caso di errore restituisce gli originali.
    """
    if not moduli_data and not objective:
        return moduli_data, objective

    target_name = "English" if target_lang == "en" else "Italian"

    modules_json = []
    for m in moduli_data:
        titolo = m.get("titolo_modulo") or m.get("titolo") or ""
        spiegazione = m.get("spiegazione", "")
        esercizio = m.get("esercizio_pratico") or m.get("esercizio") or ""
        modules_json.append({
            "titolo_modulo": titolo,
            "spiegazione": spiegazione,
            "esercizio_pratico": esercizio,
        })

    prompt = f"""Translate the following microlearning content into {target_name}.
Preserve all meaning, structure, and educational content exactly.

Respond ONLY with a valid JSON object:
{{
  "objective": {"translated objective text"} or null,
  "moduli": [
    {{
      "titolo_modulo": "translated title",
      "spiegazione": "translated explanation",
      "esercizio_pratico": "translated exercise"
    }}
  ]
}}

OBJECTIVE TO TRANSLATE:
{json.dumps(objective, ensure_ascii=False) if objective else "null"}

MODULES TO TRANSLATE:
{json.dumps(modules_json, ensure_ascii=False, indent=2)}
"""

    messages = [
        {"role": "system", "content": f"You are a professional translator. Translate educational content to {target_name}. Respond only with the JSON object."},
        {"role": "user", "content": prompt},
    ]

    try:
        response_text = _get_chat_response_text(messages, temperature=TRANSLATION_TEMPERATURE, model=TRANSLATION_MODEL, timeout=TRANSLATION_TIMEOUT)
        result = json.loads(_normalize_json_text(response_text))

        translated_obj = result.get("objective") if objective else None
        if translated_obj is None and objective:
            translated_obj = objective

        translated_mods_raw = result.get("moduli", [])

        new_moduli = []
        for i, m in enumerate(moduli_data):
            new_m = dict(m)
            t = translated_mods_raw[i] if i < len(translated_mods_raw) else {}
            if "titolo_modulo" in m or "titolo_modulo" in new_m:
                new_m["titolo_modulo"] = t.get("titolo_modulo", m.get("titolo_modulo", ""))
            if "titolo" in m and "titolo_modulo" not in m:
                new_m["titolo"] = t.get("titolo_modulo", m.get("titolo", ""))
            new_m["spiegazione"] = t.get("spiegazione", m.get("spiegazione", ""))
            if "esercizio_pratico" in m or "esercizio_pratico" in new_m:
                new_m["esercizio_pratico"] = t.get("esercizio_pratico", m.get("esercizio_pratico", ""))
            if "esercizio" in m and "esercizio_pratico" not in m:
                new_m["esercizio"] = t.get("esercizio_pratico", m.get("esercizio", ""))
            new_moduli.append(new_m)

        return new_moduli, translated_obj
    except Exception:
        return moduli_data, objective


def traduci_modulo_singolo(
    titolo: str,
    spiegazione: str,
    esercizio: str,
    target_lang: str,
) -> dict:
    """Traduce un singolo modulo. Returns dict with titolo, spiegazione, esercizio.

    In caso di errore restituisce gli originali.
    """
    if target_lang == "it":
        return {"titolo": titolo, "spiegazione": spiegazione, "esercizio": esercizio}

    target_name = "English" if target_lang == "en" else "Italian"

    prompt = f"""Translate the following microlearning module content into {target_name}.
Preserve all meaning and educational content.

Respond ONLY with a valid JSON object:
{{
  "titolo_modulo": "translated title",
  "spiegazione": "translated explanation",
  "esercizio_pratico": "translated exercise"
}}

MODULE TO TRANSLATE:
TITOLO: {titolo}
SPIEGAZIONE: {spiegazione}
ESERCIZIO: {esercizio}
"""

    messages = [
        {"role": "system", "content": f"You are a professional translator. Translate educational content to {target_name}. Respond only with the JSON object."},
        {"role": "user", "content": prompt},
    ]

    try:
        response_text = _get_chat_response_text(messages, temperature=TRANSLATION_TEMPERATURE, model=TRANSLATION_MODEL, timeout=TRANSLATION_TIMEOUT)
        result = json.loads(_normalize_json_text(response_text))
        return {
            "titolo": result.get("titolo_modulo", titolo),
            "spiegazione": result.get("spiegazione", spiegazione),
            "esercizio": result.get("esercizio_pratico", esercizio),
        }
    except Exception:
        return {"titolo": titolo, "spiegazione": spiegazione, "esercizio": esercizio}
