from nicegui import ui


class Toolbar:
    """Formatting toolbar. Call attach(editor) after construction."""

    def __init__(self):
        self._editor = None
        self._build()

    def _build(self):
        btn = lambda label, tip, fn: (
            ui.button(label, on_click=fn)
            .props('flat dense')
            .classes('text-white text-xs font-mono')
            .tooltip(tip)
        )

        with ui.row().classes('items-center gap-0'):
            btn('B',    'Bold (Ctrl+B)',          lambda: self._wrap('**', '**'))
            btn('I',    'Italic (Ctrl+I)',         lambda: self._wrap('_', '_'))
            btn('~~',   'Strikethrough',           lambda: self._wrap('~~', '~~'))
            ui.separator().props('vertical').classes('mx-1 opacity-30')
            btn('H1',   'Heading 1',               lambda: self._prefix('# '))
            btn('H2',   'Heading 2',               lambda: self._prefix('## '))
            btn('H3',   'Heading 3',               lambda: self._prefix('### '))
            ui.separator().props('vertical').classes('mx-1 opacity-30')
            btn('• ',   'Bullet list',             lambda: self._prefix('- '))
            btn('1. ',  'Numbered list',           lambda: self._prefix('1. '))
            btn('> ',   'Blockquote',              lambda: self._prefix('> '))
            ui.separator().props('vertical').classes('mx-1 opacity-30')
            btn('`c`',  'Inline code',             lambda: self._wrap('`', '`'))
            btn('```',  'Code block',              lambda: self._wrap('\n```\n', '\n```\n'))
            ui.separator().props('vertical').classes('mx-1 opacity-30')
            btn('—',    'Horizontal rule',         lambda: self._insert('\n\n---\n\n'))
            btn('🔗',   'Link',                   lambda: self._insert('[text](url)'))
            btn('🖼',   'Image',                  lambda: self._insert('![alt](url)'))
            btn('⊞',   'Table',                  lambda: self._insert(
                '\n| Column 1 | Column 2 |\n|----------|----------|\n| Cell     | Cell     |\n'
            ))

    def attach(self, editor) -> None:
        self._editor = editor

    # Use JS cursor-aware insertion when possible, fall back to append.
    def _wrap(self, before: str, after: str) -> None:
        ui.run_javascript(f'window.cmInsert({before!r}, {after!r})')

    def _prefix(self, prefix: str) -> None:
        ui.run_javascript(f'window.cmPrefix({prefix!r})')

    def _insert(self, text: str) -> None:
        ui.run_javascript(f'window.cmInsert({text!r})')
