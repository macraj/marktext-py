"""Export markdown to a self-contained HTML file."""
from pathlib import Path


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.7;
    color: {text_color};
    background: {bg_color};
    max-width: 860px;
    margin: 0 auto;
    padding: 2rem 3rem;
}}
h1, h2, h3, h4, h5, h6 {{
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
}}
h1 {{ font-size: 2em; border-bottom: 1px solid #ccc; padding-bottom: 0.3em; }}
h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }}
code {{
    background: {code_bg};
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.9em;
}}
pre {{
    background: {pre_bg};
    border: 1px solid {border_color};
    border-radius: 6px;
    padding: 1em;
    overflow-x: auto;
}}
pre code {{ background: none; padding: 0; }}
blockquote {{
    border-left: 4px solid #ccc;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #666;
}}
a {{ color: #0366d6; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
th, td {{ border: 1px solid {border_color}; padding: 0.5em 1em; }}
th {{ background: {th_bg}; }}
img {{ max-width: 100%; }}
hr {{ border: none; border-top: 1px solid {border_color}; margin: 2em 0; }}
{extra_css}
</style>
</head>
<body>
{body}
</body>
</html>
"""

DARK_THEME = dict(
    text_color='#d4d4d4',
    bg_color='#1e1e1e',
    code_bg='#2d2d2d',
    pre_bg='#181818',
    border_color='#444',
    th_bg='#2a2a2a',
    extra_css='',
)

LIGHT_THEME = dict(
    text_color='#24292e',
    bg_color='#ffffff',
    code_bg='#f6f8fa',
    pre_bg='#f6f8fa',
    border_color='#e1e4e8',
    th_bg='#f6f8fa',
    extra_css='',
)


def export_html(
    markdown_html: str,
    title: str = 'Document',
    dark: bool = False,
    dest_path: str | None = None,
) -> str:
    """Render markdown HTML into a full page and optionally write to disk.

    Returns the HTML string.
    """
    theme = DARK_THEME if dark else LIGHT_THEME
    html = HTML_TEMPLATE.format(title=title, body=markdown_html, **theme)
    if dest_path:
        Path(dest_path).write_text(html, encoding='utf-8')
    return html
