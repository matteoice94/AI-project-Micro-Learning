# INCIDENT LOG - MLPG Project
Registro degli errori tecnici e dei bug riscontrati durante lo sviluppo.

## [15 Maggio 2026] - Configurazione Ambiente
- **Stato:** Setup iniziale completato.
- **Note:** Pronto per la Fase 1 (Building).

## [15 Maggio 2026] - Errori riscontrati durante lo sviluppo
- **Errore:** Modello Gemini non supportato inizialmente usato `gemini-1.5-flash`.
  - **Soluzione:** Aggiornato a `models/gemini-2.5-flash` in `src/generator.py`.
- **Errore:** Risposte AI con testo extra o blocchi markdown impedivano il parsing JSON.
  - **Soluzione:** Aggiunta logica di pulizia JSON in `valuta_risposta()` e `genera_spiegazione_alternativa()`.
- **Errore:** Il tutor doveva fermarsi e spiegare meglio quando l'utente non capiva, ma non c'era una fine empatica.
  - **Soluzione:** Implementata funzione `genera_saluto_finale()` e aggiornato il flusso in `src/main.py`.
- **Errore:** La conclusione finale era poco chiara e non separava correttamente livello, punti di forza e note.
  - **Soluzione:** Ristrutturato il riepilogo in `src/main.py` con sezioni distinte.
- **Errore:** Bug di indentazione su `main.py` durante la gestione della conferma sulla comprensione.
  - **Soluzione:** Corretto il blocco `if continua ...` e rivisto il ciclo di comprensione.

## [19 Maggio 2026] - Miglioramento gestione confusione intermedio/avanzato
- **Errore:** La gestione della confusione non era sufficientemente mirata per utenti di livello intermedio o avanzato.
  - **Soluzione:** Estesa `genera_spiegazione_alternativa()` per utilizzare il livello utente e generare output strutturato con spiegazione semplificata, esempio pratico e passaggi consigliati.
- **Errore:** La domanda di chiarimento era troppo generica.
  - **Soluzione:** Aggiornato `main.py` per chiedere l’area precisa di confusione e passare questo dettaglio al prompt dell’AI.

## [19 Maggio 2026] - Estensione interfacce web
- **Errore:** L’applicazione era limitata al terminale e non offriva una UI grafica accessibile.
  - **Soluzione:** Creati `app.py` (Flask), `streamlit_app.py` (Streamlit) e l’interfaccia HTML in `templates/index.html`.
- **Errore:** La versione web non era supportata da `requirements.txt`.
  - **Soluzione:** Aggiornato `requirements.txt` con `flask` e `streamlit`.

---

## [25 Maggio 2026] - Superamento quota giornaliera (Error 429)
- **Data:** 25 Maggio 2026
- **Problema:** Superamento quota giornaliera (Error 429).
  - **Dettagli:** Le chiamate all'API Gemini restituivano errori di rate limit durante picchi di utilizzo.
- **Soluzione adottata:** Implementazione di una logica di Retry con attesa (Exponential Backoff semplificato) e consolidamento dei prompt per ridurre il numero totale di chiamate API.
  - **Note implementative:** Aggiunto `_call_with_retries()` in `src/generator.py` che effettua fino a 3 tentativi con attesa tra i retry; avvolte tutte le chiamate a `model.generate_content(...)`.
- **Errore attuale:** Mancata visualizzazione dei punti di forza nel riepilogo finale.
  - **Stato:** Non risolto.
  - **Dettagli:** Il flusso dati dei `punti_di_forza` viene raccorto correttamente ma non appare nella visualizzazione finale o nella risposta JSON del riepilogo.
- **Lezione appresa:** La progettazione efficiente del software deve sempre considerare i limiti di risorsa delle API esterne.

## [28 Maggio 2026] - Correzione flusso riepilogo finale e UI
- **Errore:** Il percorso generato dal modello richiedeva ancora l’oggetto `feedback_valutazione` incorporato, pur essendo ora gestito separatamente.
  - **Soluzione:** Rimosso `feedback_valutazione` da `Prompts/system_mlpg.md` e aggiornato `src/models.py` per mantenere `TutorResponse` separato da `RiepilogoFinale`.
- **Errore:** `RiepilogoFinale` conteneva ancora `commento_costruttivo` non previsto dal prompt finale.
  - **Soluzione:** Rimosso il campo da `src/models.py` e allineata la UI per mostrare solo `punti_di_forza`, `punti_da_migliorare`, `diario_di_bordo` e `saluto_conclusivo`.
- **Errore:** La generazione del riepilogo finale veniva eseguita prematuramente nel corso dei singoli moduli.
  - **Soluzione:** Aggiunta funzione `genera_riepilogo_finale()` in `src/generator.py` e nuovo endpoint `/api/final-summary` in `app.py`; la UI Streamlit e HTML ora richiedono il riepilogo solo dopo l’ultimo modulo.
- **Errore:** Possibile discrepanza Git locale/remote durante il push su GitHub.
  - **Soluzione:** Confermato che il commit locale è stato pushato con successo su `origin/main`; il problema locale potrebbe essere dovuto a line endings o branch non allineato.
- **Lezione appresa:** Quando si cambia un flusso architetturale, è necessario aggiornare in parallelo modello dati, logica backend e UI in tutte le interfacce.

---

## [24 Giugno 2026] - Recovery flow, RAG, storico persistente
- **Errore:** OpenRouter HTTP 404 — endpoint errato (`/v1/chat/completions` invece di `/api/v1/chat/completions`).
  - **Soluzione:** Corretto URL in `src/generator.py:17`.

- **Errore:** `valuta_risposta()` e `genera_spiegazione_alternativa()` chiamavano `json.loads()` direttamente senza normalizzare il testo, causando "impossibile processare la risposta JSON" quando l'LLM restituiva blocchi ```json.
  - **Soluzione:** Applicata `_normalize_json_text()` in tutte le funzioni di parsing (`generator.py:158,208,285,339`).

- **Errore:** `KeyError: 'spiegazione'` su moduli archiviati con struttura vecchia.
  - **Soluzione:** Migrazione automatica e `.get()` con fallback in `streamlit_app.py`.

- **Feature:** Sistema di hint e recovery flow su due tentativi con archiviazione modulo.
- **Feature:** Database SQLite persistente (`src/database.py`) con embedding via OpenRouter e RAG retrieval.
- **Feature:** Storico sessioni navigabile con moduli cliccabili e riesumibili.
- **Lezione appresa:** La normalizzazione JSON va applicata in tutti i punti di parsing, non solo in alcuni. Le modifiche ai campi dei dati salvati richiedono migrazioni retrocompatibili.

---

## [25 Giugno 2026] - Completamento migrazione Gemini → OpenRouter
- **Errore:** `NameError: name 'st' is not defined` in `streamlit_app.py`.
  - **Soluzione:** Ripristinato file da git (era stato corrotto durante edit). File originale contiene tutte le importazioni necessarie (`streamlit as st`, `src.generator`, `src.database`).
  - **Nota:** L'app richiede `src.database` che fornisce `get_all_sessions()`, `get_session_modules()`, `save_session()`, `get_module_attempts()`.

- **Status:** Migrazione da Gemini a OpenRouter completata.
  - `src/generator.py`: Tutte le funzioni ora usano `OPENROUTER_API_URL = "https://api.openrouter.ai/v1/chat/completions"`.
  - `requirements.txt`: Rimosso `google-generativeai`, mantenute dipendenze per OpenRouter (native con urllib).
  - `.env`: Aggiunto `OPENROUTER_API_KEY`, rimosso `GEMINI_API_KEY`.
  - `streamlit_app.py`: Recuperato e validato (integro).
  
- **Lezione appresa:** Quando si ripristina da git dopo edits corrotti, verificare che tutte le dipendenze siano importate correttamente e che il file abbia la struttura prevista.

---

## [26 Giugno 2026] - Refactoring storico, login multi-utente e UI cards
- **Errore:** La sezione storico utilizzava colonne affiancate con bottoni grandi, poco adatti alla sidebar.
  - **Soluzione:** Sostituiti con lista Markdown compatta + badge pills e piccolo pulsante ▶ per apertura.

- **Errore:** Il badge pill si sovrapponeva al pulsante ▶ in sidebar.
  - **Soluzione:** Badge spostato inline con il titolo nella stessa colonna, eliminata colonna separata.

- **Errore:** Dopo risposta corretta in modulo archiviato, l'utente veniva reindirizzato alla pagina iniziale (`modulo_archivio_aperto = None` + `rerun`).
  - **Soluzione:** Rimosso redirect. Ora l'utente resta sul modulo e vede "Risposta corretta!" come nel percorso attivo.

- **Errore:** La UI dei moduli archiviati era diversa da quella dei moduli attivi (mono-colonna, feedback non persistente).
  - **Soluzione:** Allineato layout a due colonne, feedback e hint ora persistenti in `session_state`.

- **Errore:** Streamlit si bloccava dopo il timeout del tool Bash.
  - **Soluzione:** Lanciato Streamlit come processo background detached con `Start-Process -WindowStyle Hidden`.

- **Feature:** Aggiunta autenticazione multi-utente (login/registrazione) per storico personale.
  - **Dettagli:** Tabella `users` in SQLite, password hashata con salt, filtro sessioni per `user_id`.

- **Feature:** Condivisione pubblica via ngrok con tunnel HTTPS.
  - **Dettagli:** Installato ngrok v3.39.8, autenticato con token, tunnel su porta 8501.

- **Feature:** Barra di avanzamento (gamification) sotto obiettivo di apprendimento.
- **Feature:** Effetto card con gradienti e bordi per colonne spiegazione/esercizio.
- **Feature:** Badge pills colorati per stato moduli (Fatto/Arch./Aperto).
- **Feature:** Syntax highlighting per blocchi di codice (```python```).
- **Feature:** Le risposte corrette dei moduli archiviati sono ora persistenti e ricaricate alla riapertura.

---

## [1 Luglio 2026] - Database, UI, Logo e Animazioni

### Bug Fix — psycopg2 compatibility
- **Errore:** `AttributeError: conn.execute()` su PostgreSQL (psycopg2 non supporta `execute()` direttamente sulla connessione).
  - **Soluzione:** Creato wrapper `_DB` in `database.py` che unifica l'interfaccia sqlite3/psycopg2 con metodo `.execute()`.
  - **Note:** Aggiunto try/except per import psycopg2 con fallback a SQLite se non installato.

### Bug Fix — create_user catch troppo ampio
- **Errore:** `except Exception` in `create_user()` trattava ogni errore come "Username già esistente".
  - **Soluzione:** Catch specifico per `UniqueViolation` (PG) e "UNIQUE constraint" (SQLite), log separato per altri errori.

### Bug Fix — find_similar_modules senza LIMIT
- **Errore:** `find_similar_modules()` fetchava tutte le righe senza LIMIT, O(n) scan.
  - **Soluzione:** Aggiunto `LIMIT 200` alla query SQL.

### Bug Fix — Loop infinito selectbox stato modulo
- **Errore:** Il dropdown stato modulo offriva solo "in sospeso" e "completato", ma i moduli potevano essere "archiviato". Il mismatch causava rerender infiniti.
  - **Soluzione:** Aggiunto "archiviato" come terza opzione, `update_module_state()` ora supporta `archived=True`.

### Bug Fix — Confirm dialog per azioni distruttive
- **Errore:** Delete sessione, delete modulo e logout senza conferma causavano perdita dati accidentale.
  - **Soluzione:** Convertiti in `st.popover` con pulsante di conferma esplicito.

### Bug Fix — Progress bar overflow e stringhe hardcodate
- **Errore:** Barra di avanzamento crashava se `completati > totali`; messaggio "terzo modulo" hardcodato.
  - **Soluzione:** `min(completati/totali, 1.0)` + stringa dinamica con conteggio moduli.

### Bug Fix — Migrazione archiviati eseguita a ogni page load
- **Errore:** Il blocco migrazione dati girava su ogni caricamento pagina.
  - **Soluzione:** Aggiunta guardia `_migrated_archiviati` in session_state.

### Bug Fix — Prompt system_mlpg.md JSON rotto
- **Errore:** Graffa extra nel template JSON mostrato al LLM.
  - **Soluzione:** Rimossa graffa duplicata, cancellato file vuoto `system_mlpg.md.txt`.

### Bug Fix — Filtro euristico bloccava codice Python
- **Errore:** `valida_input_euristico()` scambiava codice Python per spam (ratio caratteri unici < 0.3, keyword overlap zero).
  - **Soluzione:** Soglia alzata da 8 a 80 caratteri; keyword overlap saltato se rileva indicatori di codice (`def`, `print(`, `=`, `{`).

### Feature — Multi-pagina con st.navigation
- **Azione:** Convertita app single-page in multi-pagina con `st.navigation`.
  - **Dettagli:** Pagina "🏠 Nuovo Percorso" (principale) e "📚 I Miei Percorsi" (storico a schermo intero).
  - **Componente condiviso:** `_render_modulo_archivio()` usato da entrambe le pagine.

### Feature — Logo robot 8-bit con espressioni animate
- **Azione:** Creato logo pixel art stile retro (432x348, griglia 24px).
  - **Dettagli:** 3 espressioni (neutro 2x2 occhi, happy ^ ^, thinking 1px strizzato + bocca a sx) + versione animata con ciclo glitch+morph di 12s.
  - **Palette:** Blu oltremare #003F87, indaco #4B0082, azzurro #64B5F6, oro #FFD700, nero schermo #0A1628.

### Feature — Robot integrato nell'UI come indicatore di stato
- **Azione:** Robot visibile in login, welcome, sidebar, e sotto i pulsanti "Valuta soluzione" e "Chiedi chiarimenti".
  - **Dettagli:** State machine a due passi: click → thinking robot → valutazione API → happy/neutral.
  - **Modulo:** `src/robot_display.py` per helper riutilizzabile.

## [6 Luglio 2026] - Sicurezza: password in chiaro con SHA-256 + salt hardcoded
- **Errore:** `database.py` usava `hashlib.sha256()` con salt fisso `mlpg_salt_2026_xyz` per hashare le password. Il salt era uguale per tutti gli utenti e visibile nel codice sorgente.
- **Soluzione:** Sostituito con `bcrypt` (salt per-utente). Aggiunta backward compatibility: le password legacy SHA-256 vengono migrate automaticamente al primo login corretto.

## [6 Luglio 2026] - Flask debug=True in produzione
- **Errore:** `app.py:240` aveva `debug=True` hardcodato, esponendo la console Werkzeug e permettendo esecuzione arbitraria di codice.
- **Soluzione:** Sostituito con `FLASK_DEBUG` env var, default `False`.

## [6 Luglio 2026] - ImportError: valuta_con_pipeline non trovata
- **Errore:** Streamlit non trovava `valuta_con_pipeline` in `src/generator.py` nonostante fosse presente nel file. I test da CLI funzionavano.
- **Causa:** Cache `.pyc` stantia nel venv + processo Streamlit che teneva in memoria il modulo vecchio.
- **Soluzione:** Pulizia completa `__pycache__`, kill processo, `-B` flag per evitare scrittura .pyc. Non ha funzionato finché non sono stati killati TUTTI i processi python residui.

## [6 Luglio 2026] - PostgreSQL: DATE('now', '-7 days') non esiste
- **Errore:** `get_user_weekly_activity()` usava la sintassi SQLite `DATE('now', '-7 days')` che PostgreSQL non supporta.
- **Soluzione:** Calcolata la data in Python con `datetime.timedelta` e passata come parametro, compatibile con entrambi i backend.

## [6 Luglio 2026] - PostgreSQL: colonna created_at ambigua
- **Errore:** La query `get_user_weekly_activity()` aveva `DATE(created_at)` senza qualificatore di tabella, ambiguo tra `attempts.created_at` e `sessions.created_at`.
- **Soluzione:** Aggiunto prefisso tabella: `DATE(a.created_at)`.

## [6 Luglio 2026] - Pulizia file inutilizzati
- **Errore:** Cartella `logos/` conteneva 35 SVG, di cui solo 4 usati dal codice. Le 31 varianti scartate occupavano ~200 KB.
- **Soluzione:** Eliminati 31 SVG inutilizzati + 4 HTML preview + tutte le cache. Tenuti solo i 4 SVG referenziati da `robot_display.py`.

## [6 Luglio 2026] - Stringhe hardcodate in italiano dopo i18n
- **Errore:** Nonostante il sistema i18n, lo status dropdown ("in sospeso"/"completato"/"archiviato"), il titolo app ("MLPG Tutor con Streamlit"), il language selector ("Italiano") e i diario note erano ancora hardcodati in italiano.
- **Soluzione:** Status dropdown rifattorizzato a indici con `format_func` tradotto. Tutte le stringhe rimanenti wrappate in `tr()`.

## [6 Luglio 2026] - Persistenza sessione al refresh
- **Errore:** Fare F5 riportava alla pagina di login perché `st.session_state` non sopravvive al refresh del browser.
- **Soluzione:** Implementato session token firmato (SHA-256) salvato in `st.query_params`. Al refresh, il token viene verificato e l'utente auto-autenticato.

## [7 Luglio 2026] - Nuovi badge, profilo utente e logo

**Nuovi badge (9):** Aggiunti badge Centenario, Poliglotta, Enciclopedico, Collezionista, Saggio, Nottambulo, Fenice, Fulmine, Modulo Perfetto.
- **DB:** Nuove colonne `langs_used`, `night_sessions`, `perfect_modules`, `phoenix_earned`, `avatar`, `theme_color`, `featured_badges` in `user_stats`.
- **Nota:** `update_streak` ora restituisce 3 valori `(streak, max_streak, is_phoenix)` — aggiornati tutti i chiamanti.

**Badge SVG (doppio anello):** Sostituite emoji con SVG generati via `badge_svg()` in `gamification.py`.
- 5 categorie colore: moduli (verde), precisione (blu), streak (arancione), livelli (viola), traguardi (oro).
- Counter globale `_svg_counter` per evitare conflitti ID gradiente in pagina.

**Galleria badge:** Tab "Galleria Badge" in Obiettivi con tutti i badge (sbloccati/bloccati) in griglia 4x4.

**Profilo utente:** Sistema di personalizzazione profilo con avatar (16 emoji), colore tema (8 colori), badge in vetrina (max 3).
- Mini-card compatta nella sidebar con avatar, nome, livello e badge SVG.
- Pagina profilo pubblico accessibile cliccando username nella classifica.
- **Errore:** Avatar non persisteva dopo click — i bottoni usavano variabili locali perse al rerun.
- **Soluzione:** Spostata selezione avatar/colore in `st.session_state` (`profile_avatar`, `profile_theme`, `profile_featured`).

**Logo MLPG (work in progress):** Logo SVG generato via Claude, cartuccia SNES + robot + glow.
- **Errore:** Logo non visibile in sidebar con `st.markdown` (codice SVG visualizzato come testo) e `st.image()` (immagine rotta).
- **Soluzione:** Rimosso temporaneamente dalla sidebar. Il file `logos/mlpg_logo.svg` è salvato per perfezionamento futuro.
