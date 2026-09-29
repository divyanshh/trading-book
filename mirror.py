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
            f'data-trades="{trades}" data-win="{win}" tabindex="0" '
            f'aria-label="{name}: {value:+,} rupees over {trades} trades">'
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
        f"<tr><td>{n}</td><td>{tr}</td><td>{w:.1f}%</td>"
        f'<td class="{"good" if v >= 0 else "bad"}">{v:+,}</td></tr>'
        for n, v, tr, w in BOOK_MONTHS
    )

    return (
        LANDING.replace("@@STYLE@@", style)
        .replace("@@BARS@@", "".join(bars))
        .replace("@@COORDS@@", coords)
        .replace("@@CARDS@@", cards)
        .replace("@@ROWS@@", rows)
        .replace("@@TOTAL@@", f"{BOOK_TOTAL:,}")
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
<meta name="description" content="A systematic India equity and crypto trading book, published every session: the rules, the realised record, and the ideas that were tested and thrown away.">
<title>Morning Book — a trading system, in the open</title>@@STYLE@@<style>
.wrap{max-width:1100px}
.hero{padding:56px 0 34px;border-bottom:1px solid var(--line)}
.hero h1{font-size:clamp(2rem,5.5vw,3.4rem);line-height:1.08;margin:.2em 0 .3em;letter-spacing:-.02em}
.hero .tag{font-size:clamp(1rem,2.2vw,1.2rem);color:var(--ink-2);max-width:62ch;line-height:1.55}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:34px 0 8px}
.kpi{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:16px 18px}
.kpi b{display:block;font-size:clamp(1.3rem,3vw,1.9rem);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi span{display:block;font-size:12px;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.06em}
.chartwrap{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:20px;margin:26px 0}
.chartwrap header{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;justify-content:space-between;margin-bottom:6px}
.toggle{display:flex;gap:0;border:1px solid var(--line-strong);border-radius:8px;overflow:hidden}
.toggle button{background:transparent;border:0;color:var(--ink-2);font:inherit;font-size:12.5px;
  padding:6px 13px;cursor:pointer}
.toggle button[aria-pressed=true]{background:var(--line);color:var(--ink)}
.bars{display:flex;align-items:flex-end;gap:clamp(4px,1.6vw,16px);height:190px;margin-top:18px}
.bar-slot{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;
  height:100%;cursor:pointer;border-radius:6px;outline-offset:3px}
.bar-slot:hover,.bar-slot:focus-visible{background:rgba(255,255,255,.04)}
.bar{width:100%;max-width:64px;height:0;border-radius:5px 5px 0 0;transition:height .9s cubic-bezier(.2,.7,.2,1)}
.loaded .bar{height:var(--h)}
.bar.up{background:linear-gradient(180deg,var(--green),color-mix(in srgb,var(--green) 55%,transparent))}
.bar.down{background:linear-gradient(180deg,color-mix(in srgb,var(--red) 55%,transparent),var(--red))}
.bar-label{font-size:11.5px;color:var(--muted);margin-top:8px}
.readout{min-height:1.5em;font-size:13.5px;color:var(--ink-2);margin-top:14px;font-variant-numeric:tabular-nums}
.curve{width:100%;height:190px;margin-top:18px;display:none}
.curve polyline{fill:none;stroke:var(--green);stroke-width:2.2;vector-effect:non-scaling-stroke;
  stroke-dasharray:1000;stroke-dashoffset:1000;animation:draw 1.5s .2s cubic-bezier(.3,.7,.3,1) forwards}
@keyframes draw{to{stroke-dashoffset:0}}
.showcurve .bars{display:none}.showcurve .curve{display:block}
.dis{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:16px 18px}
.dis h3{margin:0 0 6px;font-size:15px}
.dis p{margin:0;color:var(--ink-2);font-size:13.5px;line-height:1.6}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:18px 0}
.books{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:18px 0}
.book{display:block;border:1px solid var(--line);background:var(--card);border-radius:12px;
  padding:22px;text-decoration:none;transition:border-color .18s,transform .18s}
.book:hover{border-color:var(--accent);transform:translateY(-2px)}
.book h3{margin:0 0 4px}.book p{margin:0;color:var(--muted);font-size:13px}
.cta{border:1px solid var(--line-strong);background:var(--card);border-radius:12px;
  padding:26px;margin:30px 0;text-align:center}
.cta a.btn{display:inline-block;margin-top:12px;padding:11px 22px;border-radius:8px;
  background:var(--accent);color:var(--canvas);font-weight:650;text-decoration:none}
@media (prefers-reduced-motion:reduce){.bar{transition:none}.curve polyline{animation:none;stroke-dashoffset:0}}
</style></head><body><div class="wrap">

<section class="hero">
<p class="eyebrow">systematic india equity &middot; crypto perpetuals &middot; published every session</p>
<h1>A trading system, kept in the open.</h1>
<p class="tag">Every session this book publishes what the scanner found, what was bought and
sold, and what the rules refused &mdash; along with the research that killed ideas we liked.
The losing months are on the same page as the winning ones.</p>

<div class="kpis">
  <div class="kpi"><b class="count" data-to="@@TOTAL@@" data-prefix="&#8377;">&#8377;0</b><span>realised, 6 months</span></div>
  <div class="kpi"><b class="count" data-to="@@TRADES@@">0</b><span>closed trades</span></div>
  <div class="kpi"><b>@@WIN@@%</b><span>win rate</span></div>
  <div class="kpi"><b>@@GL@@&times;</b><span>gain / loss</span></div>
</div>
<p class="note">Realised only, real money, as of @@ASOF@@. Two of three trades lose money &mdash;
the average win is &#8377;@@AVGWIN@@ against an average loss of &#8377;@@AVGLOSS@@, which is what
makes a 32% hit rate work.</p>
</section>

<h2>The record</h2>
<div class="chartwrap" id="chart">
  <header>
    <p class="stamp" style="margin:0">Realised P&amp;L by month &middot; hover or tab a bar</p>
    <div class="toggle" role="group" aria-label="chart view">
      <button type="button" data-view="monthly" aria-pressed="true">monthly</button>
      <button type="button" data-view="cumulative" aria-pressed="false">cumulative</button>
    </div>
  </header>
  <div class="bars">@@BARS@@</div>
  <svg class="curve" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="cumulative realised P and L">
    <polyline points="@@COORDS@@"/>
  </svg>
  <p class="readout" id="readout">Six months, 159 closed trades, &#8377;@@TOTAL@@ realised.</p>
</div>

<table>
<thead><tr><th>month</th><th>trades</th><th>win %</th><th>realised</th></tr></thead>
<tbody>@@ROWS@@</tbody>
</table>
<p class="note">May was the worst month and the most useful one: the loss analysis that followed
produced the two hard rules the system still runs under. Trade count fell from 61 in May to 11
in August &mdash; that is the gates refusing, which is most of what they do.
<a href="stocks/analysis/2026-09-29_six_months.html">The full six months &rarr;</a></p>

<h2>What we tested and threw away</h2>
<p class="tag" style="max-width:70ch">The interesting part of a system is what it refuses to
believe. Each of these was an idea we wanted to be true, measured properly &mdash; disjoint
samples, both halves of the window, a permutation test &mdash; and dropped.</p>
<div class="grid3">@@CARDS@@</div>

<h2>The books</h2>
<div class="books">
  <a class="book" href="stocks/"><h3>Equity &rarr;</h3>
     <p>@@SDAYS@@ sessions, newest @@SNEW@@ &middot; @@SANA@@ standing analyses</p></a>
  <a class="book" href="crypto/"><h3>Crypto &rarr;</h3>
     <p>@@CDAYS@@ day(s), newest @@CNEW@@ &middot; @@CANA@@ standing analyses</p></a>
</div>

<h2>Evidence</h2>
<p>The equity figures above are our own bookkeeping, reconstructed from fills &mdash; and that
reconstruction has been wrong before. The broker's own statement is the one number independent
of it: <a href="stocks/analysis/2026-09-29_verified_pnl.html">verified P&amp;L &rarr;</a>.
Crypto is evidenced far more weakly and
<a href="crypto/analysis/2026-09-29_delta_pnl.html">says so on its own page</a>.</p>

<div class="cta">
<h2 style="margin-top:0">Interested?</h2>
<p class="tag" style="margin:0 auto">If you build systematic strategies, trade one, or just
want to argue about a gate that should be dropped &mdash; get in touch.</p>
<a class="btn" href="https://divyanshh.github.io/divyanshh/">Contact &rarr;</a>
</div>

<footer>
<strong>Not investment advice, and not an offer of any service.</strong> This is a personal
research log of one person's own trading account, published because writing it down honestly
is how it gets better. Past results do not predict future results; most of these months are one
market. Nothing here is a recommendation to buy or sell anything.
Source: <a href="https://github.com/divyanshh/trading-book">divyanshh/trading-book</a>.
</footer>
</div>
<script>
(function(){
  var chart=document.getElementById('chart'), out=document.getElementById('readout');
  var fmt=function(n){return (n<0?'-':'+')+'₹'+Math.abs(n).toLocaleString('en-IN');};
  requestAnimationFrame(function(){chart.classList.add('loaded');});

  document.querySelectorAll('.bar-slot').forEach(function(slot){
    var show=function(){
      out.textContent=slot.dataset.month+' — '+fmt(+slot.dataset.value)+
        ' over '+slot.dataset.trades+' trades, '+slot.dataset.win+'% of them winners.';
    };
    slot.addEventListener('mouseenter',show); slot.addEventListener('focus',show);
  });

  document.querySelectorAll('.toggle button').forEach(function(btn){
    btn.addEventListener('click',function(){
      document.querySelectorAll('.toggle button').forEach(function(b){
        b.setAttribute('aria-pressed', String(b===btn));
      });
      chart.classList.toggle('showcurve', btn.dataset.view==='cumulative');
    });
  });

  // Count up, but only once and only if the visitor has not asked for less motion.
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.count').forEach(function(el){
    var to=+el.dataset.to.replace(/,/g,''), pre=el.dataset.prefix||'';
    if(reduce){el.textContent=pre+to.toLocaleString('en-IN');return;}
    var t0=null, dur=900;
    function step(ts){
      if(!t0)t0=ts;
      var k=Math.min(1,(ts-t0)/dur), eased=1-Math.pow(1-k,3);
      el.textContent=pre+Math.round(to*eased).toLocaleString('en-IN');
      if(k<1)requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
})();
</script>
</body></html>"""

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
