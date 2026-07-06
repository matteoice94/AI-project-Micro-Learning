import sys
from .generator import (
    generate_microlearning_path,
    valuta_con_pipeline,
    genera_spiegazione_alternativa,
    genera_riepilogo_finale,
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
from .i18n import tr


def main():
    lang = "it"
    if "--en" in sys.argv or "-e" in sys.argv:
        lang = "en"

    init_db()

    print(tr("cli_header", lang))
    topic = input(tr("cli_topic_prompt", lang) + " ").strip()
    level = input(tr("cli_level_prompt", lang) + " ").strip()

    if not topic or not level:
        print(tr("cli_topic_level_error", lang))
        return

    storico_risposte = []
    diario_note = []
    interruzione_per_dubbio = False
    moduli_archiviati = []

    try:
        context = find_similar_modules(topic, top_k=RAG_TOP_K) or None
        res = generate_microlearning_path(topic, level, context_modules=context, lang=lang)

        sid = save_session(topic, level, [m.model_dump() for m in res.percorso_studio.moduli])
        db_mods = get_session_modules(sid)
        db_map = {str(dbm["module_index"] + 1): dbm["id"] for dbm in db_mods}

        print(f"\n{tr('cli_objective', lang)}: {res.percorso_studio.metadati.objective_apprendimento}\n")

        for idx, modulo in enumerate(res.percorso_studio.moduli):
            print("=" * 50)
            print(f"{tr('module_n', lang)} {modulo.id}: {modulo.titolo_modulo}")
            print("=" * 50)
            print(f"{tr('explanation', lang)}:\n{modulo.spiegazione}\n")
            print(f"{tr('exercise', lang)}:\n{modulo.esercizio_pratico}\n")

            id_modulo = str(modulo.id)
            db_id = db_map.get(id_modulo)
            tentativi = 0
            ultima_risposta = None
            stop_percorso = False

            while tentativi < 2:
                user_solution = input(tr("cli_solution_prompt", lang) + " ").strip()
                if not user_solution:
                    print(tr("cli_empty_solution", lang) + "\n")
                    break

                pipeline = valuta_con_pipeline(modulo.esercizio_pratico, user_solution, level, lang,
                                               tentativi=tentativi)

                if not pipeline["valido"]:
                    print(f"\n⚠️  {pipeline['message']}\n")
                    continue

                try:
                    feedback = pipeline["feedback"]

                    if db_id:
                        save_attempt(db_id, user_solution, feedback.esito or "", feedback.model_dump_json())

                    if feedback.esito in ("sbagliata", "parziale"):
                        if ultima_risposta == user_solution:
                            print(f"\n{tr('cli_same_answer', lang)}\n")
                        else:
                            tentativi += 1
                            ultima_risposta = user_solution

                        if pipeline["archive"]:
                            moduli_archiviati.append(modulo.titolo_modulo)
                            diario_note.append(f"Modulo {modulo.id} ({modulo.titolo_modulo}): archived after {tentativi} attempts")
                            if db_id:
                                update_module_state(db_id, archived=True)
                            print(f"\n{tr('cli_module_archived', lang)}\n")
                            break
                        elif pipeline["hint"]:
                            print(f"\n--- {tr('hint_label', lang)} ---\n{pipeline['hint']}\n")
                            print(f"{tr('constructive_comment', lang)}: {feedback.commento_costruttivo}")
                            print(f"{tr('improvement_suggestion', lang)}: {feedback.suggerimento_miglioramento}\n")

                            capito = input(tr("cli_understood", lang) + " ").strip().lower()
                            if capito in ('no', 'n'):
                                dubbio = input(tr("cli_what_unclear", lang) + " ").strip()
                                try:
                                    chiar = genera_spiegazione_alternativa(modulo.titolo_modulo, modulo.spiegazione, dubbio, level, lang)
                                    print(f"\n{tr('explanation', lang)}: {chiar.get('spiegazione_semplificata', '')}")
                                    if chiar.get('esempio_pratico'):
                                        print(f"{tr('practical_example', lang)}: {chiar.get('esempio_pratico')}")
                                    diario_note.append(f"Modulo {modulo.id}: {dubbio}")
                                    interruzione_per_dubbio = True
                                except Exception as e:
                                    print(f"{tr('cli_clarify_error', lang)}: {e}")
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
                    print(f"{tr('cli_clarify_error', lang)}: {e}\n")
                    break
            else:
                continue

        if storico_risposte or moduli_archiviati:
            if not storico_risposte:
                for m in moduli_archiviati:
                    storico_risposte.append({"esercizio": "", "soluzione": ""})
            try:
                riepilogo = genera_riepilogo_finale(storico_risposte, diario_note, level, lang)
                if sid:
                    save_riepilogo(sid, riepilogo.model_dump_json())

                print("\n" + "=" * 50)
                print(tr("cli_final_summary_header", lang))
                print("=" * 50)
                print(f"{tr('cli_summary_level', lang)}: {level}")
                print(f"\n{tr('cli_strengths', lang)}:")
                for p in (riepilogo.punti_di_forza or []):
                    print(f"  - {p}")
                print(f"\n{tr('cli_improvements', lang)}:")
                for p in (riepilogo.punti_da_migliorare or []):
                    print(f"  - {p}")
                print(f"\n{tr('cli_logbook', lang)}:\n  {riepilogo.diario_di_bordo}")
                print(f"\n{tr('cli_farewell', lang)}:\n  {riepilogo.saluto_conclusivo}")
            except Exception as e:
                print(f"{tr('cli_summary_error', lang)}: {e}")

    except Exception as e:
        print(f"{tr('generation_error', lang)}: {e}")


if __name__ == "__main__":
    main()
