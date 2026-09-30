#!/usr/bin/env python3
"""Mirror the stored daily reports into this repo, and index them.

Runs in GitHub Actions every evening after the 18:00 IST build (and on demand).
It reads equity-service's public report index (`/api/v1/reports/`), fetches
every day this repo does not yet hold, writes `stocks/reports/YYYY-MM-DD.html`,
then rebuilds the site. Idempotent: a day already present is never re-fetched, so a
rebuilt report replaces its file only if `--refresh` is given.

**Two books, three levels** (2026-09-29). The site used to be one index over
one book. It is now a hub with a section per book, because the crypto book
arrived and interleaving two unrelated instruments in one date-ordered table
made both harder to read:

    /                     the hub — stocks and crypto
    /stocks/              equity: analyses, then daily reports by month
    /crypto/              crypto: analyses, then daily reports by month

Equity's daily reports moved to `stocks/reports/` on 2026-09-30, so the two
books finally match — crypto's had always been at `crypto/reports/`, and one
book sitting at the root while the other was nested was an accident of which
came first. Every URL this archive has published still resolves: see
:func:`write_redirects`.

Crypto has no public report API yet, so `crypto/reports/` is filled by hand
from `crypto-service`:

    heroku run --app cryptoo-service --no-tty -- python manage.py daily_report \
        | sed -n '/<!doctype html>/,$p' > crypto/reports/$(date +%F).html

and this script indexes whatever it finds there. When that service grows a
report API, `crypto_rows` is the one function that changes.
"""
from __future__ import annotations

import html
import json
import re
import ssl
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = "https://equity-service-fd1143ae8c7a.herokuapp.com/api/v1/reports/"
"""The service serves its stored reports publicly — the owner publishes them
here anyway, so the mirror needs no credential of any kind (2026-09-23)."""
ROOT = Path(__file__).resolve().parent
OVERRIDES = ROOT / "overrides"
"""Hand-finished pages, `YYYY-MM-DD.html`. A day here is published in place of
the dyno's copy — the dyno renders the scan, but analysis written by hand
(the 23 Sep IPO review, for one) lives only in the file, and a refresh run
silently threw it away once. Anything under here wins, always."""
STOCKS = ROOT / "stocks"
CRYPTO = ROOT / "crypto"
REPORTS = STOCKS / "reports"
"""Equity's daily pages. Moved under `stocks/` on 2026-09-30 so the two books
are symmetrical — crypto's had always been at `crypto/reports/`, and one book
sitting at the root while the other was nested was an accident of which came
first. Every old `/reports/<name>` is a meta-refresh onto the new path; those
URLs have been shared and an archive that breaks its own links to look tidier
has made itself worse."""
ANALYSIS = STOCKS / "analysis"
"""Standing analyses — the six-month retrospective and its successors. Not a
day's page: they are written once, listed separately on the index, and
re-skinned with the rest whenever the renderer's theme moves. ``_bridge.css``
beside them maps their own class names onto that theme."""

CRYPTO_ANALYSIS = CRYPTO / "analysis"
CRYPTO_REPORTS = CRYPTO / "reports"
"""Crypto's daily pages, written by `crypto-service`'s own `daily_report` and
dropped in by hand until that service serves them over HTTP."""

EXTRAS = ROOT / "extras"
"""Standalone pages, `YYYY-MM-DD_<slug>.html`, published under reports/ and
linked from the index row of their day."""


def _context() -> ssl.SSLContext | None:
    """certifi's roots where they are installed, the system's otherwise.

    GitHub Actions trusts the service's certificate out of the box; a macOS
    python.org build does not, because it ships no system root store and the
    owner runs this by hand when a report has to go up now. Falling back to
    ``None`` keeps the Actions path exactly as it was.
    """
    try:
        import certifi
    except ModuleNotFoundError:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def fetch(url: str) -> str:
    with urllib.request.urlopen(  # noqa: S310 — fixed https host
        url, timeout=120, context=_context()
    ) as response:
        return response.read().decode("utf-8")


def fetch_index() -> list[dict]:
    return json.loads(fetch(BASE))


def extras_for(day: str, *, base: str = "reports") -> str:
    links = []
    for page in sorted(EXTRAS.glob(f"{day}_*.html")):
        slug = page.stem[len(day) + 1 :].replace("_", " ")
        links.append(f'<a href="{base}/{page.name}">{html.escape(slug)}</a>')
    return (" · " + " · ".join(links)) if links else ""


def verdict(summary: str) -> str:
    first = (summary or "").strip().splitlines()
    return first[0] if first else "—"


STYLE = re.compile(r"<style>.*?</style>", re.S)
STYLE_FALLBACK = "<style>body{font:15px/1.5 system-ui,sans-serif;margin:2rem}</style>"

# This is deliberately appended after each renderer stylesheet.  Daily reports
# arrive from two services, while the long-form studies have their own bridge
# CSS; their semantic classes are stable, so the shared token layer lets the
# entire public book use the landing page's visual language without changing
# the evidence or calculations inside any report.
THEME_MARKER = "/* morning-book-shared-theme */"
SHARED_THEME = r"""
/* morning-book-shared-theme */
:root{color-scheme:light;--canvas:#fff;--card:#fff;--head:#f8fafc;--line:#e5e7eb;--line-strong:#cbd5e1;--ink:#0f172a;--ink-2:#334155;--muted:#64748b;--faint:#94a3b8;--blue:#2563eb;--blue-ink:#1d4ed8;--blue-50:#eff6ff;--blue-100:#dbeafe;--green:#059669;--green-50:#ecfdf5;--green-100:#d1fae5;--green-line:#a7f3d0;--red:#dc2626;--red-50:#fef2f2;--red-100:#fee2e2;--red-line:#fecaca;--amber:#b45309;--amber-50:#fffbeb;--amber-100:#fef3c7;--amber-line:#fde68a;--canvas-fade:rgba(255,255,255,0);--shadow:0 1px 2px rgba(15,23,42,.04),0 12px 30px rgba(15,23,42,.06);--radius:14px}
html.dark{color-scheme:dark;--canvas:#0f172a;--card:#111827;--head:#172033;--line:#293548;--line-strong:#475569;--ink:#f8fafc;--ink-2:#cbd5e1;--muted:#94a3b8;--faint:#64748b;--blue:#60a5fa;--blue-ink:#93c5fd;--blue-50:#172554;--blue-100:#1e3a8a;--green:#34d399;--green-50:#052e2b;--green-100:#064e3b;--green-line:#065f46;--red:#fb7185;--red-50:#450a0a;--red-100:#7f1d1d;--red-line:#991b1b;--amber:#fbbf24;--amber-50:#422006;--amber-100:#713f12;--amber-line:#92400e;--canvas-fade:rgba(15,23,42,0);--shadow:none}
html{color-scheme:light;background:var(--canvas)}
body{background:var(--canvas);color:var(--ink);font-size:15px;background-image:radial-gradient(520px circle at var(--pointer-x,50%) var(--pointer-y,0%),rgba(37,99,235,.10),transparent 68%),radial-gradient(circle at 85% 22%,rgba(124,58,237,.045),transparent 20%);transition:background .45s ease-out}
body::before{display:none}.dark body{background-image:radial-gradient(560px circle at var(--pointer-x,50%) var(--pointer-y,0%),rgba(96,165,250,.15),transparent 68%),radial-gradient(circle at 85% 22%,rgba(167,139,250,.07),transparent 22%)}.wrap{max-width:none;width:100%;padding:22px 32px 80px}.mb-nav{box-sizing:border-box;width:100%;display:flex;align-items:center;gap:10px;margin:0 0 28px;padding:0 0 15px;border-bottom:1px solid var(--line);font-size:13px}.mb-nav a{display:inline-flex;align-items:center;gap:9px;color:var(--ink);font-weight:750;text-decoration:none}.mb-nav a:hover{color:var(--blue)}.mb-nav b{display:grid;place-items:center;width:27px;height:27px;border-radius:8px;background:var(--blue);color:#fff;font-size:16px}.mb-nav small{color:var(--muted);font-weight:650}.mb-theme{margin-left:auto;display:grid;place-items:center;width:36px;height:36px;border:0;border-radius:10px;background:transparent;color:var(--muted);font-size:17px;cursor:pointer}.mb-theme:hover{background:var(--blue-50);color:var(--blue)}body>.mb-nav{min-height:64px;margin-bottom:28px;padding:13px 38px 14px}header.top{position:relative;overflow:hidden;margin:0 0 28px;padding:30px 32px 28px;border:1px solid var(--line);border-radius:22px;background:linear-gradient(135deg,color-mix(in srgb,var(--blue-50) 88%,var(--card)),var(--card) 62%,color-mix(in srgb,var(--blue) 8%,var(--card)));box-shadow:var(--shadow)}header.top::after{content:"";position:absolute;width:310px;height:310px;right:-100px;top:-180px;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--blue) 18%,transparent),transparent 68%);pointer-events:none}header.top>*{position:relative;z-index:1}.wrap>.eyebrow{display:inline-flex;padding:6px 10px;border-radius:999px;background:var(--blue-50);border:1px solid var(--blue-100)}.wrap>.eyebrow+h1{margin-top:12px}
.eyebrow{color:var(--blue)}h1{font-size:clamp(30px,4vw,44px);letter-spacing:-.045em;margin-bottom:7px}.stamp{color:var(--muted)}.plate,.plate.open,.scroll,.glance>div,.card,figure,.tbl-scroll,.stat,.act,.mrow{box-shadow:var(--shadow)}nav.toc{background:linear-gradient(var(--canvas) 85%,var(--canvas-fade))}.plate{border-radius:16px}.glance>div::before,.stat::before{background:var(--blue)}.glance>div:first-child::before{background:var(--green)}h2,.sec-head h2{border-left-color:var(--blue)}
/* Institutional presentation: information hierarchy over decoration. */
html.dark{--canvas:#0d0d0c;--card:#171715;--head:#1d1c19;--line:#35332d;--line-strong:#514b3c;--ink:#f4f0e7;--ink-2:#d0c7b8;--muted:#9f9686;--faint:#70695e;--blue:#d7a84e;--blue-ink:#f1ca7a;--blue-50:#272114;--blue-100:#46371d;--green:#72c98c;--green-50:#142419;--green-100:#1c3825;--green-line:#31553a;--red:#ec7d70;--red-50:#321816;--red-100:#51231f;--red-line:#74342c;--amber:#e4b759;--amber-50:#302713;--amber-100:#4b3c1c;--amber-line:#70571f}.dark body{background-color:#0d0d0c;background-image:linear-gradient(rgba(216,168,78,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(216,168,78,.035) 1px,transparent 1px),radial-gradient(700px circle at var(--pointer-x,50%) var(--pointer-y,0%),rgba(216,168,78,.12),transparent 66%)}.dark .mb-nav{border-bottom-color:#35332d}.dark .mb-nav b{border-radius:6px;background:#f4f0e7;color:#171715}.dark .mb-theme{border-color:#514b3c}.dark header.top{border-color:#514b3c;background:linear-gradient(135deg,#1b1a17,#151512 68%,#241e14)}.dark .glance>div,.dark .card,.dark figure,.dark .tbl-scroll,.dark .stat,.dark .act,.dark .mrow,.dark .scroll{border-color:#35332d;background:#171715}.dark nav.toc a{border-radius:5px;box-shadow:none}.dark h1,.dark h2,.dark h3{letter-spacing:-.035em}.dark .plate{border-radius:8px}.dark .plate,.dark .plate.open{box-shadow:none}.dark .wrap>.eyebrow{border-radius:4px}.dark td,.dark .prose p,.dark p{color:#d0c7b8}.dark .stamp,.dark .lede{color:#9f9686}
@media(max-width:640px){.wrap{padding:16px 16px 52px}.mb-nav{margin-bottom:22px}.mb-nav small{font-size:11px}body>.mb-nav{min-height:58px;padding:10px 16px 11px}h1{font-size:30px}}
"""


def themed_style(style: str) -> str:
    """Add the public Morning Book token layer exactly once to a stylesheet."""
    if not style:
        style = STYLE_FALLBACK
    style = re.sub(r"/\* morning-book-shared-theme \*/.*?(?=</style>)", "", style, flags=re.S)
    return style[: -len("</style>")] + SHARED_THEME + "</style>"


def add_book_nav(text: str, page: Path) -> str:
    """Give every public daily report and analysis the same navigation/theme control."""
    # The services still use their former book name in their generated title
    # and masthead.  Preserve their data while keeping the public brand
    # consistent when archived pages are refreshed.
    text = text.replace("Morning Book", "Trading Book")
    # Every published page is exactly two levels down now — `stocks/reports/`,
    # `crypto/reports/`, `*/analysis/` — so the nav reaches the root. It used
    # to resolve to "../" for report pages, which was right while equity's sat
    # at `/reports/` and meant crypto's "Trading Book" link landed on
    # `/crypto/` instead of the book.
    home = "../../"
    nav = (
        f'<nav class="mb-nav" aria-label="Trading Book"><a href="{home}">'
        '<b aria-hidden="true">↗</b><span>Trading Book</span></a>'
        '<button class="mb-theme" type="button" aria-label="Switch to dark theme" title="Change theme">◐</button></nav>'
    )
    script = ("<script>(function(){try{if(localStorage.getItem('trading-book-theme')!=='light')document.documentElement.classList.add('dark')}catch(e){document.documentElement.classList.add('dark')}"
              "if(!matchMedia('(prefers-reduced-motion: reduce)').matches)addEventListener('pointermove',function(e){document.documentElement.style.setProperty('--pointer-x',e.clientX+'px');document.documentElement.style.setProperty('--pointer-y',e.clientY+'px')},{passive:true});"
              "var b=document.querySelector('.mb-theme');if(!b)return;function s(){var d=document.documentElement.classList.contains('dark');b.textContent=d?'☀':'◐';b.setAttribute('aria-label',d?'Switch to light theme':'Switch to dark theme')}s();b.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('trading-book-theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}s()})})();</script>")
    if 'class="mb-nav"' in text:
        updated = re.sub(r'<nav class="mb-nav"[^>]*>.*?</nav>', nav, text, count=1, flags=re.S)
        updated = re.sub(r"<script>\(function\(\)\{try\{if\(localStorage\.getItem\('trading-book-theme'\).*?</script>", "", updated, count=1, flags=re.S)
        return updated.replace(nav, nav + script, 1)
    return re.sub(r"(<body(?:\s[^>]*)?>)", r"\1" + nav + script, text, count=1, flags=re.I)


def newest_style(rows: list[dict]) -> str:
    """The renderer's own stylesheet, taken from the service's newest page.

    **Fetched, not read back off disk.** This used to read
    ``reports/<newest>.html`` — a file the mirror itself writes, and which an
    override replaces with a hand-finished page. So the archive took its theme
    from its own previous output and then stamped that over every page,
    including the fresh one: a stylesheet change could never reach the archive
    at all.

    It was found on 2026-09-25, when the first setup charts published
    unstyled. The SVG was right, the CSS sizing it was three deploys old, and
    every chart rendered at the browser's default 300x150 stretched across
    whatever space it was given. A theme read from the archive describes the
    archive; the theme has to come from the thing that renders.
    """
    for r in rows:
        page = fetch(BASE + f"{r['as_of']}.html")
        m = STYLE.search(page)
        if m:
            return m.group(0)
    return ""


def restyle_analysis(style: str) -> int:
    """The standing analyses, on the same stylesheet plus their bridge.

    Both books' folders, each with its own `_bridge.css` beside it — the two
    are identical today and are kept separate anyway, because the bridge maps
    *that* folder's hand-written class names and the two sets will drift.
    """
    style = themed_style(style)
    n = 0
    for folder in (ANALYSIS, CRYPTO_ANALYSIS):
        bridge = folder / "_bridge.css"
        if not bridge.exists():
            continue
        merged = style[: -len("</style>")] + bridge.read_text(encoding="utf-8") + "</style>"
        for page in folder.glob("*.html"):
            text = page.read_text(encoding="utf-8")
            updated = STYLE.sub(lambda _m: merged, text, count=1) if STYLE.search(text) else text
            updated = add_book_nav(updated, page)
            if updated != text:
                page.write_text(updated, encoding="utf-8")
                n += 1
    return n


def last_revised(page: Path) -> str:
    """The date this file last actually changed, from git.

    The filename date says what a study is *about*; it says nothing about when
    it was last right. On 2026-09-26 four analyses were corrected — two of them
    materially, the close-based replay moving from Rs 21.16L to Rs 23.8L — and
    the index went on showing 2026-09-23 and 2026-09-25 beside them, so the
    owner looked at the site and saw nothing had happened. It had; the column
    was answering a different question.

    Git rather than mtime: a checkout touches every file, and a revision date
    that moves when nothing was revised is worse than none.

    **The mirror's own commits are excluded**, and that is the whole
    difficulty. :func:`restyle_analysis` rewrites the stylesheet inside every
    analysis page whenever the renderer's theme moves, and those runs are
    committed as "mirror <date>". Counting them made six pages claim they were
    revised on 2026-09-24 when what changed was their CSS. So the newest commit
    that is *not* one of the mirror's own is the one that means something.
    """
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs",
             "--invert-grep", "--grep=^mirror ", "--", page.name],
            cwd=page.parent, capture_output=True, text=True, timeout=10, check=False,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def analyses(folder: Path = ANALYSIS) -> list[tuple[str, str, int, str]]:
    """(file, title, bytes, revised) for every standing analysis, newest first.

    ``revised`` is empty unless the page changed after the day it is named for,
    which is the only case worth a reader's attention.
    """
    out = []
    for page in sorted(folder.glob("*.html"), reverse=True):
        text = page.read_text(encoding="utf-8")
        found = re.search(r"<title>(.*?)</title>", text, re.S)
        revised = last_revised(page)
        out.append((page.name, html.unescape(found.group(1)).strip() if found else page.stem,
                    len(text), revised if revised > page.name[:10] else ""))
    return out


def restyle(style: str) -> int:
    """Swap every archived page's stylesheet for the newest one.

    The renderer only ever changes CSS against stable class names, so a page
    stored under an older theme re-skins cleanly. Without this the archive
    would be a museum of every theme the report has had."""
    style = themed_style(style)
    n = 0
    for page in [
        *REPORTS.glob("20*.html"),
        *OVERRIDES.glob("20*.html"),
        *EXTRAS.glob("20*.html"),
        *CRYPTO_REPORTS.glob("20*.html"),
    ]:
        text = page.read_text(encoding="utf-8")
        updated = STYLE.sub(lambda _m: style, text, count=1) if STYLE.search(text) else text
        updated = add_book_nav(updated, page)
        if updated != text:
            page.write_text(updated, encoding="utf-8")
            n += 1
    return n


def days_with_only_extras(rows: list[dict]) -> list[dict]:
    """Days that have a hand-written page but no report yet.

    The index is built from the service's report list, so a day with no report
    had no row at all — and anything written for it was published and
    unreachable. That is how the IPO review for 25 September came to sit at a
    live URL that nothing linked to: it was written at 01:30, and the book for
    that day does not exist until the 18:00 build.

    These rows carry no link to ``reports/<day>.html``, because there is no
    report there to link to. They say so instead.
    """
    known = {r["as_of"] for r in rows}
    days = {p.stem[:10] for p in EXTRAS.glob("20*.html")} - known
    return [
        {
            "as_of": day,
            "summary": "",
            "bytes": sum(p.stat().st_size for p in EXTRAS.glob(f"{day}_*.html")),
            "no_report": True,
        }
        for day in sorted(days, reverse=True)
    ]


def primary_page(day: str) -> str | None:
    """The page the day's own date should open.

    The report when there is one, and otherwise the day's first hand-written
    page. A date rendered as plain text reads as a dead row — every other date
    in the index is a link — so the one page that day does have is what its
    date points at.
    """
    if (REPORTS / f"{day}.html").exists():
        return f"reports/{day}.html"
    pages = sorted(EXTRAS.glob(f"{day}_*.html"))
    return f"reports/{pages[0].name}" if pages else None


def row_html(r: dict, *, prefix: str = "reports", with_extras: bool = True) -> str:
    """One day in a section index. A day with no book yet is not a dead row."""
    if r.get("no_report"):
        day, target = r["as_of"], primary_page(r["as_of"])
        head = f'<a href="../{target}">{day}</a>' if target else day
        return (
            f'<tr><td class="l">{head}{extras_for(r["as_of"], base="reports")}</td>'
            '<td class="l warn"><span>no book yet</span></td>'
            '<td class="l">written before the 18:00 build</td>'
            f'<td>{r["bytes"] // 1024} KB</td></tr>'
        )
    gate = "fail" if "BLOCKED" in verdict(r["summary"]) else "pass"
    # Passed in, never inferred from `prefix`. It used to read
    # `prefix == "../reports"`, which worked only because equity's reports sat
    # at the root and crypto's did not — so the moment both books used the same
    # relative prefix, every crypto row sprouted equity's IPO reviews.
    extras = extras_for(r["as_of"], base="reports") if with_extras else ""
    return (
        f'<tr><td class="l"><a href="{prefix}/{r["as_of"]}.html">{r["as_of"]}</a>'
        f"{extras}</td>"
        f'<td class="l {gate}"><span>{html.escape(verdict(r["summary"]))}</span></td>'
        f'<td class="l">{html.escape(" · ".join((r["summary"] or "").splitlines()[1:3]))}</td>'
        f'<td>{r["bytes"] // 1024} KB</td></tr>'
    )


def months_html(rows: list[dict], *, prefix: str, with_extras: bool) -> list[str]:
    """The day tables, newest month first."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    extra_days = days_with_only_extras(rows) if with_extras else []
    for r in (*rows, *extra_days):
        by_month[r["as_of"][:7]].append(r)
    parts = []
    for month in sorted(by_month, reverse=True):
        label = date.fromisoformat(by_month[month][0]["as_of"]).strftime("%B %Y")
        items = "".join(
            row_html(r, prefix=prefix, with_extras=with_extras)
            for r in sorted(by_month[month], key=lambda r: r["as_of"], reverse=True)
        )
        parts.append(
            f"<h2>{label}</h2>"
            '<div class="scroll"><table><thead><tr><th class="l">day</th>'
            '<th class="l">gate</th><th class="l">summary</th><th>size</th>'
            f"</tr></thead><tbody>{items}</tbody></table></div>"
        )
    return parts


def analysis_html(folder: Path) -> str:
    """The standing analyses for one book, or "" when it has none yet."""
    found = analyses(folder)
    if not found:
        return ""
    items = "".join(
        f'<tr><td class="l"><a href="analysis/{name}">{html.escape(title)}</a></td>'
        f'<td class="l"><span class="badge">analysis</span></td>'
        f'<td class="l">{html.escape(name[:10])}</td>'
        f'<td class="l">{f"<b>revised {html.escape(revised)}</b>" if revised else ""}</td>'
        f"<td>{size // 1024} KB</td></tr>"
        for name, title, size, revised in found
    )
    return (
        '<h2>Analysis</h2><div class="scroll"><table><thead><tr>'
        '<th class="l">document</th><th class="l">kind</th><th class="l">as of</th>'
        '<th class="l">revised</th><th>size</th></tr></thead><tbody>'
        + items
        + "</tbody></table></div>"
    )


def crypto_rows() -> list[dict]:
    """The crypto days, read off disk.

    Equity's index comes from the service's API; crypto has none yet, so the
    files themselves are the index. The verdict is lifted out of the rendered
    page's own plate rather than recomputed — the page is the record, and a
    second opinion about it formed here is exactly the kind of disagreement
    this archive exists not to have.
    """
    out = []
    for page in sorted(CRYPTO_REPORTS.glob("20*.html"), reverse=True):
        text = page.read_text(encoding="utf-8")
        state = re.search(r'<div class="state">(.*?)</div>', text, re.S)
        plate = re.search(r'<div class="plate [^"]*">.*?<p>(.*?)</p>', text, re.S)
        headline = html.unescape(state.group(1)).strip() if state else "—"
        detail = html.unescape(re.sub(r"<[^>]+>", "", plate.group(1))).strip() if plate else ""
        out.append(
            {
                "as_of": page.stem,
                "summary": f"{headline}\n{detail}",
                "bytes": len(text),
            }
        )
    return out


def _stub(path: Path, target: str, what: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<!doctype html><meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="0; url={target}">'
        f'<link rel="canonical" href="{target}">'
        f'<title>Moved</title><a href="{target}">This {what} moved to {target}</a>',
        encoding="utf-8",
    )


def write_redirects() -> int:
    """Keep every URL this archive has ever published working.

    Two moves so far, and the same rule for both: the pages moved, the links
    people saved did not. A one-line meta-refresh at each old path costs
    nothing, and an archive that breaks its own links to look tidier has made
    itself worse.

    * 2026-09-29 — the analyses split into `stocks/` and `crypto/`.
    * 2026-09-30 — equity's daily reports moved from `/reports/` to
      `stocks/reports/`, so the two books finally match. That is the bigger
      set: nine months of daily pages and every IPO review beside them.

    `canonical` as well as the refresh, so a search engine that indexed the old
    path learns the new one rather than carrying both.
    """
    moved = {p.name: "stocks" for p in ANALYSIS.glob("*.html")}
    moved.update({p.name: "crypto" for p in CRYPTO_ANALYSIS.glob("*.html")})
    for name, book in moved.items():
        _stub(ROOT / "analysis" / name, f"../{book}/analysis/{name}", "analysis")

    for page in REPORTS.glob("20*.html"):
        _stub(ROOT / "reports" / page.name, f"../stocks/reports/{page.name}", "report")

    return len(moved) + len(list(REPORTS.glob("20*.html")))


def build_site(rows: list[dict], style: str) -> None:
    """The hub and the two section pages."""
    themed = themed_style(style)
    crypto = crypto_rows()
    newest = rows[0]["as_of"] if rows else ""
    newest_crypto = crypto[0]["as_of"] if crypto else ""

    (STOCKS / "index.html").write_text(
        SECTION.format(
            style=themed,
            book="Stocks",
            eyebrow="equity-service · nse · daily report archive",
            stamp=(
                f"{len(rows)} trading days, mirrored every evening at 19:00 IST."
                + (f' <a href="reports/{newest}.html">Open the latest ({newest}) →</a>' if newest else "")
            ),
            body=analysis_html(ANALYSIS)
            + "".join(months_html(rows, prefix="reports", with_extras=True)),
            footer=(
                "Each page is the report as equity-service rendered it that evening; "
                "hand-written sections (IPO reviews) are added over it."
            ),
        ),
        encoding="utf-8",
    )

    (CRYPTO / "index.html").write_text(
        SECTION.format(
            style=themed,
            book="Crypto",
            eyebrow="crypto-service · delta exchange india · perpetual futures",
            stamp=(
                f"{len(crypto)} day(s) recorded."
                + (
                    f' <a href="reports/{newest_crypto}.html">Open the latest '
                    f"({newest_crypto}) →</a>"
                    if newest_crypto
                    else " The first report lands today."
                )
            ),
            body=analysis_html(CRYPTO_ANALYSIS)
            + "".join(months_html(crypto, prefix="reports", with_extras=False)),
            footer=(
                "Each page is the book as crypto-service's <code>daily_report</code> "
                "rendered it. Funding is not in any P&amp;L figure yet — see the note "
                "under Performance on any day's page."
            ),
        ),
        encoding="utf-8",
    )

    market_rows = "".join(
        f"<tr><td>{start}</td><td>{end}</td><td>{condition}</td><td class=\"{'good' if change >= 0 else 'bad'}\">{change:+.2f}%</td></tr>"
        for start, end, condition, change in (
            ("25 Sep 2026", "Current", "Downtrend", -1.84),
            ("19 Sep 2026", "24 Sep 2026", "Rally attempt", -1.22),
            ("09 Sep 2026", "18 Sep 2026", "Downtrend", -0.37),
            ("13 May 2026", "08 Sep 2026", "Uptrend under pressure", 0.95),
            ("09 Apr 2026", "12 May 2026", "Confirmed uptrend", -1.67),
            ("08 Apr 2026", "08 Apr 2026", "Rally attempt", 0.00),
            ("31 Mar 2026", "07 Apr 2026", "Downtrend", 3.54),
        )
    )
    market_body = f'''<section class="glance"><div><div class="n bad">−0.71%</div><div class="k">six-month Nifty return</div></div><div><div class="n bad">Downtrend</div><div class="k">current MarketSmith condition</div></div><div><div class="n">25 Sep</div><div class="k">current condition began</div></div></section>
<section class="prose"><h2>Market condition history</h2><p>MarketSmith's public market-condition API, recorded at 30 September 2026. The six-month return compounds the condition intervals from 31 March onward. It is a market context signal, not a trade recommendation.</p></section>
<div class="scroll"><table><thead><tr><th>start</th><th>end</th><th>MarketSmith condition</th><th>Nifty 50 return</th></tr></thead><tbody>{market_rows}</tbody></table></div>
<p class="note">Source: MarketSmith India’s <code>mshkSubscription/getMarketHistory.json</code>. The equity service now reads this API for the market-status input used by the regime recorder; distribution-day counts remain separately sourced from MarketSmith's daily-close feed.</p>'''
    (STOCKS / "market-trend.html").write_text(
        SECTION.format(
            style=themed,
            book="Market Trend",
            eyebrow="MarketSmith · Nifty 50 · six-month context",
            stamp="API snapshot: 30 September 2026",
            body=market_body,
            footer="Market context is displayed separately from system performance.",
        ),
        encoding="utf-8",
    )

    (ROOT / "index.html").write_text(
        landing_html(
            style,
            {
                "stocks_days": len(rows),
                "stocks_newest": newest or "—",
                "stocks_analyses": len(analyses(ANALYSIS)),
                "crypto_days": len(crypto),
                "crypto_newest": newest_crypto or "—",
                "crypto_analyses": len(analyses(CRYPTO_ANALYSIS)),
            },
        ),
        encoding="utf-8",
    )
    (ROOT / "latest.html").write_text(
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=stocks/reports/{newest}.html">'
        f'<title>Trading Book — latest</title>'
        f'<a href="stocks/reports/{newest}.html">{newest}</a>',
        encoding="utf-8",
    )
    (REPORTS / "index.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    if crypto:
        (CRYPTO_REPORTS / "index.json").write_text(json.dumps(crypto, indent=1), encoding="utf-8")


BOOK_AS_OF = "2026-09-29"
"""When `show_performance` last produced the figures below.

Hardcoded rather than fetched, because the landing page must render from a
clone with no network and no dyno. Re-run
`python manage.py show_performance --tenant t-default --months 6` and paste;
the date is printed on the page so a stale table is visible rather than silent.
"""

BOOK_MONTHS: list[tuple[str, int, int, float]] = [
    # (month, realised rupees, closed trades, win %)
    ("Apr", 2726, 25, 28.0),
    ("May", -108593, 61, 21.3),
    ("Jun", 83683, 20, 35.0),
    ("Jul", 122456, 19, 31.6),
    ("Aug", 9353, 11, 45.5),
    ("Sep", 306757, 23, 56.5),
]
BOOK_TOTAL = 416382
BOOK_CAPITAL = 2_000_000
BOOK_TRADES = 159
BOOK_WIN_PCT = 32.1
BOOK_GAIN_LOSS = 1.68
BOOK_AVG_WIN = 20212
BOOK_AVG_LOSS = -5689


def landing_html(style: str, stats: dict[str, object]) -> str:
    """The hub, as a landing page rather than an index.

    Everything is inline — no external script, no font CDN, no chart library.
    The book's pages have always loaded nothing from outside themselves, and a
    landing page is the worst place to break that: it is the one page a
    stranger opens, often on a phone, sometimes behind a filter that eats
    third-party requests.
    """
    peak = max(abs(v) for _, v, _, _ in BOOK_MONTHS) or 1
    bars = []
    cumulative = 0
    points = []
    for i, (name, value, trades, win) in enumerate(BOOK_MONTHS):
        cumulative += value
        points.append(cumulative)
        height = abs(value) / peak * 100
        cls = "up" if value >= 0 else "down"
        bars.append(
            f'<div class="bar-slot" data-month="{name}" data-value="{value}" '
            f'data-return="{value / BOOK_CAPITAL * 100:+.1f}" '
            f'data-trades="{trades}" data-win="{win}" tabindex="0" '
            f'aria-label="{name}: {value / BOOK_CAPITAL * 100:+.1f} percent, '
            f'{value:+,} rupees over {trades} trades">'
            f'<div class="bar {cls}" style="--h:{height:.1f}%"></div>'
            f'<span class="bar-label">{name}</span></div>'
        )
    span = max(max(points), 0) - min(min(points), 0) or 1
    coords = " ".join(
        f"{i / (len(points) - 1) * 100:.2f},{100 - (v - min(min(points), 0)) / span * 100:.2f}"
        for i, v in enumerate(points)
    )

    disproved = [
        ("G3 — momentum gate", "Admits 4.4% of the population for +0.34pp, p=0.43. "
         "Momentum against return is U-shaped. Tighter thresholds measured worse."),
        ("G5 — RRG quadrant gate", "+0.16pp at t=0.45 on disjoint samples, sign-flipping "
         "between halves. WEAKENING groups had the highest forward return of the four."),
        ("Industry relative strength", "Top-ranked industries beat the rest by +0.26pp, "
         "t=0.61, permutation p=0.189. The one version that survived a split was the "
         "size factor wearing a different name."),
    ]
    cards = "".join(
        f'<article class="dis"><h3>{t}</h3><p>{d}</p></article>' for t, d in disproved
    )

    rows = "".join(
        f'<tr><td>{n}</td><td class="{"good" if v >= 0 else "bad"}">'
        f'{v / BOOK_CAPITAL * 100:+.1f}%</td><td>{tr}</td><td>{w:.1f}%</td>'
        f'<td class="{"good" if v >= 0 else "bad"}">{v:+,}</td></tr>'
        for n, v, tr, w in BOOK_MONTHS
    )
    best_month = max(BOOK_MONTHS, key=lambda row: row[1])
    worst_month = min(BOOK_MONTHS, key=lambda row: row[1])

    page = (
        LANDING.replace("@@STYLE@@", style)
        .replace("@@BARS@@", "".join(bars))
        .replace("@@COORDS@@", coords)
        .replace("@@CARDS@@", cards)
        .replace("@@ROWS@@", rows)
        .replace("@@TOTAL@@", f"{BOOK_TOTAL:,}")
        .replace("@@CAPITAL@@", f"{BOOK_CAPITAL:,}")
        .replace("@@RETURN@@", f"{BOOK_TOTAL / BOOK_CAPITAL * 100:.1f}")
        .replace("@@BESTMONTH@@", best_month[0])
        .replace("@@BESTRETURN@@", f"{best_month[1] / BOOK_CAPITAL * 100:.1f}")
        .replace("@@BESTPNL@@", f"{best_month[1]:,}")
        .replace("@@WORSTMONTH@@", worst_month[0])
        .replace("@@WORSTRETURN@@", f"{abs(worst_month[1] / BOOK_CAPITAL * 100):.1f}")
        .replace("@@WORSTPNL@@", f"{abs(worst_month[1]):,}")
        .replace("@@TRADES@@", str(BOOK_TRADES))
        .replace("@@WIN@@", f"{BOOK_WIN_PCT:.1f}")
        .replace("@@GL@@", f"{BOOK_GAIN_LOSS:.2f}")
        .replace("@@AVGWIN@@", f"{BOOK_AVG_WIN:,}")
        .replace("@@AVGLOSS@@", f"{abs(BOOK_AVG_LOSS):,}")
        .replace("@@ASOF@@", BOOK_AS_OF)
        .replace("@@SDAYS@@", str(stats["stocks_days"]))
        .replace("@@SNEW@@", str(stats["stocks_newest"]))
        .replace("@@SANA@@", str(stats["stocks_analyses"]))
        .replace("@@CDAYS@@", str(stats["crypto_days"]))
        .replace("@@CNEW@@", str(stats["crypto_newest"]))
        .replace("@@CANA@@", str(stats["crypto_analyses"]))
    )
    # Lead with independently checkable evidence rather than decorative status.
    return re.sub(r'<aside class="system-card".*?</aside>', HERO_PROOF, page, count=1, flags=re.S)


LANDING = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A systematic India equity and crypto trading book: live rules, realised evidence, and every rejected idea.">
<meta name="theme-color" content="#050814"><title>Trading Book</title>@@STYLE@@<style>
:root{--accent:#5eead4;--cyan:#22d3ee;--violet:#a78bfa;--pink:#f472b6;--night:#050814}
html{scroll-behavior:smooth;scroll-padding-top:90px}body{background:var(--night);overflow-x:hidden}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:-2;background:
 radial-gradient(circle at 18% 12%,rgba(34,211,238,.11),transparent 28%),
 radial-gradient(circle at 82% 22%,rgba(167,139,250,.10),transparent 25%),
 linear-gradient(rgba(94,234,212,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(94,234,212,.025) 1px,transparent 1px);background-size:auto,auto,54px 54px,54px 54px}
.page-progress{position:fixed;inset:0 0 auto;height:2px;z-index:1000;background:rgba(255,255,255,.03)}
.page-progress span{display:block;width:100%;height:100%;transform:scaleX(0);transform-origin:left;background:linear-gradient(90deg,var(--cyan),var(--violet),var(--pink))}
.site-nav{position:fixed;z-index:50;top:18px;left:50%;transform:translateX(-50%);width:min(1080px,calc(100% - 28px));display:flex;align-items:center;justify-content:space-between;gap:18px;padding:10px 12px 10px 16px;border:1px solid rgba(255,255,255,.1);border-radius:18px;background:rgba(5,8,20,.72);backdrop-filter:blur(22px);box-shadow:0 18px 60px rgba(0,0,0,.3)}
.brand{display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none;font-weight:850;letter-spacing:-.03em}.brand-mark{display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:linear-gradient(135deg,var(--cyan),var(--violet));color:#051018;font-size:14px;box-shadow:0 0 24px rgba(34,211,238,.22)}
.nav-links{display:flex;gap:4px;align-items:center}.nav-links a{color:var(--muted);text-decoration:none;font-size:12px;font-weight:650;padding:8px 9px;border-radius:10px}.nav-links a:hover,.nav-links a:focus-visible{color:var(--ink);background:rgba(255,255,255,.06)}
.nav-cta,.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;border-radius:11px;font-weight:750;transition:transform .2s,border-color .2s,box-shadow .2s}.nav-cta{padding:9px 13px;color:#061018;background:var(--accent);font-size:12px}.button{padding:12px 17px;border:1px solid rgba(255,255,255,.12);color:var(--ink)}.button.primary{background:linear-gradient(135deg,var(--cyan),var(--violet));color:#050814;border:0;box-shadow:0 10px 32px rgba(34,211,238,.15)}.button:hover{transform:translateY(-2px);border-color:var(--cyan)}
.nav-toggle{display:none;border:0;background:transparent;color:var(--ink);font-size:22px}
.landing-wrap{max-width:1180px;margin:0 auto;padding:0 28px 84px;position:relative}.hero{min-height:100vh;display:grid;grid-template-columns:minmax(0,1.08fr) minmax(360px,.92fr);gap:clamp(36px,7vw,88px);align-items:center;padding:125px 0 72px;position:relative}
#market-canvas{position:absolute;inset:76px -12vw 0;width:124vw;height:calc(100% - 76px);opacity:.48;z-index:-1;mask-image:linear-gradient(to bottom,black,transparent 94%)}
.status{display:inline-flex;align-items:center;gap:9px;padding:7px 12px;border:1px solid rgba(94,234,212,.22);border-radius:99px;background:rgba(94,234,212,.06);color:var(--accent);font-size:11px;font-weight:750;letter-spacing:.09em;text-transform:uppercase}.pulse{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 14px var(--accent);animation:pulse 2s ease-in-out infinite}@keyframes pulse{50%{opacity:.35;box-shadow:none}}
.hero h1{font-size:clamp(3.6rem,8.5vw,7.7rem);line-height:.9;letter-spacing:-.075em;margin:24px 0;color:#f6f8ff;max-width:8ch}.hero h1 em{font-family:Georgia,serif;font-weight:400;background:linear-gradient(100deg,var(--cyan),var(--violet) 52%,var(--pink));-webkit-background-clip:text;color:transparent}.hero-copy{font-size:clamp(1rem,1.7vw,1.18rem);line-height:1.72;color:var(--ink-2);max-width:59ch}.hero-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}.micro-proof{display:flex;flex-wrap:wrap;gap:18px;margin-top:34px;color:var(--faint);font-size:11px;text-transform:uppercase;letter-spacing:.08em}.micro-proof span::before{content:"✓";color:var(--accent);margin-right:7px}
.system-card{border:1px solid rgba(255,255,255,.1);border-radius:24px;background:linear-gradient(145deg,rgba(19,28,46,.86),rgba(9,14,29,.72));backdrop-filter:blur(24px);padding:22px;box-shadow:0 40px 100px rgba(0,0,0,.35);transform:perspective(900px) rotateY(-3deg) rotateX(1deg);transition:transform .35s}.system-card:hover{transform:none}.window-bar{display:flex;align-items:center;gap:7px;border-bottom:1px solid rgba(255,255,255,.07);padding-bottom:16px;color:var(--muted);font:11px var(--mono)}.window-bar i{width:8px;height:8px;border-radius:50%;background:#fb7185}.window-bar i:nth-child(2){background:#fbbf24}.window-bar i:nth-child(3){background:#4ade80}.window-bar span{margin-left:auto}
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;align-items:center;margin:26px 0}.flow-step{position:relative;text-align:center;padding:12px 3px 10px;border:1px solid var(--line);border-radius:10px;background:rgba(255,255,255,.025);font:700 9px var(--mono);letter-spacing:.08em;color:var(--muted)}.flow-step.active{color:var(--accent);border-color:rgba(94,234,212,.35);box-shadow:inset 0 0 25px rgba(94,234,212,.05)}.flow-step:not(:last-child)::after{content:"";position:absolute;right:-7px;top:50%;width:7px;height:1px;background:var(--line-strong)}
.terminal{font:12px/1.8 var(--mono);color:var(--ink-2);background:#060a14;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:15px 16px}.terminal div{display:flex;justify-content:space-between;gap:10px}.terminal code{background:none;padding:0;color:var(--muted)}.terminal b{font-weight:650}.terminal .ok{color:var(--accent)}.terminal .wait{color:#fbbf24}
.mini-curve{width:100%;height:110px;margin-top:20px}.mini-curve path{fill:none;stroke:url(#heroGradient);stroke-width:3;stroke-linecap:round;filter:drop-shadow(0 0 7px rgba(34,211,238,.35));stroke-dasharray:700;stroke-dashoffset:700;animation:draw 2s .4s ease forwards}@keyframes draw{to{stroke-dashoffset:0}}
.ticker{border-block:1px solid rgba(255,255,255,.07);overflow:hidden;margin:0 calc(50% - 50vw);background:rgba(255,255,255,.018)}.ticker-track{display:flex;width:max-content;gap:44px;padding:13px 0;animation:marquee 28s linear infinite;color:var(--muted);font:700 10px var(--mono);letter-spacing:.12em;text-transform:uppercase}.ticker-track b{color:var(--accent)}@keyframes marquee{to{transform:translateX(-50%)}}
.section{padding:110px 0 0}.section-head{display:grid;grid-template-columns:.65fr 1.35fr;gap:40px;align-items:start;margin-bottom:30px}.section-kicker{color:var(--cyan);font:750 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;margin:7px 0}.section h2{border:0;padding:0;margin:0;font-size:clamp(2.2rem,5vw,4.4rem);line-height:1.02;letter-spacing:-.055em}.section-head p:last-child{color:var(--ink-2);font-size:16px;line-height:1.7;max-width:56ch;margin:6px 0 0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 18px}.kpi{position:relative;overflow:hidden;border:1px solid rgba(255,255,255,.08);background:linear-gradient(145deg,rgba(19,28,46,.8),rgba(12,18,33,.65));border-radius:16px;padding:20px}.kpi::after{content:"";position:absolute;inset:auto -20% -80% 30%;height:120px;background:radial-gradient(circle,var(--glow,rgba(34,211,238,.14)),transparent 66%)}.kpi b{display:block;font-size:clamp(1.45rem,3vw,2.3rem);letter-spacing:-.045em;font-variant-numeric:tabular-nums;color:#f6f8ff}.kpi span{display:block;font:650 10px var(--mono);color:var(--muted);margin-top:8px;text-transform:uppercase;letter-spacing:.09em}
.chartwrap{border:1px solid rgba(255,255,255,.09);background:rgba(13,20,36,.72);border-radius:22px;padding:24px;margin-top:14px;box-shadow:0 30px 80px rgba(0,0,0,.22)}.chartwrap header{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}.chart-label{margin:0;color:var(--muted);font:650 11px var(--mono);text-transform:uppercase;letter-spacing:.08em}.toggle,.filters{display:flex;gap:4px;padding:4px;border:1px solid var(--line);border-radius:11px;background:#080d19}.toggle button,.filters button{background:transparent;border:0;color:var(--muted);font:650 11px var(--mono);padding:7px 10px;border-radius:7px;cursor:pointer}.toggle button[aria-pressed=true],.filters button[aria-pressed=true]{background:var(--line);color:var(--ink)}
.bars{display:flex;align-items:flex-end;gap:clamp(5px,1.5vw,16px);height:215px;margin-top:22px}.bar-slot{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;cursor:pointer;border-radius:8px;outline-offset:3px}.bar-slot:hover,.bar-slot:focus-visible{background:rgba(255,255,255,.035)}.bar{width:100%;max-width:70px;height:0;border-radius:7px 7px 2px 2px;transition:height 1s cubic-bezier(.2,.75,.2,1)}.loaded .bar{height:var(--h)}.bar.up{background:linear-gradient(180deg,var(--accent),rgba(94,234,212,.25));box-shadow:0 -8px 24px rgba(94,234,212,.12)}.bar.down{background:linear-gradient(180deg,rgba(248,113,113,.22),var(--red))}.bar-label{font:650 10px var(--mono);color:var(--muted);margin-top:8px}.readout{min-height:1.5em;font-size:13px;color:var(--ink-2);margin:15px 0 0;font-variant-numeric:tabular-nums}.curve{width:100%;height:215px;margin-top:22px;display:none}.curve polyline{fill:none;stroke:var(--accent);stroke-width:2.4;vector-effect:non-scaling-stroke;stroke-dasharray:1000;stroke-dashoffset:1000;animation:draw 1.5s .2s ease forwards}.showcurve .bars{display:none}.showcurve .curve{display:block}.data-table{margin-top:14px;border-radius:16px;overflow:hidden;border:1px solid var(--line)}
.evidence-grid{display:grid;grid-template-columns:1fr;gap:18px}.evidence-card{border:1px solid rgba(255,255,255,.09);border-radius:22px;background:rgba(13,20,36,.72);overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.22)}.browser-bar{display:flex;align-items:center;gap:7px;height:48px;padding:0 15px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.025)}.browser-bar i{width:7px;height:7px;border-radius:50%;background:#fb7185}.browser-bar i:nth-child(2){background:#fbbf24}.browser-bar i:nth-child(3){background:#4ade80}.address{margin-left:7px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--faint);font:10px var(--mono)}.external{margin-left:auto;color:var(--accent);text-decoration:none;font:700 10px var(--mono);white-space:nowrap}.zerodha-link{display:block;background:#fff;overflow:hidden}.zerodha-proof{display:block;width:100%;height:auto;background:#fff;transition:transform .3s ease}.zerodha-link:hover .zerodha-proof,.zerodha-link:focus-visible .zerodha-proof{transform:scale(1.012)}
.proof-image{display:block;width:100%;height:520px;object-fit:contain;background:#fff;cursor:zoom-in}.evidence-caption{padding:15px 18px;color:var(--ink-2);font-size:12.5px;border-top:1px solid var(--line)}
.research-controls{display:flex;justify-content:flex-end;margin-bottom:14px}.research-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.research-card{display:flex;min-height:235px;flex-direction:column;padding:20px;border:1px solid rgba(255,255,255,.08);border-radius:18px;background:linear-gradient(145deg,rgba(19,28,46,.76),rgba(10,15,28,.6));text-decoration:none;transition:transform .22s,border-color .22s}.research-card:hover{transform:translateY(-5px);border-color:rgba(34,211,238,.42)}.research-card[hidden]{display:none}.research-card small{font:750 10px var(--mono);letter-spacing:.09em;text-transform:uppercase;color:var(--cyan)}.research-card h3{font-size:20px;line-height:1.25;color:var(--ink);margin:18px 0 10px}.research-card p{color:var(--muted);font-size:13px;line-height:1.55;margin:0}.research-card span{margin-top:auto;padding-top:20px;color:var(--accent);font-weight:700}
.truth-grid,.fit-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.truth-card,.fit-card{position:relative;padding:22px;border:1px solid rgba(255,255,255,.08);border-radius:18px;background:linear-gradient(145deg,rgba(19,28,46,.76),rgba(10,15,28,.6))}.truth-card small,.fit-card small{font:750 10px var(--mono);letter-spacing:.09em;text-transform:uppercase;color:var(--cyan)}.truth-card h3,.fit-card h3{font-size:20px;margin:17px 0 9px}.truth-card p,.fit-card p{color:var(--muted);font-size:13.5px;line-height:1.65;margin:0}.truth-card strong{color:var(--ink)}
.status-strip{display:flex;align-items:flex-start;gap:13px;margin:18px 0;padding:15px 17px;border:1px solid rgba(251,191,36,.2);border-radius:14px;background:rgba(251,191,36,.055);color:var(--ink-2);font-size:13px;line-height:1.55}.status-strip b{flex:0 0 auto;color:#fbbf24;font:750 10px var(--mono);letter-spacing:.08em;text-transform:uppercase;margin-top:3px}
.risk-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.risk-number{display:flex;flex-direction:column;justify-content:flex-end;min-height:310px;padding:26px;border:1px solid rgba(248,113,113,.22);border-radius:20px;background:radial-gradient(circle at 80% 15%,rgba(248,113,113,.14),transparent 42%),rgba(13,20,36,.72)}.risk-number.best{border-color:rgba(94,234,212,.25);background:radial-gradient(circle at 80% 15%,rgba(94,234,212,.15),transparent 42%),rgba(13,20,36,.72)}.risk-number small{font:750 10px var(--mono);color:#fb7185;letter-spacing:.1em;text-transform:uppercase}.risk-number.best small{color:var(--accent)}.risk-number b{font-size:clamp(3rem,7vw,6rem);letter-spacing:-.06em;color:#fb7185;margin:12px 0}.risk-number.best b{color:var(--accent)}.risk-number p{color:var(--muted);margin:0;line-height:1.6}.risk-list{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;grid-column:1/-1}.risk-item{padding:17px 19px;border:1px solid var(--line);border-radius:14px;background:rgba(13,20,36,.68)}.risk-item b{display:block;margin-bottom:5px}.risk-item span{color:var(--muted);font-size:13px;line-height:1.55}
.partner-panel{margin-top:110px;padding:clamp(28px,6vw,64px);border:1px solid rgba(94,234,212,.18);border-radius:28px;background:radial-gradient(circle at 100% 0,rgba(34,211,238,.12),transparent 35%),radial-gradient(circle at 0 100%,rgba(167,139,250,.14),transparent 38%),rgba(13,20,36,.76)}.partner-panel .section-head{margin-bottom:28px}.partner-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:26px}.partner-note{max-width:72ch;color:var(--faint);font-size:11.5px;line-height:1.6;margin:18px 0 0}.mini-list{list-style:none;padding:0;margin:15px 0 0;display:grid;gap:8px}.mini-list li{color:var(--ink-2);font-size:12.5px}.mini-list li::before{content:"\\2192";color:var(--accent);margin-right:8px}
.books{display:grid;grid-template-columns:1fr 1fr;gap:18px}.book{position:relative;overflow:hidden;display:block;min-height:260px;padding:28px;border:1px solid rgba(255,255,255,.09);border-radius:22px;background:rgba(13,20,36,.72);text-decoration:none;transition:transform .25s,border-color .25s}.book:hover{transform:translateY(-4px);border-color:var(--book-accent)}.book::after{content:"";position:absolute;width:240px;height:240px;border-radius:50%;right:-90px;bottom:-120px;background:radial-gradient(circle,var(--book-glow),transparent 70%)}.book small{font:700 10px var(--mono);color:var(--book-accent);letter-spacing:.1em;text-transform:uppercase}.book h3{font-size:clamp(2rem,4vw,3.5rem);color:var(--ink);letter-spacing:-.05em;margin:42px 0 8px}.book p{color:var(--muted);max-width:38ch}.book b{display:block;color:var(--ink-2);margin-top:24px}.closing{margin-top:110px;padding:70px 30px;text-align:center;border:1px solid rgba(255,255,255,.09);border-radius:26px;background:radial-gradient(circle at 50% 120%,rgba(167,139,250,.18),transparent 52%),rgba(13,20,36,.7)}.closing h2{font-size:clamp(2.6rem,7vw,6rem);max-width:12ch;margin:0 auto 20px;line-height:.95}.closing p{max-width:56ch;margin:0 auto 25px;color:var(--ink-2)}
[data-reveal]{opacity:1;transform:translateY(24px);transition:transform .7s ease}[data-reveal].visible{transform:none}.lightbox{position:fixed;inset:0;z-index:100;display:none;place-items:center;padding:24px;background:rgba(2,4,10,.9);backdrop-filter:blur(16px)}.lightbox.open{display:grid}.lightbox img{max-width:min(920px,96vw);max-height:90vh;border-radius:18px;box-shadow:0 30px 100px #000}.lightbox button{position:absolute;right:22px;top:18px;border:0;background:transparent;color:white;font-size:34px;cursor:pointer}
.site-footer{display:grid;grid-template-columns:1fr auto;gap:24px;align-items:end}.site-footer p{margin:0;max-width:78ch}.source-note{font:10px var(--mono);color:var(--faint);text-align:right}
@media(max-width:900px){.nav-links{display:none;position:absolute;top:61px;left:0;right:0;padding:10px;background:rgba(5,8,20,.96);border:1px solid var(--line);border-radius:15px;flex-direction:column;align-items:stretch}.site-nav.open .nav-links{display:flex}.nav-toggle{display:block}.nav-cta{display:none}.hero{grid-template-columns:1fr;padding-top:132px}.system-card{transform:none}.section-head{grid-template-columns:1fr;gap:10px}.kpis{grid-template-columns:1fr 1fr}.evidence-grid,.books,.risk-grid,.risk-list{grid-template-columns:1fr}.research-grid,.truth-grid,.fit-grid{grid-template-columns:1fr 1fr}}
@media(max-width:600px){.landing-wrap{padding-inline:16px}.hero h1{font-size:clamp(3.3rem,18vw,5.2rem)}.kpis,.research-grid,.truth-grid,.fit-grid{grid-template-columns:1fr}.section{padding-top:82px}.evidence-grid{margin-inline:-8px}.proof-image{height:430px}.site-footer{grid-template-columns:1fr}.source-note{text-align:left}.flow-step{font-size:7px}.section-head p:last-child{font-size:14px}.status-strip{display:block}.status-strip b{display:block;margin-bottom:7px}.partner-panel{margin-top:82px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.pulse,.ticker-track,.mini-curve path,.curve polyline{animation:none;stroke-dashoffset:0}.bar,[data-reveal]{transition:none}[data-reveal]{opacity:1;transform:none}}

/* AstroWind-derived presentation layer: centered marketing hero, stats strip,
   rounded bento cards, primary pill actions and a light/dark token system. */
:root{color-scheme:light;--canvas:#fff;--card:#fff;--head:#f8fafc;--line:#e5e7eb;--line-strong:#cbd5e1;--ink:#0f172a;--ink-2:#334155;--muted:#64748b;--faint:#94a3b8;--accent:#2563eb;--cyan:#2563eb;--violet:#7c3aed;--pink:#db2777;--night:#fff;--green:#059669;--red:#dc2626;--blue:#2563eb;--blue-ink:#1d4ed8;--blue-50:#eff6ff;--blue-100:#dbeafe;--green-50:#ecfdf5;--green-100:#d1fae5;--red-50:#fef2f2;--red-100:#fee2e2;--amber-50:#fffbeb;--amber-100:#fef3c7;--shadow:0 1px 2px rgba(15,23,42,.04),0 12px 30px rgba(15,23,42,.06)}
html.dark{color-scheme:dark;--canvas:#0f172a;--card:#111827;--head:#172033;--line:#293548;--line-strong:#475569;--ink:#f8fafc;--ink-2:#cbd5e1;--muted:#94a3b8;--faint:#64748b;--accent:#60a5fa;--cyan:#60a5fa;--violet:#a78bfa;--pink:#f472b6;--night:#0f172a;--green:#34d399;--red:#fb7185;--blue:#60a5fa;--blue-ink:#93c5fd;--blue-50:#172554;--blue-100:#1e3a8a;--green-50:#052e2b;--green-100:#064e3b;--red-50:#450a0a;--red-100:#7f1d1d;--amber-50:#422006;--amber-100:#713f12;--shadow:none}
html.dark{--canvas:#0d0d0c;--card:#171715;--head:#1d1c19;--line:#35332d;--line-strong:#514b3c;--ink:#f4f0e7;--ink-2:#d0c7b8;--muted:#9f9686;--faint:#70695e;--accent:#d7a84e;--cyan:#d7a84e;--violet:#c8954d;--pink:#e4b759;--night:#0d0d0c;--green:#72c98c;--red:#ec7d70;--blue:#d7a84e;--blue-ink:#f1ca7a;--blue-50:#272114;--blue-100:#46371d;--green-50:#142419;--green-100:#1c3825;--red-50:#321816;--red-100:#51231f;--amber-50:#302713;--amber-100:#4b3c1c}
body{background:var(--canvas);color:var(--ink);font-size:15px}body::before{background:radial-gradient(620px circle at var(--pointer-x,50%) var(--pointer-y,5%),rgba(37,99,235,.13),transparent 68%),radial-gradient(circle at 82% 20%,rgba(124,58,237,.06),transparent 22%);transition:background .45s ease-out}.dark body::before{background:radial-gradient(680px circle at var(--pointer-x,50%) var(--pointer-y,5%),rgba(215,168,78,.16),transparent 68%),radial-gradient(circle at 82% 20%,rgba(228,183,89,.07),transparent 24%)}
.site-nav{top:0;width:min(1240px,100%);padding:15px 24px;border:0;border-bottom:1px solid color-mix(in srgb,var(--line) 72%,transparent);border-radius:0;background:color-mix(in srgb,var(--canvas) 88%,transparent);box-shadow:none;backdrop-filter:blur(18px)}.brand-mark{background:var(--accent);color:white;box-shadow:none}.brand small{font-size:11px;font-weight:650;letter-spacing:0;color:var(--muted)}.nav-links a{color:var(--muted);font-size:14px}.nav-links a:hover{color:var(--accent);background:var(--blue-50)}.nav-actions{display:flex;align-items:center;gap:7px}.nav-cta{border-radius:999px;background:var(--accent);color:white;padding:10px 17px}.theme-toggle{display:grid;place-items:center;width:39px;height:39px;border:0;border-radius:10px;background:transparent;color:var(--muted);font-size:18px;cursor:pointer}.theme-toggle:hover{background:var(--blue-50);color:var(--accent)}
.landing-wrap{max-width:1240px;padding-inline:24px}.hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(360px,.8fr);align-items:center;gap:clamp(42px,7vw,94px);min-height:660px;padding:132px 0 76px;text-align:left}.hero>div[data-reveal]{max-width:710px;margin:0}.status{border-color:color-mix(in srgb,var(--accent) 30%,var(--line));background:var(--blue-50);color:var(--accent)}.pulse{background:var(--accent);box-shadow:none}.hero h1{max-width:11ch;margin:22px 0 18px;font-size:clamp(3rem,5.5vw,5.25rem);line-height:.98;letter-spacing:-.058em;color:var(--ink)}.hero h1 em{font-family:inherit;font-weight:800;color:var(--accent);background:none;-webkit-text-fill-color:currentColor}.hero-copy{max-width:610px;margin:0;font-size:clamp(1rem,1.7vw,1.14rem);color:var(--muted)}.hero-actions,.micro-proof{justify-content:flex-start}.button{border-radius:6px;border-color:var(--line-strong);color:var(--ink);padding:13px 19px}.button:hover{border-color:var(--accent);box-shadow:none}.button.primary{background:var(--accent);color:white;box-shadow:none}.hero-proof{overflow:hidden;border:1px solid var(--line);border-radius:10px;background:var(--card);box-shadow:0 28px 75px rgba(15,23,42,.14);transform:none;transition:border-color .3s,box-shadow .3s}.hero-proof:hover{transform:none;border-color:var(--accent);box-shadow:0 35px 85px rgba(15,23,42,.18)}.dark .hero-proof{border-color:#2d3a4e;background:#101722;box-shadow:0 28px 75px rgba(0,0,0,.32)}.proof-top{display:flex;align-items:center;gap:8px;padding:13px 15px;border-bottom:1px solid var(--line);font-size:10px;font-weight:750;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}.proof-top a{margin-left:auto;color:var(--accent);text-decoration:none;font-size:10px}.proof-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:none}.hero-proof>a{display:block;background:#fff}.hero-proof img{display:block;width:100%;height:auto}.proof-bottom{display:grid;gap:6px;padding:16px 17px;color:var(--muted);font-size:12px;line-height:1.55}.proof-bottom strong{color:var(--ink);font-size:13px}.ticker{display:none}.system-card{display:none}
.ticker{background:var(--head);border-color:var(--line)}.ticker-track{color:var(--muted)}.ticker-track b{color:var(--accent)}.section{padding-top:104px}.section-head{display:block;max-width:820px;margin:0 auto 42px;text-align:center}.section-kicker{color:var(--accent);font-size:12px}.section h2{font-size:clamp(2.3rem,5vw,4.2rem);color:var(--ink)}.section-head p:last-child{max-width:720px;margin:16px auto 0;color:var(--muted);font-size:18px}.status-strip{border-color:#fde68a;background:#fffbeb;color:#475569}.dark .status-strip{border-color:#713f12;background:#422006;color:#cbd5e1}.status-strip b{color:#b45309}.dark .status-strip b{color:#fbbf24}
.hero{min-height:100svh;padding:84px 0 40px}.section{padding-top:64px}
.kpis{gap:0;border-block:1px solid var(--line);margin:28px 0}.kpi{border:0;border-right:1px solid var(--line);border-radius:0;background:transparent;padding:25px;text-align:center}.kpi:last-child{border-right:0}.kpi::after{display:none}.kpi b{color:var(--accent);font-size:clamp(2rem,4vw,3.5rem)}.kpi span{color:var(--muted)}.chartwrap,.evidence-card,.truth-card,.fit-card,.research-card,.book,.risk-item{background:var(--card);border-color:var(--line);box-shadow:var(--shadow)}.chartwrap{border-radius:24px}.toggle,.filters{background:var(--head);border-color:var(--line)}.toggle button[aria-pressed=true],.filters button[aria-pressed=true]{background:var(--card);color:var(--accent);box-shadow:var(--shadow)}.data-table{border-color:var(--line);background:var(--card)}
.truth-grid,.research-grid,.fit-grid{gap:20px}.truth-card,.fit-card,.research-card{border-radius:24px;padding:26px}.truth-card small,.fit-card small,.research-card small{color:var(--accent)}.evidence-card{border-radius:24px}.browser-bar{background:var(--head);border-color:var(--line)}.risk-number{border-color:#fecaca;background:linear-gradient(145deg,#fff,#fff1f2);box-shadow:var(--shadow)}.risk-number.best{border-color:#a7f3d0;background:linear-gradient(145deg,#fff,#ecfdf5)}.dark .risk-number{border-color:#7f1d1d;background:linear-gradient(145deg,#111827,#2a111b)}.dark .risk-number.best{border-color:#065f46;background:linear-gradient(145deg,#111827,#092e2b)}.books{gap:22px}.book{background:var(--card);border-radius:24px}.partner-panel{border-color:color-mix(in srgb,var(--accent) 25%,var(--line));background:linear-gradient(135deg,var(--blue-50),color-mix(in srgb,var(--violet) 8%,var(--card)));box-shadow:var(--shadow)}.closing{background:var(--accent);border:0;color:white}.closing .section-kicker,.closing h2,.closing p{color:white}.closing .button.primary{background:white;color:#1d4ed8}.site-footer{color:var(--muted)}.source-note{color:var(--faint)}
@media(max-width:900px){.site-nav{padding-inline:17px}.nav-links{top:69px;background:var(--canvas);border-color:var(--line)}.nav-actions .nav-cta{display:none}.hero{grid-template-columns:1fr;gap:42px;min-height:auto;padding-top:120px;text-align:center}.hero>div[data-reveal]{margin:auto}.hero h1{margin-inline:auto;font-size:clamp(3rem,13vw,5rem)}.hero-copy{margin-inline:auto}.hero-actions,.micro-proof{justify-content:center}.hero-proof{width:min(560px,100%);margin:auto}.section-head{text-align:left;margin-inline:0}.section-head p:last-child{margin-inline:0}.kpis{grid-template-columns:1fr 1fr;border:1px solid var(--line);border-radius:20px;overflow:hidden}.kpi{border-bottom:1px solid var(--line)}.kpi:nth-child(2){border-right:0}.kpi:nth-last-child(-n+2){border-bottom:0}}
@media(max-width:600px){.landing-wrap{padding-inline:16px}.site-nav{max-width:100vw;padding-inline:16px}.brand{white-space:nowrap}.nav-actions{margin-left:auto;gap:2px;flex:0 0 auto}.theme-toggle{width:35px;height:35px}.hero{padding-top:112px}.hero h1{max-width:100%;font-size:clamp(2.55rem,13vw,3.75rem);line-height:.98;overflow-wrap:anywhere}.hero h1 .hero-break,.hero h1 em{display:block}.hero-copy{width:100%;font-size:1rem;line-height:1.65;overflow-wrap:anywhere}.hero-actions{flex-direction:column;align-items:stretch}.hero-actions .button{width:100%}.micro-proof{display:grid;grid-template-columns:1fr;justify-content:start;max-width:260px;margin:28px auto 0;text-align:left;gap:8px}.system-card{padding:16px;overflow:hidden}.window-bar span{font-size:9px}.flow{gap:3px}.flow-step:not(:last-child)::after{display:none}.terminal{font-size:10px;padding:13px 11px}.kpis{grid-template-columns:1fr}.kpi{border-right:0}.kpi:nth-last-child(-n+2){border-bottom:1px solid var(--line)}.kpi:last-child{border-bottom:0}.section{padding-top:76px}}
</style><script>(function(){try{if(localStorage.getItem('trading-book-theme')!=='light')document.documentElement.classList.add('dark')}catch(e){document.documentElement.classList.add('dark')}})()</script></head><body><div class="page-progress" aria-hidden="true"><span></span></div>
<nav class="site-nav" aria-label="Primary"><a class="brand" href="#top"><span class="brand-mark">↗</span><span>Trading Book</span></a><div class="nav-links" id="nav-links"><a href="#record">Record</a><a href="stocks/market-trend.html">Market trend</a><a href="#evidence">Evidence</a><a href="#risk">Risk</a><a href="#research">Research</a><a href="#partner">Partner</a></div><div class="nav-actions"><button class="theme-toggle" type="button" aria-label="Switch to dark theme" title="Change theme">◐</button><a class="nav-cta" href="#partner">Request diligence ↗</a><button class="nav-toggle" type="button" aria-controls="nav-links" aria-expanded="false" aria-label="Open navigation">☰</button></div></nav>
<main id="top"><div class="landing-wrap"><section class="hero"><canvas id="market-canvas" aria-hidden="true"></canvas><div data-reveal><span class="status"><i class="pulse"></i> personal capital · public record</span><h1>Agentic trading, <em>documented.</em></h1><p class="hero-copy">A public operating record for an India equity system: independently displayed realised P&amp;L, complete research notes, daily decisions, and risk limits. The evidence comes before the narrative.</p><div class="hero-actions"><a class="button primary" href="#record">Open performance record <span>↓</span></a><a class="button" href="#research">Read the research ↗</a></div><div class="micro-proof"><span>Broker evidence</span><span>Risk disclosed</span><span>Research separated from results</span></div></div>
<aside class="system-card" data-reveal><div class="window-bar"><i></i><i></i><i></i><span>system / decision-loop</span></div><div class="flow"><div class="flow-step active">SCAN</div><div class="flow-step active">GATE</div><div class="flow-step active">SIZE</div><div class="flow-step">EXEC</div><div class="flow-step">LEARN</div></div><div class="terminal"><div><code>equity.book</code><b class="ok">published</b></div><div><code>crypto.plan</code><b class="wait">waiting for setup</b></div><div><code>risk.engine</code><b class="ok">hard limits on</b></div><div><code>evidence</code><b class="ok">attached</b></div></div><svg class="mini-curve" viewBox="0 0 500 110" preserveAspectRatio="none" aria-label="decorative equity curve"><defs><linearGradient id="heroGradient"><stop stop-color="#22d3ee"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs><path d="M2 91 C34 88 52 75 78 80 S120 95 146 68 S190 42 221 58 S270 76 301 43 S350 19 381 38 S430 66 498 9"/></svg></aside></section></div>
<div class="ticker" aria-hidden="true"><div class="ticker-track"><span><b>01</b> scan completed candles</span><span><b>02</b> reject before ranking</span><span><b>03</b> size from the stop</span><span><b>04</b> protect at the venue</span><span><b>05</b> publish what happened</span><span><b>01</b> scan completed candles</span><span><b>02</b> reject before ranking</span><span><b>03</b> size from the stop</span><span><b>04</b> protect at the venue</span><span><b>05</b> publish what happened</span></div></div>
<div class="landing-wrap">
<section class="section" id="record" data-reveal><div class="section-head"><div><p class="section-kicker">01 / Personal account record</p><h2>The curve, including the crater.</h2></div><p>Six months of realised equity P&amp;L reconstructed from the owner’s fills, measured against &#8377;20 lakh of capital. May stays on the same scale as every winning month.</p></div><div class="status-strip"><b>Return basis</b><span>Every percentage below is simple monthly P&amp;L divided by a fixed &#8377;20,00,000 capital base. It is transparent and comparable across these months, but it is not cash-flow-adjusted TWRR or a client composite.</span></div><div class="kpis"><div class="kpi"><b>+@@RETURN@@%</b><span>six-month return · &#8377;@@TOTAL@@</span></div><div class="kpi" style="--glow:rgba(94,234,212,.24);border-color:rgba(94,234,212,.25)"><b style="color:var(--accent)">+@@BESTRETURN@@%</b><span>highest recorded month · @@BESTMONTH@@</span></div><div class="kpi" style="--glow:rgba(248,113,113,.16)"><b>−@@WORSTRETURN@@%</b><span>max monthly drawdown · @@WORSTMONTH@@</span></div><div class="kpi" style="--glow:rgba(167,139,250,.16)"><b class="count" data-to="@@TRADES@@">0</b><span>closed trades</span></div></div>
<div class="chartwrap" id="chart"><header><p class="chart-label">Monthly return on &#8377;20L capital · as of @@ASOF@@</p><div class="toggle" role="group" aria-label="Chart view"><button type="button" data-view="monthly" aria-pressed="true">monthly</button><button type="button" data-view="cumulative" aria-pressed="false">cumulative</button></div></header><div class="bars">@@BARS@@</div><svg class="curve" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Cumulative realised P and L"><polyline points="@@COORDS@@"/></svg><p class="readout" id="readout">Six months: +@@RETURN@@% on &#8377;20L, or &#8377;@@TOTAL@@ realised.</p></div><div class="data-table"><table><thead><tr><th>month</th><th>return on &#8377;20L</th><th>trades</th><th>win %</th><th>realised P&amp;L</th></tr></thead><tbody>@@ROWS@@</tbody></table></div><p class="note">Best month: <strong>@@BESTMONTH@@, +@@BESTRETURN@@%</strong> (+&#8377;@@BESTPNL@@). Worst month: <strong>@@WORSTMONTH@@, −@@WORSTRETURN@@%</strong> (−&#8377;@@WORSTPNL@@). The average win is &#8377;@@AVGWIN@@ against an average loss of &#8377;@@AVGLOSS@@; the overall win rate is @@WIN@@%. <a href="stocks/analysis/2026-09-29_six_months.html">Audit the full six months →</a></p></section>

<section class="section" id="evidence" data-reveal><div class="section-head"><div><p class="section-kicker">02 / Evidence hierarchy</p><h2>What is proven—and what is not.</h2></div><p>Trust comes from preserving the boundary between broker evidence, internal reconstruction and simulation. Each answers a different question.</p></div><div class="truth-grid"><article class="truth-card"><small>Broker verified</small><h3>Realised account P&amp;L</h3><p>The Zerodha page independently confirms the displayed account P&amp;L. It does <strong>not</strong> prove capital employed, percentage return, drawdown or strategy attribution.</p></article><article class="truth-card"><small>Internally reconciled</small><h3>159 closed trades</h3><p>The ledger supports trade-level analysis and the monthly curve. It remains owner-maintained until an independent performance verification is completed.</p></article><article class="truth-card"><small>Research only</small><h3>Backtests and scenarios</h3><p>Simulated results are labelled separately and include their capital, cost and rule assumptions. They are evidence about a model, not realised investor returns.</p></article></div><div class="evidence-grid" style="margin-top:18px"><article class="evidence-card"><div class="browser-bar"><i></i><i></i><i></i><span class="address">console.zerodha.com/verified/828da14b</span><a class="external" href="https://console.zerodha.com/verified/828da14b" target="_blank" rel="noopener">OPEN LIVE ↗</a></div><a class="zerodha-link" href="https://console.zerodha.com/verified/828da14b" target="_blank" rel="noopener" aria-label="Open the live Zerodha verified P and L page"><img class="zerodha-proof" src="assets/zerodha-verified-2026-09-30.png" width="3442" height="1402" alt="Zerodha verified P and L page for Divyansh Jain showing net realised P and L since 3 April 2026"></a><p class="evidence-caption">Click the screenshot to open the live public verification on Zerodha.</p></article><article class="evidence-card"><div class="browser-bar"><i></i><i></i><i></i><span class="address">Delta Exchange India · supplied statement</span><a class="external" href="assets/delta-april-may-2026.jpg" target="_blank">FULL SIZE ↗</a></div><img class="proof-image" id="delta-proof" src="assets/delta-april-may-2026.jpg" width="820" height="706" alt="Delta Exchange India statement for 1 April to 15 May 2026 showing initial equity, current equity and realised P and L"><p class="evidence-caption">A separate crypto account artifact. It is not included in the equity record above.</p></article></div><div class="status-strip"><b>Reconciliation note</b><span>The internal equity ledger is cut off at 29 September and totals &#8377;416,382; the Zerodha screenshot captured on 30 September shows &#8377;432,948.62. The &#8377;16,566.62 difference must be reconciled before an external performance presentation.</span></div></section>

<section class="section" id="risk" data-reveal><div class="section-head"><div><p class="section-kicker">03 / Range of outcomes</p><h2>Highlight the high. Keep the drawdown beside it.</h2></div><p>The strongest month and the maximum recorded monthly drawdown use the same &#8377;20 lakh denominator. Neither is hidden inside an aggregate rupee figure.</p></div><div class="risk-grid"><article class="risk-number best"><small>Highest recorded month · @@BESTMONTH@@</small><b>+@@BESTRETURN@@%</b><p>+&#8377;@@BESTPNL@@ realised on the &#8377;20 lakh capital base, with 23 closed trades and 56.5% winners.</p></article><article class="risk-number"><small>Maximum recorded monthly drawdown · @@WORSTMONTH@@</small><b>−@@WORSTRETURN@@%</b><p>Approximately 5% of the same capital base: −&#8377;@@WORSTPNL@@ over 61 closed trades, with 21.3% winners.</p></article><div class="risk-list"><article class="risk-item"><b>Monthly drawdown definition</b><span>−@@WORSTRETURN@@% is the largest realised calendar-month loss divided by &#8377;20 lakh. It is not an intramonth mark-to-market peak-to-trough calculation.</span></article><article class="risk-item"><b>Low hit rate by design</b><span>Only @@WIN@@% of closed trades won in this window. The system depends on the average winner materially exceeding the average loss.</span></article><article class="risk-item"><b>Short live window</b><span>Six months is one market regime. TWRR, benchmark comparison and independent attribution still remain before an investable performance presentation.</span></article></div></div></section>

<section class="section" id="research" data-reveal><div class="section-head"><div><p class="section-kicker">04 / Research log</p><h2>Ideas earn their place.</h2></div><p>Winning narratives are easy to manufacture after the chart moves. These reports preserve the rules, failures and counter-evidence that shaped the live systems.</p></div><div class="research-controls"><div class="filters" role="group" aria-label="Filter research"><button type="button" data-filter="all" aria-pressed="true">all</button><button type="button" data-filter="equity" aria-pressed="false">equity</button><button type="button" data-filter="crypto" aria-pressed="false">crypto</button></div></div><div class="research-grid"><a class="research-card" data-kind="equity" href="stocks/analysis/2026-09-29_six_months.html"><small>Equity · audit</small><h3>Six months, 159 closed trades</h3><p>The realised record, the bad month, and the risk/reward structure behind a low win rate.</p><span>Read analysis →</span></a><a class="research-card" data-kind="equity" href="stocks/analysis/2026-09-27_entry_selection.html"><small>Equity · selection</small><h3>Why 86 trades were skipped</h3><p>Which filters removed opportunity, and whether the best rejected trades were recoverable.</p><span>Read analysis →</span></a><a class="research-card" data-kind="equity" href="stocks/analysis/2026-09-29_industry_rs.html"><small>Equity · rejected idea</small><h3>Industry RS did not predict return</h3><p>A good story that failed the split-period and permutation checks.</p><span>Read analysis →</span></a><a class="research-card" data-kind="crypto" href="crypto/analysis/2026-09-28_exact_crypto.html"><small>Crypto · production</small><h3>Rebuilding the April strategy</h3><p>Exact fills, automatic selection, six-month replay, and the narrow live profile.</p><span>Read analysis →</span></a><a class="research-card" data-kind="crypto" href="crypto/analysis/2026-09-28_crypto_thresholds.html"><small>Crypto · backtest</small><h3>Thresholds that survived</h3><p>What transferred from the equity logic—and what failed when crypto behaved differently.</p><span>Read analysis →</span></a><a class="research-card" data-kind="crypto" href="crypto/analysis/2026-09-29_delta_pnl.html"><small>Crypto · evidence</small><h3>What the Delta record proves</h3><p>The strongest available evidence and the important claims it still cannot support.</p><span>Read analysis →</span></a></div></section>

<section class="section" id="books" data-reveal><div class="section-head"><div><p class="section-kicker">05 / Operating books</p><h2>Inspect the system day by day.</h2></div><p>Daily operational reports live separately from standing research. Each book keeps its own rules, schedules and evidence.</p></div><div class="books"><a class="book" href="stocks/" style="--book-accent:var(--cyan);--book-glow:rgba(34,211,238,.18)"><small>India equity</small><h3>Stocks ↗</h3><p>Scans, gates, setups, positions and retrospectives from the equity service.</p><b>@@SDAYS@@ sessions · newest @@SNEW@@ · @@SANA@@ analyses</b></a><a class="book" href="crypto/" style="--book-accent:var(--violet);--book-glow:rgba(167,139,250,.2)"><small>Perpetual futures · separate research</small><h3>Crypto ↗</h3><p>The automatic TIS lifecycle, daily book, execution record and research. Crypto is not part of the equity proposition.</p><b>@@CDAYS@@ day(s) · newest @@CNEW@@ · @@CANA@@ analyses</b></a></div></section>

<section class="partner-panel" id="partner" data-reveal><div class="section-head"><div><p class="section-kicker">06 / Diligence conversations</p><h2>Build the regulated wrapper around the evidence.</h2></div><p>The strategy is open for serious diligence and regulated-distribution conversations. It is <strong>not accepting deposits, pooled money or discretionary client mandates directly.</strong></p></div><div class="fit-grid"><article class="fit-card"><small>Best fit now</small><h3>SEBI-registered PMS partner</h3><p>Evaluate the rules, execution stack, account history and capacity assumptions for a compliant investment approach.</p><ul class="mini-list"><li>Trade-level ledger</li><li>Backtest assumptions</li><li>Production architecture</li></ul></article><article class="fit-card"><small>Prospective allocator</small><h3>Qualified diligence</h3><p>Review the record and register interest while the operating and verification structure is developed.</p><ul class="mini-list"><li>No funds accepted here</li><li>No assured-return claim</li><li>No investment recommendation</li></ul></article><article class="fit-card"><small>Research partner</small><h3>Verification and scale</h3><p>Help establish TWRR, benchmarking, independent attribution, execution controls and realistic capacity.</p><ul class="mini-list"><li>Audit methodology</li><li>Risk reporting</li><li>Operational controls</li></ul></article></div><div class="partner-actions"><a class="button primary" href="mailto:divyansh.jain.2015@gmail.com?subject=Morning%20Book%20diligence%20request&amp;body=I%20am%20interested%20as%20a%20PMS%20partner%2C%20prospective%20allocator%2C%20or%20research%20partner.%20Please%20share%20the%20appropriate%20diligence%20material.">Request the diligence pack ↗</a><a class="button" href="https://divyanshh.github.io/divyanshh/">About the builder</a></div><p class="partner-note">A request starts a conversation only. Any future investment service would be offered through the applicable registered entity, agreement, disclosures and eligibility process.</p></section>

<section class="closing" data-reveal><p class="section-kicker">The operating principle</p><h2>Evidence before capital.</h2><p>The goal is an investable, independently verifiable system. Until the regulated structure and performance presentation exist, this remains a public personal research record.</p><a class="button primary" href="latest.html">Open today’s operating book ↗</a></section>
<footer class="site-footer"><p><strong>Personal research record—not an offer, solicitation or investment advice.</strong> Past results do not predict future results. No funds are accepted through this site. Nothing here is a recommendation to buy or sell. Source: <a href="https://github.com/divyanshh/trading-book">divyanshh/trading-book</a>.</p><span class="source-note">Design system adapted from<br><a href="https://github.com/arthelokyo/astrowind">AstroWind</a> · <a href="licenses/ASTROWIND-LICENSE.md">MIT license</a></span></footer></div></main>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Delta statement preview"><button type="button" aria-label="Close preview">×</button><img src="assets/delta-april-may-2026.jpg" alt="Expanded Delta Exchange India statement"></div>
<script>(function(){
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,progress=document.querySelector('.page-progress span'),nav=document.querySelector('.site-nav');
function onScroll(){var range=Math.max(1,document.documentElement.scrollHeight-innerHeight);progress.style.transform='scaleX('+Math.min(1,scrollY/range)+')'}addEventListener('scroll',onScroll,{passive:true});onScroll();
if(!reduce)addEventListener('pointermove',function(e){document.documentElement.style.setProperty('--pointer-x',e.clientX+'px');document.documentElement.style.setProperty('--pointer-y',e.clientY+'px')},{passive:true});
var themeButton=document.querySelector('.theme-toggle');function syncTheme(){var dark=document.documentElement.classList.contains('dark');themeButton.textContent=dark?'☀':'◐';themeButton.setAttribute('aria-label',dark?'Switch to light theme':'Switch to dark theme')}syncTheme();themeButton.addEventListener('click',function(){document.documentElement.classList.toggle('dark');try{localStorage.setItem('trading-book-theme',document.documentElement.classList.contains('dark')?'dark':'light')}catch(e){}syncTheme()});
var toggle=document.querySelector('.nav-toggle');toggle.addEventListener('click',function(){var open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'×':'☰'});document.querySelectorAll('.nav-links a').forEach(function(a){a.addEventListener('click',function(){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.textContent='☰'})});
var reveal=function(){document.querySelectorAll('[data-reveal]').forEach(function(el){el.classList.add('visible')})};if('IntersectionObserver'in window&&!reduce){var observer=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('visible');observer.unobserve(e.target)}})},{threshold:.12});document.querySelectorAll('[data-reveal]').forEach(function(el){observer.observe(el)})}else{reveal()}
var chart=document.getElementById('chart'),out=document.getElementById('readout'),fmt=function(n){return(n<0?'-':'+')+'₹'+Math.abs(n).toLocaleString('en-IN')};requestAnimationFrame(function(){chart.classList.add('loaded')});document.querySelectorAll('.bar-slot').forEach(function(slot){var show=function(){out.textContent=slot.dataset.month+' — '+slot.dataset.return+'% on ₹20L ('+fmt(+slot.dataset.value)+'), '+slot.dataset.trades+' trades, '+slot.dataset.win+'% winners.'};slot.addEventListener('mouseenter',show);slot.addEventListener('focus',show)});document.querySelectorAll('.toggle button').forEach(function(btn){btn.addEventListener('click',function(){document.querySelectorAll('.toggle button').forEach(function(b){b.setAttribute('aria-pressed',String(b===btn))});chart.classList.toggle('showcurve',btn.dataset.view==='cumulative')})});
document.querySelectorAll('.count').forEach(function(el){var to=+el.dataset.to.replace(/,/g,''),pre=el.dataset.prefix||'';if(reduce){el.textContent=pre+to.toLocaleString('en-IN');return}var start=null;function step(ts){if(!start)start=ts;var k=Math.min(1,(ts-start)/950),ease=1-Math.pow(1-k,3);el.textContent=pre+Math.round(to*ease).toLocaleString('en-IN');if(k<1)requestAnimationFrame(step)}requestAnimationFrame(step)});
document.querySelectorAll('.filters button').forEach(function(btn){btn.addEventListener('click',function(){document.querySelectorAll('.filters button').forEach(function(b){b.setAttribute('aria-pressed',String(b===btn))});document.querySelectorAll('.research-card').forEach(function(card){card.hidden=btn.dataset.filter!=='all'&&card.dataset.kind!==btn.dataset.filter})})});
var box=document.querySelector('.lightbox'),proof=document.getElementById('delta-proof');function closeBox(){box.classList.remove('open');document.body.style.overflow=''}proof.addEventListener('click',function(){box.classList.add('open');document.body.style.overflow='hidden';box.querySelector('button').focus()});box.querySelector('button').addEventListener('click',closeBox);box.addEventListener('click',function(e){if(e.target===box)closeBox()});addEventListener('keydown',function(e){if(e.key==='Escape')closeBox()});
if(!reduce){var canvas=document.getElementById('market-canvas'),ctx=canvas.getContext('2d'),pts=[];function size(){var r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);canvas.width=r.width*d;canvas.height=r.height*d;ctx.setTransform(d,0,0,d,0,0);pts=Array.from({length:34},function(){return{x:Math.random()*r.width,y:Math.random()*r.height,vx:(Math.random()-.5)*.16,vy:(Math.random()-.5)*.16}})}function drawNet(){var w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);pts.forEach(function(p,i){p.x=(p.x+p.vx+w)%w;p.y=(p.y+p.vy+h)%h;for(var j=i+1;j<pts.length;j++){var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.hypot(dx,dy);if(d<145){ctx.strokeStyle='rgba(34,211,238,'+(1-d/145)*.11+')';ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke()}}ctx.fillStyle='rgba(167,139,250,.42)';ctx.beginPath();ctx.arc(p.x,p.y,1.2,0,Math.PI*2);ctx.fill()});requestAnimationFrame(drawNet)}size();addEventListener('resize',size,{passive:true});drawNet()}
})();</script></body></html>"""

HERO_PROOF = """<aside class="hero-proof" data-reveal><div class="proof-top"><span class="proof-dot"></span><span>Independent broker evidence</span><a href="https://console.zerodha.com/verified/828da14b" target="_blank" rel="noopener">Open live ↗</a></div><a href="https://console.zerodha.com/verified/828da14b" target="_blank" rel="noopener" aria-label="Open Zerodha's live verified P and L page"><img src="assets/zerodha-verified-2026-09-30.png" width="3442" height="1402" alt="Zerodha verified account P and L page"></a><div class="proof-bottom"><strong>Realised account P&amp;L, independently displayed.</strong><span>The broker page verifies the total shown; it does not establish capital employed, drawdown or strategy attribution.</span></div></aside>"""

SECTION = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Book — {book}</title>{style}</head><body><div class="wrap"><nav class="mb-nav" aria-label="Trading Book"><a href="../"><b aria-hidden="true">↗</b><span>Trading Book</span></a><button class="mb-theme" type="button" aria-label="Switch to dark theme" title="Change theme">◐</button></nav><script>(function(){{try{{if(localStorage.getItem('trading-book-theme')!=='light')document.documentElement.classList.add('dark')}}catch(e){{document.documentElement.classList.add('dark')}}if(!matchMedia('(prefers-reduced-motion: reduce)').matches)addEventListener('pointermove',function(e){{document.documentElement.style.setProperty('--pointer-x',e.clientX+'px');document.documentElement.style.setProperty('--pointer-y',e.clientY+'px')}},{{passive:true}});var b=document.querySelector('.mb-theme');if(!b)return;function s(){{var d=document.documentElement.classList.contains('dark');b.textContent=d?'☀':'◐';b.setAttribute('aria-label',d?'Switch to light theme':'Switch to dark theme')}}s();b.addEventListener('click',function(){{document.documentElement.classList.toggle('dark');try{{localStorage.setItem('trading-book-theme',document.documentElement.classList.contains('dark')?'dark':'light')}}catch(e){{}}s()}})}})();</script>
<p class="eyebrow">{eyebrow}</p><h1>{book}</h1>
<p class="stamp">{stamp}</p>
{body}
<footer>{footer} Source: <a href="https://github.com/divyanshh/trading-book">divyanshh/trading-book</a>.</footer>
</div></body></html>"""




def main() -> int:
    refresh = "--refresh" in sys.argv
    rows = fetch_index()
    for folder in (REPORTS, STOCKS, CRYPTO, CRYPTO_REPORTS):
        folder.mkdir(parents=True, exist_ok=True)
    fetched = 0
    for r in rows:
        target = REPORTS / f"{r['as_of']}.html"
        if target.exists() and not refresh:
            continue
        page = fetch(BASE + f"{r['as_of']}.html")
        if not re.match(r"<!doctype html>", page, re.I):
            print(f"skip {r['as_of']}: not html", file=sys.stderr)
            continue
        target.write_text(page, encoding="utf-8")
        fetched += 1
    # The stylesheet comes from the service, not from this directory. An
    # override is finished by hand under whatever theme was current when it was
    # written, and it is the archive that follows the renderer — which only
    # works if the theme is read from the renderer. See `newest_style`.
    style = newest_style(rows)
    for page in OVERRIDES.glob("20*.html"):
        (REPORTS / page.name).write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    for page in EXTRAS.glob("20*.html"):
        (REPORTS / page.name).write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    restyled = restyle(style) + restyle_analysis(style)
    redirects = write_redirects()
    build_site(rows, style or STYLE_FALLBACK)
    print(
        f"{len(rows)} equity reports indexed, {fetched} fetched, "
        f"{len(list(CRYPTO_REPORTS.glob('20*.html')))} crypto days, "
        f"{len(list(OVERRIDES.glob('20*.html')))} overridden, "
        f"{len(list(EXTRAS.glob('20*.html')))} extras, {restyled} restyled, "
        f"{redirects} redirects"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
