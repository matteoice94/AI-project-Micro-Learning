"""Sistema di gamification: XP, livelli, badge e streak."""

import json
from datetime import date, datetime

# ── Livelli ─────────────────────────────────────────────────
XP_PER_LEVEL = [
    0, 50, 120, 220, 350, 520, 740, 1020, 1370, 1800,
]

# ── Badge definitions ─────────────────────────────────────
BADGES = {
    "first_correct": {"icon": "🥇", "name_it": "Prima Risposta", "name_en": "First Answer",
                      "desc_it": "Prima risposta corretta", "desc_en": "First correct answer"},
    "student_5": {"icon": "📚", "name_it": "Studente", "name_en": "Student",
                  "desc_it": "5 moduli completati", "desc_en": "5 modules completed"},
    "graduate_15": {"icon": "🎓", "name_it": "Laureato", "name_en": "Graduate",
                    "desc_it": "15 moduli completati", "desc_en": "15 modules completed"},
    "perfectionist": {"icon": "🎯", "name_it": "Perfezionista", "name_en": "Perfectionist",
                      "desc_it": "3 risposte corrette di fila al primo tentativo",
                      "desc_en": "3 correct answers in a row on first try"},
    "unstoppable": {"icon": "🔥", "name_it": "Inarrestabile", "name_en": "Unstoppable",
                    "desc_it": "7 giorni di streak", "desc_en": "7 day streak"},
    "master": {"icon": "🏆", "name_it": "Maestro", "name_en": "Master",
               "desc_it": "Raggiunto livello 5", "desc_en": "Reached level 5"},
    "legend": {"icon": "💎", "name_it": "Leggenda", "name_en": "Legend",
               "desc_it": "Raggiunto livello 10", "desc_en": "Reached level 10"},
    "explorer": {"icon": "🗺️", "name_it": "Esploratore", "name_en": "Explorer",
                 "desc_it": "Studiati 3 topic diversi", "desc_en": "Studied 3 different topics"},
    "path_master": {"icon": "🏅", "name_it": "Percorso Completo", "name_en": "Path Master",
                    "desc_it": "Completato un intero percorso (3 moduli)",
                    "desc_en": "Completed a full path (3 modules)"},
    "centurion": {"icon": "🎯", "name_it": "Centenario", "name_en": "Centurion",
                  "desc_it": "100 risposte corrette totali", "desc_en": "100 total correct answers"},
    "polyglot": {"icon": "🌐", "name_it": "Poliglotta", "name_en": "Polyglot",
                 "desc_it": "Ha usato l'app in italiano e inglese", "desc_en": "Used the app in both Italian and English"},
    "encyclopedic": {"icon": "📖", "name_it": "Enciclopedico", "name_en": "Encyclopedic",
                     "desc_it": "10 moduli completati", "desc_en": "10 modules completed"},
    "collector": {"icon": "🎖️", "name_it": "Collezionista", "name_en": "Collector",
                  "desc_it": "5 badge diversi sbloccati", "desc_en": "5 different badges unlocked"},
    "sage": {"icon": "🧠", "name_it": "Saggio", "name_en": "Sage",
             "desc_it": "50 moduli completati", "desc_en": "50 modules completed"},
    "night_owl": {"icon": "🦉", "name_it": "Nottambulo", "name_en": "Night Owl",
                  "desc_it": "3 sessioni dopo le 22:00", "desc_en": "3 sessions after 10 PM"},
    "phoenix": {"icon": "🔥", "name_it": "Fenice", "name_en": "Phoenix",
                "desc_it": "Tornato dopo 7+ giorni di assenza", "desc_en": "Returned after 7+ days away"},
    "lightning": {"icon": "⚡", "name_it": "Fulmine", "name_en": "Lightning",
                  "desc_it": "10 risposte corrette di fila al primo tentativo",
                  "desc_en": "10 correct answers in a row on first try"},
    "perfect_module": {"icon": "💎", "name_it": "Modulo Perfetto", "name_en": "Perfect Module",
                       "desc_it": "Modulo completato con 0 errori", "desc_en": "Module completed with 0 mistakes"},
}


def xp_for_level(level: int) -> int:
    if level < 1:
        return 0
    if level <= len(XP_PER_LEVEL):
        return XP_PER_LEVEL[level - 1]
    return XP_PER_LEVEL[-1] + (200 * (level - len(XP_PER_LEVEL)))


def level_from_xp(xp: int) -> int:
    for i, threshold in enumerate(XP_PER_LEVEL):
        if xp < threshold:
            return i
    # beyond level 10
    extra = xp - XP_PER_LEVEL[-1]
    return len(XP_PER_LEVEL) + extra // 200


def xp_to_next_level(xp: int) -> tuple[int, int, int]:
    """Returns (current_level, xp_for_next_level, xp_needed_to_reach_next)."""
    lvl = level_from_xp(xp)
    if lvl >= len(XP_PER_LEVEL):
        next_lvl = lvl + 1
        needed = 200
        current_threshold = XP_PER_LEVEL[-1] + (200 * (lvl - len(XP_PER_LEVEL)))
    else:
        next_lvl = lvl + 1
        needed = XP_PER_LEVEL[lvl] - XP_PER_LEVEL[lvl - 1] if lvl >= 1 else XP_PER_LEVEL[0]
        current_threshold = XP_PER_LEVEL[lvl - 1] if lvl >= 1 else 0
    progress = xp - current_threshold
    return lvl, needed, progress


def award_xp(reason: str) -> int:
    """Returns XP to award for a given action."""
    xp_map = {
        "module_completed": 15,
        "module_first_try": 10,  # bonus on top of module_completed
        "path_completed": 25,
        "clarification": 2,
    }
    return xp_map.get(reason, 0)


def check_badges(stats: dict) -> list[str]:
    """Check which new badges the user has earned. Returns (new_badges, all_earned)."""
    earned = json.loads(stats.get("badges", "[]")) if isinstance(stats.get("badges"), str) else stats.get("badges", [])
    new = []

    topics = json.loads(stats.get("topics_studied", "[]")) if isinstance(stats.get("topics_studied"), str) else stats.get("topics_studied", [])
    langs_used = json.loads(stats.get("langs_used", "[]")) if isinstance(stats.get("langs_used"), str) else stats.get("langs_used", [])

    checks = [
        ("first_correct", stats.get("total_correct", 0) >= 1),
        ("student_5", stats.get("total_modules_completed", 0) >= 5),
        ("graduate_15", stats.get("total_modules_completed", 0) >= 15),
        ("encyclopedic", stats.get("total_modules_completed", 0) >= 10),
        ("sage", stats.get("total_modules_completed", 0) >= 50),
        ("centurion", stats.get("total_correct", 0) >= 100),
        ("master", stats.get("level", 0) >= 5),
        ("legend", stats.get("level", 0) >= 10),
        ("unstoppable", stats.get("max_streak", 0) >= 7),
        ("path_master", stats.get("total_paths_completed", 0) >= 1),
        ("explorer", len(topics) >= 3),
        ("polyglot", "it" in langs_used and "en" in langs_used),
        ("night_owl", stats.get("night_sessions", 0) >= 3),
        ("phoenix", stats.get("phoenix_earned", 0) >= 1),
        ("perfect_module", stats.get("perfect_modules", 0) >= 1),
        ("perfectionist", stats.get("consecutive_correct", 0) >= 3),
        ("lightning", stats.get("consecutive_correct", 0) >= 10),
    ]

    for badge_key, condition in checks:
        if condition and badge_key not in earned:
            earned.append(badge_key)
            new.append(badge_key)

    # Collector: checked after all other badges processed
    if len(earned) >= 5 and "collector" not in earned:
        earned.append("collector")
        new.append("collector")

    return new, earned


def update_streak(stats: dict) -> tuple[int, int, bool]:
    """Update daily streak. Returns (new_streak, new_max_streak, is_phoenix)."""
    today = date.today().isoformat()
    last = stats.get("last_active_date", "")
    streak = stats.get("current_streak", 0)
    max_streak = stats.get("max_streak", 0)

    if last == today:
        return streak, max_streak, False

    yesterday = date.today()
    is_phoenix = False
    try:
        last_date = datetime.strptime(last, "%Y-%m-%d").date() if last else None
    except (ValueError, TypeError):
        last_date = None

    if last_date and (yesterday - last_date).days == 1:
        streak += 1
    else:
        if last_date and (yesterday - last_date).days >= 7 and not stats.get("phoenix_earned", 0):
            is_phoenix = True
        streak = 1

    max_streak = max(max_streak, streak)
    return streak, max_streak, is_phoenix


def badge_info(badge_key: str, lang: str = "it") -> dict:
    info = BADGES.get(badge_key, {})
    return {
        "key": badge_key,
        "icon": info.get("icon", "🏅"),
        "name": info.get(f"name_{lang}", info.get("name_it", badge_key)),
        "desc": info.get(f"desc_{lang}", info.get("desc_it", "")),
    }


# ── Badge SVG rendering ────────────────────────────────────
BADGE_CATEGORY_COLORS = {
    "moduli":       {"main": "#4CAF50", "light": "#c8e6c9", "dark": "#2E7D32"},
    "precisione":   {"main": "#2196F3", "light": "#bbdefb", "dark": "#0D47A1"},
    "streak":       {"main": "#FF9800", "light": "#ffe0b2", "dark": "#BF360C"},
    "livelli":      {"main": "#9C27B0", "light": "#e1bee7", "dark": "#4A148C"},
    "traguardi":    {"main": "#FFC107", "light": "#fff9c4", "dark": "#F57F17"},
}

BADGE_CATEGORIES = {
    "first_correct": "moduli",
    "student_5": "moduli",
    "graduate_15": "moduli",
    "encyclopedic": "moduli",
    "sage": "moduli",
    "perfectionist": "precisione",
    "lightning": "precisione",
    "perfect_module": "precisione",
    "unstoppable": "streak",
    "phoenix": "streak",
    "master": "livelli",
    "legend": "livelli",
    "path_master": "traguardi",
    "explorer": "traguardi",
    "centurion": "traguardi",
    "collector": "traguardi",
    "night_owl": "traguardi",
    "polyglot": "traguardi",
}


_svg_counter = 0


def badge_svg(badge_key: str, lang: str = "it", size: int = 60, locked: bool = False) -> str:
    """Render a badge as SVG (doppio anello style)."""
    global _svg_counter
    _svg_counter += 1
    info = badge_info(badge_key, lang)
    icon = info["icon"] if not locked else "🔒"
    cat = BADGE_CATEGORIES.get(badge_key, "moduli")
    colors = BADGE_CATEGORY_COLORS[cat]

    if locked:
        colors = {"main": "#aaa", "light": "#ddd", "dark": "#888"}

    uid = f"{badge_key}_{_svg_counter}"
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 60 60">'
        f'<defs>'
        f'<radialGradient id="g_{uid}" cx="35%" cy="30%">'
        f'<stop offset="0%" stop-color="#fff"/>'
        f'<stop offset="100%" stop-color="{colors["light"]}"/>'
        f'</radialGradient>'
        f'</defs>'
        f'<circle cx="30" cy="30" r="28" fill="none" stroke="{colors["main"]}" stroke-width="6" opacity="0.3"/>'
        f'<circle cx="30" cy="30" r="26" fill="{colors["main"]}" stroke="{colors["dark"]}" stroke-width="2"/>'
        f'<circle cx="30" cy="30" r="22" fill="url(#g_{uid})"/>'
        f'<text x="30" y="39" text-anchor="middle" font-size="22">{icon}</text>'
        f'{"<text x=\"44\" y=\"17\" font-size=\"10\">✨</text>" if not locked else ""}'
        f'</svg>'
    )
