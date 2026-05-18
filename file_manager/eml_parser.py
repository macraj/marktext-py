"""Parse .eml e-mail files into Markdown."""
from pathlib import Path
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, getaddresses
from email.message import EmailMessage
import re


def _decode_header(value: str | None) -> str:
    if not value:
        return ''
    return str(value).strip()


def _format_addrs(value: str | None) -> str:
    if not value:
        return ''
    parts = []
    for name, addr in getaddresses([value]):
        if name and addr:
            parts.append(f'{name} <{addr}>')
        elif addr:
            parts.append(addr)
        elif name:
            parts.append(name)
    return ', '.join(parts)


def _html_to_markdown(html: str) -> str:
    """Very lightweight HTML→Markdown — good enough for most e-mails."""
    s = html
    # Strip scripts/styles
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S | re.I)
    # Line breaks / paragraphs
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'</p\s*>', '\n\n', s, flags=re.I)
    s = re.sub(r'<p[^>]*>', '', s, flags=re.I)
    # Headings
    for i in range(1, 7):
        s = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>',
                   lambda m, lvl=i: '\n' + '#' * lvl + ' ' + m.group(1).strip() + '\n',
                   s, flags=re.S | re.I)
    # Bold / italic
    s = re.sub(r'<(b|strong)[^>]*>(.*?)</\1>', r'**\2**', s, flags=re.S | re.I)
    s = re.sub(r'<(i|em)[^>]*>(.*?)</\1>', r'*\2*', s, flags=re.S | re.I)
    # Links
    s = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
               r'[\2](\1)', s, flags=re.S | re.I)
    # Lists
    s = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', s, flags=re.S | re.I)
    s = re.sub(r'</?(ul|ol)[^>]*>', '\n', s, flags=re.I)
    # Strip all remaining tags
    s = re.sub(r'<[^>]+>', '', s)
    # Decode common entities
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&')
           .replace('&lt;', '<').replace('&gt;', '>')
           .replace('&quot;', '"').replace('&#39;', "'"))
    # Collapse excessive blank lines
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def _extract_body(msg: EmailMessage) -> tuple[str, bool]:
    """Return (markdown_body, was_html)."""
    text_part = None
    html_part = None

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get('Content-Disposition') or '').lower()
            if 'attachment' in disp:
                continue
            if ctype == 'text/plain' and text_part is None:
                text_part = part
            elif ctype == 'text/html' and html_part is None:
                html_part = part
    else:
        if msg.get_content_type() == 'text/html':
            html_part = msg
        else:
            text_part = msg

    if text_part is not None:
        try:
            body = text_part.get_content()
        except Exception:
            body = text_part.get_payload(decode=True)
            if isinstance(body, bytes):
                body = body.decode(text_part.get_content_charset() or 'utf-8',
                                   errors='replace')
        return body.strip(), False

    if html_part is not None:
        try:
            html = html_part.get_content()
        except Exception:
            payload = html_part.get_payload(decode=True)
            html = payload.decode(html_part.get_content_charset() or 'utf-8',
                                  errors='replace') if isinstance(payload, bytes) else payload
        return _html_to_markdown(html), True

    return '', False


def _list_attachments(msg: EmailMessage) -> list[str]:
    names = []
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get('Content-Disposition') or '').lower()
            fname = part.get_filename()
            if fname and ('attachment' in disp or 'inline' in disp):
                names.append(fname)
    return names


def eml_to_markdown(path: str) -> str:
    """Read an .eml file and convert it to a Markdown document."""
    raw = Path(path).read_bytes()
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    subject = _decode_header(msg.get('Subject')) or '(no subject)'
    from_ = _format_addrs(msg.get('From'))
    to_ = _format_addrs(msg.get('To'))
    cc_ = _format_addrs(msg.get('Cc'))
    date_ = _decode_header(msg.get('Date'))

    body, _ = _extract_body(msg)
    attachments = _list_attachments(msg)

    lines = [f'# {subject}', '']
    meta = []
    if from_:
        meta.append(f'- **From:** {from_}')
    if to_:
        meta.append(f'- **To:** {to_}')
    if cc_:
        meta.append(f'- **Cc:** {cc_}')
    if date_:
        meta.append(f'- **Date:** {date_}')
    if meta:
        lines.extend(meta)
        lines.append('')

    lines.append('---')
    lines.append('')
    lines.append(body)

    if attachments:
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('**Attachments:**')
        for name in attachments:
            lines.append(f'- {name}')

    return '\n'.join(lines)
