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
    create_user,
    authenticate_user,
    save_session,
    save_attempt,
    update_module_state,
    rename_module,
    delete_module,
    rename_session,
    delete_session,
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
    
    /* ── 1. Card effetto schede ── */
    .main [data-testid="column"] {
        background: linear-gradient(145deg, #141e30, #1a2332);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        transition: border-color 0.2s ease;
    }
    .main [data-testid="column"]:hover {
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    /* ── 2. Badge pills per stato ── */
    .badge {
        display: inline-block;
        padding: 0 10px;
        border-radius: 20px;
        font-size: 0.7em;
        font-weight: 700;
        line-height: 1.8;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }
    .badge.badge-completato {
        background: rgba(76, 175, 80, 0.2);
        color: #81C784;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    .badge.badge-archiviato {
        background: rgba(33, 150, 243, 0.2);
        color: #64B5F6;
        border: 1px solid rgba(33, 150, 243, 0.3);
    }
    .badge.badge-sospeso {
        background: rgba(255, 152, 0, 0.2);
        color: #FFB74D;
        border: 1px solid rgba(255, 152, 0, 0.3);
    }
    
    /* ── 3. Syntax highlighting per codice ── */
    code {
        background: #0d1f3c !important;
        color: #e0e0e0 !important;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.9em;
    }
    pre {
        background: #0a1628 !important;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px !important;
        overflow-x: auto;
    }
    pre code {
        background: none !important;
        padding: 0 !important;
        border: none !important;
    }
    
    /* ── 4. Altezza uniforme colonne ── */
    .main [data-testid="column"] > div {
        height: 100%;
    }
    
    /* ── Login card ── */
    div.login-card {
        background: linear-gradient(145deg, #141e30, #1a2332);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 40px 32px;
        text-align: center;
    }
    div.login-card h1 {
        margin-bottom: 4px;
    }
    div.login-card p.sub {
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 24px;
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
if "user" not in st.session_state:
    st.session_state.user = None

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


# ── Login ──────────────────────────────────────────────────
if not st.session_state.user:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { display: flex; justify-content: center; align-items: center; min-height: 90vh; }
    </style>
    """, unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### 🤖 MLPG Tutor")
        st.markdown('<p class="sub">Accedi per continuare</p>', unsafe_allow_html=True)
        tab = st.radio("", ["Accedi", "Registrati"], horizontal=True, label_visibility="collapsed")
        if tab == "Accedi":
            username = st.text_input("👤 Username", key="login_user")
            password = st.text_input("🔑 Password", type="password", key="login_pass")
            if st.button("🚀 Accedi", use_container_width=True, type="primary"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Username o password errati")
        else:
            reg_user = st.text_input("👤 Username", key="reg_user")
            reg_pass = st.text_input("🔑 Password", type="password", key="reg_pass")
            reg_confirm = st.text_input("🔑 Conferma password", type="password", key="reg_confirm")
            if st.button("📝 Registrati", use_container_width=True, type="primary"):
                if not reg_user or not reg_pass:
                    st.error("❌ Compila tutti i campi")
                elif reg_pass != reg_confirm:
                    st.error("❌ Le password non coincidono")
                elif len(reg_pass) < 4:
                    st.error("❌ Password troppo corta (min 4 caratteri)")
                else:
                    uid = create_user(reg_user, reg_pass)
                    if uid:
                        st.session_state.user = {"id": uid, "username": reg_user}
                        st.rerun()
                    else:
                        st.error("❌ Username già esistente")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Logout in sidebar ─────────────────────────────────────

# ── Header ─────────────────────────────────────────────────
st.title("🤖 MLPG Tutor con Streamlit")
st.markdown("✨ Genera un percorso personalizzato, valuta le tue soluzioni e chiedi chiarimenti mirati.")

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    col_user, col_logout = st.columns([2, 1])
    with col_user:
        st.caption(f"👤 {st.session_state.user['username']}")
    with col_logout:
        if st.button("🚪", key="logout_btn"):
            st.session_state.user = None
            st.session_state.response = None
            st.session_state.modulo_archivio_aperto = None
            st.rerun()
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
                    sid = save_session(topic, level, [m.model_dump() for m in mods], st.session_state.user["id"])
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
    
    # ── Storico nella sidebar (compatto con gestione) ─────
    with st.expander("📜 Storico Percorsi", expanded=False):
        sessions = get_all_sessions(st.session_state.user["id"])
        if not sessions:
            st.info("📭 Ancora nessun percorso salvato.")
        else:
            for sess in sessions:
                sess_key_base = f"s_{sess['id']}"
                with st.expander(
                    f"📚 {sess['topic']} ({sess['level']}) — {sess['created_at'][:10]}",
                    expanded=False
                ):
                    st.caption(f"📅 Creato il {sess['created_at'][:19]}")
                    
                    # ── Riga controllo sessione ──
                    col_r, col_d = st.columns([1, 1])
                    with col_r:
                        rp = st.popover("✏️ Rinomina", key=f"rn_sess_{sess_key_base}")
                        with rp:
                            nuovo_nome = st.text_input(
                                "Nuovo nome", value=sess["topic"],
                                key=f"rni_sess_{sess_key_base}"
                            )
                            if st.button("💾 Salva", key=f"rns_sess_{sess_key_base}"):
                                rename_session(sess["id"], nuovo_nome)
                                st.rerun()
                    with col_d:
                        if st.button("🗑️ Elimina", key=f"del_sess_{sess_key_base}"):
                            delete_session(sess["id"])
                            st.rerun()
                    
                    if sess["riepilogo"]:
                        st.caption(f"📝 {sess['riepilogo'][:120]}…" if len(sess["riepilogo"]) > 120 else f"📝 {sess['riepilogo']}")
                    
                    # ── Lista moduli (apribili) ──
                    mods = get_session_modules(sess["id"])
                    if mods:
                        st.markdown("**Moduli:**")
                        for m in mods:
                            stato_icon = "✅" if m["completed"] else "📦" if m["archived"] else "⏳"
                            badge_cls = "completato" if m["completed"] else "archiviato" if m["archived"] else "sospeso"
                            badge_txt = "Fatto" if m["completed"] else "Arch." if m["archived"] else "Aperto"
                            col_i, col_t, col_a = st.columns([0.3, 2.6, 0.6])
                            with col_i:
                                st.markdown(stato_icon)
                            with col_t:
                                st.markdown(
                                    f"{m['titolo'][:25]} <span class='badge badge-{badge_cls}'>{badge_txt}</span>",
                                    unsafe_allow_html=True,
                                )
                            with col_a:
                                if st.button("▶", key=f"apri_mod_{sess_key_base}_{m['id']}"):
                                    st.session_state.modulo_archivio_aperto = {
                                        "id": str(m["id"]),
                                        "session_id": sess["id"],
                                        "topic": sess["topic"],
                                        "livello": sess["level"],
                                        "titolo": m["titolo"],
                                        "spiegazione": m["spiegazione"],
                                        "esercizio": m["esercizio"],
                                        "ultima_soluzione": "",
                                    }
                                    st.session_state.hint_corrente = None
                                    st.rerun()
                        
                        # ── Gestione moduli ──
                        st.markdown("---")
                        st.markdown("**🔧 Gestione Moduli**")
                        opts = {
                            f"Modulo {m['module_index']+1}: {m['titolo'][:35]}": m
                            for m in mods
                        }
                        sel_label = st.selectbox(
                            "Seleziona modulo",
                            list(opts.keys()),
                            key=f"sel_mod_{sess_key_base}",
                            label_visibility="collapsed",
                        )
                        sel_mod = opts[sel_label]
                        
                        cur_stato = (
                            "completato" if sel_mod["completed"]
                            else "archiviato" if sel_mod["archived"]
                            else "in sospeso"
                        )
                        nuovo_stato = st.selectbox(
                            "Stato",
                            ["in sospeso", "completato"],
                            index=0 if cur_stato == "in sospeso" else 1,
                            key=f"st_mod_{sess_key_base}_{sel_mod['id']}",
                        )
                        if nuovo_stato != cur_stato:
                            update_module_state(
                                sel_mod["id"],
                                completed=(nuovo_stato == "completato"),
                                archived=False,
                            )
                            st.rerun()
                        
                        col_ren, col_del_m = st.columns([1, 1])
                        with col_ren:
                            rp_m = st.popover("✏️ Rinomina modulo", key=f"rn_mod_{sess_key_base}_{sel_mod['id']}")
                            with rp_m:
                                nuovo_titolo = st.text_input(
                                    "Titolo", value=sel_mod["titolo"],
                                    key=f"rni_mod_{sess_key_base}_{sel_mod['id']}",
                                )
                                if st.button("💾", key=f"rns_mod_{sess_key_base}_{sel_mod['id']}"):
                                    rename_module(sel_mod["id"], nuovo_titolo)
                                    st.rerun()
                        with col_del_m:
                            if st.button("🗑️ Elimina modulo", key=f"del_mod_{sess_key_base}_{sel_mod['id']}"):
                                delete_module(sel_mod["id"])
                                st.rerun()
                        
                        # ── Tentativi del modulo selezionato ──
                        attempts = get_module_attempts(sel_mod["id"])
                        if attempts:
                            with st.expander("📋 Tentativi", expanded=False):
                                for att in attempts[-3:]:
                                    esito_icon = (
                                        "✅" if att["esito"] == "corretta"
                                        else "⚠️" if att["esito"] == "parziale"
                                        else "❌"
                                    )
                                    st.caption(f"{esito_icon} {att['created_at'][:16]}")

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

# ── vista modulo storico ───────────────────────────────────
if st.session_state.modulo_archivio_aperto:
    arch = st.session_state.modulo_archivio_aperto

    # ── Navigazione tra moduli della stessa sessione ──
    session_id = arch.get("session_id")
    mods_in_session = get_session_modules(session_id) if session_id else []
    current_mod_id = int(arch["id"])
    current_idx = next(
        (i for i, m in enumerate(mods_in_session) if m["id"] == current_mod_id),
        -1,
    )

    col_back, col_nav, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅️ Torna", use_container_width=True):
            st.session_state.modulo_archivio_aperto = None
            st.rerun()
    with col_nav:
        if session_id and current_idx >= 0:
            st.markdown(
                f"<div style='text-align:center'>📚 <strong>{arch.get('topic', '')}</strong> — "
                f"Modulo {current_idx+1}/{len(mods_in_session)}</div>",
                unsafe_allow_html=True,
            )
    with col_next:
        if session_id and current_idx < len(mods_in_session) - 1:
            if st.button("▶ Successivo", use_container_width=True):
                m = mods_in_session[current_idx + 1]
                st.session_state.modulo_archivio_aperto = {
                    "id": str(m["id"]),
                    "session_id": session_id,
                    "topic": arch["topic"],
                    "livello": arch["livello"],
                    "titolo": m["titolo"],
                    "spiegazione": m["spiegazione"],
                    "esercizio": m["esercizio"],
                    "ultima_soluzione": "",
                }
                st.session_state.hint_corrente = None
                st.rerun()

    if arch.get("topic"):
        st.info(f"📚 **Argomento:** {arch['topic']} ({arch.get('livello', '')})")
    
    st.markdown(f"#### 📖 {arch.get('titolo', 'Modulo')}")

    # ── Recupera risposta già data ──
    existing_answer = ""
    mod_completato = False
    if arch["id"] in st.session_state.risposte_utente:
        existing_answer = st.session_state.risposte_utente[arch["id"]]["soluzione"]
        mod_completato = True
    else:
        tentativi = get_module_attempts(int(arch["id"]))
        for att in reversed(tentativi):
            if att["esito"] == "corretta":
                existing_answer = att["soluzione"]
                mod_completato = True
                st.session_state.risposte_utente[arch["id"]] = {
                    "esercizio": arch["esercizio"],
                    "soluzione": existing_answer,
                }
                break

    if mod_completato:
        st.success("✅ Modulo già completato — ecco la tua risposta")

    col_spiega, col_esercizio = st.columns([1, 1])
    with col_spiega:
        st.markdown("**Spiegazione:**")
        st.markdown(arch.get("spiegazione", ""))
    with col_esercizio:
        st.markdown("**Esercizio:**")
        st.markdown(arch.get("esercizio", ""))

    st.markdown("---")

    solution = st.text_area("💭 La tua soluzione", value=existing_answer, key=f"soluzione_arch_{arch['id']}", height=150)
    if st.button("✅ Valuta soluzione", key=f"valuta_arch_{arch['id']}", use_container_width=True, type="primary"):
        if not solution:
            st.error("❌ Inserisci una soluzione prima di valutare.")
        else:
            try:
                with st.spinner("⏳ Valutazione in corso..."):
                    feedback = valuta_risposta(arch["esercizio"], solution)
                st.session_state.feedbacks[arch["id"]] = feedback

                if feedback.esito in ("sbagliata", "parziale"):
                    hint = genera_hint(arch["esercizio"], solution, arch.get("livello", "base"), 1)
                    st.session_state.hint_corrente = hint
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
                    try:
                        db_id = int(arch["id"])
                        save_attempt(db_id, solution, "corretta", feedback.model_dump_json())
                        update_module_state(db_id, completed=True)
                    except (ValueError, Exception):
                        pass
                    st.success("🎉 Risposta corretta!")
            except Exception as exc:
                st.error(f"❌ Errore nella valutazione: {exc}")

    # ── Feedback persistente ──
    if arch["id"] in st.session_state.feedbacks:
        feedback = st.session_state.feedbacks[arch["id"]]
        st.markdown("---")
        col_comment, col_suggest = st.columns(2)
        with col_comment:
            st.markdown("**💡 Commento costruttivo:**")
            st.write(feedback.commento_costruttivo)
        with col_suggest:
            st.markdown("**🎯 Suggerimento di miglioramento:**")
            st.write(feedback.suggerimento_miglioramento)

    # ── Hint persistente ──
    if st.session_state.hint_corrente and arch["id"] in st.session_state.feedbacks:
        fb_esito = st.session_state.feedbacks[arch["id"]].esito
        if fb_esito in ("sbagliata", "parziale"):
            st.markdown("---")
            st.warning(f"💡 **Suggerimento:** {st.session_state.hint_corrente}")

    st.markdown("---")
    st.markdown("#### 🤔 Chiedi chiarimenti mirati")
    dubbio = st.text_area("Quale parte non ti è chiara?", key=f"dubbio_arch_{arch['id']}", height=100)
    if st.button("💬 Genera spiegazione mirata", key=f"clarify_arch_{arch['id']}", use_container_width=True):
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

    col_torna_bottom, _ = st.columns([1, 1])
    with col_torna_bottom:
        if st.button("⬅️ Torna", key=f"torna_arch_{arch['id']}", use_container_width=True):
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

    # ── Barra di avanzamento ──────────────────────────────
    totali = len(modules)
    completati = len(st.session_state.risposte_utente)
    if totali > 0:
        st.progress(completati / totali)
        st.caption(f"📊 {completati}/{totali} moduli completati")

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
        st.markdown(module.spiegazione)
    
    with col_esercizio:
        st.markdown("**Esercizio:**")
        st.markdown(module.esercizio_pratico)

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
