#!/usr/bin/env python3
"""Refresh the hub's two book counters without regenerating the hub.

`mirror.py` rebuilds `index.html` from its own template, which destroys the
interactive benchmark chart the owner maintains there by hand. It has done so
four times: the page is 74,474 bytes after his crosshair fix, 75,163 after the
1 and 2 October mirror runs, back to 74,474 after `db817ac Preserve interactive
benchmark across mirrors`, then 77,656 after a run on 5 October.

So the workflow restores `index.html` after mirroring, and this re-stamps the
only part of it that goes stale — the counters under each book:

    <b>13 sessions · newest 2026-10-05 · 16 analyses</b>
    <b>3 day(s) · newest 2026-10-01 · 3 analyses</b>

Counts come from the directories mirror.py has just refreshed, so they stay
truthful without the page being rebuilt. If either line stops matching, this
exits non-zero rather than writing a page with a wrong number on it: a stale
counter is visible and survivable, a silently wrong one is not.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
HUB = ROOT / "index.html"


def equity() -> tuple[int, str, int]:
    rows = json.loads((ROOT / "stocks/reports/index.json").read_text())
    newest = max(r["as_of"] for r in rows)
    return len(rows), newest, len(list((ROOT / "stocks/analysis").glob("*.html")))


def crypto() -> tuple[int, str, int]:
    days = sorted(p.stem for p in (ROOT / "crypto/reports").glob("20*.html"))
    return len(days), days[-1] if days else "—", len(
        list((ROOT / "crypto/analysis").glob("*.html"))
    )


def main() -> int:
    page = HUB.read_text(encoding="utf-8")
    e_n, e_new, e_a = equity()
    c_n, c_new, c_a = crypto()
    wanted = {
        r"<b>\d+ sessions · newest \d{4}-\d{2}-\d{2} · \d+ analyses</b>":
            f"<b>{e_n} sessions · newest {e_new} · {e_a} analyses</b>",
        r"<b>\d+ day\(s\) · newest [^<·]+ · \d+ analyses</b>":
            f"<b>{c_n} day(s) · newest {c_new} · {c_a} analyses</b>",
    }
    for pattern, replacement in wanted.items():
        matches = re.findall(pattern, page)
        if len(matches) != 1:
            print(f"counter not found exactly once: {pattern}", file=sys.stderr)
            return 1
        page = re.sub(pattern, replacement, page)
        print(f"  {matches[0]}  ->  {replacement}")
    HUB.write_text(page, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
