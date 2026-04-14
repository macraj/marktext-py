from nicegui import ui


EDITOR_CSS = """
<style>
.cm-editor {
    height: 100%;
    font-size: 15px;
}
.cm-scroller {
    font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    line-height: 1.7;
}
.cm-content {
    padding-bottom: 40vh;
}
</style>
"""

INITIAL_CONTENT = """\
# Welcome to MarkText-Py

Start writing **markdown** here. The preview updates in real time.

## Features

- Live preview
- Syntax highlighting
- Export to PDF and HTML
- Multiple themes

## Code Example

```python
def hello():
    print("Hello, MarkText-Py!")
```

## Math (coming soon)

Inline math: $E = mc^2$

Block math:

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$
"""


class MarkdownEditor:
    def __init__(self, content: str = INITIAL_CONTENT):
        ui.html(EDITOR_CSS)
        self.codemirror = (
            ui.codemirror(
                value=content,
                language='markdown',
                theme='dracula',
            )
            .classes('w-full h-full')
        )

    @property
    def value(self) -> str:
        return self.codemirror.value

    def set_value(self, content: str) -> None:
        self.codemirror.value = content
