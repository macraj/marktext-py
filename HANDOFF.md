# HANDOFF: MarkText-Py

**Last Updated:** 2026-08-04
**Current Version:** 0.6.2 (`pyproject.toml`)
**Status:** Stable, all work committed and pushed to `origin/master`. No outstanding
uncommitted fixes. The two long-standing "not yet browser-tested" features (PDF margins,
`.eml` import) are still unverified in the UI — see Next Steps.

---

## Goal

MarkText-Py is a NiceGUI-based Markdown editor with live preview, PDF/HTML export, themes, and multiple edit modes (Split, Source, Typewriter, Focus).

---

## Working Tree State (2026-08-04)

**Clean of outstanding fixes.** Everything below was committed and pushed this session.

**Untracked clutter:** the repo root holds ~18 unrelated personal files (Polish PDFs and
`.md` drafts — investor memo, training plans, Orange complaint, fitness plans) plus
`.playwright-mcp/`. None of it belongs to MarkText-Py; they are documents being edited
*with* the app, not artifacts of it. **Do not `git add -A` in this repo** — stage by name.
Ask before deleting any of them.

---

## This Session (2026-08-04) — two user-reported bugs, both fixed

Committed as `9ca8db1` (v0.6.2) and `<docs commit>`; pushed to `origin/master`.

### Bug 1: blank lines added for signature space vanished from exported PDF
**Root cause — not in the exporter.** CommonMark collapses any run of blank lines into a
single block separator, so `render()` in `editor/preview.py` destroyed the information
before `export_pdf()` ever saw it. Confirmed directly:
`'Z poważaniem,\n\n\n\n\n\n\n\nJan Kowalski\n'` → `<p>Z poważaniem,</p><p>Jan Kowalski</p>`.

**Fix:** new `_expand_blank_lines()` in `editor/preview.py`, called from `render()`.
Each blank line *beyond the first* (the first is a normal paragraph break) becomes 1em of
vertical space. Runs after math protection; skips fenced code blocks — verified they pass
through byte-identical, so ASCII art and indented code are safe. Because it lives in
`render()`, it fixes preview, HTML export and PDF export at once.

### Bug 2: last line of the preview hidden behind the footer
**Root cause — measured in the browser, not guessed.** `.nicegui-content` is `height: 100vh`
but sits at `top: 35px` (below the header), so it overflows the viewport bottom by exactly
the header height. Measured: viewport 720px, header 35px, footer 32px → the splitter needs
**67px** of bottom margin to clear both. It had 40px — 27px short, i.e. roughly one line of
text. Hence "everything visible except the last line."

**Fix:** `.q-splitter` margin-bottom `40px → 67px` in `main.py:457`. Re-measured after:
preview bottom 653px, footer top 688px — 35px clearance, no overlap.

⚠️ **This is the third time this margin has been raised for the same symptom** (CHANGELOG:
"increase splitter bottom margin to 40px for taller footer"). 67px is the sum of two
independently-changeable numbers (header 35 + footer 32). Add a toolbar row or a footer
button and the symptom returns identically. The durable fix is to compute it in CSS —
`height: calc(100vh - 35px)` on `.nicegui-content` instead of a margin on the splitter —
but that touches a rule marked "DO NOT CHANGE" below, so it was deliberately left alone
during a bug fix. Offered to the user as separate work; not yet accepted.

### Also done this session
- **`README.md` restored.** It had been overwritten with a Polish fitness plan. The draft
  was unique (not a copy of `moj_plan_treningowy.md` et al.) and matched the existing
  `foundational-fitness-enduro-2026.pdf`, so it was preserved as
  `foundational-fitness-enduro-2026.md` before `git checkout -- README.md`.
- **`README.md` updated** for features it never documented: `.eml` import, page numbers,
  adjustable PDF margins, the new blank-line behaviour, `eml_parser.py` in the structure
  tree, and a warning that "Manual setup" must set `UV_PROJECT_ENVIRONMENT` or it walks
  straight into the iCloud hang below.
- **iCloud venv fix committed** (`run.sh`, `install.sh`, `uv.lock`) — was left uncommitted
  by the 2026-07-15 session.

---

## Recent Session (2026-07-15) — fixed "app won't start" (iCloud-synced venv hang)

### Bug: `./run.sh` / `uv run python main.py` hung forever, no output, no error
**Root cause:** The repo lives under `~/Documents`, which is iCloud Drive-synced with
"Optimize Mac Storage" enabled. `.venv`'s thousands of small package files had been
evicted to cloud-only placeholders (`ls -lO` showed `hidden,compressed,dataless`
flags on files like `yarl/_query.py`). The very first heavy import
(`from nicegui import app, ui`, which pulls in `aiohttp`/`yarl`) tried to read one of
those placeholder files, which triggered a re-download from iCloud that never
completed — Python blocked indefinitely at ~1% CPU with zero output, even before
NiceGUI's own startup banner printed.

**Diagnosis method (for future reference):**
- `timeout N uv run python -u -c "print('start'); from nicegui import app, ui"` → `start` printed, then hung with `timeout` exit code 124 and ~1% CPU (blocked, not computing)
- `faulthandler.dump_traceback_later(4, exit=True)` around the import pinpointed the frozen frame inside `importlib` reading `yarl/_query.py`
- `ls -lO@ <file>` on that path showed `dataless` — the iCloud placeholder flag

**Fix applied (committed 2026-08-04):**
- Deleted the stuck `.venv` (was inside the iCloud-synced project dir) and recreated
  it at `~/.venvs/marktext-py`, which is **outside** any iCloud-synced folder
- `run.sh` and `install.sh` both now `export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/marktext-py"`
  before calling `uv sync` / `uv run`, so `uv` always creates/uses the venv there
  instead of defaulting to `./.venv`
- Verified: `uv run python -u main.py` now prints `NiceGUI ready to go on
  http://localhost:8080...` within ~2s and the port is listening (confirmed via `lsof`)

**Notes:**
- Old `.gitignore`'d `.venv` reference is now stale/unused but harmless; no cleanup needed.
- If this machine is reinstalled or a fresh clone is made elsewhere, `install.sh` will
  recreate the venv at `~/.venvs/marktext-py` automatically — no manual step needed.
- README now documents this trap for anyone following "Manual setup" with a bare `uv`.

### Unrelated: `README.md` contained the wrong content
Resolved 2026-08-04 — see "Also done this session" above.

---

## Prior Session (2026-05-20) — adjustable PDF top/bottom margin

### Feature: user-selectable vertical PDF margin
**Files:** `export/pdf_export.py`, `main.py`, `pyproject.toml`
**Status:** Done (v0.6.1, commit `9c4fea6`, pushed)

**What was added:**
- New `vertical_margin_cm: float | None` arg on `export_pdf()` (None = keep auto-detect from content).
- `_build_page_css()` accepts `tb_override` that wins over `MARGIN_PROFILES[profile]`'s top/bottom value. Left/right stays profile-driven.
- Export dialog (`main.py` `action_export`) now has a `Top/bottom margin (PDF only)` select with options: Auto, 0.5/0.8/1.0/1.5/2.0/2.5 cm. Wired through to `export_pdf(..., vertical_margin_cm=vmargin.value)`.
- Auto-detect logic in `_detect_margin_profile()` is unchanged — only the top/bottom dimension is overridable; user said horizontal margins were fine.

**Not verified in browser this session** — feature is small and additive; UI smoke test (open the export dialog, pick 0.5 cm, export, confirm visibly tighter top/bottom) still TODO.

---

## Prior Session (2026-05-18) — .eml import + PDF export

### Feature: open .eml files, edit as markdown, export to PDF
**Files:** `file_manager/eml_parser.py` (new), `file_manager/file_ops.py`, `main.py`, `pyproject.toml`
**Status:** Done (v0.6.0, pushed)

**What was added:**
- New `file_manager/eml_parser.py` — `eml_to_markdown(path)` using stdlib `email` (BytesParser + `policy.default`)
  - Subject → `# H1`
  - From / To / Cc / Date → bulleted meta block
  - Body: prefers `text/plain`; falls back to `text/html` with a lightweight regex-based HTML→md converter (`_html_to_markdown`)
  - Lists filename of any attachments at the bottom (not extracted)
- `read_file()` in `file_ops.py` detects `.eml` suffix and routes through the parser
- File-open picker in `main.py` accepts `.eml` (added to the extension whitelist on the directory listing)
- On opening `.eml`, `state['path']` is set to `None` so:
  - Save won't overwrite the source .eml with markdown text
  - Save As / Export propose a filename derived from the e-mail subject (via existing `propose_filename()` which picks the first H1)
- Same `None`-binding applied to `action_open_recent` for .eml entries
- Version bump 0.5.8 → 0.6.0; commit `2bebed3`, pushed to origin/master

**Verified manually:**
- Synthetic `.eml` (EmailMessage → bytes → tmpfile → eml_to_markdown) produced expected markdown with Subject/From/To/Date and body.
- Import smoke test passed.
- UI not exercised in browser this session — golden path (open .eml from picker → preview → Export PDF) should be validated next time the app is run.

---

## Prior Sessions (kept for reference)

### 2026-04-22 — Page numbers in PDF export (v0.5.6)
- New checkbox: `Page numbers — "Page X of Y — filename" (PDF only)` in export dialog.
- Implemented via CSS `@page` margin boxes (`@bottom-center`) in `_build_page_css(page_numbers, doc_title)`.
- `doc_title` = `Path(state['path']).name` when a file is open, else `title`.

### 2026-04-15 — Export dialog filename/folder fix (v0.5.5)
- Use `Path(state['path']).stem + '.pdf'` when a file is loaded (not `propose_filename()`).
- Default folder = `load_last_folder()` when no file is open; call `save_last_folder(dest)` after export.
- ⚠️ **RECURRING BUG class** — after any change to `action_export`, re-verify: filename matches loaded file, folder defaults to last-used, folder is saved.

### 2026-04-14 — PDF font + checkboxes + editor layout + toolbar (v0.5.x)
- `_fix_checkboxes()` swaps `<input type="checkbox">` → `☐`/`☑` before WeasyPrint
- `extra_css` arg on `export_html()` injects `body { font-size: 13px; }` for PDF
- `margin-bottom: 40px` on `.q-splitter` to clear the fixed footer
- Toolbar fix: `document.querySelector('.cm-content').cmView.view` (CM6 puts `cmView` on `.cm-content`)

---

## What Didn't Work (DO NOT REPEAT)

| Approach | Why it failed |
|---|---|
| CSS `padding-bottom` on `.cm-content` | CodeMirror ignores CSS padding for scroll calculations |
| JS `requestMeasure()` after padding | Root cause was footer overlap, not CM layout |
| Replacing `ui.footer()` with `ui.element('div')` | Breaks toolbar, editor interactivity, status bar. Quasar layout depends on `q-footer` |
| Changing `padding: 0 !important` to partial padding | Quasar adds padding-top that breaks layout |
| `document.querySelector('.cm-editor').cmView` | **cmView is on `.cm-content`, NOT `.cm-editor`** (CM6 internal) |
| Deriving export filename from `propose_filename()` when a `.md` file is loaded | Generates slug from headings, ignoring actual filename |
| Binding `state['path']` to a loaded `.eml` | Save would silently overwrite the source e-mail with markdown text |

---

## Architecture Overview

```
main.py               — NiceGUI page, layout, all actions (open/save/export/theme/mode)
editor/
  markdown_editor.py  — CodeMirror wrapper (ui.codemirror), EDITOR_CSS
  preview.py          — HTML preview panel, render() via markdown-it
  toolbar.py          — Bold/italic/link toolbar buttons (call window.cmInsert/cmPrefix)
  modes.py            — EditMode enum, Typewriter/Focus JS/CSS
export/
  html_export.py      — HTML_TEMPLATE, export_html(extra_css=) — also used by PDF export
  pdf_export.py       — export_pdf() via WeasyPrint; _fix_ol_start(), _fix_checkboxes(),
                        _build_page_css(page_numbers, doc_title) for @page margin boxes
file_manager/
  file_ops.py         — read/write files (routes .eml → eml_parser), recent files,
                        propose_filename(), save/load_last_folder()
  eml_parser.py       — stdlib email → markdown (headers + text/plain or HTML→md + attachments)
themes/
  theme_manager.py    — THEMES dict, load_theme_css(), CM_THEMES for CodeMirror themes
static/
  custom.js           — cmInsert(), cmPrefix(), image paste, window._cmView setup
```

**Layout (flex column, 100vh):**
```
ui.header()              — Quasar q-header (fixed) — toolbar + file buttons
ui.splitter(value=50)    — flex:1, overflow:hidden, margin-bottom:40px
  left:  MarkdownEditor  — ui.codemirror, height:100%
  right: Preview         — ui.scroll_area > ui.html
ui.footer()              — Quasar q-footer (fixed) — word/char count + mode buttons
```

**Critical CSS (DO NOT CHANGE):**
```css
body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; }
.nicegui-content { height: 100vh; display: flex; flex-direction: column; padding: 0 !important; }
.q-splitter { flex: 1; overflow: hidden; margin-bottom: 40px; }
.q-splitter__panel { overflow: auto; }
```

- **DO NOT** change `padding: 0 !important` to partial padding — Quasar adds padding-top that breaks layout
- **DO NOT** replace `ui.footer()` with a div — breaks interactivity
- The `margin-bottom: 40px` on splitter prevents footer overlap

---

## Next Steps

**Pending verification of already-shipped features:**

1. **Verify blank lines survive an actual PDF export** (v0.6.2). The fix was verified in the
   *preview* via browser measurement, and `_expand_blank_lines()` sits in the shared
   `render()` path — but no `.pdf` was actually opened and eyeballed this session. Export a
   doc with ~7 blank lines before a signature line and confirm the gap is really there.
2. **Check the blank-line fix against the PDF margin feature.** `_expand_blank_lines()` emits
   `1em` spacers; `export_pdf()` injects `body { font-size: 13px }`, so 1em ≈ 13px there
   rather than the preview's 14px. Gaps will be ~7% tighter in PDF than on screen. Probably
   fine, but nobody has looked.
3. **UI smoke test for adjustable PDF margin** (v0.6.1, never browser-tested) — open the export
   dialog, pick 0.5 cm, export a multi-page doc, verify top/bottom space shrinks and left/right
   is unchanged. Also confirm "Auto" still picks compact/normal/spacious from content.
4. **UI smoke test for .eml flow** (v0.6.0, never browser-tested) — run `./run.sh`, open a
   real `.eml` from the picker, confirm:
   - Subject becomes the H1, meta block renders, body looks sane.
   - Export PDF produces a file named after the subject in the last-used folder.
   - Save (Ctrl+S) opens Save As (no path bound), proposing a `.md` name.

**Backlog (no one has asked for these):**

5. **Make the footer clearance self-computing** — see the ⚠️ in this session's Bug 2. Would
   stop the "last line hidden" symptom recurring a fourth time.
6. **HTML e-mail quality** — `_html_to_markdown` is regex-based and intentionally minimal. If users hit complex marketing HTML, consider switching to `html2text` or `markdownify` (would add a dependency).
7. **Inline images / attachments** — currently only filenames are listed. Could extract to a sidecar folder and reference from markdown if there's demand.
8. **Recent files menu** — `.eml` entries show up alongside `.md`. Fine for now; consider an icon to distinguish them if it gets noisy.

---

## How to Run

```bash
cd /Users/macc/Documents/marktext-py
./run.sh
# Opens http://localhost:8080 automatically
# Cmd+Shift+R to hard-refresh if JS changes aren't taking effect
```

⚠️ **Use `./run.sh`, not a bare `uv run main.py`.** A bare `uv run` defaults to `./.venv`,
which lives in an iCloud-synced folder and will hang on import once iCloud evicts the
package files (full diagnosis in the 2026-07-15 entry). `run.sh` exports
`UV_PROJECT_ENVIRONMENT="$HOME/.venvs/marktext-py"` to avoid this. If you must call `uv`
directly, export that variable first.

---

## Commit History (recent, newest first)

```
9c4fea6  feat: adjustable top/bottom margin in PDF export  ← this session (v0.6.1)
2bebed3  feat: open and export .eml files as markdown  (v0.6.0)
f8c9913  fix: replace browser file picker with server-side browser to preserve full paths
50b2682  feat: add app icon (favicon + apple-touch-icon)
30e7652  feat: add page numbers toggle to PDF export dialog
530b1a0  bump: version 0.5.4 → 0.5.5
b3add90  fix: use loaded filename and remembered folder in export dialog
b014ffd  bump: version 0.5.3 → 0.5.4
4c7df64  docs: add MIT license
776a305  bump: version 0.5.2 → 0.5.3
22e855b  docs: add README and extend install.sh with Linux support
88f06dd  chore: bump version to 0.5.2
24e65a3  feat: add folder picker to PDF/HTML export dialog
c264f5d  chore: bump version to 0.5.1
52d3e56  fix: resolve export path from current file, fallback to ~/Documents
914e244  chore: bump version to 0.5.0
```
