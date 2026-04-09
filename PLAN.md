# MarkText-Py: Pure Python Markdown Editor

## Context
Build a MarkText-inspired markdown editor as a pure Python web app using **NiceGUI** with **weasyprint** for PDF export. The app runs locally in the browser and provides a full-featured markdown editing experience.

**Project location:** `~/Documents/marktext-py/`
**Python:** 3.14.3 (homebrew)
**Package manager:** `uv`

---

## Architecture

Single-file entry point (`main.py`) with modular components:

```
~/Documents/marktext-py/
├── main.py                  # App entry point, NiceGUI server
├── editor/
│   ├── __init__.py
│   ├── markdown_editor.py   # Core editor component (CodeMirror via NiceGUI)
│   ├── preview.py           # Live preview renderer
│   ├── toolbar.py           # Toolbar with formatting buttons
│   └── modes.py             # Edit modes (source, typewriter, focus)
├── export/
│   ├── __init__.py
│   ├── pdf_export.py        # weasyprint PDF generation
│   └── html_export.py       # HTML export
├── themes/
│   ├── __init__.py
│   ├── theme_manager.py     # Theme switching logic
│   └── css/                 # Theme CSS files
│       ├── cadmium_light.css
│       ├── dark.css
│       ├── material_dark.css
│       ├── one_dark.css
│       ├── graphite_light.css
│       └── ulysses_light.css
├── file_manager/
│   ├── __init__.py
│   └── file_ops.py          # Open/save/recent files
├── static/
│   └── custom.js            # Client-side JS for clipboard image paste, etc.
└── pyproject.toml
```

## Key Technology Choices

| Component | Library | Why |
|-----------|---------|-----|
| Package manager | **uv** | Fast, modern Python package/project manager |
| UI framework | **NiceGUI 2.x** | Web-based, Python-only, supports custom JS/CSS |
| Code editor | **CodeMirror 6** (via `ui.codemirror`) | NiceGUI has built-in CodeMirror with markdown mode |
| Markdown parsing | **markdown-it-py** | CommonMark + GFM + extensions (math, frontmatter, emoji) |
| Math rendering | **KaTeX** (JS, loaded via CDN) | Fast client-side math rendering |
| PDF export | **weasyprint** | Pure Python HTML→PDF, good CSS support |
| Image paste | Custom JS snippet | Intercept paste event, convert to base64/save to disk |

## Setup Commands

```bash
cd ~/Documents/marktext-py
uv init
uv add nicegui markdown-it-py mdit-py-plugins weasyprint pygments
```

Run with:
```bash
uv run python main.py
```

## Implementation Plan (Phased)

### Phase 1: Project Setup & Core Editor
1. Init project with `uv init` + `pyproject.toml`
2. Set up NiceGUI app with basic layout (sidebar + main area)
3. Integrate CodeMirror editor with markdown syntax highlighting
4. Add live preview panel using markdown-it-py rendering
5. Wire up real-time sync: editor changes → preview updates

### Phase 2: File Operations
6. Open file dialog (NiceGUI `ui.upload` + native file picker)
7. Save file (download or write to local path)
8. Recent files list in sidebar
9. New file / unsaved changes detection

### Phase 3: Toolbar & Formatting
10. Toolbar component: bold, italic, heading, link, image, code block, list, quote, table
11. Each button inserts/wraps markdown syntax in editor
12. Keyboard shortcuts (Ctrl+B, Ctrl+I, etc.)

### Phase 4: Export
13. HTML export — render markdown to styled HTML file
14. PDF export — markdown → HTML → weasyprint → PDF
15. Export dialog with options (include CSS theme, page size)

### Phase 5: Themes
16. Create 6 theme CSS files matching MarkText themes
17. Theme manager — switch themes, persist preference
18. Apply theme to both editor and preview panes

### Phase 6: Edit Modes
19. **Source Code mode** — plain CodeMirror, no preview
20. **Typewriter mode** — current line always centered
21. **Focus mode** — dim all paragraphs except current

### Phase 7: Advanced Features
22. KaTeX math rendering in preview (`$...$` and `$$...$$`)
23. YAML front matter parsing and display
24. Emoji support (`:emoji_name:` → unicode)
25. Clipboard image paste (JS intercept → save to disk → insert `![](path)`)
26. Word/character count in status bar

## Verification

1. `uv run python main.py` → opens browser at localhost:8080
2. Type markdown → verify live preview updates
3. Open/save `.md` files
4. Switch themes → verify editor + preview restyle
5. Toggle modes (source/typewriter/focus)
6. Export PDF → verify rendered output
7. Type `$E=mc^2$` → verify KaTeX renders
8. Paste image from clipboard → verify insertion
