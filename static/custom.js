/**
 * MarkText-Py client-side helpers.
 * Loaded via ui.add_body_html() in main.py.
 */

// Insert/wrap text at the CodeMirror cursor position.
// Called from Python via ui.run_javascript().
window.cmInsert = function (before, after = '') {
    const view = window._cmView;
    if (!view) return;
    const { state, dispatch } = view;
    const sel = state.selection.main;
    const selected = state.sliceDoc(sel.from, sel.to);
    const replacement = before + selected + after;
    dispatch(state.update({
        changes: { from: sel.from, to: sel.to, insert: replacement },
        selection: { anchor: sel.from + before.length, head: sel.from + before.length + selected.length },
    }));
    view.focus();
};

window.cmPrefix = function (prefix) {
    const view = window._cmView;
    if (!view) return;
    const { state, dispatch } = view;
    const line = state.doc.lineAt(state.selection.main.head);
    // Toggle: if already prefixed, remove; otherwise add.
    if (line.text.startsWith(prefix)) {
        dispatch(state.update({ changes: { from: line.from, to: line.from + prefix.length, insert: '' } }));
    } else {
        dispatch(state.update({ changes: { from: line.from, insert: prefix } }));
    }
    view.focus();
};

// Clipboard image paste: convert pasted image to base64 data URL and insert markdown.
function setupImagePaste() {
    document.addEventListener('paste', async (e) => {
        const view = window._cmView;
        if (!view) return;
        const items = Array.from(e.clipboardData?.items || []);
        const imageItem = items.find(i => i.type.startsWith('image/'));
        if (!imageItem) return;

        e.preventDefault();
        const file = imageItem.getAsFile();
        if (!file) return;

        // Convert to base64 data URL
        const reader = new FileReader();
        reader.onload = (ev) => {
            const dataUrl = ev.target.result;
            const markdown = `![pasted image](${dataUrl})`;
            const { state, dispatch } = view;
            const sel = state.selection.main;
            dispatch(state.update({
                changes: { from: sel.from, to: sel.to, insert: markdown },
                selection: { anchor: sel.from + markdown.length },
            }));
            view.focus();
        };
        reader.readAsDataURL(file);
    });
}

// Store the CodeMirror view reference when the component mounts.
// NiceGUI's codemirror exposes the view on the element.
document.addEventListener('DOMContentLoaded', () => {
    const poll = setInterval(() => {
        const el = document.querySelector('.cm-editor');
        if (el && el.cmView) {
            window._cmView = el.cmView.view;
            clearInterval(poll);
            setupImagePaste();
        }
    }, 200);
});
