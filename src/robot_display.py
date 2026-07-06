from pathlib import Path

ROBOT_DIR = Path(__file__).resolve().parents[1] / "logos"
SIZES = {"sm": 80, "md": 120, "lg": 180, "xl": 240}


def _robot_path(expression: str) -> Path | None:
    mapping = {
        "neutral": "robot_8bit_neutral_nomouth.svg",
        "happy": "robot_8bit_happy_v8.svg",
        "thinking": "robot_8bit_thinking_v4.svg",
        "animated": "robot_8bit_animated_final.svg",
    }
    filename = mapping.get(expression)
    if not filename:
        return None
    path = ROBOT_DIR / filename
    return path if path.exists() else None


def get_robot_path(expression: str) -> str:
    """Restituisce il percorso del file SVG, usabile con st.image()."""
    p = _robot_path(expression)
    return str(p) if p else ""


def robot_html(expression: str, size: int | str = 120) -> str:
    """HTML per embeddare il robot. Per l'animato usa <object> per evitare conflitti CSS."""
    path = _robot_path(expression)
    if not path:
        return ""

    px = SIZES.get(str(size), size) if isinstance(size, str) else size
    h = int(px * 348 / 432)

    if expression == "animated":
        return (
            f'<div style="text-align:center;margin:8px 0">'
            f'<object data="{path.as_posix()}" type="image/svg+xml" '
            f'width="{px}" height="{h}" style="pointer-events:none">'
            f'</object></div>'
        )

    return (
        f'<div style="text-align:center;margin:8px 0">'
        f'<img src="{path.as_posix()}" width="{px}" height="{h}" '
        f'style="image-rendering:pixelated;image-rendering:crisp-edges">'
        f'</div>'
    )


def robot_neutral(size: int = 120) -> str:
    return robot_html("neutral", size)


def robot_happy(size: int = 120) -> str:
    return robot_html("happy", size)


def robot_thinking(size: int = 120) -> str:
    return robot_html("thinking", size)


def robot_animated(size: int = 120) -> str:
    return robot_html("animated", size)
