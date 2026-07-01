from .generator import (
    generate_microlearning_path,
    valuta_risposta,
    genera_spiegazione_alternativa,
    genera_riepilogo_finale,
    genera_hint,
    valida_input_euristico,
    sanity_check_risposta,
)
from .database import (
    init_db,
    save_session,
    save_attempt,
    update_module_state,
    save_riepilogo,
    find_similar_modules,
    get_session_modules,
)
from .config import RAG_TOP_K


def main():
    init_db()

    print("=== MLPG Tutor: Generazione Percorso Microlearning ===")
    topic = input("Inserisci l'argomento da studiare: ").strip()
    level = input("Inserisci il livello (base, intermedio, avanzato): ").strip()

    if not topic or not level:
        print("Errore: argomento e livello sono obbligatori.")
        return

    storico_risposte = []
    diario_note = []
    interruzione_per_dubbio = False
    moduli_archiviati = []

    try:
        context = find_similar_modules(topic, top_k=RAG_TOP_K) or None
        res = generate_microlearning_path(topic, level, context_modules=context)

        sid = save_session(topic, level, [m.model_dump() for m in res.percorso_studio.moduli])
        db_mods = get_session_modules(sid)
        db_map = {str(dbm["module_index"] + 1): dbm["id"] for dbm in db_mods}

        print(f"\nObiettivo: {res.percorso_studio.metadati.objective_apprendimento}\n")

        for idx, modulo in enumerate(res.percorso_studio.moduli):
            print("=" * 50)
            print(f"MODULO {modulo.id}: {modulo.titolo_modulo}")
            print("=" * 50)
            print(f"Spiegazione:\n{modulo.spiegazione}\n")
            print(f"Esercizio:\n{modulo.esercizio_pratico}\n")

            id_modulo = str(modulo.id)
            db_id = db_map.get(id_modulo)
            tentativi = 0
            ultima_risposta = None
            stop_percorso = False

            while tentativi < 2:
                user_solution = input("Scrivi la tua soluzione (o premi Invio per saltare): ").strip()
                if not user_solution:
                    print("Soluzione vuota. Passaggio al prossimo modulo.\n")
                    break

                # Opzione A — Filtro euristico (gratuito, immediato)
                valido_eur, motivo_eur = valida_input_euristico(modulo.esercizio_pratico, user_solution)
                if not valido_eur:
                    print(f"\n⚠️  {motivo_eur}\n")
                    continue

                # Opzione C — Sanity check LLM (leggero)
                print("🔍 Verifica pertinenza della risposta...")
                pertinente, motivo_sc = sanity_check_risposta(modulo.esercizio_pratico, user_solution)
                if not pertinente:
                    msg = "La tua risposta non sembra pertinente all'esercizio"
                    if motivo_sc:
                        msg += f": {motivo_sc}"
                    print(f"\n⚠️  {msg}. Riprova con una risposta più mirata.\n")
                    continue

                try:
                    # Opzione B — Valutazione completa (prompt arricchito)
                    feedback = valuta_risposta(modulo.esercizio_pratico, user_solution)

                    if db_id:
                        save_attempt(db_id, user_solution, feedback.esito or "", feedback.model_dump_json())

                    if feedback.esito in ("sbagliata", "parziale"):
                        if ultima_risposta == user_solution:
                            print("\nHai inviato la stessa risposta. Rileggi l'hint qui sotto.\n")
                        else:
                            tentativi += 1
                            ultima_risposta = user_solution

                        if tentativi >= 2:
                            moduli_archiviati.append(modulo.titolo_modulo)
                            diario_note.append(f"Modulo {modulo.id} ({modulo.titolo_modulo}): archiviato dopo {tentativi} tentativi")
                            if db_id:
                                update_module_state(db_id, archived=True)
                            print("\nModulo archiviato per una prossima sessione. Passiamo avanti.\n")
                            break
                        else:
                            hint = genera_hint(modulo.esercizio_pratico, user_solution, level, tentativi)
                            print(f"\n--- Suggerimento ---\n{hint}\n")
                            print(f"Commento: {feedback.commento_costruttivo}")
                            print(f"Miglioramento: {feedback.suggerimento_miglioramento}\n")

                            # comprensione
                            capito = input("Hai capito meglio ora? (sì/no, default sì): ").strip().lower()
                            if capito in ('no', 'n'):
                                dubbio = input("Quale parte non ti è chiara? ").strip()
                                try:
                                    chiar = genera_spiegazione_alternativa(modulo.titolo_modulo, modulo.spiegazione, dubbio, level)
                                    print(f"\nSpiegazione: {chiar.get('spiegazione_semplificata', '')}")
                                    if chiar.get('esempio_pratico'):
                                        print(f"Esempio: {chiar.get('esempio_pratico')}")
                                    diario_note.append(f"Modulo {modulo.id}: {dubbio}")
                                    interruzione_per_dubbio = True
                                except Exception as e:
                                    print(f"Errore chiarimento: {e}")
                            continue
                    else:
                        storico_risposte.append({
                            'esercizio': modulo.esercizio_pratico,
                            'soluzione': user_solution,
                        })
                        if db_id:
                            update_module_state(db_id, completed=True)
                        print(f"\n{feedback.commento_costruttivo}\n")
                        break

                except Exception as e:
                    print(f"Errore nella valutazione: {e}\n")
                    break
            else:
                continue

        if storico_risposte or moduli_archiviati:
            if not storico_risposte:
                for m in moduli_archiviati:
                    storico_risposte.append({"esercizio": "", "soluzione": ""})
            try:
                riepilogo = genera_riepilogo_finale(storico_risposte, diario_note, level)
                if sid:
                    save_riepilogo(sid, riepilogo.model_dump_json())

                print("\n" + "=" * 50)
                print("RIEPILOGO FINALE")
                print("=" * 50)
                print(f"Livello: {level}")
                print(f"\nPunti di forza:")
                for p in (riepilogo.punti_di_forza or []):
                    print(f"  - {p}")
                print(f"\nPunti da migliorare:")
                for p in (riepilogo.punti_da_migliorare or []):
                    print(f"  - {p}")
                print(f"\nDiario di bordo:\n  {riepilogo.diario_di_bordo}")
                print(f"\nSaluto:\n  {riepilogo.saluto_conclusivo}")
            except Exception as e:
                print(f"Errore riepilogo finale: {e}")

    except Exception as e:
        print(f"Errore durante la generazione: {e}")


if __name__ == "__main__":
    main()
