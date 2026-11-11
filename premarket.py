#!/usr/bin/env python3
"""The hand-written pre-session read, as a section of the day's report.

The checklist is walked the evening before where it can be: the model
portfolio, the setups with their sector pass, the news on every live name, the
earnings dates, the IPO board. That work used to end up in a chat window and
nowhere else, or — once — in ``analysis/``, which is for standing pieces rather
than for one session. **A day's reading belongs in the day's report.**

    python3 premarket.py 2026-11-12

writes ``extras/<date>_premarket.html`` (standalone) and splices the section
into ``overrides/<date>.html`` ahead of Market breadth — the override the
mirror publishes over the dyno's copy.

Deliberately the same shape as ``ipo_review.py``: same ``BY_DAY`` table, same
``write``/``splice`` split, same refusal to invent a section for a day nobody
wrote one for. Two scripts that splice hand-written work into the same page
and disagree about how is how the 16 October override loop happened.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

ANCHOR = "market-breadth"
"""Where the section goes: immediately before the report's first section.

The pre-session read is what the rest of the page is read *through*, so it
sits above the data rather than below it. Matched on the id, not the element,
for the reason ``ipo_review._anchor`` gives: a section becomes a ``<details>``
the day somebody folds it, and a splice keyed to ``<h2>`` then fails silently
behind a green mirror.
"""

SLUG = "pre-session-read"


def _anchor(page: str, slug: str) -> int:
    """Where the section carrying this id begins, whatever element opens it."""
    match = re.search(rf'<(?:h2|details)[^>]*\bid="{re.escape(slug)}"', page)
    return match.start() if match else -1


def _style(day: str) -> str:
    """The report's own stylesheet, so the standalone page is not a different site."""
    override = ROOT / "overrides" / f"{day}.html"
    candidates = [override] if override.exists() else []
    candidates += sorted(ROOT.glob("overrides/20*.html"), reverse=True)
    for path in candidates:
        found = re.search(r"<style>.*?</style>", path.read_text(encoding="utf-8"), re.S)
        if found:
            return found.group(0)
    raise SystemExit(
        "no stylesheet found in any override. The standalone page would be "
        "unreadable, so nothing is written."
    )


def write(day: str, markup: str) -> None:
    """The standalone page always; the report section only once there is a report.

    Both halves say what they did. A run before the day's report exists is the
    ordinary case — the read is written the night before — and it must not
    report a splice it did not perform.
    """
    standalone = ROOT / "extras" / f"{day}_premarket.html"
    standalone.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Pre-session read — {day}</title>{_style(day)}</head><body>"
        f'<div class="wrap"><p class="eyebrow">equity-service · cortex · {day}</p>'
        f"{markup}"
        "<footer>Written by hand the evening before, against that evening's build "
        "and a live read of the brokers. Also a section of "
        f'<a href="{day}.html#{SLUG}">the day\'s report</a>.'
        "</footer></div></body></html>",
        encoding="utf-8",
    )
    print(f"  wrote extras/{standalone.name}")

    override = ROOT / "overrides" / f"{day}.html"
    if not override.exists():
        print(
            f"  overrides/{day}.html does not exist yet — the report builds at "
            f"09:25 and 18:00 IST.\n"
            f"  Re-run this after mirroring to splice the section into it."
        )
        return

    page = override.read_text(encoding="utf-8")
    start = _anchor(page, SLUG)
    end = _anchor(page, ANCHOR)
    if end < 0:
        raise SystemExit(
            f"no {ANCHOR} anchor in the override; the renderer's section markup "
            "has changed and the pre-session read has nowhere to go"
        )
    # Replace an existing section rather than stacking a second copy: this is
    # run again on every mirror of the day, and `refresh_today.py` hands it a
    # clean report each time, so both paths have to be idempotent.
    page = (page[:start] if start >= 0 else page[:end]) + markup + page[end:]
    if f'href="#{SLUG}"' not in page:
        page = page.replace(
            f'<a href="#{ANCHOR}">',
            f'<a href="#{SLUG}">Pre-session read</a><a href="#{ANCHOR}">',
            1,
        )
    override.write_text(page, encoding="utf-8")
    print(f"  spliced the section into overrides/{override.name}")


# ── 12 November 2026 ────────────────────────────────────────────────────────
# Walked 11 Nov 19:45 IST against the 18:05 build and a 19:30 read of the
# brokers. Nine of fourteen checklist steps settled before the session.

PREMARKET_2026_11_12 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">The checklist, walked the evening before. <strong>Nine of its fourteen steps were
settled on Wednesday night</strong> — the model portfolio, the setups with their sector pass, the
news on every live name, the earnings dates, the IPO board, and the four the database answers on
its own. The five left are the ones only the morning can answer. Scan times:
<strong>SWING 11 Nov 17:30 IST</strong>; WEEKLY, ETF, ETF_WEEKLY, STRIKE and REVERSAL all 9 Nov,
because <code>evening-scan</code> has not succeeded since 30 October.</p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> The
<em>to entry</em> distances are how far each trigger sat above the last price the scan saw on 11
November.</p>

<h3 class="sub">The market the board sits in</h3>
<p>Both entry gates are open and the broad index earns it: the Nifty is in a confirmed uptrend
carrying <strong>zero distribution days</strong>, follow-through dated 15 October. Next 50 is
confirmed too. That is the whole of the good news.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th class="l">status</th><th>dist days</th><th class="l">follow-through</th></tr></thead><tbody>
<tr><td class="l">Nifty 50</td><td class="l pass"><span>Confirmed Uptrend</span></td><td>0</td><td class="l">2026-10-15</td></tr>
<tr><td class="l">Nifty Next 50</td><td class="l pass"><span>Confirmed Uptrend</span></td><td>1</td><td class="l">2026-11-02</td></tr>
<tr><td class="l">Nifty Midcap 150</td><td class="l fail"><span>Under Pressure</span></td><td>3</td><td class="l">&mdash;</td></tr>
<tr><td class="l">NIFTY Smallcap 100</td><td class="l warn"><span>Rally Attempt</span></td><td>9</td><td class="l">&mdash;</td></tr>
</tbody></table></div>
<p class="note"><strong>This is the finding that matters on Thursday.</strong> Every name past the
gates below is a small or a mid cap. The gates read the broad indices, and the broad indices are
not where these names live: smallcap is only at a rally attempt and carrying nine distribution
days, midcap is under pressure. <strong>The pool the board draws from is in a materially worse
shape than the index that opened the gate for it.</strong> That refuses nothing — it is the reason
to be slower than an open gate suggests.</p>

<h3 class="sub">Breadth and flows</h3>
<p>Breadth for 11 November is <strong>70.31% of the universe above its own 20-day average against a
prior-five mean of 59.22%</strong>, and rising. Flows for the session: <strong>FII +₹12,563 crore
against DII −₹8,435 crore</strong> — foreign money buying into domestic selling, the fifth such
session in six.</p>
<p class="note"><strong>This page's own masthead disagrees with those breadth numbers, and the
masthead is the one that is wrong.</strong> It reads 62.60% against 54.22%.
<code>build-daily-report</code> runs at 18:05 and <code>record-market-regime</code> at 18:47, so the
evening page is rendered <em>before</em> that evening's breadth is recorded and carries the previous
session's reading. The gate is open on both numbers, so nothing was mis-gated — but the report
under-states breadth by one session every night, and that is a defect rather than a rounding
difference.</p>

<h3 class="sub">Four past every binding gate</h3>
<p>SWING, 11 November 17:30 IST: 1,061 scanned, 609 with a stop derived, 32 at seven or more of
eight, 24 actionable. Four carry a clean <em>blocked by</em> column.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th class="l">sector</th><th>mkt cap</th><th>gates</th><th>RS</th><th class="l">A/D</th><th>ADR</th><th>entry</th><th>stop</th><th>stop %</th><th>to entry</th><th class="l">RRG</th><th>MS rank</th></tr></thead><tbody>
<tr><td class="l">TFCILTD</td><td class="l">Financial Svcs-Specialty</td><td>7,495 Cr</td><td class="pass">8/8</td><td>97</td><td class="l">A+</td><td>3.8%</td><td>172.34</td><td>162.01</td><td>6.0%</td><td>+3.6%</td><td class="l">LEADING</td><td class="fail">78</td></tr>
<tr><td class="l">SONACOMS</td><td class="l">Auto/Truck-Original Eqp</td><td>56,175 Cr</td><td class="pass">8/8</td><td>92</td><td class="l">A</td><td>3.2%</td><td>935.12</td><td>903.90</td><td>3.3%</td><td>+1.1%</td><td class="l">IMPROVING</td><td class="fail">52</td></tr>
<tr><td class="l">LOTUSDEV</td><td class="l">Bldg-Heavy Construction</td><td>11,819 Cr</td><td class="pass">8/8</td><td>91</td><td class="l">A-</td><td>4.9%</td><td>233.87</td><td>221.75</td><td>5.2%</td><td>+4.1%</td><td class="l">IMPROVING</td><td class="fail">122</td></tr>
<tr><td class="l">MLKFOOD</td><td class="l">Food-Dairy Products</td><td>235 Cr</td><td class="warn">7/8</td><td>92</td><td class="l">A-</td><td>4.9%</td><td>100.20</td><td>96.66</td><td>3.5%</td><td>+1.1%</td><td class="l">LEADING</td><td class="pass">15</td></tr>
</tbody></table></div>
<p class="note"><strong>Read the last column before the first.</strong> O'Neil's ceiling on an
industry group rank is 40. Three of these four fail it on MarketSmith's number — TFCILTD 78,
SONACOMS 52, LOTUSDEV 122 — where our own rank says 3, 40 and 33 for the same three. Measured on
4 November across three names, ours was optimistic every time. <strong>Only MLKFOOD passes the
ceiling on their number, and it is a ₹235 crore company</strong>, which is its own objection. Run
the full audit before an order, not the rank shown here.</p>

<h3 class="sub">The sector pass, name by name</h3>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th class="l">quadrant</th><th>sector breadth</th><th class="l">sector regime</th><th>dist</th><th class="l">read</th></tr></thead><tbody>
<tr><td class="l">TFCILTD</td><td class="l">LEADING</td><td class="pass">92%</td><td class="l">Nifty Financial Services — Confirmed Uptrend</td><td>0</td><td class="l">Strongest of the four on every column. Sector breadth went 17% → 92% in thirty sessions.</td></tr>
<tr><td class="l">SONACOMS</td><td class="l">IMPROVING</td><td class="pass">76%</td><td class="l">Nifty Auto — Confirmed Uptrend</td><td>0</td><td class="l">Clean sector. Already held, so this is an add rather than a new name.</td></tr>
<tr><td class="l">LOTUSDEV</td><td class="l">IMPROVING</td><td>67%</td><td class="l">Nifty Realty — Confirmed Uptrend</td><td>0</td><td class="l">Sector confirmed 3 November; breadth up from 44%.</td></tr>
<tr><td class="l">MLKFOOD</td><td class="l">LEADING</td><td class="warn">&mdash;</td><td class="l">Nifty FMCG — Confirmed Uptrend</td><td>3</td><td class="l">Food-Dairy carries too few priced names to draw a sector breadth at all, so one column of the pass cannot be answered.</td></tr>
</tbody></table></div>

<h3 class="sub">News, on every live name</h3>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th class="l">what the search returned</th></tr></thead><tbody>
<tr><td class="l">TFCILTD</td><td class="l">Q2 FY27 declared 3 November: standalone profit ≈ ₹38.6 cr against ₹29.1 cr (+32.6%), revenue ≈ ₹80.2 cr (+20.6%). <strong>A real print behind the move.</strong> Nothing adverse.</td></tr>
<tr><td class="l">LOTUSDEV</td><td class="l">Q2 on 15 October; nothing at all in November. Last items are a September interim dividend of ₹0.30 and an August Juhu redevelopment with ₹1,600 cr GDV.</td></tr>
<tr><td class="l">SONACOMS</td><td class="l">Only an index-flow story — the stock among the session's most active. No company news. Q2 was 26 October.</td></tr>
<tr><td class="l">MLKFOOD</td><td class="l">Q1 FY27 turned profitable on ₹22 lakh net profit. On a ₹235 crore company that is noise, not a story.</td></tr>
<tr><td class="l">LTTS</td><td class="l">Q2 on 19 October. The earlier read stands: the headline +67% profit growth is about <strong>+16%</strong> once a ₹165 crore one-off is taken out.</td></tr>
<tr><td class="l">PVRINOX</td><td class="l">Q2 on 28 October, a buyback board meeting 31 August. Nothing new.</td></tr>
</tbody></table></div>
<p class="note">One search result carried text instructing the reader to disregard the other results
and follow a link. It was ignored, its figures are flagged above as unverified against the filing,
and it is recorded here because a page that hides the attempt teaches nothing.</p>

<h3 class="sub">Earnings — nothing inside five days</h3>
<p>NSE's own corporate board-meeting record, read for every held name and every resting entry. All
have reported Q2 FY27; none has a meeting scheduled.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th class="l">last board meeting</th><th class="l">purpose</th></tr></thead><tbody>
<tr><td class="l">CUPID</td><td class="l">11 Nov 2026</td><td class="l">Q2 results — the position is held through its own print</td></tr>
<tr><td class="l">LAURUSLABS</td><td class="l">29 Oct 2026</td><td class="l">Q2 results / dividend</td></tr>
<tr><td class="l">SBC</td><td class="l">15 Oct 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">SHUKRAPHAR</td><td class="l">3–4 Nov 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">SONACOMS</td><td class="l">26 Oct 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">LTTS</td><td class="l">19 Oct 2026</td><td class="l">Q2 results / dividend</td></tr>
<tr><td class="l">PVRINOX</td><td class="l">28 Oct 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">TFCILTD</td><td class="l">3 Nov 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">LOTUSDEV</td><td class="l">15 Oct 2026</td><td class="l">Q2 results</td></tr>
<tr><td class="l">MLKFOOD</td><td class="l fail"><span>no record</span></td><td class="l"><strong>NSE returns an empty meeting list.</strong> Its earnings date is unverified, so it does not clear this check.</td></tr>
</tbody></table></div>

<h3 class="sub">The IPO board is empty — checked at the exchange</h3>
<p><code>show_ipos</code> has been broken for a sixth session: it answers that the page it reads
<em>carries no current mainboard table at all</em>. So the board section below proves nothing on its
own — a parser that cannot find the table and a board that is genuinely empty produce the same
sentence. <strong>The board was therefore read at NSE directly.</strong>
<code>api/ipo-current-issue</code> returns <code>[]</code> and
<code>api/all-upcoming-issues?category=ipo</code> returns <code>[]</code>. The last mainboard issues
on the past-issues list are <strong>Bombay Coated and Special Steels</strong> (29 Oct – 2 Nov, ₹82,
listed 5 Nov) and <strong>M. K. Sons Fine Jewels</strong> (28–30 Oct, ₹162, listed 4 Nov);
everything since is SME, which is out of scope. <strong>Nothing to apply for, and nothing to write
up</strong> — but the empty board is now a verified fact rather than a parser's silence.</p>

<h3 class="sub">What Thursday morning still has to do</h3>
<div class="scroll"><table><thead><tr><th class="l">step</th><th class="l">why it cannot be answered the night before</th></tr></thead><tbody>
<tr><td class="l">pre-open jobs</td><td class="l">They run after 09:05. Reading them earlier reads yesterday's.</td></tr>
<tr><td class="l">MarketSmith mail</td><td class="l">The pre-open mail lands between 08:39 and 09:03. <strong>Every body read in full</strong> — the level that decides a week lives in the prose, not in the three fields anything parses out of it.</td></tr>
<tr><td class="l">scheduled jobs</td><td class="l">One of twenty-five is outside its budget: <code>evening-scan</code>, last successful 30 October 17:49, now <strong>193 hours silent</strong> on an unknown error. It attempts nightly and fails, so it still registers as having run. Eight sessions of weekly, ETF and reversal setups have been lost to it.</td></tr>
<tr><td class="l">untracked holdings</td><td class="l">All out-of-scope legacy names, plus one parking-fund quantity drift deferred to outside market hours.</td></tr>
<tr><td class="l">published</td><td class="l">A message defect rather than a real failure: the step compares the site's newest date against the date asked for, so any next-day run reads &ldquo;built but not mirrored&rdquo; even when the site is current.</td></tr>
</tbody></table></div>

<h3 class="sub">Open faults this pass re-confirmed</h3>
<ul class="links">
<li class="fail"><strong><code>evening-scan</code>, dead since 30 October.</strong> The costliest of these: five of the six scanners on this page are showing 9 November rows.</li>
<li class="fail"><strong><code>show_ipos</code>, broken for six sessions.</strong> It answers the same way for an empty board and for a moved table.</li>
<li class="fail"><strong>The evening report is built before the evening's breadth is recorded.</strong> 18:05 against 18:47; the masthead runs one session behind every night.</li>
<li><strong>The checklist's publish step cannot describe a next-day run.</strong> Cosmetic, but it reports a failure that did not happen, and a watchdog that cries wolf is one nobody reads.</li>
</ul>
<p class="note">Written 11 November 2026, 19:45 IST, against the 18:05 build and a live read of the
brokers at 19:30. Prices are 11 November closes.</p>
"""

BY_DAY: dict[str, str] = {
    "2026-11-12": PREMARKET_2026_11_12,
}


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else ""
    if day not in BY_DAY:
        print(f"no pre-session read written for {day!r}; known: {', '.join(sorted(BY_DAY))}")
        return 1
    print(f"{day}: pre-session read")
    write(day, BY_DAY[day])
    return 0


if __name__ == "__main__":
    sys.exit(main())
