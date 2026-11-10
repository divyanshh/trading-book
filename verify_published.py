#!/usr/bin/env python3
"""Did the page we committed actually reach the public URL?

    python3 verify_published.py 2026-11-02

Exits 0 only when every path checked is served with exactly the bytes HEAD
holds for it. Anything else is a failure with a reason, because the whole
point is to replace a human squinting at a curl.

**Why a 200 is not evidence, and neither is a 404.** On 2 November 2026 both
readings lied, in opposite directions, inside twenty minutes:

* Three curls returned **404** for `stocks/reports/2026-11-02.html` while the
  GitHub Pages build for that commit had already finished successfully. The
  file was there; the CDN edge had not caught up.
* A later curl returned **200** at the previous version's byte count, for a
  page that had been corrected and re-mirrored. Status said published,
  content was stale, and nothing in the response distinguished the two.

A check that reads only the status code passes in both cases. A check that
greps for a marker string passes the second one too, because the marker was
in the old version as well. Only the byte count separates them, and only
because the file is generated — so comparing to `git show HEAD:<path>` is a
real assertion rather than a vibe.

**The retry loop is the cache, not the build.** Pages reports its build as
finished before every edge is serving it, so a single read taken a second
after the workflow goes green is a coin flip. Each attempt appends a cache
buster and sends `Cache-Control: no-cache`, which moves most edges; the
backoff covers the rest. Fifteen attempts over about two minutes was enough
every time it was tried by hand.

**It reads HEAD, not the working tree.** A file edited and not committed is
not published, and a check that compared against the working tree would call
that success — which is the same class of error as the two above: an
assertion that cannot fail in the case it exists for.
"""

from __future__ import annotations

import subprocess
import sys
import time

SITE = "https://divyanshh.github.io/trading-book"
ATTEMPTS = 15
PAUSE = 8.0


def committed(path: str) -> bytes:
    """The bytes HEAD holds for ``path``, or an empty result if it holds none."""
    done = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        capture_output=True,
        check=False,
    )
    return done.stdout if done.returncode == 0 else b""


def fetch(path: str) -> tuple[int, bytes]:
    """Status and body, through ``curl``.

    Not ``urllib``: the macOS python.org build ships no root certificates, so
    every call fails with CERTIFICATE_VERIFY_FAILED and this script would
    report a healthy site as unpublished — a false alarm is as useless as the
    false all-clear it was written to replace. ``curl`` uses the system trust
    store and is present both here and on the runner.
    """
    url = f"{SITE}/{path}?cb={time.time_ns()}"
    done = subprocess.run(
        [
            "curl", "--silent", "--show-error", "--location",
            "--max-time", "30",
            "--header", "Cache-Control: no-cache",
            "--write-out", "%{http_code}",
            "--output", "-",
            url,
        ],
        capture_output=True,
        check=False,
    )
    if done.returncode != 0:
        print(f"  {path}: curl exit {done.returncode} — retrying")
        return 0, b""
    body, status = done.stdout[:-3], done.stdout[-3:]
    try:
        return int(status), body
    except ValueError:
        return 0, b""


def verify(path: str) -> bool:
    want = committed(path)
    if not want:
        print(f"FAIL {path}: nothing committed at this path in HEAD")
        return False

    last = ""
    for attempt in range(1, ATTEMPTS + 1):
        status, body = fetch(path)
        if status == 200 and body == want:
            print(f"  ok   {path}  {len(body):,} bytes  (attempt {attempt})")
            return True
        if status == 200:
            last = f"200 but {len(body):,} bytes against {len(want):,} committed — stale edge"
        elif status:
            last = f"HTTP {status}"
        if attempt < ATTEMPTS:
            time.sleep(PAUSE)

    print(f"FAIL {path}: {last} after {ATTEMPTS} attempts")
    return False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    day = argv[1]
    paths = [
        f"stocks/reports/{day}.html",
        f"stocks/reports/{day}_ipo_review.html",
        # The crypto book publishes here too, and until 2026-11-10 this script
        # did not look. Its page had not reached the site since 7 October and
        # nothing noticed for thirty-four days, because the one command whose
        # job is proving a publish landed only ever asked about equity.
        f"crypto/reports/{day}.html",
        "index.html",
    ]
    # Absent from HEAD is not this script's failure to report. The claim here
    # is narrow on purpose — *what was committed is what is served* — and a
    # day with no report committed has nothing to check. The IPO review is
    # hand-written and most days have none; the day report is missing on an
    # NSE holiday, when the Mon-Fri mirror still runs and the service built
    # nothing. Failing on those would make this red on days when nothing is
    # wrong, which is how a check stops being read.
    #
    # A report that should exist and does not is a different fault, and it has
    # its own owner: the checklist's `report` step, which after 09:45 asks
    # whether build-daily-report-morning stamped a success today.
    optional = {
        f"stocks/reports/{day}.html",
        f"stocks/reports/{day}_ipo_review.html",
        # Optional for the same reason as the equity report, and a different
        # one: the crypto pass runs seven days a week while this script is
        # also called by the weekday equity mirror, which has no crypto page
        # to prove on a day the crypto pass has not run yet.
        f"crypto/reports/{day}.html",
    }

    print(f"verifying {day} against HEAD")
    bad = []
    for path in paths:
        if path in optional and not committed(path):
            print(f"  --   {path}  not written for this day")
            continue
        if not verify(path):
            bad.append(path)

    if bad:
        print(f"\nNOT PUBLISHED: {', '.join(bad)}")
        return 1
    print("\nall published, byte-for-byte")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
