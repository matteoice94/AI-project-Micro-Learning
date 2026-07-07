"""
Modulo centralizzato per internazionalizzazione (IT / EN).
Tutti i testi utente dell'applicazione passano attraverso `tr(key, lang)`.
"""

TRANSLATIONS = {
    # ── Generali ──────────────────────────────────────────
    "save": {"it": "Salva", "en": "Save"},
    "cancel": {"it": "Annulla", "en": "Cancel"},
    "confirm": {"it": "Conferma", "en": "Confirm"},
    "delete": {"it": "Elimina", "en": "Delete"},
    "rename": {"it": "Rinomina", "en": "Rename"},
    "new": {"it": "Nuovo", "en": "New"},
    "back": {"it": "Torna", "en": "Back"},
    "next": {"it": "Successivo", "en": "Next"},
    "logout": {"it": "Esci", "en": "Logout"},
    "level": {"it": "Livello", "en": "Level"},
    "base": {"it": "base", "en": "basic"},
    "intermediate": {"it": "intermedio", "en": "intermediate"},
    "advanced": {"it": "avanzato", "en": "advanced"},
    "name": {"it": "Nome", "en": "Name"},
    "name_optional": {"it": "Nome (opzionale)", "en": "Name (optional)"},
    "confirm_delete": {"it": "Conferma eliminazione", "en": "Confirm deletion"},

    # ── Login / Registrazione ────────────────────────────
    "login_title": {"it": "Accedi o Registrati", "en": "Login or Register"},
    "login_tab": {"it": "Accedi", "en": "Login"},
    "register_tab": {"it": "Registrati", "en": "Register"},
    "username": {"it": "Username", "en": "Username"},
    "password": {"it": "Password", "en": "Password"},
    "confirm_password": {"it": "Conferma password", "en": "Confirm password"},
    "fill_all_fields": {"it": "Compila tutti i campi", "en": "Please fill in all fields"},
    "passwords_mismatch": {"it": "Le password non coincidono", "en": "Passwords do not match"},
    "password_too_short": {"it": "Password troppo corta (min 4 caratteri)", "en": "Password too short (min 4 characters)"},
    "username_exists": {"it": "Username già esistente", "en": "Username already exists"},
    "wrong_credentials": {"it": "Username o password errati", "en": "Username or password incorrect"},
    "really_logout": {"it": "Vuoi davvero uscire?", "en": "Do you really want to log out?"},
    "forgot_password": {"it": "Password dimenticata?", "en": "Forgot password?"},
    "forgot_password_title": {"it": "Recupera Password", "en": "Recover Password"},
    "forgot_password_desc": {"it": "Inserisci il tuo username per ricevere un token di reset.", "en": "Enter your username to receive a reset token."},
    "send_reset_token": {"it": "Genera Token", "en": "Generate Token"},
    "user_not_found": {"it": "Username non trovato", "en": "Username not found"},
    "reset_token_created": {"it": "Token generato. Usalo per reimpostare la password.", "en": "Token generated. Use it to reset your password."},
    "reset_token_label": {"it": "Token di Reset", "en": "Reset Token"},
    "reset_password_title": {"it": "Reimposta Password", "en": "Reset Password"},
    "reset_password_desc": {"it": "Inserisci il token ricevuto e la nuova password.", "en": "Enter the received token and your new password."},
    "new_password": {"it": "Nuova Password", "en": "New Password"},
    "reset_password_btn": {"it": "Reimposta Password", "en": "Reset Password"},
    "reset_success": {"it": "Password reimpostata con successo!", "en": "Password reset successfully!"},
    "reset_invalid_token": {"it": "Token non valido o scaduto", "en": "Invalid or expired token"},

    # ── Page Titles ───────────────────────────────────────
    "page_title": {"it": "MLPG Tutor Streamlit", "en": "MLPG Tutor Streamlit"},
    "new_path_page": {"it": "Nuovo Percorso", "en": "New Path"},
    "history_page": {"it": "I Miei Percorsi", "en": "My Paths"},
    "prev_page": {"it": "Precedente", "en": "Previous"},
    "next_page": {"it": "Successiva", "en": "Next"},
    "page_n": {"it": "Pagina {n}", "en": "Page {n}"},
    "path_description": {
        "it": "Genera un percorso personalizzato, valuta le tue soluzioni e chiedi chiarimenti mirati.",
        "en": "Generate a personalized path, evaluate your solutions, and ask targeted clarifications.",
    },
    "history_description": {
        "it": "Gestisci i tuoi percorsi di apprendimento passati. Rinomina, elimina o riapri i moduli archiviati.",
        "en": "Manage your past learning paths. Rename, delete, or reopen archived modules.",
    },

    # ── Sidebar ───────────────────────────────────────────
    "sidebar_config": {"it": "Configurazione", "en": "Configuration"},
    "sidebar_topic": {"it": "Argomento", "en": "Topic"},
    "sidebar_topic_placeholder": {
        "it": "Es: Python, Matematica, etc.",
        "en": "Eg: Python, Mathematics, etc.",
    },
    "sidebar_level": {"it": "Livello", "en": "Level"},
    "sidebar_modules_count": {"it": "Numero di moduli", "en": "Number of Modules"},
    "sidebar_name_placeholder": {"it": "Il tuo nome", "en": "Your name"},
    "sidebar_generate": {"it": "Genera percorso", "en": "Generate path"},
    "sidebar_new": {"it": "Nuovo", "en": "New"},
    "sidebar_archived": {"it": "Moduli da Riprendere", "en": "Modules to Retake"},
    "topic_level_required": {
        "it": "Argomento e livello sono obbligatori.",
        "en": "Topic and level are required.",
    },
    "path_generated": {
        "it": "Percorso generato e salvato!",
        "en": "Path generated and saved!",
    },
    "generating_spinner": {
        "it": "Generazione percorso in corso...",
        "en": "Generating path...",
    },
    "translating_modules": {
        "it": "Traduzione moduli in corso...",
        "en": "Translating modules...",
    },

    # ── Welcome Page ──────────────────────────────────────
    "welcome_message": {
        "it": "Benvenuto! Inizia generando un nuovo percorso dalla barra laterale.",
        "en": "Welcome! Start by generating a new path from the sidebar.",
    },
    "how_to_start": {"it": "Come iniziare", "en": "How to Start"},
    "how_to_start_1": {"it": "Scegli un **argomento**", "en": "Choose a **topic**"},
    "how_to_start_2": {"it": "Seleziona il tuo **livello**", "en": "Select your **level**"},
    "how_to_start_3": {"it": "Clicca **Genera percorso**", "en": "Click **Generate path**"},
    "how_it_works": {"it": "Come funziona", "en": "How It Works"},
    "how_it_works_1": {"it": "Ricevi **3 moduli** su misura", "en": "Get **3 tailored modules**"},
    "how_it_works_2": {"it": "Risolvi gli **esercizi pratici**", "en": "Solve **practical exercises**"},
    "how_it_works_3": {"it": "Chiedi **chiarimenti mirati**", "en": "Ask **targeted clarifications**"},
    "tips": {"it": "Suggerimenti", "en": "Tips"},
    "tip_1": {
        "it": "Se non capisci: usa **Chiedi chiarimenti**",
        "en": "If you don't understand: use **Ask for clarifications**",
    },
    "tip_2": {"it": "Se sbagli 2 volte: il modulo si **archivia**", "en": "If you're wrong twice: the module gets **archived**"},
    "tip_3": {"it": "Potrai **riprovare** dalla sidebar", "en": "You can **retry** from the sidebar"},

    # ── Active Path ───────────────────────────────────────
    "learning_objective": {"it": "Obiettivo di apprendimento", "en": "Learning Objective"},
    "modules_completed": {"it": "moduli completati", "en": "modules completed"},
    "select_module": {"it": "Seleziona modulo", "en": "Select module"},
    "module_n": {"it": "Modulo", "en": "Module"},
    "explanation": {"it": "Spiegazione", "en": "Explanation"},
    "exercise": {"it": "Esercizio", "en": "Exercise"},
    "your_solution": {"it": "La tua soluzione", "en": "Your solution"},
    "evaluate_solution": {"it": "Valuta soluzione", "en": "Evaluate solution"},
    "insert_solution_first": {
        "it": "Inserisci una soluzione prima di valutare.",
        "en": "Enter a solution before evaluating.",
    },
    "correct_answer": {"it": "Risposta corretta!", "en": "Correct answer!"},
    "not_pertinent": {
        "it": "La tua risposta non sembra pertinente all'esercizio",
        "en": "Your answer does not seem relevant to the exercise",
    },
    "retry_focused": {
        "it": "Riprova con una risposta più mirata.",
        "en": "Try again with a more focused answer.",
    },
    "same_answer_warning": {
        "it": "Hai inviato la stessa risposta. Rileggi l'hint qui sotto e riprova con un approccio diverso.",
        "en": "You submitted the same answer. Re-read the hint below and try a different approach.",
    },
    "constructive_comment": {"it": "Commento costruttivo", "en": "Constructive Comment"},
    "improvement_suggestion": {
        "it": "Suggerimento di miglioramento",
        "en": "Improvement Suggestion",
    },
    "hint_label": {"it": "Suggerimento", "en": "Hint"},
    "already_attempted": {
        "it": "Hai già tentato questo modulo in precedenza. Puoi riprovare qui sotto.",
        "en": "You have already attempted this module. You can retry below.",
    },
    "module_archived_after": {
        "it": "Modulo archiviato dopo {count} tentativi. Potrai riprovare dalla sezione 'Moduli da Riprendere'.",
        "en": "Module archived after {count} attempts. You can retry from the 'Modules to Retake' section.",
    },

    # ── Clarifications ────────────────────────────────────
    "ask_clarification": {"it": "Chiedi chiarimenti mirati", "en": "Ask Targeted Clarifications"},
    "which_part_unclear": {
        "it": "Quale parte non ti è chiara?",
        "en": "Which part is unclear to you?",
    },
    "generate_targeted_explanation": {
        "it": "Genera spiegazione mirata",
        "en": "Generate targeted explanation",
    },
    "enter_doubt_first": {
        "it": "Inserisci il dubbio specifico prima di procedere.",
        "en": "Enter the specific doubt before proceeding.",
    },
    "simplified_explanation": {
        "it": "Spiegazione semplificata",
        "en": "Simplified Explanation",
    },
    "practical_example": {"it": "Esempio pratico", "en": "Practical Example"},
    "suggested_steps": {"it": "Passaggi consigliati", "en": "Suggested Steps"},
    "evaluating_spinner": {
        "it": "Valutazione in corso...",
        "en": "Evaluating...",
    },
    "clarification_spinner": {
        "it": "Generazione spiegazione...",
        "en": "Generating explanation...",
    },

    # ── Final Summary ─────────────────────────────────────
    "final_summary": {"it": "Riepilogo Finale", "en": "Final Summary"},
    "generate_final_summary": {
        "it": "Genera riepilogo finale",
        "en": "Generate Final Summary",
    },
    "insert_at_least_one_solution": {
        "it": "Inserisci almeno una soluzione ai moduli prima di generare il riepilogo finale.",
        "en": "Enter at least one solution before generating the final summary.",
    },
    "final_results": {"it": "Risultati Finali", "en": "Final Results"},
    "strengths": {"it": "Punti di forza", "en": "Strengths"},
    "improvements": {"it": "Punti da migliorare", "en": "Areas for Improvement"},
    "logbook": {"it": "Diario di bordo", "en": "Logbook"},
    "farewell": {"it": "Saluto conclusivo", "en": "Farewell"},
    "no_strengths": {"it": "Nessun punto di forza disponibile.", "en": "No strengths available."},
    "no_improvements": {
        "it": "Nessun punto da migliorare disponibile.",
        "en": "No improvement points available.",
    },
    "no_notes": {"it": "Nessuna nota disponibile.", "en": "No notes available."},
    "no_greeting": {"it": "Nessun saluto disponibile.", "en": "No greeting available."},
    "summary_generated": {
        "it": "Riepilogo finale generato con successo.",
        "en": "Final summary generated successfully.",
    },
    "summary_generating": {
        "it": "Generazione riepilogo...",
        "en": "Generating summary...",
    },
    "summary_hint": {
        "it": "Genera il riepilogo finale quando hai completato tutti i {count} moduli.",
        "en": "Generate the final summary when you have completed all {count} modules.",
    },
    "summary_later": {
        "it": "Il riepilogo finale sarà disponibile alla conclusione dell'ultimo modulo.",
        "en": "The final summary will be available at the end of the last module.",
    },
    "starting_level": {"it": "Livello di partenza", "en": "Starting Level"},

    # ── Status ────────────────────────────────────────────
    "completed": {"it": "Completato", "en": "Completed"},
    "archived": {"it": "Archiviato", "en": "Archived"},
    "pending": {"it": "In sospeso", "en": "Pending"},
    "in_progress": {"it": "In corso", "en": "In Progress"},
    "to_retake": {"it": "Da riprendere", "en": "To Retake"},
    "already_completed": {
        "it": "Modulo già completato — ecco la tua risposta",
        "en": "Module already completed — here is your answer",
    },

    # ── History Page ──────────────────────────────────────
    "no_sessions": {
        "it": "Ancora nessun percorso salvato. Torna alla pagina **Nuovo Percorso** per crearne uno!",
        "en": "No saved paths yet. Go back to **New Path** to create one!",
    },
    "no_archived_modules": {
        "it": "Nessun modulo archiviato.",
        "en": "No archived modules.",
    },
    "created_on": {"it": "Creato il", "en": "Created on"},
    "new_name": {"it": "Nuovo nome", "en": "New name"},
    "delete_session_warning": {
        "it": "Eliminare l'intera sessione? Tutti i moduli e tentativi andranno persi.",
        "en": "Delete the entire session? All modules and attempts will be lost.",
    },
    "delete_module_warning": {
        "it": "Eliminare questo modulo? I tentativi associati andranno persi.",
        "en": "Delete this module? Associated attempts will be lost.",
    },
    "modules_label": {"it": "Moduli", "en": "Modules"},
    "select_module_label": {"it": "Seleziona modulo", "en": "Select module"},
    "state": {"it": "Stato", "en": "Status"},
    "rename_module_label": {"it": "Rinomina modulo", "en": "Rename module"},
    "delete_module_label": {"it": "Elimina modulo", "en": "Delete module"},
    "title": {"it": "Titolo", "en": "Title"},
    "attempts_label": {"it": "Tentativi", "en": "Attempts"},
    "manage_modules": {"it": "Gestione Moduli", "en": "Module Management"},
    "open_module": {"it": "Apri modulo", "en": "Open module"},
    "loading": {"it": "Caricamento...", "en": "Loading..."},
    "no_past_sessions": {
        "it": "Nessuna sessione passata.",
        "en": "No past sessions.",
    },

    # ── Error Messages ────────────────────────────────────
    "eval_error": {"it": "Errore nella valutazione", "en": "Evaluation error"},
    "clarify_error": {
        "it": "Errore nella generazione dei chiarimenti",
        "en": "Error generating clarifications",
    },
    "summary_error": {
        "it": "Errore nella generazione del riepilogo finale",
        "en": "Error generating final summary",
    },
    "generation_error": {
        "it": "Errore durante la generazione",
        "en": "Error during generation",
    },
    "connection_error": {
        "it": "Errore di connessione. Riprova.",
        "en": "Connection error. Try again.",
    },
    "generation_error_label": {
        "it": "Errore nella generazione.",
        "en": "Generation error.",
    },
    "invalid_json_response": {
        "it": "Risposta non valida: il JSON generato non corrisponde al formato TutorResponse.",
        "en": "Invalid response: the generated JSON does not match the TutorResponse format.",
    },
    "eval_parse_error": {
        "it": "Errore nella valutazione: impossibile processare la risposta JSON.",
        "en": "Evaluation error: unable to process the JSON response.",
    },
    "empty_history": {
        "it": "Lo storico delle risposte è vuoto. Impossibile generare il riepilogo finale.",
        "en": "Response history is empty. Cannot generate the final summary.",
    },
    "clarification_parse_error": {
        "it": "Errore nella generazione della spiegazione semplificata: risposta non valida.",
        "en": "Error generating simplified explanation: invalid response.",
    },

    # ── Flask API errors ──────────────────────────────────
    "api_topic_level": {
        "it": "Topic e livello sono obbligatori.",
        "en": "Topic and level are required.",
    },
    "api_exercise_solution": {
        "it": "Esercizio e soluzione sono obbligatori.",
        "en": "Exercise and solution are required.",
    },
    "api_exercise_solution_level": {
        "it": "Esercizio, soluzione e livello sono obbligatori.",
        "en": "Exercise, solution and level are required.",
    },
    "api_topic_explanation_doubt_level": {
        "it": "Argomento, spiegazione, dubbio e livello sono obbligatori.",
        "en": "Topic, explanation, doubt and level are required.",
    },
    "api_solutions_level": {
        "it": "Soluzioni e livello sono obbligatori.",
        "en": "Solutions and level are required.",
    },
    "api_level_required": {
        "it": "Il livello è obbligatorio.",
        "en": "Level is required.",
    },
    "api_module_db_id": {
        "it": "module_db_id obbligatorio.",
        "en": "module_db_id required.",
    },
    "api_session_id": {
        "it": "session_id obbligatorio.",
        "en": "session_id required.",
    },
    "api_not_pertinent": {
        "it": "La risposta non sembra pertinente all'esercizio",
        "en": "The answer does not seem relevant to the exercise",
    },

    # ── Heuristic Filter ──────────────────────────────────
    "heuristic_too_short": {
        "it": "La risposta è troppo corta. Prova a scrivere una soluzione più articolata.",
        "en": "The answer is too short. Try writing a more detailed solution.",
    },
    "heuristic_encouragement": {
        "it": "Non preoccuparti se non sai la risposta! Usa il pulsante 'Chiedi chiarimenti' per ricevere un aiuto mirato. Sono qui per supportarti!",
        "en": "Don't worry if you don't know the answer! Use the 'Ask for clarifications' button to get targeted help. I'm here to support you!",
    },
    "heuristic_repeated_words": {
        "it": "La risposta contiene parole ripetute. Prova a formulare una soluzione più strutturata.",
        "en": "The answer contains repeated words. Try to formulate a more structured solution.",
    },
    "heuristic_random_chars": {
        "it": "La risposta sembra composta da caratteri casuali. Riprova con parole di senso compiuto.",
        "en": "The answer appears to be random characters. Try again with meaningful words.",
    },
    "heuristic_too_short_eval": {
        "it": "La risposta è troppo breve per essere valutata. Prova a elaborare di più.",
        "en": "The answer is too short to be evaluated. Try to elaborate more.",
    },
    "heuristic_irrelevant": {
        "it": "La risposta non sembra pertinente all'esercizio. Prova a leggere meglio la domanda e rispondere in modo mirato.",
        "en": "The answer does not seem relevant to the exercise. Try reading the question more carefully and responding in a targeted way.",
    },

    # ── Fallback Hints ────────────────────────────────────
    "fallback_hint_1": {
        "it": "Riprova! Rileggi attentamente la spiegazione del modulo e concentrati sui concetti chiave. Se serve, chiedi un chiarimento qui sotto.",
        "en": "Try again! Carefully re-read the module explanation and focus on key concepts. If needed, ask for clarification below.",
    },
    "fallback_hint_2": {
        "it": "Non preoccuparti, succede! Prova a scomporre il problema in passaggi più piccoli. Usa la sezione 'Chiedi chiarimenti mirati' se un concetto non ti è chiaro.",
        "en": "Don't worry, it happens! Try breaking the problem down into smaller steps. Use the 'Ask Targeted Clarifications' section if a concept is unclear.",
    },
    "fallback_hint_generic": {
        "it": "Rileggi la spiegazione e prova con un approccio diverso.",
        "en": "Re-read the explanation and try a different approach.",
    },

    # ── Generator Error Messages ─────────────────────────
    "gen_api_key_not_found": {
        "it": "OPENROUTER_API_KEY non trovata. Assicurati che sia definita nel file .env.",
        "en": "OPENROUTER_API_KEY not found. Make sure it is defined in the .env file.",
    },
    "gen_no_choices": {
        "it": "OpenRouter response non valida: nessuna scelta trovata.",
        "en": "Invalid OpenRouter response: no choices found.",
    },
    "gen_no_content": {
        "it": "OpenRouter response non valida: contenuto testo mancante.",
        "en": "Invalid OpenRouter response: text content missing.",
    },
    "gen_network_error": {
        "it": "Errore di rete OpenRouter",
        "en": "OpenRouter network error",
    },
    "embed_api_key_not_found": {
        "it": "OPENROUTER_API_KEY non trovata per embeddings.",
        "en": "OPENROUTER_API_KEY not found for embeddings.",
    },
    "embed_invalid_response": {
        "it": "Risposta embedding non valida.",
        "en": "Invalid embedding response.",
    },

    # ── DB errors ─────────────────────────────────────────
    "db_user_create_error": {
        "it": "Errore creazione utente",
        "en": "Error creating user",
    },

    # ── CLI ───────────────────────────────────────────────
    "cli_header": {
        "it": "=== MLPG Tutor: Generazione Percorso Microlearning ===",
        "en": "=== MLPG Tutor: Microlearning Path Generator ===",
    },
    "cli_topic_prompt": {
        "it": "Inserisci l'argomento da studiare:",
        "en": "Enter the topic to study:",
    },
    "cli_level_prompt": {
        "it": "Inserisci il livello (base, intermedio, avanzato):",
        "en": "Enter the level (basic, intermediate, advanced):",
    },
    "cli_topic_level_error": {
        "it": "Errore: argomento e livello sono obbligatori.",
        "en": "Error: topic and level are required.",
    },
    "cli_objective": {"it": "Obiettivo", "en": "Objective"},
    "cli_solution_prompt": {
        "it": "Scrivi la tua soluzione (o premi Invio per saltare):",
        "en": "Write your solution (or press Enter to skip):",
    },
    "cli_empty_solution": {
        "it": "Soluzione vuota. Passaggio al prossimo modulo.",
        "en": "Empty solution. Moving to the next module.",
    },
    "cli_same_answer": {
        "it": "Hai inviato la stessa risposta. Rileggi l'hint qui sotto.",
        "en": "You submitted the same answer. Re-read the hint below.",
    },
    "cli_verifying": {
        "it": "Verifica pertinenza della risposta...",
        "en": "Checking answer relevance...",
    },
    "cli_module_archived": {
        "it": "Modulo archiviato per una prossima sessione. Passiamo avanti.",
        "en": "Module archived for a future session. Moving on.",
    },
    "cli_understood": {
        "it": "Hai capito meglio ora? (sì/no, default sì):",
        "en": "Do you understand better now? (yes/no, default yes):",
    },
    "cli_what_unclear": {
        "it": "Quale parte non ti è chiara?",
        "en": "Which part is unclear?",
    },
    "cli_clarify_error": {
        "it": "Errore chiarimento",
        "en": "Clarification error",
    },
    "cli_final_summary_header": {"it": "RIEPILOGO FINALE", "en": "FINAL SUMMARY"},
    "cli_summary_level": {"it": "Livello", "en": "Level"},
    "cli_strengths": {"it": "Punti di forza", "en": "Strengths"},
    "cli_improvements": {"it": "Punti da migliorare", "en": "Areas for Improvement"},
    "cli_logbook": {"it": "Diario di bordo", "en": "Logbook"},
    "cli_farewell": {"it": "Saluto", "en": "Farewell"},
    "cli_summary_error": {"it": "Errore riepilogo finale", "en": "Final summary error"},

    # ── HTML Interface ────────────────────────────────────
    "html_page_title": {"it": "MLPG Tutor Web", "en": "MLPG Tutor Web"},
    "html_main_heading": {"it": "MLPG Tutor Web", "en": "MLPG Tutor Web"},
    "html_main_description": {
        "it": "Genera il percorso, rispondi agli esercizi e ricevi feedback, suggerimenti e chiarimenti mirati.",
        "en": "Generate a path, answer exercises, and receive feedback, hints and targeted clarifications.",
    },
    "html_topic_label": {"it": "Argomento", "en": "Topic"},
    "html_topic_placeholder": {
        "it": "Esempio: programmazione Python",
        "en": "Example: Python programming",
    },
    "html_level_label": {"it": "Livello", "en": "Level"},
    "html_level_select": {"it": "Seleziona...", "en": "Select..."},
    "html_name_label": {"it": "Nome (opzionale)", "en": "Name (optional)"},
    "html_name_placeholder": {"it": "Es. Matteo", "en": "Eg. John"},
    "html_generate_btn": {"it": "Genera percorso", "en": "Generate path"},
    "html_archived_sidebar": {"it": "Moduli da riprendere", "en": "Modules to Retake"},
    "html_history_sidebar": {"it": "Storico sessioni", "en": "Session History"},
    "html_summary_title": {"it": "Riepilogo sessione", "en": "Session Summary"},
    "html_summary_generate_btn": {
        "it": "Genera riepilogo finale",
        "en": "Generate final summary",
    },
    "html_learning_objective": {
        "it": "Obiettivo di apprendimento",
        "en": "Learning Objective",
    },
    "html_level_badge": {"it": "Livello", "en": "Level"},
    "html_completed_badge": {"it": "Completato", "en": "Completed"},
    "html_in_progress_badge": {"it": "In corso", "en": "In Progress"},
    "html_archived_badge": {"it": "Archiviato", "en": "Archived"},
    "html_retake_badge": {"it": "Da riprendere", "en": "To Retake"},
    "html_explanation_label": {"it": "Spiegazione", "en": "Explanation"},
    "html_exercise_label": {"it": "Esercizio", "en": "Exercise"},
    "html_solution_label": {"it": "La tua soluzione", "en": "Your solution"},
    "html_solution_placeholder": {
        "it": "Inserisci qui la tua risposta...",
        "en": "Enter your answer here...",
    },
    "html_retry_placeholder": {
        "it": "Riprova a risolvere l'esercizio...",
        "en": "Try solving the exercise again...",
    },
    "html_eval_btn": {"it": "Valuta soluzione", "en": "Evaluate solution"},
    "html_clarify_btn": {"it": "Chiedi chiarimenti", "en": "Ask for clarifications"},
    "html_prev_module": {"it": "Modulo precedente", "en": "Previous module"},
    "html_next_module": {"it": "Modulo successivo", "en": "Next module"},
    "html_close_archive": {
        "it": "Chiudi vista archivio",
        "en": "Close archive view",
    },
    "html_clarify_targeted": {
        "it": "Genera spiegazione mirata",
        "en": "Generate targeted explanation",
    },
    "html_doubt_placeholder": {
        "it": "Esempio: non capisco il ciclo for",
        "en": "Example: I don't understand for loops",
    },
    "html_doubt_label": {"it": "Qual è il dubbio specifico?", "en": "What is your specific doubt?"},
    "html_insert_solution": {
        "it": "Inserisci una soluzione prima di valutare.",
        "en": "Enter a solution before evaluating.",
    },
    "html_insert_doubt": {
        "it": "Descrivi il dubbio specifico prima di chiedere chiarimenti.",
        "en": "Describe the specific doubt before asking for clarifications.",
    },
    "html_topic_level_error": {
        "it": "Argomento e livello sono obbligatori.",
        "en": "Topic and level are required.",
    },
    "html_archived_msg": {
        "it": "Questo modulo è stato archiviato. Puoi riprenderlo dalla sidebar \"Moduli da riprendere\".",
        "en": "This module has been archived. You can retake it from the \"Modules to Retake\" sidebar.",
    },
    "html_archived_after": {
        "it": "Questo modulo è stato archiviato. Potrai riprenderlo in un secondo momento dalla sidebar \"Moduli da riprendere\".",
        "en": "This module has been archived. You can retake it later from the \"Modules to Retake\" sidebar.",
    },
    "html_same_answer_msg": {
        "it": "Hai inviato la stessa risposta. Rileggi il suggerimento sopra e prova con un approccio diverso.",
        "en": "You submitted the same answer. Re-read the hint above and try a different approach.",
    },
    "html_wrong_status": {"it": "Sbagliata", "en": "Wrong"},
    "html_partial_status": {"it": "Parziale", "en": "Partial"},
    "html_correct_status": {"it": "Corretta!", "en": "Correct!"},
    "html_comment_label": {"it": "Commento", "en": "Comment"},
    "html_suggestion_label": {"it": "Suggerimento", "en": "Suggestion"},
    "html_hint_prefix": {
        "it": "Suggerimento (tentativo {count}/2)",
        "en": "Hint (attempt {count}/2)",
    },
    "html_hint_simple": {"it": "Suggerimento", "en": "Hint"},
    "html_summary_strengths": {"it": "Punti di forza", "en": "Strengths"},
    "html_summary_improvements": {
        "it": "Punti da migliorare",
        "en": "Areas for Improvement",
    },
    "html_summary_logbook": {"it": "Diario di bordo", "en": "Logbook"},
    "html_summary_farewell": {"it": "Saluto conclusivo", "en": "Farewell"},
    "html_no_strengths": {
        "it": "Nessun punto di forza disponibile.",
        "en": "No strengths available.",
    },
    "html_no_improvements": {
        "it": "Nessun punto da migliorare disponibile.",
        "en": "No improvement points available.",
    },
    "html_no_notes": {"it": "Nessuna nota disponibile.", "en": "No notes available."},
    "html_no_greeting": {
        "it": "Nessun saluto disponibile.",
        "en": "No greeting available.",
    },
    "html_archived_list_empty": {
        "it": "Nessun modulo archiviato.",
        "en": "No archived modules.",
    },
    "html_insert_at_least_one": {
        "it": "Inserisci almeno una soluzione prima di generare il riepilogo finale.",
        "en": "Enter at least one solution before generating the final summary.",
    },
    "html_eval_error": {
        "it": "Errore nella valutazione.",
        "en": "Evaluation error.",
    },
    "html_clarify_targeted_label": {
        "it": "Spiegazione mirata",
        "en": "Targeted Explanation",
    },
    "html_explanation_text": {"it": "Spiegazione", "en": "Explanation"},
    "html_practical_example": {"it": "Esempio pratico", "en": "Practical Example"},
    "html_suggested_steps": {
        "it": "Passaggi consigliati",
        "en": "Suggested Steps",
    },
    "html_connection_eval_error": {
        "it": "Errore di connessione durante la valutazione.",
        "en": "Connection error during evaluation.",
    },
    "html_connection_error": {
        "it": "Errore di connessione.",
        "en": "Connection error.",
    },
    "html_level_status": {"it": "Livello", "en": "Level"},
    "html_progress": {"it": "Progresso", "en": "Progress"},
    "html_completed_count": {"it": "completati", "en": "completed"},
    "html_archived_count": {"it": "Archiviati", "en": "Archived"},
    "html_collected_comments": {"it": "Commenti raccolti", "en": "Collected Comments"},
    "html_diary_label": {"it": "Diario di bordo", "en": "Logbook"},
    "html_no_difficulties": {
        "it": "Nessuna difficoltà specifica registrata.",
        "en": "No specific difficulties recorded.",
    },
    "html_modules_list": {
        "it": "Moduli totali",
        "en": "Total modules",
    },
    "html_current_module": {"it": "Modulo attuale", "en": "Current module"},
    "html_error_label": {"it": "Errore", "en": "Error"},
    "html_base": {"it": "Base", "en": "Basic"},
    "html_intermediate": {"it": "Intermedio", "en": "Intermediate"},
    "html_advanced": {"it": "Avanzato", "en": "Advanced"},
    "lang_label": {"it": "Lingua / Language:", "en": "Language:"},
    "app_main_title": {"it": "MLPG Tutor con Streamlit", "en": "MLPG Tutor with Streamlit"},
    "lang_italiano": {"it": "Italiano", "en": "Italian"},
    "lang_english": {"it": "English", "en": "English"},
    "diary_module_prefix": {"it": "Modulo", "en": "Module"},
    "diary_archived_after": {"it": "archiviato dopo {count} tentativi", "en": "archived after {count} attempts"},

    # ── Gamification ────────────────────────────────────────
    "achievements_page": {"it": "Obiettivi", "en": "Achievements"},
    "dashboard_page": {"it": "Dashboard", "en": "Dashboard"},
    "your_level": {"it": "Livello", "en": "Level"},
    "xp_progress": {"it": "Progresso XP", "en": "XP Progress"},
    "current_streak": {"it": "Streak attuale", "en": "Current Streak"},
    "days": {"it": "giorni", "en": "days"},
    "total_correct_stat": {"it": "Risposte corrette", "en": "Correct Answers"},
    "total_wrong_stat": {"it": "Risposte sbagliate", "en": "Wrong Answers"},
    "accuracy_stat": {"it": "Precisione", "en": "Accuracy"},
    "modules_completed_stat": {"it": "Moduli completati", "en": "Modules Completed"},
    "paths_completed_stat": {"it": "Percorsi completati", "en": "Paths Completed"},
    "badges_title": {"it": "Badge", "en": "Badges"},
    "no_badges_yet": {"it": "Nessun badge ancora. Completa moduli per sbloccarli!", "en": "No badges yet. Complete modules to unlock them!"},
    "leaderboard_title": {"it": "Classifica", "en": "Leaderboard"},
    "new_badge_unlocked": {"it": "Nuovo badge sbloccato!", "en": "New badge unlocked!"},
    "xp_earned": {"it": "+{} XP guadagnati", "en": "+{} XP earned"},
    "badge_gallery_tab": {"it": "Galleria Badge", "en": "Badge Gallery"},
    "badge_summary_tab": {"it": "Riepilogo", "en": "Summary"},
    "badge_locked": {"it": "Bloccato", "en": "Locked"},
    "badge_unlocked_count": {"it": "{unlocked} sbloccati su {total}", "en": "{unlocked} unlocked out of {total}"},

    # ── Profilo ──────────────────────────────────────────────
    "profile_title": {"it": "Il Mio Profilo", "en": "My Profile"},
    "profile_edit": {"it": "Personalizza Profilo", "en": "Customize Profile"},
    "profile_avatar": {"it": "Scegli il tuo avatar", "en": "Choose your avatar"},
    "profile_color": {"it": "Colore tema", "en": "Theme color"},
    "profile_featured": {"it": "Badge in vetrina (max 3)", "en": "Featured badges (max 3)"},
    "profile_save": {"it": "Salva profilo", "en": "Save profile"},
    "profile_saved": {"it": "Profilo aggiornato!", "en": "Profile updated!"},
    "profile_public_title": {"it": "Profilo di", "en": "Profile of"},
    "profile_no_featured": {"it": "Nessun badge in vetrina", "en": "No featured badges"},
    "profile_back": {"it": "← Torna alla classifica", "en": "← Back to leaderboard"},

    # ── Dashboard ───────────────────────────────────────────
    "dashboard_performance": {"it": "Performance", "en": "Performance"},
    "dashboard_learning": {"it": "Apprendimento", "en": "Learning"},
    "topic_distribution": {"it": "Distribuzione topic", "en": "Topic Distribution"},
    "weekly_activity": {"it": "Attività ultimi 7 giorni", "en": "Last 7 Days Activity"},
    "no_activity_data": {"it": "Nessun dato di attività ancora.", "en": "No activity data yet."},
    "no_topic_data": {"it": "Nessun topic studiato ancora.", "en": "No topics studied yet."},
    "topics_studied": {"it": "Topic studiati", "en": "Topics Studied"},
    "weekly_summary": {"it": "Riepilogo settimanale", "en": "Weekly Summary"},
    "attempts_label": {"it": "tentativi", "en": "attempts"},
    "best_streak": {"it": "Record streak", "en": "Best streak"},
    "no_leaderboard": {"it": "Nessun dato in classifica.", "en": "No leaderboard data yet."},
    "accuracy_donut_label": {"it": "Precisione", "en": "Accuracy"},
    "total_attempts": {"it": "totale tentativi", "en": "total attempts"},
    "this_week": {"it": "Questa settimana", "en": "This week"},
    "last_7_days": {"it": "Ultimi 7 giorni", "en": "Last 7 days"},
    "motivational_great": {"it": "Stai andando alla grande! Continua cosi'! 🚀", "en": "You're doing great! Keep it up! 🚀"},
    "motivational_good": {"it": "Buon lavoro! Ogni modulo ti avvicina al prossimo livello 💪", "en": "Good work! Every module brings you closer to the next level 💪"},
    "motivational_start": {"it": "Inizia un nuovo percorso per sbloccare le tue statistiche! ✨", "en": "Start a new path to unlock your stats! ✨"},
    "motivational_comeback": {"it": "Bentornato! Riprendi da dove avevi lasciato 😊", "en": "Welcome back! Pick up where you left off 😊"},
    "sessions_this_week": {"it": "sessioni questa settimana", "en": "sessions this week"},
    "day_mon": {"it": "Lun", "en": "Mon"},
    "day_tue": {"it": "Mar", "en": "Tue"},
    "day_wed": {"it": "Mer", "en": "Wed"},
    "day_thu": {"it": "Gio", "en": "Thu"},
    "day_fri": {"it": "Ven", "en": "Fri"},
    "day_sat": {"it": "Sab", "en": "Sat"},
    "day_sun": {"it": "Dom", "en": "Sun"},
}


def tr(key: str, lang: str = "it", **kwargs) -> str:
    """Restituisce la traduzione per la chiave nella lingua specificata."""
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang, entry.get("it", key))
    if kwargs:
        text = text.format(**kwargs)
    return text


SUPPORTED_LANGS = ["it", "en"]


def get_system_prompt_path(lang: str = "it"):
    """Restituisce il percorso del system prompt in base alla lingua."""
    from pathlib import Path
    project_root = Path(__file__).resolve().parents[1]
    if lang == "en":
        path = project_root / "Prompts" / "system_mlpg_en.md"
        if path.exists():
            return path
    return project_root / "Prompts" / "system_mlpg.md"
