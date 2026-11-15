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


BY_DAY: dict[str, str] = {
    "2026-11-12": PREMARKET_2026_11_12,
    "2026-11-16": PREMARKET_2026_11_16,
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
