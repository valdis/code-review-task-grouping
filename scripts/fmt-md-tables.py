#!/usr/bin/env python3
"""Auto-format every GitHub-Flavored-Markdown table in a file so columns align.

Finds each contiguous run of table lines (a header row, a delimiter row of
`---`/`:--:` cells, then body rows), recomputes per-column widths, and rewrites
the run with padded cells. Alignment markers in the delimiter row are honored:

    |:---|   left      |:--:|  center     |---:|  right     |---|  default (left)

Display-width aware: emoji such as the ones used in this repo (status icons)
render roughly two terminal cells wide, so they are counted as width 2 when
padding — this keeps the *rendered* columns aligned, not just the byte counts.

Inline-markup stripping (default ON): editors with "conceal" markdown rendering
(e.g. vim with concealed `**bold**`/`*italic*`/`` `code` ``) hide the marker
characters when the cursor leaves the line, which *shrinks* the visible cell and
misaligns the table at runtime. To stay aligned in those editors, cell contents
are stripped of `**`, `__`, `*`, `_` and backtick markers before alignment, so
the stored text matches what the editor actually displays. Pass --keep-markup to
disable this and keep the raw `**…**`/`` `…` `` markers in the cells.

Usage:
    scripts/fmt-md-tables.py FILE...               # format in place
    scripts/fmt-md-tables.py --check FILE...       # exit 1 if any file would change
    scripts/fmt-md-tables.py --keep-markup FILE... # don't strip **bold**/`code`
    scripts/fmt-md-tables.py -                     # read stdin, write stdout
"""
from __future__ import annotations

import re
import sys
import unicodedata

# Code-point ranges that render as two cells in a monospace/terminal grid.
# (Covers the emoji + CJK/full-width blocks; enough for our docs.)
_WIDE_RANGES = (
    (0x1100, 0x115F),   # Hangul Jamo
    (0x2329, 0x232A),
    (0x2600, 0x27BF),   # misc symbols + dingbats (✅ ⚠ live near here)
    (0x2B00, 0x2BFF),
    (0x2E80, 0x303E),   # CJK radicals .. Kangxi
    (0x3041, 0x33FF),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),   # CJK unified
    (0xA000, 0xA4CF),
    (0xAC00, 0xD7A3),   # Hangul syllables
    (0xF900, 0xFAFF),
    (0xFE10, 0xFE19),
    (0xFE30, 0xFE6F),
    (0xFF00, 0xFF60),   # full-width forms
    (0xFFE0, 0xFFE6),
    (0x1F000, 0x1FAFF),  # emoji planes
    (0x20000, 0x3FFFD),
)


def _char_width(ch: str) -> int:
    cp = ord(ch)
    if unicodedata.combining(ch):
        return 0
    if ch == "\uFE0F":  # variation selector-16 (emoji presentation) — zero-width
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    for lo, hi in _WIDE_RANGES:
        if lo <= cp <= hi:
            return 2
    return 1


def display_width(s: str) -> int:
    return sum(_char_width(c) for c in s)


# Inline emphasis/code markers that a concealing editor hides. Order matters:
# strip the two-char markers (** __) before the one-char ones (* _).
_EMPHASIS_RE = (
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),   # **bold**
    (re.compile(r"__(.+?)__"), r"\1"),       # __bold__
    (re.compile(r"\*(.+?)\*"), r"\1"),       # *italic*
    (re.compile(r"(?<!\w)_(.+?)_(?!\w)"), r"\1"),  # _italic_ (word-boundary safe)
    (re.compile(r"`+([^`]+?)`+"), r"\1"),    # `code` / ``code``
)


def strip_inline_markup(cell: str) -> str:
    """Remove **bold**/*italic*/`code` markers from a cell.

    Matches what a concealing markdown editor displays, so widths computed from
    the result stay aligned even when the markers are visually hidden. Runs each
    rule to a fixed point so nested/adjacent markers collapse fully.
    """
    prev = None
    out = cell
    while out != prev:
        prev = out
        for pat, repl in _EMPHASIS_RE:
            out = pat.sub(repl, out)
    return out


def _pad(cell: str, width: int, align: str) -> str:
    gap = width - display_width(cell)
    if gap <= 0:
        return cell
    if align == "right":
        return " " * gap + cell
    if align == "center":
        left = gap // 2
        return " " * left + cell + " " * (gap - left)
    return cell + " " * gap  # left / default


def _split_row(line: str) -> list[str]:
    """Split a `| a | b |` row into trimmed cells (drop the outer empties)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    # Note: we don't support escaped pipes inside cells; the docs use \| which
    # is a literal pipe in rendered output but reads as an escaped pipe here.
    parts = s.split("|")
    # Re-join cells that were split on an escaped pipe (`\|`).
    cells, buf = [], ""
    for p in parts:
        if buf:
            buf = buf + "|" + p
        else:
            buf = p
        if buf.endswith("\\"):
            continue  # the trailing backslash escaped the pipe we just split on
        cells.append(buf.strip())
        buf = ""
    if buf:
        cells.append(buf.strip())
    return cells


def _is_delim_cell(cell: str) -> bool:
    c = cell.strip()
    return len(c) >= 3 and set(c) <= set(":-") and "-" in c


def _is_delim_row(line: str) -> bool:
    cells = _split_row(line)
    return bool(cells) and all(_is_delim_cell(c) for c in cells)


def _alignment(cell: str) -> str:
    c = cell.strip()
    left, right = c.startswith(":"), c.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left-explicit"
    return "left"


def _looks_like_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.count("|") >= 2


def format_table(block: list[str], strip_markup: bool = True) -> list[str]:
    """`block` is [header, delimiter, *body]; return aligned lines.

    When ``strip_markup`` is true (default), inline emphasis/code markers are
    removed from every header and body cell before alignment so the result lines
    up in editors that conceal those markers.
    """
    header = _split_row(block[0])
    delim = _split_row(block[1])
    body = [_split_row(r) for r in block[2:]]
    if strip_markup:
        header = [strip_inline_markup(c) for c in header]
        body = [[strip_inline_markup(c) for c in r] for r in body]
    ncols = max([len(header), len(delim)] + [len(r) for r in body])

    def norm(row: list[str]) -> list[str]:
        return row + [""] * (ncols - len(row))

    header = norm(header)
    delim = norm(delim) if any(delim) else [":-:"] * ncols
    body = [norm(r) for r in body]
    aligns = [_alignment(delim[i]) if i < len(delim) else "left" for i in range(ncols)]

    widths = []
    for i in range(ncols):
        col_cells = [header[i]] + [r[i] for r in body]
        widths.append(max(3, max(display_width(c) for c in col_cells)))

    def render(cells: list[str]) -> str:
        out = []
        for i in range(ncols):
            a = aligns[i]
            a = "left" if a == "left-explicit" else a
            out.append(_pad(cells[i], widths[i], a))
        return "| " + " | ".join(out) + " |"

    def render_delim() -> str:
        out = []
        for i in range(ncols):
            w = widths[i]
            a = aligns[i]
            if a == "center":
                out.append(":" + "-" * (w - 2) + ":")
            elif a == "right":
                out.append("-" * (w - 1) + ":")
            elif a == "left-explicit":
                out.append(":" + "-" * (w - 1))
            else:
                out.append("-" * w)
        return "| " + " | ".join(out) + " |"

    return [render(header), render_delim()] + [render(r) for r in body]


def format_document(text: str, strip_markup: bool = True) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        # A table starts where a row is followed by a delimiter row.
        if (
            _looks_like_table_row(lines[i])
            and i + 1 < n
            and _is_delim_row(lines[i + 1])
        ):
            block = [lines[i], lines[i + 1]]
            j = i + 2
            while j < n and _looks_like_table_row(lines[j]) and not _is_delim_row(lines[j]):
                block.append(lines[j])
                j += 1
            out.extend(format_table(block, strip_markup=strip_markup))
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def main(argv: list[str]) -> int:
    args = argv[1:]
    check = False
    strip_markup = True
    # Flags may appear in any order before the file list.
    rest = []
    for a in args:
        if a == "--check":
            check = True
        elif a == "--keep-markup":
            strip_markup = False
        else:
            rest.append(a)
    args = rest
    if not args:
        print(__doc__)
        return 2

    if args == ["-"]:
        sys.stdout.write(format_document(sys.stdin.read(), strip_markup=strip_markup))
        return 0

    changed = False
    for path in args:
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        formatted = format_document(src, strip_markup=strip_markup)
        if formatted != src:
            changed = True
            if check:
                print(f"would reformat: {path}")
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(formatted)
                print(f"formatted: {path}")
        elif not check:
            print(f"unchanged: {path}")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
