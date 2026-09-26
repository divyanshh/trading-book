#!/usr/bin/env python3
"""Mirror equity-service's stored daily reports into this repo, and index them.

Runs in GitHub Actions every evening after the 18:00 IST build (and on demand).
It reads the service's public report index (`/api/v1/reports/`), fetches every
day this repo does not yet hold, writes `reports/YYYY-MM-DD.html`, then
rebuilds `index.html` (by month, with each day's verdict) and `latest.html`
(a redirect to the newest). Idempotent: a day already present is never
re-fetched, so a rebuilt report replaces its file only if `--refresh` is given.

Needs nothing but the network: the service serves the reports publicly.
"""
from __future__ import annotations

import html
import json
import re
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
ANALYSIS = ROOT / "analysis"
"""Standing analyses — the six-month retrospective and its successors. Not a
day's page: they are written once, listed separately on the index, and
re-skinned with the rest whenever the renderer's theme moves. ``_bridge.css``
beside them maps their own class names onto that theme."""

EXTRAS = ROOT / "extras"
"""Standalone pages, `YYYY-MM-DD_<slug>.html`, published under reports/ and
linked from the index row of their day."""


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 — fixed https host
        return response.read().decode("utf-8")


def fetch_index() -> list[dict]:
    return json.loads(fetch(BASE))


def extras_for(day: str) -> str:
    links = []
    for page in sorted(EXTRAS.glob(f"{day}_*.html")):
        slug = page.stem[len(day) + 1 :].replace("_", " ")
        links.append(f'<a href="reports/{page.name}">{html.escape(slug)}</a>')
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
    """The standing analyses, on the same stylesheet plus their bridge."""
    bridge = ANALYSIS / "_bridge.css"
    if not style or not bridge.exists():
        return 0
    merged = style[: -len("</style>")] + bridge.read_text(encoding="utf-8") + "</style>"
    n = 0
    for page in ANALYSIS.glob("*.html"):
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


def analyses() -> list[tuple[str, str, int, str]]:
    """(file, title, bytes, revised) for every standing analysis, newest first.

    ``revised`` is empty unless the page changed after the day it is named for,
    which is the only case worth a reader's attention.
    """
    out = []
    for page in sorted(ANALYSIS.glob("*.html"), reverse=True):
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
    for page in [*REPORTS.glob("20*.html"), *OVERRIDES.glob("20*.html"), *EXTRAS.glob("20*.html")]:
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


def row_html(r: dict) -> str:
    """One day in the index. A day with no book yet is not a dead row."""
    if r.get("no_report"):
        day, target = r["as_of"], primary_page(r["as_of"])
        head = f'<a href="{target}">{day}</a>' if target else day
        return (
            f'<tr><td class="l">{head}{extras_for(r["as_of"])}</td>'
            '<td class="l warn"><span>no book yet</span></td>'
            '<td class="l">written before the 18:00 build</td>'
            f'<td>{r["bytes"] // 1024} KB</td></tr>'
        )
    gate = "fail" if "BLOCKED" in verdict(r["summary"]) else "pass"
    return (
        f'<tr><td class="l"><a href="reports/{r["as_of"]}.html">{r["as_of"]}</a>'
        f'{extras_for(r["as_of"])}</td>'
        f'<td class="l {gate}"><span>{html.escape(verdict(r["summary"]))}</span></td>'
        f'<td class="l">{html.escape(" · ".join((r["summary"] or "").splitlines()[1:3]))}</td>'
        f'<td>{r["bytes"] // 1024} KB</td></tr>'
    )


def build_index(rows: list[dict]) -> None:
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in (*rows, *days_with_only_extras(rows)):
        by_month[r["as_of"][:7]].append(r)
    parts = []
    for month in sorted(by_month, reverse=True):
        label = date.fromisoformat(by_month[month][0]["as_of"]).strftime("%B %Y")
        items = "".join(
            row_html(r)
            for r in sorted(by_month[month], key=lambda r: r["as_of"], reverse=True)
        )
        parts.append(f'<h2>{label}</h2><div class="scroll"><table><thead><tr><th class="l">day</th><th class="l">gate</th><th class="l">summary</th><th>size</th></tr></thead><tbody>{items}</tbody></table></div>')
    found = analyses()
    if found:
        items = "".join(
            f'<tr><td class="l"><a href="analysis/{name}">{html.escape(title)}</a></td>'
            f'<td class="l"><span class="badge">analysis</span></td>'
            f'<td class="l">{html.escape(name[:10])}</td>'
            f'<td class="l">{f"<b>revised {html.escape(revised)}</b>" if revised else ""}</td>'
            f'<td>{size // 1024} KB</td></tr>'
            for name, title, size, revised in found
        )
        parts.insert(
            0,
            '<h2>Analysis</h2><div class="scroll"><table><thead><tr>'
            '<th class="l">document</th><th class="l">kind</th><th class="l">as of</th>'
            '<th class="l">revised</th>'
            "<th>size</th></tr></thead><tbody>" + items + "</tbody></table></div>",
        )
    newest = rows[0]["as_of"] if rows else ""  # a real report, never an extras-only day
    page = TEMPLATE.format(style=newest_style(rows) or STYLE_FALLBACK, body="".join(parts), newest=newest, count=len(rows))
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    (ROOT / "latest.html").write_text(
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=reports/{newest}.html">'
        f'<title>Morning Book — latest</title><a href="reports/{newest}.html">{newest}</a>',
        encoding="utf-8",
    )
    (REPORTS / "index.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Book</title>{style}<style>.wrap{{max-width:1100px}}</style></head><body><div class="wrap">
<p class="eyebrow">equity-service · daily report archive</p><h1>Morning Book</h1>
<p class="stamp">{count} trading days, mirrored every evening at 19:00 IST. <a href="latest.html">Open the latest ({newest}) →</a></p>
{body}
<footer>Each page is the report as the service rendered it that evening; hand-written sections (IPO reviews) are added over it. Source: <a href="https://github.com/divyanshh/trading-book">divyanshh/trading-book</a>.</footer>
</div></body></html>"""


def main() -> int:
    refresh = "--refresh" in sys.argv
    rows = fetch_index()
    REPORTS.mkdir(exist_ok=True)
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
    build_index(rows)
    print(f"{len(rows)} reports indexed, {fetched} fetched, "
          f"{len(list(OVERRIDES.glob('20*.html')))} overridden, {len(list(EXTRAS.glob('20*.html')))} extras, {restyled} restyled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
