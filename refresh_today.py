#!/usr/bin/env python3
"""Re-fetch one day's report from the service, so an override cannot serve stale.

**The loop this breaks.** ``mirror.py`` fetches a report only when the file is
missing, then copies every ``overrides/*.html`` over the published copy --
unconditionally, because an override is meant to win. The IPO splice step then
rebuilds the day's override *from the published file*. So once an override
exists for a day, it is the source of its own replacement: the service can
rebuild that report as often as it likes and the site will keep serving the
version the override was first cut from.

It survives ``--refresh`` too, which is the part that wastes an afternoon. The
refresh does re-fetch, and the override pass then overwrites the fresh copy a
few lines later.

Observed three times on 2026-10-16: the sector-breadth charts, then the chart
sizing fix, then the sizing fix again, each rebuilt on the dyno and each
invisible on the site until both files were deleted by hand.

**What this does.** After the mirror has run and applied the old override, it
re-fetches the day's report from the service and writes it back over the
published copy. The splice step that follows then cuts the override from
current content instead of from itself.

Ordering is the whole of it: this must run *after* ``mirror.py`` and *before*
the splice. Run before the mirror, the override pass would simply overwrite the
fresh copy again.

**It refuses rather than risks.** A failed fetch, a non-HTML body or anything
under the stub threshold leaves every file untouched and exits 0 -- a mirror
that already succeeded must not be turned into a failure by this, and a
300-byte redirect stub has been published as a report once already.

**It also refuses any day it cannot put back together.** The service's copy is
the report alone; the published page is that report *plus* the hand-written IPO
review spliced into it, which is why the stale file is the larger of the two.
Replacing it is only safe because the splice runs immediately afterwards and
rebuilds the section from ``ipo_review.py``. For a day with no ``BY_DAY``
entry, nothing would rebuild it, and a refresh would quietly delete
hand-written work -- so those days are left alone whatever state they are in.

    python3 refresh_today.py [YYYY-MM-DD]
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import mirror

ROOT = Path(__file__).resolve().parent
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

STUB_BYTES = 50_000
"""Below this a "report" is a redirect stub or a failed render.

The same threshold the splice step uses, and for the same reason: on 1 October
a 300-byte stub went out as a report with every section missing.
"""


def regenerable(day: str) -> bool:
    """Can the hand-written part of this day's page be rebuilt from the repo?

    Only true when ``ipo_review.py`` carries the day, because that is the one
    thing spliced into a published report that does not come from the service.
    Read from the module rather than grepped so a renamed table cannot make
    this quietly answer "yes" for every day.
    """
    try:
        import ipo_review
    except Exception as exc:  # noqa: BLE001 — unreadable means "do not touch"
        print(f"ipo_review unreadable ({type(exc).__name__}); refusing to refresh")
        return False
    return day in ipo_review.BY_DAY


def refresh(day: str) -> int:
    """Re-fetch ``day`` over the published copy. Returns 0 always."""
    if not regenerable(day):
        print(f"refresh {day}: no hand-written review to rebuild; left as is")
        return 0

    target = mirror.REPORTS / f"{day}.html"
    try:
        page = mirror.fetch(mirror.BASE + f"{day}.html")
    except Exception as exc:  # noqa: BLE001 — any failure means "leave it alone"
        print(f"refresh {day}: service unreachable ({type(exc).__name__}); left as is")
        return 0

    if not re.match(r"<!doctype html>", page, re.I):
        print(f"refresh {day}: not html; left as is")
        return 0
    if len(page.encode("utf-8")) < STUB_BYTES:
        print(f"refresh {day}: {len(page)} bytes is a stub; left as is")
        return 0

    before = target.read_text(encoding="utf-8") if target.exists() else ""
    if before == page:
        print(f"refresh {day}: already current ({len(page):,} bytes)")
        return 0

    target.write_text(page, encoding="utf-8")
    # Said loudly: this line is the evidence that an override had gone stale,
    # and the sizes say by how much.
    print(
        f"refresh {day}: REPLACED a stale published copy — "
        f"{len(before):,} bytes on disk, {len(page):,} bytes from the service"
    )
    return 0


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else dt.datetime.now(IST).date().isoformat()
    try:
        dt.date.fromisoformat(day)
    except ValueError:
        print(f"not a date: {day!r}", file=sys.stderr)
        return 2
    return refresh(day)


if __name__ == "__main__":
    sys.exit(main())
