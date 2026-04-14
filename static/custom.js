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
        // NiceGUI stores Vue component instances in mounted_app.elements.
        // The CodeMirror component has an .editor property (EditorView).
        if (typeof mounted_app === 'undefined' || !mounted_app.elements) return;
        const cmComponent = Object.values(mounted_app.elements).find(e => e && e.editor);
        if (cmComponent) {
            window._cmView = cmComponent.editor;
            clearInterval(poll);
            setupImagePaste();
        }
    }, 200);
});
