## v0.5.3 (2026-04-15)

## v0.5.2 (2026-04-15)

### Bug Fixes

- resolve export path from current file, fallback to ~/Documents
- find EditorView via .cm-content.cmView.view
- get CodeMirror view from NiceGUI component instead of DOM property
- increase splitter bottom margin to 40px for taller footer
- revert to original padding and add margin-bottom on splitter
- restore ui.footer() and preserve Quasar vertical padding
- restore status bar visibility after footer refactor
- replace q-footer with plain div to stop it overlapping editor
- scroll past end via JS requestMeasure instead of CSS
- allow scrolling past last line in editor

### Features

- add folder picker to PDF/HTML export dialog
- smart PDF margins based on content analysis

## v0.4.0 (2026-04-14)

### Bug Fixes

- show filename in title bar after opening file via browser picker
- use padding instead of margin on hr to prevent CSS margin collapsing
- prevent margin collapsing on horizontal rules
- increase vertical spacing around horizontal rules
- increase horizontal padding in preview panel
- graceful shutdown on Ctrl+C without traceback
- live preview refresh and improve CSS layout for preview panel

### Features

- auto-open browser window on startup

## v0.3.0 (2026-04-10)

### Bug Fixes

- update browser tab title on file open, improve PDF export reliability, add install/run scripts
- enable markdown table rendering and fix PDF export on macOS

## v0.2.7 (2026-04-09)

### Bug Fixes

- attach file-input onchange via JS — Vue v-html strips inline handlers

## v0.2.6 (2026-04-09)

### Bug Fixes

- close Open dialog automatically after file picked via Browse

## v0.2.5 (2026-04-09)

### Bug Fixes

- use HTML label+input for file picker to preserve user gesture context

## v0.2.4 (2026-04-09)

### Bug Fixes

- replace ui.upload with native JS file picker for Open

## v0.2.3 (2026-04-09)

### Bug Fixes

- open via upload now works — defer load until Open button click

## v0.2.2 (2026-04-09)

### Bug Fixes

- replace broken hidden-upload open button with proper dialog

## v0.2.1 (2026-04-09)

### Bug Fixes

- add missing top-level import os — save dialog silently crashed

## v0.2.0 (2026-04-09)

### Bug Fixes

- save now reads from state['content'] (server-side value was stale)
feat: intelligent filename proposal from first heading/line + last folder

### Features

- Phase 6-7 — edit modes, math, emoji, word count
- Phase 5 — six themes with live switching and persistence
- Phase 4 — HTML and PDF export
- Phase 3 — toolbar formatting and keyboard shortcuts
- Phase 2 — file operations (open, save, save as, recent)
- Phase 1 — core editor with live markdown preview
