from .generator import generate_microlearning_path, valuta_risposta, genera_spiegazione_alternativa, genera_riepilogo_finale

def main():
    print("=== MLPG Tutor: Generazione Percorso Microlearning ===")
    topic = input("Inserisci l'argomento da studiare: ").strip()
    level = input("Inserisci il livello (base, intermedio, avanzato): ").strip()
    nome = input("Inserisci il tuo nome (opzionale): ").strip() or "Studente"

    if not topic or not level:
        print("Errore: argomento e livello sono obbligatori.")
        return

    # Lista per tracciare argomenti con difficoltà per il recupero
    argomenti_da_recuperare = []
    punti_di_forza = []
    interruzione_per_dubbio = False
    storico_risposte = []
    percorso_completo = True

    try:
        res = generate_microlearning_path(topic, level)
        print("\n--- Risultato Generazione ---")
        print(f"Obiettivo: {res.percorso_studio.metadati.objective_apprendimento}\n")

        for idx, modulo in enumerate(res.percorso_studio.moduli):
            print("=" * 50)
            print(f"MODULO {modulo.id}: {modulo.titolo_modulo}")
            print("=" * 50)
            print(f"Spiegazione:\n{modulo.spiegazione}\n")
            print(f"Esercizio:\n{modulo.esercizio_pratico}\n")
            
            # Chiedi la soluzione all'utente
            print("--- Prova a risolvere l'esercizio ---")
            user_solution = input("Scrivi la tua soluzione:\n").strip()
            
            if user_solution:
                storico_risposte.append({
                    'esercizio': modulo.esercizio_pratico,
                    'soluzione': user_solution,
                })
                try:
                    # Valuta la risposta
                    feedback = valuta_risposta(modulo.esercizio_pratico, user_solution)
                    # Raccogli i punti di forza analitici (se presenti)
                    if feedback.punti_di_forza:
                        punti_di_forza.extend(feedback.punti_di_forza)

                    print("\n--- Valutazione del Tutor ---")
                    print(f"Commento costruttivo:\n{feedback.commento_costruttivo}\n")
                    # Mostra punti di forza e punti migliorabili separatamente
                    if feedback.punti_di_forza:
                        print("Punti di forza:")
                        for p in feedback.punti_di_forza:
                            print(f"  - {p}")
                        print()
                    else:
                        print("Punti di forza: nessun punto analitico generato.\n")

                    if feedback.punti_migliorabili:
                        print("Punti migliorabili:")
                        for pm in feedback.punti_migliorabili:
                            print(f"  - {pm}")
                        print()
                    else:
                        print("Punti migliorabili: nessun punto segnalato.\n")

                    print(f"Suggerimento di miglioramento:\n{feedback.suggerimento_miglioramento}\n")
                    
                    # Ciclo di comprensione
                    stop_percorso = False
                    while True:
                        comprensione = input("Hai capito bene questo concetto? (sì/no): ").strip().lower()
                        
                        if comprensione in ['sì', 'si', 's', 'y', 'yes']:
                            print("Ottimo! Procediamo al prossimo modulo.\n")
                            break
                        elif comprensione in ['no', 'n']:
                            print("\nNo problem! Genero una spiegazione mirata per il tuo dubbio...\n")
                            dubbio_utente = input("Quale parte precisa non ti è chiara? Indica un termine, un passaggio o un concetto specifico: ").strip()
                            try:
                                spiegazione_alt = genera_spiegazione_alternativa(
                                    modulo.titolo_modulo,
                                    modulo.spiegazione,
                                    dubbio_utente,
                                    level
                                )
                                print("\n--- Spiegazione Semplificata ---")
                                print(spiegazione_alt.get('spiegazione_semplificata', ''))
                                if spiegazione_alt.get('esempio_pratico'):
                                    print("\n--- Esempio pratico ---")
                                    print(spiegazione_alt.get('esempio_pratico'))
                                if spiegazione_alt.get('passaggi'):
                                    print("\n--- Passaggi consigliati ---")
                                    for passaggio in spiegazione_alt.get('passaggi', []):
                                        print(f"  - {passaggio}")
                                print()
                                
                                # Traccia l'argomento per il recupero
                                argomenti_da_recuperare.append(
                                    f"Modulo {modulo.id} ({modulo.titolo_modulo}): {dubbio_utente}"
                                )
                                
                                continua = input("\nHai capito meglio ora? (sì/no): ").strip().lower()
                                if continua in ['sì', 'si', 's', 'y', 'yes']:
                                    print("Perfetto! Procediamo al prossimo modulo.\n")
                                    break
                                else:
                                    print("Ok, archiviamo questo argomento per il recupero successivo e interrompiamo il percorso.\n")
                                    stop_percorso = True
                                    percorso_completo = False
                                    interruzione_per_dubbio = True
                                    break
                            except Exception as e:
                                print(f"Errore nella generazione della spiegazione semplificata: {e}\n")
                                stop_percorso = True
                                break
                        else:
                            print("Per favore rispondi con 'sì' o 'no'.")
                            continue
                    
                    if stop_percorso:
                        break
                except Exception as e:
                    print(f"Errore nella valutazione: {e}\n")
            else:
                print("Soluzione vuota. Passaggio al modulo successivo...\n")
        
        if percorso_completo and storico_risposte:
            try:
                riepilogo_finale = genera_riepilogo_finale(
                    storico_risposte,
                    argomenti_da_recuperare,
                    level,
                )

                print("\n" + "=" * 50)
                print("RIEPILOGO FINALE")
                print("=" * 50)
                print(f"Livello di partenza: {level}")

                print("\nPunti di forza:")
                if riepilogo_finale.punti_di_forza:
                    for forza in riepilogo_finale.punti_di_forza:
                        print(f"  - {forza}")
                else:
                    print("  - Nessun punto di forza disponibile.")

                print("\nPunti da migliorare:")
                if riepilogo_finale.punti_da_migliorare:
                    for miglioramento in riepilogo_finale.punti_da_migliorare:
                        print(f"  - {miglioramento}")
                else:
                    print("  - Nessun punto da migliorare disponibile.")

                print("\nDiario di bordo:")
                print(riepilogo_finale.diario_di_bordo or "  - Nessuna nota disponibile.")

                print("\nSaluto conclusivo:")
                print(riepilogo_finale.saluto_conclusivo or "  - Nessun saluto disponibile.")
            except Exception as e:
                print(f"Errore nella generazione del riepilogo finale: {e}")
        else:
            print("\nIl riepilogo finale non è stato generato perché il percorso non è stato completato o non ci sono risposte sufficienti.")

    except Exception as e:
        print(f"Errore durante la generazione: {e}")


if __name__ == "__main__":
    main()
