/**
 * MarkText-Py client-side helpers.
 */

// Insert/wrap text at the CodeMirror cursor position.
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
    if (line.text.startsWith(prefix)) {
        dispatch(state.update({ changes: { from: line.from, to: line.from + prefix.length, insert: '' } }));
    } else {
        dispatch(state.update({ changes: { from: line.from, insert: prefix } }));
    }
    view.focus();
};

// Native OS file picker — reads file client-side, POSTs to /api/open-file.
window.openFilePicker = function (sessionKey) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.md,.txt,.markdown';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const content = await file.text();
        await fetch('/api/open-file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_key: sessionKey, name: file.name, content: content }),
        });
    };
    input.click();
};

// Clipboard image paste.
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
