# MarkText-Py

A lightweight Markdown editor inspired by [MarkText](https://github.com/marktext/marktext), built entirely in Python with [NiceGUI](https://nicegui.io).

Runs as a local web app in your browser — no Electron, no heavy dependencies.

## Features

- **Live preview** — split-pane editor with real-time Markdown rendering
- **Multiple edit modes** — Split, Source-only, Typewriter (centered cursor), Focus (dim inactive paragraphs)
- **6 themes** — Dark, One Dark, Material Dark, Cadmium Light, Graphite Light, Ulysses Light
- **Export** — PDF and HTML export with page size and dark/light options
- **File management** — New, Open (native file picker or path input), Save, Save As, Recent files
- **Toolbar & shortcuts** — Bold, Italic, Headings, Lists, Code, Links, Tables, and more
- **Math & Emoji** — KaTeX math rendering and emoji support
- **Word & character count** in status bar

## Requirements

- **Python 3.13+**
- **macOS** or **Linux** (Windows not tested)
- [uv](https://docs.astral.sh/uv/) — installed automatically by the install script

### System dependencies (for PDF export)

PDF export uses [WeasyPrint](https://weasyprint.org), which needs Pango:

| OS | Command |
|---|---|
| macOS (Homebrew) | `brew install pango` |
| Debian / Ubuntu | `sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi-dev` |
| Fedora / RHEL | `sudo dnf install pango pango-devel` |

The install script handles this automatically.

## Quick start

```bash
git clone https://github.com/macraj/marktext-py.git
cd marktext-py
./install.sh
./run.sh
```

The editor opens at **http://localhost:8080** in your default browser.

## Manual setup

If you prefer to set things up yourself:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python dependencies
uv sync

# Install Pango for PDF export (macOS example)
brew install pango

# Run
uv run python main.py
```

## Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Cmd/Ctrl + S` | Save |
| `Cmd/Ctrl + B` | Bold |
| `Cmd/Ctrl + I` | Italic |
| `Cmd/Ctrl + K` | Insert link |

## Project structure

```
marktext-py/
├── main.py              # App entry point and UI layout
├── editor/
│   ├── markdown_editor.py   # CodeMirror-based editor component
│   ├── preview.py           # Live Markdown preview renderer
│   ├── toolbar.py           # Formatting toolbar
│   └── modes.py             # Edit modes (split, source, typewriter, focus)
├── export/
│   ├── pdf_export.py        # PDF export via WeasyPrint
│   └── html_export.py       # HTML export
├── file_manager/
│   └── file_ops.py          # File I/O, recent files, path utilities
├── themes/
│   ├── theme_manager.py     # Theme loading and persistence
│   └── css/                 # Theme stylesheets (6 themes)
├── static/
│   └── custom.js            # CodeMirror cursor helpers
├── install.sh               # One-step installer
└── run.sh                   # Launch script
```

## License

MIT
