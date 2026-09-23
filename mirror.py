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
    """The `<style>` block of the newest report — the one stylesheet every page gets."""
    for r in rows:
        page = REPORTS / f"{r['as_of']}.html"
        if page.exists():
            m = STYLE.search(page.read_text(encoding="utf-8"))
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


def analyses() -> list[tuple[str, str, int]]:
    """(file, title, bytes) for every standing analysis, newest first."""
    out = []
    for page in sorted(ANALYSIS.glob("*.html"), reverse=True):
        text = page.read_text(encoding="utf-8")
        found = re.search(r"<title>(.*?)</title>", text, re.S)
        out.append((page.name, html.unescape(found.group(1)).strip() if found else page.stem,
                    len(text)))
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


def build_index(rows: list[dict]) -> None:
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_month[r["as_of"][:7]].append(r)
    parts = []
    for month in sorted(by_month, reverse=True):
        label = date.fromisoformat(by_month[month][0]["as_of"]).strftime("%B %Y")
        items = "".join(
            f'<tr><td class="l"><a href="reports/{r["as_of"]}.html">{r["as_of"]}</a>{extras_for(r["as_of"])}</td>'
            f'<td class="l {"fail" if "BLOCKED" in verdict(r["summary"]) else "pass"}"><span>{html.escape(verdict(r["summary"]))}</span></td>'
            f'<td class="l">{html.escape(" · ".join((r["summary"] or "").splitlines()[1:3]))}</td>'
            f'<td>{r["bytes"]//1024} KB</td></tr>'
            for r in sorted(by_month[month], key=lambda r: r["as_of"], reverse=True)
        )
        parts.append(f'<h2>{label}</h2><div class="scroll"><table><thead><tr><th class="l">day</th><th class="l">gate</th><th class="l">summary</th><th>size</th></tr></thead><tbody>{items}</tbody></table></div>')
    found = analyses()
    if found:
        items = "".join(
            f'<tr><td class="l"><a href="analysis/{name}">{html.escape(title)}</a></td>'
            f'<td class="l"><span class="badge">analysis</span></td>'
            f'<td class="l">{html.escape(name[:10])}</td><td>{size // 1024} KB</td></tr>'
            for name, title, size in found
        )
        parts.insert(
            0,
            '<h2>Analysis</h2><div class="scroll"><table><thead><tr>'
            '<th class="l">document</th><th class="l">kind</th><th class="l">as of</th>'
            "<th>size</th></tr></thead><tbody>" + items + "</tbody></table></div>",
        )
    newest = rows[0]["as_of"] if rows else ""
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
    # The stylesheet is read from the dyno's newest page *before* overrides are
    # laid over it — an override is finished by hand under whatever theme was
    # current when it was written, and it is the archive that follows the
    # renderer, not the other way round.
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
