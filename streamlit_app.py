import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

import streamlit as st
from src.generator import (
    generate_microlearning_path,
    valuta_risposta,
    genera_spiegazione_alternativa,
    genera_riepilogo_finale,
)

st.set_page_config(page_title="MLPG Tutor Streamlit", layout="wide")

if "response" not in st.session_state:
    st.session_state.response = None
if "risposte_utente" not in st.session_state:
    st.session_state.risposte_utente = {}
if "diario_note" not in st.session_state:
    st.session_state.diario_note = []
if "interruzione_dubbio" not in st.session_state:
    st.session_state.interruzione_dubbio = False
if "final_summary" not in st.session_state:
    st.session_state.final_summary = None
if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = {}

st.title("MLPG Tutor con Streamlit")
st.write("Genera un percorso, valuta una risposta e chiedi chiarimenti mirati." )

with st.sidebar:
    st.header("Configurazione")
    topic = st.text_input("Argomento", key="topic")
    level = st.selectbox("Livello", ["", "base", "intermedio", "avanzato"], key="level")
    name = st.text_input("Nome (opzionale)", key="name")
    if st.button("Genera percorso"):
        if not topic or not level:
            st.error("Argomento e livello sono obbligatori.")
        else:
            try:
                st.session_state.response = generate_microlearning_path(topic, level)
                st.session_state.risposte_utente = {}
                st.session_state.diario_note = []
                st.session_state.interruzione_dubbio = False
                st.session_state.final_summary = None
                st.session_state.feedbacks = {}
                st.success("Percorso generato con successo.")
            except Exception as exc:
                st.error(f"Impossibile generare il percorso: {exc}")

if st.session_state.response:
    response = st.session_state.response
    modules = response.percorso_studio.moduli
    objective = response.percorso_studio.metadati.objective_apprendimento
    livello = response.percorso_studio.metadati.difficolta_impostata

    st.markdown("---")
    st.subheader("Obiettivo di apprendimento")
    st.write(objective)

    module_labels = [f"{mod.id} - {mod.titolo_modulo}" for mod in modules]
    selected_idx = st.selectbox("Seleziona modulo", range(len(modules)), format_func=lambda x: module_labels[x], key="selected_module")
    module = modules[selected_idx]

    st.markdown(f"### Modulo {module.id}: {module.titolo_modulo}")
    st.write(module.spiegazione)
    st.write("**Esercizio:**")
    st.write(module.esercizio_pratico)

    solution = st.text_area("La tua soluzione", key=f"solution_{module.id}")
    if st.button("Valuta soluzione", key=f"valuta_{module.id}"):
        if not solution:
            st.error("Inserisci una soluzione prima di valutare.")
        else:
            try:
                feedback = valuta_risposta(module.esercizio_pratico, solution)
                st.session_state.feedbacks[module.id] = feedback
                st.session_state.risposte_utente[str(module.id)] = {
                    "esercizio": module.esercizio_pratico,
                    "soluzione": solution,
                }
                st.success("Feedback generato.")
            except Exception as exc:
                st.error(f"Errore nella valutazione: {exc}")

    if module.id in st.session_state.feedbacks:
        feedback = st.session_state.feedbacks[module.id]
        st.markdown("**Commento costruttivo:**")
        st.write(feedback.commento_costruttivo)
        st.markdown("**Suggerimento di miglioramento:**")
        st.write(feedback.suggerimento_miglioramento)

    st.markdown("---")
    st.subheader("Chiedi chiarimenti mirati")
    dubbio = st.text_area("Quale parte non ti è chiara?", key=f"dubbio_{module.id}")
    if st.button("Genera spiegazione mirata", key=f"clarify_{module.id}"):
        if not dubbio:
            st.error("Inserisci il dubbio specifico prima di procedere.")
        else:
            try:
                clar = genera_spiegazione_alternativa(module.titolo_modulo, module.spiegazione, dubbio, livello)
                st.write("**Spiegazione semplificata**")
                st.write(clar.get("spiegazione_semplificata", ""))
                st.write("**Esempio pratico**")
                st.write(clar.get("esempio_pratico", ""))
                if clar.get("passaggi"):
                    st.write("**Passaggi consigliati**")
                    for item in clar.get("passaggi", []):
                        st.write(f"- {item}")
                st.session_state.diario_note.append(f"Modulo {module.id} ({module.titolo_modulo}): {dubbio}")
                st.session_state.interruzione_dubbio = True
            except Exception as exc:
                st.error(f"Errore nella generazione dei chiarimenti: {exc}")

    st.markdown("---")
    st.subheader("Riepilogo finale")
    st.write(f"**Livello di partenza:** {livello}")

    if module.id == modules[-1].id:
        if st.button("Genera riepilogo finale", key="genera_riepilogo_finale"):
            if not st.session_state.risposte_utente:
                st.error("Inserisci almeno una soluzione ai moduli prima di generare il riepilogo finale.")
            else:
                try:
                    riepilogo = genera_riepilogo_finale(
                        list(st.session_state.risposte_utente.values()),
                        st.session_state.diario_note,
                        livello,
                    )
                    st.session_state.final_summary = riepilogo
                    st.success("Riepilogo finale generato con successo.")
                except Exception as exc:
                    st.error(f"Errore nella generazione del riepilogo finale: {exc}")

        if st.session_state.final_summary:
            riepilogo = st.session_state.final_summary
            st.markdown("**Punti di forza:**")
            if riepilogo.punti_di_forza:
                for point in riepilogo.punti_di_forza:
                    st.write(f"- {point}")
            else:
                st.write("- Nessun punto di forza disponibile.")

            st.markdown("**Punti da migliorare:**")
            if riepilogo.punti_da_migliorare:
                for point in riepilogo.punti_da_migliorare:
                    st.write(f"- {point}")
            else:
                st.write("- Nessun punto da migliorare disponibile.")

            st.markdown("**Diario di bordo:**")
            st.write(riepilogo.diario_di_bordo or "- Nessuna nota disponibile.")

            st.markdown("**Saluto conclusivo:**")
            st.write(riepilogo.saluto_conclusivo or "- Nessun saluto disponibile.")
        else:
            st.info("Genera il riepilogo finale quando hai completato il terzo modulo.")
    else:
        st.info("Il riepilogo finale sarà disponibile alla conclusione dell'ultimo modulo.")
