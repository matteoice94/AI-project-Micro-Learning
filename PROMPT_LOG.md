# PROMPT LOG - MLPG Project
Registro delle modifiche e dei test effettuati sui prompt.

## [15 Maggio 2026] - Setup Iniziale
- **Azione:** Creato `system_mlpg.md` basato sulla Specifica v3.0.
- **Obiettivo:** Definire il comportamento del tutor e il formato JSON di output.
- **Risultato atteso:** L'LLM deve restituire esattamente 3 moduli validabili via Pydantic.

## [15 Maggio 2026] - Prompt aggiornati
- **Azione:** Aggiornato prompt del tutor per richiedere risposta JSON-only e `spiegazione_semplificata` in caso di confusione.
- **Obiettivo:** Assicurare che il modello non generi testo libero oltre al JSON e che fornisca spiegazioni semplificate quando l'utente dice di non capire.
- **Risultato atteso:** Risposta valida JSON con campo `spiegazione_semplificata` e nessun modulo rigenerato inutilmente.

- **Azione:** Aggiunta logica di parsing in `src/generator.py` per estrarre JSON da risposte contenenti blocchi markdown.
- **Obiettivo:** Rendere robusto il processo di validazione anche quando Gemini ritorna codice o testo extra.
- **Risultato atteso:** Valutazioni e spiegazioni alternative processate correttamente senza errori di parsing.

- **Azione:** Aggiunta prompt di chiusura empatica personalizzata in `genera_saluto_finale()`.
- **Obiettivo:** Generare un saluto finale motivante e rassicurante, diverso se l'utente ha interrotto per dubbi.
- **Risultato atteso:** Saluto umano in italiano, con tono incoraggiante e rassicurante.

## [19 Maggio 2026] - Prompt per spiegazioni mirate ai livelli intermedi/avanzati
- **Azione:** Aggiornato `genera_spiegazione_alternativa()` perché risponda in modo differenziato secondo il livello `base/intermedio/avanzato`.
- **Obiettivo:** Fornire spiegazioni più utili per utenti intermedi/avanzati usando esempio pratico e passaggi chiari.
- **Risultato atteso:** L'AI fornisce una spiegazione mirata al livello e un output JSON strutturato con contenuti di supporto.

- **Azione:** Modificato `main.py` per chiedere un dubbio specifico e passare quel contesto al prompt.
- **Obiettivo:** Ridurre l'ambiguità del feedback dell'utente e indirizzare meglio la spiegazione alternativa.
- **Risultato atteso:** Il tutor risponde a un punto preciso di confusione e non ripete un modulo inutile.

## [19 Maggio 2026] - Web interface e Streamlit
- **Azione:** Creato `app.py` (Flask) e `streamlit_app.py` con interfaccia Streamlit.
- **Obiettivo:** Rendere il tutor fruibile tramite browser con UI grafica e percorsi interattivi.
- **Risultato atteso:** L’utente può usare il tutor via web, generare moduli e richiedere chiarimenti mirati senza terminale.

- **Azione:** Aggiornato `requirements.txt` includendo `flask` e `streamlit`.
- **Obiettivo:** Assicurare che l’ambiente supporti le nuove interfacce web.
- **Risultato atteso:** Installazione completa delle dipendenze per eseguire sia Flask che Streamlit.

---
## [25 Maggio 2026] - Retry e prompt token-efficienti
- **Azione:** Aggiunto `_call_with_retries()` in `src/generator.py` e aggiornato `Prompts/system_mlpg.md` per richiedere risposte estremamente concise e token-efficienti.
- **Obiettivo:** Gestire gli errori 429 con un retry su backoff semplificato e ridurre il numero totale di chiamate API.
- **Risultato atteso:** Maggiore robustezza contro i limiti quota, output JSON più compatto e meno spreco di token.
- **Nota:** L'errore della mancata visualizzazione dei punti di forza è ancora presente e dovrà essere risolto separatamente.

## [28 Maggio 2026] - Allineamento flusso finale e API cumulativo
- **Azione:** Rifattorizzato il flusso di riepilogo finale per generarlo con una singola chiamata cumulativa dopo il terzo modulo.
- **Obiettivo:** Eliminare le chiamate API intermedie per il riepilogo e mantenere una cronologia utente coerente tra terminale, Streamlit e UI HTML.
- **Risultato osservato:** Il percorso iniziale ora restituisce solo `percorso_studio`, mentre il riepilogo finale viene generato separatamente tramite `genera_riepilogo_finale()`.
- **Dettagli:** Aggiornati `src/models.py`, `src/generator.py`, `streamlit_app.py`, `templates/index.html` e `app.py`.
- **Nota:** Il saluto conclusivo è stato spostato nella risposta del riepilogo finale e non viene più generato come output separato per ogni modulo.

---
*Aggiungi qui le prossime modifiche quando testerai i prompt su VS Code.*

## [24 Giugno 2026] - Recovery flow, RAG memory e storico persistente
- **Azione:** Corretto endpoint OpenRouter da `/v1/chat/completions` a `/api/v1/chat/completions`.
  - **Obiettivo:** Risolvere HTTP 404.
  - **Risultato:** API funzionante.

- **Azione:** Applicata `_normalize_json_text()` in tutte le funzioni (`valuta_risposta`, `genera_spiegazione_alternativa`, `genera_riepilogo_finale`, `generate_microlearning_path`).
  - **Obiettivo:** Gestire risposte LLM con blocchi ```json markdown.
  - **Risultato:** Parsing JSON robusto in tutta la codebase.

- **Azione:** Aggiornato prompt di `valuta_risposta` per differenziare `commento_costruttivo` (caloroso/entusiasta) da `suggerimento_miglioramento` (concreto/orientato al futuro) e aggiunto campo `esito` ("corretta"/"parziale"/"sbagliata").
  - **Obiettivo:** Feedback più espressivo e distinguibile tra i due campi.
  - **Risultato:** Commento motivante e suggerimento pratico con stili diversi.

- **Azione:** Creata funzione `genera_hint()` con fallback testuale, attivata al primo errore.
  - **Obiettivo:** Guidare l'utente senza dare la risposta.
  - **Risultato:** Hint LLM (max 60 parole) o fallback generico.

- **Azione:** Implementato recovery flow (1° errore → hint, 2° errore diverso → archivia modulo per futura sessione).
  - **Obiettivo:** Evitare stress da ripetuti insuccessi.
  - **Risultato:** Modulo archiviato con dati completi, riprendibile dalla sidebar.

- **Azione:** Aggiunto campo `esito` al modello `FeedbackValutazione`.
  - **Obiettivo:** Discriminare automaticamente risposte corrette/parziali/sbagliate.
  - **Risultato:** Logica di recovery basata su flag esplicito.

- **Azione:** Creato `src/database.py` con SQLite persistente, embedding via OpenRouter (`text-embedding-3-small`) e RAG retrieval (`find_similar_modules`).
  - **Obiettivo:** Memoria a lungo termine tra sessioni e arricchimento contestuale dei prompt.
  - **Risultato:** I nuovi percorsi ricevono come contesto i moduli semanticamente simili del passato.

- **Azione:** Aggiunta sezione "Storico" nella sidebar e vista moduli passati cliccabili/riesumibili.
  - **Obiettivo:** Navigare sessioni precedenti e riprovare moduli.
  - **Risultato:** Storico persistente con tentativi, stato e riapertura moduli.

---

## [25 Giugno 2026] - Completamento migrazione provider Gemini → OpenRouter
- **Azione:** Migrazione completa da Google Gemini a OpenRouter per tutte le funzioni in `src/generator.py`.
  - **Dettagli:** 
    - Endpoint corretto: `https://api.openrouter.ai/v1/chat/completions`
    - Modello usato: `gpt-4o-mini` (default OpenRouter)
    - Tutte le funzioni (`generate_microlearning_path`, `valuta_risposta`, `genera_spiegazione_alternativa`, `genera_riepilogo_finale`, `genera_hint`, `genera_saluto_finale`) ora usano OpenRouter via `urllib.request`
  - **Obiettivo:** Eliminare dipendenza da Google Gemini API e sfruttare OpenRouter per maggiore flessibilità di modello.
  - **Risultato:** Codebase funzionante con OpenRouter, `.env` aggiornato con `OPENROUTER_API_KEY`.

- **Azione:** Pulizia di `requirements.txt`: rimosso `google-generativeai`, mantenute sole dipendenze essenziali.
  - **Obiettivo:** Ridurre weight del progetto e eliminate dipendenze inutili.
  - **Risultato:** Setup più leggero e focus su OpenRouter.

- **Azione:** Ripristino e validazione di `streamlit_app.py` da git (file corrotto durante edit manuale).
  - **Obiettivo:** Recuperare struttura integra con tutte le importazioni (`streamlit`, `src.generator`, `src.database`).
  - **Risultato:** Streamlit app completamente funzionante con storico sessioni, gestione moduli e riapertura moduli archiviati.

---

## [26 Giugno 2026] - Refactoring storico, login multi-utente e UI cards
- **Azione:** Refactoring completo della sezione "Storico Percorsi" nella sidebar: sostituiti bottoni con lista Markdown compatta, badge pills colorati e pulsante ▶ per aprire moduli.
  - **Obiettivo:** Ottimizzare storico per spazi stretti (sidebar).
  - **Risultato:** Lista moduli con emoji stato, badge `Fatto`/`Arch.`/`Aperto` e navigazione inline.

- **Azione:** Aggiunta gestione sessioni (rinomina ✏️ ed elimina 🗑️) e gestione moduli (cambio stato, rinomina, elimina) all'interno dello storico.
  - **Obiettivo:** Dare all'utente il controllo completo sui propri percorsi.
  - **Risultato:** Sessioni e moduli modificabili direttamente dalla sidebar.

- **Azione:** Aggiunta barra di avanzamento `st.progress()` sotto l'obiettivo di apprendimento.
  - **Obiettivo:** Mostrare visivamente il progresso (X/Y moduli completati).
  - **Risultato:** Feedback visivo immediato sull'avanzamento nel percorso.

- **Azione:** Implementato effetto card con gradient, bordo semitrasparente e border-radius per colonne spiegazione/esercizio. Aggiunti badge pills colorati con CSS. Attivato syntax highlighting per blocchi di codice tramite `st.markdown()`.
  - **Obiettivo:** Migliorare leggibilità e impatto visivo dell'interfaccia.
  - **Risultato:** UI più moderna, codice evidenziato nel tema scuro, badge stato colorati.

- **Azione:** Allineata UI dei moduli storico a quella dei moduli attivi: layout a due colonne, feedback persistente in `session_state`, hint persistente.
  - **Obiettivo:** UX coerente tra moduli archiviati e correnti.
  - **Risultato:** Stessa esperienza di navigazione e valutazione in entrambi i contesti.

- **Azione:** Le risposte corrette dei moduli archiviati vengono ora salvate e pre-caricate nella textarea alla riapertura del modulo.
  - **Obiettivo:** Permettere all'utente di rileggere le proprie soluzioni passate.
  - **Risultato:** Textarea pre-compilata con l'ultima risposta corretta dal DB o da `risposte_utente`.

- **Azione:** Implementato sistema di autenticazione multi-utente: tabella `users` in SQLite, schermata di login/registrazione all'avvio, storico filtrato per `user_id`.
  - **Obiettivo:** Ogni utente ha il proprio storico personale (condivisione via ngrok sicura).
  - **Risultato:** Login con username/password (hashata), registrazione, logout. Sessioni filtrate per utente.

---

## [1 Luglio 2026] - Prompt, UX e Logo

### Prompt — Tutor incoraggiante per risposte "non lo so"
- **Azione:** Modificato `valida_input_euristico()` e `valuta_risposta()` per non bloccare/bloccare meno le risposte di difficoltà.
  - **Obiettivo:** Invece di dire "Sembra che tu non abbia provato", il tutor ora incoraggia e suggerisce di usare "Chiedi chiarimenti".
  - **Dettagli:** I pattern "non lo so", "non capisco" etc. non sono più bloccanti ma mostrano un messaggio incoraggiante. Il prompt di valutazione AI imposta `esito: parziale` (non "sbagliata") e invita a chiedere aiuto.

### UX — Multi-pagina Streamlit (st.navigation)
- **Azione:** Convertita app da single-page a multi-pagina con `st.navigation` e `st.Page`.
  - **Obiettivo:** Separare creazione percorso da gestione storico, dando più spazio a quest'ultimo.
  - **Risultato:** Due pagine: "Nuovo Percorso" e "I Miei Percorsi". Sidebar contestuale (configurazione solo nella prima). Componente condiviso `_render_modulo_archivio()`.

### UX — Logo robot 8-bit animato
- **Azione:** Creato logo pixel art (432x348, blocchi 24px) con palette MLPG.
  - **Obiettivo:** Dare identità visiva al tutor con un personaggio riconoscibile.
  - **Risultato:** 3 espressioni statiche (neutro 2x2, happy ^ ^, thinking 1px) + versione animata con glitch+morph di 12 secondi.

### UX — Robot come indicatore di stato nell'UI
- **Azione:** Integrato il robot in login, welcome, sidebar e sotto i pulsanti di azione.
  - **Obiettivo:** Feedback visivo immediato sullo stato dell'operazione (in attesa, in elaborazione, completata).
  - **Risultato:** State machine: neutro (idle) → thinking (elaborazione) → happy (successo). Il robot segue l'azione attiva (valutazione o chiarimenti), mutuamente esclusivo.

## [6 Luglio 2026] - Internazionalizzazione IT/EN
- **Azione:** Creato modulo `src/i18n.py` con dizionario centralizzato ~260 chiavi per italiano e inglese.
- **Obiettivo:** Supporto lingua su tutte le interfacce (Streamlit, Flask/HTML, CLI).
- **Risultato:** Selettore lingua in sidebar e login page. Tutti i testi UI tradotti via `tr()`. LLM prompt e output automaticamente nella lingua selezionata (system_mlpg_en.md).

## [6 Luglio 2026] - Traduzione moduli on-the-fly
- **Azione:** Aggiunte funzioni `traduci_percorso_completo()` e `traduci_modulo_singolo()` in `src/generator.py`.
- **Obiettivo:** Cambiando lingua, i moduli già generati vengono tradotti via LLM. Le risposte salvate dell'utente NON vengono mai tradotte.
- **Risultato:** `_sync_lang()` traduce percorso attivo + archiviati + storico (con cache). Modello di traduzione: `google/gemini-flash-1.5` (veloce).

## [6 Luglio 2026] - Pipeline valutazione unificata
- **Azione:** Creata `valuta_con_pipeline()` in `src/generator.py` (heuristic → sanity → LLM eval → hint → archive).
- **Obiettivo:** Eliminare 130+ righe duplicate tra streamlit_app.py, app.py, main.py.
- **Risultato:** Streamlit, Flask e CLI usano la stessa funzione.

## [6 Luglio 2026] - Bilanciamento esito valutazione
- **Azione:** Aggiornati i prompt di valutazione (IT e EN) per rendere "sbagliata" più frequente e "parziale" più selettivo.
- **Obiettivo:** Evitare che qualsiasi risposta venga classificata come "parziale" impedendo l'archiviazione dopo 2 errori.
- **Modifica:** Regola esplicita: "parziale" = l'utente ha azzeccato qualcosa. Risposte sbagliate/imprecise/incomplete → "sbagliata". Incoraggiamento nel commento, non nell'esito.
- **Heuristic filter:** Passato da match esatto a substring per catturare risposte come "non lo so, mi dispiace".

## [6 Luglio 2026] - Sanity check: "non lo so" ora considerato pertinente
- **Azione:** Aggiornato il prompt del sanity check (IT e EN) per escludere le ammissioni di difficoltà dai criteri "non pertinente".
- **Obiettivo:** Evitare che "non lo so" venga bloccato con messaggi passivo-aggressivi ("non dimostra alcuno sforzo").
- **Risultato:** "non lo so" passa il sanity check e arriva alla valutazione, che risponde in modo incoraggiante.

## [7 Luglio 2026] - Logo 8-bit cartuccia SNES
- **Azione:** Generato prompt per Claude per logo MLPG in stile pixel art / 8-bit.
- **Obiettivo:** Creare un logo con robot 8-bit e testo "MLPG" dentro una cartuccia stile SNES con effetto glow/neon.
- **Prompt Claude:** Logo SVG con cartuccia videogioco, robot pixel art scalato dall'esistente, testo MLPG in pixel font oro, doppio alone glow dietro robot e sotto testo, circuiti decorativi oro, palette blu/indaco/oro.
- **Risultato:** SVG salvato in `logos/mlpg_logo.svg` — cartuccia con ombra, glow radiale, testo con 2 layer di ombra glow. Robot scalato 0.55x centrato nella cartuccia.