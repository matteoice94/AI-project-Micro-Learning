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
    genera_hint,
)
from src.database import (
    init_db,
    save_session,
    save_attempt,
    update_module_state,
    save_riepilogo,
    get_all_sessions,
    get_session_modules,
    get_module_attempts,
    find_similar_modules,
)
from src.config import RAG_TOP_K

st.set_page_config(
    page_title="MLPG Tutor Streamlit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Clean EdTech Theme ─────────────────────────────────────
st.markdown("""
<style>
    /* Colori tema Clean EdTech */
    :root {
        --primary-blue: #003F87;      /* Blu Oltremare */
        --primary-indigo: #4B0082;    /* Indaco */
        --success-green: #2D5016;     /* Verde positivo */
        --hint-orange: #FF8C00;       /* Arancione hint */
        --bg-light: #F5F5F5;          /* Grigio chiarissimo */
    }
    
    /* Sfondo pagina - Blu oltremare scurissimo */
    .stApp {
        background-color: #0A1628;
        color: #FFFFFF;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0D1F3C;
    }
    
    /* Testo principale */
    .stMarkdown, .stText, .stWrite {
        color: #FFFFFF !important;
    }
    
    /* Pulsanti primari */
    .stButton > button[type="button"] {
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    /* Card success (verde) */
    .stSuccess {
        background-color: #1B5E20 !important;
        color: #FFFFFF !important;
        border-left: 4px solid #4CAF50 !important;
    }
    
    /* Card info (blu) */
    .stInfo {
        background-color: #0D47A1 !important;
        color: #FFFFFF !important;
        border-left: 4px solid #42A5F5 !important;
    }
    
    /* Card warning (arancione) */
    .stWarning {
        background-color: #E65100 !important;
        color: #FFFFFF !important;
        border-left: 4px solid #FF9800 !important;
    }
    
    /* Card error */
    .stError {
        background-color: #B71C1C !important;
        color: #FFFFFF !important;
        border-left: 4px solid #EF5350 !important;
    }
    
    /* Input fields */
    .stTextInput, .stTextArea, .stSelectbox {
        color: #FFFFFF !important;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ── init DB ────────────────────────────────────────────────
if "db_init" not in st.session_state:
    init_db()
    st.session_state.db_init = True

# ── session state ──────────────────────────────────────────
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
if "tentativi_modulo" not in st.session_state:
    st.session_state.tentativi_modulo = {}
if "moduli_archiviati" not in st.session_state:
    st.session_state.moduli_archiviati = []
if "ultima_risposta_modulo" not in st.session_state:
    st.session_state.ultima_risposta_modulo = {}
if "hint_corrente" not in st.session_state:
    st.session_state.hint_corrente = None
if "modulo_archivio_aperto" not in st.session_state:
    st.session_state.modulo_archivio_aperto = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "module_db_ids" not in st.session_state:
    st.session_state.module_db_ids = {}
if "show_history" not in st.session_state:
    st.session_state.show_history = False

# ── migrazione archiviati vecchi ───────────────────────────
if st.session_state.moduli_archiviati:
    migrati = []
    for a in st.session_state.moduli_archiviati:
        if "spiegazione" not in a:
            a["spiegazione"] = ""
        if "livello" not in a:
            a["livello"] = ""
        if "topic" not in a:
            a["topic"] = ""
        migrati.append(a)
    st.session_state.moduli_archiviati = migrati

# ── helper ─────────────────────────────────────────────────
def _reset_current_path():
    st.session_state.risposte_utente = {}
    st.session_state.diario_note = []
    st.session_state.interruzione_dubbio = False
    st.session_state.final_summary = None
    st.session_state.feedbacks = {}
    st.session_state.tentativi_modulo = {}
    st.session_state.ultima_risposta_modulo = {}
    st.session_state.hint_corrente = None
    st.session_state.current_session_id = None
    st.session_state.module_db_ids = {}


# ── Header ─────────────────────────────────────────────────
st.title("🤖 MLPG Tutor con Streamlit")
st.markdown("✨ Genera un percorso personalizzato, valuta le tue soluzioni e chiedi chiarimenti mirati.")

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurazione")
    topic = st.text_input("🎯 Argomento", key="topic", placeholder="Es: Python, Matematica, etc.")
    level = st.selectbox("📊 Livello", ["", "base", "intermedio", "avanzato"], key="level")
    name = st.text_input("👤 Nome (opzionale)", key="name", placeholder="Il tuo nome")

    st.markdown("---")
    
    # ── Pulsanti principali ────────────────────────────────
    col_gen, col_reset = st.columns(2)
    with col_gen:
        generate_btn = st.button("🚀 Genera percorso", key="gen_btn", use_container_width=True, type="primary")
    with col_reset:
        if st.button("🔄 Nuovo", use_container_width=True):
            _reset_current_path()
            st.session_state.response = None
            st.session_state.show_history = False
            st.rerun()
    
    if generate_btn:
        if not topic or not level:
            st.error("❌ Argomento e livello sono obbligatori.")
        else:
            try:
                with st.spinner("⏳ Generazione percorso in corso..."):
                    # RAG: recupera moduli simili dal passato
                    sim = find_similar_modules(topic, top_k=RAG_TOP_K)
                    context = sim if sim else None

                    st.session_state.response = generate_microlearning_path(topic, level, context_modules=context)
                    _reset_current_path()

                    # salva su DB
                    mods = st.session_state.response.percorso_studio.moduli
                    sid = save_session(topic, level, [m.model_dump() for m in mods])
                    st.session_state.current_session_id = sid

                    # mappa id_modulo -> db_id
                    db_mods = get_session_modules(sid)
                    for dbm in db_mods:
                        st.session_state.module_db_ids[str(dbm["module_index"] + 1)] = dbm["id"]

                st.success("✅ Percorso generato e salvato!")
                st.rerun()
            except Exception as exc:
                st.error(f"❌ Errore: {exc}")

    st.markdown("---")
    
    # ── Storico nella sidebar ──────────────────────────────
    with st.expander("📜 Storico Percorsi", expanded=False):
        sessions = get_all_sessions()
        if not sessions:
            st.info("📭 Ancora nessun percorso salvato.")
        else:
            for sess in sessions:
                with st.expander(
                    f"📚 {sess['topic']} ({sess['level']}) — {sess['created_at'][:10]}",
                    expanded=False
                ):
                    st.caption(f"📅 Creato il {sess['created_at'][:19]}")
                    if sess["riepilogo"]:
                        st.markdown("**📝 Riepilogo:**")
                        st.write(sess["riepilogo"][:250])
                    
                    mods = get_session_modules(sess["id"])
                    st.markdown("**Moduli:**")
                    for m in mods:
                        stato_icon = "✅" if m["completed"] else "📦" if m["archived"] else "⏳"
                        stato = "completato" if m["completed"] else "archiviato" if m["archived"] else "in sospeso"
                        col_mod, col_stato = st.columns([3, 1])
                        with col_mod:
                            if st.button(f"🔹 {m['titolo']}", key=f"hist_mod_{m['id']}", use_container_width=True):
                                st.session_state.modulo_archivio_aperto = {
                                    "id": str(m["id"]),
                                    "topic": sess["topic"],
                                    "livello": sess["level"],
                                    "titolo": m["titolo"],
                                    "spiegazione": m["spiegazione"],
                                    "esercizio": m["esercizio"],
                                    "ultima_soluzione": "",
                                }
                                st.session_state.hint_corrente = None
                                st.rerun()
                        with col_stato:
                            st.caption(f"{stato_icon} {stato}")
                        
                        attempts = get_module_attempts(m["id"])
                        if attempts:
                            for att in attempts[-1:]:
                                esito_icon = "✅" if att["esito"] == "corretta" else "⚠️" if att["esito"] == "parziale" else "❌"
                                st.caption(f"  {esito_icon} {att['created_at'][:16]}")

    st.markdown("---")
    
    # ── Moduli da riprendere nella sidebar ──────────────────
    if st.session_state.moduli_archiviati:
        st.markdown("### 🔖 Moduli da Riprendere")
        for arch in st.session_state.moduli_archiviati:
            label = arch["titolo"]
            if arch.get("topic"):
                label += f" ({arch['topic']})"
            if st.button(f"🔹 {label}", key=f"go_arch_{arch['id']}_{arch.get('topic', '')}", use_container_width=True):
                st.session_state.modulo_archivio_aperto = arch
                st.session_state.hint_corrente = None
                st.rerun()

# ── vista modulo archiviato ────────────────────────────────
if st.session_state.modulo_archivio_aperto:
    arch = st.session_state.modulo_archivio_aperto

    col_titolo, col_torna = st.columns([3, 1])
    with col_titolo:
        st.markdown(f"### 📖 {arch.get('titolo', 'Modulo')}")
    with col_torna:
        if st.button("⬅️ Torna", use_container_width=True):
            st.session_state.modulo_archivio_aperto = None
            st.rerun()

    if arch.get("topic"):
        st.info(f"📚 **Argomento originale:** {arch['topic']}")
    
    st.markdown("#### Spiegazione")
    st.write(arch.get("spiegazione", ""))
    
    st.markdown("#### Esercizio")
    st.write(arch.get("esercizio", ""))

    solution = st.text_area("💭 La tua soluzione", key="soluzione_archivio", height=120)
    if st.button("✅ Valuta soluzione", key="valuta_archivio", use_container_width=True):
        if not solution:
            st.error("❌ Inserisci una soluzione prima di valutare.")
        else:
            try:
                with st.spinner("⏳ Valutazione in corso..."):
                    feedback = valuta_risposta(arch["esercizio"], solution)
                if feedback.esito in ("sbagliata", "parziale"):
                    hint = genera_hint(arch["esercizio"], solution, arch.get("livello", "base"), 1)
                    st.warning(f"⚠️ **Suggerimento:** {hint}")
                    st.markdown("**💡 Commento costruttivo:**")
                    st.write(feedback.commento_costruttivo)
                    st.markdown("**🎯 Suggerimento di miglioramento:**")
                    st.write(feedback.suggerimento_miglioramento)
                else:
                    st.session_state.moduli_archiviati = [
                        a for a in st.session_state.moduli_archiviati
                        if a["id"] != arch["id"] or a.get("topic") != arch.get("topic")
                    ]
                    if arch["id"] not in st.session_state.risposte_utente:
                        st.session_state.risposte_utente[arch["id"]] = {
                            "esercizio": arch["esercizio"],
                            "soluzione": solution,
                        }
                    # salva tentativo e aggiorna DB per moduli dello storico
                    try:
                        db_id = int(arch["id"])
                        save_attempt(db_id, solution, "corretta", feedback.model_dump_json())
                        update_module_state(db_id, completed=True)
                    except (ValueError, Exception):
                        pass
                    st.session_state.modulo_archivio_aperto = None
                    st.success("🎉 Modulo completato con successo!")
                    st.rerun()
            except Exception as exc:
                st.error(f"❌ Errore nella valutazione: {exc}")

    st.markdown("---")
    st.markdown("#### 🤔 Chiedi chiarimenti mirati")
    dubbio = st.text_area("Quale parte non ti è chiara?", key="dubbio_archivio", height=100)
    if st.button("💬 Genera spiegazione mirata", key="clarify_archivio", use_container_width=True):
        if not dubbio:
            st.error("❌ Inserisci il dubbio specifico prima di procedere.")
        else:
            try:
                with st.spinner("⏳ Generazione spiegazione..."):
                    clar = genera_spiegazione_alternativa(arch["titolo"], arch["spiegazione"], dubbio, arch.get("livello", "base"))
                col_1, col_2 = st.columns(2)
                with col_1:
                    st.markdown("**📝 Spiegazione semplificata**")
                    st.write(clar.get("spiegazione_semplificata", ""))
                with col_2:
                    st.markdown("**🔧 Esempio pratico**")
                    st.write(clar.get("esempio_pratico", ""))
                if clar.get("passaggi"):
                    st.markdown("**📋 Passaggi consigliati**")
                    for item in clar.get("passaggi", []):
                        st.write(f"- {item}")
            except Exception as exc:
                st.error(f"❌ Errore nella generazione dei chiarimenti: {exc}")

    if st.button("⬅️ Torna al percorso corrente", key="torna_archivio_bottom", use_container_width=True):
        st.session_state.modulo_archivio_aperto = None
        st.rerun()

# ── percorso attuale ───────────────────────────────────────
elif st.session_state.response:
    response = st.session_state.response
    modules = response.percorso_studio.moduli
    objective = response.percorso_studio.metadati.objective_apprendimento
    livello = response.percorso_studio.metadati.difficolta_impostata

    st.markdown("---")
    
    # ── Obiettivo di apprendimento ──────────────────────────
    st.markdown("### 🎯 Obiettivo di apprendimento")
    st.info(objective)

    st.markdown("---")
    
    # ── Selezione modulo ────────────────────────────────────
    module_labels = [f"Modulo {idx+1}: {mod.titolo_modulo}" for idx, mod in enumerate(modules)]
    selected_idx = st.selectbox("📚 Seleziona modulo", range(len(modules)), format_func=lambda x: module_labels[x], key="selected_module")
    module = modules[selected_idx]

    id_modulo = str(module.id)
    is_archived = any(a["id"] == id_modulo and a.get("topic", "") == (topic or "") for a in st.session_state.moduli_archiviati)

    if is_archived:
        st.warning("⚠️ Hai già tentato questo modulo in precedenza. Puoi riprovare qui sotto.")
    
    st.markdown(f"#### 📖 Modulo {module.id}: {module.titolo_modulo}")

    col_spiega, col_esercizio = st.columns([1, 1])
    
    with col_spiega:
        st.markdown("**Spiegazione:**")
        st.write(module.spiegazione)
    
    with col_esercizio:
        st.markdown("**Esercizio:**")
        st.write(module.esercizio_pratico)

    st.markdown("---")
    
    solution = st.text_area("💭 La tua soluzione", key=f"solution_{module.id}", height=150)
    if st.button("✅ Valuta soluzione", key=f"valuta_{module.id}", use_container_width=True, type="primary"):
        if not solution:
            st.error("❌ Inserisci una soluzione prima di valutare.")
        else:
            try:
                with st.spinner("⏳ Valutazione in corso..."):
                    feedback = valuta_risposta(module.esercizio_pratico, solution)
                st.session_state.feedbacks[module.id] = feedback

                if feedback.esito in ("sbagliata", "parziale"):
                    ultima = st.session_state.ultima_risposta_modulo.get(id_modulo)
                    if ultima is not None and ultima == solution:
                        st.warning("⚠️ Hai inviato la stessa risposta. Rileggi l'hint qui sotto e riprova con un approccio diverso.")
                    else:
                        tentativi = st.session_state.tentativi_modulo.get(id_modulo, 0) + 1
                        st.session_state.tentativi_modulo[id_modulo] = tentativi
                        st.session_state.ultima_risposta_modulo[id_modulo] = solution

                        # salva tentativo su DB
                        db_id = st.session_state.module_db_ids.get(id_modulo)
                        if db_id:
                            save_attempt(db_id, solution, feedback.esito, feedback.model_dump_json())

                        if tentativi >= 2:
                            st.session_state.moduli_archiviati.append({
                                "id": id_modulo,
                                "topic": topic,
                                "livello": livello,
                                "titolo": module.titolo_modulo,
                                "spiegazione": module.spiegazione,
                                "esercizio": module.esercizio_pratico,
                                "ultima_soluzione": solution,
                            })
                            st.session_state.diario_note.append(
                                f"Modulo {module.id} ({module.titolo_modulo}): archiviato dopo {tentativi} tentativi"
                            )
                            if db_id:
                                update_module_state(db_id, archived=True)
                            st.warning(f"📦 Modulo archiviato dopo {tentativi} tentativi. Potrai riprovare dalla sezione 'Moduli da Riprendere'.")
                            st.rerun()
                        else:
                            hint = genera_hint(module.esercizio_pratico, solution, livello, tentativi)
                            st.session_state.hint_corrente = hint

                else:
                    # risposta corretta
                    st.session_state.moduli_archiviati = [
                        a for a in st.session_state.moduli_archiviati
                        if not (a["id"] == id_modulo and a.get("topic", "") == (topic or ""))
                    ]
                    st.session_state.risposte_utente[id_modulo] = {
                        "esercizio": module.esercizio_pratico,
                        "soluzione": solution,
                    }
                    db_id = st.session_state.module_db_ids.get(id_modulo)
                    if db_id:
                        save_attempt(db_id, solution, "corretta", feedback.model_dump_json())
                        update_module_state(db_id, completed=True)
                    st.success("🎉 Risposta corretta!")

            except Exception as exc:
                st.error(f"❌ Errore nella valutazione: {exc}")

    if module.id in st.session_state.feedbacks:
        feedback = st.session_state.feedbacks[module.id]
        st.markdown("---")
        col_comment, col_suggest = st.columns(2)
        with col_comment:
            st.markdown("**💡 Commento costruttivo:**")
            st.write(feedback.commento_costruttivo)
        with col_suggest:
            st.markdown("**🎯 Suggerimento di miglioramento:**")
            st.write(feedback.suggerimento_miglioramento)

    if st.session_state.hint_corrente:
        if module.id in st.session_state.feedbacks:
            fb_esito = st.session_state.feedbacks[module.id].esito
            if fb_esito in ("sbagliata", "parziale"):
                st.markdown("---")
                st.warning(f"💡 **Suggerimento:** {st.session_state.hint_corrente}")

    st.markdown("---")
    st.markdown("#### 🤔 Chiedi chiarimenti mirati")
    dubbio = st.text_area("Quale parte non ti è chiara?", key=f"dubbio_{module.id}", height=100)
    if st.button("💬 Genera spiegazione mirata", key=f"clarify_{module.id}", use_container_width=True):
        if not dubbio:
            st.error("❌ Inserisci il dubbio specifico prima di procedere.")
        else:
            try:
                with st.spinner("⏳ Generazione spiegazione..."):
                    clar = genera_spiegazione_alternativa(module.titolo_modulo, module.spiegazione, dubbio, livello)
                
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("**📝 Spiegazione semplificata**")
                    st.write(clar.get("spiegazione_semplificata", ""))
                with col_right:
                    st.markdown("**🔧 Esempio pratico**")
                    st.write(clar.get("esempio_pratico", ""))
                
                if clar.get("passaggi"):
                    st.markdown("**📋 Passaggi consigliati**")
                    for item in clar.get("passaggi", []):
                        st.write(f"- {item}")
                
                st.session_state.diario_note.append(f"Modulo {module.id} ({module.titolo_modulo}): {dubbio}")
                st.session_state.interruzione_dubbio = True
            except Exception as exc:
                st.error(f"❌ Errore nella generazione dei chiarimenti: {exc}")

    st.markdown("---")
    st.markdown("#### 📊 Riepilogo finale")
    st.write(f"**Livello di partenza:** {livello}")

    if module.id == modules[-1].id:
        if st.button("📝 Genera riepilogo finale", key="genera_riepilogo_finale", use_container_width=True, type="primary"):
            tutte_risposte = list(st.session_state.risposte_utente.values())
            if not tutte_risposte and not st.session_state.moduli_archiviati:
                st.error("❌ Inserisci almeno una soluzione ai moduli prima di generare il riepilogo finale.")
            else:
                try:
                    with st.spinner("⏳ Generazione riepilogo..."):
                        for arch in st.session_state.moduli_archiviati:
                            if arch["id"] not in st.session_state.risposte_utente:
                                st.session_state.risposte_utente[arch["id"]] = {
                                    "esercizio": arch["esercizio"],
                                    "soluzione": arch.get("ultima_soluzione", ""),
                                }
                        riepilogo = genera_riepilogo_finale(
                            list(st.session_state.risposte_utente.values()),
                            st.session_state.diario_note,
                            livello,
                        )
                        st.session_state.final_summary = riepilogo
                        # salva riepilogo su DB
                        sid = st.session_state.current_session_id
                        if sid:
                            save_riepilogo(sid, riepilogo.model_dump_json())
                    st.success("✅ Riepilogo finale generato con successo.")
                except Exception as exc:
                    st.error(f"❌ Errore nella generazione del riepilogo finale: {exc}")

        if st.session_state.final_summary:
            riepilogo = st.session_state.final_summary
            st.markdown("---")
            st.markdown("### 📋 Risultati Finali")
            
            col_strengths, col_improvements = st.columns(2)
            
            with col_strengths:
                st.success("✅ **Punti di forza:**")
                if riepilogo.punti_di_forza:
                    for point in riepilogo.punti_di_forza:
                        st.write(f"🌟 {point}")
                else:
                    st.write("- Nessun punto di forza disponibile.")

            with col_improvements:
                st.info("📈 **Punti da migliorare:**")
                if riepilogo.punti_da_migliorare:
                    for point in riepilogo.punti_da_migliorare:
                        st.write(f"🎯 {point}")
                else:
                    st.write("- Nessun punto da migliorare disponibile.")

            st.markdown("---")
            st.markdown("**📝 Diario di bordo:**")
            st.write(riepilogo.diario_di_bordo or "- Nessuna nota disponibile.")

            st.markdown("---")
            st.markdown("**🎊 Saluto conclusivo:**")
            st.write(riepilogo.saluto_conclusivo or "- Nessun saluto disponibile.")
        else:
            st.info("💭 Genera il riepilogo finale quando hai completato il terzo modulo.")
    else:
        st.info("📌 Il riepilogo finale sarà disponibile alla conclusione dell'ultimo modulo.")

# ── Pagina di benvenuto (nessun percorso ancora generato) ─
else:
    st.markdown("---")
    st.info("👋 Benvenuto! Inizia generando un nuovo percorso dalla barra laterale.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🎯 Come iniziare")
        st.write("""
1. Scegli un **argomento**
2. Seleziona il tuo **livello**
3. Clicca **Genera percorso**
""")
    with col2:
        st.markdown("### 📚 Come funziona")
        st.write("""
- Ricevi **3 moduli** su misura
- Risolvi gli **esercizi pratici**
- Chiedi **chiarimenti mirati**
""")
    with col3:
        st.markdown("### 💡 Suggerimenti")
        st.write("""
- Se non capisci: usa **Chiedi chiarimenti**
- Se sbagli 2 volte: il modulo si **archivia**
- Potrai **riproverà** dalla sidebar
""")
