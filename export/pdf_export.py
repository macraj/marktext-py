"""Export markdown to PDF via weasyprint."""
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
    from weasyprint import HTML, CSS

    page_css = f'@page {{ size: {page_size}; margin: 2.5cm 2cm; }}'
    html_str = export_html(markdown_html, title=title, dark=dark)
    pdf_bytes = HTML(string=html_str).write_pdf(
        stylesheets=[CSS(string=page_css)]
    )
    if dest_path:
        Path(dest_path).write_bytes(pdf_bytes)
    return pdf_bytes
