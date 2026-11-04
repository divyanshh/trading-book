#!/usr/bin/env python3
"""Is the published page WRONG, as opposed to merely present?

    python3 review_site.py 2026-11-04

``verify_published.py`` answers a different question and answers it well: did
the bytes we committed reach the public URL. It cannot tell a correct page
from a confidently wrong one, because both arrive intact.

**Every check here is a bug that shipped.** On 4 November 2026 the book was
published four times carrying faults that 3,600 passing tests and a green
byte-for-byte verify all missed, because each one was a statement the page
made rather than a crash:

* A one-symbol probe wrote a ScanRun, so the SWING table read "1 scanned" and
  reported no setups. The owner read the page correctly — "tis swing is
  showing 0" — and the page was faithfully reporting a probe.
* The 52-week column printed the gate COUNT on both sides of the slash, so
  every row read "SWING 8/8": the one value meaning "cleared everything", on a
  section built to show names the scanner missed or refused.
* A section returned early when NSE had no file for the day, taking a chart
  that reads forty-five days of history with it. The chart was simply absent,
  with nothing saying so.
* Three audit pages went out in the renderer's raw stylesheet because they
  were not in the restyle globs, next to reports wearing the book's theme.

None of those is detectable by asking "did the file arrive". All four are
obvious to anyone who looks at the page, which is the point: this looks.

Exit 0 when every check passes. Non-zero with a reason otherwise, and the
reason names the incident so the next reader knows what it is protecting.
"""

from __future__ import annotations

import html
import json
import re
import ssl
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://divyanshh.github.io/trading-book"
API = "https://equity-service-fd1143ae8c7a.herokuapp.com/api/v1"

STRATEGIES = ("SWING", "WEEKLY", "STRIKE", "REVERSAL", "ETF", "ETF_WEEKLY")

MIN_UNIVERSE = {
    "SWING": 100,
    "WEEKLY": 100,
    "STRIKE": 100,
    "REVERSAL": 100,
    "ETF": 10,
    "ETF_WEEKLY": 10,
}
"""Below this, a strategy table is reporting a probe rather than a scan.

**Per strategy, because one number was wrong on the first run.** A flat
threshold of 100 failed ETF and ETF_WEEKLY, whose universe is 23 curated
funds — the check called a complete scan a probe. The equity scanners see
~880 names, so 100 is far above any probe; the ETF ones get 10, which is
still well above the one-symbol case this exists to catch."""

EXPECTED_SECTIONS = (
    "How the indices closed",
    "Institutional flows",
    "Sector breadth",
    "What is holding up",
    "At their 52-week highs",
)
"""Sections whose silent disappearance has cost a morning before.

"Where the money has been" is deliberately absent from this list: it lives
inside the index board and is checked separately, because it was the one that
vanished."""

CONSTANT_COLUMN_ROWS = 8
"""Rows a table needs before a constant column means anything.

Four was the first value and it fired on every short watch table on the page.
"""

MIN_SVGS = 20
"""A page that has lost its charts still reads like a page."""


@dataclass
class Finding:
    severity: str
    what: str
    detail: str


def _context() -> ssl.SSLContext | None:
    """certifi's roots where installed, the system's otherwise.

    The macOS python.org build ships no root certificates, so a plain default
    context fails on this host and succeeds in Actions — which would make this
    reviewer green in CI and broken on the desk. Same shape as `mirror.py`.
    """
    try:
        import certifi
    except ModuleNotFoundError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def fetch(url: str) -> str:
    """Read a URL, defeating the CDN cache.

    Pages serves a stale edge for a while after a build, and a reviewer that
    reads the previous version will either clear a page it never saw or fail
    one that is already fixed. Both waste the reader's trust."""
    import random

    sep = "&" if "?" in url else "?"
    request = urllib.request.Request(  # noqa: S310
        f"{url}{sep}cb={random.randint(1, 10**9)}",  # noqa: S311
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache", "User-Agent": "review-site"},
    )
    with urllib.request.urlopen(request, timeout=30, context=_context()) as response:  # noqa: S310
        return response.read().decode("utf-8", "replace")


def text_of(page: str) -> str:
    """The page as a reader sees it: no tags, collapsed whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(page)))


def check_scan_tables(flat: str) -> list[Finding]:
    """Every strategy table reports a scan, not a probe.

    The 4 November failure: `find_setups --symbol KDDL` wrote a ScanRun with a
    universe of one, the report showed the newest run per strategy, and two
    tables reported probes as the night's work."""
    out: list[Finding] = []
    for strategy in STRATEGIES:
        match = re.search(rf"{strategy} — ([\d,]+) scanned", flat)
        if match is None:
            out.append(
                Finding("warn", f"{strategy} table missing", "No '<strategy> — N scanned' line.")
            )
            continue
        scanned = int(match.group(1).replace(",", ""))
        if scanned < MIN_UNIVERSE.get(strategy, 100):
            out.append(
                Finding(
                    "fail",
                    f"{strategy} scanned only {scanned}",
                    "That is a one-symbol probe reported as the night's scan — the "
                    "4 November 'tis swing is showing 0' failure. Re-run the full "
                    "scan and rebuild.",
                )
            )
    return out


def check_no_column_is_constant(page: str) -> list[Finding]:
    """No table column shows the same non-empty value on every row.

    The 52-week census printed the gate count on both sides of the slash and
    read "SWING 8/8" on every row. A column that never varies is either a bug
    or a column nobody needs; both are worth a look."""
    out: list[Finding] = []
    for table in re.findall(r"<table.*?</table>", page, re.S):
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)
        body = [re.findall(r"<td[^>]*>(.*?)</td>", r, re.S) for r in rows]
        body = [[re.sub(r"<[^>]+>", "", c).strip() for c in cells] for cells in body if cells]
        if len(body) < CONSTANT_COLUMN_ROWS:
            continue
        width = min(len(cells) for cells in body)
        for column in range(width):
            values = {cells[column] for cells in body}
            only = next(iter(values))
            if len(values) == 1 and only and only not in {"—", "-", "0", ""}:
                out.append(
                    Finding(
                        # **Observation, not verdict.** A column CAN legitimately
                        # be constant — eight names all refused for the same
                        # reason is a real reading, and warning about it trained
                        # the first run to be ignored. Surfacing it and leaving
                        # the judgement to the reviewer is the division of labour
                        # this pair is built on.
                        "info",
                        f"a column is constant: every row reads {only!r}",
                        "The 52-week 'in scan' column read 'SWING 8/8' on every row "
                        "because the gate count was printed on both sides of the "
                        "slash. Check the cell builder.",
                    )
                )
    return out


def check_sections(flat: str) -> list[Finding]:
    out = [
        Finding("fail", f"section missing: {title}", "It has silently disappeared before.")
        for title in EXPECTED_SECTIONS
        if title not in flat
    ]
    if "Where the money has been" not in flat:
        out.append(
            Finding(
                "fail",
                "the month-and-week chart is gone",
                "The index board used to return early when NSE had no file for the "
                "day and take this chart with it, though it reads forty-five days of "
                "history and does not depend on today.",
            )
        )
    return out


def check_index_board(flat: str) -> list[Finding]:
    """The board reports a session, and says which one."""
    if "No index file" in flat:
        return [
            Finding(
                "fail",
                "the index board is empty",
                "It must show the last session that CLOSED, not the page's own date "
                '— "How the indices closed is always last day\'s data" (owner, '
                "2026-11-04). An empty board now means the archive was unreadable.",
            )
        ]
    if "indices closed higher" not in flat:
        return [Finding("warn", "the index board has no summary line", "Expected 'N of M'.")]
    return []


def check_charts(page: str) -> list[Finding]:
    count = page.count("<svg")
    if count < MIN_SVGS:
        return [
            Finding(
                "fail",
                f"only {count} charts on the page",
                "Sparklines come from screener.in, which returns HTTP 429 under load; "
                "a page that has lost its charts still reads like a page.",
            )
        ]
    return []


def check_audit_links(page: str, day: str) -> list[Finding]:
    """Every audit a row links to is published, themed, and carries a read."""
    out: list[Finding] = []
    linked = sorted(set(re.findall(r'href="\.\./audits/([A-Z0-9]+)\.html"', page)))
    for symbol in linked:
        try:
            audit = fetch(f"{SITE}/stocks/audits/{symbol}.html")
        except Exception as exc:  # noqa: BLE001
            out.append(
                Finding(
                    "fail",
                    f"{day}: the {symbol} row links to a page that does not load",
                    f"{exc}. A link to a page nobody wrote is worse than no link.",
                )
            )
            continue
        if "morning-book-shared-theme" not in audit:
            out.append(
                Finding(
                    "fail",
                    f"{symbol} audit is not wearing the book's theme",
                    "It is missing from the restyle globs in mirror.py, which is how "
                    "the first three audits went out in the renderer's raw colours.",
                )
            )
        if "The read" not in text_of(audit):
            out.append(
                Finding(
                    "warn",
                    f"{symbol} audit has no read section",
                    "A transcription of MarketSmith is not an analysis.",
                )
            )
    if linked:
        out.append(Finding("info", f"{len(linked)} audit link(s) checked", ", ".join(linked)))
    return out


def check_against_api(page: str, flat: str) -> list[Finding]:
    """The page's own numbers against what the service currently holds."""
    try:
        rows = json.loads(fetch(f"{API}/audits/"))
    except Exception as exc:  # noqa: BLE001
        return [Finding("warn", "could not read the audit index", str(exc))]
    # **Against the HTML, not the flattened text.** The first run compared
    # hrefs to a string with every tag stripped out, so it reported SBC and
    # KDDL as unlinked on a page that linked both — three lines above an INFO
    # saying it had just checked them.
    missing = [
        row["symbol"]
        for row in rows
        if f'audits/{row["symbol"]}.html' not in page and row["symbol"] in flat
    ]
    if missing:
        return [
            Finding(
                "warn",
                f"stored audits not linked from the page: {', '.join(missing)}",
                "The symbol appears on the page and an audit exists for it, but the "
                "row does not link to it.",
            )
        ]
    return []


def review(day: str) -> list[Finding]:
    page = fetch(f"{SITE}/stocks/reports/{day}.html")
    flat = text_of(page)
    findings: list[Finding] = []
    findings += check_scan_tables(flat)
    findings += check_sections(flat)
    findings += check_index_board(flat)
    findings += check_charts(page)
    findings += check_no_column_is_constant(page)
    findings += check_audit_links(page, day)
    findings += check_against_api(page, flat)
    findings.append(Finding("info", f"page is {len(page):,} bytes", f"{SITE}/stocks/reports/{day}.html"))
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    day = sys.argv[1]
    findings = review(day)
    rank = {"fail": 0, "warn": 1, "info": 2}
    for finding in sorted(findings, key=lambda f: rank.get(f.severity, 3)):
        print(f"[{finding.severity.upper():4}] {finding.what}")
        if finding.detail:
            print(f"        {finding.detail}")
    failures = sum(1 for f in findings if f.severity == "fail")
    warnings = sum(1 for f in findings if f.severity == "warn")
    print(f"\n{failures} failure(s), {warnings} warning(s) on {day}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
