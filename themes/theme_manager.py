"""Theme switching and persistence."""
import json
from pathlib import Path

PREFS_FILE = Path.home() / '.marktext_py_prefs.json'

THEMES = {
    'Dark':           'dark',
    'One Dark':       'one_dark',
    'Material Dark':  'material_dark',
    'Cadmium Light':  'cadmium_light',
    'Graphite Light': 'graphite_light',
    'Ulysses Light':  'ulysses_light',
}

# CodeMirror built-in themes that correspond to each theme
CM_THEMES = {
    'dark':           'dracula',
    'one_dark':       'dracula',
    'material_dark':  'dracula',
    'cadmium_light':  'default',
    'graphite_light': 'default',
    'ulysses_light':  'default',
}

CSS_DIR = Path(__file__).parent / 'css'


def load_theme_css(theme_key: str) -> str:
    css_file = CSS_DIR / f'{theme_key}.css'
    return css_file.read_text(encoding='utf-8')


def load_saved_theme() -> str:
    """Return saved theme key, default to 'dark'."""
    try:
        prefs = json.loads(PREFS_FILE.read_text())
        return prefs.get('theme', 'dark')
    except Exception:
        return 'dark'


def save_theme(theme_key: str) -> None:
    try:
        prefs = json.loads(PREFS_FILE.read_text()) if PREFS_FILE.exists() else {}
    except Exception:
        prefs = {}
    prefs['theme'] = theme_key
    PREFS_FILE.write_text(json.dumps(prefs))
