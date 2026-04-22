"""Export markdown to PDF via weasyprint."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from export.html_export import export_html


_OL_START_RE = re.compile(r'<ol\s+start=(["\'])(\d+)\1')
_CHECKBOX_RE = re.compile(r'<input[^>]*type=["\']checkbox["\'][^>]*>', re.IGNORECASE)

# Margin profiles: (top/bottom, left/right) in cm
MARGIN_PROFILES = {
    'compact':  (0.8, 1.0),
    'normal':   (1.5, 1.5),
    'spacious': (2.0, 2.0),
}


def _fix_ol_start(html: str) -> str:
    """Inject counter-reset so weasyprint honours <ol start="N">.

    Weasyprint 68.x ignores the HTML `start` attribute on ordered lists,
    so numbered lists that don't start at 1 render as 1, 2, 3, .... We
    work around it by adding an inline counter-reset that sets the
    `list-item` counter to N-1 before the first item.
    """
    def repl(m):
        quote = m.group(1)
        n = int(m.group(2))
        return (
            f'<ol start={quote}{n}{quote} '
            f'style="counter-reset: list-item {n - 1}"'
        )
    return _OL_START_RE.sub(repl, html)


def _fix_checkboxes(html: str) -> str:
    """Replace <input type="checkbox"> with unicode chars for weasyprint.

    Weasyprint renders checkbox inputs as replaced elements that break inline
    flow, putting the checkbox on its own line above the label text.
    """
    def repl(m: re.Match) -> str:
        return '☑' if 'checked' in m.group(0).lower() else '☐'
    return _CHECKBOX_RE.sub(repl, html)


def _detect_margin_profile(html: str) -> str:
    """Choose a margin profile based on content analysis.

    Returns 'compact', 'normal', or 'spacious'.
    """
    has_tables = bool(re.search(r'<table[\s>]', html, re.IGNORECASE))
    has_wide_code = bool(re.search(r'<pre[\s>]', html, re.IGNORECASE))

    text_only = re.sub(r'<[^>]+>', '', html)
    text_len = len(text_only.strip())

    # Count block-level elements to estimate document complexity
    headings = len(re.findall(r'<h[1-6][\s>]', html, re.IGNORECASE))
    paragraphs = len(re.findall(r'<p[\s>]', html, re.IGNORECASE))
    code_blocks = len(re.findall(r'<pre[\s>]', html, re.IGNORECASE))
    tables = len(re.findall(r'<table[\s>]', html, re.IGNORECASE))

    # Wide elements (tables, code blocks) benefit from compact margins
    wide_elements = code_blocks + tables
    if wide_elements >= 3 or (has_tables and has_wide_code):
        return 'compact'

    # Short documents (< ~1 page of text) use compact margins
    if text_len < 1500 and headings <= 3:
        return 'compact'

    # Long, text-heavy documents with many sections use spacious for readability
    if text_len > 8000 and headings >= 6 and paragraphs >= 15 and wide_elements == 0:
        return 'spacious'

    return 'normal'


def _build_page_css(
    page_size: str,
    margin_profile: str,
    page_numbers: bool = False,
    doc_title: str = '',
) -> str:
    """Build @page CSS rule for the given profile."""
    tb, lr = MARGIN_PROFILES[margin_profile]
    if not page_numbers:
        return f'@page {{ size: {page_size}; margin: {tb}cm {lr}cm; }}'

    safe_title = doc_title.replace('"', '\\"')
    label = '"Page " counter(page) " of " counter(pages)'
    if safe_title:
        label += f' " \u2014 {safe_title}"'
    footer_css = (
        f'@bottom-center {{'
        f' content: {label};'
        f' font-size: 9px;'
        f' color: #888;'
        f'}}'
    )
    return f'@page {{ size: {page_size}; margin: {tb}cm {lr}cm; {footer_css} }}'


PDF_EXTRA_CSS = """
body { font-size: 13px; max-width: none; margin: 0; padding: 0; }
pre { white-space: pre-wrap; word-wrap: break-word; }
"""


def _needs_brew_env() -> bool:
    """Check if we need DYLD_LIBRARY_PATH for Homebrew libs on macOS."""
    if sys.platform != 'darwin':
        return False
    if 'DYLD_LIBRARY_PATH' in os.environ:
        return False
    brew_lib = '/opt/homebrew/lib'
    return os.path.isdir(brew_lib)


_SUBPROCESS_SCRIPT = """\
import json, sys
from pathlib import Path
from weasyprint import HTML, CSS

args = json.loads(sys.stdin.read())
page_css = args["page_css"]
pdf_bytes = HTML(string=args["html"]).write_pdf(
    stylesheets=[CSS(string=page_css)]
)
dest = args.get("dest_path")
if dest:
    Path(dest).write_bytes(pdf_bytes)
else:
    sys.stdout.buffer.write(pdf_bytes)
"""


def export_pdf(
    markdown_html: str,
    title: str = 'Document',
    dark: bool = False,
    page_size: str = 'A4',
    dest_path: str | None = None,
    page_numbers: bool = False,
    doc_title: str = '',
) -> bytes:
    """Render markdown HTML to PDF bytes via weasyprint.

    Also writes to dest_path if provided. Returns raw PDF bytes.
    """
    margin_profile = _detect_margin_profile(markdown_html)
    page_css = _build_page_css(page_size, margin_profile, page_numbers=page_numbers, doc_title=doc_title)

    html_str = export_html(
        _fix_checkboxes(_fix_ol_start(markdown_html)),
        title=title,
        dark=dark,
        extra_css=PDF_EXTRA_CSS,
    )

    if _needs_brew_env():
        payload = json.dumps({
            'html': html_str,
            'page_css': page_css,
            'page_size': page_size,
            'dest_path': dest_path,
        })
        env = {**os.environ, 'DYLD_LIBRARY_PATH': '/opt/homebrew/lib'}
        result = subprocess.run(
            [sys.executable, '-c', _SUBPROCESS_SCRIPT],
            input=payload, text=True,
            env=env, capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        pdf_bytes = Path(dest_path).read_bytes() if dest_path else result.stdout
    else:
        from weasyprint import HTML, CSS
        pdf_bytes = HTML(string=html_str).write_pdf(
            stylesheets=[CSS(string=page_css)]
        )
        if dest_path:
            Path(dest_path).write_bytes(pdf_bytes)

    return pdf_bytes
