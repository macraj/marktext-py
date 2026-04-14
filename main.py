import os
import sys
import signal
from pathlib import Path
from nicegui import app, ui
from fastapi import Request

# Module-level store for files picked via JS native file picker.
# Keyed by session_key (str(id(state)) per page load).
_pending_files: dict[str, dict] = {}


@app.post('/api/open-file')
async def _api_open_file(request: Request):
    data = await request.json()
    _pending_files[data['session_key']] = {
        'name': data['name'],
        'content': data['content'],
    }
    return {'ok': True}

app.add_static_files('/static', str(Path(__file__).parent / 'static'))
from editor.markdown_editor import MarkdownEditor, INITIAL_CONTENT
from editor.preview import Preview
from editor.toolbar import Toolbar
from file_manager.file_ops import (
    load_recent, read_file, write_file,
    propose_filename, save_last_folder, load_last_folder,
)
from editor.preview import render as render_md, KATEX_HEAD
from export.html_export import export_html
from export.pdf_export import export_pdf
from themes.theme_manager import THEMES, CM_THEMES, load_theme_css, load_saved_theme, save_theme
from editor.modes import EditMode, MODE_LABELS, TYPEWRITER_JS, TYPEWRITER_JS_OFF, FOCUS_CSS, FOCUS_CSS_OFF


@ui.page('/')
def index():
    # Mutable state
    current_theme = load_saved_theme()
    state = {
        'path': None,           # current file path (str | None)
        'dirty': False,         # unsaved changes
        'theme': current_theme,
        'content': INITIAL_CONTENT,  # always up-to-date editor text
    }

    preview_ref: list[Preview] = []
    editor_ref: list[MarkdownEditor] = []
    title_label_ref: list = []
    recent_menu_ref: list = []
    splitter_ref: list = []
    mode_btn_ref: list = []
    state['mode'] = EditMode.SPLIT

    # ------------------------------------------------------------------ helpers
    def _set_title(path: str | None, dirty: bool = False) -> None:
        name = path.split('/')[-1] if path else 'Untitled'
        marker = ' •' if dirty else ''
        full_title = f'MarkText-Py — {name}{marker}'
        if title_label_ref:
            title_label_ref[0].set_text(full_title)
        ui.run_javascript(f'document.title = {full_title!r}')

    def _load_content(content: str, path: str | None = None) -> None:
        state['path'] = path
        state['dirty'] = False
        state['content'] = content
        editor_ref[0].set_value(content)
        preview_ref[0].update(content)
        _set_title(path, dirty=False)

    def _mark_dirty() -> None:
        if not state['dirty']:
            state['dirty'] = True
            _set_title(state['path'], dirty=True)

    # ----------------------------------------------------------- file actions
    def action_new() -> None:
        if state['dirty']:
            with ui.dialog() as dlg, ui.card():
                ui.label('Discard unsaved changes?')
                with ui.row():
                    ui.button('Discard', on_click=lambda: (dlg.close(), _load_content(INITIAL_CONTENT))).props('color=negative')
                    ui.button('Cancel', on_click=dlg.close).props('flat')
            dlg.open()
        else:
            _load_content(INITIAL_CONTENT)

    # Unique key for this page session — used to route JS file picks back here.
    session_key = str(id(state))
    # Holds open dialog ref so the pending-file timer can close it.
    open_dialog_ref: list = []

    def action_open() -> None:
        """Open via native OS file picker (JS) or manual path input."""
        with ui.dialog() as dlg, ui.card().classes('w-96'):
            open_dialog_ref.clear()
            open_dialog_ref.append(dlg)

            ui.label('Open File').classes('text-lg font-semibold mb-2')

            # HTML label+input — label click triggers file picker (direct user
            # gesture, no Python round-trip).  Vue's v-html strips inline
            # handlers, so we attach onchange via ui.run_javascript below.
            input_id = f'file-open-{session_key}'
            ui.html(f'''
<label style="display:flex;align-items:center;gap:8px;cursor:pointer;
              padding:8px 16px;border-radius:4px;background:#1976d2;
              color:white;font-size:14px;width:100%;box-sizing:border-box;justify-content:center;">
  <span class="material-icons" style="font-size:18px">folder_open</span>
  Browse files…
  <input type="file" id="{input_id}" accept=".md,.txt,.markdown" style="display:none">
</label>''')
            # Attach the change handler via JS (v-html strips inline handlers).
            ui.run_javascript(f'''
                const el = document.getElementById({input_id!r});
                if (el) el.onchange = async function(e) {{
                    const file = e.target.files[0];
                    if (!file) return;
                    const text = await file.text();
                    await fetch('/api/open-file', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            session_key: {session_key!r},
                            name: file.name,
                            content: text
                        }})
                    }});
                }};
            ''')

            ui.label('— or type the full path —').classes(
                'text-xs text-gray-500 my-2 text-center w-full')

            path_input = ui.input(
                label='File path',
                placeholder='/Users/you/notes.md',
            ).classes('w-full')

            def _close():
                open_dialog_ref.clear()
                dlg.close()

            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=_close).props('flat')

                def do_open_path():
                    p = os.path.expanduser(path_input.value.strip())
                    try:
                        content = read_file(p)
                        _load_content(content, path=p)
                        save_last_folder(p)
                        _close()
                        ui.notify(f'Opened: {p.split("/")[-1]}', color='positive')
                    except Exception as exc:
                        ui.notify(f'Could not open: {exc}', color='negative')

                ui.button('Open path', on_click=do_open_path).props('flat')

        dlg.open()

    def action_save() -> None:
        if state['path']:
            write_file(state['path'], state['content'])
            state['dirty'] = False
            _set_title(state['path'], dirty=False)
            ui.notify('Saved', color='positive')
        else:
            action_save_as()

    def action_save_as() -> None:
        content = state['content']
        suggested = state['path'] or propose_filename(content)

        with ui.dialog() as dlg, ui.card().classes('w-96'):
            ui.label('Save As').classes('text-lg font-semibold mb-2')
            path_input = ui.input(
                label='File path',
                value=suggested,
            ).classes('w-full')
            with ui.row().classes('justify-end gap-2 mt-2'):
                ui.button('Cancel', on_click=dlg.close).props('flat')
                def do_save():
                    p = os.path.expanduser(str(path_input.value).strip())
                    write_file(p, state['content'])
                    save_last_folder(p)
                    state['path'] = p
                    state['dirty'] = False
                    _set_title(p, dirty=False)
                    dlg.close()
                    ui.notify(f'Saved to {p}', color='positive')
                    _rebuild_recent_menu()
                ui.button('Save', on_click=do_save).props('color=primary')
        dlg.open()

    def action_open_recent(path: str) -> None:
        try:
            content = read_file(path)
            _load_content(content, path)
            save_last_folder(path)
            ui.notify(f'Opened: {path.split("/")[-1]}', color='positive')
        except Exception as exc:
            ui.notify(f'Could not open: {exc}', color='negative')

    # ----------------------------------------------------------- export actions
    def action_export() -> None:
        with ui.dialog() as dlg, ui.card().classes('w-96'):
            ui.label('Export Document').classes('text-lg font-semibold mb-2')

            fmt = ui.select(
                ['PDF', 'HTML'],
                value='PDF',
                label='Format',
            ).classes('w-full')

            page_size = ui.select(
                ['A4', 'Letter', 'A3'],
                value='A4',
                label='Page size (PDF only)',
            ).classes('w-full')

            dark_toggle = ui.checkbox('Dark theme', value=False)

            _export_base = propose_filename(
                state['content']
            ).removesuffix('.md')
            path_input = ui.input(
                label='Save to path',
                value=_export_base + '.pdf',
            ).classes('w-full')

            def _update_ext():
                p = path_input.value
                if fmt.value == 'PDF' and not p.endswith('.pdf'):
                    path_input.value = p.rsplit('.', 1)[0] + '.pdf'
                elif fmt.value == 'HTML' and not p.endswith('.html'):
                    path_input.value = p.rsplit('.', 1)[0] + '.html'

            fmt.on('update:model-value', lambda _: _update_ext())

            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dlg.close).props('flat')

                def do_export():
                    dest = os.path.expanduser(path_input.value.strip())
                    content = state['content']
                    rendered_html = render_md(content)
                    title = (state['path'] or 'Document').split('/')[-1]
                    try:
                        if fmt.value == 'PDF':
                            export_pdf(
                                rendered_html,
                                title=title,
                                dark=dark_toggle.value,
                                page_size=page_size.value,
                                dest_path=dest,
                            )
                        else:
                            export_html(
                                rendered_html,
                                title=title,
                                dark=dark_toggle.value,
                                dest_path=dest,
                            )
                        dlg.close()
                        ui.notify(f'Exported to {dest}', color='positive')
                    except Exception as exc:
                        ui.notify(f'Export failed: {exc}', color='negative')

                ui.button('Export', on_click=do_export).props('color=primary')

        dlg.open()

    def _rebuild_recent_menu() -> None:
        if not recent_menu_ref:
            return
        menu = recent_menu_ref[0]
        menu.clear()
        recent = load_recent()
        with menu:
            if recent:
                for p in recent:
                    name = p.split('/')[-1]
                    ui.menu_item(name, on_click=lambda _, rp=p: action_open_recent(rp))
            else:
                ui.menu_item('(no recent files)').props('disable')

    # ----------------------------------------------------------- mode actions
    def apply_mode(mode: EditMode) -> None:
        state['mode'] = mode
        sp = splitter_ref[0] if splitter_ref else None

        if mode == EditMode.SOURCE:
            if sp:
                sp.set_value(100)   # full width to editor, hide preview
            ui.run_javascript(TYPEWRITER_JS_OFF)
            ui.run_javascript(f"""
                let el = document.getElementById('focus-mode-css');
                if (el) el.textContent = '';
            """)
        elif mode == EditMode.SPLIT:
            if sp:
                sp.set_value(50)
            ui.run_javascript(TYPEWRITER_JS_OFF)
            ui.run_javascript(f"""
                let el = document.getElementById('focus-mode-css');
                if (el) el.textContent = '';
            """)
        elif mode == EditMode.TYPEWRITER:
            if sp:
                sp.set_value(50)
            ui.run_javascript(TYPEWRITER_JS)
            ui.run_javascript(f"""
                let el = document.getElementById('focus-mode-css');
                if (el) el.textContent = '';
            """)
        elif mode == EditMode.FOCUS:
            if sp:
                sp.set_value(50)
            ui.run_javascript(TYPEWRITER_JS_OFF)
            ui.run_javascript(f"""
                let el = document.getElementById('focus-mode-css');
                if (!el) {{
                    el = document.createElement('style');
                    el.id = 'focus-mode-css';
                    document.head.appendChild(el);
                }}
                el.textContent = {FOCUS_CSS!r};
            """)

        if mode_btn_ref:
            mode_btn_ref[0].set_text(MODE_LABELS[mode])

    # ----------------------------------------------------------- theme actions
    def apply_theme(theme_key: str) -> None:
        state['theme'] = theme_key
        save_theme(theme_key)
        css = load_theme_css(theme_key)
        # Inject/replace CSS vars into the page
        ui.run_javascript(f"""
            let el = document.getElementById('app-theme');
            if (!el) {{ el = document.createElement('style'); el.id = 'app-theme'; document.head.appendChild(el); }}
            el.textContent = {css!r};
        """)
        # Switch CodeMirror theme
        cm_theme = CM_THEMES.get(theme_key, 'default')
        if editor_ref:
            editor_ref[0].codemirror.props(f'theme={cm_theme}')
        # Update preview background to match theme bg
        is_dark = 'light' not in theme_key
        ui.run_javascript(f"""
            const r = document.documentElement;
            const bg = getComputedStyle(r).getPropertyValue('--bg').trim();
            const fg = getComputedStyle(r).getPropertyValue('--text').trim();
            document.body.style.background = bg;
        """)

    # ------------------------------------------------------------------ layout
    ui.add_head_html("""
    <style>
        body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; }
        .nicegui-content { height: 100vh; display: flex; flex-direction: column; padding: 0 !important; }
        .q-splitter { flex: 1; overflow: hidden; margin-bottom: 30px; }
        .q-splitter__panel { overflow: auto; }
    </style>
    """)
    # Inject initial theme CSS vars
    ui.add_head_html(f'<style id="app-theme">{load_theme_css(state["theme"])}</style>')
    # KaTeX for math rendering
    ui.add_head_html(KATEX_HEAD)

    # Load custom JS (cursor-aware CodeMirror helpers)
    ui.add_body_html('<script src="/static/custom.js"></script>')

    # Keyboard shortcuts
    def on_key(e) -> None:
        mod = e.modifiers.ctrl or e.modifiers.meta
        if not mod:
            return
        if e.key == 's':
            action_save()
        elif e.key == 'b':
            ui.run_javascript("window.cmInsert('**', '**')")
        elif e.key == 'i':
            ui.run_javascript("window.cmInsert('_', '_')")
        elif e.key == 'k':
            ui.run_javascript("window.cmInsert('[', '](url)')")

    ui.keyboard(on_key=on_key)

    # Header / toolbar
    with ui.header(elevated=True).classes('bg-gray-800 text-white px-4 py-1 items-center justify-between'):
        with ui.row().classes('items-center gap-3'):
            title_lbl = ui.label('MarkText-Py — Untitled').classes('text-base font-semibold tracking-wide')
            title_label_ref.append(title_lbl)
            ui.separator().props('vertical color=white').classes('opacity-30')
            toolbar = Toolbar()

        with ui.row().classes('items-center gap-2'):
            ui.button('New', icon='add', on_click=action_new) \
                .props('flat dense color=white').classes('text-xs')

            ui.button('Open', icon='folder_open', on_click=action_open) \
                .props('flat dense color=white').classes('text-xs')

            ui.button('Save', icon='save', on_click=action_save) \
                .props('flat dense color=white').classes('text-xs')

            ui.button('Export', icon='download', on_click=action_export) \
                .props('flat dense color=white').classes('text-xs')

            # Recent files menu
            with ui.button('Recent', icon='history') \
                    .props('flat dense color=white').classes('text-xs'):
                with ui.menu() as recent_menu:
                    recent_menu_ref.append(recent_menu)
            _rebuild_recent_menu()

            # Theme picker
            with ui.button('Theme', icon='palette') \
                    .props('flat dense color=white').classes('text-xs'):
                with ui.menu():
                    for label, key in THEMES.items():
                        ui.menu_item(
                            label,
                            on_click=lambda _, k=key: apply_theme(k),
                        )

    # Main split view
    with ui.splitter(value=50).classes('w-full flex-1') as splitter:
        splitter_ref.append(splitter)
        with splitter.before:
            with ui.element('div').classes('w-full h-full flex flex-col'):
                editor = MarkdownEditor(INITIAL_CONTENT)
                editor_ref.append(editor)
                toolbar.attach(editor)

        with splitter.after:
            preview = Preview()
            preview_ref.append(preview)

    # Status bar
    with ui.footer().classes('bg-gray-800 text-gray-400 px-4 py-1 text-xs'):
        with ui.row().classes('items-center gap-4 w-full justify-between'):
            with ui.row().classes('items-center gap-4'):
                ui.label('Markdown').classes('text-gray-500')
                ui.label('UTF-8').classes('text-gray-500')
                word_lbl  = ui.label('0 words').classes('text-gray-500')
                char_lbl  = ui.label('0 chars').classes('text-gray-500')
            # Mode switcher
            with ui.button_group().props('flat'):
                for mode in EditMode:
                    ui.button(
                        MODE_LABELS[mode],
                        on_click=lambda _, m=mode: apply_mode(m),
                    ).props('flat dense').classes('text-gray-400 text-xs')

    def _update_counts(text: str) -> None:
        words = len(text.split())
        chars = len(text)
        word_lbl.set_text(f'{words:,} words')
        char_lbl.set_text(f'{chars:,} chars')

    def _sync_preview():
        """Polling sync: check if editor content changed and update preview."""
        current = editor.codemirror.value
        if current != state['content']:
            state['content'] = current
            if preview_ref:
                preview_ref[0].update(current)
            _mark_dirty()
            _update_counts(current)

    ui.timer(0.3, _sync_preview)

    # Poll for files picked via native JS file picker
    def _check_pending_file():
        if session_key in _pending_files:
            file_data = _pending_files.pop(session_key)
            if open_dialog_ref:
                open_dialog_ref[0].close()
                open_dialog_ref.clear()
            _load_content(file_data['content'], path=file_data['name'])
            ui.notify(f'Opened: {file_data["name"]}', color='positive')

    ui.timer(0.3, _check_pending_file)

    # Initial render
    preview.update(INITIAL_CONTENT)
    _update_counts(INITIAL_CONTENT)


# Graceful shutdown on Ctrl+C
def _handle_shutdown(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, _handle_shutdown)

ui.run(
    title='MarkText-Py',
    dark=True,
    port=8080,
    reload=False,
    show=True,
)
