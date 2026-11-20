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
names may be placed.</strong></p>
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
<tr><td class="l"><b>SHUKRAMED</b> &mdash; open fault</td><td class="l">The SHUKRAPHAR renaming has <b>cut the position loose</b>. The brokers hold <b>2,644 shares</b> as SHUKRAMED (2,000 / 379 / 265) and list them as not ours; this service still records SHUKRAPHAR with a stop at 79.25, and <b>no sell order rests at any broker for either symbol</b>.</td><td class="l fail"><span>unprotected in all three</span></td></tr>
<tr><td class="l">Six stale stop records</td><td class="l">ACMESOLAR, GLAND, LAURUSLABS, PAYTM, SSWL and SHYAMMETL still have stop rows in our record with <b>no position and no broker order behind any of them</b> &mdash; residue from positions already closed.</td><td class="l warn"><span>record, not risk</span></td></tr>
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
weeks. <strong>Against that, four positions can no longer lose:</strong> CUPID and SGMART in all three
accounts have their stops at the entry price, and SGMART alone is carrying <b>+4R</b>. The book is not
in trouble; it is simply not being added to, and has not been for six sessions.</p>
"""


BY_DAY: dict[str, str] = {
    "2026-11-12": PREMARKET_2026_11_12,
    "2026-11-16": PREMARKET_2026_11_16,
    "2026-11-17": PREMARKET_2026_11_17,
    "2026-11-18": PREMARKET_2026_11_18,
    "2026-11-19": PREMARKET_2026_11_19,
    "2026-11-20": PREMARKET_2026_11_20,
    "2026-11-23": PREMARKET_2026_11_23,
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
