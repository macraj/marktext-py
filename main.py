import os
import sys
import signal
from pathlib import Path
from nicegui import app, ui

app.add_static_files('/static', str(Path(__file__).parent / 'static'))

_STATIC = Path(__file__).parent / 'static'
app.add_static_file(local_file=str(_STATIC / 'apple-touch-icon.png'), url_path='/apple-touch-icon.png')
app.add_static_file(local_file=str(_STATIC / 'apple-touch-icon-precomposed.png'), url_path='/apple-touch-icon-precomposed.png')
app.add_static_file(local_file=str(_STATIC / 'favicon.png'), url_path='/favicon.ico')
from editor.markdown_editor import MarkdownEditor, INITIAL_CONTENT
from editor.preview import Preview
from editor.toolbar import Toolbar
from file_manager.file_ops import (
    load_recent, read_file, write_file, save_recent,
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

    def action_open() -> None:
        """Open via server-side file browser — gives us a real, writable path."""
        with ui.dialog() as dlg, ui.card().classes('w-[560px]'):
            ui.label('Open File').classes('text-lg font-semibold mb-2')

            start_dir = load_last_folder()
            if state['path'] and os.path.isabs(state['path']):
                parent = str(Path(state['path']).resolve().parent)
                if os.path.isdir(parent):
                    start_dir = parent
            cur = {'dir': start_dir, 'file': None}

            dir_input = ui.input(label='Folder', value=cur['dir']).classes('w-full')
            file_list = ui.column().classes('w-full max-h-80 overflow-y-auto gap-0 border rounded')
            selected_lbl = ui.label('').classes('text-xs text-gray-400 truncate w-full mt-1')

            def _render_dir(d: str):
                cur['dir'] = d
                cur['file'] = None
                selected_lbl.text = ''
                dir_input.value = d
                file_list.clear()
                with file_list:
                    parent = os.path.dirname(d)
                    if parent and parent != d:
                        ui.button('📁 ..', on_click=lambda p=parent: _render_dir(p)).props(
                            'flat dense no-caps align=left').classes('w-full')
                    try:
                        entries = sorted(os.listdir(d), key=str.lower)
                    except (PermissionError, FileNotFoundError) as e:
                        ui.label(f'⛔ {e}').classes('text-red-400')
                        return
                    # Directories first
                    for name in entries:
                        if name.startswith('.'):
                            continue
                        full = os.path.join(d, name)
                        if os.path.isdir(full):
                            ui.button(
                                f'📁 {name}',
                                on_click=lambda f=full: _render_dir(f),
                            ).props('flat dense no-caps align=left').classes('w-full')
                    # Then markdown/text files
                    for name in entries:
                        if name.startswith('.'):
                            continue
                        full = os.path.join(d, name)
                        if os.path.isfile(full) and name.lower().endswith(('.md', '.markdown', '.txt', '.eml')):
                            def _pick(f=full, n=name):
                                cur['file'] = f
                                selected_lbl.text = f
                            ui.button(
                                f'📄 {name}',
                                on_click=_pick,
                            ).props('flat dense no-caps align=left').classes('w-full')

            _render_dir(cur['dir'])

            def _go_to_input():
                p = os.path.expanduser(dir_input.value.strip())
                if os.path.isfile(p):
                    _open_path(p)
                elif os.path.isdir(p):
                    _render_dir(p)
                else:
                    ui.notify('Not a file or directory', color='negative')

            dir_input.on('keydown.enter', _go_to_input)

            def _open_path(p: str):
                try:
                    content = read_file(p)
                    # .eml is imported as markdown — don't bind path (Save would overwrite the source)
                    bound = None if p.lower().endswith('.eml') else p
                    _load_content(content, path=bound)
                    save_last_folder(p)
                    save_recent(p)
                    _rebuild_recent_menu()
                    dlg.close()
                    ui.notify(f'Opened: {Path(p).name}', color='positive')
                except Exception as exc:
                    ui.notify(f'Could not open: {exc}', color='negative')

            with ui.row().classes('justify-end gap-2 mt-3 w-full'):
                ui.button('Cancel', on_click=dlg.close).props('flat')
                def _do_open():
                    if not cur['file']:
                        ui.notify('Select a file first', color='warning')
                        return
                    _open_path(cur['file'])
                ui.button('Open', on_click=_do_open).props('color=primary')

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
            bound = None if path.lower().endswith('.eml') else path
            _load_content(content, bound)
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

            vmargin = ui.select(
                {None: 'Auto', 0.5: '0.5 cm', 0.8: '0.8 cm', 1.0: '1.0 cm',
                 1.5: '1.5 cm', 2.0: '2.0 cm', 2.5: '2.5 cm'},
                value=None,
                label='Top/bottom margin (PDF only)',
            ).classes('w-full')

            dark_toggle = ui.checkbox('Dark theme', value=False)
            page_numbers_toggle = ui.checkbox('Page numbers — "Page X of Y — filename" (PDF only)', value=False)

            if state['path']:
                _export_folder = str(Path(state['path']).resolve().parent)
                _basename = Path(state['path']).stem + '.pdf'
            else:
                _export_folder = load_last_folder()
                _basename = Path(propose_filename(
                    state['content'], folder=_export_folder,
                )).stem + '.pdf'

            # --- folder selector (server-side listing) ---
            _folder_ref = {'value': _export_folder}

            folder_label = ui.label(_export_folder).classes(
                'text-xs text-gray-400 truncate w-full')

            def _pick_folder():
                with ui.dialog() as fdlg, ui.card().classes('w-[500px]'):
                    ui.label('Choose folder').classes('text-lg font-semibold mb-2')
                    cur = {'dir': _folder_ref['value']}
                    dir_input = ui.input(label='Path', value=cur['dir']).classes('w-full')
                    file_list = ui.column().classes('w-full max-h-64 overflow-y-auto gap-0')

                    def _render_dir(d: str):
                        cur['dir'] = d
                        dir_input.value = d
                        file_list.clear()
                        with file_list:
                            parent = os.path.dirname(d)
                            if parent != d:
                                ui.button('📁 ..', on_click=lambda p=parent: _render_dir(p)).props(
                                    'flat dense no-caps align=left').classes('w-full')
                            try:
                                entries = sorted(os.listdir(d))
                            except PermissionError:
                                ui.label('⛔ Permission denied').classes('text-red-400')
                                return
                            for name in entries:
                                if name.startswith('.'):
                                    continue
                                full = os.path.join(d, name)
                                if os.path.isdir(full):
                                    ui.button(
                                        f'📁 {name}',
                                        on_click=lambda f=full: _render_dir(f),
                                    ).props('flat dense no-caps align=left').classes('w-full')

                    _render_dir(cur['dir'])

                    def _go_to_input():
                        p = os.path.expanduser(dir_input.value.strip())
                        if os.path.isdir(p):
                            _render_dir(p)
                        else:
                            ui.notify('Not a directory', color='negative')

                    dir_input.on('keydown.enter', _go_to_input)

                    with ui.row().classes('justify-end gap-2 mt-2 w-full'):
                        ui.button('Cancel', on_click=fdlg.close).props('flat')
                        def _select():
                            chosen = cur['dir']
                            _folder_ref['value'] = chosen
                            folder_label.text = chosen
                            path_input.value = os.path.join(chosen, os.path.basename(path_input.value))
                            fdlg.close()
                        ui.button('Select', on_click=_select).props('color=primary')
                fdlg.open()

            with ui.row().classes('w-full items-end gap-2'):
                path_input = ui.input(
                    label='Filename',
                    value=os.path.join(_export_folder, _basename),
                ).classes('flex-grow')
                ui.button(icon='folder_open', on_click=_pick_folder).props(
                    'flat dense').classes('mb-1')

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
                            short_name = Path(state['path']).name if state['path'] else title
                            export_pdf(
                                rendered_html,
                                title=title,
                                dark=dark_toggle.value,
                                page_size=page_size.value,
                                dest_path=dest,
                                page_numbers=page_numbers_toggle.value,
                                doc_title=short_name,
                                vertical_margin_cm=vmargin.value,
                            )
                        else:
                            export_html(
                                rendered_html,
                                title=title,
                                dark=dark_toggle.value,
                                dest_path=dest,
                            )
                        save_last_folder(dest)
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
        .q-splitter { flex: 1; overflow: hidden; margin-bottom: 40px; }
        .q-splitter__panel { overflow: auto; }
    </style>
    """)
    # Inject initial theme CSS vars
    ui.add_head_html(f'<style id="app-theme">{load_theme_css(state["theme"])}</style>')
    # KaTeX for math rendering
    ui.add_head_html(KATEX_HEAD)
    ui.add_head_html(
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">'
        '<link rel="icon" type="image/png" sizes="192x192" href="/static/icon-192.png">'
        '<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon.png">'
    )

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
