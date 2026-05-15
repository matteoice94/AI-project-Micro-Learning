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

---
*Aggiungi qui le prossime modifiche quando testerai i prompt su VS Code.*