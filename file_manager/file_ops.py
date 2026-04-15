"""File open/save/recent operations."""
import json
import re
import os
from pathlib import Path

RECENT_FILE = Path.home() / '.marktext_py_recent.json'
MAX_RECENT = 10
_PREFS_FILE = Path.home() / '.marktext_py_prefs.json'


def _load_prefs() -> dict:
    try:
        return json.loads(_PREFS_FILE.read_text())
    except Exception:
        return {}


def _save_prefs(prefs: dict) -> None:
    try:
        existing = _load_prefs()
        existing.update(prefs)
        _PREFS_FILE.write_text(json.dumps(existing))
    except Exception:
        pass


def load_last_folder() -> str:
    return _load_prefs().get('last_folder', str(Path.home() / 'Documents'))


def save_last_folder(path: str) -> None:
    _save_prefs({'last_folder': str(Path(path).resolve().parent)})


def propose_filename(content: str, folder: str | None = None) -> str:
    """Derive a filename from document content.

    Strategy (in order):
    1. First H1 heading  (`# Title`)
    2. First H2/H3 heading
    3. First non-empty, non-heading line
    4. Fallback: 'untitled'

    Slugifies the result and appends .md.
    """
    folder = folder or load_last_folder()

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip markdown heading markers
        text = re.sub(r'^#{1,6}\s+', '', line)
        if text:
            slug = _slugify(text)
            return str(Path(folder) / f'{slug}.md')

    return str(Path(folder) / 'untitled.md')


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)       # remove special chars
    text = re.sub(r'[\s_-]+', '-', text).strip('-')  # spaces → hyphens
    return text[:60] or 'untitled'             # max 60 chars


def load_recent() -> list[str]:
    try:
        return json.loads(RECENT_FILE.read_text())
    except Exception:
        return []


def save_recent(path: str) -> None:
    recent = load_recent()
    if path in recent:
        recent.remove(path)
    recent.insert(0, path)
    RECENT_FILE.write_text(json.dumps(recent[:MAX_RECENT]))


def read_file(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')


def write_file(path: str, content: str) -> None:
    Path(path).write_text(content, encoding='utf-8')
    save_recent(path)
