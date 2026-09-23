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
        parts.append(f"<h2>{label}</h2><div class=\"scroll\"><table><thead><tr><th class=\"l\">day</th><th class=\"l\">gate</th><th class=\"l\">summary</th><th>size</th></tr></thead><tbody>{items}</tbody></table></div>")
    newest = rows[0]["as_of"] if rows else ""
    page = TEMPLATE.format(body="".join(parts), newest=newest, count=len(rows))
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    (ROOT / "latest.html").write_text(
        f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=reports/{newest}.html">'
        f'<title>Morning Book — latest</title><a href="reports/{newest}.html">{newest}</a>',
        encoding="utf-8",
    )
    (REPORTS / "index.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


TEMPLATE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Book</title><style>
:root{{--bg:#faf8f5;--ink:#1c1b19;--muted:#6b6862;--line:#e6e2db;--pass-bg:#e3f4e8;--fail-bg:#fbe3e0}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Inter,sans-serif}}
.wrap{{max-width:900px;margin:0 auto;padding:36px 20px 80px}}h1{{font-size:28px;margin:0 0 4px}}h2{{font-size:19px;margin:34px 0 10px}}
.sub{{color:var(--muted);margin:0 0 18px}}table{{border-collapse:collapse;width:100%}}th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
th.l,td.l{{text-align:left}}td.l span{{padding:2px 8px;border-radius:100px;font-size:12.5px;font-weight:600}}td.pass span{{background:var(--pass-bg)}}td.fail span{{background:var(--fail-bg)}}
a{{color:inherit}}.scroll{{overflow-x:auto}}
</style></head><body><div class="wrap">
<h1>Morning Book</h1><p class="sub">equity-service daily report, mirrored every evening. {count} days. <a href="latest.html">Open the latest ({newest})</a>.</p>
{body}
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
    for page in OVERRIDES.glob("20*.html"):
        (REPORTS / page.name).write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    for page in EXTRAS.glob("20*.html"):
        (REPORTS / page.name).write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    build_index(rows)
    print(f"{len(rows)} reports indexed, {fetched} fetched, "
          f"{len(list(OVERRIDES.glob('20*.html')))} overridden, {len(list(EXTRAS.glob('20*.html')))} extras")
    return 0


if __name__ == "__main__":
    sys.exit(main())
