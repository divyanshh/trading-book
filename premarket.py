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
        f"{markup.strip()}"
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
    # Replace an existing section rather than stacking a second copy: this runs
    # again on every mirror of the day, and `refresh_today.py` hands it a clean
    # report each time, so both paths have to be idempotent.
    #
    # **The whitespace is why it was not.** An anchor points at `<h2`, not at
    # the newline in front of it, so a markup string with a leading blank line
    # left that line behind in `page[:start]` and then added its own -- one
    # extra newline per run, for as long as the day keeps being mirrored. The
    # section count stayed right and the bytes drifted, which is the kind of
    # defect that is only ever found by hashing the output twice.
    head = (page[:start] if start >= 0 else page[:end]).rstrip()
    page = head + "\n" + markup.strip() + "\n" + page[end:]
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
<tr><td class="l">TFCILTD</td><td class="l">LEADING</td><td class="pass">92%</td><td class="l">Nifty Financial Services — Confirmed Uptrend</td><td>0</td><td class="l">Sector breadth went 17% → 92% in thirty sessions. <strong>An earlier version of this page called it the strongest of the four on every column; the audit below withdraws that.</strong></td></tr>
<tr><td class="l">SONACOMS</td><td class="l">IMPROVING</td><td class="pass">76%</td><td class="l">Nifty Auto — Confirmed Uptrend</td><td>0</td><td class="l">Clean sector. Already held, so this is an add rather than a new name.</td></tr>
<tr><td class="l">LOTUSDEV</td><td class="l">IMPROVING</td><td>67%</td><td class="l">Nifty Realty — Confirmed Uptrend</td><td>0</td><td class="l">Sector confirmed 3 November; breadth up from 44%.</td></tr>
<tr><td class="l">MLKFOOD</td><td class="l">LEADING</td><td class="warn">&mdash;</td><td class="l">Nifty FMCG — Confirmed Uptrend</td><td>3</td><td class="l">Food-Dairy carries too few priced names to draw a sector breadth at all, so one column of the pass cannot be answered.</td></tr>
</tbody></table></div>

<h3 class="sub">The audit, and what it did to this list</h3>
<p>Ten names were put through the full MarketSmith page before any order — ratings, surveillance,
cash flow against reported profit, ownership, board, bulk deals and the NSE earnings date. <strong>The
scanner's gate count and the audit disagree almost everywhere</strong>, and where they do, the audit
is the source with a history behind it.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>blockers</th><th>MS group rank</th><th class="l">what the page says</th></tr></thead><tbody>
<tr><td class="l">LENSKART</td><td class="pass">0</td><td class="pass">2</td><td class="l">The only clean page. Operating cash above pre-tax profit four years running. But nine block SELLs — a pre-IPO trust sold 35,000,000 shares at 683.02 on 21 Sep, below where it is bought.</td></tr>
<tr><td class="l">AARTIPHARM</td><td class="warn">1</td><td class="pass">5</td><td class="l">Mar-22: −₹43.7 Cr operating cash on +₹155.4 Cr pre-tax. Promoters −3.44pp. Six block sells.</td></tr>
<tr><td class="l">CPPLUS</td><td class="warn">1</td><td class="pass">33</td><td class="l">Best fundamentals here — EPS rank 99, and the only name with real institutions. Five straight years of profit not becoming cash.</td></tr>
<tr><td class="l">ISFT</td><td class="warn">1</td><td class="pass">20</td><td class="l">Four surveillance flags, including the <strong>trade-to-trade segment</strong>.</td></tr>
<tr><td class="l">SSWL</td><td class="fail">2</td><td class="fail">45</td><td class="l">ASM list, no institutions.</td></tr>
<tr><td class="l">ROSSTECH</td><td class="fail">2</td><td class="fail">69</td><td class="l">Cash negative in 2 of 3 years; promoters −4.90pp.</td></tr>
<tr><td class="l">PAYTM</td><td class="fail">2</td><td class="fail">73</td><td class="l">The year profit arrived is the year cash left: −₹743 Cr on +₹582 Cr pre-tax.</td></tr>
<tr><td class="l">RATNAVEER</td><td class="fail">2</td><td class="fail">79</td><td class="l">500,000 shares through at 364.15 on <strong>9 November</strong>, just under the trigger.</td></tr>
<tr><td class="l">BMWVENTLTD</td><td class="fail">2</td><td class="fail">131</td><td class="l">Worst rank in the batch; low liquidity.</td></tr>
<tr><td class="l">TFCILTD</td><td class="fail">3</td><td class="fail">71</td><td class="l"><strong>ASM list, no institutional holding, promoters hold 3.85%.</strong> Bulk tape is prop desks churning both sides. Mar-21: −₹171 Cr operating cash.</td></tr>
</tbody></table></div>
<p class="note"><strong>TFCILTD is the correction this page owes.</strong> It scored 8 of 8 with
nothing blocking, and the first version of this read called it the strongest name on the board.
Its page carries three blockers. A clean gate count said nothing whatever about an ASM listing,
an absent institutional base or a 3.85% promoter holding — which is the whole argument for the
audit being a separate step, and the reason it is never skipped.</p>
<p class="note">Every name above has its own page under <code>stocks/audits/</code>, carrying the
evidence and a written read.</p>

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


# ── 16 November 2026 ────────────────────────────────────────────
# Built Friday 13 Nov 18:00 IST against that evening's build and a live broker
# read; revised Sunday 15 Nov after the MarketSmith weekend mail. Prices are
# Friday closes, which are still the last traded prices on Monday morning.

PREMARKET_2026_11_16 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Monday opens with <strong>seven entries resting across three accounts</strong> and
the gates open: the Nifty is in a confirmed uptrend carrying two distribution days, and breadth is
<strong>75.98% of the universe above its own 20-day average</strong>. The question Monday actually
decides is not which name to buy. It is <strong>whether a trigger can pay for itself when it
fires.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes
are Friday 13 November’s. Gaps are from that close to the resting trigger.</p>

<h3 class="sub">Can the book pay for what it has already ordered?</h3>
<div class="scroll"><table><thead><tr><th class="l">account</th><th>free cash</th><th>parking it can sell</th><th>resting orders</th><th class="l">covered?</th></tr></thead><tbody>
<tr><td class="l">t-default</td><td>2,02,497</td><td>33,65,021</td><td>14,83,387</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">akul</td><td>28,703</td><td>3,46,638</td><td>1,58,840</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">t-ramprasad</td><td>6,273</td><td>&mdash; none</td><td>2,32,689</td><td class="l fail"><span>NO &mdash; short 2,26,416</span></td></tr>
</tbody></table></div>
<p class="note"><strong>t-ramprasad cannot fill a single one of its seven orders.</strong> The
smallest is ₹26,137 against ₹6,273 of cash and no parking fund. Every trigger that fires there on
Monday is rejected. t-default and akul can cover everything, but only <em>reactively</em> — the
order is refused first, parking is sold, then it is re-placed, by which time the price has moved.
<strong>That is exactly how MCX, GCSL and SGMART were missed on Friday.</strong></p>

<h3 class="sub">What is resting, and how far it has to travel</h3>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>Fri close</th><th>trigger</th><th>gap</th><th>t-default</th><th>akul</th><th>t-ramprasad</th><th>all three</th></tr></thead><tbody>
<tr><td class="l">GLAND</td><td>3,334.10</td><td>3,377.24</td><td class="pass">+1.29%</td><td>2,33,030</td><td>23,641</td><td>37,150</td><td>2,93,821</td></tr>
<tr><td class="l">LTTS</td><td>4,247.20</td><td>4,356.09</td><td>+2.56%</td><td>1,69,888</td><td>17,424</td><td>26,137</td><td>2,13,449</td></tr>
<tr><td class="l">RATNAVEER</td><td>364.35</td><td>380.36</td><td>+4.39%</td><td>2,06,916</td><td>23,202</td><td>33,091</td><td>2,63,209</td></tr>
<tr><td class="l">CPPLUS</td><td>4,148.00</td><td>4,338.66</td><td>+4.60%</td><td>2,55,981</td><td>26,032</td><td>39,048</td><td>3,21,061</td></tr>
<tr><td class="l">TFCILTD</td><td>163.95</td><td>172.34</td><td>+5.12%</td><td>1,66,825</td><td>18,613</td><td>26,540</td><td>2,11,978</td></tr>
<tr><td class="l">RUBICON</td><td>1,677.20</td><td>1,777.45</td><td>+5.98%</td><td>2,41,733</td><td>26,662</td><td>37,326</td><td>3,05,721</td></tr>
<tr><td class="l">LALITHAA</td><td>349.40</td><td>375.25</td><td>+7.40%</td><td>2,09,014</td><td>23,266</td><td>33,397</td><td>2,65,677</td></tr>
<tr><td class="l"><b>Total</b></td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td><b>14,83,387</b></td><td><b>1,58,840</b></td><td><b>2,32,689</b></td><td><b>18,74,916</b></td></tr>
</tbody></table></div>
<p><strong>GLAND is the live one</strong> — 1.3% away, the only name that could plausibly fire on
the open, and the only clean 8/8 in the queue.</p>

<h3 class="sub">The scan &mdash; 27 actionable</h3>
<p>Run by hand on <strong>15 November against Friday’s closes</strong>, because
<code>evening-scan</code> last succeeded on <strong>30 October</strong> and its last attempt was 10
November. SWING: 1,061 scanned, 672 with a stop derived, <strong>27 actionable, seven of them a
clean 8/8</strong>. Scan run 451.</p>
<p class="sub">Distance from Friday’s close to the trigger. Nothing fires unless the name travels
this far; green is inside 1.5%.</p>
<svg viewBox="0 0 470 384" width="100%" style="max-width:640px" role="img" aria-label="How far each actionable setup sits below its trigger, Friday close"><text x="0" y="9" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GCSL</text><rect x="92" y="1" width="19.8" height="9" rx="2" fill="var(--green)"/><text x="117.8" y="9" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.33%</text><text x="0" y="23" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GLAND</text><rect x="92" y="15" width="49.8" height="9" rx="2" fill="var(--green)"/><text x="147.8" y="23" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.83%</text><text x="0" y="37" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SBC</text><rect x="92" y="29" width="54.0" height="9" rx="2" fill="var(--green)"/><text x="152.0" y="37" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.90%</text><text x="0" y="51" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PTCIL</text><rect x="92" y="43" width="82.2" height="9" rx="2" fill="var(--green)"/><text x="180.2" y="51" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.37%</text><text x="0" y="65" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KRISHANA</text><rect x="92" y="57" width="87.0" height="9" rx="2" fill="var(--green)"/><text x="185.0" y="65" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.45%</text><text x="0" y="79" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RAYMOND</text><rect x="92" y="71" width="108.0" height="9" rx="2" fill="var(--series-1)"/><text x="206.0" y="79" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.80%</text><text x="0" y="93" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">YUKEN</text><rect x="92" y="85" width="108.6" height="9" rx="2" fill="var(--series-1)"/><text x="206.6" y="93" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.81%</text><text x="0" y="107" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SONACOMS</text><rect x="92" y="99" width="115.8" height="9" rx="2" fill="var(--series-1)"/><text x="213.8" y="107" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.93%</text><text x="0" y="121" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LENSKART</text><rect x="92" y="113" width="120.6" height="9" rx="2" fill="var(--series-1)"/><text x="218.6" y="121" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.01%</text><text x="0" y="135" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PVRINOX</text><rect x="92" y="127" width="135.6" height="9" rx="2" fill="var(--series-1)"/><text x="233.6" y="135" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.26%</text><text x="0" y="149" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ASKAUTOLTD</text><rect x="92" y="141" width="136.8" height="9" rx="2" fill="var(--series-1)"/><text x="234.8" y="149" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.28%</text><text x="0" y="163" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KAPSTON</text><rect x="92" y="155" width="146.4" height="9" rx="2" fill="var(--series-1)"/><text x="244.4" y="163" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.44%</text><text x="0" y="177" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LTTS</text><rect x="92" y="169" width="153.6" height="9" rx="2" fill="var(--series-1)"/><text x="251.6" y="177" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.56%</text><text x="0" y="191" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LOTUSDEV</text><rect x="92" y="183" width="161.4" height="9" rx="2" fill="var(--series-1)"/><text x="259.4" y="191" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.69%</text><text x="0" y="205" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PRADPME</text><rect x="92" y="197" width="162.0" height="9" rx="2" fill="var(--series-1)"/><text x="260.0" y="205" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.70%</text><text x="0" y="219" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LAURUSLABS</text><rect x="92" y="211" width="171.0" height="9" rx="2" fill="var(--series-1)"/><text x="269.0" y="219" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.85%</text><text x="0" y="233" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHYAMMETL</text><rect x="92" y="225" width="183.0" height="9" rx="2" fill="var(--series-1)"/><text x="281.0" y="233" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.05%</text><text x="0" y="247" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ALGOQUANT</text><rect x="92" y="239" width="196.2" height="9" rx="2" fill="var(--series-1)"/><text x="294.2" y="247" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.27%</text><text x="0" y="261" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHUKRAPHAR</text><rect x="92" y="253" width="199.8" height="9" rx="2" fill="var(--series-1)"/><text x="297.8" y="261" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.33%</text><text x="0" y="275" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">MBAPL</text><rect x="92" y="267" width="205.2" height="9" rx="2" fill="var(--series-1)"/><text x="303.2" y="275" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.42%</text><text x="0" y="289" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">BMWVENTLTD</text><rect x="92" y="281" width="205.8" height="9" rx="2" fill="var(--series-1)"/><text x="303.8" y="289" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.43%</text><text x="0" y="303" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">QPOWER</text><rect x="92" y="295" width="226.2" height="9" rx="2" fill="var(--series-1)"/><text x="324.2" y="303" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.77%</text><text x="0" y="317" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">WELSPUNLIV</text><rect x="92" y="309" width="231.6" height="9" rx="2" fill="var(--series-1)"/><text x="329.6" y="317" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.86%</text><text x="0" y="331" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">DIACABS</text><rect x="92" y="323" width="247.2" height="9" rx="2" fill="var(--amber)"/><text x="345.2" y="331" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.12%</text><text x="0" y="345" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GLOBAL</text><rect x="92" y="337" width="260.4" height="9" rx="2" fill="var(--amber)"/><text x="358.4" y="345" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.34%</text><text x="0" y="359" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RATNAVEER</text><rect x="92" y="351" width="263.4" height="9" rx="2" fill="var(--amber)"/><text x="361.4" y="359" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.39%</text><text x="0" y="373" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SAMBHV</text><rect x="92" y="365" width="286.8" height="9" rx="2" fill="var(--amber)"/><text x="384.8" y="373" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.78%</text></svg>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>gates</th><th>entry</th><th>SL</th><th>stop%</th><th>Fri close</th><th>to entry</th><th>chop</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>RATNAVEER</b></td><td class="pass">8/8</td><td>380.36</td><td>362.00</td><td>4.83%</td><td>364.35</td><td class="warn">+4.39%</td><td>86%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>DIACABS</b></td><td class="pass">8/8</td><td>393.74</td><td>371.60</td><td>5.62%</td><td>378.15</td><td class="warn">+4.12%</td><td>71%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>LAURUSLABS</b></td><td class="pass">8/8</td><td>2,492.98</td><td>2,351.50</td><td>5.68%</td><td>2,424.00</td><td class="">+2.85%</td><td>94%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>KRISHANA</b></td><td class="pass">8/8</td><td>251.31</td><td>237.89</td><td>5.34%</td><td>247.71</td><td class="pass">+1.45%</td><td>67%</td><td class="l">results filed 14 Nov</td></tr>
<tr><td class="l"><b>GLAND</b></td><td class="pass">8/8</td><td>3,361.71</td><td>3,268.50</td><td>2.77%</td><td>3,334.10</td><td class="pass">+0.83%</td><td>80%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>SONACOMS</b></td><td class="pass">8/8</td><td>936.77</td><td>888.20</td><td>5.18%</td><td>919.00</td><td class="">+1.93%</td><td>75%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>LOTUSDEV</b></td><td class="pass">8/8</td><td>234.07</td><td>221.80</td><td>5.24%</td><td>227.94</td><td class="">+2.69%</td><td>73%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SHUKRAPHAR</b></td><td class="">7/8</td><td>84.97</td><td>81.06</td><td>4.60%</td><td>82.23</td><td class="">+3.33%</td><td>80%</td><td class="l">held</td></tr>
<tr><td class="l"><b>RAYMOND</b></td><td class="">7/8</td><td>1,169.73</td><td>1,100.40</td><td>5.93%</td><td>1,149.00</td><td class="">+1.80%</td><td>73%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SBC</b></td><td class="">7/8</td><td>70.93</td><td>67.80</td><td>4.41%</td><td>70.30</td><td class="pass">+0.90%</td><td>75%</td><td class="l">held</td></tr>
<tr><td class="l"><b>PRADPME</b></td><td class="">7/8</td><td>637.17</td><td>613.30</td><td>3.75%</td><td>620.40</td><td class="">+2.70%</td><td>49%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>WELSPUNLIV</b></td><td class="">7/8</td><td>259.80</td><td>244.60</td><td>5.85%</td><td>250.14</td><td class="">+3.86%</td><td>72%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>GCSL</b></td><td class="">7/8</td><td>825.65</td><td>776.15</td><td>6.00%</td><td>822.95</td><td class="pass">+0.33%</td><td>87%</td><td class="l">held — chased Friday</td></tr>
<tr><td class="l"><b>MBAPL</b></td><td class="">7/8</td><td>203.04</td><td>191.11</td><td>5.88%</td><td>196.33</td><td class="">+3.42%</td><td>59%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>GLOBAL</b></td><td class="">7/8</td><td>151.39</td><td>143.00</td><td>5.54%</td><td>145.09</td><td class="warn">+4.34%</td><td>74%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>KAPSTON</b></td><td class="">7/8</td><td>558.01</td><td>530.80</td><td>4.88%</td><td>544.70</td><td class="">+2.44%</td><td>69%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>YUKEN</b></td><td class="">7/8</td><td>1,142.18</td><td>1,076.90</td><td>5.72%</td><td>1,121.90</td><td class="">+1.81%</td><td>70%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SAMBHV</b></td><td class="">7/8</td><td>172.34</td><td>162.70</td><td>5.59%</td><td>164.47</td><td class="warn">+4.78%</td><td>83%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>QPOWER</b></td><td class="">7/8</td><td>1,537.07</td><td>1,462.20</td><td>4.87%</td><td>1,481.20</td><td class="">+3.77%</td><td>59%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>PVRINOX</b></td><td class="">7/8</td><td>1,678.35</td><td>1,583.30</td><td>5.66%</td><td>1,641.20</td><td class="">+2.26%</td><td>89%</td><td class="l">held · trail frozen</td></tr>
<tr><td class="l"><b>LENSKART</b></td><td class="">7/8</td><td>741.63</td><td>701.50</td><td>5.41%</td><td>727.00</td><td class="">+2.01%</td><td>80%</td><td class="l">held · trail frozen</td></tr>
<tr><td class="l"><b>PTCIL</b></td><td class="">7/8</td><td>24,699.30</td><td>23,910.00</td><td>3.20%</td><td>24,365.00</td><td class="pass">+1.37%</td><td>64%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td class="">7/8</td><td>1,356.01</td><td>1,292.90</td><td>4.65%</td><td>1,315.90</td><td class="">+3.05%</td><td>63%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>ALGOQUANT</b></td><td class="">7/8</td><td>86.96</td><td>83.00</td><td>4.55%</td><td>84.21</td><td class="">+3.27%</td><td>70%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>ASKAUTOLTD</b></td><td class="">7/8</td><td>657.36</td><td>641.50</td><td>2.41%</td><td>642.70</td><td class="">+2.28%</td><td>63%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>LTTS</b></td><td class="">7/8</td><td>4,356.09</td><td>4,105.00</td><td>5.76%</td><td>4,247.20</td><td class="">+2.56%</td><td>57%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>BMWVENTLTD</b></td><td class="">7/8</td><td>66.96</td><td>63.50</td><td>5.17%</td><td>64.74</td><td class="">+3.43%</td><td>33%</td><td class="l">held · unplaced in t-default</td></tr>
</tbody></table></div>
<p class="note"><strong>GCSL is 0.33% from its trigger and GLAND 0.83%</strong> — the two that can
realistically fire on the open. Both stops are the contraction low. Five of the 27 are names already
held and three are already resting, so the genuinely new list is nineteen; every one of them still
needs the full audit before anything is placed, and <strong>nothing here was placed.</strong>
Charts, sector and RS columns for these names are in the day’s report.</p>

<h3 class="sub">What MarketSmith said over the weekend</h3>
<p>The 15 November mail makes a group argument rather than a name argument: O’Neil’s finding that
leaders travel in packs, and two packs at 52-week highs right now.</p>
<div class="scroll"><table><thead><tr><th class="l">pack</th><th class="l">names at new highs</th><th class="l">our exposure</th></tr></thead><tbody>
<tr><td class="l">Pharma</td><td class="l">Divi’s, Aurobindo, <b>Gland Pharma</b>, Sai Life, Emcure &mdash; Nifty Pharma +1.2% Friday</td><td class="l pass"><span>GLAND resting, all three accounts</span></td></tr>
<tr><td class="l">Banks &amp; financials</td><td class="l">ICICI, Kotak, Karur Vysya, <b>MCX</b></td><td class="l pass"><span>MCX filled Friday; TFCILTD resting</span></td></tr>
</tbody></table></div>
<p class="note">Both names were picked by our own scanners on their own evidence; the mail is
confirmation that institutions are buying the <em>groups</em> around them, not a new signal. It
changes nothing that is resting. <strong>It is worth saying plainly that this arrived as a link in
the mail body and our parser recorded the message as “nothing recognised”</strong> — the body was
read by hand, which is the standing rule, and the parser is what missed it.</p>

<h3 class="sub">The diary</h3>
<p>Checked against NSE board-meeting filings: <strong>no company we hold or have resting reports
next week.</strong> KRISHANA, which is unplaced, is the single filing.</p>
<div class="scroll"><table><thead><tr><th class="l">when</th><th class="l">event</th><th class="l">why it matters</th></tr></thead><tbody>
<tr><td class="l">Sat 14 Nov</td><td class="l">KRISHANA board meeting</td><td class="l">The only filing on any name we hold, want or have resting. KRISHANA is 8/8 and unplaced, held back for exactly this.</td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="l">GLAND &mdash; new CEO takes charge</td><td class="l">Deepak Sapra (ex Dr Reddy’s) starts the day our entry rests 1.3% above the close. Q2 behind the setup is strong (PAT +58%), but a chief-executive handover sits across the trigger.</td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="l">LALITHAA &mdash; second anchor lock-in expires</td><td class="l">Releases the remaining anchor tranche into a stock already &minus;6% over a month. Our trigger sits 7.4% above Friday’s close, so it is unlikely to fire before the unlock &mdash; but if it does, supply arrives the next day.</td></tr>
<tr><td class="l">18&ndash;20 Nov</td><td class="l">Crystal Crop Protection IPO</td><td class="l">Mainboard, ~₹439&ndash;600 Cr, dates still flagged tentative and the band TBA. The IPO review is due the moment the band prints.</td></tr>
</tbody></table></div>

<h3 class="sub">Stops going into Monday</h3>
<p><strong>BMWVENTLTD is 1.9% above its stop</strong> in akul (382 sh) and t-ramprasad (546 sh) —
the closest thing in the book to being taken out. If it goes it costs ₹1,146 and ₹1,638. LENSKART
(3.5%) and SHUKRAPHAR (3.6%) are next, and like BMWVENTLTD they are the losing positions: a loser
sitting near its stop is the stop working.</p>
<p class="note"><strong>15 of 41 positions cannot trail.</strong> AARTIPHARM, LENSKART, PAYTM,
PVRINOX, ROSSTECH and SSWL have their whole holding booked on the add leg with an empty base, so
the trail computes a zero quantity and the broker rejects it. They are protected at their current
level; those levels simply cannot rise. Nothing is due to trail before Monday, so there is time to
fix it first. Everything else is correctly unchanged — only CUPID is past +8%, and its stop is
already at cost in all three accounts.</p>

<h3 class="sub">Waiting on a decision</h3>
<ul>
<li><strong>Fund t-ramprasad, or stand its orders down.</strong> ₹2,32,690 of triggers against
₹6,273 and no parking fund. Not one of the seven can fill.</li>
<li><strong>Raise the position ceiling 20 → 24.</strong> t-default is 21/20 and akul 22/20 because
<code>adopt_holding</code> does not test the cap. No further fanout placement works in either until
it moves. Blocks KINGFA, BMWVENTLTD and KRISHANA.</li>
<li><strong>Fix the frozen trails.</strong> Data relabel or a code fallback in
<code>_base_quantity</code>; both need your word.</li>
<li><strong>The five weekly names</strong> — MARKSANS, FCL, CHENNPETRO, RAMRAT, SYRMA — sit at
15&ndash;19% stops, above the hardcoded 10% ceiling. KINGFA is the one that is placeable, as a daily
setup at 4.3%.</li>
<li><strong>Parking policy against the resting book.</strong> ₹14.8L resting in t-default against
₹2.02L cash. Reactive funding means rejections on a fast open.</li>
</ul>
<p class="note">Built Friday 13 November 2026, 18:00 IST from the service’s records, a live broker
read and NSE filings; revised Sunday 15 November after the MarketSmith weekend mail. Closes are
Friday’s. Nothing here places an order.</p>
"""


PREMARKET_2026_11_17 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Tuesday opens with <strong>our own gates shut on both legs</strong>. Breadth is
<strong>65.11% of the universe above its own 20-day average against a prior-five mean of
69.42%</strong> — falling, so the breadth gate is shut — and the computed status reads
<strong>DOWNTREND</strong> on six distribution days with no follow-through since. A buy needs both
open. <strong>None of tonight&rsquo;s twenty-six actionable names may be placed on Tuesday,
however good they look.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes
are Monday 16 November&rsquo;s. The scan was run by hand tonight against them — SWING run 458.</p>

<h3 class="sub" id="pre-gates">The two gates, and who disagrees</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l">65.11% against 69.42%, falling</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">DOWNTREND &mdash; 6 distribution days counted, no follow-through day since</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED_UPTREND, 2 distribution days</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Nifty vs its 20MA</td><td class="l">+5.91%</td><td class="l"><span>extended</span></td></tr>
</tbody></table></div>
<p class="note">The divergence is the read, and it is not new information — it is the same market
described twice. MarketSmith&rsquo;s own weekly, <em>&ldquo;Few Leaders, One Flying Index&rdquo;</em>,
says <strong>only 20 of the top 500 stocks are doing the lifting</strong>, that large companies grew
profits <strong>36% against 6%</strong> for smaller ones, that the market is extended and that
waiting for a pullback is the smarter move. Their headline status says buy; their own research says
wait. <strong>Our gates say wait in numbers.</strong></p>

<h3 class="sub" id="pre-today">What Monday actually did</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">where it ended</th></tr></thead><tbody>
<tr><td class="l">KRISHANA</td><td class="l">Gapped through its 251.31 trigger to 254 on the open and filled in t-default (745 @ 253.98) and akul (83 @ 254.25)</td><td class="l fail"><span>back under its own pivot at ~243</span></td></tr>
<tr><td class="l">GLAND</td><td class="l">ATO rejected for cash in all three; parking sold to the shortfall and re-bought 69 and 7 @ 3,392, 25 @ 3,385 in Ram&rsquo;s</td><td class="l pass"><span>held, stopped, all three</span></td></tr>
<tr><td class="l">GCSL</td><td class="l">Rejected for cash in Ram&rsquo;s, re-bought 48 @ 833.90 at the chase ceiling</td><td class="l pass"><span>held, stopped</span></td></tr>
<tr><td class="l">LAURUSLABS</td><td class="l">Stop fired 13:17 in all three &mdash; 78 / 8 / 12 at ~2,251.5 against a 2,252.40 stop</td><td class="l fail"><span>&minus;₹12,708, slippage under ₹1</span></td></tr>
</tbody></table></div>
<p class="note"><strong>KRISHANA is the day in one name.</strong> Ram&rsquo;s retry filled at
<strong>243.35 &mdash; below the trigger</strong>, which is a better price only because the breakout
had already failed. The two accounts that filled at the open are underwater on it, and it has since
<strong>dropped off the actionable list entirely</strong>. Last night it was a clean 8/8.</p>

<h3 class="sub" id="pre-scan">The scan &mdash; 26 actionable, none of them placeable</h3>
<p>Run by hand tonight against Monday&rsquo;s closes. <strong>SWING run 458: 570 candidates, 26
actionable, seven of them a clean 8/8.</strong> Every other scanner returned <strong>zero</strong> —
WEEKLY (533 candidates), ETF (21), ETF_WEEKLY (22) and REVERSAL (385). STRIKE returns the identical
26 and is not a traded strategy.</p>
<p class="sub">That the weekly book is empty while the daily list is full is itself the tape: these
are one- and two-day breakouts in a market with no sustained leadership underneath them.</p>
<p class="sub">Distance from Monday&rsquo;s close to the trigger. Nothing fires unless the name travels this far; green is inside 1.5%, amber is 3.5% or more. <strong>With both gates shut none of it may be bought &mdash; this is what is being refused, drawn.</strong></p>
<svg viewBox="0 0 470 314" width="100%" style="max-width:640px" role="img" aria-label="How far each actionable setup sits below its trigger, Monday close"><text x="0" y="9" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GRAPHITE</text><rect x="92" y="1" width="68.3" height="9" rx="2" fill="var(--green)"/><text x="166.3" y="9" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.0%</text><text x="0" y="23" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ALGOQUANT</text><rect x="92" y="15" width="75.1" height="9" rx="2" fill="var(--green)"/><text x="173.1" y="23" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.1%</text><text x="0" y="37" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SSWL</text><rect x="92" y="29" width="95.6" height="9" rx="2" fill="var(--green)"/><text x="193.6" y="37" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.4%</text><text x="0" y="51" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GLAND</text><rect x="92" y="43" width="102.4" height="9" rx="2" fill="var(--green)"/><text x="200.4" y="51" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.5%</text><text x="0" y="65" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SBC</text><rect x="92" y="57" width="102.4" height="9" rx="2" fill="var(--green)"/><text x="200.4" y="65" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.5%</text><text x="0" y="79" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LOTUSDEV</text><rect x="92" y="71" width="109.3" height="9" rx="2" fill="var(--series-1)"/><text x="207.3" y="79" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.6%</text><text x="0" y="93" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LENSKART</text><rect x="92" y="85" width="116.1" height="9" rx="2" fill="var(--series-1)"/><text x="214.1" y="93" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.7%</text><text x="0" y="107" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">BMWVENTLTD</text><rect x="92" y="99" width="136.6" height="9" rx="2" fill="var(--series-1)"/><text x="234.6" y="107" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.0%</text><text x="0" y="121" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHIVAUM</text><rect x="92" y="113" width="157.1" height="9" rx="2" fill="var(--series-1)"/><text x="255.1" y="121" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.3%</text><text x="0" y="135" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PVRINOX</text><rect x="92" y="127" width="163.9" height="9" rx="2" fill="var(--series-1)"/><text x="261.9" y="135" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.4%</text><text x="0" y="149" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LTTS</text><rect x="92" y="141" width="163.9" height="9" rx="2" fill="var(--series-1)"/><text x="261.9" y="149" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.4%</text><text x="0" y="163" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">TAMBOLIIN</text><rect x="92" y="155" width="170.7" height="9" rx="2" fill="var(--series-1)"/><text x="268.7" y="163" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.5%</text><text x="0" y="177" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KSHINTL</text><rect x="92" y="169" width="191.2" height="9" rx="2" fill="var(--series-1)"/><text x="289.2" y="177" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.8%</text><text x="0" y="191" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHADOWFAX</text><rect x="92" y="183" width="204.9" height="9" rx="2" fill="var(--series-1)"/><text x="302.9" y="191" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.0%</text><text x="0" y="205" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHYAMMETL</text><rect x="92" y="197" width="204.9" height="9" rx="2" fill="var(--series-1)"/><text x="302.9" y="205" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.0%</text><text x="0" y="219" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHUKRAPHAR</text><rect x="92" y="211" width="225.3" height="9" rx="2" fill="var(--series-1)"/><text x="323.3" y="219" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.3%</text><text x="0" y="233" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">WELSPUNLIV</text><rect x="92" y="225" width="225.3" height="9" rx="2" fill="var(--series-1)"/><text x="323.3" y="233" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.3%</text><text x="0" y="247" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ARIHANTCAP</text><rect x="92" y="239" width="239.0" height="9" rx="2" fill="var(--amber)"/><text x="337.0" y="247" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.5%</text><text x="0" y="261" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RATNAVEER</text><rect x="92" y="253" width="259.5" height="9" rx="2" fill="var(--amber)"/><text x="357.5" y="261" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.8%</text><text x="0" y="275" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PAYTM</text><rect x="92" y="267" width="266.3" height="9" rx="2" fill="var(--amber)"/><text x="364.3" y="275" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.9%</text><text x="0" y="289" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">AARTIPHARM</text><rect x="92" y="281" width="273.1" height="9" rx="2" fill="var(--amber)"/><text x="371.1" y="289" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.0%</text><text x="0" y="303" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SONACOMS</text><rect x="92" y="295" width="286.8" height="9" rx="2" fill="var(--amber)"/><text x="384.8" y="303" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.2%</text></svg>
<p class="note">Per-name price charts for all of these &mdash; 139 of them &mdash; are in <a href="2026-11-16.html">Monday&rsquo;s report</a>, alongside the sector pass, RRG quadrant, industry rank and volume columns this table leaves out.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>gates</th><th>RS</th><th>A/D</th><th>chop</th><th>ADR</th><th>entry</th><th>SL</th><th>stop%</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>RATNAVEER</b></td><td class="pass">8/8</td><td>97</td><td>A+</td><td>86%</td><td>4.8%</td><td>375.95</td><td>356.50</td><td>5.2%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>SHADOWFAX</b></td><td class="pass">8/8</td><td>96</td><td>B+</td><td>66%</td><td>4.8%</td><td>298.40</td><td>281.35</td><td>5.7%</td><td class="l">new</td></tr>
<tr><td class="l"><b>KSHINTL</b></td><td class="pass">8/8</td><td>95</td><td>D&minus;</td><td>59%</td><td>4.6%</td><td>1,052.10</td><td>1,016.50</td><td>3.4%</td><td class="l">new &mdash; A/D D&minus; is distribution</td></tr>
<tr><td class="l"><b>SHIVAUM</b></td><td class="pass">8/8</td><td>92</td><td>B&minus;</td><td>83%</td><td>4.1%</td><td>567.13</td><td>550.00</td><td>3.0%</td><td class="l">new</td></tr>
<tr><td class="l"><b>GLAND</b></td><td class="pass">8/8</td><td>92</td><td>B+</td><td>81%</td><td>3.5%</td><td>3,435.86</td><td>3,307.20</td><td>3.7%</td><td class="l">held &mdash; re-derived again tonight</td></tr>
<tr><td class="l"><b>SONACOMS</b></td><td class="pass">8/8</td><td>92</td><td>A</td><td>75%</td><td>3.2%</td><td>936.77</td><td>888.20</td><td>5.2%</td><td class="l">held</td></tr>
<tr><td class="l"><b>LOTUSDEV</b></td><td class="pass">8/8</td><td>91</td><td>A&minus;</td><td>72%</td><td>4.8%</td><td>235.37</td><td>221.80</td><td>5.8%</td><td class="l">new</td></tr>
<tr><td class="l"><b>SHUKRAPHAR</b></td><td>7/8</td><td>98</td><td>A+</td><td>80%</td><td>6.3%</td><td>84.97</td><td>81.06</td><td>4.6%</td><td class="l">held</td></tr>
<tr><td class="l"><b>SSWL</b></td><td>7/8</td><td>97</td><td>A</td><td>90%</td><td>6.4%</td><td>578.40</td><td>561.20</td><td>3.0%</td><td class="l">held</td></tr>
<tr><td class="l"><b>SBC</b></td><td>7/8</td><td>97</td><td>A+</td><td>75%</td><td>2.9%</td><td>71.43</td><td>67.80</td><td>5.1%</td><td class="l">held</td></tr>
<tr><td class="l"><b>TAMBOLIIN</b></td><td>7/8</td><td>95</td><td>D+</td><td>80%</td><td>8.2%</td><td>337.82</td><td>320.00</td><td>5.3%</td><td class="l">new &mdash; 8.2% ADR is wild</td></tr>
<tr><td class="l"><b>WELSPUNLIV</b></td><td>7/8</td><td>95</td><td>A+</td><td>72%</td><td>5.3%</td><td>254.16</td><td>243.36</td><td>4.2%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>PVRINOX</b></td><td>7/8</td><td>89</td><td>A</td><td>90%</td><td>3.6%</td><td>1,678.35</td><td>1,620.20</td><td>3.5%</td><td class="l">held &middot; trail frozen</td></tr>
<tr><td class="l"><b>LENSKART</b></td><td>7/8</td><td>89</td><td>B+</td><td>80%</td><td>3.4%</td><td>747.49</td><td>716.30</td><td>4.2%</td><td class="l">held &middot; MS buy watchlist</td></tr>
<tr><td class="l"><b>PAYTM</b></td><td>7/8</td><td>89</td><td>B+</td><td>75%</td><td>3.6%</td><td>1,963.92</td><td>1,872.20</td><td>4.7%</td><td class="l">held</td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td>7/8</td><td>87</td><td>A&minus;</td><td>64%</td><td>3.7%</td><td>1,356.01</td><td>1,292.90</td><td>4.7%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>ALGOQUANT</b></td><td>7/8</td><td>83</td><td>B</td><td>70%</td><td>4.5%</td><td>85.67</td><td>81.65</td><td>4.7%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>AARTIPHARM</b></td><td>7/8</td><td>83</td><td>B</td><td>66%</td><td>4.9%</td><td>1,025.85</td><td>979.65</td><td>4.5%</td><td class="l">held</td></tr>
<tr><td class="l"><b>LTTS</b></td><td>7/8</td><td>79</td><td>A</td><td>58%</td><td>3.5%</td><td>4,328.24</td><td>4,105.00</td><td>5.2%</td><td class="l">resting &mdash; back on the list</td></tr>
<tr><td class="l"><b>GRAPHITE</b></td><td>7/8</td><td>78</td><td>A&minus;</td><td>56%</td><td>4.0%</td><td>805.61</td><td>764.15</td><td>5.1%</td><td class="l">new</td></tr>
<tr><td class="l"><b>ARIHANTCAP</b></td><td>7/8</td><td>74</td><td>B+</td><td>75%</td><td>4.7%</td><td>95.58</td><td>91.35</td><td>4.4%</td><td class="l">new &mdash; RS 74, below the band</td></tr>
<tr><td class="l"><b>BMWVENTLTD</b></td><td>7/8</td><td>72</td><td>B</td><td>34%</td><td>3.9%</td><td>66.96</td><td>63.50</td><td>5.2%</td><td class="l">held &mdash; RS 72, chop 34%</td></tr>
</tbody></table></div>
<p class="note">Four of the twenty-six &mdash; GLOBAL, PTCIL, BSE and PRINCEPIPE &mdash; are
actionable but did not render a full row in tonight&rsquo;s build, so their levels are not repeated
here rather than estimated. <strong>Charts, the sector pass and the RS columns for all of them are
in the day&rsquo;s report.</strong> Every one still needs the full audit before anything is placed,
and with both gates shut nothing can be.</p>
<p class="note"><strong>Two names answer open questions.</strong> <b>LTTS</b> is back on the list,
which closes last night&rsquo;s finding that its resting 4,356.09 trigger had no current scan
evidence behind it &mdash; tonight&rsquo;s entry is 4,328.24 on the same 4,105.00 stop.
<b>RUBICON</b> is still absent for the second night running, while MarketSmith names it one of five
leaders to watch and carries it on the buy watchlist. That disagreement is unresolved and the
position rests at 1,777.45 in both accounts.</p>

<h3 class="sub" id="pre-flows">Who is actually buying &mdash; FII and DII</h3>
<p class="sub">Net cash-market flows in &#8377; crore, to Monday 16 November. The two are
trading against each other, and have been all week.</p>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>FII net</th><th>DII net</th><th>FII 5-session</th><th>FII buy</th><th>FII sell</th></tr></thead><tbody>
<tr><td class="l"><b>Mon 16 Nov</b></td><td class="pass">+4,865</td><td class="bad">&minus;3,519</td><td class="pass">+38,207</td><td>15,637</td><td>10,772</td></tr>
<tr><td class="l">Fri 13 Nov</td><td class="pass">+5,737</td><td class="bad">&minus;2,254</td><td class="pass">+33,342</td><td>18,340</td><td>12,603</td></tr>
<tr><td class="l">Thu 12 Nov</td><td class="pass">+7,831</td><td class="bad">&minus;6,331</td><td class="pass">+41,356</td><td>20,273</td><td>12,443</td></tr>
<tr><td class="l">Wed 11 Nov</td><td class="pass">+12,563</td><td class="bad">&minus;8,435</td><td class="pass">+48,500</td><td>30,087</td><td>17,524</td></tr>
<tr><td class="l">Mon 9 Nov</td><td class="pass">+7,212</td><td class="bad">&minus;7,173</td><td class="pass">+43,220</td><td>20,311</td><td>13,099</td></tr>
</tbody></table></div>
<p class="note"><strong>Foreign money has bought every session this week and domestic money has
sold every session.</strong> FIIs are +&#8377;38,207 Cr over five sessions. That is the mechanism
behind &ldquo;few leaders, one flying index&rdquo;: foreign flows go into the large, liquid names
that carry the Nifty, while domestic institutions take profits across the broader market &mdash;
which is where every one of our setups lives. <strong>A rising index on falling breadth is not a
contradiction when you can see who is on each side of it.</strong></p>

<h3 class="sub" id="pre-breadth">Breadth, and the day the gate shut</h3>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>above their 20MA</th><th>prior-5 mean</th><th class="l">breadth gate</th></tr></thead><tbody>
<tr><td class="l"><b>Mon 16 Nov</b></td><td class="bad">65.11%</td><td>69.42%</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Fri 13 Nov</td><td>74.94%</td><td>65.42%</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Thu 12 Nov</td><td>75.95%</td><td>62.65%</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Wed 11 Nov</td><td>70.31%</td><td>59.22%</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Tue 10 Nov</td><td>62.60%</td><td>54.22%</td><td class="l pass"><span>open</span></td></tr>
</tbody></table></div>
<p class="note"><strong>The gate was open every session last week and shut on Monday.</strong>
Breadth did not drift down &mdash; it fell from 74.94% to 65.11% in a single session while the
prior-five mean kept rising to 69.42%, so the two crossed. This is the first shut reading of the
move, not the continuation of a decline.</p>

<h3 class="sub" id="pre-funding">Can the book pay for what it has already ordered?</h3>
<div class="scroll"><table><thead><tr><th class="l">account</th><th>held</th><th>free cash</th><th>parking it can sell</th><th>resting orders</th><th class="l">covered?</th></tr></thead><tbody>
<tr><td class="l">t-default</td><td>59,34,806</td><td>1,87,863</td><td>26,785 units &asymp; 31,31,100</td><td>24,50,238</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">akul</td><td>3,48,154</td><td>18,974</td><td>2,818 units &asymp; 3,29,480</td><td>2,12,072</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">t-ramprasad</td><td>5,18,507</td><td>66,002</td><td>&mdash; none</td><td>4,27,130</td><td class="l fail"><span>NO &mdash; short 3,61,128</span></td></tr>
</tbody></table></div>
<p class="note">The reactive rule was run live for the first time on Monday and it worked: GLAND was
refused for cash in all three accounts, the broker named its own shortfall, parking was sold to
<em>that</em> figure plus 5% and the stock was bought back inside the chase ceiling.
<strong>t-ramprasad is still the one that cannot be fixed that way</strong> &mdash; it holds no
parking and is never swept. It funded itself on Monday only because its legacy holdings were sold
by hand.</p>

<h3 class="sub" id="pre-diary">The diary</h3>
<div class="scroll"><table><thead><tr><th class="l">when</th><th class="l">event</th><th class="l">why it matters</th></tr></thead><tbody>
<tr><td class="l">Tue 17 Nov</td><td class="l">Crystal Crop Protection &mdash; anchor bidding</td><td class="l">The book opens to anchors a day before retail. Anchor demand is the first honest read on a deal whose grey-market premium has halved since Friday.</td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="l">LALITHAA &mdash; second anchor lock-in expires</td><td class="l">Releases the remaining anchor tranche. Our trigger rests at 375.25 in both accounts; supply arrives whether or not it fires.</td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="l">SANSERA investor meet</td><td class="l">Third of three this week.</td></tr>
<tr><td class="l">Wed 18 Nov</td><td class="l">KRISHANA earnings call, 12:00</td><td class="l">A call, not a results date &mdash; results were filed 14 Nov with PAT up ~135%. But it is an event on a position now held in all three accounts and sitting under its pivot.</td></tr>
<tr><td class="l">Wed 18 Nov</td><td class="l">SHYAMMETL analyst meet</td><td class="l">Resting at 1,356.01 in all three.</td></tr>
<tr><td class="l">18&ndash;20 Nov</td><td class="l">Crystal Crop Protection IPO</td><td class="l">₹259&ndash;272, ~₹455 Cr. <b>AVOID</b> &mdash; see the IPO review.</td></tr>
<tr><td class="l">19&ndash;23 Nov</td><td class="l">Mahanadi Coalfields IPO</td><td class="l">₹129&ndash;136, ₹8,981 Cr, 100% offer-for-sale by Coal India. <b>SKIP</b> as a trade.</td></tr>
</tbody></table></div>

<h3 class="sub" id="pre-decisions">Waiting on a decision</h3>
<ul>
<li><strong>GLAND rests at two different stops.</strong> 3,233.10 in t-default and akul, 3,268.50 in
t-ramprasad, because Ram&rsquo;s was re-derived on a later scan. Tonight the scanner moved it again,
to 3,307.20. Three accounts, one name, three levels &mdash; this breaks the rule that all three hold
the same position and it needs one number.</li>
<li><strong>RUBICON.</strong> Absent from our scan two nights running; named a leader by
MarketSmith. Resting at 1,777.45 in t-default and akul.</li>
<li><strong>Fund t-ramprasad or stand its orders down.</strong> ₹4,27,130 resting against ₹66,002.</li>
<li><strong>The report pipeline is broken at both ends.</strong>
<code>build-daily-report-morning</code> has failed three days running &mdash; last success 13
November, 37 hours silent against a 26-hour budget. <code>evening-scan</code> has not succeeded
since 30 October. Both are being stood in for by hand every night.</li>
<li><strong><code>show_ipos</code> can no longer read its source</strong> &mdash; the IPO board was
rebuilt by hand tonight. The parser needs fixing before it is trusted again.</li>
</ul>
<p class="note">Built Monday 16 November 2026 from the service&rsquo;s records, a live read of all
three brokers, tonight&rsquo;s hand-run scan (SWING run 458) and NSE filings. Closes are
Monday&rsquo;s. Nothing here places an order.</p>
"""


PREMARKET_2026_11_18 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Wednesday opens with <strong>both gates shut for a second session</strong>. Breadth is
<strong>65.79% of the universe above its own 20-day average against a prior-five mean of 69.65%</strong>
&mdash; the reading rose today and the gate still shut, because the mean rose faster &mdash; and the
computed status reads
<strong>DOWNTREND</strong> on seven distribution days. <strong>None of tonight&rsquo;s twenty-four
actionable names may be placed on Wednesday.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes are
Tuesday 17 November&rsquo;s. All six scanners were run by hand tonight against them &mdash; SWING run 466.</p>
<p class="note"><strong>The one number to read first: GLAND closed at 3,248.40 and the stop in t-default
and akul rests at 3,233.10.</strong> That is fifteen rupees, 0.47%. The same name&rsquo;s stop in
t-ramprasad &mdash; 3,268.50, set thirty-five rupees higher because it was derived on a later scan &mdash;
<strong>fired this afternoon at 14:50</strong>. Sixty-nine shares and seven shares are carrying tonight
what twenty-five already paid.</p>

<p class="note"><strong>Two things further down this page are wrong, and they are wrong in the
machine-built sections, not here.</strong> <b>&ldquo;IPOs &mdash; mainboard&rdquo; says &ldquo;No
mainboard IPO is open or upcoming&rdquo;.</b> That is false &mdash; Crystal Crop opens today and
Mahanadi opens tomorrow &mdash; and it is the broken <code>show_ipos</code> parser, not a reading of the
board. <strong>The hand-written IPO review lower down is the one to read.</strong> And <b>&ldquo;How the
market opened&rdquo; shows Tuesday&rsquo;s pre-open</b>, not Wednesday&rsquo;s: GIFT Nifty 25,302.50
against a 25,291.10 previous close, quoted 17 Nov 09:09 IST. Wednesday&rsquo;s gap is not on this page and
cannot be &mdash; it is written the evening before. Both are listed as open faults at the foot of this
section.</p>

<h3 class="sub" id="pre-morning">Morning update &mdash; written 13:30, Wednesday 18 November</h3>
<p class="note"><strong>Two things on this page were written before the facts arrived, and both are
corrected here rather than quietly edited.</strong></p>
<div class="scroll"><table><thead><tr><th class="l">what the page said</th><th class="l">what actually happened</th></tr></thead><tbody>
<tr><td class="l">Nvidia was &ldquo;the real risk on this page&rdquo; &mdash; its quarter was unknown when this was written.</td><td class="l pass"><b>It beat.</b> Revenue <b>$115.84bn, +103%</b> against ~$109bn expected; adjusted EPS $2.68 against ~$2.47; Q4 guided near <b>$130bn</b>; a <b>$150bn</b> buyback increase; shares +3&ndash;5% after hours. The board will not reinstate Jensen Huang. One blemish: gross margin guided down to <b>71&ndash;72%</b> from 74.9%.</td></tr>
<tr><td class="l">I said to expect <b>a firmer open</b> on the back of that beat.</td><td class="l fail"><b>Wrong.</b> GIFT Nifty was <b>25,243 at 08:15 against a 25,387.40 close &mdash; down 155 points</b>, and MarketSmith&rsquo;s own headline read <em>&ldquo;GIFT Nifty Signals Caution.&rdquo;</em> Wall Street fell on Tuesday <b>before</b> Nvidia reported &mdash; Dow &minus;848.75 (&minus;1.64%), S&amp;P &minus;1.03%, Nasdaq &minus;0.74% on semiconductor selling. The beat lifted <b>Asia</b> afterwards (Kospi +3.08%, Taiex +1.13%, Nikkei +1.03%); it did not lift India&rsquo;s open.</td></tr>
</tbody></table></div>
<p class="sub">MarketSmith&rsquo;s status is unchanged &mdash; <b>Confirmed Uptrend, 2 distribution days, no
downgrade</b> &mdash; with a stated conditional: they cut to &ldquo;Uptrend Under Pressure&rdquo; if the
count rises or the Nifty breaches key support. Gold fell to its lowest since September 2025 as Fed
officials argued for <b>further rate hikes</b>; Brent $92.98.</p>

<h3 class="sub" id="pre-today-actual">What the session actually did</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l"><b>GLAND</b></td><td class="l">The weak open took it straight through the 3,233.10 stop at <b>09:15:58</b>. t-default sold 69 at an average of <b>3,221.86</b>, akul 7 at <b>3,224.34</b> &mdash; both roughly eleven rupees <em>below</em> the stop.</td><td class="l fail"><span>&minus;&#8377;11,739.66 and &minus;&#8377;1,173.62</span></td></tr>
<tr><td class="l"><b>GLAND</b>, the whole position</td><td class="l">With Ram&rsquo;s 25 shares stopped on the 17th at &minus;&#8377;2,923.60, the name is now closed in all three accounts.</td><td class="l fail"><span><b>&minus;&#8377;15,836.88 across the book</b></span></td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td class="l">Fired at 09:15:49 and <b>filled in t-ramprasad</b> &mdash; 38 at 1,359.92, adopted and stopped at 1,292.90. Rejected for funds in the other two; <b>both refusals were phantom</b>, &#8377;214,250 and &#8377;23,052 of dead reservations left by the rejected orders themselves.</td><td class="l warn"><span>held in Ram only</span></td></tr>
<tr><td class="l"><b>SHYAMMETL</b>, the decision</td><td class="l">It fell straight back to ~1,320, <b>below its own 1,356.01 trigger</b> &mdash; a failed breakout on the day it broke out, on a name failing two gates (G5 sector LAGGING, <b>G7 RS 87</b> against a 90 floor). The triggers were re-rested, then <b>cancelled on his call</b>.</td><td class="l"><span>not bought in t-default or akul</span></td></tr>
<tr><td class="l">Parking</td><td class="l">Free cash parked across all three at 116.98 &mdash; 3,380, 342 and <b>1,794 units</b>.</td><td class="l pass"><span>&#8377;645,262 &middot; <b>t-ramprasad&rsquo;s first parking ever</b></span></td></tr>
</tbody></table></div>
<p class="note"><strong>The stop that matters, and an open question.</strong> He observed that GLAND&rsquo;s
stop should have been <b>3,169</b> &mdash; the swing low <em>less</em> the 2% buffer (3,233.10 &times;
0.98 = 3,168.44). Our stop rested <b>at</b> 3,233.10, the structural level with no buffer, which is the
rule as written since close-based stops were disarmed on 6 November. <strong>On today&rsquo;s evidence he
is right and this was a shakeout:</strong> our own fills bottomed at <b>3,221.1</b> and the stock was back
at <b>&#8377;3,249</b> by 11:32, above its previous close. A 3,169 stop would have needed another 1.6%
below our fills to trigger. <em>The exact intraday low could not be verified &mdash; every quote source
refused or timed out &mdash; so this is an inference from our own fills, not a confirmed low.</em>
<strong>The rule has NOT been changed on the strength of one name over two days.</strong> The proposal is
to measure <code>structural &times; 0.98</code> against <code>structural</code> across the whole closed
book, count how many exits flip and what it does to total R, and ship the buffer only if it wins.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l">65.79% against 69.65%, on 877 names</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">DOWNTREND &mdash; 7 distribution days on smallcap, day 25 of a rally attempt on the Nifty</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED_UPTREND, 2 distribution days</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Nifty vs its 20MA</td><td class="l">+6.08%, against +5.91% on Monday</td><td class="l"><span>more extended</span></td></tr>
</tbody></table></div>
<p class="note">The service and MarketSmith have now disagreed <strong>five sessions running</strong>, and
agree on only <strong>18 of 42 recorded days (43%)</strong>. That is not a tie-break to be settled by
preference. The section below is what the disagreement is actually made of.</p>

<h3 class="sub" id="pre-indices">Why the index and the market disagree &mdash; all 17 indices, counted</h3>
<p class="sub">Distribution days and status per index, computed tonight. This is the same fact MarketSmith
writes as &ldquo;few leaders, one flying index&rdquo;, measured instead of asserted.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">status</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>NIFTY</b></td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">day 25 of a rally attempt</td></tr>
<tr><td class="l"><b>SMALLCAP</b></td><td class="bad">7</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l"><b>the only broad index not confirmed &mdash; and where every one of our setups lives</b></td></tr>
<tr><td class="l">MIDCAP</td><td>2</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">day 17</td></tr>
<tr><td class="l">NEXT 50</td><td>1</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">follow-through 2 Nov</td></tr>
<tr><td class="l">IT</td><td class="bad">8</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">eight distribution days inside a confirmed uptrend &mdash; follow-through 16 Oct</td></tr>
<tr><td class="l">METAL</td><td>3</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l">the only sector downgraded</td></tr>
<tr><td class="l">ENERGY</td><td>2</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">&mdash;</td></tr>
<tr><td class="l">AUTO &middot; FMCG &middot; MEDIA &middot; PHARMA &middot; REALTY &middot; HEALTHCARE</td><td>1</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">six sectors, one distribution day each</td></tr>
<tr><td class="l">BANK &middot; FIN SERVICES &middot; PSU BANK &middot; CONSUMER DURABLES</td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">clean; follow-throughs 5 Nov, 3 Nov, 29 Oct</td></tr>
</tbody></table></div>
<p class="note"><strong>The Nifty has zero distribution days. Smallcap has seven.</strong> Both readings are
correct and they describe different markets. MarketSmith grades the index, so it sees a confirmed uptrend;
our status grades the breadth of the thing we actually buy, so it sees a downtrend. <strong>Banks and
financials are clean and carrying the index; smallcap is being distributed underneath it.</strong> Every
name in the table further down is a smallcap. That is the whole disagreement, and on this evidence the
gate is reading the right market.</p>

<h3 class="sub" id="pre-today">What Tuesday did</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">where it ended</th></tr></thead><tbody>
<tr><td class="l"><b>GLAND</b></td><td class="l">The 3,268.50 stop in t-ramprasad fired at 14:50 &mdash; 25 shares at an average of <b>3,268.06</b> against a 3,385.00 entry. t-default and akul, stopped thirty-five rupees lower at 3,233.10, did not fire.</td><td class="l fail"><span>&minus;&#8377;2,923.60 realised, &#8377;11.60 of slippage</span></td></tr>
<tr><td class="l"><b>GLAND</b> &amp; <b>KRISHANA</b></td><td class="l">Both <b>skipped by tonight&rsquo;s scan entirely</b> &mdash; &ldquo;no base to hang a stop from&rdquo;. The two names carrying the damage are the two with no base left.</td><td class="l fail"><span>&minus;4.23% and &minus;4.36% held</span></td></tr>
<tr><td class="l">t-ramprasad</td><td class="l">Two hand-sells by the account holder &mdash; ITC 100 @ 294.55 and TATAPOWER 270 @ 343.35. Not ours; recorded, not acted on.</td><td class="l"><span>cash &#8377;1,87,619</span></td></tr>
<tr><td class="l">t-default</td><td class="l">Nothing of ours fired. Book closed at &#8377;59,99,612.68 against &#8377;59,34,970.28 invested.</td><td class="l pass"><span>+&#8377;64,642 total, &minus;&#8377;5,207 on the day</span></td></tr>
<tr><td class="l">LIQUIDCASE</td><td class="l">&#8377;1,87,765 of idle cash queued into parking as an AMO at his instruction &mdash; 1,598 units at a 117.50 limit.</td><td class="l warn"><span>competes with the resting ATOs at the open</span></td></tr>
</tbody></table></div>
<p class="note"><strong>GLAND is the three-stops problem turning into money.</strong> One name, three
accounts, three levels &mdash; 3,233.10, 3,268.50, and a scan that said 3,307.20 on Monday night. The
middle one fired and the other two are fifteen rupees away. <strong>It needs one number.</strong></p>

<h3 class="sub" id="pre-scan">The scan &mdash; 24 actionable, none of them placeable</h3>
<p>Run by hand tonight against Tuesday&rsquo;s closes. <strong>SWING run 466: 614 candidates, 24
actionable, six of them a clean 8/8.</strong> Every other scanner returned <strong>zero</strong> &mdash;
WEEKLY 467 (574 candidates), ETF 468 (20), ETF_WEEKLY 469 (21) and REVERSAL 471 (397). STRIKE 470 returns
the identical 24 and is not a traded strategy.</p>
<p class="sub">That the weekly book is empty for a second night while the daily list stays full is the same
tell as Monday: one- and two-day breakouts with no sustained leadership underneath them.</p>
<p class="sub">Distance from Tuesday&rsquo;s close to the trigger. Nothing fires unless the name travels this far; green is inside 1.5%, amber is 3.5% or more. <strong>With both gates shut none of it may be bought &mdash; this is what is being refused, drawn.</strong></p>
<svg viewBox="0 0 470 342" width="100%" style="max-width:640px" role="img" aria-label="How far each actionable setup sits below its trigger, Tuesday 17 November close"><text x="0" y="9" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PVRINOX</text><rect x="92" y="1" width="68.3" height="9" rx="2" fill="var(--green)"/><text x="166.3" y="9" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.0%</text><text x="0" y="23" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ISFT</text><rect x="92" y="15" width="68.3" height="9" rx="2" fill="var(--green)"/><text x="166.3" y="23" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.0%</text><text x="0" y="37" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">TFCILTD</text><rect x="92" y="29" width="75.1" height="9" rx="2" fill="var(--green)"/><text x="173.1" y="37" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.1%</text><text x="0" y="51" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KARURVYSYA</text><rect x="92" y="43" width="88.8" height="9" rx="2" fill="var(--green)"/><text x="186.8" y="51" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.3%</text><text x="0" y="65" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GCSL</text><rect x="92" y="57" width="102.4" height="9" rx="2" fill="var(--green)"/><text x="200.4" y="65" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.5%</text><text x="0" y="79" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">MCX</text><rect x="92" y="71" width="136.6" height="9" rx="2" fill="var(--series-1)"/><text x="234.6" y="79" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.0%</text><text x="0" y="93" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LENSKART</text><rect x="92" y="85" width="143.4" height="9" rx="2" fill="var(--series-1)"/><text x="241.4" y="93" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.1%</text><text x="0" y="107" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GRAPHITE</text><rect x="92" y="99" width="143.4" height="9" rx="2" fill="var(--series-1)"/><text x="241.4" y="107" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.1%</text><text x="0" y="121" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">TIMEX</text><rect x="92" y="113" width="163.9" height="9" rx="2" fill="var(--series-1)"/><text x="261.9" y="121" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.4%</text><text x="0" y="135" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LOTUSDEV</text><rect x="92" y="127" width="170.8" height="9" rx="2" fill="var(--series-1)"/><text x="268.8" y="135" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.5%</text><text x="0" y="149" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHYAMMETL</text><rect x="92" y="141" width="184.4" height="9" rx="2" fill="var(--series-1)"/><text x="282.4" y="149" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.7%</text><text x="0" y="163" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SAMBHV</text><rect x="92" y="155" width="184.4" height="9" rx="2" fill="var(--series-1)"/><text x="282.4" y="163" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.7%</text><text x="0" y="177" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">LTTS</text><rect x="92" y="169" width="198.1" height="9" rx="2" fill="var(--series-1)"/><text x="296.1" y="177" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.9%</text><text x="0" y="191" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PTCIL</text><rect x="92" y="183" width="211.7" height="9" rx="2" fill="var(--series-1)"/><text x="309.7" y="191" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.1%</text><text x="0" y="205" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PAYTM</text><rect x="92" y="197" width="218.6" height="9" rx="2" fill="var(--series-1)"/><text x="316.6" y="205" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.2%</text><text x="0" y="219" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHUKRAPHAR</text><rect x="92" y="211" width="225.4" height="9" rx="2" fill="var(--series-1)"/><text x="323.4" y="219" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.3%</text><text x="0" y="233" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">UTTAMSUGAR</text><rect x="92" y="225" width="225.4" height="9" rx="2" fill="var(--series-1)"/><text x="323.4" y="233" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.3%</text><text x="0" y="247" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">BMWVENTLTD</text><rect x="92" y="239" width="239.0" height="9" rx="2" fill="var(--amber)"/><text x="337.0" y="247" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.5%</text><text x="0" y="261" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SBC</text><rect x="92" y="253" width="239.0" height="9" rx="2" fill="var(--amber)"/><text x="337.0" y="261" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.5%</text><text x="0" y="275" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">DIVISLAB</text><rect x="92" y="267" width="252.7" height="9" rx="2" fill="var(--amber)"/><text x="350.7" y="275" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.7%</text><text x="0" y="289" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">TAMBOLIIN</text><rect x="92" y="281" width="266.4" height="9" rx="2" fill="var(--amber)"/><text x="364.4" y="289" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.9%</text><text x="0" y="303" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SONACOMS</text><rect x="92" y="295" width="280.0" height="9" rx="2" fill="var(--amber)"/><text x="378.0" y="303" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.1%</text><text x="0" y="317" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GLOBAL</text><rect x="92" y="309" width="293.7" height="9" rx="2" fill="var(--amber)"/><text x="391.7" y="317" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.3%</text><text x="0" y="331" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RATNAVEER</text><rect x="92" y="323" width="314.2" height="9" rx="2" fill="var(--amber)"/><text x="412.2" y="331" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.6%</text></svg>

<p class="note"><strong>This table and the report&rsquo;s own TIS table below it are not the same
list, and neither is wrong.</strong> This one is the scanner&rsquo;s twenty-four <em>actionable</em> names.
The report&rsquo;s table ranks by what it would deploy and prints twenty-five, which includes four the scan
refused &mdash; SHIVAUM, NITINSPIN, CENTUM and CPPLUS &mdash; and leaves out three it passed: GLOBAL,
GRAPHITE and PTCIL. <strong>Read the gates column, not the row count.</strong> Note also that six names
score 8/8 here while the report marks four of them &ldquo;blocked by G5&rdquo;: <b>G5 is the sector
rotation note, which records where money is going and refuses nothing.</b> On the scanner&rsquo;s own
verdict the six clean 8/8s are TFCILTD, MCX, RATNAVEER, SONACOMS, DIVISLAB and LOTUSDEV.</p>
<p class="note">Per-name price charts for all of these are in <a href="2026-11-17.html">Tuesday&rsquo;s
report</a>, alongside the sector pass, RRG quadrant, industry rank and volume columns this table leaves out.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>gates</th><th>RS</th><th>chop</th><th>entry</th><th>SL</th><th>stop%</th><th>to entry</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>SHUKRAPHAR</b></td><td>7/8</td><td>98</td><td>81%</td><td>84.97</td><td>81.06</td><td>4.6%</td><td>+3.3%</td><td class="l">held &middot; sector LEADING</td></tr>
<tr><td class="l"><b>RATNAVEER</b></td><td class="pass">8/8</td><td>97</td><td>86%</td><td>375.95</td><td>356.50</td><td>5.2%</td><td>+4.6%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>TFCILTD</b></td><td class="pass">8/8</td><td>97</td><td>85%</td><td>168.01</td><td>160.76</td><td>4.3%</td><td>+1.1%</td><td class="l">resting at 172.34 &mdash; <b>above tonight&rsquo;s entry</b></td></tr>
<tr><td class="l"><b>SBC</b></td><td>7/8</td><td>97</td><td>75%</td><td>71.43</td><td>67.80</td><td>5.1%</td><td>+3.5%</td><td class="l">held, all three</td></tr>
<tr><td class="l"><b>TAMBOLIIN</b></td><td>7/8</td><td>95</td><td>81%</td><td>338.48</td><td>320.00</td><td>5.5%</td><td>+3.9%</td><td class="l">7.8% ADR &mdash; wild</td></tr>
<tr><td class="l"><b>GCSL</b></td><td>7/8</td><td>94</td><td>87%</td><td>841.63</td><td>816.60</td><td>3.0%</td><td>+1.5%</td><td class="l">held &middot; sector LEADING</td></tr>
<tr><td class="l"><b>TIMEX</b></td><td>7/8</td><td>94</td><td>75%</td><td>756.46</td><td>715.55</td><td>5.4%</td><td>+2.4%</td><td class="l">new &middot; sector LEADING</td></tr>
<tr><td class="l"><b>GLOBAL</b></td><td>7/8</td><td>93</td><td>74%</td><td>151.39</td><td>143.00</td><td>5.5%</td><td>+4.3%</td><td class="l">actionable in the scan; no row in the report&rsquo;s table below</td></tr>
<tr><td class="l"><b>SONACOMS</b></td><td class="pass">8/8</td><td>92</td><td>75%</td><td>936.77</td><td>888.20</td><td>5.2%</td><td>+4.1%</td><td class="l">held</td></tr>
<tr><td class="l"><b>LOTUSDEV</b></td><td class="pass">8/8</td><td>91</td><td>71%</td><td>238.48</td><td>225.65</td><td>5.4%</td><td>+2.6%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>DIVISLAB</b></td><td class="pass">8/8</td><td>90</td><td>83%</td><td>11,567.59</td><td>10,954.00</td><td>5.3%</td><td>+3.7%</td><td class="l">new &mdash; a large-cap on this list is unusual</td></tr>
<tr><td class="l"><b>MCX</b></td><td class="pass">8/8</td><td>90</td><td>51%</td><td>3,780.15</td><td>3,586.00</td><td>5.1%</td><td>+2.0%</td><td class="l">held &mdash; chop 51%, low for an 8/8</td></tr>
<tr><td class="l"><b>SAMBHV</b></td><td>7/8</td><td>90</td><td>82%</td><td>168.44</td><td>159.62</td><td>5.2%</td><td>+2.7%</td><td class="l">new</td></tr>
<tr><td class="l"><b>UTTAMSUGAR</b></td><td>7/8</td><td>90</td><td>63%</td><td>377.15</td><td>361.30</td><td>4.2%</td><td>+3.3%</td><td class="l">new</td></tr>
<tr><td class="l"><b>PVRINOX</b></td><td>7/8</td><td>89</td><td>90%</td><td>1,693.38</td><td>1,620.20</td><td>4.3%</td><td>+1.0%</td><td class="l">held &middot; closest to its trigger</td></tr>
<tr><td class="l"><b>ISFT</b></td><td>7/8</td><td>82</td><td>69%</td><td>120.14</td><td>117.00</td><td>2.6%</td><td>+1.0%</td><td class="l">new &mdash; tightest stop on the list</td></tr>
<tr><td class="l"><b>KARURVYSYA</b></td><td>7/8</td><td>77</td><td>71%</td><td>398.65</td><td>378.20</td><td>5.1%</td><td>+1.3%</td><td class="l">new &mdash; a bank, and banks are the clean sector</td></tr>
<tr><td class="l"><b>LENSKART</b></td><td>7/8</td><td>89</td><td>80%</td><td>754.26</td><td>716.30</td><td>5.0%</td><td>+2.1%</td><td class="l">held &middot; MS buy watchlist</td></tr>
<tr><td class="l"><b>GRAPHITE</b></td><td>7/8</td><td>78</td><td>57%</td><td>809.32</td><td>764.15</td><td>5.6%</td><td>+2.1%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td>7/8</td><td>87</td><td>65%</td><td>1,356.71</td><td>1,292.90</td><td>4.7%</td><td>+2.7%</td><td class="l">resting at 1,356.01, all three &mdash; analyst meet Wednesday</td></tr>
<tr><td class="l"><b>LTTS</b></td><td>7/8</td><td>79</td><td>59%</td><td>4,328.24</td><td>4,105.00</td><td>5.2%</td><td>+2.9%</td><td class="l">resting at 4,356.09 &mdash; <b>above tonight&rsquo;s entry</b></td></tr>
<tr><td class="l"><b>PTCIL</b></td><td>7/8</td><td>89</td><td>63%</td><td>24,699.30</td><td>23,220.00</td><td>6.0%</td><td>+3.1%</td><td class="l">resting, all three &middot; stop 6.0% breaks the 5% cap</td></tr>
<tr><td class="l"><b>PAYTM</b></td><td>7/8</td><td>89</td><td>75%</td><td>1,963.92</td><td>1,872.20</td><td>4.7%</td><td>+3.2%</td><td class="l">held &middot; <b>MS added it to the model portfolio today at 1,900</b></td></tr>
<tr><td class="l"><b>BMWVENTLTD</b></td><td>7/8</td><td>72</td><td>35%</td><td>66.96</td><td>63.50</td><td>5.2%</td><td>+3.5%</td><td class="l">held &mdash; chop 35%, the least reliable on the list</td></tr>
</tbody></table></div>
<p class="note"><strong>Four resting triggers now sit above the price the scan derives tonight.</strong>
TFCILTD rests at 172.34 against a fresh 168.01, LTTS at 4,356.09 against 4,328.24, RUBICON at 1,777.45
against 1,750.39 and CPPLUS at 4,338.66 against 4,123.23. None is wrong &mdash; each was derived on an
earlier scan &mdash; but all four will buy later and higher than tonight&rsquo;s read says they should. The same drift is what left GLAND on three different stops.</p>
<p class="note"><strong>RUBICON answers a question that has been open three nights.</strong> It is no longer
absent from the scan: <b>7/8, RS 96, EPS +83% QoQ, entry 1,750.39, stop 1,650.50, +3.95% away</b> &mdash; figures from the SWING refusal list, which the report does not print, so there is no RUBICON row in the table below to check them against. It fails
exactly one gate &mdash; <b>G3, the momentum gate</b>, on +5% in 30 days and +20% in 90. That is the gate this
book measured and found admits 4.4% of the population for +0.34 points of return at <b>p = 0.43</b>, with the
sign flipping between periods. <strong>The only thing standing between RUBICON and the actionable list is the
one gate we know buys nothing</strong> &mdash; while MarketSmith names it a leader and carries it on the buy
watchlist, and our own order rests at 1,777.45, above tonight&rsquo;s entry. <b>CPPLUS</b> is refused by the
same gate on the same evidence: RS 96, EPS +304% QoQ, entry 4,123.23 against a resting 4,338.66.</p>

<h3 class="sub" id="pre-news">News on every live name</h3>
<p class="sub">Searched by hand tonight across all held positions and every name within reach of a
trigger. Where nothing was found it says nothing was found.</p>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what was found</th><th class="l">what it changes</th></tr></thead><tbody>
<tr><td class="l"><b>SHUKRAPHAR</b></td><td class="l">NSE approved a name and symbol change to <b>Shukra Medtech, symbol SHUKRAMED, effective Friday 20 November</b> (approval 16 Nov).</td><td class="l fail"><span>ACTION &mdash; held in all three; the ticker breaks in three sessions</span></td></tr>
<tr><td class="l"><b>GLAND</b></td><td class="l"><b>No disclosed catalyst for the 4.06% fall.</b> No block deal, no MSCI or Nifty change, no USFDA item, no downgrade dated 17 Nov; results were 6 Nov. It fell on ~4.1 lakh shares while the Sensex rose 427 points <em>and Nifty Pharma was up</em>. The likeliest cause is the <b>16 November CDMO de-rating</b> &mdash; Laurus &minus;10% intraday, Sai Life &minus;7.4%, Divi&rsquo;s &minus;4% on a Jefferies CRDMO note &mdash; reaching Gland a day late.</td><td class="l fail"><span>an unexplained distribution day, one session off its high</span></td></tr>
<tr><td class="l"><b>KRISHANA</b></td><td class="l">Closed <b>flat on Tuesday, &minus;0.05% at 243</b>. The earnings call is <b>confirmed for Wednesday 18 Nov at 12:00</b>, intimated 11 Nov. Q2 PAT 77.86 Cr, +134.73%.</td><td class="l warn"><span>the loss is against our cost, not a Tuesday move &mdash; it is sell-the-news after a run off 101.80</span></td></tr>
<tr><td class="l"><b>AARTIPHARM</b></td><td class="l">Promoter and Chairman Emeritus <b>died 15 November</b> and ceases to be a promoter; a holding reclassification should follow. Also sits in the CDMO cohort marked down on the 16th.</td><td class="l warn"><span>held &mdash; expect a SAST filing</span></td></tr>
<tr><td class="l"><b>PAYTM</b></td><td class="l"><b>RBI granted in-principle authorisation</b> to issue prepaid instruments and wallets, 13 Nov. Conditional, not full clearance.</td><td class="l pass"><span>held &middot; and MarketSmith added it at 1,900 today</span></td></tr>
<tr><td class="l"><b>PVRINOX</b></td><td class="l">Two outlook upgrades to Positive &mdash; India Ratings 13 Nov, <b>CRISIL 17 Nov</b>. 52-week high intraday Tuesday.</td><td class="l pass"><span>held &middot; closest name to its trigger</span></td></tr>
<tr><td class="l"><b>ROSSTECH</b></td><td class="l">SAST disclosure 17 Nov: <b>SBI Mutual Fund crossed 5%</b> (5.7503%) through the 299.99 Cr preferential allotment at 1,166.</td><td class="l pass"><span>held</span></td></tr>
<tr><td class="l"><b>ISFT</b></td><td class="l">SAST 17 Nov &mdash; an acquirer group went <b>13.69% to 15.71%</b>. The stock is <b>circuit-prone</b>: upper circuit 9 Nov, 52-week high 13 Nov then a lower-circuit close the same day, and NSE sought a price-movement clarification in September.</td><td class="l warn"><span>second-closest to a trigger, on a 2.6% stop &mdash; a circuit either side makes that stop theoretical</span></td></tr>
<tr><td class="l"><b>TFCILTD</b></td><td class="l"><b>Exchange sought a clarification on volume and price movement, 12 Nov</b>; the company replied it holds no undisclosed information.</td><td class="l warn"><span>resting in all three &mdash; surveillance-adjacent at an all-time high</span></td></tr>
<tr><td class="l"><b>SBC</b></td><td class="l">Nothing in the window. Standing, not new: <b>41.55% of the promoter holding is pledged</b>, up 1.57 points in the September quarter.</td><td class="l warn"><span>held in all three</span></td></tr>
<tr><td class="l"><b>CUPID</b></td><td class="l">All-time high 13 Nov then &minus;4.5% on the 16th; brokers call it profit-booking with no company trigger. Q2 PAT +133%, FY27 guidance raised.</td><td class="l"><span>held</span></td></tr>
<tr><td class="l"><b>SGMART</b></td><td class="l">Six-session run to all-time highs with <b>no announcement behind it</b>.</td><td class="l warn"><span>held &mdash; an unexplained vertical move</span></td></tr>
<tr><td class="l"><b>ISFT</b> &amp; <b>GLOBAL</b></td><td class="l"><b>Both are on ESM Stage 1 and both trade in series BE &mdash; trade-for-trade.</b> Every trade settles by delivery: <b>no intraday, no BTST</b>, and tight price bands. Neither was on any watch list; this was found by pulling NSE&rsquo;s own surveillance file.</td><td class="l fail"><span>ISFT is the second-closest name to a trigger, on a 2.6% stop &mdash; T2T plus circuits makes that stop theoretical</span></td></tr>
<tr><td class="l"><b>TFCILTD</b></td><td class="l">On <b>long-term ASM Stage I since 3 November</b>, series EQ &mdash; nine days <em>before</em> the volume clarification, so the two are separate events and the ASM came first. The exchange query was on <b>volume</b>, not price; the company replied the move is market-driven with nothing undisclosed.</td><td class="l warn"><span>resting in all three &mdash; ASM I is the mild tier, so still placeable, but it is a flag on a name the whole book is sized into</span></td></tr>
<tr><td class="l"><b>CUPID</b>, <b>GCSL</b>, <b>SSWL</b></td><td class="l">All three on <b>long-term ASM Stage I</b>, series EQ.</td><td class="l warn"><span>held in all three accounts</span></td></tr>
<tr><td class="l">TAMBOLIIN</td><td class="l"><b>Clear</b>, against expectation &mdash; its last measure expired in May. A 7.8% daily range on a 299 Cr company is not, by itself, a surveillance flag.</td><td class="l pass"><span>&mdash;</span></td></tr>
<tr><td class="l">SONACOMS &middot; MCX &middot; LENSKART &middot; GCSL &middot; SSWL &middot; BMWVENTLTD &middot; GRAPHITE &middot; DIVISLAB &middot; KARURVYSYA &middot; TIMEX</td><td class="l">Nothing material in the last five sessions. LENSKART&rsquo;s FII holding rose to 18.26% from 12.76% in the September quarter; BMWVENTLTD went ex-dividend 13 Nov.</td><td class="l pass"><span>&mdash;</span></td></tr>
</tbody></table></div>
<p class="note"><strong>Surveillance was pulled in the end, from NSE&rsquo;s own daily indicator file
&mdash; 570 flagged symbols, dated 16 November.</strong> All twenty-four names were checked, and the
seventeen not named above are clear as of that file: GLAND, KRISHANA, SONACOMS, SBC, SHUKRAPHAR,
AARTIPHARM, LENSKART, MCX, PAYTM, PVRINOX, ROSSTECH, SGMART, BMWVENTLTD, RATNAVEER, SHYAMMETL, LTTS and
PTCIL. <strong>Two caveats that matter.</strong> The file is <b>Monday&rsquo;s</b>, so a measure imposed
effective Tuesday would not appear in it. And while the ASM rows are double-sourced, <b>the ESM and
trade-for-trade columns come from that one file</b> &mdash; Trendlyne does not track ESM at all and
reported ISFT as clear, which is true of ASM and would have read as a clean bill. <strong>Confirm ISFT
and GLOBAL on a second source before acting on them.</strong> The 17 November bulk and block tape was
still not published anywhere.</p>
<p class="note"><strong>What Tuesday&rsquo;s index closes say, and it is the same thing this page&rsquo;s
index table says.</strong> Nifty closed <b>25,387.40, +0.38%</b>, the Sensex +427 points, <b>Nifty Bank
at a record high</b> &mdash; while <b>Smallcap 100 fell 0.22%</b> and IT fell 0.90%. Monday was the same
shape: Sensex +512 while smallcaps fell over a point. <strong>Two consecutive sessions of large-caps up
and smallcaps down</strong>, with foreign money going into the benchmarks and our gate reading the
market underneath them.</p>
<p class="note"><strong>Overnight, and it is the real risk on this page.</strong> <b>Nvidia had not
reported at the time of writing</b> &mdash; its quarter lands around 02:50 IST, before our open, with
options implying a move near 8%. <b>It is the first Nvidia report in the company&rsquo;s history without
Jensen Huang</b>, who resigned on 12 November; the CFO hosts the call as interim chief executive. Nvidia
closed Monday at its lowest since July 2025 after a third straight fall. Separately, <strong>the Fed is
hiking, not cutting</strong> &mdash; the December move was priced near certainty &mdash; Brent is about
$92.76 and the dollar index sits at a nineteen-month high. <strong>Any GIFT Nifty level quoted on this
page was read before all of that and carries almost no information about Wednesday.</strong></p>

<h3 class="sub" id="pre-flows">Who is actually buying &mdash; FII and DII</h3>
<p class="sub">Net cash-market flows in &#8377; crore, to Tuesday 17 November.</p>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>FII net</th><th>DII net</th><th>FII buy</th><th>FII sell</th></tr></thead><tbody>
<tr><td class="l"><b>Tue 17 Nov</b></td><td class="pass">+4,195</td><td class="pass"><b>+197</b></td><td>19,931</td><td>15,736</td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="pass">+4,865</td><td class="bad">&minus;3,519</td><td>15,637</td><td>10,772</td></tr>
<tr><td class="l">Fri 13 Nov</td><td class="pass">+5,737</td><td class="bad">&minus;2,254</td><td>18,340</td><td>12,603</td></tr>
<tr><td class="l">Thu 12 Nov</td><td class="pass">+7,831</td><td class="bad">&minus;6,331</td><td>20,273</td><td>12,443</td></tr>
<tr><td class="l">Wed 11 Nov</td><td class="pass">+12,563</td><td class="bad">&minus;8,435</td><td>30,087</td><td>17,524</td></tr>
</tbody></table></div>
<p class="note"><strong>The mechanic broke today.</strong> Yesterday&rsquo;s page said foreign money had
bought every session this week while domestic money sold every session, and that this was what produced a
rising index on falling breadth. <strong>On Tuesday the DIIs turned net buyers &mdash; +&#8377;197 Cr, the
first positive domestic print of the week.</strong> It is a small number and one session, so it is a crack
rather than a turn. But the explanation the last page leaned on no longer describes the tape, and it is
worth saying that plainly rather than repeating it. Breadth did not improve on the same day, which is the
part that does not fit yet.</p>

<h3 class="sub" id="pre-breadth">Breadth, two sessions into the shut gate</h3>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>above their 20MA</th><th>prior-5 mean</th><th class="l">breadth gate</th></tr></thead><tbody>
<tr><td class="l"><b>Tue 17 Nov</b></td><td class="bad">65.79%</td><td>69.65%</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="bad">65.11%</td><td>69.42%</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Fri 13 Nov</td><td>74.94%</td><td>65.42%</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Thu 12 Nov</td><td>75.95%</td><td>62.65%</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Wed 11 Nov</td><td>70.31%</td><td>59.22%</td><td class="l pass"><span>open</span></td></tr>
</tbody></table></div>
<p class="note"><strong>Breadth stopped falling &mdash; it went up, from 65.11% to 65.79% &mdash; and the
gate is still shut.</strong> That is the mean catching up rather than the market deteriorating: the
prior-five average is still climbing, from 69.42% to 69.65%, because it is still dropping last week&rsquo;s
seventies out of the window. The gate opens when breadth crosses back over the mean, and on these two
numbers that needs roughly four more points. It is worth knowing that the gate can now shut on a day the
market improved.</p>

<h3 class="sub" id="pre-funding">Can the book pay for what it has already ordered?</h3>
<div class="scroll"><table><thead><tr><th class="l">account</th><th>free cash</th><th>parking it can sell</th><th>resting orders</th><th class="l">covered?</th></tr></thead><tbody>
<tr><td class="l">t-default</td><td>1,87,863 <span class="muted">&mdash; queued into parking</span></td><td>26,785 units &asymp; 31,32,238</td><td>24,50,238</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">akul</td><td>18,974</td><td>2,818 units &asymp; 3,29,497</td><td>2,12,072</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">t-ramprasad</td><td>1,87,619</td><td>&mdash; none</td><td>4,27,130</td><td class="l fail"><span>NO &mdash; short 2,39,511</span></td></tr>
</tbody></table></div>
<p class="note"><strong>t-default&rsquo;s free cash was queued into the parking fund tonight at his
instruction</strong> &mdash; 1,598 LIQUIDCASE at a 117.50 limit, as an after-market order. The tool itself
declined to do it: <code>park_cash</code> reports zero idle cash in all three accounts, because it subtracts
what is already committed to live entry orders, and every account is committed well past its cash. The
expected consequence at the open is that the parking buy takes the cash first, the entry triggers are
refused for funds, and the reactive rule sells parking back to fund them. <strong>t-ramprasad is still the
one that cannot be fixed that way</strong> &mdash; it holds no parking. Its position improved today only
because its owner sold two legacy holdings by hand.</p>

<h3 class="sub" id="pre-diary">The diary</h3>
<div class="scroll"><table><thead><tr><th class="l">when</th><th class="l">event</th><th class="l">why it matters</th></tr></thead><tbody>
<tr><td class="l"><b>Wed 18 Nov, pre-open</b></td><td class="l"><b>Nvidia&rsquo;s quarter</b>, due after Tuesday&rsquo;s US close &mdash; not yet reported when this was written</td><td class="l">It lands near 02:50 IST, before our open, with options implying a move near 8% &mdash; and it is the first Nvidia report without Jensen Huang, who resigned on 12 November. The stock fell 4.1% on Monday to its lowest close since July 2025, and Monday&rsquo;s Nasdaq was &minus;2.49%. IT already carries eight distribution days, the most of any index we track.</td></tr>
<tr><td class="l">Wed 18 Nov, 12:00</td><td class="l">KRISHANA earnings call</td><td class="l">A call, not a results date &mdash; results were filed 14 Nov with PAT up ~135%. But it is held in all three accounts, sitting under its pivot at &minus;4.36%, and the scanner can no longer find a base in it.</td></tr>
<tr><td class="l">Wed 18 Nov</td><td class="l">SHYAMMETL analyst meet</td><td class="l">Resting at 1,356.01 in all three; tonight&rsquo;s entry is 1,356.71.</td></tr>
<tr><td class="l">18&ndash;20 Nov</td><td class="l"><b>Crystal Crop Protection IPO opens</b></td><td class="l">&#8377;259&ndash;272, ~&#8377;455 Cr. <b>AVOID on the case</b> &mdash; but the anchor book filed at 18:55 is better than the premium implied: &#8377;135.96 Cr, 17 investors at the top of the band, 44.28% domestic mutual funds. See the IPO review.</td></tr>
<tr><td class="l">19&ndash;23 Nov</td><td class="l">Mahanadi Coalfields IPO</td><td class="l">&#8377;129&ndash;136, &#8377;8,981 Cr, 100% offer-for-sale by Coal India. <b>SKIP</b> as a trade.</td></tr>
</tbody></table></div>

<h3 class="sub" id="pre-decisions">Waiting on a decision</h3>
<ul>
<li><strong>GLAND needs one stop number, and it is now urgent.</strong> 3,233.10 in t-default and akul,
3,268.50 in t-ramprasad &mdash; which <em>fired today</em> &mdash; and Monday&rsquo;s scan said 3,307.20.
The two surviving positions close 0.47% above their stop. <b>69 and 7 shares are exposed to any gap
down.</b></li>
<li><strong>RUBICON, and the G3 gate behind it.</strong> No longer absent: 7/8, RS 96, EPS +83% QoQ,
refused only by a gate measured at p = 0.43. The same gate refuses CPPLUS at RS 96 and EPS +304%. This is
no longer a question about one stock.</li>
<li><strong>Two resting triggers are above tonight&rsquo;s derived entries</strong> &mdash; TFCILTD 172.34
against 168.01, LTTS 4,356.09 against 4,328.24. Re-rest or leave them to buy higher.</li>
<li><strong>Fund t-ramprasad or stand its orders down.</strong> &#8377;4,27,130 resting against
&#8377;1,87,619 and no parking to sell.</li>
<li><strong><code>evening-scan</code> has still not succeeded since 30 October</strong> &mdash; eighteen
days against a 30-hour budget, last error UNKNOWN. Every scan on this page was run by hand.
<code>build-daily-report-morning</code>, broken three days running, <b>recovered this morning</b> and ran
green at 09:30.</li>
<li><strong><code>show_ipos</code> still cannot read its source</strong> &mdash; the IPO board is rebuilt by
hand again tonight.</li>
</ul>
<p class="note">Built Tuesday 17 November 2026 from the service&rsquo;s records, a live read of all three
brokers, tonight&rsquo;s hand-run scans (SWING 466, WEEKLY 467, ETF 468, ETF_WEEKLY 469, STRIKE 470,
REVERSAL 471), the 17-index distribution-day count, recorded FII/DII flows and NSE filings. Closes are
Tuesday&rsquo;s. Nothing here places an order.</p>
"""


PREMARKET_2026_11_19 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Thursday opens with <strong>one gate open and the other at its worst reading of the
move</strong>. Our follow-through gate flipped to <strong>CONFIRMED_UPTREND</strong> and now agrees with
MarketSmith for the first time in six sessions &mdash; but it did so on a <strong>follow-through dated 2
November, sixteen days old</strong>. Meanwhile breadth fell to <strong>59.52% against a prior-five mean of
70.35%</strong>, a gap of 10.83 points against Tuesday&rsquo;s 3.86. <strong>Entries remain blocked, on
breadth, and none of tonight&rsquo;s thirty-three actionable names may be placed.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes are
Wednesday 18 November&rsquo;s. All six scanners were run by hand tonight against them &mdash; SWING run 479.</p>
<p class="note"><strong>Read the open gate carefully.</strong> A gate that turns green on a sixteen-day-old
event while the breadth it is meant to confirm collapses is not a buy signal, it is a lag. The two readings
are measuring different things: the follow-through looks backwards at one day in early November, breadth
looks at what 877 names did on Wednesday. <strong>On this evidence the breadth gate is the one carrying
information.</strong></p>

<h3 class="sub" id="pre-corrections">Two things this book got wrong, corrected</h3>
<div class="scroll"><table><thead><tr><th class="l">what was said</th><th class="l">what is true</th></tr></thead><tbody>
<tr><td class="l">The 18th&rsquo;s page said the <b>&ldquo;foreign buying against domestic selling&rdquo; mechanic had BROKEN</b>, because the DIIs printed +&#8377;197 Cr on the 17th &mdash; their first positive session of the week.</td><td class="l fail"><b>It had not broken. I over-read a single session.</b> On the 18th domestic selling resumed harder: <b>DII &minus;&#8377;3,159.90 Cr</b> against <b>FII +&#8377;5,866.78 Cr</b>, with foreign buying unbroken across every session in the table below. One print is not a turn, and it was called one.</td></tr>
<tr><td class="l">Wednesday evening&rsquo;s first scan ran at 16:16 and reported <b>24 actionable</b>.</td><td class="l fail"><b>It was priced off the 17th.</b> The bhavcopy had not been ingested, so a run stamped 18 November carried 17 November prices &mdash; TFCILTD&rsquo;s &ldquo;last&rdquo; read 166.16 when the close was <b>169.69</b>. Caught before publishing, all six re-run, and the real count is <b>33</b>. The tell was twenty-four <em>identical</em> distance-to-trigger figures against the previous page.</td></tr>
</tbody></table></div>
<p class="note"><strong>Three things further down this page are wrong, and all three are machine-built,
not written here.</strong> <b>&ldquo;IPOs &mdash; mainboard&rdquo; says no mainboard issue is open or
upcoming</b> &mdash; false, Mahanadi opens today and Crystal is mid-subscription; that is the broken
<code>show_ipos</code> parser, and the hand-written IPO review lower down is the one to read. <b>&ldquo;How
the market opened&rdquo; carries Wednesday&rsquo;s pre-open</b>, quoted 18 Nov 08:57 with GIFT Nifty at
25,243 &mdash; it cannot carry Thursday&rsquo;s, because this page is written the evening before. And the
<b>breadth history repeats 9 and 10 November identically</b> at 62.60% / 54.22%, which looks like a carried
row rather than two sessions; since that history feeds the prior-five mean the gate is judged against,
<strong>it is on the decisions list below</strong>.</p>
<p class="note">The second one is worth keeping. <strong>A scan stamped with today&rsquo;s date can still be
priced off yesterday</strong>, and the only reliable check is to compare one known name&rsquo;s last price
against that day&rsquo;s close. Had it shipped, TFCILTD would have carried a stop of 160.76 instead of
<b>165.24</b> &mdash; four and a half rupees too low, roughly &#8377;12,000 of extra risk on one name
&mdash; and nine setups would have been missing.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l"><b>59.52% against 70.35%</b> on 877 names &mdash; a 10.83-point gap, against 3.86 on Tuesday</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">CONFIRMED_UPTREND &mdash; follow-through on the Nifty at <b>2 November</b>, despite 8 distribution days on smallcap</td><td class="l pass"><span>OPEN</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED_UPTREND, 2 distribution days &mdash; <b>agreeing with ours for the first time in six sessions</b></td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Nifty vs its 20MA</td><td class="l">+4.92%, down from +6.08% &mdash; the index gave ground on Wednesday</td><td class="l"><span>less extended</span></td></tr>
</tbody></table></div>

<h3 class="sub" id="pre-indices">What deteriorated on Wednesday &mdash; three sectors downgraded</h3>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">status</th><th class="l">change today</th></tr></thead><tbody>
<tr><td class="l"><b>METAL</b></td><td class="bad">6</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail">was UNDER PRESSURE on 3 &mdash; <b>downgraded twice in two sessions</b></td></tr>
<tr><td class="l"><b>ENERGY</b></td><td class="bad">4</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l warn">was CONFIRMED UPTREND on 2</td></tr>
<tr><td class="l"><b>CONSUMER DURABLES</b></td><td>3</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l warn">was CONFIRMED UPTREND on <b>zero</b></td></tr>
<tr><td class="l">NEXT 50</td><td class="bad">4</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l warn">was 1 &mdash; picked up three in a session</td></tr>
<tr><td class="l"><b>SMALLCAP</b></td><td class="bad">8</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail">was 7 &mdash; still the only broad index not confirmed</td></tr>
<tr><td class="l">IT</td><td class="bad">8</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">unchanged &mdash; joint-most distributed with smallcap, both on 8</td></tr>
<tr><td class="l">NIFTY &middot; BANK &middot; PSU BANK</td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">unchanged &mdash; clean</td></tr>
</tbody></table></div>
<p class="note"><strong>This is the part the open follow-through gate does not see.</strong> Three sectors
were downgraded in a single session and the Next 50 took three distribution days. The Nifty, the banks and
the PSU banks remain spotless. <strong>The index is not the market, and the gap between them widened
again on Wednesday.</strong></p>

<h3 class="sub" id="pre-today">What Wednesday did</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l"><b>GLAND</b></td><td class="l">The 3,233.10 stop fired at 09:15:58 on a weak open. t-default sold 69 at an average of <b>3,221.86</b>, akul 7 at <b>3,224.34</b> &mdash; both about eleven rupees <em>below</em> the stop. It then recovered to &#8377;3,249 by 11:32.</td><td class="l fail"><span>&minus;&#8377;11,739.66 and &minus;&#8377;1,173.62</span></td></tr>
<tr><td class="l"><b>GLAND</b>, all three</td><td class="l">With Ram&rsquo;s 25 stopped on the 17th at &minus;&#8377;2,923.60, the name is closed everywhere. <b>And it is back on tonight&rsquo;s list at 8/8</b>, entry 3,402.69, stop 3,208.70.</td><td class="l fail"><span><b>&minus;&#8377;15,836.88 across the book</b></span></td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td class="l">Fired at 09:15:49 and filled in <b>t-ramprasad only</b> &mdash; 38 at 1,359.92, adopted and stopped at 1,292.90. It ran to a high of <b>1,381.9</b>, well through its 1,356.01 trigger, then closed <b>1,317.1</b>. Rejected for funds in the other two.</td><td class="l warn"><span>&minus;&#8377;1,627 unrealised on the close; the 1,305.2 low came within <b>0.9%</b> of the stop</span></td></tr>
<tr><td class="l"><b>SHYAMMETL</b>, the decision</td><td class="l">A genuine breakout that failed inside the hour, on a name failing two gates. The other two legs were re-rested, then <b>cancelled on his call</b>.</td><td class="l"><span>held in Ram only &mdash; the accounts diverge by decision</span></td></tr>
<tr><td class="l">Both rejections</td><td class="l"><b>Phantom.</b> Dead reservations left by the very orders the broker had refused. <code>retire_intents</code> released <b>&#8377;214,250</b> in t-default and <b>&#8377;23,052</b> in akul, and the re-placement went through with <b>no parking sold at all</b>.</td><td class="l pass"><span>a cash problem that was not a cash problem</span></td></tr>
<tr><td class="l">Parking</td><td class="l">Free cash parked across all three at 116.98 &mdash; 3,380, 342 and <b>1,794</b> units.</td><td class="l pass"><span>&#8377;645,262 &middot; <b>t-ramprasad&rsquo;s first parking ever</b></span></td></tr>
</tbody></table></div>
<p class="note"><strong>t-ramprasad holding parking is a structural change, not a trade.</strong> Every page
until now has said that account &ldquo;holds no parking and is never swept&rdquo;, which meant a rejected
entry there could only be funded by selling a legacy holding by hand. It now has &#8377;2.1L of sellable
parking, so the reactive rule works in <strong>all three accounts</strong> for the first time.</p>
<p class="note"><strong>The stop that fired, and the question it raises.</strong> He observed that
GLAND&rsquo;s stop should have been <b>3,169</b> &mdash; the structural level less a 2% buffer
(3,233.10 &times; 0.98 = 3,168.44, which is where his figure comes from). Wednesday argues he is right: our fills bottomed at <b>3,221.1</b> and the stock was
back above its previous close within two hours, so a 3,169 stop would not have been touched. <em>The exact
intraday low could not be verified &mdash; every quote source refused &mdash; so that is an inference from
our own fills.</em> <strong>But LAURUSLABS argues the other way.</strong> Its stop was 2,252.40, a 2%
buffer puts it at 2,207.35, and the 16 November low was <b>2,190.0</b> &mdash; the buffered stop is hit
anyway, at a worse price &mdash; yet it closed 2,338.00 on the 17th, 3.8% above where we sold.
<strong>One for, one against, from the only two stop-outs available to look at.</strong> The rule has not
been changed. The proposal is to measure <code>structural &times; 0.98</code> against
<code>structural</code> across the whole closed book and ship the buffer only if it wins.</p>

<h3 class="sub" id="pre-scan">The scan &mdash; 33 actionable, none of them placeable</h3>
<p>Run by hand tonight against Wednesday&rsquo;s closes. <strong>SWING run 479: 634 candidates, 33
actionable, eleven of them a clean 8/8.</strong> Every other scanner returned <strong>zero</strong> &mdash;
WEEKLY 480 (587 candidates), ETF 481 (22), ETF_WEEKLY 482 (21) and REVERSAL 484 (325). STRIKE 483 returns
the identical 33 and is not a traded strategy.</p>
<p class="sub">Distance from Wednesday&rsquo;s close to the trigger, for the twenty-five whose stops sit inside the 6% band. Green is 1.5% or less, amber is 3.5% or more. <strong>With breadth shut none of it may be bought.</strong></p>
<svg viewBox="0 0 470 356" width="100%" style="max-width:640px" role="img" aria-label="How far each actionable setup sits below its trigger, Wednesday 18 November close"><text x="0" y="9" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">TFCILTD</text><rect x="96" y="1" width="23.6" height="9" rx="2" fill="var(--green)"/><text x="125.6" y="9" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.4%</text><text x="0" y="23" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GCSL</text><rect x="96" y="15" width="41.3" height="9" rx="2" fill="var(--green)"/><text x="143.3" y="23" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.7%</text><text x="0" y="37" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ACUTAAS</text><rect x="96" y="29" width="53.1" height="9" rx="2" fill="var(--green)"/><text x="155.1" y="37" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.9%</text><text x="0" y="51" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ISFT</text><rect x="96" y="43" width="76.7" height="9" rx="2" fill="var(--green)"/><text x="178.7" y="51" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.3%</text><text x="0" y="65" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">NINSYS</text><rect x="96" y="57" width="88.5" height="9" rx="2" fill="var(--green)"/><text x="190.5" y="65" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.5%</text><text x="0" y="79" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RATNAVEER</text><rect x="96" y="71" width="100.3" height="9" rx="2" fill="var(--series-1)"/><text x="202.3" y="79" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.7%</text><text x="0" y="93" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SAILIFE</text><rect x="96" y="85" width="112.1" height="9" rx="2" fill="var(--series-1)"/><text x="214.1" y="93" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.9%</text><text x="0" y="107" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHADOWFAX</text><rect x="96" y="99" width="118.0" height="9" rx="2" fill="var(--series-1)"/><text x="220.0" y="107" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.0%</text><text x="0" y="121" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHIVAUM</text><rect x="96" y="113" width="123.9" height="9" rx="2" fill="var(--series-1)"/><text x="225.9" y="121" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.1%</text><text x="0" y="135" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KABRAEXTRU</text><rect x="96" y="127" width="135.7" height="9" rx="2" fill="var(--series-1)"/><text x="237.7" y="135" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.3%</text><text x="0" y="149" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">UNITEDPOLY</text><rect x="96" y="141" width="147.5" height="9" rx="2" fill="var(--series-1)"/><text x="249.5" y="149" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.5%</text><text x="0" y="163" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">CUPID</text><rect x="96" y="155" width="153.4" height="9" rx="2" fill="var(--series-1)"/><text x="255.4" y="163" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.6%</text><text x="0" y="177" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">RUBICON</text><rect x="96" y="169" width="188.8" height="9" rx="2" fill="var(--series-1)"/><text x="290.8" y="177" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.2%</text><text x="0" y="191" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ROSSTECH</text><rect x="96" y="183" width="194.7" height="9" rx="2" fill="var(--series-1)"/><text x="296.7" y="191" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.3%</text><text x="0" y="205" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">MBAPL</text><rect x="96" y="197" width="200.6" height="9" rx="2" fill="var(--series-1)"/><text x="302.6" y="205" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.4%</text><text x="0" y="219" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SHUKRAPHAR</text><rect x="96" y="211" width="200.6" height="9" rx="2" fill="var(--series-1)"/><text x="302.6" y="219" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.4%</text><text x="0" y="233" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">DIACABS</text><rect x="96" y="225" width="206.5" height="9" rx="2" fill="var(--amber)"/><text x="308.5" y="233" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.5%</text><text x="0" y="247" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">KRISHANA</text><rect x="96" y="239" width="206.5" height="9" rx="2" fill="var(--amber)"/><text x="308.5" y="247" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.5%</text><text x="0" y="261" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">WHEELS</text><rect x="96" y="253" width="212.4" height="9" rx="2" fill="var(--amber)"/><text x="314.4" y="261" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.6%</text><text x="0" y="275" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PAYTM</text><rect x="96" y="267" width="230.1" height="9" rx="2" fill="var(--amber)"/><text x="332.1" y="275" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.9%</text><text x="0" y="289" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">ALGOQUANT</text><rect x="96" y="281" width="241.9" height="9" rx="2" fill="var(--amber)"/><text x="343.9" y="289" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.1%</text><text x="0" y="303" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">MCX</text><rect x="96" y="295" width="265.5" height="9" rx="2" fill="var(--amber)"/><text x="367.5" y="303" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.5%</text><text x="0" y="317" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">DIVISLAB</text><rect x="96" y="309" width="277.3" height="9" rx="2" fill="var(--amber)"/><text x="379.3" y="317" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.7%</text><text x="0" y="331" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">GLAND</text><rect x="96" y="323" width="312.7" height="9" rx="2" fill="var(--amber)"/><text x="414.7" y="331" fill="var(--muted)" font-size="9" font-family="var(--mono)">+5.3%</text><text x="0" y="345" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">SONACOMS</text><rect x="96" y="337" width="318.6" height="9" rx="2" fill="var(--amber)"/><text x="420.6" y="345" fill="var(--muted)" font-size="9" font-family="var(--mono)">+5.4%</text></svg>


<p class="note">Per-name price charts for all of these are in <a href="2026-11-18.html">Wednesday&rsquo;s
report</a>, with the sector pass, RRG quadrant and volume columns this table leaves out.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>gates</th><th>RS</th><th>A/D</th><th>chop</th><th>entry</th><th>SL</th><th>stop%</th><th>to entry</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>TFCILTD</b></td><td class="pass">8/8</td><td>97</td><td>A+</td><td>85%</td><td>170.39</td><td>165.24</td><td>3.0%</td><td class="pass"><b>+0.4%</b></td><td class="l">resting at 172.34 &mdash; <b>above</b> tonight&rsquo;s entry &middot; on long-term ASM I since 3 Nov</td></tr>
<tr><td class="l"><b>GCSL</b></td><td>7/8</td><td>94</td><td>A</td><td>87%</td><td>844.49</td><td>825.00</td><td>2.3%</td><td class="pass"><b>+0.7%</b></td><td class="l">held, all three &middot; on long-term ASM I</td></tr>
<tr><td class="l"><b>ACUTAAS</b></td><td>7/8</td><td>94</td><td>A&minus;</td><td>56%</td><td>4,025.64</td><td>3,882.10</td><td>3.6%</td><td class="pass">+0.9%</td><td class="l">new &middot; <b>on MarketSmith&rsquo;s buy watchlist</b></td></tr>
<tr><td class="l"><b>ISFT</b></td><td>7/8</td><td>82</td><td>B</td><td>69%</td><td>120.44</td><td>117.00</td><td>2.9%</td><td class="pass">+1.3%</td><td class="l"><b>ESM Stage 1, series BE &mdash; trade-for-trade</b>, so a 2.9% stop is theoretical</td></tr>
<tr><td class="l"><b>NINSYS</b></td><td>7/8</td><td>96</td><td>A+</td><td>51%</td><td>941.88</td><td>901.75</td><td>4.3%</td><td class="pass">+1.5%</td><td class="l">new</td></tr>
<tr><td class="l"><b>RATNAVEER</b></td><td class="pass">8/8</td><td>97</td><td>A+</td><td>86%</td><td>376.70</td><td>356.50</td><td>5.4%</td><td>+1.7%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>SAILIFE</b></td><td>7/8</td><td>91</td><td>B&minus;</td><td>79%</td><td>1,822.84</td><td>1,738.00</td><td>4.7%</td><td>+1.9%</td><td class="l">new &mdash; a CDMO name, the group marked down on the 16th</td></tr>
<tr><td class="l"><b>SHADOWFAX</b></td><td class="pass">8/8</td><td>96</td><td>B+</td><td>66%</td><td>304.61</td><td>288.15</td><td>5.4%</td><td>+2.0%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>SHIVAUM</b></td><td class="pass">8/8</td><td>92</td><td>B&minus;</td><td>83%</td><td>567.13</td><td>550.00</td><td>3.0%</td><td>+2.1%</td><td class="l">was refused on G3 last night; now a clean 8/8</td></tr>
<tr><td class="l"><b>KABRAEXTRU</b></td><td>7/8</td><td>98</td><td>A+</td><td>83%</td><td>746.49</td><td>715.75</td><td>4.1%</td><td>+2.3%</td><td class="l">new &mdash; RS 98, the second highest on the board</td></tr>
<tr><td class="l"><b>UNITEDPOLY</b></td><td>7/8</td><td>93</td><td>A</td><td>67%</td><td>54.11</td><td>51.63</td><td>4.6%</td><td>+2.5%</td><td class="l">new &mdash; 8.4% ADR, the widest here</td></tr>
<tr><td class="l"><b>CUPID</b></td><td class="pass">8/8</td><td><b>99</b></td><td>A+</td><td>77%</td><td>372.54</td><td>351.85</td><td>5.6%</td><td>+2.6%</td><td class="l">held, all three &middot; <b>highest RS on the board</b> &middot; on long-term ASM I</td></tr>
<tr><td class="l"><b>RUBICON</b></td><td>7/8</td><td>96</td><td>B</td><td>71%</td><td>1,710.81</td><td>1,640.00</td><td>4.1%</td><td>+3.2%</td><td class="l">resting at 1,777.45 &mdash; <b>above</b> tonight&rsquo;s entry &middot; on MS&rsquo;s watchlist a fourth night</td></tr>
<tr><td class="l"><b>ROSSTECH</b></td><td>7/8</td><td>95</td><td>A+</td><td>65%</td><td>1,582.26</td><td>1,514.90</td><td>4.3%</td><td>+3.3%</td><td class="l">held, all three</td></tr>
<tr><td class="l"><b>MBAPL</b></td><td>7/8</td><td>94</td><td>A&minus;</td><td>59%</td><td>199.40</td><td>192.40</td><td>3.5%</td><td>+3.4%</td><td class="l">new</td></tr>
<tr><td class="l"><b>SHUKRAPHAR</b></td><td>7/8</td><td>98</td><td>A+</td><td>82%</td><td>84.97</td><td>81.06</td><td>4.6%</td><td>+3.4%</td><td class="l">held &mdash; <b>becomes SHUKRAMED on Friday 20 Nov</b></td></tr>
<tr><td class="l"><b>DIACABS</b></td><td class="pass">8/8</td><td>97</td><td>A</td><td>71%</td><td>375.80</td><td>355.85</td><td>5.3%</td><td>+3.5%</td><td class="l">new</td></tr>
<tr><td class="l"><b>KRISHANA</b></td><td class="pass">8/8</td><td>96</td><td>A+</td><td>67%</td><td>250.25</td><td>240.27</td><td>4.0%</td><td>+3.5%</td><td class="l">held, all three &mdash; <b>it has re-formed a base</b>, having been skipped entirely last night</td></tr>
<tr><td class="l"><b>WHEELS</b></td><td>7/8</td><td>96</td><td>B+</td><td>58%</td><td>2,377.75</td><td>2,272.00</td><td>4.4%</td><td>+3.6%</td><td class="l">new</td></tr>
<tr><td class="l"><b>PAYTM</b></td><td>7/8</td><td>89</td><td>B+</td><td>76%</td><td>1,963.92</td><td>1,872.20</td><td>4.7%</td><td>+3.9%</td><td class="l">held &middot; MarketSmith added it to the model portfolio at 1,900</td></tr>
<tr><td class="l"><b>ALGOQUANT</b></td><td>7/8</td><td>83</td><td>B</td><td>70%</td><td>87.56</td><td>83.64</td><td>4.5%</td><td>+4.1%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>MCX</b></td><td class="pass">8/8</td><td>90</td><td>B+</td><td>51%</td><td>3,781.55</td><td>3,586.00</td><td>5.2%</td><td>+4.5%</td><td class="l">held in two, resting 7 in Ram &middot; chop 51% is the weakest 8/8 here</td></tr>
<tr><td class="l"><b>DIVISLAB</b></td><td class="pass">8/8</td><td>90</td><td>A</td><td>83%</td><td>11,567.59</td><td>10,954.00</td><td>5.3%</td><td>+4.7%</td><td class="l">resting, all three</td></tr>
<tr><td class="l"><b>GLAND</b></td><td class="pass">8/8</td><td>92</td><td>B+</td><td>83%</td><td>3,402.69</td><td>3,208.70</td><td>5.7%</td><td>+5.3%</td><td class="l"><b>stopped out on Wednesday morning at 3,221.86 &mdash; and back on the list that same evening</b></td></tr>
<tr><td class="l"><b>SONACOMS</b></td><td class="pass">8/8</td><td>92</td><td>A</td><td>75%</td><td>936.77</td><td>882.55</td><td>5.8%</td><td>+5.4%</td><td class="l">held, all three</td></tr>
</tbody></table></div>
<p class="note"><strong>Where the rest went, corrected.</strong> This table lists the twenty-five SWING
names whose stops sit inside the 6% band. The rows further down the report carrying stops of <b>13.6% to
18.6%</b> &mdash; KINGFA, CHENNPETRO, MARKSANS, IRISDOREME, SYRMA and a second RUBICON &mdash; are
<b>WEEKLY rows, not SWING ones</b>, and the WEEKLY scan returned <b>zero</b> actionable: every one of them
is blocked on G4, the stop-width gate. <strong>So the second RUBICON at 1,777.90 is a different scanner
reading the same name on a weekly base, not the data fault an earlier draft of this page called it.</strong>
And note that eight of the twenty-five below carry stops of <b>5.2% to 5.8%</b> &mdash; MCX, DIVISLAB,
DIACABS, RATNAVEER, SHADOWFAX, CUPID, GLAND and SONACOMS. Those are over the 5% cap this book applies to
stocks: actionable to the scanner, but the cap still has to be applied before anything is sized.</p>
<p class="note"><strong>On the gate counts, because the tables disagree.</strong> Eleven names score 8/8
here while the report&rsquo;s own TIS table marks nine of them &ldquo;blocked by G5&rdquo;. <b>G5 is the
sector-rotation note. It records where money is going and refuses nothing</b>, which is why a name can be
8/8 and carry a G5 mark at once. The header figure of &ldquo;66 actionable&rdquo; is SWING&rsquo;s 33 plus
STRIKE&rsquo;s identical 33 counted twice; STRIKE is not a traded strategy, so the number to read is
<b>33</b>.</p>
<p class="note"><strong>GLAND is the uncomfortable one.</strong> It stopped us out on Wednesday morning for
&minus;&#8377;12,913 across two accounts, recovered by lunchtime, and closed the day as a clean 8/8 setup
with a <em>higher</em> entry and a <em>higher</em> stop than the one that just failed. Nothing about that
is a reason to buy it back &mdash; breadth is shut and it would be a fresh position at a worse price
&mdash; but it is the clearest statement the tape has made about how tight the stop was.</p>

<h3 class="sub" id="pre-flows">Who is actually buying &mdash; FII and DII</h3>
<p class="sub">Net cash-market flows in &#8377; crore, to Wednesday 18 November.</p>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>FII net</th><th>DII net</th><th>FII buy</th><th>FII sell</th></tr></thead><tbody>
<tr><td class="l"><b>Wed 18 Nov</b></td><td class="pass">+5,867</td><td class="bad"><b>&minus;3,160</b></td><td>17,913</td><td>12,046</td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="pass">+4,195</td><td class="pass">+197</td><td>19,931</td><td>15,736</td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="pass">+4,865</td><td class="bad">&minus;3,519</td><td>15,637</td><td>10,772</td></tr>
<tr><td class="l">Fri 13 Nov</td><td class="pass">+5,737</td><td class="bad">&minus;2,254</td><td>18,340</td><td>12,603</td></tr>
<tr><td class="l">Thu 12 Nov</td><td class="pass">+7,831</td><td class="bad">&minus;6,331</td><td>20,273</td><td>12,443</td></tr>
</tbody></table></div>
<p class="note"><strong>The 18th&rsquo;s page called the single positive DII print a break in the pattern.
That was wrong and is corrected here.</strong> The 17th&rsquo;s +&#8377;197 Cr was a blip inside an
otherwise unbroken run of domestic selling, and on the 18th it resumed at &minus;&#8377;3,160 Cr while foreign
buying continued, as it has every session shown here. <strong>Foreign money goes into the large, liquid names that
carry the index; domestic institutions sell into it across the broader market &mdash; which is where every
one of tonight&rsquo;s thirty-three setups lives.</strong> That is the mechanism behind an index that
printed nine-month highs on Tuesday, gave ground on Wednesday, and still sits above its 20MA while
breadth reads 59.52%.</p>

<h3 class="sub" id="pre-breadth">Breadth, three sessions into the shut gate</h3>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>above their 20MA</th><th>prior-5 mean</th><th>gap</th><th class="l">breadth gate</th></tr></thead><tbody>
<tr><td class="l"><b>Wed 18 Nov</b></td><td class="bad"><b>59.52%</b></td><td>70.35%</td><td class="bad">&minus;10.83</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="bad">65.79%</td><td>69.65%</td><td class="bad">&minus;3.86</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="bad">65.11%</td><td>69.42%</td><td class="bad">&minus;4.31</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Fri 13 Nov</td><td>74.94%</td><td>65.42%</td><td class="pass">+9.52</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">Thu 12 Nov</td><td>75.95%</td><td>62.65%</td><td class="pass">+13.30</td><td class="l pass"><span>open</span></td></tr>
</tbody></table></div>
<p class="note"><strong>On Tuesday the reading rose and the gate still shut, because the mean rose faster.
On Wednesday both moved the wrong way.</strong> Breadth fell 6.27 points to 59.52% while the mean kept climbing to
70.35%, so the gap widened from 3.86 to 10.83 &mdash; the worst of the move. <strong>Roughly eleven points
now separate the gate from opening</strong>, against four a day ago. On the 13th three-quarters of the
universe was above its own 20-day line; tonight it is three-fifths.</p>

<h3 class="sub" id="pre-funding">Can the book pay for what it has already ordered?</h3>
<div class="scroll"><table><thead><tr><th class="l">account</th><th>held</th><th>free cash</th><th>parking it can sell</th><th>resting orders</th><th class="l">covered?</th></tr></thead><tbody>
<tr><td class="l">t-default</td><td>60,93,041</td><td>14,055</td><td>30,165 units &asymp; 35,28,702</td><td>23,73,533</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">akul</td><td>3,24,410</td><td>1,434</td><td>3,160 units &asymp; 3,69,657</td><td>2,13,447</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">t-ramprasad</td><td>4,85,559</td><td>7,523</td><td><b>1,794 units &asymp; 2,09,862</b></td><td>4,52,431</td><td class="l warn"><span>only by selling parking &mdash; <b>possible for the first time</b></span></td></tr>
</tbody></table></div>
<p class="note"><strong>Cash is deliberately thin in all three</strong>, because his instruction on Wednesday was
to park the free cash rather than hold it. The consequence is that anything firing tomorrow will likely be
refused for funds. <strong>That is now a manageable refusal rather than a dead end</strong>: every account
holds parking, Ram included, and Wednesday proved the refusals are usually phantom anyway &mdash; retiring dead
intents freed &#8377;237,302 across two accounts without selling a single unit. <strong>Ram&rsquo;s
&#8377;5L has still not landed.</strong></p>

<h3 class="sub" id="pre-diary">The diary</h3>
<div class="scroll"><table><thead><tr><th class="l">when</th><th class="l">event</th><th class="l">why it matters</th></tr></thead><tbody>

<tr><td class="l">Thu 19 Nov</td><td class="l">Mahanadi Coalfields IPO opens</td><td class="l">&#8377;129&ndash;136, &#8377;8,981 Cr, 100% offer-for-sale by Coal India. <b>SKIP</b> as a trade &mdash; see the IPO review.</td></tr>
<tr><td class="l">Thu 19 Nov</td><td class="l">Crystal Crop Protection, day 2 of 3</td><td class="l">Closes Friday. <b>AVOID on the case</b>, though the anchor book was better than the premium implied.</td></tr>
<tr><td class="l">Thu 19 Nov, 00:30 IST</td><td class="l">US FOMC minutes</td><td class="l">Released 14:00 ET Wednesday, so they land overnight. The December hike is priced near certain and gold is at its lowest since September 2025 on it.</td></tr>
<tr><td class="l"><b>Fri 20 Nov</b></td><td class="l"><b>SHUKRAPHAR becomes SHUKRAMED</b></td><td class="l">NSE approved the name and symbol change on 16 Nov. It is <b>held in all three accounts</b> with a stop resting at 79.25 under the old symbol, and whether that GTT migrates is <b>unverified</b>. This needs checking before Friday, not on it.</td></tr>
</tbody></table></div>

<h3 class="sub" id="pre-decisions">Waiting on a decision</h3>
<ul>
<li>🔴 <strong>The breadth history repeats a row.</strong> 9 and 10 November both read 62.60% against
a 54.22% mean. That series feeds the prior-five mean the gate is measured against, so a duplicated row
moves the number that decides whether anything may be bought. <b>Worth verifying the gate input before
the next session that comes close to opening it.</b></li>
<li>🔴 <strong>The stop buffer.</strong> GLAND says a 2% buffer would have saved today&rsquo;s
&minus;&#8377;12,913; LAURUSLABS says it would have been hit anyway at a worse price. <strong>One for, one
against.</strong> The measurement &mdash; <code>structural &times; 0.98</code> against
<code>structural</code> across the whole closed book, counting how many exits flip and what it does to
total R &mdash; is proposed and not yet run. <b>It needs his yes.</b></li>
<li><strong>SHUKRAPHAR&rsquo;s symbol change on Friday</strong>, with a stop resting under the old ticker
in three accounts.</li>
<li><strong>Two resting triggers sit above tonight&rsquo;s entries</strong> &mdash; TFCILTD at 172.34
against 170.39, RUBICON at 1,777.45 against 1,710.81. Both will buy higher than the scan now says.</li>
<li><strong>Orphan stop records</strong> with no position behind them: ACMESOLAR, LAURUSLABS, and now
GLAND in akul and t-ramprasad. They would be refused at the exchange rather than short anything, so this is
noise &mdash; but clearing it is his call, never a silent cancel.</li>
<li><strong>Fund t-ramprasad or stand its orders down.</strong> &#8377;4,52,431 resting against
&#8377;7,523 and &#8377;2.1L of parking.</li>
<li><strong><code>evening-scan</code> has not succeeded since 30 October</strong> &mdash; 310 hours silent
against a 30-hour budget. Every scan on this page was run by hand.</li>
</ul>
<p class="note">Built Wednesday 18 November 2026 from the service&rsquo;s records, a live read of all three
brokers, tonight&rsquo;s hand-run scans (SWING 479, WEEKLY 480, ETF 481, ETF_WEEKLY 482, STRIKE 483,
REVERSAL 484), the 17-index distribution-day count and recorded FII/DII flows. Closes are
Wednesday&rsquo;s. <strong>The first scan of the evening was priced off the previous session and was
discarded; these are the re-run.</strong> Nothing here places an order.</p>
"""


PREMARKET_2026_11_20 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Thursday was a strong index day and <strong>it did almost nothing for the gate</strong>.
The Nifty gapped down to 25,104.80, turned, and closed at the day&rsquo;s high &mdash; <strong>+1.14% to
25,514.30</strong>, with Bank Nifty at a record and <strong>Auto +4.40%</strong>. Breadth moved from
59.52% to <strong>60.25%</strong> while its prior-five mean fell from 70.35% to <strong>68.29%</strong>.
<strong>Seven tenths of a point on a one-and-a-fifth percent index day</strong>, which narrows the gap from
10.83 points to <strong>8.04</strong> &mdash; a real repair, and nowhere near enough. Entries remain
blocked, on breadth, and <strong>none of tonight&rsquo;s thirty actionable names may be placed.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes are
Thursday 19 November&rsquo;s. All six scanners were re-run by hand against them once the bhavcopy landed
&mdash; SWING run 491, STRIKE 492, WEEKLY 493, ETF 494, ETF_WEEKLY 495, REVERSAL 498.</p>
<p class="note"><strong>This is the clearest reading of the divergence the book has had.</strong> The
five-session mean is still falling &mdash; 70.35% to 68.29% &mdash; so part of tonight&rsquo;s narrower gap
is the mean coming down to meet a breadth reading that has not recovered. What is news is the
<em>shape</em> of the day: the money went into PSU banks, FMCG, banks and autos &mdash; the heavyweights
&mdash; and the broad market did not come with it. The five-session table below is the whole argument.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l"><b>60.25% against 68.29%</b> on 878 names &mdash; an 8.04-point gap, against 10.83 on Wednesday</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">CONFIRMED_UPTREND &mdash; follow-through on the Nifty still dated <b>2 November</b>, now seventeen days old</td><td class="l pass"><span>OPEN</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED_UPTREND, <b>2 distribution days</b> &mdash; mail of 19 Nov 17:04, agreeing with ours a second session</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">The follow-through date, theirs against ours</td><td class="l">MarketSmith dates the follow-through <b>15 October</b>. Our record says <b>2 November</b>. Same verdict, a different event behind it.</td><td class="l warn"><span>unresolved</span></td></tr>
</tbody></table></div>
<p class="note"><strong>The date disagreement is not cosmetic.</strong> A follow-through is the thing the
gate is counting age from, and theirs is two and a half weeks older than ours. If they are right, the
confirmation this book is trading on is thirty-five days old rather than seventeen. It has now been carried
on this page for several sessions without being settled; it is on the decisions list below.</p>

<h3 class="sub" id="pre-indices">Why a +1.14% day bought back less than a point of breadth</h3>
<p class="sub">Each index&rsquo;s move over the last <strong>five sessions</strong>, to Thursday&rsquo;s
close. The Nifty is up; most of what we actually buy is down.</p>
<svg viewBox="0 0 470 252" width="100%" style="max-width:640px" role="img" aria-label="Five-session move by index to Thursday 19 November"><line x1="281.0" y1="0" x2="281.0" y2="246" stroke="var(--rule,#d8d4cc)" stroke-width="1"/><text x="0" y="17" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PSU Bank</text><rect x="283.0" y="9" width="182.8" height="9" rx="2" fill="var(--green)"/><text x="469.8" y="17" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+4.89%</text><text x="0" y="31" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">FMCG</text><rect x="283.0" y="23" width="137.5" height="9" rx="2" fill="var(--green)"/><text x="424.5" y="31" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.68%</text><text x="0" y="45" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Bank</text><rect x="283.0" y="37" width="93.8" height="9" rx="2" fill="var(--green)"/><text x="380.8" y="45" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.51%</text><text x="0" y="59" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Media</text><rect x="283.0" y="51" width="51.9" height="9" rx="2" fill="var(--green)"/><text x="338.9" y="59" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.39%</text><text x="0" y="73" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Auto</text><rect x="283.0" y="65" width="49.0" height="9" rx="2" fill="var(--green)"/><text x="336.0" y="73" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.31%</text><text x="0" y="87" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Fin Services</text><rect x="283.0" y="79" width="32.1" height="9" rx="2" fill="var(--series-1)"/><text x="319.1" y="87" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.86%</text><text x="0" y="101" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Nifty 50</text><rect x="283.0" y="93" width="31.8" height="9" rx="2" fill="var(--series-1)"/><text x="318.8" y="101" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.85%</text><text x="0" y="115" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Healthcare</text><rect x="283.0" y="107" width="8.6" height="9" rx="2" fill="var(--series-1)"/><text x="295.6" y="115" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.23%</text><text x="0" y="129" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Energy</text><rect x="283.0" y="121" width="1.5" height="9" rx="2" fill="var(--series-1)"/><text x="288.5" y="129" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.04%</text><text x="0" y="143" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Cons Durables</text><rect x="276.4" y="135" width="2.6" height="9" rx="2" fill="var(--amber)"/><text x="272.4" y="143" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.07%</text><text x="0" y="157" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Midcap 150</text><rect x="254.7" y="149" width="24.3" height="9" rx="2" fill="var(--amber)"/><text x="250.7" y="157" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.65%</text><text x="0" y="171" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Next 50</text><rect x="249.1" y="163" width="29.9" height="9" rx="2" fill="var(--amber)"/><text x="245.1" y="171" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.80%</text><text x="0" y="185" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Pharma</text><rect x="239.4" y="177" width="39.6" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="235.4" y="185" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-1.06%</text><text x="0" y="199" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Realty</text><rect x="234.5" y="191" width="44.5" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="230.5" y="199" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-1.19%</text><text x="0" y="213" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Smallcap 100</text><rect x="233.8" y="205" width="45.2" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="229.8" y="213" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-1.21%</text><text x="0" y="227" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Metal</text><rect x="140.7" y="219" width="138.3" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="136.7" y="227" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-3.70%</text><text x="0" y="241" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">IT</text><rect x="134.4" y="233" width="144.6" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="130.4" y="241" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-3.87%</text></svg>
<p class="note"><strong>Read the sign changes, not the sizes.</strong> Over the week the Nifty 50 is
<b>+0.85%</b> while <b>Smallcap 100 is &minus;1.21%</b>, <b>Midcap 150 &minus;0.65%</b> and the
<b>Next 50 &minus;0.80%</b>. Metal is <b>&minus;3.70%</b> and IT <b>&minus;3.87%</b>. The index is being
carried by PSU Bank (+4.89%), FMCG (+3.68%) and Bank (+2.51%). <strong>Every one of tonight&rsquo;s thirty
setups lives in the half of the market that is falling.</strong> That is what a 60.25% breadth reading
under a 68.29% mean actually describes, and it is why a single good index session repaired so little of
it: the names that rose were not, in the main, the names below their own 20-day average.</p>

<h3 class="sub" id="pre-regime">Regime, after a day that looked like a repair</h3>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">status</th><th class="l">change on Thursday</th></tr></thead><tbody>
<tr><td class="l"><b>METAL</b></td><td class="bad">6</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail">unchanged &mdash; <b>still the worst-rated sector</b>, and &minus;3.70% on the week despite +0.63% today</td></tr>
<tr><td class="l"><b>ENERGY</b></td><td class="bad">4</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l warn">unchanged, on a +1.15% day</td></tr>
<tr><td class="l"><b>CONSUMER DURABLES</b></td><td>3</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l warn">unchanged &mdash; <b>and it was the second-best index of the day at +3.64%</b></td></tr>
<tr><td class="l"><b>SMALLCAP</b></td><td class="bad">8</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail">unchanged &mdash; still the only broad index not confirmed, now on day 18 of its attempt</td></tr>
<tr><td class="l">IT</td><td class="bad">8</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l fail"><b>the only index that fell</b>, &minus;1.10%, and &minus;3.87% on the week</td></tr>
<tr><td class="l">NEXT 50</td><td class="bad">4</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l">unchanged at 4</td></tr>
<tr><td class="l">NIFTY &middot; BANK &middot; PSU BANK</td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">clean &mdash; and they are the three carrying the week</td></tr>
</tbody></table></div>
<p class="note"><strong>Not one sector was upgraded.</strong> Consumer Durables rose 3.64% and stayed
UNDER PRESSURE; Energy rose 1.15% and stayed UNDER PRESSURE; Metal rose 0.63% and stayed a RALLY ATTEMPT.
<strong>Distribution days do not come off on a good day &mdash; they expire with time or get washed out by
a new follow-through</strong>, and neither happened. A single session, however green, is not a repair.</p>

<h3 class="sub" id="pre-today">What Thursday did to the book</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l"><b>SSWL</b>, all three</td><td class="l">Stopped at <b>09:22:58</b>, seven minutes into the session, in every account.</td><td class="l fail"><span>&minus;&#8377;11,428.35</span></td></tr>
<tr><td class="l"><b>PAYTM</b></td><td class="l">Stopped at <b>10:50:23</b> in t-default and akul. It was on MarketSmith&rsquo;s model portfolio at 1,900.</td><td class="l fail"><span>&minus;&#8377;9,342.20</span></td></tr>
<tr><td class="l"><b>SHYAMMETL</b></td><td class="l">Stopped at <b>15:25:28</b>, thirty-five minutes before the close, <b>in Ram only</b> &mdash; 38 at 1,292.10 against a 1,292.90 stop. The leg the other two accounts never got funded.</td><td class="l fail"><span>&minus;&#8377;2,577.16</span></td></tr>
<tr><td class="l">The day, totalled</td><td class="l">Three stop-outs against <b>&#8377;21,942.31</b> of risk at entry.</td><td class="l fail"><span><b>&minus;&#8377;23,347.71 &middot; &minus;1.06R blended</b></span></td></tr>
<tr><td class="l">Settlement</td><td class="l">All three were booked by the scheduled settlement unaided. <code>reconcile_positions</code> leaves <b>no orphan sell trigger in any account</b>; Ram&rsquo;s eleven orphans are all resting buy entries.</td><td class="l pass"><span>nothing forced, nothing left naked</span></td></tr>
<tr><td class="l">Eleven resting entries</td><td class="l">TIMEX, DIVISLAB, SANSERA, BMWVENTLTD, PTCIL, LALITHAA, RUBICON, CPPLUS, RATNAVEER, TFCILTD, LTTS &mdash; <b>none fired all day</b>, on a day the Nifty rose 1.14%.</td><td class="l warn"><span>the tape went up and our names did not</span></td></tr>
</tbody></table></div>
<p class="note"><strong>A one-rupee miss is worth noticing.</strong> SHYAMMETL&rsquo;s stop was 1,292.90
and it filled at <b>1,292.10</b> &mdash; eighty paise of slippage, which is about as clean as a stop fill
gets. The &minus;1.06R blended loss means the stops overshot the number they were
sized for by 6.4%. <strong>The loss is the cost of being wrong three times, not the cost of bad execution.</strong></p>

<h3 class="sub" id="pre-risk">What is closest to being stopped out next</h3>
<p class="sub">Distance from Thursday&rsquo;s close to the resting stop, for the tightest of
<strong>37 open positions</strong>. LIQUIDCASE is parking and is excluded.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>move</th><th>to stop</th><th>open R</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>KRISHANA</b></td><td class="bad">&minus;4.7%</td><td class="bad"><b>1.7%</b></td><td class="bad">&minus;0.74R</td><td class="l">held in all three, opened 16 Nov &mdash; <b>the tightest thing in the book</b></td></tr>
<tr><td class="l"><b>BMWVENTLTD</b></td><td class="bad">&minus;2.7%</td><td class="bad"><b>1.8%</b></td><td class="bad">&minus;0.60R</td><td class="l">held in akul and Ram only; in t-default it is still a <b>resting entry at 66.96</b></td></tr>
<tr><td class="l">SHUKRAPHAR</td><td>&minus;1.5%</td><td>3.6%</td><td>&minus;0.29R</td><td class="l">held in all three &mdash; <b>becomes SHUKRAMED tomorrow</b>, stop resting at 79.25 under the old symbol</td></tr>
<tr><td class="l">SONACOMS</td><td>&minus;2.2%</td><td>3.9%</td><td>&minus;0.37R</td><td class="l">held in all three</td></tr>
<tr><td class="l">MCX</td><td>&minus;2.0%</td><td>4.5%</td><td>&minus;0.32R</td><td class="l">on MarketSmith&rsquo;s buy watchlist tonight</td></tr>
<tr><td class="l">SGMART</td><td class="pass">+8.0%</td><td>7.4%</td><td class="pass"><b>+1.97R</b></td><td class="l">the best open position in the book</td></tr>
<tr><td class="l">CUPID</td><td class="pass">+5.9%</td><td>5.6%</td><td class="pass">+1.29R</td><td class="l">highest RS on the board</td></tr>
</tbody></table></div>
<p class="note"><strong>Two names are inside two percent of their stops.</strong> KRISHANA and
BMWVENTLTD together are carrying about 1.3R of open loss and would both be gone on a 2% down day in the
small caps &mdash; which is precisely the half of the market that has fallen every session this week.
<strong>Neither stop is to be moved.</strong> They are recorded here so that if they fire tomorrow it is
not a surprise.</p>

<h3 class="sub" id="pre-scan">The scan &mdash; 30 actionable, none of them placeable</h3>
<p>Run by hand once the 19 November bhavcopy landed. <strong>SWING run 491: 696 candidates, 30
actionable.</strong> Every other scanner returned <strong>zero</strong> &mdash; WEEKLY 493, ETF 494,
ETF_WEEKLY 495 and REVERSAL 498. STRIKE 492 returns the identical list and is not a traded strategy.
The full table, with charts, sector pass and volume columns, is further down this page.</p>
<p class="note"><strong>Seven of the thirty are missing from the table below, and that is this
page&rsquo;s own fault, not the scanner&rsquo;s.</strong> The report prints the top <b>25</b> rows per
scanner by design &mdash; <code>--top</code> defaults to 25 &mdash; so with thirty actionable names, five
are cut by the limit and two more by the near-pass filter. Nothing on the machine-built page says so.
They are listed here in full.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>RS</th><th>entry</th><th>SL</th><th>stop%</th><th>to entry</th><th class="l">the one gate it fails</th></tr></thead><tbody>
<tr><td class="l"><b>ROSSTECH</b></td><td>95</td><td>1,606.71</td><td>1,514.90</td><td>5.7%</td><td>+3.1%</td><td class="l">G8 at 5.283 &mdash; <b>already held in all three</b>, so this is an add, not a new name</td></tr>
<tr><td class="l"><b>SBC</b></td><td><b>97</b></td><td>70.77</td><td>67.10</td><td>5.2%</td><td>+3.3%</td><td class="l">G6 at 0.000 &mdash; <b>already held in all three</b> at +0.80R; also an add</td></tr>
<tr><td class="l"><b>TAMBOLIIN</b></td><td>95</td><td>329.66</td><td>311.40</td><td>5.5%</td><td>+3.5%</td><td class="l">G8 at 7.377 &mdash; new name, sector IMPROVING</td></tr>
<tr><td class="l"><b>PTCIL</b></td><td>&mdash;</td><td>24,699.30</td><td>23,220.00</td><td>6.0%</td><td>+3.6%</td><td class="l">G7 at 89 against a 90 bar &mdash; <b>already resting in t-default</b> at this exact trigger</td></tr>
<tr><td class="l"><b>SAMBHV</b></td><td>&mdash;</td><td>168.44</td><td>159.10</td><td>5.5%</td><td>+4.3%</td><td class="l">G8 at 5.024 &mdash; new name</td></tr>
<tr><td class="l"><b>GLOBAL</b></td><td>93</td><td>151.39</td><td>143.00</td><td>5.5%</td><td>+4.3%</td><td class="l">G6 at &minus;11.000 &mdash; new name, no sector rating at all</td></tr>
<tr><td class="l"><b>CONSOFINVT</b></td><td>&mdash;</td><td>339.63</td><td>320.00</td><td>5.8%</td><td>+6.0%</td><td class="l">G6 at 3.000 &mdash; furthest from its trigger of the thirty</td></tr>
</tbody></table></div>
<p class="note"><strong>Every one of the seven carries a stop wider than 5%</strong>, which is the cap this
book applies to stocks &mdash; 5.2% to 6.0%. That is not a coincidence: the report orders candidates by
gates passed and then by stop width, so the widest stops are exactly what the 25-row cut takes off the
bottom. <strong>So the rows being hidden are, as a group, the ones that would need the cap applied anyway.</strong>
It is still wrong for the page to be silent about it, and the fix &mdash; print the count that was cut
&mdash; is on the decisions list.</p>
<p class="note"><strong>Two of the seven are adds to winners, not new risk.</strong> ROSSTECH is held in
all three at +0.79R and SBC at +0.80R, and both printed a fresh entry tonight. Pyramiding is not something
this book does today and no rule covers it. <strong>Noted, not proposed.</strong></p>

<h3 class="sub" id="pre-flows">Who is actually buying &mdash; FII and DII</h3>
<p class="sub">Net cash-market flows in &#8377; crore. <strong>Thursday&rsquo;s figures had not published
when this page was built</strong>, so the newest row is Wednesday&rsquo;s.</p>
<div class="scroll"><table><thead><tr><th class="l">day</th><th>FII net</th><th>DII net</th><th>FII 5-session</th></tr></thead><tbody>
<tr><td class="l"><b>Wed 18 Nov</b></td><td class="pass">+5,867</td><td class="bad"><b>&minus;3,160</b></td><td class="pass">+28,494</td></tr>
<tr><td class="l">Tue 17 Nov</td><td class="pass">+4,195</td><td class="pass">+197</td><td class="pass">+35,191</td></tr>
<tr><td class="l">Mon 16 Nov</td><td class="pass">+4,865</td><td class="bad">&minus;3,519</td><td class="pass">+38,207</td></tr>
<tr><td class="l">Fri 13 Nov</td><td class="pass">+5,737</td><td class="bad">&minus;2,254</td><td class="pass">+33,342</td></tr>
<tr><td class="l">Thu 12 Nov</td><td class="pass">+7,831</td><td class="bad">&minus;6,331</td><td class="pass">+41,356</td></tr>
</tbody></table></div>
<p class="note"><strong>The mechanic is unchanged and Thursday is exactly what it looks like.</strong>
Foreign money buys the large, liquid names that carry the index; domestic institutions sell into it across
the broader market. A session where PSU Bank, FMCG, Bank and Auto do the lifting and the smallcaps add
0.71% is that trade, printed. <strong>The FII five-session sum has nonetheless fallen from +41,356 to
+28,494 &mdash; foreign buying is still positive but it is decelerating.</strong></p>

<h3 class="sub" id="pre-marketsmith">MarketSmith, read in full tonight</h3>
<div class="scroll"><table><thead><tr><th class="l">what they publish</th><th class="l">what it says</th></tr></thead><tbody>
<tr><td class="l">Market status</td><td class="l"><b>CONFIRMED UPTREND</b>, <b>2 distribution days</b>, follow-through dated <b>15 October</b></td></tr>
<tr><td class="l">Sectors confirmed</td><td class="l">Bank, Pharma, Financial Services, FMCG, Realty, Energy, Auto, Media, Consumer Durables</td></tr>
<tr><td class="l">Sectors under pressure</td><td class="l fail"><b>Metal and IT</b> &mdash; the same two our own count rates worst</td></tr>
<tr><td class="l">Buy watchlist</td><td class="l">Raghav Productivity Enhancers, Rubicon Research, <b>Acutaas Chemicals</b>, Sudeep Pharma, <b>Lenskart Solutions</b>, <b>MCX</b>, Nykaa, Union Bank</td></tr>
</tbody></table></div>
<p class="note"><strong>Three of their watchlist are already in this book.</strong> MCX and Lenskart are
held in all three accounts; Rubicon has a resting entry at 1,777.45 and has been on their list four nights
running. <strong>Where they and we disagree is Energy and Consumer Durables</strong> &mdash; they call both
confirmed, our own distribution count has both UNDER PRESSURE. Their sector read is a judgement; ours is a
count of days. Neither gates anything.</p>

<h3 class="sub" id="pre-funding">Can the book pay for what it has already ordered?</h3>
<div class="scroll"><table><thead><tr><th class="l">account</th><th>free cash</th><th>committed to resting orders</th><th class="l">covered?</th></tr></thead><tbody>
<tr><td class="l">t-default</td><td>14,395</td><td>51,69,367</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">akul</td><td>5,916</td><td>5,26,534</td><td class="l warn"><span>only by selling parking</span></td></tr>
<tr><td class="l">t-ramprasad</td><td><b>5,930</b></td><td>10,89,580</td><td class="l warn"><span>only by selling parking &mdash; <b>and the &#8377;5L has still not landed</b></span></td></tr>
</tbody></table></div>
<p class="note"><strong>Cash is deliberately at the buffer in all three</strong>, on his instruction to
park rather than hold. Anything firing tomorrow will likely be refused for funds, and the standing sequence
is unchanged: <b>retire dead intents first</b> &mdash; most refusals this month have been phantom
reservations rather than real shortfalls &mdash; then sell exactly the shortfall from parking, and only
parking. <strong>Ram&rsquo;s capital was set to &#8377;10,00,000 on his instruction on Thursday at 15:52</strong>,
which puts risk at &#8377;1,000 and deploy at &#8377;1,00,000 per trade, with risk_pct sitting on its 0.10%
floor. That figure covers his whole account including &#8377;3.46L of legacy holdings this book never
trades; our side of it is about &#8377;6.55L. <b>Raised with him, not acted on.</b></p>

<h3 class="sub" id="pre-diary">The diary</h3>
<div class="scroll"><table><thead><tr><th class="l">when</th><th class="l">event</th><th class="l">why it matters</th></tr></thead><tbody>
<tr><td class="l"><b>Fri 20 Nov</b></td><td class="l"><b>SHUKRAPHAR becomes SHUKRAMED</b></td><td class="l">Held in all three with a stop resting at <b>79.25</b> under the old symbol. Whether the GTT migrates is <b>unverified</b>. It is 3.6% from that stop. <b>Check it at the open, not after.</b></td></tr>
<tr><td class="l">Fri 20 Nov</td><td class="l">Crystal Crop Protection closes</td><td class="l"><b>AVOID</b> on the case &mdash; see the IPO review below.</td></tr>
<tr><td class="l">Mon 23 Nov</td><td class="l">Mahanadi Coalfields closes</td><td class="l">&#8377;129&ndash;136, &#8377;8,981 Cr, <b>100% offer-for-sale</b> by Coal India, premium inert near &#8377;4. <b>SKIP</b> as a trade.</td></tr>
</tbody></table></div>

<h3 class="sub" id="pre-decisions">Waiting on a decision</h3>
<ul>
<li>🔴 <strong>SHUKRAPHAR&rsquo;s stop, tomorrow morning.</strong> Three accounts, one symbol change, a
stop at 79.25 that is 3.6% away and may or may not survive the rename. <b>This is the only item on this
list with a deadline.</b></li>
<li>🔴 <strong>The follow-through date.</strong> MarketSmith says 15 October, our record says 2 November.
Both produce CONFIRMED_UPTREND today, so nothing is currently mis-gated &mdash; but the gate counts age
from that date, and the two answers differ by eighteen days. <b>It has been carried unresolved for a week.</b></li>
<li>🔴 <strong>The report hides rows without saying so.</strong> <code>--top</code> is 25 and tonight there
were 30 actionable. The fix is to print the number cut, not to raise the limit. <b>His call.</b></li>
<li><strong>The stop buffer, still unmeasured.</strong> <code>structural &times; 0.98</code> against
<code>structural</code> across the whole closed book. Proposed on the 19th, not yet run, needs his yes.</li>
<li><strong>Parking in akul and t-ramprasad</strong> contradicts the older &ldquo;keep their cash
free&rdquo; policy. It is there on his explicit override; the contradiction is noted, not resolved.</li>
<li><strong>t-default carries one stop more than it has stoppable positions</strong> &mdash; 24 triggers
against 11 resting entries and 13 stops, consistent with the carried orphan stop records ACMESOLAR,
GLAND and LAURUSLABS. <b>Never cancelled silently.</b></li>
<li><strong>BMWVENTLTD is held in akul and Ram but rests as an unfilled entry in t-default</strong>, which
breaks the rule that all three accounts hold the same names. Saying it out loud is the rule.</li>
<li><strong><code>show_ipos</code> has been unable to read its source for five nights.</strong> The
machine-built &ldquo;IPOs &mdash; mainboard&rdquo; section further down <b>falsely says no mainboard issue
is open</b>. Two are. The hand-written IPO review is the one to read.</li>
</ul>
<p class="note">Built Thursday 19 November 2026 after the close, from the service&rsquo;s records, a live
read of all three brokers, tonight&rsquo;s hand-run scans (SWING 491, STRIKE 492, WEEKLY 493, ETF 494,
ETF_WEEKLY 495, REVERSAL 498), the 17-index distribution-day count, the MarketSmith mail of 19 Nov 17:04
read in full, and recorded FII/DII flows to the 18th. Closes are Thursday&rsquo;s. Nothing here places an
order.</p>
"""


PREMARKET_2026_11_23 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Friday was the best index day of the week and <strong>it made the divergence
worse, not better</strong>. The Nifty closed <strong>+1.12% at 25,800.60</strong> &mdash; a fourth
straight weekly gain, with <strong>Bank Nifty at a record</strong> and eleven of seventeen indices
higher. Breadth fell from 60.25% to <strong>53.59%</strong> while its prior-five mean fell from
68.29% to <strong>65.13%</strong>. <strong>The gap widened from 8.04 points to 11.54</strong>, which
is wider than it was on Wednesday, before Thursday&rsquo;s repair. Entries stay blocked, on breadth,
for a <strong>sixth consecutive session</strong>, and <strong>none of the thirty-seven actionable
SWING names may be placed.</strong> (The glance bar above counts 74 across all six scanners; 37 is
the SWING list alone.)</p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes are
Friday 20 November&rsquo;s. All six scanners were re-run by hand against them in the small hours of
Saturday &mdash; SWING 01:38, WEEKLY 01:49, ETF 02:14, ETF_WEEKLY 02:15, STRIKE 02:16, REVERSAL 02:27
IST &mdash; so the page carries Friday&rsquo;s prices, not Saturday&rsquo;s date.</p>
<p class="note"><strong>Read the sign, not the size.</strong> A 1.12% index day that takes breadth
down six and a half points is not a rally the market joined; it is money moving into fewer names.
Bank led at <b>+2.49%</b>, Financial Services <b>+2.02%</b>, Realty <b>+1.71%</b> &mdash; and
<b>Media fell 1.68%</b> while the India VIX rose <b>7.51% to 17.32</b> on a day the index closed at
its highest of the month. <strong>Fear and the index rose together</strong>, which is the shape of a
narrow tape, and it is the same shape MarketSmith described in Friday&rsquo;s evening mail.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l"><b>53.59% against 65.13%</b> &mdash; an <b>11.54-point gap, against 8.04 on Thursday</b>. The lowest breadth reading in the thirty sessions on record here</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">CONFIRMED_UPTREND on the Nifty, <b>0 distribution days</b>, day 21, follow-through still dated <b>2 November</b></td><td class="l pass"><span>OPEN</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED_UPTREND, <b>2 distribution days</b> &mdash; agreeing on the verdict a third session, disagreeing on the count</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">The follow-through date, theirs against ours</td><td class="l">MarketSmith dates it <b>15 October</b>; our record says <b>2 November</b>. Unchanged, unsettled, and carried for a fourth session</td><td class="l warn"><span>unresolved</span></td></tr>
<tr><td class="l"><b>IT</b> &mdash; our own status</td><td class="l"><b>DOWNTREND</b>, 9 distribution days, rally attempt on day 2. MarketSmith still reads it UPTREND UNDER PRESSURE</td><td class="l fail"><span>no buys there</span></td></tr>
</tbody></table></div>
<p class="note"><strong>One status actually changed, and it changed downward.</strong> IT was a
CONFIRMED UPTREND on Thursday with eight distribution days; it took a ninth on Friday &mdash; on a
<b>+1.30%</b> day for the sector &mdash; and fell to DOWNTREND, which bars buying there outright
regardless of breadth. <strong>MarketSmith has not made the same call</strong>, and that disagreement
is now the second standing one on this page.</p>

<h3 class="sub" id="pre-indices">Why a +1.12% day cost six points of breadth</h3>
<p class="sub">Each index&rsquo;s move over the last <strong>five sessions</strong>, to Friday&rsquo;s
close. The large-cap benchmarks are up; everything we actually buy from is flat or down.</p>
<svg viewBox="0 0 470 248" width="100%" style="max-width:640px" role="img" aria-label="Five-session move by index to Friday 20 November"><line x1="230.0" y1="0" x2="230.0" y2="242" stroke="var(--rule,#d8d4cc)" stroke-width="1"/><text x="0" y="8" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">PSU Bank</text><rect x="232.0" y="0" width="194.9" height="9" rx="2" fill="var(--green)"/><text x="430.9" y="8" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+6.72%</text><text x="0" y="22" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Bank</text><rect x="232.0" y="14" width="171.1" height="9" rx="2" fill="var(--green)"/><text x="407.1" y="22" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+5.90%</text><text x="0" y="36" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Fin Services</text><rect x="232.0" y="28" width="105.8" height="9" rx="2" fill="var(--green)"/><text x="341.9" y="36" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.65%</text><text x="0" y="50" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">FMCG</text><rect x="232.0" y="42" width="105.3" height="9" rx="2" fill="var(--green)"/><text x="341.3" y="50" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.63%</text><text x="0" y="64" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Auto</text><rect x="232.0" y="56" width="89.0" height="9" rx="2" fill="var(--green)"/><text x="325.0" y="64" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+3.07%</text><text x="0" y="78" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Nifty 50</text><rect x="232.0" y="70" width="75.7" height="9" rx="2" fill="var(--green)"/><text x="311.7" y="78" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+2.61%</text><text x="0" y="92" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Realty</text><rect x="232.0" y="84" width="55.7" height="9" rx="2" fill="var(--green)"/><text x="291.7" y="92" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.92%</text><text x="0" y="106" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Healthcare</text><rect x="232.0" y="98" width="40.6" height="9" rx="2" fill="var(--green)"/><text x="276.6" y="106" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+1.40%</text><text x="0" y="120" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Next 50</text><rect x="232.0" y="112" width="13.3" height="9" rx="2" fill="var(--series-1)"/><text x="249.3" y="120" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.46%</text><text x="0" y="134" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Midcap 150</text><rect x="232.0" y="126" width="9.0" height="9" rx="2" fill="var(--series-1)"/><text x="245.0" y="134" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.31%</text><text x="0" y="148" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Cons Durables</text><rect x="232.0" y="140" width="3.8" height="9" rx="2" fill="var(--series-1)"/><text x="239.8" y="148" text-anchor="start" fill="var(--muted)" font-size="9" font-family="var(--mono)">+0.13%</text><text x="0" y="162" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Media</text><rect x="224.8" y="154" width="3.2" height="9" rx="2" fill="var(--amber)"/><text x="220.8" y="162" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.11%</text><text x="0" y="176" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Energy</text><rect x="221.9" y="168" width="6.1" height="9" rx="2" fill="var(--amber)"/><text x="217.9" y="176" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.21%</text><text x="0" y="190" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Pharma</text><rect x="212.9" y="182" width="15.1" height="9" rx="2" fill="var(--amber)"/><text x="208.9" y="190" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-0.52%</text><text x="0" y="204" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Smallcap 100</text><rect x="196.7" y="196" width="31.3" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="192.7" y="204" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-1.08%</text><text x="0" y="218" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">IT</text><rect x="172.6" y="210" width="55.4" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="168.6" y="218" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-1.91%</text><text x="0" y="232" fill="var(--ink-2)" font-size="10" font-family="var(--mono)">Metal</text><rect x="141.6" y="224" width="86.4" height="9" rx="2" fill="var(--red,#dc2626)"/><text x="137.6" y="232" text-anchor="end" fill="var(--muted)" font-size="9" font-family="var(--mono)">-2.98%</text></svg>
<p class="note"><strong>The spread is the whole story and it has widened again.</strong> Over the week
the <b>Nifty 50 is +2.61%</b> while <b>Smallcap 100 is &minus;1.08%</b>, <b>Midcap 150 +0.31%</b> and
<b>Next 50 +0.46%</b>. <b>PSU Bank +6.72%</b> and <b>Bank +5.90%</b> carried it; <b>Metal &minus;2.98%</b>
and <b>IT &minus;1.91%</b> paid for it. Over twenty sessions the same split holds &mdash; Nifty
<b>+14.16%</b>, Smallcap <b>+9.61%</b>, IT <b>&minus;2.10%</b>. <strong>A gate that reads
participation rather than price is doing exactly what it was built to do here:</strong> the index is
making highs out of five sectors, and the half of the market our setups live in has gone sideways for
a fortnight.</p>

<h3 class="sub" id="pre-regime">Regime, after the best day of the week</h3>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">our status</th><th class="l">what changed on Friday</th></tr></thead><tbody>
<tr><td class="l"><b>IT</b></td><td class="bad">9</td><td class="l fail"><span>DOWNTREND</span></td><td class="l fail"><b>downgraded from CONFIRMED UPTREND</b> on a +1.30% session &mdash; a ninth distribution day, and a rally attempt now on day 2</td></tr>
<tr><td class="l"><b>CONSUMER DURABLES</b></td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass"><b>upgraded from UNDER PRESSURE</b> &mdash; three distribution days expired and none replaced them</td></tr>
<tr><td class="l"><b>METAL</b></td><td class="bad">7</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail">a seventh distribution day &mdash; <b>still the worst-rated sector</b>, and &minus;2.98% on the week</td></tr>
<tr><td class="l"><b>SMALLCAP</b></td><td class="bad">5</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l warn">8 distribution days to 5, but <b>still the only broad index unconfirmed</b>, on day 20 of its attempt</td></tr>
<tr><td class="l"><b>ENERGY</b></td><td>3</td><td class="l warn"><span>UNDER PRESSURE</span></td><td class="l warn">4 to 3 and no upgrade. <b>MarketSmith reads this one CONFIRMED UPTREND</b></td></tr>
<tr><td class="l">NEXT 50 &middot; MIDCAP 150</td><td>2 &middot; 1</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">both improved &mdash; Next 50 from 4, Midcap from 2</td></tr>
<tr><td class="l">NIFTY &middot; BANK &middot; PSU BANK &middot; REALTY</td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">clean, and they are the four carrying the month</td></tr>
</tbody></table></div>
<p class="note"><strong>Distribution days came off across the board and the gate did not move.</strong>
Next 50, Midcap, Smallcap, Energy and Consumer Durables all improved their counts &mdash; because
distribution days <em>expire with time</em>, not because Friday was good. <strong>Breadth cannot
expire.</strong> It is recomputed from the close every session, and on Friday it fell.</p>

<h3 class="sub" id="pre-today">What Friday did to the book: nothing at all</h3>
<div class="scroll"><table><thead><tr><th class="l">name</th><th class="l">what happened</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l">Every open position</td><td class="l"><b>Not one stop was hit</b> in any of the three accounts &mdash; the first session this week without a stop-out.</td><td class="l pass"><span>34 open, unchanged</span></td></tr>
<tr><td class="l">Ten resting entries</td><td class="l">TIMEX, DIVISLAB, SANSERA, PTCIL, LALITHAA, RUBICON, CPPLUS, RATNAVEER, TFCILTD, LTTS &mdash; <b>none fired, for a second session running</b>, on a day the Nifty rose 1.12%. Ram carries an eleventh, an MCX add at 3,780.15.</td><td class="l warn"><span>the tape went up and our names did not</span></td></tr>
<tr><td class="l">Cash against those entries</td><td class="l">&#8377;65,56,494 held; <b>&#8377;28,45,896 would be spent if every resting order fired</b> against <b>&#8377;74,769 of free cash</b> across all three. t-default holds &#8377;38.2L of LIQUIDCASE parking behind that; akul and Ram do not.</td><td class="l warn"><span>short in all three if they all fire</span></td></tr>
<tr><td class="l"><b>SHUKRAMED</b> &mdash; fault cleared</td><td class="l">Friday&rsquo;s open fault is <b>closed</b>. The SHUKRAPHAR renaming had cut the position loose; on <b>21 November</b> the holding was adopted in all three accounts and reconciled, and a live <b>SELL stop now rests at 79.25</b> against all of it &mdash; 2,000 / 379 / 265, <b>2,644 shares</b>. Risk across the three is <b>&#8377;9,241</b>. That 79.25 is the original structural level and was never breached, so no new stop had to be invented. One gap remains: the rename leaves too few unbroken daily bars under the new symbol, so <b>this page carries no chart for SHUKRAMED</b>.</td><td class="l pass"><span>protected in all three</span></td></tr>
<tr><td class="l">Stale stop records</td><td class="l"><b>Swept.</b> ACMESOLAR, GLAND, LAURUSLABS, PAYTM, SSWL and SHYAMMETL carried stop rows against trades already closed &mdash; <b>18 rows across the three accounts</b>, not the six names this page counted on Friday, and every one of them already gone at the broker. All were retired on <b>21 November</b> by <code>prune_stale_stops</code>; a re-run reports nothing stale in any account, and <code>reconcile_positions</code> finds <b>no SEVERE findings</b> anywhere. They were records rather than risk &mdash; but they were the records the daily stop check reads, which is why nothing ever reported them.</td><td class="l pass"><span>record cleared</span></td></tr>
<tr><td class="l">MarketSmith, Friday 11:49</td><td class="l">Removed <b>PAYTM</b> from the model portfolio at <b>&minus;9%</b>, four days after adding it on the 17th. <b>Our stop took us out on Thursday</b>, a day ahead of them, at &minus;&#8377;9,342.20.</td><td class="l"><span>out first, for once</span></td></tr>
</tbody></table></div>
<p class="note"><strong>SHUKRAMED is the one thing on this page that is not a matter of opinion.</strong>
A corporate renaming moved the holding to a ticker the service does not recognise, so it is counted as
somebody else&rsquo;s stock, excluded from the book, and left without a resting stop in any account.
<b>It is the only unprotected position across the three.</b> It needs an <code>adopt_holding</code>
under the new symbol and a stop rested against it before the open, and that is a decision for Divyansh,
not something to be done quietly overnight.</p>

<h3 class="sub" id="pre-risk">What is closest to being stopped out next</h3>
<p class="sub">Distance from Friday&rsquo;s close to the resting stop, for the tightest of
<strong>34 open rows</strong>. LIQUIDCASE is parking and is excluded.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>move</th><th>to stop</th><th>open R</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>BMWVENTLTD</b></td><td class="bad">&minus;3.4%</td><td class="bad"><b>1.1%</b></td><td class="bad">&minus;0.76R</td><td class="l">382 in akul, 546 in Ram, none in t-default &mdash; <b>the tightest thing in the book</b>, and the name is closed to new buying</td></tr>
<tr><td class="l"><b>MCX</b></td><td class="bad">&minus;5.0%</td><td class="bad"><b>1.5%</b></td><td class="bad">&minus;0.78R</td><td class="l">held in t-default and akul &mdash; and <b>on MarketSmith&rsquo;s buy watchlist at the same time</b>, with an add resting at 3,780.15 in Ram</td></tr>
<tr><td class="l">SONACOMS</td><td class="bad">&minus;3.0%</td><td>2.8%</td><td class="bad">&minus;0.52R</td><td class="l">held in all three, stop at the structural level since entry</td></tr>
<tr><td class="l">KRISHANA</td><td>&minus;3.1%</td><td>3.4%</td><td>&minus;0.49R</td><td class="l">held in all three; Ram&rsquo;s leg is the only one green, at +1.2%</td></tr>
<tr><td class="l">SBC</td><td class="pass">+2.8%</td><td>4.3%</td><td class="pass">+0.85R</td><td class="l">the stop has been moved up to 65.66, locking &minus;0.50R rather than a full one</td></tr>
<tr><td class="l">CUPID</td><td class="pass">+5.7%</td><td>5.4%</td><td class="pass">+1.21R</td><td class="l">stop sits <b>at the entry price</b> &mdash; it can no longer lose</td></tr>
<tr><td class="l"><b>SGMART</b></td><td class="pass">+17.0%</td><td>14.5%</td><td class="pass"><b>+4.01R</b></td><td class="l">the best position in the book by a distance, and also stopped at entry</td></tr>
</tbody></table></div>
<p class="note"><strong>Two names are inside two percent of their stops and both are losers.</strong>
BMWVENTLTD and MCX carry about 1.5R of open loss between them and would be gone on a bad Monday in the
small caps &mdash; which is the half of the market that has now been flat or falling for three straight
weeks. <strong>Against that, two names can no longer lose:</strong> CUPID in all three accounts and
SGMART in the two that hold it have their stops at the entry price &mdash; five legs in all, with
SGMART alone carrying <b>+4R</b>. SBC is not one of them: its stop has been raised but still sits
below entry, locking &minus;0.50R rather than nothing. The book is not
in trouble; it is simply not being added to, and has not been for six sessions.</p>

<h3>The weekend mail, read in full</h3>
<p><strong>One MarketSmith email arrived over the weekend</strong> &mdash; the Weekly Report, at
<b>09:31 on Saturday 21 November</b>. Nothing came on Sunday. It carries <strong>no new Big Picture
status and no new distribution-day count</strong>, so the status this page is built on is still
Friday&rsquo;s, unchanged.</p>
<p>What it does is <strong>repeat Friday&rsquo;s reading in its own words</strong>. Its headline is
<em>Nifty&rsquo;s Bank-Powered Climb Continues</em>: Bank Nifty through <b>64,000 for the first time</b>,
pulling the Nifty to a ten-month high and a fourth straight weekly gain, <em>&ldquo;even as a global AI
selloff tested nerves&rdquo;</em> &mdash; the same narrow tape this page describes above, from the same
close. Its sector line is that <strong>IT and Metal have slipped to Under Pressure</strong>, which is
<strong>exactly what the regime table below already carries</strong> for both: it confirms Friday, it
does not move it. On IT our own status is a step worse than theirs and stays so.</p>
<p>Its idea list names five &mdash; <b>Rubicon Research</b>, <b>Raghav Productivity Enhancers</b>,
Engineers India, Apollo Micro Systems and <b>Acutaas Chemicals</b>. <strong>Three of those five are
Friday&rsquo;s buy watchlist again</strong> (Raghav, Rubicon and Acutaas, at ranks 1, 2 and 3), and
<strong>Rubicon is already one of our ten resting entries</strong>. Engineers India and Apollo Micro
Systems are the only two names in the weekend mail that were not in front of us on Friday, and
neither is in the book or on a trigger.</p>
<p class="note">The rest of the mail is a table of contents pointing at the web report &mdash; a market
outlook, a featured article on a subsidiary trading above its parent, and a learning piece on selling
discipline. <strong>There is nothing in it that changes a stop, a trigger or the gate.</strong>
It is on this page because it was read, and because a weekend that adds nothing is itself worth
recording: the page you are reading was built on Friday&rsquo;s close and the weekend did not
overtake it.</p>
"""


PREMARKET_2026_11_25 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead"><strong>There has been no session since Monday.</strong> Tuesday 24 November was an
NSE holiday (Prakash Gurpurb Sri Guru Nanak Dev), so every price on this page is
<strong>Monday 23 November&rsquo;s close</strong> and nothing about the tape has changed in
forty-eight hours. What Monday did was make the gate worse. Breadth fell to
<strong>46.15%</strong> against a prior-five mean of <strong>60.66%</strong> &mdash; a
<strong>14.51-point gap</strong>, against 11.54 on Friday and 8.04 on Thursday. It is
<strong>the lowest breadth reading in the thirty sessions on record here</strong>, and the widest
gap. Entries stay blocked, on breadth, for a <strong>seventh consecutive session</strong>, and
<strong>none of the thirty actionable SWING names may be placed.</strong></p>
<p class="sub"><strong>Nothing here is an instruction and nothing here was placed.</strong> Closes
are Monday 23 November&rsquo;s. The six scanners were run against those closes on Monday evening
&mdash; SWING 20:31, WEEKLY 20:43, ETF 21:11, ETF_WEEKLY 21:11, STRIKE 21:12, REVERSAL 21:24 IST
&mdash; and <strong>they were deliberately not re-run for this page</strong>: with no new close there
is no new input, and a second run would reproduce Monday&rsquo;s list exactly while costing an hour
of compute. <strong>MarketSmith&rsquo;s pre-market mail for Wednesday arrived at 09:00 and this page has
been refreshed with it</strong> &mdash; both mails are read in full below. Nothing in it changes the
breadth reading, which is computed from closes and there has been no close since Monday.</p>
<p class="note"><strong>The index fell 1.75% and the banks did it.</strong> Nifty
<b>25,349.65</b>, down 1.75%, opening at 25,929.15 and closing a whisker above its own low of
25,343.85 &mdash; <b>eleven advances against thirty-nine declines</b> on volume
<b>21.17% higher at 518.92m</b>, which is the definition of a distribution day and took
MarketSmith&rsquo;s count from two to <b>three</b>. <b>Bank Nifty fell 3.17% from a record high</b>
set days earlier; Metal <b>&minus;3.68%</b>, PSU Bank <b>&minus;3.25%</b>, Private Bank
<b>&minus;3.19%</b>. <b>IT was the only real gainer, +1.69%</b> &mdash; the sector this service&rsquo;s
own regime map has been refusing to buy for a week.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l">Breadth vs its prior-5 mean</td><td class="l"><b>46.15% against 60.66%</b> &mdash; a <b>14.51-point gap</b>, against 11.54 on Friday. <b>The lowest breadth and the widest gap in the thirty sessions recorded here</b></td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l">Our computed status</td><td class="l">CONFIRMED_UPTREND on the Nifty, <b>1 distribution day</b> (from 0), attempt day 22, follow-through still dated <b>2 November</b></td><td class="l pass"><span>OPEN</span></td></tr>
<tr><td class="l">MarketSmith&rsquo;s status</td><td class="l">CONFIRMED UPTREND. Their Monday evening mail counted <b>3 distribution days</b>; <b>Wednesday&rsquo;s pre-market mail counts 2</b> &mdash; one aged out across the holiday, so the session that took them to three has already been partly undone. Fifth session agreeing on the verdict, disagreeing on the count</td><td class="l pass"><span>open</span></td></tr>
<tr><td class="l">The follow-through date, theirs against ours</td><td class="l">MarketSmith dates it <b>15 October</b>; our record says <b>2 November</b>. Unchanged, unsettled, carried for a sixth session</td><td class="l warn"><span>unresolved</span></td></tr>
<tr><td class="l">Their own warning</td><td class="l">The 23 Nov mail says in terms that <b>a higher distribution count or a breach of key support would take them to UPTREND UNDER PRESSURE</b>. They are one bad session from downgrading</td><td class="l warn"><span>on notice</span></td></tr>
</tbody></table></div>
<p class="note"><strong>The two gates have now disagreed for seven sessions, and the disagreement is
getting wider rather than resolving.</strong> The market-status gate reads OPEN because the Nifty is
in a confirmed uptrend near its highs; the breadth gate reads SHUT because the number of stocks
participating has collapsed to 46%. <strong>Monday is the cleanest example yet of why the second
gate exists:</strong> the index fell 1.75% on 11 advances against 39 declines, which is a narrow tape
going down for the same reason it had been going narrowly up &mdash; the money is in five or six
names and it moved. <b>A gate built on the index alone would not have seen a thing until Monday.</b></p>

<h3 class="sub" id="pre-indices">Where Monday&rsquo;s damage landed</h3>
<p class="sub">MarketSmith&rsquo;s sector moves for the <strong>23 November</strong> session, as their
evening Big Picture prints them. The banks and metals paid for the whole fall; only three indices
closed green.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>23 Nov move</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>Nifty IT</b></td><td class="pass">+1.69%</td><td class="l">the best sector of the day &mdash; and the one <b>our own regime map rates RALLY ATTEMPT on 9 distribution days</b>, which bars buying there</td></tr>
<tr><td class="l">Consumer Durables</td><td class="pass">+0.59%</td><td class="l">one of only three green closes</td></tr>
<tr><td class="l">Realty</td><td class="pass">+0.31%</td><td class="l">the third</td></tr>
<tr><td class="l">Auto</td><td class="bad">&minus;1.03%</td><td class="l">the mildest of the fallers</td></tr>
<tr><td class="l">Energy</td><td class="bad">&minus;1.78%</td><td class="l">our status on Energy is a step worse than theirs and has been for a week</td></tr>
<tr><td class="l">PSE &middot; Oil &amp; Gas</td><td class="bad">&minus;1.98% &middot; &minus;2.01%</td><td class="l">&mdash;</td></tr>
<tr><td class="l">Financial Services</td><td class="bad">&minus;2.49%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>Private Bank &middot; PSU Bank &middot; Bank</b></td><td class="bad">&minus;3.19% &middot; &minus;3.25% &middot; &minus;3.17%</td><td class="l"><b>Bank Nifty fell 3.17% from a record high.</b> The index that carried the whole of November gave back a chunk of it in one session</td></tr>
<tr><td class="l"><b>Nifty Metal</b></td><td class="bad">&minus;3.68%</td><td class="l">the worst sector of the day, with <b>Tata Steel &minus;8.43%</b> inside it</td></tr>
<tr><td class="l">Midcaps &middot; Smallcaps</td><td class="bad">&minus;1.01% &middot; &minus;0.66%</td><td class="l"><b>both fell less than the Nifty</b> &mdash; for the first time in weeks the broad market was not the thing being sold</td></tr>
</tbody></table></div>
<p class="note"><strong>The last row is the one worth keeping.</strong> For three weeks this page has
recorded a large-cap index making highs while midcaps and smallcaps went nowhere. On Monday that
reversed: the Nifty fell <b>1.75%</b> while midcaps fell <b>1.01%</b> and smallcaps <b>0.66%</b>.
<strong>That is not yet good news</strong> &mdash; everything fell &mdash; but it is the first session in
which the half of the market our setups live in outperformed, and if it repeats it is what the
breadth gate re-opening would look like from the inside. <b>One session is not a signal.</b>
Biggest fallers: Tata Steel &minus;8.43%, Axis &minus;3.97%, HDFC Bank &minus;3.33%, ICICI
&minus;3.32%, Hindalco &minus;3.13%, SBI &minus;2.79%, L&amp;T &minus;2.59%, Kotak &minus;2.51%.
Biggest gainers: TCS +3.53%, Shriram Finance +2.46%, Tech Mahindra +1.79%, HCL Tech +1.48%,
Titan +1.30%.</p>

<h3 class="sub" id="pre-regime">Regime, on Monday&rsquo;s close</h3>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">our status</th><th class="l">what changed since Friday</th></tr></thead><tbody>
<tr><td class="l"><b>NIFTY</b></td><td>1</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l warn"><b>took its first distribution day</b> &mdash; 0 to 1, on day 22 of the attempt. MarketSmith counts 3</td></tr>
<tr><td class="l"><b>METAL</b></td><td class="bad">9</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail"><b>7 to 9 in one session</b> &mdash; the worst-rated sector, and &minus;3.68% on Monday</td></tr>
<tr><td class="l"><b>IT</b></td><td class="bad">9</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l warn"><b>back up from DOWNTREND</b> &mdash; the attempt is on day 3 after Monday&rsquo;s +1.69%. Still 9 distribution days, still no buys</td></tr>
<tr><td class="l"><b>ENERGY</b></td><td class="bad">6</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l fail"><b>downgraded from UNDER PRESSURE</b>, 3 distribution days to 6. <b>MarketSmith still reads it CONFIRMED UPTREND</b></td></tr>
<tr><td class="l"><b>SMALLCAP</b></td><td class="bad">7</td><td class="l fail"><span>RALLY ATTEMPT</span></td><td class="l warn">5 to 7, on day 21 &mdash; <b>still the only broad index never confirmed</b></td></tr>
<tr><td class="l">NEXT 50 &middot; MIDCAP 150</td><td>2 &middot; 2</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">both unchanged</td></tr>
<tr><td class="l">BANK &middot; PSU BANK &middot; REALTY &middot; CONS DURABLES</td><td class="pass">0</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">clean counts &mdash; <b>including Bank, on the day it fell 3.17%</b>: one heavy down day is not a distribution day unless the volume test is met too</td></tr>
<tr><td class="l">AUTO &middot; FIN SERVICES &middot; FMCG &middot; PHARMA &middot; HEALTHCARE</td><td>1</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">unchanged</td></tr>
<tr><td class="l">MEDIA</td><td>2</td><td class="l pass"><span>CONFIRMED UPTREND</span></td><td class="l pass">unchanged</td></tr>
</tbody></table></div>
<p class="note"><strong>Four sectors took distribution days on Monday and two of them took two.</strong>
Metal went 7 to 9, Smallcap 5 to 7, Energy 3 to 6, and the Nifty itself took its first. <strong>This
is the opposite of last Friday</strong>, when five counts fell because distribution days expire with
time rather than because anything improved. <b>MarketSmith&rsquo;s own sector block disagrees with
ours in two places</b> and has done for a week: they read Energy as a Confirmed Uptrend where we read
a rally attempt on six distribution days, and they have IT and Metal at Uptrend Under Pressure where
we rate both rally attempts on nine. <strong>Where they and we disagree, the stricter reading is the
one the gate uses</strong>, and on both names that is ours.</p>

<h3 class="sub" id="pre-today">What changed in two days: nothing on the tape, a great deal in the book</h3>
<div class="scroll"><table><thead><tr><th class="l">what</th><th class="l">what happened</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l"><b>Close-based stops &mdash; RE-ARMED</b></td><td class="l">On his instruction on <b>23 November</b> the close-based stop rule was switched back on, reversing the 6 November disarming. A stop is now judged on <b>the close</b>; the trigger that rests at the broker is a disaster floor <b>5% beneath the structural level</b>, not the decision itself. <b>All 34 legs across the three accounts were re-rested the same evening</b> &mdash; each new trigger placed before the old one was cancelled, so nothing was ever uncovered.</td><td class="l pass"><span>34 legs moved</span></td></tr>
<tr><td class="l">Sizing, deliberately unchanged</td><td class="l">Position sizes were <b>not</b> re-cut to the new, wider floor. He was told plainly that this widens the worst case from roughly 8% to roughly 12% on a gap-through, and chose to leave sizing alone.</td><td class="l warn"><span>his call, on the record</span></td></tr>
<tr><td class="l">The exit review, published</td><td class="l">Every position closed in the last month was measured after the fact: <b>30 closes, 13 names, &minus;&#8377;1,35,508 realised</b>, and of the nine names with sessions since the sale <b>all nine printed back above the exit price</b>, six still trade above it, median drift <b>+4.3%</b>. That measurement is what the re-arming above answers.</td><td class="l pass"><span>on the site</span></td></tr>
<tr><td class="l">Monday&rsquo;s three stop-outs, as evidence</td><td class="l"><b>MCX</b> level 3,481.30, low 3,455.00, <b>close 3,581.60</b> &mdash; it would have held. <b>KRISHANA</b> level 237.89, low 237.50 &mdash; <b>sold by thirty-nine paise</b> &mdash; <b>close 241.26</b>. <b>BMWVENTLTD</b> level 63.50, low 61.62, <b>close 63.31</b> &mdash; a genuine break. Two of the three were wicks.</td><td class="l warn"><span>two of three</span></td></tr>
<tr><td class="l">The book</td><td class="l"><b>32 open rows, 12 names</b>, across the three accounts, read at the broker at 00:37 this morning. Nothing has moved since Monday because nothing could.</td><td class="l"><span>unchanged</span></td></tr>
<tr><td class="l"><b>Open item &mdash; the resting entries</b></td><td class="l">The broker order book <b>showed no pending orders in any of the three accounts</b> when it was read at 00:37 IST. Monday&rsquo;s eight resting entries were at-the-open orders, which lapse with the session, and overnight reads do not list standing triggers alongside day orders &mdash; so this is <b>not</b> evidence that the stops are gone. <b>It is also not proof they are there.</b> Both have to be verified against the broker at the open, before anything else is done.</td><td class="l warn"><span>verify at 09:00</span></td></tr>
<tr><td class="l"><b>Open item &mdash; MCX in Ram</b></td><td class="l">A live BUY add still rests at <b>3,780.15</b> in t-ramprasad &mdash; roughly 8.8% above the level the same name was stopped out at on Monday. It was <b>not</b> cancelled, because cancelling an entry silently is not something this service does. <b>MarketSmith has MCX on its buy watchlist</b> in the same mail.</td><td class="l warn"><span>his call</span></td></tr>
</tbody></table></div>
<p class="note"><strong>The re-arming is the most consequential change this book has made in a month,
and it is worth stating what it does and does not fix.</strong> It stops the service being sold by a
wick: a position now has to <em>close</em> below its level to be exited, and Monday&rsquo;s MCX and
KRISHANA are two examples from a single session of trades that would have survived. <strong>It also
roughly doubles the bad tail.</strong> A name that gaps straight through and keeps falling is now
held to a floor 5% lower, on unchanged size, so the loss on that trade is about half as large again
as it would have been. <b>That trade-off was put to him explicitly and he took it.</b> Post-exit
drift is not a backtest of holding on, and this page will not pretend otherwise &mdash; the honest
claim is narrow: the old rule was firing on the wrong event.</p>

<h3 class="sub" id="pre-risk">What is closest to being stopped out next</h3>
<p class="sub">Distance from Monday&rsquo;s close to <strong>two</strong> levels now, which is the
point of the re-arming: the <strong>structural stop</strong>, judged on a close, and the
<strong>resting trigger</strong> 5% beneath it, which only a disaster reaches intraday.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>move</th><th>to stop (close)</th><th>to trigger</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>SONACOMS</b></td><td class="bad">&minus;3.6%</td><td class="bad"><b>1.6%</b></td><td>6.5%</td><td class="l">held in all three &mdash; <b>the tightest thing in the book</b>, and on MarketSmith&rsquo;s model portfolio, where it fell 0.73% on Monday</td></tr>
<tr><td class="l"><b>LENSKART</b></td><td class="bad">&minus;2.8%</td><td class="bad"><b>1.8%</b></td><td>6.7%</td><td class="l">held in all three, as an add. <b>Also on MarketSmith&rsquo;s buy watchlist</b> in the same mail that has it two percent above our stop</td></tr>
<tr><td class="l">SBC</td><td class="pass">+1.6%</td><td>3.2%</td><td>8.1%</td><td class="l">two legs in every account, base and add, with separate levels at 65.87 and 64.56</td></tr>
<tr><td class="l">CUPID</td><td class="pass">+4.7%</td><td>4.5%</td><td>9.3%</td><td class="l">stop sits <b>at the entry price</b> &mdash; it can no longer lose</td></tr>
<tr><td class="l">SHUKRAMED</td><td class="pass">+6.4%</td><td>6.0%</td><td>10.7%</td><td class="l">the renamed position, protected in all three since 21 November</td></tr>
<tr><td class="l">TFCILTD</td><td>+0.2%</td><td>6.6%</td><td>11.3%</td><td class="l">Ram only &mdash; he bought it himself on Monday and it was adopted and protected the same hour</td></tr>
<tr><td class="l"><b>SGMART</b></td><td class="pass">+10.6%</td><td>9.6%</td><td>14.1%</td><td class="l">stopped at entry, and the best position in the book</td></tr>
<tr><td class="l">AARTIPHARM &middot; RATNAVEER &middot; ROSSTECH</td><td class="pass">+3.8% &middot; +5.4% &middot; +3.1%</td><td>10.3% &middot; 10.2% &middot; 10.0%</td><td>14.8% &middot; 14.7% &middot; 14.5%</td><td class="l">the three furthest from trouble</td></tr>
</tbody></table></div>
<p class="note"><strong>Two names sit inside two percent of their stops and both are losers</strong>
&mdash; SONACOMS at &minus;3.6% and LENSKART at &minus;2.8%, each held in all three accounts.
<strong>Under the old rule either could have been taken out by a single bad morning;</strong> under
the re-armed one they have to close below 872.10 and 701.50 respectively, and the broker&rsquo;s own
triggers sit a further five percent down at 828.50 and 666.43. <b>That is the change doing its work,
and it is also the change costing money if either keeps falling.</b> Against them, <b>CUPID and
SGMART cannot lose</b> &mdash; both stopped at entry, SGMART at +10.6%.</p>

<h3>MarketSmith, 25 November 09:00 &mdash; the Wednesday pre-market mail, read in full</h3>
<p><strong>It arrived at 09:00 and it is a gap-up note against a falling world.</strong> At 08:15 IST
GIFT Nifty futures were <b>25,754</b> against Monday&rsquo;s close of <b>25,349.65</b> &mdash; about
<b>404 points, 1.6%</b> &mdash; which would open the index back above where it broke on Monday. <b>Their
own body quotes two different figures for the same thing</b>, 25,754 in the header and &ldquo;25,728,
up 204 points&rdquo; in the text; neither is a price anything can be placed against, and both are
pre-open futures rather than the index.</p>
<p><strong>Market Pulse CONFIRMED UPTREND, and the distribution count has come down from three to
<b>two</b></strong> &mdash; one of the three aged out across the holiday. That is the first easing in
their count in a week, and it moves them a step further from the Uptrend Under Pressure downgrade
their Monday mail warned about.</p>
<p class="note"><strong>The global block is the part of this mail that actually changed, and it
changed violently.</strong> On Monday morning they had <b>14</b> markets in Confirmed Uptrend,
13 under pressure, 11 in downtrend and 11 in rally attempt. This morning it reads <b>6 &middot; 12
&middot; 26 &middot; 5</b>. <strong>Twenty-six of the forty-nine markets they track are now in
Downtrend</strong> &mdash; the United States, the United Kingdom, Japan, Germany, Canada, Australia,
Hong Kong, Singapore, South Korea, Taiwan. <strong>India is one of six left in Confirmed
Uptrend</strong>, alongside Mexico, Pakistan, Peru, Qatar and the UAE. A tape that is the last one
standing is not the same thing as a strong one.</p>
<p>What they report from overnight: <b>Dow +423.39 to 50,018.70</b>, but <b>S&amp;P 500 &minus;0.5%
to 7,201.09</b> and <b>Nasdaq &minus;1.5% to 23,733.54</b> as AI names retreated again.
<b>Asia-Pacific ex-Japan fell 2.3%</b> on Wednesday with <b>South Korea down as much as 5.3%</b>, as
Washington prepared findings from an excess-capacity trade probe covering sixteen partners.
<b>US consumer confidence jumped to 103.3 from 91.9</b>, the highest since January 2025 against a
92.5 forecast, which is feeding December rate-hike bets. <b>Brent $90.97</b> (&minus;43 cents),
<b>spot gold $3,544.54</b> (&minus;0.3%).</p>
<p><strong>Their stated driver for India is flow, not earnings:</strong> foreign investors have bought
<b>a record $14.28bn of Indian shares in November</b>, rotating out of global AI names, with US tariff
risk the standing caveat. <b>That is the same flow this service measured over 166 months and found no
predictive edge in</b>, which is why it is recorded here and not acted on.</p>
<p><strong>The Buy Watchlist is ten names this morning</strong>, read off the mail body rather than any
parser &mdash; Monday&rsquo;s eight, plus <b>ITD Cementation India</b> and <b>PNB Housing Finance</b>:
Raghav Productivity Enhancers, Rubicon Research, Acutaas Chemicals, Sudeep Pharma,
<b>Lenskart Solutions</b>, <b>MCX</b>, Nykaa, Union Bank of India, ITD Cementation, PNB Housing.
<strong>Lenskart and MCX are still ours rather than theirs</strong> &mdash; one held in all three
accounts near its stop, one stopped out on Monday.</p>
<p class="note"><strong>Their advice is unchanged and we are still not taking it.</strong> The mail
repeats Monday&rsquo;s line in the same words &mdash; focus on leadership, <b>add exposure
progressively</b>, stay disciplined. <strong>The disagreement is now in its seventh session and it is
worth stating plainly:</strong> MarketSmith reads the index and tells you to add; this page reads how
many stocks are participating and refuses. On Monday the index fell 1.75% on eleven advances against
thirty-nine declines, which is what the second reading had been warning about for a week.
<b>A gap-up open changes neither reading</b> &mdash; breadth is computed from closes, and there has not
been one since Monday. <strong>Entries stay blocked and nothing on this page may be placed.</strong></p>

<h3>MarketSmith, 23 November 17:17 &mdash; read in full</h3>
<p><strong>Monday evening&rsquo;s Big Picture &mdash; the last one written against a real
session.</strong> Nothing came on Tuesday because the market was shut, and Wednesday&rsquo;s
pre-market mail is the section above.</p>
<p><strong>Their Market Pulse is CONFIRMED UPTREND with the distribution count up from two to
three</strong>, because Monday itself qualified: the Nifty fell <b>1.75% to 25,349.65</b> on volume
<b>21.17% higher at 518.92m</b>, with <b>11 advances against 39 declines</b>. It opened at 25,929.15
and closed barely above its own low. It remains <b>4.27% above its 21-day average</b>, <b>7.85% above
the 50-day</b> and <b>3.82% below the 52-week high</b> &mdash; which is the shape of a pullback inside
an uptrend rather than a break of one. <strong>They say in terms that a higher count, or a breach of
key support, takes them to Uptrend Under Pressure.</strong></p>
<p>Their sector block reads <strong>Confirmed Uptrend</strong> for Bank, Pharma, Financial Services,
FMCG, Realty, Energy, Auto, Media and Consumer Durables, and <strong>Uptrend Under Pressure</strong>
for <b>Metal and IT</b>. <b>We are stricter on three of those</b> &mdash; Energy, Metal and IT &mdash;
and the gate uses ours.</p>
<p><strong>The Buy Watchlist is eight names</strong>, read off the mail body rather than any parser:
<b>Raghav Productivity Enhancers</b>, <b>Rubicon Research</b>, <b>Acutaas Chemicals</b>,
<b>Sudeep Pharma</b>, <b>Lenskart Solutions</b>, <b>MCX</b>, <b>Nykaa</b> and
<b>Union Bank of India</b>. <strong>Two of those eight are already our problem rather than our
opportunity:</strong> we hold LENSKART in all three accounts, 1.8% above its stop, and MCX is the
name we were stopped out of on Monday with an add still resting 8.8% higher in Ram.</p>
<p><strong>No change to the model portfolio</strong>, which closed <b>+0.24%</b>: COFORGE +2.66,
CORONA +2.36, ATHERENERG +2.26, KARURVYSYA +1.88, TITAN +1.30, SHRIPISTON +0.96, NAVINFLUOR +0.76,
TIPSMUSIC &minus;0.35, RADICO &minus;0.61, INDHOTEL &minus;0.66, <b>SONACOMS &minus;0.73</b>,
TVSMOTOR &minus;1.35, WELCORP &minus;1.47, GROWW &minus;3.61.</p>
<p class="note">Their improving industry groups, ranks under 40, with the names they attach:
Security/Safety <b>rank 3</b> (CPPLUS &mdash; which is one of our resting entries), Retail-Specialty
<b>6</b> (LENSKART), Medical-Ethical Drugs 7, Food-Dairy 10, Computer-Hardware 11 (REDINGTON),
Medical-Supplies 12 (EMCURE), Machinery-Materials Handling 13 (CRAFTSMAN), Retail-Internet 15,
Airline 17 (INDIGO), Media-Radio/TV 19, Leisure-Lodging 20, Leisure-Movies 21 (PVRINOX &mdash; which
we hold &mdash; SAREGAMA, TIPSMUSIC), Banks-Money Center 24, Consumer Products-Electronic 25,
Jewelry 26. <strong>Two of our twelve open names and one of our resting entries sit in groups
MarketSmith calls improving</strong>, which is worth exactly as much as the gate allows: nothing can
be bought while breadth is shut.</p>
"""



PREMARKET_2026_11_26 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Thursday 26 November, written before the open on Wednesday&rsquo;s close. <strong>The Nifty rose 1.85% to 25,819.25 &mdash; its best session in weeks &mdash; and the market got narrower, not broader.</strong> The share of the scanned universe holding above its own 20-day average fell again, to <b>42.52%</b> against a five-session mean of <b>56.90%</b>. That is the <strong>lowest breadth reading this page has ever recorded</strong>, lower than Monday&rsquo;s 46.15%, and it is the <strong>eighth consecutive session</strong> on which the market half our setups live in has failed its own breadth test.</p>
<p class="sub">Against that: <strong>78.0% of the Nifty 50 closed above its own 20-day average</strong>, and <strong>43 of the 50 are above their 50-day average</strong>. Forty-two of the fifty rose on Wednesday against eight that fell. On the same day, <b>the Smallcap 100 fell 0.44%</b>.</p>
<p class="note"><strong>Both of those numbers are now on this page, side by side, for the first time.</strong> Until today the report carried one breadth line, computed across everything scanned, and it has been saying &ldquo;no&rdquo; for eight sessions while the index printed green days. The second line, computed over the Nifty 50 alone, is what the index has actually been doing. <b>A 35-point gap between the two is not a market with one story in it.</b> Nothing was bought on this reading and nothing is wired to it &mdash; it is being recorded first and judged later, which is the rule here for any new measurement.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l"><b>Market breadth</b>, whole scanned universe</td><td class="l"><b>42.52%</b> above their 20-day average, against a five-session mean of <b>56.90%</b> &mdash; a <b>14.4-point</b> shortfall, the widest yet</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l"><b>The index trend</b></td><td class="l">Nifty 50 in a <b>Confirmed Uptrend</b>, one distribution day, day 23 of the advance from the 2 November follow-through. MarketSmith agrees &mdash; their count is three</td><td class="l pass"><span>OPEN</span></td></tr>
</tbody></table></div>
<p class="note"><strong>One gate open, one shut, so nothing is bought.</strong> This is the eighth session in a row in that state. It is worth being precise about what is being refused: not a bad index, not a downtrend &mdash; the index gate has been open throughout &mdash; but a market in which <b>fewer than half the names we would choose from are holding their own short-term average</b>. Entries also remain <strong>halted by hand</strong>, separately from either gate, from Monday&rsquo;s review. Trailing stops, exits and reconciliation continue to run; stopping entries is not stopping protection.</p>
<p class="note">The ten readings behind that first row, newest first: <b>42.52%</b> (vs 56.90) &middot; 46.15 (60.66) &middot; 46.15 (60.66) &middot; 53.59 (65.13) &middot; 60.25 (68.29) &middot; 59.52 (70.35) &middot; 65.79 (69.65) &middot; 65.11 (69.42) &middot; <span class="pass">74.94 (65.42)</span> &middot; <span class="pass">75.95 (62.65)</span>. <b>The last two green readings are 12 and 13 November.</b> The deterioration has been continuous since, and Wednesday&rsquo;s 1.85% index day did not interrupt it.</p>
<h3 class="sub" id="pre-indices">What Wednesday actually did</h3>
<p class="sub">MarketSmith&rsquo;s sector moves for the <strong>25 November</strong> session, as their
evening Big Picture prints them. <strong>Twelve of fifteen sectors closed green</strong> &mdash; the
mirror image of Monday, when only three did.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>25 Nov move</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>Nifty FMCG</b></td><td class="pass">+3.79%</td><td class="l">the best sector of the day, with <b>HINDUNILVR +6.08%</b> and <b>NESTLEIND +4.03%</b> inside it</td></tr>
<tr><td class="l">Pharma &middot; Healthcare</td><td class="pass">+2.38% &middot; +2.13%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>Private Bank &middot; Financial Services &middot; Bank</b></td><td class="pass">+2.21% &middot; +2.17% &middot; +1.79%</td><td class="l"><b>the banks took back most of Monday&rsquo;s 3.17% fall in one session</b></td></tr>
<tr><td class="l">Auto &middot; IT &middot; PSE</td><td class="pass">+1.16% &middot; +1.12% &middot; +1.03%</td><td class="l">&mdash;</td></tr>
<tr><td class="l">PSU Bank &middot; Energy &middot; Realty</td><td class="pass">+0.37% &middot; +0.04% &middot; +0.02%</td><td class="l">green, but barely</td></tr>
<tr><td class="l">Consumer Durables</td><td class="bad">&minus;0.13%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>Nifty Metal</b></td><td class="bad">&minus;2.04%</td><td class="l">down again &mdash; <b>TATASTEEL &minus;2.27%</b>, <b>HINDALCO &minus;1.17%</b>, <b>JSWSTEEL &minus;0.72%</b>. Two heavy down sessions in a row for the worst-rated sector on our own map</td></tr>
<tr><td class="l"><b>Nifty Media</b></td><td class="bad">&minus;4.44%</td><td class="l">the worst sector of the day by a distance</td></tr>
<tr><td class="l"><b>Midcaps &middot; Smallcaps</b></td><td class="l"><span class="pass">+0.30%</span> &middot; <span class="bad">&minus;0.44%</span></td><td class="l"><b>This is the row that matters.</b> The Nifty rose 1.85%; midcaps managed +0.30% and <b>smallcaps fell</b>. Monday&rsquo;s one session of broad-market outperformance did not repeat</td></tr>
</tbody></table></div>
<p class="note"><strong>Read the last row against the first line of this page.</strong> Wednesday was
a <b>42-advance, 8-decline session inside the Nifty 50</b> &mdash; about as broad as a large-cap day
gets &mdash; and on the same day the <b>smallcap index fell</b>. That is not a contradiction, it is
the whole story of this market in one line: <strong>the breadth that exists is large-cap breadth,
and the half of the market this service&rsquo;s setups live in did not take part.</strong>
<b>That is exactly why there are two breadth readings on this page from today</b> &mdash; see below.
Biggest Nifty gainers: HINDUNILVR +6.08%, TATACONSUM +4.66%, HDFCLIFE +4.58%, NESTLEIND +4.03%,
INDIGO +3.57%, TRENT +3.48%, HDFC Bank +3.47%, ICICI +3.44%, Bajaj Finance +3.27%. Biggest fallers:
Tata Steel &minus;2.27%, Max Health &minus;1.22%, Hindalco &minus;1.17%, JSW Steel &minus;0.72%,
Shriram Finance &minus;0.60%.</p>

<h3 class="sub" id="pre-largecap">New on this page: a second breadth reading, and a large-cap board</h3>
<p class="note"><strong>Three things were added to this report overnight, and this is the first
morning they appear.</strong> The first is a <b>second market-breadth line computed over the Nifty 50
alone</b>, drawn beside the existing one, which is computed over the whole scanned universe. The two
have been telling different stories for three weeks and until today the page only carried one of
them. The second is a <b>large-cap board</b>: every Nifty-50 name trading above its own 50-day
average, with how far it sits from its 20-day and 10-day averages, how far it is below its own
52-week high, its sector and its latest headline, <b>ranked nearest its own high first</b>. The
third is a <b>candle chart for each of those names</b>, drawn the same way the TIS setups are drawn.
<strong>None of it is a buy list and none of it is wired to the gate.</strong> It is there to be
measured first: the rule here is that a reading earns a gate only after it has been recorded long
enough to be tested, and this one has one day of history. The index membership is NSE&rsquo;s own
<b>ind_nifty50list.csv</b>, read on 26 November, and the page says so rather than guessing at
&ldquo;the fifty largest&rdquo;.</p>
<h3 class="sub" id="pre-regime">Where each index and sector stands, on our own count</h3>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>dist. days</th><th class="l">our status</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>Nifty 50</b></td><td>1</td><td class="l pass"><span>Confirmed Uptrend</span></td><td class="l">day 23, from the 2 November follow-through. MarketSmith also Confirmed Uptrend, their count 3</td></tr>
<tr><td class="l">Nifty Next 50</td><td>2</td><td class="l pass"><span>Confirmed Uptrend</span></td><td class="l">day 22, same follow-through date</td></tr>
<tr><td class="l">Midcap 150</td><td>2</td><td class="l pass"><span>Confirmed Uptrend</span></td><td class="l">day 22</td></tr>
<tr><td class="l"><b>Smallcap 100</b></td><td><b>8</b></td><td class="l warn"><span>Rally Attempt</span></td><td class="l"><b>Eight distribution days, up from seven, and it has never confirmed.</b> Day 22 of an attempt that has not produced a follow-through. This is the index our setups actually come from</td></tr>
</tbody></table></div>
<p class="note"><strong>The four rows disagree, and the disagreement is the point.</strong> Three large-cap indices are in confirmed uptrends; the small-cap index has been attempting a rally for twenty-two sessions without confirming it, and is accumulating distribution while it does. Sector-by-sector on our own count: <b>banks, PSU banks, consumer durables and FMCG are clean</b> at zero distribution days; auto, healthcare, pharma and realty carry one each. <b>IT and metal carry nine each</b> and <b>energy and media six each</b> &mdash; all four on Rally Attempt rather than confirmed.</p>
<p class="note"><strong>Four open disagreements with MarketSmith, unchanged from Monday and still unresolved.</strong> They read <b>energy</b> and <b>media</b> as Confirmed Uptrends where we read Rally Attempts; they read <b>IT</b> and <b>metal</b> as Uptrend Under Pressure where we read Rally Attempt on nine distribution days each. Our reading is the stricter one in all four and ours is what the service obeys. <b>Which reading should bind when the two disagree is a decision that has been put to Divyansh and not yet taken</b>, and it is recorded here each morning until it is.</p>

<h3 class="sub" id="pre-today">What the overnight scans found</h3>
<div class="scroll"><table><thead><tr><th class="l">scan</th><th class="l">what came back</th><th class="l">result</th></tr></thead><tbody>
<tr><td class="l"><b>Daily</b></td><td class="l"><b>1,063 names scanned</b>, 604 with a stop that could be derived, 34 clearing seven of the eight checks, <b>28 cleared all of them</b></td><td class="l warn"><span>28, none placeable</span></td></tr>
<tr><td class="l">Weekly</td><td class="l">578 candidates</td><td class="l"><span>0</span></td></tr>
<tr><td class="l">ETF &middot; ETF weekly</td><td class="l">18 and 19 funds</td><td class="l"><span>0 &middot; 0</span></td></tr>
<tr><td class="l">The other two</td><td class="l">Both ran overnight; neither is on the list of strategies this service places from</td><td class="l faint"><span>reporting only</span></td></tr>
</tbody></table></div>
<p class="note">The 28 that cleared every check, which is the longest such list in a fortnight: CUPID, TFCILTD, FREDUN, RPEL, KRISHANA, SHADOWFAX, TIMEX, SHIVAUM, GLAND, DIVISLAB, SHUKRAPHAR, KPL, RAYMOND, SBC, GCSL, MBAPL, GLOBAL, UNITEDPOLY, SAILIFE, PVRINOX, LENSKART, PTCIL, LUMAXTECH, NAVINFLUOR, ISFT, ASKAUTOLTD, LTTS, PDSL. <strong>None of them will be bought today.</strong> Six are names already held. The market-wide reading above refuses the lot of them, and entries are halted by hand on top of that. <b>Twenty-eight clean setups on the day breadth printed its lowest reading on record is itself the thing to notice</b> &mdash; individual charts keep setting up while the market underneath them keeps thinning, which is the configuration that produced the losses this halt followed.</p>
<p class="note">Separately, the running record of what the refusals cost now holds <b>325 setups</b> that were refused and then tracked: <b>169 never traded through their trigger at all</b>, 30 would have been stopped out, 126 would still be open, 22 have no bars yet. That record is kept so the refusal rule can eventually be judged on measurement rather than on how it feels during a week like this one.</p>

<h3 class="sub" id="pre-risk">The open book, and what is closest to being stopped out</h3>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>position</th><th>to its stop</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>SONACOMS</b></td><td class="bad">&minus;3.9%</td><td class="bad"><b>1.3%</b></td><td class="l"><b>The tightest in the book.</b> One ordinary down session takes it out. MarketSmith holds it too, and marked it &minus;0.32% on Wednesday</td></tr>
<tr><td class="l">ROSSTECH</td><td class="bad">&minus;5.1%</td><td class="warn">2.3%</td><td class="l">&mdash;</td></tr>
<tr><td class="l">LENSKART</td><td class="bad">&minus;1.9%</td><td class="warn">2.6%</td><td class="l">On MarketSmith&rsquo;s buy watchlist this morning, and in their rank-8 industry group, while sitting 2.6% above our stop</td></tr>
<tr><td class="l">CUPID</td><td class="pass">+5.9%</td><td class="l">stop at cost</td><td class="l">The stop has been trailed to the entry price &mdash; the position can no longer lose money</td></tr>
<tr><td class="l">AARTIPHARM &middot; PVRINOX</td><td class="pass">+4.9% &middot; +4.9%</td><td class="l">&mdash;</td><td class="l">The two best open positions</td></tr>
<tr><td class="l">RATNAVEER &middot; SBC</td><td class="pass">+5.8% &middot; +2.3%</td><td class="l">&mdash;</td><td class="l">&mdash;</td></tr>
</tbody></table></div>
<p class="note"><strong>33 positions are open across the three accounts, 14 of them on stops that have already been trailed up.</strong> Two rows carry no stop at all and <b>both are LIQUIDCASE</b> &mdash; the parking fund, which never carries one and is not a trade. That is worth stating plainly rather than leaving a &ldquo;no stop&rdquo; count on the page to read as an alarm: <b>there is no unprotected equity position in the book.</b></p>
<p class="note"><strong>Two things on the book are open and waiting on Divyansh, not on the market.</strong> First, <b>PTCIL filled on 25 November in the akul account alone</b> &mdash; a single share at 24,675, against 24,453 when the book was read this morning. Every other name in the book is held in all three accounts at each account&rsquo;s own size, so a one-account fill is a break in that rule and is being flagged rather than quietly corrected. It is not unprotected: a stop is resting against it, structurally placed at 23,461. Second, <b>SHUKRAMED has no usable price series</b> this morning, so its rows show no last price, no move and no chart anywhere on this page; the position itself is unaffected, the display is not.</p>
<h3>MarketSmith, 25 November &mdash; both mails read in full</h3>
<p><strong>The evening Big Picture, 16:52.</strong> Their Market Pulse is
<strong>CONFIRMED UPTREND</strong> with the distribution count at <b>three</b>, unchanged from
Monday evening &mdash; Wednesday was an up day on higher volume, which adds nothing to a
distribution count. The Nifty rose <b>1.85% to 25,819.25</b>, opening at 25,658.35 against Monday&rsquo;s
25,349.65 close, high 25,951.65, low 25,619.00, on volume <b>2.74% higher at 533.14m</b>, with
<b>42 advances against 8 declines</b>. The Sensex rose 1.82% to 83,938.28. It closed
<b>5.47% above its 21-day average</b>, <b>9.55% above the 50-day</b> and
<b>2.10% below its 52-week high</b> &mdash; against 4.27%, 7.85% and 3.82% on Monday, so one session
undid most of the pullback and then some. <b>Midcap 100 +0.30%, Smallcap 100 &minus;0.44%.</b></p>
<p>Their sector block for the session: FMCG <b>+3.79%</b>, Pharma +2.38%, Private Bank +2.21%,
Financial Services +2.17%, Healthcare +2.13%, Bank +1.79%, Auto +1.16%, IT +1.12%, PSE +1.03%,
PSU Bank +0.37%, Energy +0.04%, Realty +0.02%; against Media <b>&minus;4.44%</b>, Metal
<b>&minus;2.04%</b> and Consumer Durables &minus;0.13%.</p>
<p><strong>No change to the model portfolio, which closed &minus;0.93%</strong> on a day the index
rose 1.85% &mdash; worth noticing on its own: CORONA +3.37, TVSMOTOR +1.81, RADICO +1.35,
GROWW +0.47, TITAN +0.14, INDHOTEL &minus;0.24, SHRIPISTON &minus;0.31, SONACOMS &minus;0.32,
KARURVYSYA &minus;1.39, WELCORP &minus;1.64, NAVINFLUOR &minus;1.95, COFORGE &minus;3.84,
TIPSMUSIC &minus;5.00, ATHERENERG &minus;5.42. <b>Eleven of fourteen names fell on a day the Nifty
gained 1.85%.</b> Their own book is positioned where the money was not.</p>
<p class="note">Their improving industry groups, ranks under 40, with the names they attach:
Medical-Ethical Drugs <b>rank 5</b> (CORONA, ALIVUS), Retail-Specialty <b>8</b> (LENSKART &mdash;
which we hold), Food-Dairy 9, Medical-Supplies 11 (EMCURE), Computer-Hardware 12 (REDINGTON),
Leisure-Lodging 15 (INDHOTEL, THELEELA, LEMONTREE), Airline 16 (INDIGO), Retail-Internet 20
(ETERNAL, ZETWERK, CARTRADE), Leisure-Movies 21 (PVRINOX &mdash; which we hold &mdash; SAREGAMA,
TIPSMUSIC), Consumer Products-Electronic 22 (LGEINDIA), Media-Radio/TV 23, Jewelry 24,
Medical-Products 26, Banks-Money Center 27, Consumer Services-Education 28. <b>Security/Safety has
dropped out of the under-40 list</b>, which it led at rank 3 on Monday &mdash; that is the group
CPPLUS sits in.</p>
<p><strong>The 09:00 pre-market mail, same day.</strong> GIFT Nifty was <b>25,754 at 08:15</b> before
the open. The line worth keeping from it: <strong>FIIs bought a record $14.28 bn of Indian shares in
November</strong>. Their <strong>Buy Watchlist ran to ten names</strong>, read off the mail body
rather than any parser &mdash; Raghav Productivity Enhancers, Rubicon Research, Acutaas Chemicals,
Sudeep Pharma, Lenskart Solutions, Multi Commodity Exchange of India, FSN E-Commerce (Nykaa),
Union Bank of India, ITD Cementation India and PNB Housing Finance. <b>Two of those are already our
problem rather than our opportunity</b>: we hold LENSKART, and MCX is the name we were stopped out
of on Monday. Their global board has <strong>India in a Confirmed Uptrend with only five other
countries</strong>, against <b>26 in a Downtrend, the United States among them</b>.</p>
<p class="note"><strong>A note on the evening mail&rsquo;s own digest.</strong> The parser-written
summary line at the top of that message reads &ldquo;BUY WATCHLIST (23)&rdquo;, which is wrong &mdash;
the body lists ten. <b>This is the reason every one of these mails is read as prose and never from a
parser</b>, including parsers written here. A quiet field or a wrong count in a digest is not
evidence of anything; the body is.</p>
<h3 class="sub" id="pre-morning-26">09:10, before the open &mdash; the pre-market mail, read in full</h3>
<p class="sub">MarketSmith&rsquo;s pre-market note is stamped <b>08:30</b> and arrived at <b>08:59</b>. <strong>Market Pulse unchanged: Confirmed Uptrend, three distribution days.</strong></p>
<p><strong>GIFT Nifty was 26,043 at 08:15</strong>, a 118-point premium to the previous futures close and about <b>224 points above Wednesday&rsquo;s cash close of 25,819.25</b>. On their reading that points to a <b>positive Thursday open</b>. Overnight, the <b>Dow rose 164.25 points to 50,182.95</b> while the <b>S&amp;P 500 fell 0.3% to 7,182.78</b> and the <b>Nasdaq fell 0.6% to 23,585.80</b> on continued AI selling &mdash; an American session that went two ways at once. Asia ex-Japan rose 0.6%, <b>Japan&rsquo;s Nikkei +1.6%</b> and <b>South Korea +1.9%</b>.</p>
<p><strong>The macro line worth keeping.</strong> US October core PCE inflation <b>accelerated to 3.3%</b>, above expectations, and third-quarter GDP growth was <b>revised up to 4.3%</b>. Their read is that the pair strengthens expectations of a <b>December rate increase</b>; gold fell toward <b>$3,550</b> on the same news. Renewed Middle East tension is pushing oil-supply worry back into the frame.</p>
<p class="note"><strong>And the one that matters to this market today: the United States has proposed tariffs of up to 25% on Indian goods, reducible to 17% if the two countries conclude a trade agreement.</strong> That is a live headline sitting underneath a gap-up open, and it is the kind of thing that decides whether a strong opening print survives the session.</p>
<p>Stock-specific, as they list it: <b>Wipro</b>&rsquo;s bp finance-operations partnership is reported at over <b>$500m</b>, moving roughly 3,000 employees across India, Hungary and Malaysia. <b>Siemens Energy India</b> Q4 net profit <b>+81.4% to &#8377;653 crore</b>, revenue +30.5% to &#8377;3,453 crore, margin 23.8% against 18.1%. <b>Schaeffler AG</b> is reported to be planning a block sale of up to <b>6% of Schaeffler India, about &#8377;3,188 crore</b>. <b>Lupin</b> has USFDA clearance for single-dose Dalbavancin. In <b>Global Health</b>, Temasek sold 2.4% at &#8377;1,460 a share with HDFC MF, Norges and SBI MF on the other side. Orders: Diamond Power Infra &#8377;488 crore, Atlanta Electricals &#8377;523 crore from APTRANSCO, KSB a boiler feed-pump package for JSW&rsquo;s Salboni plant, Juniper Green a 150 MW wind-solar hybrid PPA with NTPC.</p>
<p class="note"><strong>Their buy watchlist is the same ten as yesterday</strong> &mdash; Raghav Productivity Enhancers, Rubicon Research, Acutaas Chemicals, Sudeep Pharma, <b>Lenskart Solutions</b>, MCX, FSN E-Commerce (Nykaa), Union Bank of India, ITD Cementation India, PNB Housing Finance. Two of those remain our own problem rather than our opportunity: <b>we hold LENSKART</b>, which sits 2.6% above its stop this morning, and <b>MCX</b> is the name we were stopped out of on Monday. Their global board still has <b>India in a Confirmed Uptrend with only five other countries</b>, against <b>twenty in Downtrend</b> &mdash; Japan, Germany, China and South Korea among them &mdash; and <b>thirteen in Rally Attempt, the United States among those</b>.</p>
<p class="note"><strong>What this does not change.</strong> A gap-up open is not breadth. Yesterday&rsquo;s 1.85% index day was built on fifty stocks while the smallcap index fell, and the reading at the top of this page &mdash; <b>42.52% against a five-session mean of 56.90%</b> &mdash; is computed from Wednesday&rsquo;s close and stands whatever the first print does. <b>Nothing is bought today.</b> Entries remain halted by hand as well as refused by the reading.</p>

<h3 class="sub" id="pre-defect-26">A defect found in the book this morning, not yet fixed</h3>
<p class="note"><strong>SBC&rsquo;s protective stops rest for more shares than the accounts hold, in all three accounts.</strong> t-default holds <b>6,742</b> with stop orders covering <b>10,113</b>; akul holds <b>865</b> against <b>1,241</b>; t-ramprasad holds <b>1,396</b> against <b>2,094</b>. That is roughly <b>1.44&times; the holding in each</b>, and the shape is the same everywhere: a second stop leg is resting against shares that are not there. The position is over-protected rather than naked, which is the better of the two failures &mdash; but if both legs were to fire in one move, each account would sell more than it owns.</p>
<p class="note"><b>Nothing has been cancelled.</b> Live orders are not touched without Divyansh saying so, and a stop that is too large is not an emergency in the way a missing one would be. It is written here, and on his list, to be decided rather than quietly corrected. Separately, all three accounts show a gap between the LIQUIDCASE the broker reports and the quantity this service records &mdash; 36,920 against 31,902, 3,869 against 145, and 2,522 against 493. The parking fund is not a trade and carries no stop by design; the mismatch is a bookkeeping fault and is listed with the rest.</p>
"""

PREMARKET_2026_11_27 = """
<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Friday 27 November, written before the open on Thursday&rsquo;s close. <strong>The Nifty added 0.25% to 25,884.50 &mdash; a ten-month high &mdash; on volume 28.90% lower than the day before, and with 28 of its own fifty members falling.</strong> Breadth across the scanned universe came back to <b>43.76%</b> above their own 20-day average, against a five-session mean of <b>52.27%</b>. That is better than Wednesday&rsquo;s record low of 42.52%, and it is still an <b>8.5-point shortfall</b>. It is the <strong>ninth consecutive session</strong> the market half our setups live in has failed its own breadth test.</p>
<p class="sub">An index at a ten-month high, made on falling volume, with more of its members down than up, is a narrow print rather than a strong one. <b>Midcaps rose 0.32% and smallcaps 0.74%</b> on the same day, which is the first session in a while the broad market has outpaced the index &mdash; one session, and not yet a turn.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l"><b>Market breadth</b>, whole scanned universe</td><td class="l"><b>43.76%</b> of <b>882</b> names above their 20-day average, against a five-session mean of <b>52.27%</b> &mdash; an <b>8.5-point</b> shortfall</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l"><b>The index trend</b></td><td class="l">Nifty 50 <b>4.41% above its own 20-day average</b> and 7.14% above the 50-day, in a <b>Confirmed Uptrend</b>, day 24 from the 2 November follow-through. MarketSmith agrees &mdash; their distribution count fell from three to <b>two</b></td><td class="l pass"><span>OPEN</span></td></tr>
</tbody></table></div>
<p class="note"><strong>One gate open, one shut, so nothing is bought &mdash; the ninth session in a row in that state.</strong> Entries are also <strong>halted by hand</strong>, separately from either gate, since Monday&rsquo;s review. Trailing stops, exits and reconciliation are meant to keep running regardless; <b>this morning several of them are not, and that is the first thing on this page that needs a decision</b> &mdash; see the last section.</p>
<p class="note">The ten readings behind the first row, newest first: <b>43.76%</b> (vs 52.27) &middot; 42.52 (56.90) &middot; 46.15 (60.66) &middot; 46.15 (60.66) &middot; 53.59 (65.13) &middot; 60.25 (68.29) &middot; 59.52 (70.35) &middot; 65.79 (69.65) &middot; 65.11 (69.42) &middot; <span class="pass">74.94 (65.42)</span>. <b>The last green reading is 12 November.</b> Thursday stopped the slide without reversing it: the level rose a point and the five-session mean it is measured against fell four, which is what narrows the gap &mdash; <b>the test got easier faster than the market got better.</b></p>

<h3 class="sub" id="pre-indices">What Thursday actually did</h3>
<p class="sub">MarketSmith&rsquo;s sector moves for the <strong>26 November</strong> session, as their evening Big Picture prints them.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>26 Nov move</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>Nifty IT</b></td><td class="pass">+3.66%</td><td class="l">the day&rsquo;s whole story &mdash; <b>HCLTECH +6.42%</b>, <b>TCS +4.89%</b>, <b>INFY +4.69%</b>, <b>TECHM +2.97%</b>. Four of the five biggest Nifty gainers were IT</td></tr>
<tr><td class="l"><b>Nifty Realty</b></td><td class="pass">+3.27%</td><td class="l">second best, after two flat sessions</td></tr>
<tr><td class="l">Metal &middot; Energy &middot; Pharma</td><td class="pass">+1.17% &middot; +0.58% &middot; +0.45%</td><td class="l">metal green for the first time in three sessions</td></tr>
<tr><td class="l">Financial Services &middot; Bank</td><td class="bad">&minus;0.16% &middot; &minus;0.26%</td><td class="l">gave back a little of Wednesday&rsquo;s +2.17% and +1.79%</td></tr>
<tr><td class="l">Media &middot; Auto &middot; FMCG</td><td class="bad">&minus;0.34% &middot; &minus;0.69% &middot; &minus;0.94%</td><td class="l">FMCG down after Wednesday&rsquo;s +3.79% &mdash; the one-day leader became the three-day laggard</td></tr>
<tr><td class="l"><b>Nifty Consumer Durables</b></td><td class="bad">&minus;1.33%</td><td class="l">the worst sector of the day</td></tr>
<tr><td class="l"><b>Midcaps &middot; Smallcaps</b></td><td class="l"><span class="pass">+0.32%</span> &middot; <span class="pass">+0.74%</span></td><td class="l"><b>Both beat the index for the first time in a week.</b> One session is not a rotation, and the breadth reading at the top of this page is computed from the same close</td></tr>
</tbody></table></div>
<p class="note"><strong>The internals contradict the headline, and that is worth saying plainly.</strong> The Nifty closed at a ten-month high, <b>1.85% below its 52-week high</b>, <b>4.64% above its 21-day average</b> and <b>9.46% above its 50-day</b> &mdash; and it did it with <b>22 advancing against 28 declining</b> and <b>volume 28.90% lower</b>. A handful of IT heavyweights carried the index while most of it drifted. Biggest Nifty fallers: Asian Paints &minus;2.98%, Bajaj Finance &minus;2.96%, Shriram Finance &minus;2.84%, Nestl&eacute; &minus;2.81%, Bajaj Finserv &minus;2.03%.</p>

<h3 class="sub" id="pre-regime">Where the two readings stand against each other</h3>
<p class="note">On our own count the Nifty 50 remains in a <b>Confirmed Uptrend</b>, and so does MarketSmith&rsquo;s &mdash; the follow-through both are counting from is <b>2 November</b>, and their distribution count fell to two on Thursday. Over the last 48 sessions the two readings have agreed on <b>24 of them, exactly half</b>. The most recent disagreements were <b>17, 16 and 13 November</b>, when we read Downtrend or Uptrend Under Pressure and MarketSmith read Confirmed Uptrend &mdash; ours the stricter reading each time, and ours is what the service obeys. <b>Which should bind when the two disagree is still an open decision for Divyansh.</b></p>
<p class="note">MarketSmith&rsquo;s own sector board for Thursday has <b>Bank, Pharma, Financial Services, FMCG, Realty, Energy, Auto, Media and Consumer Durables in Confirmed Uptrends</b>, and <b>Metal and IT in Uptrend Under Pressure</b> &mdash; IT marked under pressure on the day it rose 3.66%, which is what a distribution count does to a one-day move.</p>

<h3 class="sub" id="pre-risk">The open book, and what is closest to being stopped out</h3>
<p class="sub">Read live from all three brokers at <b>07:52</b>. <b>&#8377;74.47 lakh held, nothing resting to be spent, &#8377;17,039 free cash across the three.</b> Thirty-three rows: thirty equity positions and the three parking funds.</p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>position</th><th>to its stop</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>SONACOMS</b></td><td class="bad">&minus;4.1%</td><td class="bad"><b>5.9%</b></td><td class="l"><b>The tightest in the book, and the worst position in it.</b> It was 1.3% from its stop yesterday morning &mdash; Thursday&rsquo;s session bought it room, it did not fix it</td></tr>
<tr><td class="l">LENSKART</td><td class="bad">&minus;2.4%</td><td class="warn">7.1%</td><td class="l">Still on MarketSmith&rsquo;s buy watchlist while sitting under water for us</td></tr>
<tr><td class="l">SBC</td><td class="pass">+2.0%</td><td class="warn">8.3%</td><td class="l">The name with the stop defect below</td></tr>
<tr><td class="l">PVRINOX &middot; ROSSTECH</td><td class="l"><span class="pass">+0.6%</span> &middot; <span class="bad">&minus;1.9%</span></td><td class="l">10.1% &middot; 10.2%</td><td class="l">&mdash;</td></tr>
<tr><td class="l"><b>CUPID</b></td><td class="pass">+7.3%</td><td class="l">11.4%</td><td class="l">The best large position in the book</td></tr>
<tr><td class="l">SHUKRAMED &middot; TFCILTD</td><td class="l"><span class="pass">+8.9%</span> &middot; <span class="pass">+1.1%</span></td><td class="l">12.8% &middot; 12.0%</td><td class="l"><b>SHUKRAMED has a priceable series again this morning</b> &mdash; it had none yesterday, so its rows were blank across the whole page. That display fault is gone</td></tr>
<tr><td class="l">GCSL &middot; AARTIPHARM &middot; RATNAVEER</td><td class="l"><span class="pass">+3.4%</span> &middot; <span class="pass">+3.9%</span> &middot; <span class="pass">+5.9%</span></td><td class="l">13.2% &middot; 14.9% &middot; 15.1%</td><td class="l">The three furthest from trouble</td></tr>
</tbody></table></div>
<p class="note"><strong>Combined, the equity book is up about &#8377;51,400 unrealised</strong> &mdash; &#8377;36,900 in t-default, &#8377;9,900 in t-ramprasad, &#8377;4,600 in akul &mdash; with a further <b>&#8377;32,400 on the parked LIQUIDCASE</b>. <b>Nine of the twelve names are green.</b> The three that are not are SONACOMS, LENSKART and ROSSTECH, and they are also the three closest to their stops, which is how it should look.</p>
<p class="note"><strong>Three breaks in the rule that every account holds the same names, all of them old and all of them flagged rather than corrected.</strong> <b>PTCIL</b> is held in <b>akul alone</b> (one share, filled 25 November). <b>RATNAVEER</b> and <b>TFCILTD</b> are held in <b>t-ramprasad alone</b> &mdash; both bought there on Divyansh&rsquo;s own instruction. All three carry resting stops. Nothing is being evened up without him saying so.</p>

<h3 class="sub" id="pre-stops-27">The SBC stop defect, re-read &mdash; and yesterday&rsquo;s version of it was wrong</h3>
<p class="note"><strong>Yesterday this page said SBC&rsquo;s protective stops rested at the broker for roughly 1.44&times; the shares held in each account. Read again this morning against the brokers themselves, that is not what is there.</strong> The <b>orders actually resting at each broker sum exactly to the holding</b>: t-default 3,371 + 3,371 against 6,742 held; akul 489 + 376 against 865; t-ramprasad 698 + 698 against 1,396. <b>What is 1.44&times; too large is this service&rsquo;s own record of those stops</b>, which carries a base leg equal to the full holding <em>plus</em> an add leg on top of it.</p>
<p class="note"><strong>So the fault is a bookkeeping fault, not a live-order fault</strong> &mdash; the better of the two, and the opposite way round from how it was reported yesterday. It is corrected here in the same place it was got wrong. The reason it was got wrong is the standing one: <b>a stop check that reads our own records is not a check of the broker</b>, and the two tables disagreed. Nothing has been cancelled or amended at any broker.</p>
<p class="note">Two smaller things from the same read. <b>SHUKRAMED&rsquo;s stop rests 4.3% lower in akul than in the other two accounts</b> &mdash; 75.29 against 78.51 and 78.66 &mdash; because akul&rsquo;s recorded structural level (79.25) is stale against its own average cost (83.46). The position is protected, just later than its siblings. And the <b>LIQUIDCASE record-versus-broker gap persists in all three accounts</b>: 36,920 held against 31,902 recorded, 3,869 against 145, 2,522 against 493. The parking fund is not a trade and carries no stop by design; the mismatch is bookkeeping and stays on the list.</p>

<h3 class="sub" id="pre-crons-27">&#9888; The protection jobs are still not running, and the failure counts grew overnight</h3>
<p class="note"><strong>This is the most important thing on the page and it is not about the market.</strong> The scheduled jobs that trail stops, book fills, reconcile positions against the brokers and process exits have been failing continuously since <b>25 November 10:31</b>. As of this morning: <b>book-policy-fills has failed 855 consecutive times</b> (585 yesterday), <b>trail-stop-losses 49</b> (35 yesterday), reconcile-positions 28, book-confirmed-fills 28, pyramid-adds 18, with advance-book-policy, exit-book-policy, exit-broken-stops and settle-exits all overdue as well. The overnight scan job has been silent for <b>134 hours</b>.</p>
<p class="note"><strong>The cause is known and it is ours.</strong> Halting entries was done with a blanket pause across all three accounts, and the jobs that protect the open book read that same pause as &ldquo;no account to work on&rdquo; and refuse to run. <b>Halting entries was never meant to halt protection.</b> The open positions are not unprotected &mdash; every one of them has a stop resting at its broker right now, which is what the section above confirms &mdash; but <b>nothing is moving those stops up as prices rise, and nothing is reconciling the book against the brokers automatically.</b> Both have been done by hand this week instead.</p>
<p class="note"><strong>The fix is one command and it is Divyansh&rsquo;s to give</strong>, not something to take unilaterally: lift the blanket pause so the protection jobs run again, and leave the separate entry halt in place so nothing is bought. The two are different switches and only one of them was meant to be thrown. This has now been on the page two mornings running.</p>
<p class="note"><strong>The trail was run by hand this morning, on all three accounts, at 08:42&ndash;08:46.</strong> Nine stops moved up: <b>GCSL 777.48&nbsp;&rarr;&nbsp;782.30</b> and <b>SBC 65.97&nbsp;&rarr;&nbsp;66.11</b> in every account, plus <b>PTCIL</b> and <b>SHUKRAMED</b> in akul and <b>RATNAVEER</b> in t-ramprasad. <b>SHUKRAMED&rsquo;s move closes the akul gap described two sections above</b> &mdash; its structural level is no longer stale against its own cost. Five names had nothing to give: the level already resting sits above what the trail would compute, which for <b>CUPID</b> and <b>SHUKRAMED</b> means they are still pinned at their entry price while 7.3% and 8.9% ahead.</p>
<p class="note"><strong>&#9888; Three names refused the move, in all three accounts, for the same reason.</strong> <b>AARTIPHARM, PVRINOX and ROSSTECH</b> each came back <em>placement rejected &mdash; quantity must be positive, got 0</em>. These are the positions carrying a second, added leg, and the code that works out how many shares a replacement stop should cover computes zero for them. <b>None of the three is unprotected</b> &mdash; each kept the stop it already had, at 915.60, 1,551.00 and 1,375.00. But they cannot be trailed at all until the writer is fixed, and theirs were the two largest pending moves on the book: ROSSTECH would have gone to 1,417.74 and AARTIPHARM to 934.87, each about three percent of protection left on the table. This is a defect that was predicted on paper and has now been seen nine times live, and it is the second thing on this page needing a decision.</p>

<h3>MarketSmith, 26 November &mdash; the evening Big Picture, read in full</h3>
<p><strong>Market Pulse: CONFIRMED UPTREND, distribution days down from three to two.</strong> The Nifty rose <b>0.25% to 25,884.50</b>, a <b>ten-month high</b> &mdash; open 25,841.25, high 25,973.80, low 25,734.60 &mdash; on volume <b>28.90% lower</b>, with <b>22 advances against 28 declines</b>. It closed <b>4.64% above its 21-day average</b>, <b>9.46% above the 50-day</b> and <b>1.85% below its 52-week high</b>. Midcap 100 +0.32%, Smallcap 100 +0.74%.</p>
<p>Leaders: <b>HCLTECH +6.42</b>, BSE +5.70, <b>TCS +4.89</b>, <b>INFY +4.69</b>, TECHM +2.97. Laggards: Asian Paints &minus;2.98, Bajaj Finance &minus;2.96, Shriram Finance &minus;2.84, Nestl&eacute; &minus;2.81, Bajaj Finserv &minus;2.03. Sectors: IT +3.66, Realty +3.27, Metal +1.17, Energy +0.58, Pharma +0.45; against Consumer Durables &minus;1.33, FMCG &minus;0.94, Auto &minus;0.69, Media &minus;0.34, Bank &minus;0.26, Financial Services &minus;0.16.</p>
<p class="note"><strong>One change to the model portfolio, and it is an addition.</strong> They added <b>Action Construction Equipment (ACE)</b> at <b>&#8377;1,287</b>, with a buy range of <b>&#8377;1,258&ndash;1,320</b> &mdash; EPS Rank 92, RS 82, Buyer Demand B+, Group Rank 52, breaking out of a stage-one cup-with-handle after nine weeks. <b>It is not on our own list and nothing is being bought from theirs</b>; it is recorded because their adds are worth watching against what our own scans find.</p>
<p class="note">Their <strong>buy watchlist runs to ten names</strong>, read off the mail body rather than any parser: Raghav Productivity Enhancers, Rubicon Research, Acutaas Chemicals, Sudeep Pharma, <b>Lenskart Solutions</b>, Multi Commodity Exchange of India, FSN E-Commerce (Nykaa), Union Bank of India, Cemindia Projects and PNB Housing Finance. Two remain our problem rather than our opportunity &mdash; <b>we hold LENSKART</b>, which is 7.1% above its stop and under water, and <b>MCX</b> is the name we were stopped out of on Monday. ITD Cementation has dropped off and Cemindia Projects has come on.</p>
<p class="note"><strong>One news item needs disambiguating before anyone reads it the wrong way.</strong> Their news block carries a US FDA outcome &mdash; a Voluntary Action Indicated classification and an Establishment Inspection Report &mdash; for <b>SHILPAMED</b>. <b>We hold SHUKRAMED, which is a different company.</b> The two tickers are easy to confuse and this page has confused readers with them before, so it is being spelled out rather than left to be inferred.</p>

<h3 class="sub" id="pre-morning-27">09:08, before the open &mdash; the pre-market mail, read in full</h3>
<p class="sub">Stamped <b>08:30</b>, arrived <b>09:08</b> &mdash; the latest of any session measured, and read here in full. <strong>Market Pulse unchanged: Confirmed Uptrend, two distribution days.</strong></p>
<p><strong>Their own headline calls for a cautious start, and their two readings of GIFT Nifty do not agree with each other.</strong> The top of the mail gives <b>GIFT Nifty at 25,957.50 at 08:15</b> against Thursday&rsquo;s cash close of <b>25,884.50</b> &mdash; a <b>73-point premium</b>. The bullet underneath gives <b>25,985.50</b>, and calls it <b>72 points or 0.28% lower</b> against a previous futures settle of <b>26,032</b>. Both can be true at once &mdash; futures below their own settle but still above cash &mdash; but the two prices quoted for the same 08:15 reading differ by 28 points, so <b>neither is treated here as a number to act on.</b> The direction they agree on is a mildly positive open against cash, a softer one against futures.</p>
<p><strong>Overnight, as they list it.</strong> <b>Wall Street was shut on Thursday for Thanksgiving</b>; S&amp;P 500 and Nasdaq 100 futures were <b>+0.7%</b> on Friday ahead of a shortened session, AI names recovering. <b>Nikkei +0.7%</b>, <b>South Korea +2.0%</b>, MSCI Asia-Pacific ex-Japan +0.5% &mdash; but still <b>8.2% lower for November</b>. The rate line is the one that matters: interest-rate futures imply a <strong>99% chance of a 25-basis-point Fed hike in December</strong>, Tokyo core inflation is at a sixteen-month high, the dollar index is at <b>103.8</b> heading for a third straight monthly gain, and the <b>US 10-year yield has risen to 4.89%</b>. Brent eased 38 cents to <b>$96.19</b> after Thursday&rsquo;s near-$2 jump on Hormuz tanker and Saudi refinery attacks.</p>
<p class="note"><strong>The domestic line carries one number that cuts against the gloom and one that does not.</strong> <b>FIIs net bought &#8377;5,843.33 crore on Thursday</b> &mdash; a large single-session buy. Against that, the <b>rupee settled 18 paise weaker at 92.38</b> on costlier crude and the <strong>proposed US tariffs of up to 25% on Indian goods</strong>, which is the same live headline that sat under Wednesday&rsquo;s gap-up and has not gone away. Their cash-market breadth for Thursday reads <b>2,149 advances against 1,906 declines</b> &mdash; positive across the whole exchange, on the same day the Nifty&rsquo;s own fifty went 22 up and 28 down. <b>Those two facts are both true and they describe different markets</b>; the breadth test at the top of this page measures the one our setups actually live in.</p>
<p class="note"><strong>Their buy watchlist is back to ten and has rotated once:</strong> Raghav Productivity Enhancers, Rubicon Research, Acutaas Chemicals, Sudeep Pharma, <b>Lenskart Solutions</b>, MCX, FSN E-Commerce (Nykaa), Union Bank of India, <b>ITD Cementation India</b> and PNB Housing Finance. <b>ITD Cementation has returned and Cemindia Projects has dropped off</b> &mdash; the exact reverse of Thursday evening&rsquo;s list. <b>We hold LENSKART</b>, which remains their idea and our underwater position at the same time.</p>
<p class="note"><strong>Their global board has India in a Confirmed Uptrend with only six other countries</strong> &mdash; United Kingdom, Mexico, Pakistan, Peru, Qatar and the UAE &mdash; against <b>seventeen in Downtrend</b> (Germany, China, Hong Kong, Brazil and Italy among them), <b>ten under pressure</b>, and <b>fifteen in Rally Attempt, the United States among those</b>. India is in a distinct minority of strong markets, which is the context the tariff headline sits in.</p>
<p>Stock-specific, from their list: <b>Mahanadi Coalfields lists on the BSE today</b> in the &lsquo;B&rsquo; group under scrip code 545032 at an issue price of <b>&#8377;136</b>, joining a special pre-open session &mdash; it is covered in the IPO review on this page. <b>Zydus Lifesciences</b>&rsquo; US arm received a <b>Complete Response Letter</b> from the FDA for Saroglitazar, tied to an October inspection of its Moraiya plant. <b>NSE</b> has SEBI&rsquo;s nod for corporate bond index futures and <b>BSE</b> an Index Service Provider registration. Orders and corporate actions: Waaree Renewable a 120 MWp module-and-EPC order, Texmaco Rail &#8377;55.63 crore from Utkal Alumina, Supriya Lifescience a buyback to be considered on 2 December, Poonawalla Fincorp a preferential issue on 1 December, Ashiana Housing a Chennai senior-living land buy with &#8377;1,100 crore sales potential, Exide a further &#8377;250 crore into its battery arm, KPI Green 65.1 MWp more at Bharuch, Acme Solar 50 MW at Bikaner, Omnitech a BrahMos airframe order, and block deals in Amagi (Norwest selling &#8377;262 crore) and IIFL Finance (Smallcap World selling &#8377;337 crore, UBS buying &#8377;259 crore). <b>Nothing in that list touches a name we hold.</b></p>
<p class="note"><strong>And the part where they and the rulebook part company, which is worth writing down rather than glossing.</strong> Their advice this morning is explicit: &ldquo;<em>investors currently have a favorable window to build positions</em>&rdquo;, and &ldquo;<em>add exposure: increase allocation progressively</em>&rdquo;. <b>We are doing the opposite, and deliberately.</b> Their reading is of the index; ours is of the 882 names our scans actually buy from, and that reading has failed for nine consecutive sessions. <b>Nothing is bought today.</b> Entries are halted by hand as well as refused by the gate, and nothing in this mail changes either &mdash; the breadth figure at the top of this page was computed from Thursday&rsquo;s close and stands whatever the first print does.</p>
"""


PREMARKET_2026_11_30 = """<h2 id="pre-session-read">Pre-session read</h2>
<p class="lead">Monday 30 November, written on Friday&rsquo;s close. <strong>The Nifty lost 1.07% to 25,607.20 &mdash; 277.30 points, and its first losing week after four winning ones &mdash; while the Midcap 100 rose 0.10% and the Smallcap 100 rose 0.56%.</strong> Breadth across the scanned universe came back at <b>48.30%</b> above their own 20-day average, against a five-session mean of <b>49.16%</b>. <b>The shortfall is 0.86 of a point</b> &mdash; the narrowest it has been in this whole stretch, and still a shortfall. It is the <strong>tenth consecutive session</strong> the market our setups live in has failed its own breadth test.</p>
<p class="sub">Divyansh read Friday as a small-cap day and asked whether the book should move that way. <strong>He is right about Friday and the measurement says Friday does not carry.</strong> That is the second section on this page, and it is the first time the question has been measured rather than argued.</p>

<h3 class="sub" id="pre-gates">The two gates</h3>
<div class="scroll"><table><thead><tr><th class="l">reading</th><th class="l">value</th><th class="l">verdict</th></tr></thead><tbody>
<tr><td class="l"><b>Market breadth</b>, whole scanned universe</td><td class="l"><b>48.30%</b> of <b>882</b> names above their 20-day average, against a five-session mean of <b>49.16%</b> &mdash; a <b>0.86-point</b> shortfall</td><td class="l fail"><span>SHUT</span></td></tr>
<tr><td class="l"><b>The index trend</b></td><td class="l">Nifty 50 <b>2.69% above its own 20-day average</b> and 5.69% above the 50-day EMA, in a <b>Confirmed Uptrend</b> counted from the <b>2 November</b> follow-through. MarketSmith agrees, and their distribution count <b>fell from two to one</b> on Friday</td><td class="l pass"><span>OPEN</span></td></tr>
</tbody></table></div>
<p class="note"><strong>One gate open, one shut, so nothing is bought &mdash; the tenth session in a row in that state.</strong> Entries are also <strong>halted by hand</strong>, separately from either gate, and remain so. The breadth gap has closed from 8.5 points on Friday morning to <b>0.86</b> this morning, which is the first genuine improvement in the series rather than the test getting easier: <b>the level rose 4.5 points and the mean it is measured against fell 3.1</b>, so most of the closing is real and some of it is the mean decaying.</p>
<p class="note"><strong>&#9888; A reporting fault in the same readout, found on Friday evening and not yet fixed.</strong> The regime printer says &ldquo;<em>MarketSmith CONFIRMED_UPTREND 42d stale &mdash; ignored</em>&rdquo;. It is not stale. The interval it is reading runs <b>2026-10-16 &rarr; current</b> and the printer is treating the interval&rsquo;s <em>start</em> as its as-of date. Friday&rsquo;s own board has MarketSmith at <b>Confirmed Uptrend</b> and so does ours &mdash; the two agree. <b>This matters because the follow-through gate refuses to buy on &ldquo;unknown or stale&rdquo;</b>, so a cosmetic misread sits one step away from being a real refusal. It is on the fix list, not fixed.</p>

<h3 class="sub" id="pre-caps">&ldquo;Small caps were up and the Nifty was down&rdquo; &mdash; measured</h3>
<p class="sub">Divyansh asked on Friday evening whether the book should turn toward small caps. <strong>The premise is correct and the conclusion does not follow</strong>, and the way to tell them apart is to measure the condition rather than the day.</p>
<p class="note"><strong>Friday, as described.</strong> Nifty 50 <b>&minus;1.07%</b>, Midcap 100 <b>+0.10%</b>, Smallcap 100 <b>+0.56%</b>. That is exactly the divergence he saw.</p>
<p class="note"><strong>What that condition has been worth.</strong> A new backtest replays the exact rule &mdash; <em>the Nifty fell and the smallcaps rose</em> &mdash; across <b>345 sessions</b> of the real NSE index archive, <b>7 July 2025 to 27 November 2026</b>, and asks what the smallcap-minus-Nifty spread did <em>afterwards</em>. The condition fired on <b>49 of 344 sessions, 14.2% of them</b>.</p>
<div class="scroll"><table><thead><tr><th class="l">sessions ahead</th><th>after it fired</th><th>after it did not</th><th>gap</th><th>permutation p</th></tr></thead><tbody>
<tr><td class="l">1</td><td class="pass">+0.09</td><td>&minus;0.00</td><td class="pass">+0.09</td><td>0.47</td></tr>
<tr><td class="l">5</td><td class="bad">&minus;0.17</td><td class="pass">+0.06</td><td class="bad"><b>&minus;0.23</b></td><td>0.39</td></tr>
<tr><td class="l">10</td><td class="bad">&minus;0.30</td><td class="pass">+0.11</td><td class="bad"><b>&minus;0.41</b></td><td>0.29</td></tr>
<tr><td class="l">20</td><td class="bad">&minus;0.24</td><td class="pass">+0.34</td><td class="bad"><b>&minus;0.57</b></td><td>0.38</td></tr>
</tbody></table></div>
<p class="note"><strong>Past the first day it is negative at every horizon, negative in both halves of the sample, and nothing is close to significant.</strong> Ten thousand permutations that shuffle which days the signal picked out &mdash; keeping the return series exactly as it fell &mdash; beat the real signal between 29% and 47% of the time. <b>A day on which the broad market outruns the index is a description of that day.</b> The honest reading is not &ldquo;rotate&rdquo; and not &ldquo;do the opposite&rdquo; either; it is that this particular day carries no information about the next month.</p>
<p class="note"><strong>One related signal did look real, and it fails the split that every finding on this site has to survive.</strong> &ldquo;Smallcaps ahead over the trailing five sessions&rdquo; showed a <b>+0.83</b> gap at ten sessions (p&nbsp;=&nbsp;0.0022) and <b>+1.35</b> at twenty (p&nbsp;=&nbsp;0.0038) &mdash; which, taken whole, reads like an edge. Split within periods it collapses: <b>first half +0.09 (p&nbsp;=&nbsp;0.74) and +0.14 (p&nbsp;=&nbsp;0.74); second half +1.13 (p&nbsp;=&nbsp;0.02) and +1.67 (p&nbsp;=&nbsp;0.07)</b>. All of it is one regime. <b>And it is not firing anyway</b> &mdash; the trailing-five spread is currently negative. A cross-section is not evidence until it survives a within-period split, which is the rule that saved us here.</p>
<p class="note"><strong>The window decides the answer, and that is itself the finding.</strong> Over the last <b>60 sessions</b> the large caps led decisively &mdash; Nifty <b>+6.34%</b> against Midcap 150 <b>&minus;3.76%</b> and Smallcap 100 <b>&minus;2.26%</b>. Over <b>calendar 2026, on our own closes</b>, it is the exact reverse: non-index names returned <b>+15.4%</b> against index members&rsquo; <b>+7.1%</b>, measured in Thursday&rsquo;s large-cap study. Both are true. <b>Any rotation call that flips depending on which of those two windows you happen to pick is not a call, it is a window.</b></p>
<p class="note"><strong>And the change is not one that is available to us.</strong> The scanned universe is <b>1,065 names</b>, almost none of them Nifty 50 &mdash; <b>the book is already entirely small and mid cap.</b> The other direction was measured on Thursday and earns nothing: all <b>980</b> large-cap rule combinations tested lost money, against <b>+0.4%</b> for simply holding the index members. <strong>So: no change on capitalisation, and none is proposed.</strong> The things actually binding are further down this page.</p>

<h3 class="sub" id="pre-indices">What Friday actually did</h3>
<p class="sub">MarketSmith&rsquo;s sector moves for the <strong>27 November</strong> session, as their weekly Big Picture prints them.</p>
<div class="scroll"><table><thead><tr><th class="l">index</th><th>27 Nov move</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>Nifty IT</b></td><td class="bad">&minus;1.88%</td><td class="l">the day&rsquo;s whole story, and the exact reverse of Thursday&rsquo;s +3.66% &mdash; <b>TCS, Infosys and HCLTECH each &minus;2.5% to &minus;2.8%</b></td></tr>
<tr><td class="l">Auto &middot; Realty &middot; Financial Services</td><td class="bad">&minus;1.48% &middot; &minus;1.43% &middot; &minus;1.33%</td><td class="l">Realty gave back nearly half of Thursday&rsquo;s +3.27%</td></tr>
<tr><td class="l">FMCG &middot; Bank &middot; Pharma</td><td class="bad">&minus;0.93% &middot; &minus;0.78% &middot; &minus;0.40%</td><td class="l">FMCG down a second session</td></tr>
<tr><td class="l"><b>Nifty Metal</b></td><td class="pass">+1.40%</td><td class="l">the best sector of the day, green a second session</td></tr>
<tr><td class="l">Media &middot; Consumer Durables &middot; Energy</td><td class="pass">+0.53% &middot; +0.26% &middot; +0.15%</td><td class="l">Consumer Durables recovered from Thursday&rsquo;s &minus;1.33%</td></tr>
<tr><td class="l"><b>Midcaps &middot; Smallcaps</b></td><td class="l"><span class="pass">+0.10%</span> &middot; <span class="pass">+0.56%</span></td><td class="l"><b>Both beat the index for a second consecutive session.</b> Two sessions is still not a rotation &mdash; see the measured section above</td></tr>
</tbody></table></div>
<p class="note"><strong>The one internal that argues against reading Friday as distribution.</strong> The Nifty fell 1.07% on volume <b>16.52% lower</b> than Thursday&rsquo;s. A fall on lighter volume is not a distribution day, and MarketSmith&rsquo;s count duly came <b>down from two to one</b> on a day the index dropped nearly 300 points. Only <b>10 of the Nifty&rsquo;s own fifty</b> advanced. The index closed <b>2.94% above its 21-day average</b>, <b>8.06% above the 50-day</b> and <b>2.90% below its 52-week high</b>.</p>
<p class="note"><strong>The drivers, as the desks give them.</strong> <b>Brent above $97</b>, the <b>rupee near 92.92</b>, rising bond yields, and profit-taking into the first down week in five. The US tariff reassessment is still the live overhang. Sources: <a href="https://www.businesstoday.in/markets/stocks/story/bt-closing-bell-sensex-plunges-989-pts-nifty-ends-at-25607-what-fridays-market-fall-reflects-569980-2026-11-27">Business Today</a> and <a href="https://insights.dsij.in/dsijarticledetail/closing-bell-sensex-falls-nearly-1000-points-nifty-50-drops-over-1-nifty-small-cap-jumps-nearly-05-60677">DSIJ</a>. The Sensex closed <b>83,339.26</b>, down 989.34 points or 1.17%.</p>
<p class="note"><strong>And the flow number cuts against the headline.</strong> On the day the index fell 277 points, <b>FIIs net bought &#8377;1,634.33 crore</b> (bought &#8377;14,259.45 Cr, sold &#8377;12,625.12 Cr) while <b>DIIs net sold &#8377;556.42 crore</b>. Foreign money was the buyer into the fall. That is recorded, not acted on &mdash; <b>166 months of FII flow were measured on this site and carry no predictive edge</b>, so it does not gate anything.</p>

<h3 class="sub" id="pre-risk">The open book, and what is closest to being stopped out</h3>
<p class="sub">Read live from all three brokers at <b>16:30 Friday</b>, after the trail was run by hand. <b>Twelve equity names plus the three parking funds.</b></p>
<div class="scroll"><table><thead><tr><th class="l">symbol</th><th>position</th><th>to its stop</th><th class="l">note</th></tr></thead><tbody>
<tr><td class="l"><b>SONACOMS</b></td><td class="bad">&minus;4.5%</td><td class="bad"><b>0.61%</b></td><td class="l"><b>The name that decides itself on Monday.</b> Stop 873.60 in all three accounts against a 879.00 close &mdash; it was 5.9% away on Friday morning and Friday&rsquo;s session spent nearly all of it. <b>MarketSmith still holds it</b> in their model portfolio, at RS 90 and +28.90% over its 200-day, down 1.51% on the week</td></tr>
<tr><td class="l">LENSKART</td><td class="bad">&minus;1.8%</td><td class="warn">2.6%</td><td class="l">Under water for us and <b>on MarketSmith&rsquo;s buy watchlist at the same time</b>, as it has been all week</td></tr>
<tr><td class="l">SBC</td><td class="pass">+1.5%</td><td class="warn">2.8%</td><td class="l">Stop trailed to 66.18 on Friday</td></tr>
<tr><td class="l">ROSSTECH</td><td class="bad">&minus;0.6%</td><td class="l">6.4%</td><td class="l">One of the three that cannot be trailed &mdash; see below</td></tr>
<tr><td class="l">TFCILTD &middot; PTCIL</td><td class="l"><span class="pass">+0.5%</span> &middot; <span class="pass">+3.2%</span></td><td class="l">6.9% &middot; 7.5%</td><td class="l">Both are single-account holdings, flagged below</td></tr>
<tr><td class="l">GCSL &middot; PVRINOX</td><td class="l"><span class="pass">+3.6%</span> &middot; <span class="pass">+3.0%</span></td><td class="l">7.6% &middot; 7.6%</td><td class="l">GCSL trailed to 786.65; PVRINOX could not be</td></tr>
<tr><td class="l">SHUKRAMED &middot; RATNAVEER</td><td class="l"><span class="pass">+7.8%</span> &middot; <span class="pass">+4.1%</span></td><td class="l">8.2% &middot; 8.4%</td><td class="l">&mdash;</td></tr>
<tr><td class="l">AARTIPHARM</td><td class="pass">+3.9%</td><td class="l">9.8%</td><td class="l">The third that cannot be trailed</td></tr>
<tr><td class="l"><b>CUPID</b></td><td class="pass">+12.7%</td><td class="l">11.2%</td><td class="l"><b>The best position in the book</b>, and still stopped at 346.00 &mdash; barely above its own cost, because the trail will not lift a stop past what the 20-day average supports</td></tr>
</tbody></table></div>
<p class="note"><strong>Ten of the twelve names are green.</strong> The equity book is up about <strong>&#8377;69,800 unrealised</strong> &mdash; &#8377;51,812 in t-default, &#8377;11,133 in t-ramprasad, &#8377;6,842 in akul &mdash; with a further <b>&#8377;34,950 on the parked LIQUIDCASE</b> across the three. The two red names are <b>SONACOMS</b> and <b>LENSKART</b>, and they are also the two closest to their stops, which is how a book should look.</p>
<p class="note"><strong>Twelve stops were trailed up on Friday afternoon</strong> &mdash; CUPID to 346.00, GCSL to 786.65 and SBC to 66.18 in every account, plus PTCIL in akul, RATNAVEER in t-ramprasad and SHUKRAMED in akul. <b>Nine refused</b>, which is the next section.</p>
<p class="note"><strong>Three breaks in the rule that every account holds the same names</strong>, all old and all flagged rather than corrected. <b>PTCIL</b> is held in <b>akul alone</b>. <b>RATNAVEER</b> and <b>TFCILTD</b> are held in <b>t-ramprasad alone</b> &mdash; both bought there on Divyansh&rsquo;s own instruction. All three carry resting stops. Nothing is evened up without him saying so.</p>

<h3 class="sub" id="pre-stops-30">&#9888; Three names cannot be trailed at all, and two parking funds have no stop recorded</h3>
<p class="note"><strong>AARTIPHARM, PVRINOX and ROSSTECH each refused their trail in all three accounts, for the same reason</strong> &mdash; <em>placement rejected: quantity must be positive, got 0</em>. These are the positions carrying a second, added leg, and the code that works out how many shares a replacement stop should cover computes <b>zero</b> for them. <b>None of the three is unprotected</b>: each kept the stop it already had, at <b>915.60</b>, <b>1,551.00</b> and <b>1,375.00</b>. But they cannot be moved up at all until the writer is fixed, and they have now failed <b>eighteen times live</b> across Friday&rsquo;s two passes. <b>The fix belongs in the writer, not in the rows</b> &mdash; editing the stored quantities would hide the defect rather than end it.</p>
<p class="note"><strong>LIQUIDCASE has no stop of any kind recorded in akul or t-ramprasad.</strong> The parking fund is not a trade and is not meant to carry one, so this is a bookkeeping gap rather than an exposed position &mdash; but it is the kind of gap a stop check that reads our own records would tick green over, and it is written down here for that reason. <b>t-default&rsquo;s parking does carry one, at 115.92.</b></p>
<p class="note"><strong>And the standing one: a stop check that reads our own database is not a check.</strong> Everything above was read against the brokers themselves. Where our record and the broker disagree, the broker is what is quoted.</p>

<h3>MarketSmith, 27 November &mdash; the weekly Big Picture, read in full</h3>
<p><strong>Their headline:</strong> &ldquo;<em>Crude Shock on D-Street: Brent Above $97 and IT Selloff Drag Nifty 1% Lower to 25,607, Ending its Four-Week Winning Run.</em>&rdquo; <strong>Market Pulse: CONFIRMED UPTREND, distribution days down from two to one.</strong> The Nifty fell <b>1.07% to 25,607.20</b> on volume <b>16.52% lower</b>, with only <b>10 of the fifty</b> advancing &mdash; closing <b>2.94% above its 21-day average</b>, <b>8.06% above the 50-day</b> and <b>2.90% below its 52-week high</b>. Midcap 100 +0.10%, Smallcap 100 +0.56%.</p>
<p>Sectors: <b>Metal +1.40</b>, Media +0.53, Consumer Durables +0.26, Energy +0.15; against <b>IT &minus;1.88</b>, Auto &minus;1.48, Realty &minus;1.43, Financial Services &minus;1.33, FMCG &minus;0.93, Bank &minus;0.78, Pharma &minus;0.40. <b>Eight of eleven sectoral indices closed lower.</b> On their own sector board, <b>Metal and IT are in Uptrend Under Pressure</b> and the rest in Confirmed Uptrends &mdash; Metal marked under pressure on the day it rose 1.40%, which is what a distribution count does to a one-day move.</p>
<p class="note"><strong>Two additions to their model portfolio this week, and one of them arrived with a full alert.</strong> They added <b>Action Construction Equipment (ACE)</b> and <b>Indo-MIM (INDOMIM)</b>. The Indo-MIM alert, timed <b>10:52 on Friday</b>, gives an add price of <b>&#8377;1,342</b> and a buy range of <b>&#8377;1,322&ndash;1,388</b> &mdash; Metal Processing &amp; Fabrication, market cap <b>&#8377;64,144.08 Cr</b>, 50-day average traded value <b>&#8377;201.49 Cr</b>, <b>EPS Rank 96</b>, <b>RS Rating 95</b>, Buyer Demand <b>B+</b>, breaking out of a stage-one cup-with-handle after six weeks of consolidation. <b>Neither name is on our own list and nothing is bought from theirs</b>; they are recorded because their adds are worth watching against what our scans find. Their model portfolio was <b>&minus;0.40% on the week</b>.</p>
<p class="note"><strong>Two industry-group moves worth noting, because we hold into one of them.</strong> <b>Retail&ndash;Specialty improved from rank 43 to 8</b> &mdash; that is the group <b>LENSKART</b> sits in, which remains on their buy watchlist while sitting under water for us. <b>Leisure&ndash;Movies improved from 38 to 21</b>, which is <b>PVRINOX</b>, one of the three names whose stop cannot be moved.</p>
<p class="note"><strong>And their own position in SONACOMS, which is our tightest.</strong> They hold it, down <b>1.51% on the week</b>, at <b>RS 90</b>, <b>+4.47% over its 50-day</b> and <b>+28.90% over its 200-day</b>, with the position <b>+1.97%</b> for them. <b>Our stop is 0.61% below Friday&rsquo;s close</b> and it is ours that binds. If Monday opens lower it goes, and that is the rule working rather than failing.</p>
<p class="note"><strong>Where they and the rulebook part company, again.</strong> Their reading is of the index, which is in a Confirmed Uptrend with one distribution day. Ours is of the <b>882 names our scans actually buy from</b>, and that reading has now failed for ten consecutive sessions. <b>Nothing is bought on Monday.</b> Entries are halted by hand as well as refused by the gate.</p>
"""


BY_DAY: dict[str, str] = {
    "2026-11-12": PREMARKET_2026_11_12,
    "2026-11-16": PREMARKET_2026_11_16,
    "2026-11-17": PREMARKET_2026_11_17,
    "2026-11-18": PREMARKET_2026_11_18,
    "2026-11-19": PREMARKET_2026_11_19,
    "2026-11-20": PREMARKET_2026_11_20,
    "2026-11-23": PREMARKET_2026_11_23,
    # 24 Nov was an NSE holiday; the 25th is built on the 23rd's close.
    "2026-11-25": PREMARKET_2026_11_25,
    "2026-11-26": PREMARKET_2026_11_26,
    "2026-11-27": PREMARKET_2026_11_27,
    "2026-11-30": PREMARKET_2026_11_30,
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
