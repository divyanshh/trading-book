#!/usr/bin/env python3
"""Mirror equity-service's stored daily reports into this repo, and index them.

Runs in GitHub Actions every evening after the 18:00 IST build (and on demand).
It asks the dyno for the report index (`show_report --index`), fetches every
day this repo does not yet hold, writes `reports/YYYY-MM-DD.html`, then
rebuilds `index.html` (by month, with each day's verdict) and `latest.html`
(a redirect to the newest). Idempotent: a day already present is never
re-fetched, so a rebuilt report replaces its file only if `--refresh` is given.

Needs the Heroku CLI on PATH and HEROKU_API_KEY in the environment.
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

APP = "equity-service"
ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"


def dyno(*args: str) -> str:
    cmd = ["heroku", "run", "--no-tty", "--exit-code", "--app", APP, "--", "python", "manage.py", *args]
    if not os.environ.get("HEROKU_API_KEY"):
        sys.exit("HEROKU_API_KEY is not set — add it under Settings > Secrets and variables > Actions")
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        # heroku's own message (bad token, app not found, dyno failure) is on stderr;
        # without it the Actions log shows only a CalledProcessError.
        sys.exit(f"heroku run failed ({done.returncode}):\n{done.stderr.strip()[-2000:]}")
    out = done.stdout
    # `heroku run` prefixes its own progress lines; the payload starts at the doctype or the JSON.
    for marker in ("<!doctype html>", "<!DOCTYPE html>", "[", "{"):
        i = out.find(marker)
        if i >= 0:
            return out[i:]
    return out


def fetch_index() -> list[dict]:
    raw = dyno("show_report", "--index")
    return json.loads(raw[: raw.rfind("]") + 1])


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
            f'<tr><td class="l"><a href="reports/{r["as_of"]}.html">{r["as_of"]}</a></td>'
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
        page = dyno("show_report", "--date", r["as_of"])
        if not re.match(r"<!doctype html>", page, re.I):
            print(f"skip {r['as_of']}: not html", file=sys.stderr)
            continue
        target.write_text(page, encoding="utf-8")
        fetched += 1
    build_index(rows)
    print(f"{len(rows)} reports indexed, {fetched} fetched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
