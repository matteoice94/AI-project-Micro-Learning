import sys
import json
import hashlib
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

import streamlit as st
from src.generator import (
    generate_microlearning_path,
    valuta_con_pipeline,
    valuta_risposta,
    genera_hint,
    genera_spiegazione_alternativa,
    genera_riepilogo_finale,
    traduci_percorso_completo,
    traduci_modulo_singolo,
)
from src.robot_display import get_robot_path, robot_html
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
    award_user_xp,
    track_wrong_answer,
    get_user_stats,
    get_leaderboard,
    get_user_topic_stats,
    get_user_accuracy,
    get_user_weekly_activity,
    backfill_user_stats,
)
from src.config import RAG_TOP_K
from src.i18n import tr, SUPPORTED_LANGS
from src.gamification import xp_to_next_level, level_from_xp, badge_info, BADGES

st.set_page_config(
    page_title=tr("page_title"),
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

    /* ── Session card nella pagina storico ── */
    .session-card {
        background: linear-gradient(145deg, #141e30, #1a2332);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .session-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── init DB ────────────────────────────────────────────────
if "db_init" not in st.session_state:
    init_db()
    st.session_state.db_init = True

if "db_backfill" not in st.session_state:
    try:
        backfill_user_stats()
    except Exception:
        pass
    st.session_state.db_backfill = True

# ── session state ──────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "it"
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
if "_migrated_archiviati" not in st.session_state:
    st.session_state._migrated_archiviati = False
if "response_lang" not in st.session_state:
    st.session_state.response_lang = "it"
if "archiviati_lang" not in st.session_state:
    st.session_state.archiviati_lang = "it"
if "translated_cache" not in st.session_state:
    st.session_state.translated_cache = {}

# ── migrazione archiviati vecchi (eseguita una sola volta) ──
if not st.session_state._migrated_archiviati and st.session_state.moduli_archiviati:
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
    st.session_state._migrated_archiviati = True


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


def _lang():
    return st.session_state.get("lang", "it")


def _award_correct(reason: str, topic: str = "", first_try: bool = True):
    """Award XP for correct answers and show badge notifications."""
    user_id = st.session_state.user.get("id") if st.session_state.user else None
    xp, badges = award_user_xp(user_id, reason, topic, first_try)
    if badges:
        for b in badges:
            info = badge_info(b, _lang())
            st.toast(f"{info['icon']} {tr('new_badge_unlocked', _lang())}: {info['name']}!", icon="🎉")
    if xp > 0:
        st.toast(tr("xp_earned", _lang(), count=xp), icon="⚡")


def _award_wrong():
    """Track wrong answers for accuracy."""
    user_id = st.session_state.user.get("id") if st.session_state.user else None
    track_wrong_answer(user_id)


def _award_path_complete(topic: str = ""):
    """Award XP for completing a full path."""
    user_id = st.session_state.user.get("id") if st.session_state.user else None
    xp, badges = award_user_xp(user_id, "path_completed", topic, True)
    if badges:
        for b in badges:
            info = badge_info(b, _lang())
            st.toast(f"{info['icon']} {tr('new_badge_unlocked', _lang())}: {info['name']}!", icon="🎉")


@st.cache_data(ttl="30s")
def _cached_sessions(user_id: int | None):
    return get_all_sessions(user_id)


@st.cache_data(ttl="30s")
def _cached_modules(sid: int):
    return get_session_modules(sid)


@st.cache_data(ttl="30s")
def _cached_attempts(module_id: int):
    return get_module_attempts(module_id)


@st.cache_data(ttl="60s")
def _cached_similar(topic: str, top_k: int):
    return find_similar_modules(topic, top_k=top_k)


def _sync_lang(new_lang: str):
    """Traduce moduli attivi e archiviati quando la lingua cambia."""
    old_lang = st.session_state.get("lang", "it")
    if new_lang == old_lang:
        return
    st.session_state.lang = new_lang

    # ── Traduci percorso attivo ──
    if st.session_state.response and st.session_state.response_lang != new_lang:
        try:
            response = st.session_state.response
            moduli_orig = [m.model_dump() for m in response.percorso_studio.moduli]
            objective_orig = response.percorso_studio.metadati.objective_apprendimento
            with st.spinner(tr("translating_modules", new_lang)):
                moduli_trad, obj_trad = traduci_percorso_completo(
                    moduli_orig, objective_orig, new_lang
                )
            if moduli_trad and obj_trad:
                for m_trad, m_orig in zip(moduli_trad, response.percorso_studio.moduli):
                    m_orig.titolo_modulo = m_trad.get("titolo_modulo", m_orig.titolo_modulo)
                    m_orig.spiegazione = m_trad.get("spiegazione", m_orig.spiegazione)
                    m_orig.esercizio_pratico = m_trad.get("esercizio_pratico", m_orig.esercizio_pratico)
                response.percorso_studio.metadati.objective_apprendimento = obj_trad
            st.session_state.response_lang = new_lang
        except Exception:
            pass

    # ── Traduci moduli archiviati (NON ultima_soluzione) ──
    if st.session_state.moduli_archiviati and st.session_state.archiviati_lang != new_lang:
        try:
            moduli_arch = st.session_state.moduli_archiviati
            with st.spinner(tr("translating_modules", new_lang)):
                moduli_trad, _ = traduci_percorso_completo(moduli_arch, None, new_lang)
            if moduli_trad:
                for m_trad, m_arch in zip(moduli_trad, moduli_arch):
                    m_arch["titolo"] = m_trad.get("titolo", m_trad.get("titolo_modulo", m_arch.get("titolo", "")))
                    m_arch["spiegazione"] = m_trad.get("spiegazione", m_arch.get("spiegazione", ""))
                    m_arch["esercizio"] = m_trad.get("esercizio", m_trad.get("esercizio_pratico", m_arch.get("esercizio", "")))
            st.session_state.archiviati_lang = new_lang
        except Exception:
            pass

    # Reset cache traduzioni storico
    st.session_state.translated_cache = {}
    _persist_session()


def _get_translated_db_module(module_id: str, original: dict, lang: str) -> dict:
    """Restituisce un modulo del DB tradotto nella lingua corrente (con cache).

    NON traduce mai la soluzione dell'utente (chiave 'ultima_soluzione').
    """
    cache = st.session_state.translated_cache

    if module_id not in cache:
        cache[module_id] = {}

    if lang not in cache[module_id]:
        translated = traduci_modulo_singolo(
            original.get("titolo", ""),
            original.get("spiegazione", ""),
            original.get("esercizio", ""),
            lang,
        )
        cache[module_id][lang] = translated

    return cache[module_id][lang]


def _translate_session_modules(mods: list[dict], lang: str) -> list[dict]:
    """Traduce in batch i titoli dei moduli di una sessione per la lista storico.

    Usa la cache; fa una sola chiamata LLM per i moduli non ancora tradotti.
    """
    if lang == "it":
        return mods

    cache = st.session_state.translated_cache
    to_translate = []
    for m in mods:
        mid = str(m["id"])
        if mid not in cache or lang not in cache[mid]:
            to_translate.append(m)

    if to_translate:
        try:
            translated_list, _ = traduci_percorso_completo(to_translate, None, lang)
            for m_orig, m_trad in zip(to_translate, translated_list):
                mid = str(m_orig["id"])
                cache.setdefault(mid, {})[lang] = {
                    "titolo": m_trad.get("titolo", m_trad.get("titolo_modulo", m_orig.get("titolo", ""))),
                    "spiegazione": m_trad.get("spiegazione", m_orig.get("spiegazione", "")),
                    "esercizio": m_trad.get("esercizio", m_trad.get("esercizio_pratico", m_orig.get("esercizio", ""))),
                }
        except Exception:
            for m in to_translate:
                mid = str(m["id"])
                cache.setdefault(mid, {})[lang] = {
                    "titolo": m.get("titolo", ""),
                    "spiegazione": m.get("spiegazione", ""),
                    "esercizio": m.get("esercizio", ""),
                }

    result = []
    for m in mods:
        mid = str(m["id"])
        if mid in cache and lang in cache[mid]:
            new_m = dict(m)
            new_m["titolo"] = cache[mid][lang]["titolo"]
            result.append(new_m)
        else:
            result.append(m)
    return result


# ── Session persistence (survives browser refresh) ──────────
SESSION_SECRET = "mlpg_2026_session"


def _make_session_token(user_id: int, username: str) -> str:
    sig = hashlib.sha256(f"{user_id}:{username}:{SESSION_SECRET}".encode()).hexdigest()[:12]
    payload = f"{user_id}:{username}:{sig}"
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _verify_session_token(token: str) -> tuple[int, str] | None:
    try:
        payload = base64.urlsafe_b64decode(token.encode()).decode()
        user_id_str, username, sig = payload.split(":", 2)
        expected = hashlib.sha256(f"{user_id_str}:{username}:{SESSION_SECRET}".encode()).hexdigest()[:12]
        if sig == expected:
            return int(user_id_str), username
    except Exception:
        pass
    return None


if not st.session_state.get("user") and not st.session_state.get("_session_checked"):
    st.session_state._session_checked = True
    token = st.query_params.get("session")
    if token:
        result = _verify_session_token(token)
        if result:
            uid, uname = result
            st.session_state.user = {"id": uid, "username": uname}
            st.session_state.lang = st.query_params.get("slang", "it")


def _persist_session():
    if st.session_state.user:
        uid = st.session_state.user["id"]
        uname = st.session_state.user["username"]
        token = _make_session_token(uid, uname)
        st.query_params["session"] = token
        st.query_params["slang"] = st.session_state.get("lang", "it")


# ── Login ──────────────────────────────────────────────────
if not st.session_state.user:
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .main .block-container { display: flex; justify-content: center; align-items: center; min-height: 90vh; }
    </style>
    """, unsafe_allow_html=True)
    lang = _lang()

    st.markdown("""
    <div style='position:fixed;top:16px;right:16px;z-index:1000;'>
    """, unsafe_allow_html=True)
    lang_icons = {"it": "🇮🇹 IT", "en": "🇬🇧 EN"}
    cols_lang = st.columns(len(SUPPORTED_LANGS))
    for i, l in enumerate(SUPPORTED_LANGS):
        with cols_lang[i]:
            if st.button(lang_icons[l], key=f"lang_{l}", use_container_width=True,
                         type="primary" if l == lang else "secondary"):
                _sync_lang(l)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.image(get_robot_path("neutral"), width=160)
        tab = st.radio(tr("login_title", lang), [tr("login_tab", lang), tr("register_tab", lang)],
                       horizontal=True, label_visibility="collapsed")
        if tab == tr("login_tab", lang):
            username = st.text_input(f"👤 {tr('username', lang)}", key="login_user")
            password = st.text_input(f"🔑 {tr('password', lang)}", type="password", key="login_pass")
            if st.button(f"🚀 {tr('login_tab', lang)}", use_container_width=True, type="primary"):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    _persist_session()
                    st.rerun()
                else:
                    st.error(f"❌ {tr('wrong_credentials', lang)}")
        else:
            reg_user = st.text_input(f"👤 {tr('username', lang)}", key="reg_user")
            reg_pass = st.text_input(f"🔑 {tr('password', lang)}", type="password", key="reg_pass")
            reg_confirm = st.text_input(f"🔑 {tr('confirm_password', lang)}", type="password", key="reg_confirm")
            if st.button(f"📝 {tr('register_tab', lang)}", use_container_width=True, type="primary"):
                if not reg_user or not reg_pass:
                    st.error(f"❌ {tr('fill_all_fields', lang)}")
                elif reg_pass != reg_confirm:
                    st.error(f"❌ {tr('passwords_mismatch', lang)}")
                elif len(reg_pass) < 4:
                    st.error(f"❌ {tr('password_too_short', lang)}")
                else:
                    uid = create_user(reg_user, reg_pass)
                    if uid:
                        st.session_state.user = {"id": uid, "username": reg_user}
                        _persist_session()
                        st.rerun()
                    else:
                        st.error(f"❌ {tr('username_exists', lang)}")
    st.stop()


# ══════════════════════════════════════════════════════════════
# Shared: vista modulo archivio (usata da entrambe le pagine)
# ══════════════════════════════════════════════════════════════
def _render_modulo_archivio():
    arch = st.session_state.modulo_archivio_aperto
    lang = _lang()

    # ── Traduci modulo dal DB se necessario (NON tradurre ultima_soluzione) ──
    if arch.get("_from_db") and lang != "it":
        module_id = str(arch["id"])
        translated = _get_translated_db_module(module_id, arch, lang)
        arch = dict(arch)
        arch["titolo"] = translated.get("titolo", arch.get("titolo", ""))
        arch["spiegazione"] = translated.get("spiegazione", arch.get("spiegazione", ""))
        arch["esercizio"] = translated.get("esercizio", arch.get("esercizio", ""))

    session_id = arch.get("session_id")
    mods_in_session = _cached_modules(session_id) if session_id else []
    current_mod_id = int(arch["id"])
    current_idx = next(
        (i for i, m in enumerate(mods_in_session) if m["id"] == current_mod_id),
        -1,
    )

    col_back, col_nav, col_next = st.columns([1, 2, 1])
    with col_back:
        if st.button(f"⬅️ {tr('back', lang)}", use_container_width=True):
            st.session_state.modulo_archivio_aperto = None
            st.rerun()
    with col_nav:
        if session_id and current_idx >= 0:
            st.markdown(
                f"<div style='text-align:center'>📚 <strong>{arch.get('topic', '')}</strong> — "
                f"{tr('module_n', lang)} {current_idx+1}/{len(mods_in_session)}</div>",
                unsafe_allow_html=True,
            )
    with col_next:
        if session_id and current_idx < len(mods_in_session) - 1:
            if st.button(f"▶ {tr('next', lang)}", use_container_width=True):
                m = mods_in_session[current_idx + 1]
                st.session_state.modulo_archivio_aperto = {
                    "id": str(m["id"]),
                    "_from_db": True,
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
        st.info(f"📚 **{tr('sidebar_topic', lang)}:** {arch['topic']} ({arch.get('livello', '')})")

    st.markdown(f"#### 📖 {arch.get('titolo', tr('module_n', lang))}")

    existing_answer = ""
    mod_completato = False
    if arch["id"] in st.session_state.risposte_utente:
        existing_answer = st.session_state.risposte_utente[arch["id"]]["soluzione"]
        mod_completato = True
    else:
        tentativi = _cached_attempts(int(arch["id"]))
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
        st.success(f"✅ {tr('already_completed', lang)}")

    col_spiega, col_esercizio = st.columns([1, 1])
    with col_spiega:
        st.markdown(f"**{tr('explanation', lang)}:**")
        st.markdown(arch.get("spiegazione", ""))
    with col_esercizio:
        st.markdown(f"**{tr('exercise', lang)}:**")
        st.markdown(arch.get("esercizio", ""))

    st.markdown("---")

    solution = st.text_area(f"💭 {tr('your_solution', lang)}", value=existing_answer,
                            key=f"soluzione_arch_{arch['id']}", height=150)
    if st.button(f"✅ {tr('evaluate_solution', lang)}", key=f"valuta_arch_{arch['id']}",
                 use_container_width=True, type="primary"):
        if not solution:
            st.error(f"❌ {tr('insert_solution_first', lang)}")
        else:
            try:
                with st.spinner(f"⏳ {tr('evaluating_spinner', lang)}"):
                    feedback = valuta_risposta(arch["esercizio"], solution, lang)
                st.session_state.feedbacks[arch["id"]] = feedback

                if feedback.esito in ("sbagliata", "parziale"):
                    hint = genera_hint(arch["esercizio"], solution, arch.get("livello", "base"), 1, lang)
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
                    st.success(f"🎉 {tr('correct_answer', lang)}")
                    _award_correct("module_completed", arch.get("topic", ""), True)
            except Exception as exc:
                st.error(f"❌ {tr('eval_error', lang)}: {exc}")

    _, col_r, _ = st.columns([1, 1, 1])
    with col_r:
        if arch["id"] in st.session_state.feedbacks:
            fb = st.session_state.feedbacks[arch["id"]]
            if fb.esito == "corretta":
                st.image(get_robot_path("happy"), width=140)
            else:
                st.image(get_robot_path("neutral"), width=140)
        else:
            st.image(get_robot_path("neutral"), width=140)

    if arch["id"] in st.session_state.feedbacks:
        feedback = st.session_state.feedbacks[arch["id"]]
        st.markdown("---")
        col_comment, col_suggest = st.columns(2)
        with col_comment:
            st.markdown(f"**💡 {tr('constructive_comment', lang)}:**")
            st.write(feedback.commento_costruttivo)
        with col_suggest:
            st.markdown(f"**🎯 {tr('improvement_suggestion', lang)}:**")
            st.write(feedback.suggerimento_miglioramento)

    if st.session_state.hint_corrente and arch["id"] in st.session_state.feedbacks:
        fb_esito = st.session_state.feedbacks[arch["id"]].esito
        if fb_esito in ("sbagliata", "parziale"):
            st.markdown("---")
            st.warning(f"💡 **{tr('hint_label', lang)}:** {st.session_state.hint_corrente}")

    st.markdown("---")
    st.markdown(f"#### 🤔 {tr('ask_clarification', lang)}")
    dubbio = st.text_area(tr("which_part_unclear", lang), key=f"dubbio_arch_{arch['id']}", height=100)
    if st.button(f"💬 {tr('generate_targeted_explanation', lang)}",
                 key=f"clarify_arch_{arch['id']}", use_container_width=True):
        if not dubbio:
            st.error(f"❌ {tr('enter_doubt_first', lang)}")
        else:
            try:
                with st.spinner(f"⏳ {tr('clarification_spinner', lang)}"):
                    clar = genera_spiegazione_alternativa(arch["titolo"], arch["spiegazione"],
                                                          dubbio, arch.get("livello", "base"), lang)
                col_1, col_2 = st.columns(2)
                with col_1:
                    st.markdown(f"**📝 {tr('simplified_explanation', lang)}**")
                    st.write(clar.get("spiegazione_semplificata", ""))
                with col_2:
                    st.markdown(f"**🔧 {tr('practical_example', lang)}**")
                    st.write(clar.get("esempio_pratico", ""))
                if clar.get("passaggi"):
                    st.markdown(f"**📋 {tr('suggested_steps', lang)}**")
                    for item in clar.get("passaggi", []):
                        st.write(f"- {item}")
            except Exception as exc:
                st.error(f"❌ {tr('clarify_error', lang)}: {exc}")

    col_torna_bottom, _ = st.columns([1, 1])
    with col_torna_bottom:
        if st.button(f"⬅️ {tr('back', lang)}", key=f"torna_arch_{arch['id']}", use_container_width=True):
            st.session_state.modulo_archivio_aperto = None
            st.rerun()


# ══════════════════════════════════════════════════════════════
# Page: Nuovo Percorso
# ══════════════════════════════════════════════════════════════
def nuovo_percorso_page():
    lang = _lang()
    st.title(f"🤖 {tr('app_main_title', lang)}")
    st.markdown(f"✨ {tr('path_description', lang)}")

    if st.session_state.modulo_archivio_aperto:
        _render_modulo_archivio()

    elif st.session_state.response:
        response = st.session_state.response
        modules = response.percorso_studio.moduli
        objective = response.percorso_studio.metadati.objective_apprendimento
        livello = response.percorso_studio.metadati.difficolta_impostata
        topic_val = st.session_state.get("topic", "")

        st.markdown("---")

        st.markdown(f"### 🎯 {tr('learning_objective', lang)}")
        st.info(objective)

        totali = len(modules)
        completati = len(st.session_state.risposte_utente)
        if totali > 0:
            st.progress(min(completati / totali, 1.0))
            st.caption(f"📊 {completati}/{totali} {tr('modules_completed', lang)}")

        st.markdown("---")

        module_labels = [f"{tr('module_n', lang)} {idx+1}: {mod.titolo_modulo}" for idx, mod in enumerate(modules)]
        selected_idx = st.selectbox(f"📚 {tr('select_module', lang)}", range(len(modules)),
                                    format_func=lambda x: module_labels[x], key="selected_module")
        module = modules[selected_idx]

        id_modulo = str(module.id)
        is_archived = any(a["id"] == id_modulo and a.get("topic", "") == (topic_val or "")
                          for a in st.session_state.moduli_archiviati)

        if is_archived:
            st.warning(f"⚠️ {tr('already_attempted', lang)}")

        st.markdown(f"#### 📖 {tr('module_n', lang)} {module.id}: {module.titolo_modulo}")

        col_spiega, col_esercizio = st.columns([1, 1])

        with col_spiega:
            st.markdown(f"**{tr('explanation', lang)}:**")
            st.markdown(module.spiegazione)

        with col_esercizio:
            st.markdown(f"**{tr('exercise', lang)}:**")
            st.markdown(module.esercizio_pratico)

        st.markdown("---")

        solution = st.text_area(f"💭 {tr('your_solution', lang)}", key=f"solution_{module.id}", height=150)
        if st.button(f"✅ {tr('evaluate_solution', lang)}", key=f"valuta_{module.id}",
                     use_container_width=True, type="primary"):
            if not solution:
                st.error(f"❌ {tr('insert_solution_first', lang)}")
            else:
                st.session_state._robot_eval = (id_modulo, solution)
                st.rerun()

        _, col_r, _ = st.columns([1, 1, 1])
        with col_r:
            task = st.session_state.pop("_robot_eval", None)
            if task and task[0] == id_modulo:
                st.image(get_robot_path("thinking"), width=140)
                _sol = task[1]

                # Pipeline condivisa: heuristic → sanity → LLM eval → hint
                pipeline = valuta_con_pipeline(
                    module.esercizio_pratico, _sol, livello, lang,
                    tentativi=st.session_state.tentativi_modulo.get(id_modulo, 0),
                )

                if not pipeline["valido"]:
                    st.warning(f"⚠️ {pipeline['message']}")
                    st.session_state._robot_eval_done = id_modulo
                else:
                    feedback = pipeline["feedback"]
                    st.session_state.feedbacks[module.id] = feedback

                    if feedback.esito in ("sbagliata", "parziale"):
                        ultima = st.session_state.ultima_risposta_modulo.get(id_modulo)
                        if ultima is not None and ultima == _sol:
                            st.warning(f"⚠️ {tr('same_answer_warning', lang)}")
                        else:
                            tentativi = st.session_state.tentativi_modulo.get(id_modulo, 0) + 1
                            st.session_state.tentativi_modulo[id_modulo] = tentativi
                            st.session_state.ultima_risposta_modulo[id_modulo] = _sol

                            db_id = st.session_state.module_db_ids.get(id_modulo)
                            if db_id:
                                save_attempt(db_id, _sol, feedback.esito, feedback.model_dump_json())
                            _award_wrong()

                            if pipeline["archive"]:
                                st.session_state.moduli_archiviati.append({
                                    "id": id_modulo,
                                    "topic": topic_val,
                                    "livello": livello,
                                    "titolo": module.titolo_modulo,
                                    "spiegazione": module.spiegazione,
                                    "esercizio": module.esercizio_pratico,
                                    "ultima_soluzione": _sol,
                                })
                                st.session_state.diario_note.append(
                                    f"{tr('diary_module_prefix', lang)} {module.id} ({module.titolo_modulo}): "
                                    f"{tr('diary_archived_after', lang, count=tentativi)}"
                                )
                                if db_id:
                                    update_module_state(db_id, archived=True)
                                st.warning(f"📦 {tr('module_archived_after', lang, count=tentativi)}")
                                st.rerun()
                            elif pipeline["hint"]:
                                st.session_state.hint_corrente = pipeline["hint"]

                    else:
                        st.session_state.moduli_archiviati = [
                            a for a in st.session_state.moduli_archiviati
                            if not (a["id"] == id_modulo and a.get("topic", "") == (topic_val or ""))
                        ]
                        st.session_state.risposte_utente[id_modulo] = {
                            "esercizio": module.esercizio_pratico,
                            "soluzione": _sol,
                        }
                        db_id = st.session_state.module_db_ids.get(id_modulo)
                        if db_id:
                            save_attempt(db_id, _sol, "corretta", feedback.model_dump_json())
                            update_module_state(db_id, completed=True)
                        st.success(f"🎉 {tr('correct_answer', lang)}")
                        first_try = st.session_state.tentativi_modulo.get(id_modulo, 0) == 0
                        _award_correct("module_completed", topic_val, first_try)
                    st.session_state._robot_eval_done = id_modulo

            elif st.session_state.pop("_robot_eval_done", None) == id_modulo:
                fb = st.session_state.feedbacks.get(module.id)
                if fb and fb.esito == "corretta":
                    st.image(get_robot_path("happy"), width=140)
                else:
                    st.image(get_robot_path("neutral"), width=140)
            elif module.id in st.session_state.feedbacks:
                fb = st.session_state.feedbacks[module.id]
                if fb.esito == "corretta":
                    st.image(get_robot_path("happy"), width=140)
                else:
                    st.image(get_robot_path("neutral"), width=140)
            else:
                st.image(get_robot_path("neutral"), width=140)

        if module.id in st.session_state.feedbacks:
            feedback = st.session_state.feedbacks[module.id]
            st.markdown("---")
            col_comment, col_suggest = st.columns(2)
            with col_comment:
                st.markdown(f"**💡 {tr('constructive_comment', lang)}:**")
                st.write(feedback.commento_costruttivo)
            with col_suggest:
                st.markdown(f"**🎯 {tr('improvement_suggestion', lang)}:**")
                st.write(feedback.suggerimento_miglioramento)

        if st.session_state.hint_corrente:
            if module.id in st.session_state.feedbacks:
                fb_esito = st.session_state.feedbacks[module.id].esito
                if fb_esito in ("sbagliata", "parziale"):
                    st.markdown("---")
                    st.warning(f"💡 **{tr('hint_label', lang)}:** {st.session_state.hint_corrente}")

        st.markdown("---")
        st.markdown(f"#### 🤔 {tr('ask_clarification', lang)}")
        dubbio = st.text_area(tr("which_part_unclear", lang), key=f"dubbio_{module.id}", height=100)
        if st.button(f"💬 {tr('generate_targeted_explanation', lang)}",
                     key=f"clarify_{module.id}", use_container_width=True):
            if not dubbio:
                st.error(f"❌ {tr('enter_doubt_first', lang)}")
            else:
                st.session_state._robot_clarify = (id_modulo, dubbio)
                st.rerun()

        _, col_rc, _ = st.columns([1, 1, 1])
        with col_rc:
            task_cl = st.session_state.pop("_robot_clarify", None)
            if task_cl and task_cl[0] == id_modulo:
                st.image(get_robot_path("thinking"), width=140)
                _dubbio = task_cl[1]
                try:
                    clar = genera_spiegazione_alternativa(module.titolo_modulo, module.spiegazione,
                                                          _dubbio, livello, lang)
                    st.session_state._clar_result = (id_modulo, clar, _dubbio)
                except Exception as exc:
                    st.error(f"❌ {tr('clarify_error', lang)}: {exc}")
                    st.session_state._clar_result = None

            clar_data = st.session_state.pop("_clar_result", None)
            if clar_data and clar_data[0] == id_modulo:
                clar, _dubbio_stored = clar_data[1], clar_data[2]
                st.image(get_robot_path("happy"), width=100)
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown(f"**📝 {tr('simplified_explanation', lang)}**")
                    st.write(clar.get("spiegazione_semplificata", ""))
                with col_right:
                    st.markdown(f"**🔧 {tr('practical_example', lang)}**")
                    st.write(clar.get("esempio_pratico", ""))
                if clar.get("passaggi"):
                    st.markdown(f"**📋 {tr('suggested_steps', lang)}**")
                    for item in clar.get("passaggi", []):
                        st.write(f"- {item}")
                st.session_state.diario_note.append(
                    f"{tr('diary_module_prefix', lang)} {module.id} ({module.titolo_modulo}): {_dubbio_stored}"
                )
                st.session_state.interruzione_dubbio = True

        st.markdown("---")
        st.markdown(f"#### 📊 {tr('final_summary', lang)}")
        st.write(f"**{tr('starting_level', lang)}:** {livello}")

        if module.id == modules[-1].id:
            if st.button(f"📝 {tr('generate_final_summary', lang)}", key="genera_riepilogo_finale",
                         use_container_width=True, type="primary"):
                tutte_risposte = list(st.session_state.risposte_utente.values())
                if not tutte_risposte and not st.session_state.moduli_archiviati:
                    st.error(f"❌ {tr('insert_at_least_one_solution', lang)}")
                else:
                    try:
                        with st.spinner(f"⏳ {tr('summary_generating', lang)}"):
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
                                lang,
                            )
                            st.session_state.final_summary = riepilogo
                            sid = st.session_state.current_session_id
                            if sid:
                                save_riepilogo(sid, riepilogo.model_dump_json())
                        st.success(f"✅ {tr('summary_generated', lang)}")
                        _award_path_complete(topic_val)
                        st.image(get_robot_path("happy"), width=100)
                    except Exception as exc:
                        st.error(f"❌ {tr('summary_error', lang)}: {exc}")

            if st.session_state.final_summary:
                riepilogo = st.session_state.final_summary
                st.markdown("---")
                st.markdown(f"### 📋 {tr('final_results', lang)}")

                col_strengths, col_improvements = st.columns(2)

                with col_strengths:
                    st.success(f"✅ **{tr('strengths', lang)}:**")
                    if riepilogo.punti_di_forza:
                        for point in riepilogo.punti_di_forza:
                            st.write(f"🌟 {point}")
                    else:
                        st.write(f"- {tr('no_strengths', lang)}")

                with col_improvements:
                    st.info(f"📈 **{tr('improvements', lang)}:**")
                    if riepilogo.punti_da_migliorare:
                        for point in riepilogo.punti_da_migliorare:
                            st.write(f"🎯 {point}")
                    else:
                        st.write(f"- {tr('no_improvements', lang)}")

                st.markdown("---")
                st.markdown(f"**📝 {tr('logbook', lang)}:**")
                st.write(riepilogo.diario_di_bordo or f"- {tr('no_notes', lang)}")

                st.markdown("---")
                st.markdown(f"**🎊 {tr('farewell', lang)}:**")
                st.write(riepilogo.saluto_conclusivo or f"- {tr('no_greeting', lang)}")
            else:
                st.info(f"💭 {tr('summary_hint', lang, count=totali)}")
        else:
            st.info(f"📌 {tr('summary_later', lang)}")

    # ── Pagina di benvenuto ──────────────────────────────────
    else:
        st.markdown("---")
        _, col_robot, _ = st.columns([1, 1, 1])
        with col_robot:
            st.image(get_robot_path("neutral"), width=200)
        st.info(f"👋 {tr('welcome_message', lang)}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### 🎯 {tr('how_to_start', lang)}")
            st.write(f"""
1. {tr('how_to_start_1', lang)}
2. {tr('how_to_start_2', lang)}
3. {tr('how_to_start_3', lang)}
""")
        with col2:
            st.markdown(f"### 📚 {tr('how_it_works', lang)}")
            st.write(f"""
- {tr('how_it_works_1', lang)}
- {tr('how_it_works_2', lang)}
- {tr('how_it_works_3', lang)}
""")
        with col3:
            st.markdown(f"### 💡 {tr('tips', lang)}")
            st.write(f"""
- {tr('tip_1', lang)}
- {tr('tip_2', lang)}
- {tr('tip_3', lang)}
""")


# ══════════════════════════════════════════════════════════════
# Page: I Miei Percorsi
# ══════════════════════════════════════════════════════════════
def storico_page():
    lang = _lang()

    if st.session_state.modulo_archivio_aperto:
        _render_modulo_archivio()
        return

    st.title(f"📚 {tr('history_page', lang)}")
    st.markdown(tr('history_description', lang))

    sessions = _cached_sessions(st.session_state.user["id"])
    if not sessions:
        st.info(f"📭 {tr('no_sessions', lang)}")
        return

    for sess in sessions:
        sess_key_base = f"sp_{sess['id']}"

        with st.expander(
            f"📚 {sess['topic']} ({sess['level']}) — {sess['created_at'][:10]}",
            expanded=False,
        ):
            col_info, col_actions = st.columns([3, 1.5])
            with col_info:
                st.caption(f"📅 {tr('created_on', lang)} {sess['created_at'][:19]}")
            with col_actions:
                col_r, col_d = st.columns(2)
                with col_r:
                    rp = st.popover(f"✏️ {tr('rename', lang)}", key=f"rn_sess_{sess_key_base}")
                    with rp:
                        nuovo_nome = st.text_input(
                            tr('new_name', lang), value=sess["topic"],
                            key=f"rni_sess_{sess_key_base}",
                        )
                        if st.button(f"💾 {tr('save', lang)}", key=f"rns_sess_{sess_key_base}"):
                            rename_session(sess["id"], nuovo_nome)
                            st.rerun()
                with col_d:
                    del_pop = st.popover(f"🗑️ {tr('delete', lang)}",
                                         key=f"pop_del_sess_{sess_key_base}", use_container_width=True)
                    with del_pop:
                        st.warning(f"⚠️ {tr('delete_session_warning', lang)}")
                        if st.button(f"✅ {tr('confirm_delete', lang)}",
                                     key=f"conf_del_sess_{sess_key_base}", use_container_width=True):
                            delete_session(sess["id"])
                            st.rerun()

            if sess["riepilogo"]:
                riep_text = sess["riepilogo"]
                st.caption(
                    f"📝 {riep_text[:200]}…" if len(riep_text) > 200 else f"📝 {riep_text}"
                )

            mods = _cached_modules(sess["id"])
            if mods:
                mods = _translate_session_modules(mods, lang)
                st.markdown(f"**{tr('modules_label', lang)}:**")
                for m in mods:
                    stato_icon = "✅" if m["completed"] else "📦" if m["archived"] else "⏳"
                    badge_cls = "completato" if m["completed"] else "archiviato" if m["archived"] else "sospeso"
                    badge_txt = tr('completed', lang) if m["completed"] else tr('archived', lang) if m["archived"] else tr('pending', lang)

                    col_i, col_t, col_a = st.columns([0.3, 4.0, 0.5])
                    with col_i:
                        st.markdown(stato_icon)
                    with col_t:
                        st.markdown(
                            f"{m['titolo'][:45]} <span class='badge badge-{badge_cls}'>{badge_txt}</span>",
                            unsafe_allow_html=True,
                        )
                    with col_a:
                        if st.button("▶", key=f"apri_mod_{sess_key_base}_{m['id']}",
                                     help=tr('open_module', lang)):
                            st.session_state.modulo_archivio_aperto = {
                                "id": str(m["id"]),
                                "_from_db": True,
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

                st.markdown("---")
                st.markdown(f"**🔧 {tr('manage_modules', lang)}**")
                opts = {
                    f"{tr('module_n', lang)} {m['module_index']+1}: {m['titolo'][:35]}": m
                    for m in mods
                }
                sel_label = st.selectbox(
                    tr('select_module_label', lang),
                    list(opts.keys()),
                    key=f"sel_mod_{sess_key_base}",
                    label_visibility="collapsed",
                )
                sel_mod = opts[sel_label]

                cur_stato_idx = 1 if sel_mod["completed"] else 2 if sel_mod["archived"] else 0
                stati_labels = [tr("pending", lang), tr("completed", lang), tr("archived", lang)]
                nuovo_idx = st.selectbox(
                    tr('state', lang),
                    range(3),
                    format_func=lambda i: stati_labels[i],
                    index=cur_stato_idx,
                    key=f"st_mod_{sess_key_base}_{sel_mod['id']}",
                )
                if nuovo_idx != cur_stato_idx:
                    update_module_state(
                        sel_mod["id"],
                        completed=(nuovo_idx == 1),
                        archived=(nuovo_idx == 2),
                    )
                    st.rerun()

                col_ren, col_del_m = st.columns([1, 1])
                with col_ren:
                    rp_m = st.popover(f"✏️ {tr('rename_module_label', lang)}",
                                      key=f"rn_mod_{sess_key_base}_{sel_mod['id']}")
                    with rp_m:
                        nuovo_titolo = st.text_input(
                            tr('title', lang), value=sel_mod["titolo"],
                            key=f"rni_mod_{sess_key_base}_{sel_mod['id']}",
                        )
                        if st.button("💾", key=f"rns_mod_{sess_key_base}_{sel_mod['id']}"):
                            rename_module(sel_mod["id"], nuovo_titolo)
                            st.rerun()
                with col_del_m:
                    del_pop_m = st.popover(f"🗑️ {tr('delete_module_label', lang)}",
                                           key=f"pop_del_mod_{sess_key_base}_{sel_mod['id']}",
                                           use_container_width=True)
                    with del_pop_m:
                        st.warning(f"⚠️ {tr('delete_module_warning', lang)}")
                        if st.button(f"✅ {tr('confirm', lang)}",
                                     key=f"conf_del_mod_{sess_key_base}_{sel_mod['id']}",
                                     use_container_width=True):
                            delete_module(sel_mod["id"])
                            st.rerun()

                attempts_label = tr('attempts_label', lang)
                attempts = _cached_attempts(sel_mod["id"])
                if attempts:
                    with st.expander(f"📋 {attempts_label}", expanded=False):
                        for att in attempts[-3:]:
                            esito_icon = (
                                "✅" if att["esito"] == "corretta"
                                else "⚠️" if att["esito"] == "parziale"
                                else "❌"
                            )
                            st.caption(f"{esito_icon} {att['created_at'][:16]}")


# ══════════════════════════════════════════════════════════════
# Page: Obiettivi (gamification)
# ══════════════════════════════════════════════════════════════
def obiettivi_page():
    lang = _lang()
    user_id = st.session_state.user["id"]

    st.title(f"🏆 {tr('achievements_page', lang)}")

    stats = get_user_stats(user_id)
    xp = stats.get("xp", 0)
    lvl, needed, progress = xp_to_next_level(xp)
    accuracy = get_user_accuracy(user_id)

    col_lvl, col_xp, col_str, col_acc = st.columns(4)
    with col_lvl:
        st.metric(tr("your_level", lang), lvl)
    with col_xp:
        st.metric("XP", xp, delta=None)
    with col_str:
        st.metric(tr("current_streak", lang), f"{stats.get('current_streak', 0)} {tr('days', lang)}")
    with col_acc:
        st.metric(tr("accuracy_stat", lang), f"{accuracy:.0f}%")

    pct = min(int(progress / max(needed, 1) * 100), 100)
    st.progress(pct / 100)
    st.caption(f"{tr('xp_progress', lang)}: {progress}/{needed} XP → {tr('your_level', lang)} {lvl + 1}")

    # Badges
    st.markdown("---")
    st.markdown(f"### 🎖️ {tr('badges_title', lang)}")
    badges_list = stats.get("badges", "[]")
    badges_list = json.loads(badges_list) if isinstance(badges_list, str) else badges_list
    if badges_list:
        cols_b = st.columns(3)
        for i, bkey in enumerate(badges_list):
            info = badge_info(bkey, lang)
            with cols_b[i % 3]:
                st.markdown(f"**{info['icon']} {info['name']}**")
                st.caption(info["desc"])
    else:
        st.info(tr("no_badges_yet", lang))

    # Leaderboard
    st.markdown("---")
    st.markdown(f"### 🏅 {tr('leaderboard_title', lang)}")
    lb = get_leaderboard(10)
    if lb:
        for i, entry in enumerate(lb):
            col_r, col_u, col_x = st.columns([0.5, 3, 1.5])
            with col_r:
                st.markdown(f"**{i + 1}.**")
            with col_u:
                me = "**" if entry["username"] == st.session_state.user["username"] else ""
                st.markdown(f"{me}{entry['username']}{me}")
            with col_x:
                st.caption(f"⚡ {entry['xp']} XP · Lv {entry['level']}")
    else:
        st.info(tr("no_sessions", lang))


# ══════════════════════════════════════════════════════════════
# Page: Dashboard (analytics)
# ══════════════════════════════════════════════════════════════
def dashboard_page():
    lang = _lang()
    user_id = st.session_state.user["id"]

    st.title(f"📊 {tr('dashboard_page', lang)}")

    tab_perf, tab_learn = st.tabs([tr("dashboard_performance", lang), tr("dashboard_learning", lang)])

    with tab_perf:
        stats = get_user_stats(user_id)
        accuracy = get_user_accuracy(user_id)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(tr("total_correct_stat", lang), stats.get("total_correct", 0))
        with col2:
            st.metric(tr("total_wrong_stat", lang), stats.get("total_wrong", 0))
        with col3:
            st.metric(tr("modules_completed_stat", lang), stats.get("total_modules_completed", 0))
        with col4:
            st.metric(tr("paths_completed_stat", lang), stats.get("total_paths_completed", 0))

        st.markdown("---")
        total = max(stats.get("total_correct", 0) + stats.get("total_wrong", 0), 1)
        correct_pct = stats.get("total_correct", 0) / total * 100
        wrong_pct = stats.get("total_wrong", 0) / total * 100
        st.markdown(f"**{tr('accuracy_stat', lang)}:** {accuracy:.1f}%")
        st.progress(accuracy / 100)

        # Weekly activity
        st.markdown(f"**{tr('weekly_activity', lang)}**")
        weekly = get_user_weekly_activity(user_id)
        if weekly:
            import pandas as pd
            df = pd.DataFrame(weekly)
            df["day"] = pd.to_datetime(df["day"])
            df = df.set_index("day")
            st.bar_chart(df["count"], height=200)
        else:
            st.info(tr("no_activity_data", lang))

    with tab_learn:
        topics = get_user_topic_stats(user_id)
        if topics:
            import pandas as pd
            df_t = pd.DataFrame(topics)
            st.markdown(f"**{tr('topic_distribution', lang)}**")
            st.bar_chart(df_t.set_index("topic")["session_count"], height=250)
        else:
            st.info(tr("no_topic_data", lang))

        stats = get_user_stats(user_id)
        tl = stats.get("topics_studied", "[]")
        tl = json.loads(tl) if isinstance(tl, str) else tl
        if tl:
            st.markdown(f"**{tr('topics_studied', lang)}:** {', '.join(tl)}")


# ══════════════════════════════════════════════════════════════
# Navigation + Shared Sidebar
# ══════════════════════════════════════════════════════════════
lang = _lang()
nuovo_page = st.Page(nuovo_percorso_page, title=f"🏠 {tr('new_path_page', lang)}")
storico_page_item = st.Page(storico_page, title=f"📚 {tr('history_page', lang)}")
obiettivi_page_item = st.Page(obiettivi_page, title=f"🏆 {tr('achievements_page', lang)}")
dashboard_page_item = st.Page(dashboard_page, title=f"📊 {tr('dashboard_page', lang)}")
pg = st.navigation([nuovo_page, storico_page_item, obiettivi_page_item, dashboard_page_item])

with st.sidebar:
    st.markdown(robot_html("animated", 100), unsafe_allow_html=True)

    # Language selector
    lang_icons = {"it": f"🇮🇹 {tr('lang_italiano', lang)}", "en": f"🇬🇧 {tr('lang_english', lang)}"}
    cols_lang = st.columns(len(SUPPORTED_LANGS))
    for i, l_code in enumerate(SUPPORTED_LANGS):
        with cols_lang[i]:
            if st.button(lang_icons[l_code], key=f"sidebar_lang_{l_code}",
                         use_container_width=True,
                         type="primary" if l_code == lang else "secondary"):
                _sync_lang(l_code)
                st.rerun()

    col_user, col_logout = st.columns([2, 1])
    with col_user:
        st.caption(f"👤 {st.session_state.user['username']}")
    with col_logout:
        logout_pop = st.popover("🚪", key="logout_pop")
        with logout_pop:
            st.caption(tr('really_logout', lang))
            if st.button(f"✅ {tr('logout', lang)}", key="confirm_logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.response = None
                st.session_state.modulo_archivio_aperto = None
                st.query_params.clear()
                st.rerun()

    if pg.title == f"🏠 {tr('new_path_page', lang)}":
        st.header(f"⚙️ {tr('sidebar_config', lang)}")
        topic = st.text_input(f"🎯 {tr('sidebar_topic', lang)}", key="topic",
                              placeholder=tr('sidebar_topic_placeholder', lang))
        level = st.selectbox(f"📊 {tr('sidebar_level', lang)}",
                             ["", tr('base', lang), tr('intermediate', lang), tr('advanced', lang)],
                             key="level")
        name = st.text_input(f"👤 {tr('name_optional', lang)}", key="name",
                             placeholder=tr('sidebar_name_placeholder', lang))

        st.markdown("---")

        col_gen, col_reset = st.columns(2)
        with col_gen:
            generate_btn = st.button(f"🚀 {tr('sidebar_generate', lang)}", key="gen_btn",
                                     use_container_width=True, type="primary")
        with col_reset:
            if st.button(f"🔄 {tr('sidebar_new', lang)}", use_container_width=True):
                _reset_current_path()
                st.session_state.response = None
                st.session_state.show_history = False
                st.rerun()

        if generate_btn:
            if not topic or not level:
                st.error(f"❌ {tr('topic_level_required', lang)}")
            else:
                try:
                    with st.spinner(f"⏳ {tr('generating_spinner', lang)}"):
                        sim = _cached_similar(topic, RAG_TOP_K)
                        context = sim if sim else None

                        st.session_state.response = generate_microlearning_path(
                            topic, level, context_modules=context, lang=lang
                        )
                        st.session_state.response_lang = lang
                        st.session_state.archiviati_lang = lang
                        _reset_current_path()

                        mods = st.session_state.response.percorso_studio.moduli
                        sid = save_session(topic, level,
                                           [m.model_dump() for m in mods],
                                           st.session_state.user["id"])
                        st.session_state.current_session_id = sid

                        db_mods = _cached_modules(sid)
                        for dbm in db_mods:
                            st.session_state.module_db_ids[str(dbm["module_index"] + 1)] = dbm["id"]

                    st.success(f"✅ {tr('path_generated', lang)}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ {tr('generation_error', lang)}: {exc}")

        st.markdown("---")

    if st.session_state.moduli_archiviati:
        st.markdown(f"### 🔖 {tr('sidebar_archived', lang)}")
        for arch in st.session_state.moduli_archiviati:
            label = arch["titolo"]
            if arch.get("topic"):
                label += f" ({arch['topic']})"
            if st.button(f"🔹 {label}", key=f"go_arch_{arch['id']}_{arch.get('topic', '')}",
                         use_container_width=True):
                st.session_state.modulo_archivio_aperto = arch
                st.session_state.hint_corrente = None
                st.rerun()

pg.run()
