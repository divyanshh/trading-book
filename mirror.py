#!/usr/bin/env python3
"""Mirror the stored daily reports into this repo, and index them.

Runs in GitHub Actions every evening after the 18:00 IST build (and on demand).
It reads equity-service's public report index (`/api/v1/reports/`), fetches
every day this repo does not yet hold, writes `reports/YYYY-MM-DD.html`, then
rebuilds the site. Idempotent: a day already present is never re-fetched, so a
rebuilt report replaces its file only if `--refresh` is given.

**Two books, three levels** (2026-09-29). The site used to be one index over
one book. It is now a hub with a section per book, because the crypto book
arrived and interleaving two unrelated instruments in one date-ordered table
made both harder to read:

    /                     the hub — stocks and crypto
    /stocks/              equity: analyses, then daily reports by month
    /crypto/              crypto: analyses, then daily reports by month

The **equity daily reports stay at `/reports/`** and the paths are not
rewritten. They are the URLs that have been shared, and a personal archive
that breaks its own links to look tidier has made itself worse. The section
pages link to them where they are; only the analyses moved, and those keep
working through the stubs in :func:`write_redirects`.

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
REPORTS = ROOT / "reports"
OVERRIDES = ROOT / "overrides"
"""Hand-finished pages, `YYYY-MM-DD.html`. A day here is published in place of
the dyno's copy — the dyno renders the scan, but analysis written by hand
(the 23 Sep IPO review, for one) lives only in the file, and a refresh run
silently threw it away once. Anything under here wins, always."""
STOCKS = ROOT / "stocks"
CRYPTO = ROOT / "crypto"
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
    if not style:
        return 0
    n = 0
    for folder in (ANALYSIS, CRYPTO_ANALYSIS):
        bridge = folder / "_bridge.css"
        if not bridge.exists():
            continue
        merged = style[: -len("</style>")] + bridge.read_text(encoding="utf-8") + "</style>"
        for page in folder.glob("*.html"):
            text = page.read_text(encoding="utf-8")
            if STYLE.search(text) and merged not in text:
                page.write_text(STYLE.sub(lambda _m: merged, text, count=1), encoding="utf-8")
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
    if not style:
        return 0
    n = 0
    for page in [
        *REPORTS.glob("20*.html"),
        *OVERRIDES.glob("20*.html"),
        *EXTRAS.glob("20*.html"),
        *CRYPTO_REPORTS.glob("20*.html"),
    ]:
        text = page.read_text(encoding="utf-8")
        if STYLE.search(text) and style not in text:
            page.write_text(STYLE.sub(lambda _m: style, text, count=1), encoding="utf-8")
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


def row_html(r: dict, *, prefix: str = "reports") -> str:
    """One day in a section index. A day with no book yet is not a dead row."""
    if r.get("no_report"):
        day, target = r["as_of"], primary_page(r["as_of"])
        head = f'<a href="../{target}">{day}</a>' if target else day
        return (
            f'<tr><td class="l">{head}{extras_for(r["as_of"], base="../reports")}</td>'
            '<td class="l warn"><span>no book yet</span></td>'
            '<td class="l">written before the 18:00 build</td>'
            f'<td>{r["bytes"] // 1024} KB</td></tr>'
        )
    gate = "fail" if "BLOCKED" in verdict(r["summary"]) else "pass"
    extras = extras_for(r["as_of"], base="../reports") if prefix == "../reports" else ""
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
            row_html(r, prefix=prefix)
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


def write_redirects() -> int:
    """Keep the pre-2026-09-29 analysis URLs working.

    The analyses moved into `stocks/` and `crypto/`; the links to them did not.
    A one-line meta-refresh at each old path costs nothing and means a shared
    URL from last week still lands on the page it named.
    """
    moved = {p.name: "stocks" for p in ANALYSIS.glob("*.html")}
    moved.update({p.name: "crypto" for p in CRYPTO_ANALYSIS.glob("*.html")})
    if not moved:
        return 0
    old = ROOT / "analysis"
    old.mkdir(exist_ok=True)
    for name, book in moved.items():
        target = f"../{book}/analysis/{name}"
        (old / name).write_text(
            f'<!doctype html><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<title>Moved</title><a href="{target}">This analysis moved to {book}/analysis/</a>',
            encoding="utf-8",
        )
    return len(moved)


def build_site(rows: list[dict], style: str) -> None:
    """The hub and the two section pages."""
    crypto = crypto_rows()
    newest = rows[0]["as_of"] if rows else ""
    newest_crypto = crypto[0]["as_of"] if crypto else ""

    (STOCKS / "index.html").write_text(
        SECTION.format(
            style=style,
            book="Stocks",
            eyebrow="equity-service · nse · daily report archive",
            stamp=(
                f"{len(rows)} trading days, mirrored every evening at 19:00 IST."
                + (f' <a href="../reports/{newest}.html">Open the latest ({newest}) →</a>' if newest else "")
            ),
            body=analysis_html(ANALYSIS)
            + "".join(months_html(rows, prefix="../reports", with_extras=True)),
            footer=(
                "Each page is the report as equity-service rendered it that evening; "
                "hand-written sections (IPO reviews) are added over it."
            ),
        ),
        encoding="utf-8",
    )

    (CRYPTO / "index.html").write_text(
        SECTION.format(
            style=style,
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
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=reports/{newest}.html">'
        f'<title>Morning Book — latest</title><a href="reports/{newest}.html">{newest}</a>',
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

    return (
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


LANDING = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A systematic India equity and crypto trading book: live rules, realised evidence, and every rejected idea.">
<meta name="theme-color" content="#050814"><title>Morning Book — rules, results, receipts</title>@@STYLE@@<style>
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
</style></head><body><div class="page-progress" aria-hidden="true"><span></span></div>
<nav class="site-nav" aria-label="Primary"><a class="brand" href="#top"><span class="brand-mark">↗</span><span>Morning Book</span></a><div class="nav-links" id="nav-links"><a href="#record">Record</a><a href="#evidence">Evidence</a><a href="#risk">Risk</a><a href="#research">Research</a><a href="#partner">Partner</a></div><a class="nav-cta" href="#partner">Request diligence ↗</a><button class="nav-toggle" type="button" aria-controls="nav-links" aria-expanded="false" aria-label="Open navigation">☰</button></nav>
<main id="top"><div class="landing-wrap"><section class="hero"><canvas id="market-canvas" aria-hidden="true"></canvas><div data-reveal><span class="status"><i class="pulse"></i> personal capital · system live</span><h1>The rule before <em>the result.</em></h1><p class="hero-copy">A systematic Indian equity strategy developed in a real-money account. The fills, losing months, rejected ideas and production rules are published for serious diligence—not reduced to a victory screenshot.</p><div class="hero-actions"><a class="button primary" href="#record">Review the record <span>↓</span></a><a class="button" href="#partner">Request the diligence pack ↗</a></div><div class="micro-proof"><span>Broker evidence</span><span>Backtests separated</span><span>Risk disclosed</span></div></div>
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
<footer class="site-footer"><p><strong>Personal research record—not an offer, solicitation or investment advice.</strong> Past results do not predict future results. No funds are accepted through this site. Nothing here is a recommendation to buy or sell. Source: <a href="https://github.com/divyanshh/trading-book">divyanshh/trading-book</a>.</p><span class="source-note">Interaction patterns inspired by<br><a href="https://github.com/ali-abassi/aster-landing-page-template">Aster · MIT</a></span></footer></div></main>
<div class="lightbox" role="dialog" aria-modal="true" aria-label="Delta statement preview"><button type="button" aria-label="Close preview">×</button><img src="assets/delta-april-may-2026.jpg" alt="Expanded Delta Exchange India statement"></div>
<script>(function(){
var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,progress=document.querySelector('.page-progress span'),nav=document.querySelector('.site-nav');
function onScroll(){var range=Math.max(1,document.documentElement.scrollHeight-innerHeight);progress.style.transform='scaleX('+Math.min(1,scrollY/range)+')'}addEventListener('scroll',onScroll,{passive:true});onScroll();
var toggle=document.querySelector('.nav-toggle');toggle.addEventListener('click',function(){var open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'×':'☰'});document.querySelectorAll('.nav-links a').forEach(function(a){a.addEventListener('click',function(){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.textContent='☰'})});
var reveal=function(){document.querySelectorAll('[data-reveal]').forEach(function(el){el.classList.add('visible')})};if('IntersectionObserver'in window&&!reduce){var observer=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('visible');observer.unobserve(e.target)}})},{threshold:.12});document.querySelectorAll('[data-reveal]').forEach(function(el){observer.observe(el)})}else{reveal()}
var chart=document.getElementById('chart'),out=document.getElementById('readout'),fmt=function(n){return(n<0?'-':'+')+'₹'+Math.abs(n).toLocaleString('en-IN')};requestAnimationFrame(function(){chart.classList.add('loaded')});document.querySelectorAll('.bar-slot').forEach(function(slot){var show=function(){out.textContent=slot.dataset.month+' — '+slot.dataset.return+'% on ₹20L ('+fmt(+slot.dataset.value)+'), '+slot.dataset.trades+' trades, '+slot.dataset.win+'% winners.'};slot.addEventListener('mouseenter',show);slot.addEventListener('focus',show)});document.querySelectorAll('.toggle button').forEach(function(btn){btn.addEventListener('click',function(){document.querySelectorAll('.toggle button').forEach(function(b){b.setAttribute('aria-pressed',String(b===btn))});chart.classList.toggle('showcurve',btn.dataset.view==='cumulative')})});
document.querySelectorAll('.count').forEach(function(el){var to=+el.dataset.to.replace(/,/g,''),pre=el.dataset.prefix||'';if(reduce){el.textContent=pre+to.toLocaleString('en-IN');return}var start=null;function step(ts){if(!start)start=ts;var k=Math.min(1,(ts-start)/950),ease=1-Math.pow(1-k,3);el.textContent=pre+Math.round(to*ease).toLocaleString('en-IN');if(k<1)requestAnimationFrame(step)}requestAnimationFrame(step)});
document.querySelectorAll('.filters button').forEach(function(btn){btn.addEventListener('click',function(){document.querySelectorAll('.filters button').forEach(function(b){b.setAttribute('aria-pressed',String(b===btn))});document.querySelectorAll('.research-card').forEach(function(card){card.hidden=btn.dataset.filter!=='all'&&card.dataset.kind!==btn.dataset.filter})})});
var box=document.querySelector('.lightbox'),proof=document.getElementById('delta-proof');function closeBox(){box.classList.remove('open');document.body.style.overflow=''}proof.addEventListener('click',function(){box.classList.add('open');document.body.style.overflow='hidden';box.querySelector('button').focus()});box.querySelector('button').addEventListener('click',closeBox);box.addEventListener('click',function(e){if(e.target===box)closeBox()});addEventListener('keydown',function(e){if(e.key==='Escape')closeBox()});
if(!reduce){var canvas=document.getElementById('market-canvas'),ctx=canvas.getContext('2d'),pts=[];function size(){var r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);canvas.width=r.width*d;canvas.height=r.height*d;ctx.setTransform(d,0,0,d,0,0);pts=Array.from({length:34},function(){return{x:Math.random()*r.width,y:Math.random()*r.height,vx:(Math.random()-.5)*.16,vy:(Math.random()-.5)*.16}})}function drawNet(){var w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);pts.forEach(function(p,i){p.x=(p.x+p.vx+w)%w;p.y=(p.y+p.vy+h)%h;for(var j=i+1;j<pts.length;j++){var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,d=Math.hypot(dx,dy);if(d<145){ctx.strokeStyle='rgba(34,211,238,'+(1-d/145)*.11+')';ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke()}}ctx.fillStyle='rgba(167,139,250,.42)';ctx.beginPath();ctx.arc(p.x,p.y,1.2,0,Math.PI*2);ctx.fill()});requestAnimationFrame(drawNet)}size();addEventListener('resize',size,{passive:true});drawNet()}
})();</script></body></html>"""

SECTION = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Book — {book}</title>{style}<style>.wrap{{max-width:1100px}}
.back{{display:inline-block;margin:0 0 14px;font-size:12.5px;font-weight:600;text-decoration:none}}</style></head><body><div class="wrap">
<a class="back" href="../">&larr; Morning Book</a>
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
