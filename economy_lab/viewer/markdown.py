"""Markdown to HTML, standard library only (docs/48 section 2.6).

Handles what the design and results documents actually use: ATX and
setext headings, paragraphs, bulleted and numbered lists with one level of
nesting, fenced code, pipe tables with alignment, block quotes, horizontal
rules, emphasis, inline code and links.  A construct it does not know is
rendered as the text it was written as, which is a legible failure.
"""

from __future__ import annotations

import html
import re
from typing import List, Optional


_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_RULE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})\s*$")
_SETEXT = re.compile(r"^(?:=+|-+)\s*$")
_BULLET = re.compile(r"^(\s*)([-*+])\s+(.*)$")
_NUMBER = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
_FENCE = re.compile(r"^```\s*(\w*)\s*$")
_TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
_QUOTE = re.compile(r"^>\s?(.*)$")

_CODE_SPAN = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
_DOC_REF = re.compile(r"\bdocs/(\d{2})\b(?!-)")
_URL_SAFE = re.compile(r"^(?:https?://|#|/|[\w./-]+)$")


def _inline(text: str) -> str:
    """Escape, then mark up spans; code spans are protected first."""
    pieces: List[str] = []
    codes: List[str] = []

    def stash(match: "re.Match[str]") -> str:
        content = match.group(1)
        rendered = f"<code>{html.escape(content)}</code>"
        # The documents write their cross-references as `docs/NN`, in
        # backticks; those become links into the viewer.
        reference = re.fullmatch(r"docs/(\d{2})", content.strip())
        if reference:
            rendered = f'<a href="#doc/{int(reference.group(1))}">{rendered}</a>'
        codes.append(rendered)
        return f"\x00{len(codes) - 1}\x00"

    text = _CODE_SPAN.sub(stash, text)
    text = html.escape(text, quote=False)

    def link(match: "re.Match[str]") -> str:
        label, target = match.group(1), match.group(2)
        if not _URL_SAFE.match(target):
            return match.group(0)
        doc = re.match(r"^(?:\.\./)?docs/(\d{2})-.*\.md$", target) or re.match(
            r"^docs/(\d{2})$", target
        )
        href = f"#doc/{int(doc.group(1))}" if doc else target
        return f'<a href="{html.escape(href)}">{label}</a>'

    text = _LINK.sub(link, text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    text = _DOC_REF.sub(lambda m: f'<a href="#doc/{int(m.group(1))}">docs/{m.group(1)}</a>', text)
    for index, code in enumerate(codes):
        text = text.replace(f"\x00{index}\x00", code)
    pieces.append(text)
    return "".join(pieces)


def _table(lines: List[str]) -> str:
    def cells(line: str) -> List[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [cell.strip() for cell in line.split("|")]

    header = cells(lines[0])
    aligns: List[Optional[str]] = []
    for cell in cells(lines[1]):
        left, right = cell.startswith(":"), cell.endswith(":")
        aligns.append("center" if left and right else "right" if right else "left" if left else None)
    while len(aligns) < len(header):
        aligns.append(None)

    def row(values: List[str], tag: str) -> str:
        out = []
        for index, value in enumerate(values):
            align = aligns[index] if index < len(aligns) else None
            style = f' style="text-align:{align}"' if align else ""
            out.append(f"<{tag}{style}>{_inline(value)}</{tag}>")
        return "<tr>" + "".join(out) + "</tr>"

    body = "".join(row(cells(line), "td") for line in lines[2:])
    return f"<table><thead>{row(header, 'th')}</thead><tbody>{body}</tbody></table>"


def _list_items(lines: List[str], pattern: "re.Pattern[str]") -> str:
    """Render one list; an indented run under an item becomes a nested list."""
    items: List[str] = []
    index = 0
    while index < len(lines):
        match = pattern.match(lines[index])
        if match is None:
            index += 1
            continue
        indent = len(match.group(1))
        text = [match.group(3)]
        nested: List[str] = []
        index += 1
        while index < len(lines):
            line = lines[index]
            child = _BULLET.match(line) or _NUMBER.match(line)
            if child and len(child.group(1)) > indent:
                nested.append(line)
            elif child:
                break
            elif line.strip() == "":
                index += 1
                continue
            elif nested:
                nested.append(line)
            else:
                text.append(line.strip())
            index += 1
        inner = _inline(" ".join(text))
        if nested:
            first = _BULLET.match(nested[0]) or _NUMBER.match(nested[0])
            tag = "ul" if first is not None and first.re is _BULLET else "ol"
            inner += f"<{tag}>{_list_items(nested, first.re if first else _BULLET)}</{tag}>"
        items.append(f"<li>{inner}</li>")
    return "".join(items)


def render(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    out: List[str] = []
    paragraph: List[str] = []
    index = 0

    def flush() -> None:
        if paragraph:
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        fence = _FENCE.match(stripped)
        if fence:
            flush()
            language = fence.group(1)
            code: List[str] = []
            index += 1
            while index < len(lines) and not _FENCE.match(lines[index].strip()):
                code.append(lines[index])
                index += 1
            index += 1
            cls = f' class="language-{html.escape(language)}"' if language else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        if stripped == "":
            flush()
            index += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if _SETEXT.match(stripped) and paragraph:
            # A rule line directly under paragraph text is a setext heading.
            level = 1 if stripped.startswith("=") else 2
            out.append(f"<h{level}>{_inline(' '.join(paragraph))}</h{level}>")
            paragraph.clear()
            index += 1
            continue

        if _RULE.match(stripped):
            flush()
            out.append("<hr>")
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and _TABLE_SEPARATOR.match(lines[index + 1].strip()) and "|" in lines[index + 1]:
            flush()
            block = [line]
            index += 1
            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index])
                index += 1
            out.append(_table(block))
            continue

        quote = _QUOTE.match(line)
        if quote:
            flush()
            block = []
            while index < len(lines):
                inner = _QUOTE.match(lines[index])
                if inner is None:
                    break
                block.append(inner.group(1))
                index += 1
            out.append(f"<blockquote>{render(chr(10).join(block))}</blockquote>")
            continue

        bullet = _BULLET.match(line)
        number = _NUMBER.match(line)
        if (bullet or number) and not paragraph:
            flush()
            pattern = _BULLET if bullet else _NUMBER
            block = []
            while index < len(lines):
                current = lines[index]
                if current.strip() == "":
                    # A blank line ends the list unless another item of the
                    # same kind, or an indented continuation, follows.
                    lookahead = index + 1
                    if lookahead < len(lines) and (
                        pattern.match(lines[lookahead])
                        or (lines[lookahead].startswith("  ") and lines[lookahead].strip())
                    ):
                        block.append(current)
                        index += 1
                        continue
                    break
                if _HEADING.match(current) or _FENCE.match(current.strip()):
                    break
                if not (current.startswith(" ") or _BULLET.match(current) or _NUMBER.match(current)):
                    # Unindented text after an item continues the item.
                    block.append("  " + current)
                    index += 1
                    continue
                block.append(current)
                index += 1
            tag = "ul" if pattern is _BULLET else "ol"
            out.append(f"<{tag}>{_list_items(block, pattern)}</{tag}>")
            continue

        paragraph.append(stripped)
        index += 1

    flush()
    return "\n".join(out)


def title(text: str) -> str:
    """The first heading, as plain text, or an empty string."""
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            return re.sub(r"`", "", match.group(2)).strip()
    return ""
