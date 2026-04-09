import re
from nicegui import ui
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin

try:
    from mdit_py_plugins.tasklists import tasklists_plugin
    _HAS_TASKLISTS = True
except ImportError:
    _HAS_TASKLISTS = False

# Minimal emoji map — extend as needed
EMOJI = {
    'smile': '😊', 'laughing': '😆', 'heart': '❤️', 'thumbsup': '👍',
    'thumbsdown': '👎', 'fire': '🔥', 'star': '⭐', 'check': '✅',
    'x': '❌', 'warning': '⚠️', 'rocket': '🚀', 'wave': '👋',
    'clap': '👏', 'eyes': '👀', 'bulb': '💡', 'tada': '🎉',
    'bug': '🐛', 'zap': '⚡', 'memo': '📝', 'book': '📖',
    'link': '🔗', 'lock': '🔒', 'key': '🔑', 'hammer': '🔨',
    'wrench': '🔧', 'gear': '⚙️', 'sparkles': '✨', 'art': '🎨',
}

_EMOJI_RE = re.compile(r':([a-z0-9_+-]+):')
_MATH_INLINE_RE = re.compile(r'\$(?!\$)(.+?)(?<!\$)\$')
_MATH_BLOCK_RE  = re.compile(r'\$\$\n?([\s\S]+?)\n?\$\$')


def _replace_emoji(text: str) -> str:
    return _EMOJI_RE.sub(lambda m: EMOJI.get(m.group(1), m.group(0)), text)


def _protect_math(text: str) -> tuple[str, list[str]]:
    """Replace math spans with HTML-comment placeholders that survive markdown-it."""
    stash: list[str] = []

    def stash_block(m):
        stash.append(f'<span class="math-block">\\[{m.group(1)}\\]</span>')
        return f'<!--MATHSTASH:{len(stash)-1}-->'

    def stash_inline(m):
        stash.append(f'<span class="math-inline">\\({m.group(1)}\\)</span>')
        return f'<!--MATHSTASH:{len(stash)-1}-->'

    text = _MATH_BLOCK_RE.sub(stash_block, text)
    text = _MATH_INLINE_RE.sub(stash_inline, text)
    return text, stash


_STASH_RE = re.compile(r'<!--MATHSTASH:(\d+)-->')


def _restore_math(html: str, stash: list[str]) -> str:
    return _STASH_RE.sub(lambda m: stash[int(m.group(1))], html)


def _highlight_code(code: str, lang: str, attrs: str) -> str:
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, TextLexer
        from pygments.formatters import HtmlFormatter
        try:
            lexer = get_lexer_by_name(lang) if lang else TextLexer()
        except Exception:
            lexer = TextLexer()
        return highlight(code, lexer, HtmlFormatter())
    except Exception:
        return f'<pre><code>{code}</code></pre>'


_md_builder = (
    MarkdownIt('commonmark', {
        'highlight': _highlight_code,
        'html': True,
        'linkify': True,
        'typographer': True,
    })
    .use(front_matter_plugin)
    .use(footnote_plugin)
)
if _HAS_TASKLISTS:
    _md_builder = _md_builder.use(tasklists_plugin)

md = _md_builder


def render(text: str) -> str:
    """Full pipeline: math protection → emoji → markdown → restore math."""
    text, stash = _protect_math(text)
    text = _replace_emoji(text)
    html = md.render(text)
    html = _restore_math(html, stash)
    return html


# KaTeX loaded from CDN for math rendering
KATEX_HEAD = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {
        delimiters: [
            {left: '\\\\[', right: '\\\\]', display: true},
            {left: '\\\\(', right: '\\\\)', display: false}
        ],
        throwOnError: false
    });"></script>
"""

PREVIEW_CSS = """
<style>
.md-preview {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 16px;
    line-height: 1.7;
    color: var(--text, #d4d4d4);
    padding: 2rem 3rem;
    max-width: 860px;
    margin: 0 auto;
}
.md-preview h1, .md-preview h2, .md-preview h3,
.md-preview h4, .md-preview h5, .md-preview h6 {
    color: var(--heading, #e8e8e8);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
}
.md-preview h1 { font-size: 2em; border-bottom: 1px solid var(--border,#444); padding-bottom: 0.3em; }
.md-preview h2 { font-size: 1.5em; border-bottom: 1px solid var(--border,#333); padding-bottom: 0.2em; }
.md-preview code {
    background: var(--code-bg, #2d2d2d);
    color: var(--code-fg, #e6db74);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.9em;
}
.md-preview pre {
    background: var(--pre-bg, #1e1e1e);
    border: 1px solid var(--border, #3a3a3a);
    border-radius: 6px;
    padding: 1em;
    overflow-x: auto;
}
.md-preview pre code { background: none; padding: 0; color: inherit; }
.md-preview blockquote {
    border-left: 4px solid var(--blockquote-border, #555);
    margin: 1em 0;
    padding: 0.5em 1em;
    color: var(--text-dim, #999);
    background: var(--blockquote-bg, #1a1a1a);
}
.md-preview a { color: var(--accent, #6699cc); text-decoration: none; }
.md-preview a:hover { text-decoration: underline; }
.md-preview table { border-collapse: collapse; width: 100%; margin: 1em 0; }
.md-preview th, .md-preview td { border: 1px solid var(--border,#444); padding: 0.5em 1em; }
.md-preview th { background: var(--th-bg, #2a2a2a); color: var(--heading, #e8e8e8); }
.md-preview tr:nth-child(even) { background: var(--table-even, #1e1e1e); }
.md-preview img { max-width: 100%; }
.md-preview hr { border: none; border-top: 1px solid var(--hr,#444); margin: 2em 0; }
.highlight { background: var(--pre-bg, #1e1e1e) !important; }
/* Checkboxes from tasklist plugin */
.md-preview input[type=checkbox] { margin-right: 0.4em; }
/* Math */
.math-block { display: block; overflow-x: auto; margin: 1em 0; text-align: center; }
.math-inline { display: inline; }
</style>
"""


class Preview:
    def __init__(self):
        with ui.scroll_area().classes('w-full h-full').style('background: var(--bg, #1e1e1e)'):
            self._html = ui.html(PREVIEW_CSS)

    def update(self, markdown_text: str) -> None:
        rendered = render(markdown_text)
        self._html.set_content(
            PREVIEW_CSS + f'<div class="md-preview">{rendered}</div>'
        )
        # Trigger KaTeX to re-render math in the preview after HTML update
        ui.run_javascript(
            'if(window.renderMathInElement){'
            'renderMathInElement(document.querySelector(".md-preview"),{'
            'delimiters:[{left:"\\\\[",right:"\\\\]",display:true},'
            '{left:"\\\\(",right:"\\\\)",display:false}],'
            'throwOnError:false});}'
        )
