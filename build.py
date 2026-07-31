#!/usr/bin/env python3
"""
Site generator for rashedhindash.github.io

Standard library only. No pip install, no npm, no build tools.
If Python runs, this runs.

    python build.py           -> build the site into _site/
    python build.py --serve   -> build, open a local preview, rebuild on save
    python build.py --drafts  -> include posts marked `draft: true`

Everything you actually edit lives in  content/  and  static/ .
You should never need to open this file.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
THEME = ROOT / "theme"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

SITE: dict = {}
BUILD_ID = str(int(time.time()))


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", str(text).lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "item"


def url(path: str) -> str:
    """Make a link absolute against the site's base path."""
    if not path:
        return ""
    if re.match(r"^(https?:|mailto:|tel:|#|data:)", path):
        return path
    base = SITE.get("base", "").rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def esc(text) -> str:
    return html.escape(str(text or ""), quote=True)


def parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except ValueError:
            continue
    return None


def human_date(value) -> str:
    dt = parse_date(value)
    if not dt:
        return str(value or "")
    return dt.strftime("%d %b %Y").lstrip("0")


def short_date(value) -> str:
    dt = parse_date(value)
    if not dt:
        return str(value or "")
    return dt.strftime("%b %Y")


def local_size(url_path) -> str:
    """Human-readable size of a file in static/, read at build time.

    Means download buttons state the real size without anyone maintaining it
    by hand — replace the file and the number follows.
    """
    path = str(url_path or "")
    if not path.startswith("/static/"):
        return ""
    target = STATIC / path[len("/static/"):]
    if not target.exists():
        return ""
    size = target.stat().st_size
    if size >= 1048576:
        return "%.1f MB" % (size / 1048576)
    return "%d KB" % max(1, round(size / 1024))


def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [v for v in value if str(v).strip()]
    return [v.strip() for v in str(value).split(",") if v.strip()]


# --------------------------------------------------------------------------
# front matter  (the `---` block at the top of every content file)
# --------------------------------------------------------------------------

def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    return v


def _parse_meta_lines(lines) -> dict:
    meta: dict = {}
    i, n = 0, len(lines)
    while i < n:
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()

        # multi-line block:   key: |
        if val in ("|", ">"):
            block, i = [], i + 1
            while i < n and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                block.append(lines[i].strip() if val == ">" else re.sub(r"^ {1,4}|\t", "", lines[i]))
                i += 1
            meta[key] = ("\n" if val == "|" else " ").join(block).strip()
            continue

        # block list:   key:
        #                 - one
        if val == "":
            items, j = [], i + 1
            while j < n and re.match(r"^\s+-\s+", lines[j]):
                items.append(_scalar(re.sub(r"^\s+-\s+", "", lines[j])))
                j += 1
            if items:
                meta[key], i = items, j
                continue
            meta[key] = ""
            i += 1
            continue

        # inline list:  key: [a, b]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            meta[key] = [_scalar(p) for p in inner.split(",") if p.strip()] if inner else []
        else:
            meta[key] = _scalar(val)
        i += 1
    return meta


def parse_front_matter(text: str):
    text = text.replace("\r\n", "\n").lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    return _parse_meta_lines(lines[1:end]), "\n".join(lines[end + 1:])


# --------------------------------------------------------------------------
# markdown  (a focused subset: everything you need, nothing you don't)
# --------------------------------------------------------------------------

BLOCK_TAGS = r"(?:div|section|figure|figcaption|iframe|video|audio|table|p|ul|ol|li|img|blockquote|details|summary|h[1-6]|span|a|br|hr|picture|source)"


def _emphasis(t: str) -> str:
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", t)
    t = re.sub(r"~~(.+?)~~", r"<del>\1</del>", t)
    return t


def inline(text: str) -> str:
    """Inline markdown -> html. Escapes first, so raw html here is shown literally."""
    stash: list = []

    def keep(fragment: str) -> str:
        stash.append(fragment)
        return "\x00%d\x00" % (len(stash) - 1)

    text = html.escape(str(text), quote=False)

    text = re.sub(r"`([^`]+)`", lambda m: keep("<code>%s</code>" % m.group(1)), text)

    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
        lambda m: keep(
            '<img src="%s" alt="%s"%s loading="lazy" decoding="async">'
            % (esc(url(m.group(2))), esc(m.group(1)),
               ' title="%s"' % esc(m.group(3)) if m.group(3) else "")
        ),
        text,
    )

    def _link(m):
        label, href = m.group(1), m.group(2)
        external = href.startswith("http")
        attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
        return keep('<a href="%s"%s>%s</a>' % (esc(url(href)), attrs, _emphasis(label)))

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, text)

    text = re.sub(
        r"(?<![\"=\w])(https?://[^\s<)\]]+)",
        lambda m: keep('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                       % (esc(m.group(1)), m.group(1))),
        text,
    )

    text = _emphasis(text)

    for _ in range(3):  # placeholders can nest (e.g. an image inside a link)
        if "\x00" not in text:
            break
        for i, fragment in enumerate(stash):
            text = text.replace("\x00%d\x00" % i, fragment)
    return text


def _is_block_start(line: str) -> bool:
    s = line.strip()
    return bool(
        not s
        or s.startswith(("```", "> ", "::", "|"))
        or re.match(r"^#{1,6}\s", s)
        or re.match(r"^([-*+]|\d+\.)\s+", s)
        or re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", s)
        or re.match(r"^<%s\b" % BLOCK_TAGS, s)
    )


def _build_list(items, idx, indent):
    tag = "ol" if items[idx][1] else "ul"
    parts = ["<%s>" % tag]
    while idx < len(items) and items[idx][0] >= indent:
        if items[idx][0] > indent:
            if len(parts) > 1 and parts[-1].endswith("</li>"):
                sub, idx = _build_list(items, idx, items[idx][0])
                parts[-1] = parts[-1][: -len("</li>")] + sub + "</li>"
            else:
                sub, idx = _build_list(items, idx, items[idx][0])
                parts.append("<li>%s</li>" % sub)
            continue
        body = " ".join(items[idx][2]).strip()
        parts.append("<li>%s</li>" % inline(body))
        idx += 1
    parts.append("</%s>" % tag)
    return "".join(parts), idx


def _render_list(buf):
    items = []
    for line in buf:
        m = re.match(r"^(\s*)([-*+]|\d+\.)\s+(.*)$", line)
        if m:
            depth = len(m.group(1).replace("\t", "    "))
            ordered = m.group(2) not in ("-", "*", "+")
            items.append([depth, ordered, [m.group(3)]])
        elif items and line.strip():
            items[-1][2].append(line.strip())
    if not items:
        return ""
    out, _ = _build_list(items, 0, items[0][0])
    return out


def render_markdown(text: str) -> str:
    lines = str(text).replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)

    while i < n:
        line, s = lines[i], lines[i].strip()

        if not s:
            i += 1
            continue

        if s.startswith("```"):
            lang, i, buf = s[3:].strip(), i + 1, []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="lang-%s"' % slugify(lang) if lang else ""
            out.append("<pre><code%s>%s</code></pre>"
                       % (cls, html.escape("\n".join(buf), quote=False)))
            continue

        if s.startswith("::"):
            out.append(shortcode(s))
            i += 1
            continue

        if re.match(r"^<%s\b" % BLOCK_TAGS, s):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue

        if re.match(r"^(\*\s*){3,}$|^(-\s*){3,}$|^(_\s*){3,}$", s):
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level, txt = len(m.group(1)), m.group(2).strip()
            out.append('<h%d id="%s">%s</h%d>' % (level, slugify(txt), inline(txt), level))
            i += 1
            continue

        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>%s</blockquote>" % render_markdown("\n".join(buf)))
            continue

        if s.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in s.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join("<th>%s</th>" % inline(c) for c in head)
            tbody = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r) for r in rows
            )
            out.append('<div class="table-wrap"><table><thead><tr>%s</tr></thead>'
                       "<tbody>%s</tbody></table></div>" % (thead, tbody))
            continue

        if re.match(r"^([-*+]|\d+\.)\s+", s):
            buf = []
            while i < n:
                cur = lines[i]
                if cur.strip():
                    if re.match(r"^\s*([-*+]|\d+\.)\s+", cur) or cur.startswith(("  ", "\t")):
                        buf.append(cur)
                        i += 1
                        continue
                    break
                nxt = i + 1
                if nxt < n and (re.match(r"^\s*([-*+]|\d+\.)\s+", lines[nxt])
                                or lines[nxt].startswith(("  ", "\t"))):
                    i = nxt
                    continue
                break
            out.append(_render_list(buf))
            continue

        buf = []
        while i < n and lines[i].strip() and not (buf and _is_block_start(lines[i])):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return "\n".join(p for p in out if p)


# --------------------------------------------------------------------------
# video embeds  (Google Drive first, YouTube + Vimeo + raw files too)
# --------------------------------------------------------------------------

RE_YT = re.compile(r"(?:youtube\.com/(?:watch\?v=|embed/|shorts/|live/)|youtu\.be/|^youtube:|^yt:)([A-Za-z0-9_-]{6,})")
RE_DRIVE = re.compile(r"(?:drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=)|^drive:|^gdrive:)([A-Za-z0-9_-]{10,})")
RE_VIMEO = re.compile(r"(?:vimeo\.com/(?:video/)?|^vimeo:)(\d+)")


def video_source(spec: str):
    """Return (iframe_src, poster_url, kind) for any video link you paste in."""
    spec = (spec or "").strip()
    if not spec:
        return None

    m = RE_DRIVE.search(spec)
    if m:
        fid = m.group(1)
        return ("https://drive.google.com/file/d/%s/preview" % fid,
                "https://drive.google.com/thumbnail?id=%s&sz=w1600" % fid,
                "drive")

    m = RE_YT.search(spec)
    if m:
        vid = m.group(1)
        return ("https://www.youtube-nocookie.com/embed/%s?autoplay=1&rel=0" % vid,
                "https://i.ytimg.com/vi/%s/maxresdefault.jpg" % vid,
                "youtube")

    m = RE_VIMEO.search(spec)
    if m:
        return ("https://player.vimeo.com/video/%s?autoplay=1" % m.group(1), "", "vimeo")

    if re.search(r"\.(mp4|webm|mov|m4v)(\?.*)?$", spec, re.I):
        return (url(spec), "", "file")

    return None


def video_embed(spec: str, caption: str = "", poster: str = "") -> str:
    src = video_source(spec)
    if not src:
        return ""
    embed_src, auto_poster, kind = src
    poster = url(poster) if poster else auto_poster
    cap = '<figcaption>%s</figcaption>' % inline(caption) if caption else ""

    if kind == "file":
        media = ('<video controls preload="metadata"%s playsinline>'
                 '<source src="%s"></video>'
                 % (' poster="%s"' % esc(poster) if poster else "", esc(embed_src)))
        return '<figure class="embed embed--file">%s%s</figure>' % (media, cap)

    # YouTube's maxres thumbnail doesn't exist for every video, so fall back to
    # the one that always does. Anywhere else, a missing poster just disappears
    # and leaves the play button on a clean panel.
    if kind == "youtube":
        fallback = (' onerror="this.onerror=null;'
                    "this.src=this.src.replace('maxresdefault','hqdefault')\"")
    else:
        fallback = ' onerror="this.remove()"'

    poster_img = ('<img src="%s" alt="" loading="lazy" decoding="async"%s>'
                  % (esc(poster), fallback)) if poster else ""

    return (
        '<figure class="embed embed--%s">'
        '<div class="embed-frame">'
        '<button class="embed-play" type="button" data-embed="%s" aria-label="Play video">'
        '%s<span class="embed-play-btn" aria-hidden="true"><svg viewBox="0 0 24 24" '
        'width="26" height="26"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg></span>'
        "</button></div>%s</figure>"
        % (kind, esc(embed_src), poster_img, cap)
    )


def shortcode(line: str) -> str:
    body = line.strip()[2:].strip()
    name, _, rest = body.partition(" ")
    rest = rest.strip()

    if name == "video":
        spec, _, caption = rest.partition("|")
        return video_embed(spec.strip(), caption.strip())

    if name == "note":
        return '<aside class="note">%s</aside>' % inline(rest)

    if name == "image":
        parts = rest.split("|")
        src = parts[0].strip()
        caption = parts[1].strip() if len(parts) > 1 else ""
        cap = "<figcaption>%s</figcaption>" % inline(caption) if caption else ""
        return ('<figure class="figure"><img src="%s" alt="%s" loading="lazy" '
                'decoding="async">%s</figure>' % (esc(url(src)), esc(caption), cap))

    if name == "grid":
        srcs = [s.strip() for s in rest.split("|") if s.strip()]
        cells = "".join('<img src="%s" alt="" loading="lazy" decoding="async">'
                        % esc(url(s)) for s in srcs)
        return '<div class="figure-grid">%s</div>' % cells

    return ""


# --------------------------------------------------------------------------
# content loading
# --------------------------------------------------------------------------

COLLECTIONS = {
    "work": {
        "path": "/work/",
        "title": "Work",
        "blurb": "Animation, direction and design. Selected projects and breakdowns.",
        "layout": "grid",
    },
    "research": {
        "path": "/research/",
        "title": "Research",
        "blurb": "Non-traditional research outputs, creative works, exhibitions and writing "
                 "with a research contribution.",
        "layout": "list",
    },
    "writing": {
        "path": "/writing/",
        "title": "Writing",
        "blurb": "Notes on craft, process, pipeline and the occasional rant.",
        "layout": "list",
    },
    "tutorials": {
        "path": "/tutorials/",
        "title": "Tutorials",
        "blurb": "Video walkthroughs and step-by-step guides.",
        "layout": "cards",
    },
    "tools": {
        "path": "/tools/",
        "title": "Tools",
        "blurb": "Software I build and maintain, with documentation.",
        "layout": "cards",
    },
}


class Entry:
    def __init__(self, collection, path, meta, body):
        self.collection = collection
        self.source = path
        self.meta = meta
        self.body = body
        self.slug = str(meta.get("slug") or path.stem)
        self.title = str(meta.get("title") or path.stem.replace("-", " ").title())
        self.summary = str(meta.get("summary") or meta.get("description") or "")
        self.date = parse_date(meta.get("date"))
        self.tags = as_list(meta.get("tags"))
        self.cover = meta.get("cover") or ""
        self.draft = bool(meta.get("draft"))
        self.featured = bool(meta.get("featured"))
        if collection == "docs":
            tool = slugify(meta.get("tool") or "misc")
            self.url = "/tools/%s/%s/" % (tool, self.slug)
        elif collection == "rig-categories":
            self.url = "/rigs/%s/" % self.slug
        elif collection == "rigs":
            # Rigs don't get their own page — they live on their category page.
            self.url = "/rigs/%s/#%s" % (
                slugify(meta.get("category") or "misc"), self.slug)
        elif collection == "pages":
            self.url = "/%s/" % self.slug
        else:
            self.url = "%s%s/" % (COLLECTIONS[collection]["path"], self.slug)

    @property
    def html(self):
        return render_markdown(self.body)

    def get(self, key, default=""):
        return self.meta.get(key, default)


def load_collection(name: str, folder: str, include_drafts: bool):
    directory = CONTENT / folder
    entries = []
    if not directory.exists():
        return entries
    for path in sorted(directory.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        entry = Entry(name, path, meta, body)
        if entry.draft and not include_drafts:
            continue
        entries.append(entry)
    entries.sort(
        key=lambda e: (
            e.meta.get("order") is None,
            int(e.meta.get("order") or 0),
            -(e.date.timestamp() if e.date else 0),
            e.title.lower(),
        )
    )
    return entries


# --------------------------------------------------------------------------
# page furniture
# --------------------------------------------------------------------------

def nav_html(current: str) -> str:
    items = []
    for item in SITE.get("nav", []):
        href = item.get("href", "/")
        active = current.startswith(href) and href != "/" or current == href
        items.append('<a class="nav-link%s" href="%s"%s>%s</a>'
                     % (" is-active" if active else "", esc(url(href)),
                        ' aria-current="page"' if active else "", esc(item.get("label", ""))))
    return "".join(items)


def kicker(text: str) -> str:
    return '<span class="kicker">%s</span>' % esc(text) if text else ""


def tag_row(tags) -> str:
    if not tags:
        return ""
    return '<ul class="tags">%s</ul>' % "".join(
        "<li>%s</li>" % esc(t) for t in tags
    )


def meta_row(pairs) -> str:
    cells = [
        '<div class="meta-cell"><dt>%s</dt><dd>%s</dd></div>' % (esc(k), inline(str(v)))
        for k, v in pairs if v
    ]
    return '<dl class="meta-grid">%s</dl>' % "".join(cells) if cells else ""


def card_media(entry: Entry, ratio: str = "16 / 9") -> str:
    preview = entry.get("preview")

    image = str(entry.cover or "")
    if image:
        image = url(image)
    else:
        src = video_source(str(entry.get("video") or ""))
        image = src[1] if src else ""

    # The monogram sits underneath the thumbnail. If the thumbnail 404s — an
    # unshared Drive file is the usual reason — the image removes itself and
    # the monogram shows through, rather than a broken-image icon.
    inner = '<span class="card-mark" aria-hidden="true">%s</span>' % esc(
        entry.title[:2].upper())
    if image:
        inner += ('<img src="%s" alt="" loading="lazy" decoding="async" '
                  'onerror="this.remove()">' % esc(image))
    if preview:
        inner += ('<video class="card-preview" muted loop playsinline preload="none">'
                  '<source src="%s"></video>' % esc(url(str(preview))))
    return ('<div class="card-media" style="--ratio:%s">%s</div>' % (ratio, inner))


def work_card(entry: Entry, index: int = 0) -> str:
    year = entry.date.strftime("%Y") if entry.date else str(entry.get("year") or "")
    role = str(entry.get("role") or "")
    return (
        '<a class="card card--work" href="%s" data-reveal style="--i:%d">'
        "%s"
        '<div class="card-body">'
        '<h3 class="card-title">%s</h3>'
        '<p class="card-meta">%s</p>'
        "</div></a>"
        % (esc(url(entry.url)), index, card_media(entry), esc(entry.title),
           esc(" · ".join([p for p in (role, year) if p])))
    )


def list_row(entry: Entry, index: int = 0, label_field: str = "") -> str:
    label = str(entry.get(label_field) or "") if label_field else ""
    when = short_date(entry.date) if entry.date else str(entry.get("year") or "")
    return (
        '<a class="row" href="%s" data-reveal style="--i:%d">'
        '<span class="row-when">%s</span>'
        '<span class="row-main"><span class="row-title">%s</span>%s</span>'
        '<span class="row-label">%s</span>'
        '<span class="row-arrow" aria-hidden="true">&#8599;</span>'
        "</a>"
        % (esc(url(entry.url)), index, esc(when), esc(entry.title),
           '<span class="row-sum">%s</span>' % esc(entry.summary) if entry.summary else "",
           esc(label))
    )


def tutorial_card(entry: Entry, index: int = 0) -> str:
    bits = [str(entry.get("software") or ""), str(entry.get("level") or ""),
            str(entry.get("duration") or "")]
    return (
        '<a class="card card--tut" href="%s" data-reveal style="--i:%d">'
        "%s"
        '<div class="card-body">'
        '<h3 class="card-title">%s</h3>'
        '<p class="card-meta">%s</p>'
        "</div></a>"
        % (esc(url(entry.url)), index, card_media(entry), esc(entry.title),
           esc(" · ".join([b for b in bits if b])))
    )


def tool_card(entry: Entry, index: int = 0) -> str:
    status = str(entry.get("status") or "")
    version = str(entry.get("version") or "")
    return (
        '<a class="card card--tool" href="%s" data-reveal style="--i:%d">'
        '<div class="tool-head"><h3 class="card-title">%s</h3>%s</div>'
        '<p class="tool-sum">%s</p>'
        '<p class="card-meta">%s</p>'
        "</a>"
        % (esc(url(entry.url)), index, esc(entry.title),
           '<span class="pill">%s</span>' % esc(status) if status else "",
           esc(entry.summary),
           esc(" · ".join([b for b in (str(entry.get("language") or ""), version) if b])))
    )


# --------------------------------------------------------------------------
# templates
# --------------------------------------------------------------------------

def shell(*, title, body, description="", path="/", og_image="", show_footer=True) -> str:
    template = (THEME / "base.html").read_text(encoding="utf-8")
    site_name = SITE.get("name", "")
    full_title = title if title == site_name else "%s — %s" % (title, site_name)
    site_url = SITE.get("url", "").rstrip("/")
    og = og_image or SITE.get("og_image", "")
    if og and not og.startswith("http"):
        og = site_url + url(og)

    replacements = {
        "{{title}}": esc(full_title),
        "{{description}}": esc(description or SITE.get("description", "")),
        "{{canonical}}": esc(site_url + url(path)),
        "{{og_image}}": esc(og),
        "{{site_name}}": esc(site_name),
        "{{base}}": SITE.get("base", "").rstrip("/"),
        "{{ver}}": BUILD_ID,
        "{{nav}}": nav_html(path),
        "{{body}}": body,
        "{{year}}": str(datetime.now().year),
        "{{footer}}": footer_html() if show_footer else "",
        "{{accent}}": SITE.get("accent", "#ff5c35"),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def footer_html() -> str:
    links = "".join(
        '<a href="%s"%s>%s</a>'
        % (esc(url(l.get("href", "#"))),
           ' target="_blank" rel="noopener noreferrer"' if str(l.get("href", "")).startswith("http") else "",
           esc(l.get("label", "")))
        for l in SITE.get("links", [])
    )
    email = SITE.get("email", "")
    return (
        '<div class="foot-in">'
        '<div class="foot-cta"><p class="foot-lead">%s</p>%s</div>'
        '<div class="foot-links">%s</div>'
        "</div>"
        % (esc(SITE.get("footer_line", "Open to collaboration, teaching and commissions.")),
           '<a class="foot-mail" href="mailto:%s">%s</a>' % (esc(email), esc(email)) if email else "",
           links)
    )


def page_header(title, blurb="", eyebrow="") -> str:
    return (
        '<header class="page-head">'
        "%s"
        '<h1 class="page-title" data-split>%s</h1>'
        "%s"
        "</header>"
        % (kicker(eyebrow), esc(title),
           '<p class="page-blurb">%s</p>' % inline(blurb) if blurb else "")
    )


# --------------------------------------------------------------------------
# page builders
# --------------------------------------------------------------------------

def build_home(data) -> str:
    name = SITE.get("name", "")
    words = "".join(
        '<span class="w"><span class="w-in" style="--i:%d">%s</span></span> ' % (i, esc(w))
        for i, w in enumerate(name.split())
    )

    hero = (
        '<section class="hero">'
        '<div class="hero-in">'
        '<p class="hero-kicker" style="--i:0">%s</p>'
        '<h1 class="hero-title">%s</h1>'
        '<p class="hero-lead" style="--i:4">%s</p>'
        '<div class="hero-actions" style="--i:5">'
        '<a class="btn btn--solid" href="%s">See the work</a>'
        '<a class="btn" href="%s">About me</a>'
        "</div></div>"
        '<div class="hero-glow" aria-hidden="true"></div>'
        "</section>"
        % (esc(SITE.get("role", "")), words, inline(SITE.get("tagline", "")),
           esc(url("/work/")), esc(url("/about/")))
    )

    sections = []

    featured = [e for e in data["work"] if e.featured] or data["work"][:4]
    if featured:
        sections.append(
            '<section class="band">'
            '<div class="band-head"><h2 class="band-title" data-reveal>Selected work</h2>'
            '<a class="band-more" href="%s" data-reveal>All work &#8599;</a></div>'
            '<div class="grid grid--work">%s</div></section>'
            % (esc(url("/work/")),
               "".join(work_card(e, i) for i, e in enumerate(featured[:4])))
        )

    if data["tutorials"]:
        sections.append(
            '<section class="band">'
            '<div class="band-head"><h2 class="band-title" data-reveal>Tutorials</h2>'
            '<a class="band-more" href="%s" data-reveal>All tutorials &#8599;</a></div>'
            '<div class="grid grid--tut">%s</div></section>'
            % (esc(url("/tutorials/")),
               "".join(tutorial_card(e, i) for i, e in enumerate(data["tutorials"][:3])))
        )

    mixed = []
    for entry in data["research"][:3]:
        mixed.append((entry, str(entry.get("type") or "Research")))
    for entry in data["writing"][:3]:
        mixed.append((entry, "Writing"))
    mixed.sort(key=lambda pair: -(pair[0].date.timestamp() if pair[0].date else 0))
    if mixed:
        sections.append(
            '<section class="band">'
            '<div class="band-head"><h2 class="band-title" data-reveal>Research &amp; writing</h2>'
            '<a class="band-more" href="%s" data-reveal>All research &#8599;</a></div>'
            '<div class="rows">%s</div></section>'
            % (esc(url("/research/")),
               "".join(
                   '<a class="row" href="%s" data-reveal style="--i:%d">'
                   '<span class="row-when">%s</span>'
                   '<span class="row-main"><span class="row-title">%s</span></span>'
                   '<span class="row-label">%s</span>'
                   '<span class="row-arrow" aria-hidden="true">&#8599;</span></a>'
                   % (esc(url(e.url)), i, esc(short_date(e.date)), esc(e.title), esc(label))
                   for i, (e, label) in enumerate(mixed[:5])
               ))
        )

    if data["tools"]:
        sections.append(
            '<section class="band">'
            '<div class="band-head"><h2 class="band-title" data-reveal>Tools</h2>'
            '<a class="band-more" href="%s" data-reveal>All tools &#8599;</a></div>'
            '<div class="grid grid--tools">%s</div></section>'
            % (esc(url("/tools/")),
               "".join(tool_card(e, i) for i, e in enumerate(data["tools"][:3])))
        )

    return shell(
        title=SITE.get("name", ""),
        description=SITE.get("description", ""),
        path="/",
        body='<main id="main">%s<div class="wrap">%s</div></main>' % (hero, "".join(sections)),
    )


def build_collection_index(name, entries) -> str:
    conf = COLLECTIONS[name]
    layout = conf["layout"]

    if not entries:
        inner = ('<p class="empty">Nothing here yet. Add a file to '
                 '<code>content/%s/</code> and it appears on this page.</p>' % name)
    elif layout == "grid":
        inner = '<div class="grid grid--work">%s</div>' % "".join(
            work_card(e, i) for i, e in enumerate(entries))
    elif layout == "cards" and name == "tutorials":
        inner = '<div class="grid grid--tut">%s</div>' % "".join(
            tutorial_card(e, i) for i, e in enumerate(entries))
    elif layout == "cards":
        inner = '<div class="grid grid--tools">%s</div>' % "".join(
            tool_card(e, i) for i, e in enumerate(entries))
    else:
        field = "type" if name == "research" else ""
        inner = '<div class="rows">%s</div>' % "".join(
            list_row(e, i, field) for i, e in enumerate(entries))

    body = ('<main id="main"><div class="wrap">%s%s</div></main>'
            % (page_header(conf["title"], conf["blurb"], name.upper()), inner))
    return shell(title=conf["title"], description=conf["blurb"],
                 path=conf["path"], body=body)


def build_entry(name, entry, siblings, docs_by_tool=None) -> str:
    conf = COLLECTIONS.get(name, {})
    eyebrow = conf.get("title", "")

    bits = []
    if name == "work":
        bits = [("Role", entry.get("role")), ("Client", entry.get("client")),
                ("Year", entry.date.strftime("%Y") if entry.date else entry.get("year")),
                ("Software", ", ".join(as_list(entry.get("software"))))]
    elif name == "research":
        eyebrow = str(entry.get("type") or "Research output")
        bits = [("Output type", entry.get("type")), ("Venue", entry.get("venue")),
                ("Date", human_date(entry.date) if entry.date else entry.get("year")),
                ("Contributors", ", ".join(as_list(entry.get("contributors")))),
                ("DOI / Link", ('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                                % (esc(entry.get("link")), esc(entry.get("link"))))
                 if entry.get("link") else "")]
    elif name == "tutorials":
        bits = [("Software", entry.get("software")), ("Level", entry.get("level")),
                ("Length", entry.get("duration")),
                ("Files", ('<a href="%s" target="_blank" rel="noopener noreferrer">Download</a>'
                           % esc(entry.get("files"))) if entry.get("files") else "")]
    elif name == "tools":
        bits = [("Status", entry.get("status")), ("Version", entry.get("version")),
                ("Built with", entry.get("language")),
                ("Source", ('<a href="%s" target="_blank" rel="noopener noreferrer">Repository</a>'
                            % esc(entry.get("repo"))) if entry.get("repo") else ""),
                ("Download", ('<a href="%s">Get it</a>' % esc(url(str(entry.get("download")))))
                 if entry.get("download") else "")]
    elif name == "writing":
        bits = [("Published", human_date(entry.date) if entry.date else ""),
                ("Reading time", entry.get("reading_time"))]

    hero_video = video_embed(str(entry.get("video") or ""),
                             poster=str(entry.get("cover") or ""))

    cover_block = ""
    if not hero_video and entry.cover:
        cover_block = ('<figure class="lede-figure" data-reveal>'
                       '<img src="%s" alt="" decoding="async"></figure>'
                       % esc(url(str(entry.cover))))

    research_block = ""
    if name == "research":
        fields = [("Research statement", entry.get("research_statement")),
                  ("Research background", entry.get("background")),
                  ("Contribution", entry.get("contribution")),
                  ("Significance", entry.get("significance")),
                  ("Scope", entry.get("scope"))]
        blocks = "".join(
            '<div class="ntro-item"><h3>%s</h3>%s</div>' % (esc(k), render_markdown(str(v)))
            for k, v in fields if v
        )
        if blocks:
            research_block = ('<section class="ntro" data-reveal>'
                              '<h2 class="ntro-head">Research statement</h2>%s</section>' % blocks)

    docs_block = ""
    if name == "tools" and docs_by_tool:
        docs = docs_by_tool.get(entry.slug, [])
        if docs:
            docs_block = (
                '<section class="doclist" data-reveal><h2 class="doclist-head">Documentation</h2>'
                '<div class="rows rows--tight">%s</div></section>'
                % "".join(
                    '<a class="row" href="%s" style="--i:%d">'
                    '<span class="row-main"><span class="row-title">%s</span>%s</span>'
                    '<span class="row-arrow" aria-hidden="true">&#8594;</span></a>'
                    % (esc(url(d.url)), i, esc(d.title),
                       '<span class="row-sum">%s</span>' % esc(d.summary) if d.summary else "")
                    for i, d in enumerate(docs))
            )

    index = next((i for i, e in enumerate(siblings) if e.slug == entry.slug), -1)
    prev_entry = siblings[index - 1] if index > 0 else None
    next_entry = siblings[index + 1] if 0 <= index < len(siblings) - 1 else None
    pager = ""
    if prev_entry or next_entry:
        pager = (
            '<nav class="pager">%s%s</nav>'
            % ('<a class="pager-link pager-prev" href="%s"><span>Previous</span><b>%s</b></a>'
               % (esc(url(prev_entry.url)), esc(prev_entry.title)) if prev_entry else "<span></span>",
               '<a class="pager-link pager-next" href="%s"><span>Next</span><b>%s</b></a>'
               % (esc(url(next_entry.url)), esc(next_entry.title)) if next_entry else "")
        )

    body = (
        '<main id="main"><article class="wrap article">'
        '<header class="art-head">'
        '<a class="back" href="%s">&#8592; %s</a>'
        "%s"
        '<h1 class="art-title" data-split>%s</h1>'
        "%s%s"
        "</header>"
        "%s%s"
        '<div class="prose" data-reveal>%s</div>'
        "%s%s%s"
        "</article></main>"
        % (esc(url(conf.get("path", "/"))), esc(conf.get("title", "Back")),
           kicker(eyebrow), esc(entry.title),
           '<p class="art-sum">%s</p>' % inline(entry.summary) if entry.summary else "",
           meta_row(bits),
           hero_video, cover_block,
           entry.html,
           research_block, docs_block, tag_row(entry.tags) + pager)
    )

    og = str(entry.cover or "")
    if not og:
        src = video_source(str(entry.get("video") or ""))
        og = src[1] if src else ""

    return shell(title=entry.title, description=entry.summary or SITE.get("description", ""),
                 path=entry.url, body=body, og_image=og)


def rig_card(entry: Entry, index: int = 0) -> str:
    image = str(entry.get("image") or entry.cover or "")
    download = str(entry.get("download") or "")

    kind = os.path.splitext(download)[1].lstrip(".").lower() if download else ""
    size = local_size(download)
    badge = " · ".join([b for b in (kind, size) if b])

    if download:
        # Same-origin, so `download` makes the browser save the file instead of
        # navigating anywhere. No detour through a file host.
        action = ('<a class="dl" href="%s" download>'
                  '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true">'
                  '<path d="M12 3v11m0 0 4.2-4.2M12 14l-4.2-4.2M4.5 18.5h15" '
                  'fill="none" stroke="currentColor" stroke-width="1.9" '
                  'stroke-linecap="round" stroke-linejoin="round"/></svg>'
                  '<span>Download</span>%s</a>'
                  % (esc(url(download)),
                     '<span class="dl-meta">%s</span>' % esc(badge) if badge else ""))
    else:
        action = '<span class="dl dl--soon">Coming soon</span>'

    media = ('<img src="%s" alt="%s rig" loading="lazy" decoding="async" '
             'onerror="this.remove()">' % (esc(url(image)), esc(entry.title))
             ) if image else ('<span class="card-mark" aria-hidden="true">%s</span>'
                              % esc(entry.title[:2].upper()))

    software = str(entry.get("software") or "")

    return (
        '<article class="rig" id="%s" data-reveal style="--i:%d">'
        '<div class="rig-shot">%s</div>'
        '<div class="rig-body">'
        '<div class="rig-head"><h3 class="rig-title">%s</h3>%s</div>'
        "%s"
        '<div class="rig-foot">%s</div>'
        "</div></article>"
        % (esc(entry.slug), index, media, esc(entry.title),
           '<span class="pill">%s</span>' % esc(software) if software else "",
           '<p class="rig-sum">%s</p>' % inline(entry.summary) if entry.summary else "",
           action)
    )


def build_rigs_index(categories, rigs_by_cat) -> str:
    cards = []
    for i, cat in enumerate(categories):
        count = len(rigs_by_cat.get(cat.slug, []))
        banner = str(cat.get("banner") or "")
        media = ('<div class="cat-media"><img src="%s" alt="" loading="lazy" '
                 'decoding="async" onerror="this.remove()"></div>'
                 % esc(url(banner))) if banner else '<div class="cat-media"></div>'
        cards.append(
            '<a class="cat-card" href="%s" data-reveal style="--i:%d">%s'
            '<div class="cat-body"><h2 class="cat-title">%s</h2>%s'
            '<p class="cat-count">%s</p></div></a>'
            % (esc(url(cat.url)), i, media, esc(cat.title),
               '<p class="cat-sum">%s</p>' % esc(cat.summary) if cat.summary else "",
               esc("%d rig%s" % (count, "" if count == 1 else "s")))
        )

    inner = ('<div class="cat-grid">%s</div>' % "".join(cards)) if cards else (
        '<p class="empty">No categories yet. Add a file to '
        "<code>content/rig-categories/</code>.</p>")

    body = ('<main id="main"><div class="wrap">%s%s</div></main>'
            % (page_header("Rigs", "Free character and prop rigs for 3ds Max, "
                                   "grouped by what they're built to teach.", "RIGS"),
               inner))
    return shell(title="Rigs", description="Free 3ds Max rigs for animation practice.",
                 path="/rigs/", body=body)


def build_rig_category(category: Entry, rigs, siblings) -> str:
    banner = str(category.get("banner") or "")
    banner_html = ('<figure class="rig-banner"><img src="%s" alt="%s" '
                   'decoding="async" fetchpriority="high" onerror="this.remove()">'
                   "</figure>" % (esc(url(banner)), esc(category.title))) if banner else ""

    intro = ('<div class="prose rig-intro" data-reveal>%s</div>'
             % category.html) if category.body.strip() else ""

    if rigs:
        grid = '<div class="rig-grid">%s</div>' % "".join(
            rig_card(r, i) for i, r in enumerate(rigs))
    else:
        grid = ('<p class="empty">Nothing in this category yet. Add a file to '
                "<code>content/rigs/</code> with <code>category: %s</code>.</p>"
                % esc(category.slug))

    others = "".join(
        '<a class="chip%s" href="%s">%s</a>'
        % (" is-active" if s.slug == category.slug else "", esc(url(s.url)), esc(s.title))
        for s in siblings)
    switcher = '<nav class="chips" aria-label="Rig categories">%s</nav>' % others if len(siblings) > 1 else ""

    body = (
        '<main id="main"><div class="wrap">'
        '<header class="page-head page-head--rig">'
        '<a class="back" href="%s">&#8592; Rigs</a>'
        '<h1 class="page-title" data-split>%s</h1>%s</header>'
        "%s%s%s%s"
        "</div></main>"
        % (esc(url("/rigs/")), esc(category.title),
           '<p class="page-blurb">%s</p>' % inline(category.summary) if category.summary else "",
           banner_html, switcher, intro, grid)
    )
    return shell(title=category.title, description=category.summary,
                 path=category.url, body=body, og_image=banner)


def build_doc(entry, tool, siblings) -> str:
    toc_items = re.findall(r"^##\s+(.+)$", entry.body, re.M)
    toc = ""
    if len(toc_items) > 1:
        toc = ('<nav class="toc"><p class="toc-head">On this page</p><ul>%s</ul></nav>'
               % "".join('<li><a href="#%s">%s</a></li>' % (slugify(t), esc(t))
                         for t in toc_items))

    side = ""
    if siblings:
        side = ('<aside class="docnav"><p class="docnav-head">%s docs</p><ul>%s</ul></aside>'
                % (esc(tool.title if tool else "Documentation"),
                   "".join('<li><a href="%s"%s>%s</a></li>'
                           % (esc(url(s.url)),
                              ' class="is-active"' if s.slug == entry.slug else "",
                              esc(s.title))
                           for s in siblings)))

    body = (
        '<main id="main"><div class="wrap doclayout">'
        "%s"
        '<article class="docmain">'
        '<header class="art-head art-head--doc">'
        '<a class="back" href="%s">&#8592; %s</a>'
        '<h1 class="art-title art-title--doc" data-split>%s</h1>%s</header>'
        "%s"
        '<div class="prose" data-reveal>%s</div>'
        "</article></div></main>"
        % (side,
           esc(url(tool.url if tool else "/tools/")),
           esc(tool.title if tool else "Tools"),
           esc(entry.title),
           '<p class="art-sum">%s</p>' % inline(entry.summary) if entry.summary else "",
           toc, entry.html)
    )
    return shell(title=entry.title, description=entry.summary, path=entry.url, body=body)


def build_simple_page(entry) -> str:
    body = (
        '<main id="main"><div class="wrap article article--page">'
        '<header class="art-head">%s<h1 class="art-title" data-split>%s</h1>%s</header>'
        '<div class="prose" data-reveal>%s</div>'
        "</div></main>"
        % (kicker(str(entry.get("eyebrow") or "")), esc(entry.title),
           '<p class="art-sum">%s</p>' % inline(entry.summary) if entry.summary else "",
           entry.html)
    )
    return shell(title=entry.title, description=entry.summary, path=entry.url, body=body)


def build_404() -> str:
    body = ('<main id="main"><div class="wrap notfound">'
            '<p class="kicker">404</p>'
            '<h1 class="page-title">This page moved, or never existed.</h1>'
            '<p class="page-blurb">Try the <a href="%s">work</a>, the '
            '<a href="%s">writing</a>, or go <a href="%s">home</a>.</p>'
            "</div></main>"
            % (esc(url("/work/")), esc(url("/writing/")), esc(url("/"))))
    return shell(title="Not found", path="/404.html", body=body)


# --------------------------------------------------------------------------
# feeds
# --------------------------------------------------------------------------

def build_rss(entries) -> str:
    site_url = SITE.get("url", "").rstrip("/")
    items = []
    for entry in entries[:30]:
        pub = entry.date or datetime.now()
        items.append(
            "<item><title>%s</title><link>%s</link><guid isPermaLink=\"true\">%s</guid>"
            "<pubDate>%s</pubDate><description>%s</description></item>"
            % (xml_escape(entry.title), xml_escape(site_url + url(entry.url)),
               xml_escape(site_url + url(entry.url)),
               pub.strftime("%a, %d %b %Y %H:%M:%S +0000"),
               xml_escape(entry.summary or entry.title))
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        "<title>%s</title><link>%s</link><description>%s</description>"
        "<language>en</language><lastBuildDate>%s</lastBuildDate>%s"
        "</channel></rss>"
        % (xml_escape(SITE.get("name", "")), xml_escape(site_url),
           xml_escape(SITE.get("description", "")),
           datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000"),
           "".join(items))
    )


def build_sitemap(paths) -> str:
    site_url = SITE.get("url", "").rstrip("/")
    urls = "".join("<url><loc>%s</loc></url>" % xml_escape(site_url + url(p)) for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def write(path_str: str, content: str):
    target = OUT / path_str.strip("/")
    if path_str.endswith("/") or not target.suffix:
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build(include_drafts: bool = False) -> int:
    global SITE
    SITE = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    data = {name: load_collection(name, name, include_drafts) for name in COLLECTIONS}
    docs = load_collection("docs", "docs", include_drafts)
    pages = load_collection("pages", "pages", include_drafts)

    docs_by_tool: dict = {}
    for doc in docs:
        docs_by_tool.setdefault(slugify(doc.get("tool") or "misc"), []).append(doc)

    paths = ["/"]
    write("/", build_home(data))

    for name, entries in data.items():
        write(COLLECTIONS[name]["path"], build_collection_index(name, entries))
        paths.append(COLLECTIONS[name]["path"])
        for entry in entries:
            write(entry.url, build_entry(name, entry, entries, docs_by_tool))
            paths.append(entry.url)

    rig_categories = load_collection("rig-categories", "rig-categories", include_drafts)
    rigs = load_collection("rigs", "rigs", include_drafts)

    rigs_by_cat: dict = {}
    for rig in rigs:
        rigs_by_cat.setdefault(slugify(rig.get("category") or "misc"), []).append(rig)

    if rig_categories:
        write("/rigs/", build_rigs_index(rig_categories, rigs_by_cat))
        paths.append("/rigs/")
        for category in rig_categories:
            write(category.url,
                  build_rig_category(category, rigs_by_cat.get(category.slug, []),
                                     rig_categories))
            paths.append(category.url)

    tools_by_slug = {t.slug: t for t in data["tools"]}
    for tool_slug, tool_docs in docs_by_tool.items():
        for doc in tool_docs:
            write(doc.url, build_doc(doc, tools_by_slug.get(tool_slug), tool_docs))
            paths.append(doc.url)

    for page in pages:
        write(page.url, build_simple_page(page))
        paths.append(page.url)

    write("/404.html", build_404())

    feed_items = sorted(
        [e for e in data["writing"] + data["research"] + data["tutorials"] if e.date],
        key=lambda e: -e.date.timestamp(),
    )
    (OUT / "rss.xml").write_text(build_rss(feed_items), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(build_sitemap(paths), encoding="utf-8")
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE.get("url", "").rstrip("/"),
        encoding="utf-8",
    )
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    domain = str(SITE.get("custom_domain") or "").strip()
    if domain:
        (OUT / "CNAME").write_text(domain + "\n", encoding="utf-8")

    assets = OUT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for filename in ("style.css", "app.js", "favicon.svg"):
        source = THEME / filename
        if source.exists():
            text = source.read_text(encoding="utf-8")
            text = text.replace("{{accent}}", SITE.get("accent", "#ff5c35"))
            (assets / filename).write_text(text, encoding="utf-8")

    if STATIC.exists():
        shutil.copytree(STATIC, OUT / "static", dirs_exist_ok=True)

    return len(paths)


# --------------------------------------------------------------------------
# local preview
# --------------------------------------------------------------------------

def snapshot():
    stamps = []
    for folder in (CONTENT, THEME, STATIC):
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file():
                stamps.append((str(path), path.stat().st_mtime))
    return sorted(stamps)


def serve(port: int = 8000):
    import http.server
    import socketserver

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(OUT), **kwargs)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, *args):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("\n  Preview running at  http://localhost:%d" % port)
    print("  Editing anything in content/ or theme/ rebuilds automatically.")
    print("  Press Ctrl+C to stop.\n")

    last = snapshot()
    try:
        while True:
            time.sleep(0.6)
            current = snapshot()
            if current != last:
                last = current
                try:
                    count = build()
                    print("  rebuilt  %s  (%d pages)" % (time.strftime("%H:%M:%S"), count))
                except Exception as exc:  # keep the server alive on a bad edit
                    print("  build error: %s" % exc)
    except KeyboardInterrupt:
        print("\n  Preview stopped.")


def main():
    args = sys.argv[1:]
    drafts = "--drafts" in args
    started = time.time()
    count = build(include_drafts=drafts)
    print("Built %d pages into _site/ in %.2fs" % (count, time.time() - started))

    if "--serve" in args:
        port = 8000
        for arg in args:
            if arg.startswith("--port="):
                port = int(arg.split("=", 1)[1])
        if "--open" in args:
            threading.Timer(1.0, lambda: webbrowser.open("http://localhost:%d" % port)).start()
        serve(port)


if __name__ == "__main__":
    main()
