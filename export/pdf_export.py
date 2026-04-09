"""Export markdown to PDF via weasyprint."""
import json
import os
import subprocess
import sys
from pathlib import Path
from export.html_export import export_html


PDF_EXTRA_CSS = """
@page {
    size: A4;
    margin: 2.5cm 2cm;
}
@media print {
    pre { page-break-inside: avoid; }
    h1, h2, h3 { page-break-after: avoid; }
}
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

args = json.loads(sys.argv[1])
page_css = f'@page {{ size: {args["page_size"]}; margin: 2.5cm 2cm; }}'
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
) -> bytes:
    """Render markdown HTML to PDF bytes via weasyprint.

    Also writes to dest_path if provided. Returns raw PDF bytes.
    """
    html_str = export_html(markdown_html, title=title, dark=dark)

    if _needs_brew_env():
        args = json.dumps({
            'html': html_str,
            'page_size': page_size,
            'dest_path': dest_path,
        })
        env = {**os.environ, 'DYLD_LIBRARY_PATH': '/opt/homebrew/lib'}
        result = subprocess.run(
            [sys.executable, '-c', _SUBPROCESS_SCRIPT, args],
            env=env, capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode())
        pdf_bytes = Path(dest_path).read_bytes() if dest_path else result.stdout
    else:
        from weasyprint import HTML, CSS
        page_css = f'@page {{ size: {page_size}; margin: 2.5cm 2cm; }}'
        pdf_bytes = HTML(string=html_str).write_pdf(
            stylesheets=[CSS(string=page_css)]
        )
        if dest_path:
            Path(dest_path).write_bytes(pdf_bytes)

    return pdf_bytes
