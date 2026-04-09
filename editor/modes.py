"""Edit mode management: source, split, typewriter, focus."""
from enum import Enum


class EditMode(Enum):
    SPLIT       = 'split'       # Editor + preview side by side (default)
    SOURCE      = 'source'      # Editor only, no preview
    TYPEWRITER  = 'typewriter'  # Split + cursor line always vertically centered
    FOCUS       = 'focus'       # Split + dim non-active paragraphs


MODE_LABELS = {
    EditMode.SPLIT:      'Split',
    EditMode.SOURCE:     'Source',
    EditMode.TYPEWRITER: 'Typewriter',
    EditMode.FOCUS:      'Focus',
}

# JS injected per-mode (applied / removed on mode switch)
TYPEWRITER_JS = """
(function() {
    if (window._twObserver) window._twObserver.disconnect();
    const view = window._cmView;
    if (!view) return;
    function center() {
        const cursor = view.coordsAtPos(view.state.selection.main.head);
        if (!cursor) return;
        const scroll = view.scrollDOM;
        const target = scroll.scrollTop + cursor.top - scroll.clientHeight / 2;
        scroll.scrollTo({ top: target, behavior: 'smooth' });
    }
    window._twObserver = new MutationObserver(center);
    window._twObserver.observe(view.contentDOM, { childList: true, subtree: true, characterData: true });
    window._twMode = true;
})();
"""

TYPEWRITER_JS_OFF = """
if (window._twObserver) { window._twObserver.disconnect(); window._twObserver = null; }
window._twMode = false;
"""

FOCUS_CSS = """
.cm-line { opacity: 0.3; transition: opacity 0.15s; }
.cm-line.cm-activeLine { opacity: 1 !important; }
"""

FOCUS_CSS_OFF = ""
