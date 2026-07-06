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
    """Check which new badges the user has earned. Returns list of badge keys."""
    earned = json.loads(stats.get("badges", "[]")) if isinstance(stats.get("badges"), str) else stats.get("badges", [])
    new = []

    checks = [
        ("first_correct", stats.get("total_correct", 0) >= 1),
        ("student_5", stats.get("total_modules_completed", 0) >= 5),
        ("graduate_15", stats.get("total_modules_completed", 0) >= 15),
        ("master", stats.get("level", 0) >= 5),
        ("legend", stats.get("level", 0) >= 10),
        ("unstoppable", stats.get("max_streak", 0) >= 7),
        ("path_master", stats.get("total_paths_completed", 0) >= 1),
    ]

    topics = json.loads(stats.get("topics_studied", "[]")) if isinstance(stats.get("topics_studied"), str) else stats.get("topics_studied", [])
    checks.append(("explorer", len(topics) >= 3))

    for badge_key, condition in checks:
        if condition and badge_key not in earned:
            earned.append(badge_key)
            new.append(badge_key)

    return new, earned


def update_streak(stats: dict) -> tuple[int, int]:
    """Update daily streak. Returns (new_streak, new_max_streak)."""
    today = date.today().isoformat()
    last = stats.get("last_active_date", "")
    streak = stats.get("current_streak", 0)
    max_streak = stats.get("max_streak", 0)

    if last == today:
        return streak, max_streak

    yesterday = date.today()
    try:
        last_date = datetime.strptime(last, "%Y-%m-%d").date() if last else None
    except (ValueError, TypeError):
        last_date = None

    if last_date and (yesterday - last_date).days == 1:
        streak += 1
    else:
        streak = 1

    max_streak = max(max_streak, streak)
    return streak, max_streak


def badge_info(badge_key: str, lang: str = "it") -> dict:
    info = BADGES.get(badge_key, {})
    return {
        "key": badge_key,
        "icon": info.get("icon", "🏅"),
        "name": info.get(f"name_{lang}", info.get("name_it", badge_key)),
        "desc": info.get(f"desc_{lang}", info.get("desc_it", "")),
    }
