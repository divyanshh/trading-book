#!/usr/bin/env python3
"""The hand-written IPO review, as the report's own components.

The analysis is a person's work — sources read, numbers checked, a call made
per issue (`cortex/checklists/ipo_checklist.md`). What this file removes is the
*typing* of the HTML: the data sits in `IPOS` below, and the section is emitted
with the same cards, gate-style badges and bars the scanner sections use, so
the review does not look like a different website.

    python3 ipo_review.py 2026-09-23

writes `extras/<date>_ipo_review.html` (standalone) and splices the section
into `overrides/<date>.html` between the IPO board and the exchange filings —
the override the mirror publishes over the dyno's copy.

GMP is the grey-market premium on the morning of writing; **expected listing is
GMP% minus 2.6 points**, the overstatement `backtest_gmp` measured over 295
listings (r = 0.87). A zero GMP has averaged -6.6%.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OVERSTATEMENT = 2.6


@dataclass(frozen=True)
class IPO:
    name: str
    call: str
    tone: str                 # pass / warn / fail
    dates: str
    band: str
    size: str
    split: str                # fresh / OFS
    gmp: str
    gmp_pct: float
    expected: str
    apply_as: str
    horizon: str
    book: str
    stats: tuple[tuple[str, str], ...] = ()
    note: str = ""
    flags: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (label, tone)


def card(ipo: IPO) -> str:
    """One issue as a panel: the call, the GMP against the board's best, the case."""
    e = html.escape
    fill = max(0, min(100, int(ipo.gmp_pct / 35 * 100)))
    bar = (
        f'<div class="bar"><div class="barhead"><span>expected listing</span>'
        f'<b class="{ipo.tone}">{e(ipo.expected)}</b></div>'
        f'<div class="track"><div class="fill {ipo.tone}" style="width:{fill}%"></div></div>'
        f'<div class="barfoot"><span>GMP {e(ipo.gmp)} · {ipo.gmp_pct:+.1f}% '
        f'· less the {OVERSTATEMENT} pt overstatement</span></div></div>'
    )
    flags = (
        '<div class="dots">'
        + "".join(f'<span class="dot {t}">{e(l)}</span>' for l, t in ipo.flags)
        + "</div>"
        if ipo.flags
        else ""
    )
    stats = (
        '<dl class="stats">'
        + "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in ipo.stats)
        + "</dl>"
        if ipo.stats
        else ""
    )
    return (
        f'<article class="card"><header><h3>{e(ipo.name)}</h3>'
        f'<span class="badge {ipo.tone}">{e(ipo.call)}</span></header>'
        f'<p class="meta">{e(ipo.dates)} · band {e(ipo.band)} · {e(ipo.size)} · {e(ipo.split)}</p>'
        f"{flags}{bar}{stats}"
        f'<p class="cardnote">{e(ipo.note)}</p></article>'
    )


def row(ipo: IPO) -> str:
    e = html.escape
    bar = max(0, min(100, int(ipo.gmp_pct / 35 * 100)))
    return (
        f'<tr><td class="l">{e(ipo.name)}</td>'
        f'<td class="{ipo.tone} l"><span>{e(ipo.call)}</span></td>'
        f"<td>{e(ipo.gmp)}</td>"
        f'<td class="{ipo.tone}"><span class="cellbar" style="--w:{bar}%">'
        f"{ipo.gmp_pct:+.1f}%</span></td>"
        f'<td class="{ipo.tone}">{e(ipo.expected)}</td>'
        f'<td class="l">{e(ipo.apply_as)}</td>'
        f'<td class="l">{e(ipo.horizon)}</td>'
        f'<td class="l">{e(ipo.book)}</td></tr>'
    )


def section(ipos: list[IPO], lead: str, footnote: str) -> str:
    head = (
        '<tr><th class="l">IPO</th><th class="l">call</th><th>GMP</th><th>GMP %</th>'
        '<th>expected listing</th><th class="l">apply as</th><th class="l">horizon</th>'
        '<th class="l">book</th></tr>'
    )
    return (
        '<h2 id="ipo-review">IPO review — apply, skip, avoid</h2>'
        f'<p class="lead">{lead}</p>'
        f'<div class="scroll"><table><thead>{head}</thead><tbody>'
        + "".join(row(i) for i in ipos)
        + "</tbody></table></div>"
        f'<p class="sub">{footnote}</p>'
        '<div class="cards">' + "".join(card(i) for i in ipos) + "</div>"
    )


def _style(day: str) -> str:
    """The report's own stylesheet, so the standalone page is not a different site.

    Taken from the day's override when the report has been mirrored, and from
    the most recent earlier override when it has not — the theme does not
    change between days, and the review is written before the 18:00 build far
    more often than after it.
    """
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

    **Both halves say what they did.** Until 2026-09-25 this wrote neither file
    when the day's override was absent — which is every morning before the
    18:00 build — and printed the same success line as a run that wrote both.
    A review was composed, the command reported thirteen issues written, and
    the directory was empty.
    """
    standalone = ROOT / "extras" / f"{day}_ipo_review.html"
    standalone.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>IPO review — {day}</title>{_style(day)}</head><body>"
        f'<div class="wrap"><p class="eyebrow">equity-service · cortex · {day}</p>'
        f"{markup}"
        "<footer>Hand-written under <code>cortex/checklists/ipo_checklist.md</code>. "
        f'Also a section of <a href="{day}.html#ipo-review">the day\'s report</a>.'
        "</footer></div></body></html>",
        encoding="utf-8",
    )
    print(f"  wrote extras/{standalone.name}")

    override = ROOT / "overrides" / f"{day}.html"
    if not override.exists():
        print(
            f"  overrides/{day}.html does not exist yet — the report builds at 18:00 IST.\n"
            f"  Re-run this after mirroring to splice the section into it."
        )
        return
    page = override.read_text(encoding="utf-8")
    start = page.find('<h2 id="ipo-review">')
    end = page.find('<h2 id="exchange-filings">')
    if end < 0:
        raise SystemExit("no exchange-filings anchor in the override")
    page = (page[:start] if start >= 0 else page[:end]) + markup + page[end:]
    if 'href="#ipo-review"' not in page:
        page = page.replace(
            '<a href="#ipos---mainboard">IPOs — mainboard</a>',
            '<a href="#ipos---mainboard">IPOs — mainboard</a>'
            '<a href="#ipo-review">IPO review</a>',
        )
    override.write_text(page, encoding="utf-8")
    print(f"  spliced the section into overrides/{override.name}")


# ── 23 September 2026 ───────────────────────────────────────────────────────
# Sources: Trendlyne (detail pages + research-report list), Chittorgarh, IPO
# Watch GMP board (07:50), Value Research, anchor circulars, independent
# reviews. Brokerage "Subscribe" notes cover nearly every issue and are not a
# signal; a Neutral or an Avoid from any house is.

IPOS_2026_09_23 = [
    IPO(
        name="Adroit Industries", call="APPLY", tone="pass",
        dates="23–25 Sep", band="₹134", size="₹151 Cr", split="88% fresh / 12% OFS",
        gmp="₹34", gmp_pct=25.4, expected="~+23%",
        apply_as="sHNI ₹2–10L (applied)", horizon="Listing-day sell; hold a tranche if QIB ≥ 5x",
        book="day 1: 1.1x · retail 1.69x · QIB 0",
        flags=(("best of the board", "pass"), ("small issue", "warn"), ("QIB 0 on day 1", "warn")),
        stats=(("P/E post", "23.0x"), ("RoE", "22.5%"), ("D/E", "0.41"),
               ("EBITDA margin", "27.7%"), ("retail slice", "₹53 Cr"), ("odds at 20x", "~5%")),
        note=(
            "Sixty-year driveline maker — propeller shafts, Dewas MP, >90% exports to 32 "
            "countries. FY24→FY26 revenue 125→143 Cr, PAT 14.5→26.2 Cr (+44%), EBITDA margin "
            "23.7→27.7% against 11–16% for GNA Axles, Talbros and Hindustan Hardy; 88% fresh, "
            "into Dewas and Pithampur capex. Anchors ₹45.2 Cr from six domestic AIFs (Abakkus "
            "₹10 Cr, Chhattisgarh Investments ₹10 Cr, Valour ₹7.5 Cr, Cognizant Capital ₹7.5 Cr, "
            "Aarth ₹5.2 Cr, Fortune Hands ₹5 Cr) — no mutual fund, which is adequate rather than "
            "a stamp. Risks: top-10 customers 67% of revenue, top-10 suppliers 92% of purchases, "
            "US concentration, 237-day working capital, borrowings 8→52 Cr in a year. "
            "What flips the call: QIB under 1x at Friday's close with retail above 5x is the "
            "weak-listing pattern — sell the whole allotment at the open."
        ),
    ),
    IPO(
        name="Moneyview", call="APPLY", tone="pass",
        dates="24–28 Sep", band="₹34", size="₹1,092 Cr", split="69% fresh / 31% OFS",
        gmp="₹11", gmp_pct=32.4, expected="~+30%",
        apply_as="Retail 1 lot + sHNI ₹2L", horizon="Sell 70% on listing; hold 30% only on clean Q2 credit costs",
        book="opens 24th · anchor book 23rd",
        flags=(("highest GMP", "pass"), ("RBI/DLG risk", "fail"), ("big retail slice", "pass")),
        stats=(("P/E FY26", "21.5x"), ("P/E annualised", "8.6x"), ("P/B", "2.6"),
               ("managed AUM", "₹21,380 Cr"), ("retail slice", "₹382 Cr"), ("promoters post", "20%")),
        note=(
            "Digital personal-loan platform: 140M registered users, 9.7M monetised, 48 lending "
            "partners. FY26 revenue +43% to 3,404 Cr but PAT +1% to 243 Cr — the margin "
            "compression is the number to understand, and the June quarter (PAT 174 Cr) says it "
            "may have turned; expenses fell 56%→35% of income FY24→FY26. Lead managers Axis, "
            "BofA, IIFL, Kotak. Risks: the default-loss-guarantee model is exactly where RBI has "
            "been tightening; unsecured book; top-10 partners 37% of revenue; no NPA or "
            "credit-cost disclosure in the summaries; 31% OFS; the issue was trimmed to a ~$624M "
            "valuation. As a hold this is a regulatory bet; as a listing trade it is the "
            "strongest here. Read tonight's anchor list — domestic mutual funds would de-risk it."
        ),
    ),
    IPO(
        name="Orient Cables", call="APPLY", tone="pass",
        dates="25–29 Sep", band="₹272", size="₹552 Cr", split="58% fresh / 42% OFS",
        gmp="₹34", gmp_pct=12.5, expected="~+10%",
        apply_as="Retail 1 lot; sHNI if GMP ≥ ₹30 on day 3", horizon="Sell half on listing, hold half",
        book="anchor 24 Sep · retail ₹193 Cr",
        flags=(("sector IMPROVING on our RRG", "pass"), ("PAT flat on +42% revenue", "warn")),
        stats=(("P/E post", "23.6x"), ("RoE", "25.8%"), ("D/E", "0.95"),
               ("market share", "22.9%"), ("peers", "12–16x"), ("promoters post", "82%")),
        note=(
            "#4 in networking cables — broadband, telecom, data centres, e-mobility. FY26 revenue "
            "+42% to 1,182 Cr, PAT flat at 54 Cr as copper pass-through took the margin 6.4→4.6%; "
            "the June-26 quarter recovered to PAT 33 Cr and EBITDA 11.2%, which is the question "
            "answered if it holds. ₹155 Cr of proceeds to debt, ₹92 Cr capex; JM + IIFL. "
            "Electrical/power equipment is IMPROVING on our own RRG at rank 29 — the one issue "
            "here in a sector the scan likes. 42% OFS is the caveat."
        ),
    ),
    IPO(
        name="A-One Steels", call="APPLY, small", tone="pass",
        dates="24–28 Sep", band="₹405", size="₹405 Cr", split="88% fresh / 12% OFS",
        gmp="₹50", gmp_pct=12.3, expected="~+10%",
        apply_as="Retail 1 lot only", horizon="Listing-day sell, no hold",
        book="anchor 23 Sep · no names published",
        flags=(("one-year PAT jump", "warn"), ("OCF −40%", "fail")),
        stats=(("P/E post", "24.6x"), ("RoE", "14.7%"), ("D/E", "1.17"),
               ("capacity", "1.73 MTPA"), ("peers", "17–21x"), ("to debt", "₹250 Cr")),
        note=(
            "Southern integrated steel, six plants in Karnataka and Andhra, green power under "
            "15–25-year PPAs. FY26 revenue 4,202 Cr (+18%), PAT 7.7→127 Cr as EBITDA margin went "
            "4.9→7.3%. Against it: the profit jump is one year old, operating cash flow fell ~40% "
            "to 63 Cr — profit quality unproven — and recent steel listings trade at 17–21x. "
            "PL Capital + Khambatta. One retail lot for the pop; it will trade on steel prices, "
            "not on this IPO."
        ),
    ),
    IPO(
        name="ArMee Infotech", call="SKIP", tone="warn",
        dates="23–25 Sep", band="₹375", size="₹300 Cr", split="fresh-heavy",
        gmp="₹46", gmp_pct=12.3, expected="~+10%",
        apply_as="—", horizon="—",
        book="quota retail 52.5% / NII 22.5% / QIB 25%",
        flags=(("retail-heavy quota", "fail"), ("PAT below FY24", "fail"), ("RoCE 57→24%", "fail")),
        stats=(("P/E", "26.2x"), ("PAT margin", "3.3%"), ("borrowings", "48→174 Cr"),
               ("contingent liab.", "₹129 Cr"), ("bankers' record", "7 of 9 below issue")),
        note=(
            "IT infrastructure and managed services for government and PSU clients, Ahmedabad, "
            "plus a renewable sideline. FY26 revenue 1,410 Cr (+7%), PAT 45 Cr — below FY24's "
            "50 Cr; RoE 71→29% in two years; rising receivables. 26x for a 3%-margin government "
            "contractor. The quota structure is the tell: a 52.5% retail slice against 25% QIB "
            "says the bankers do not expect institutions to fill it, and their last nine issues "
            "saw seven list below price. Ventura says Subscribe; the structure says otherwise."
        ),
    ),
    IPO(
        name="German Green Steel", call="SKIP — watch after listing", tone="warn",
        dates="25–29 Sep", band="₹139", size="₹304 Cr", split="95% fresh / 5% OFS",
        gmp="₹15", gmp_pct=10.8, expected="~+8%",
        apply_as="—", horizon="Buy post-listing only at/below book, if steel holds",
        book="anchor 24 Sep · Systematix, IIFL, CLSA",
        flags=(("cheapest on the board", "pass"), ("commodity, regional", "warn")),
        stats=(("P/E", "13.1x"), ("P/B", "0.67"), ("RoE", "18.9%"),
               ("D/E", "0.79"), ("to capacity", "₹226 Cr")),
        note=(
            "TMT bars, billets and sponge iron, Kutch. FY26 revenue 1,685 Cr (+11%), PAT 80 Cr "
            "(+33%), EBITDA 9.9%; ₹226 Cr into capacity plus a hybrid wind and solar plant. The "
            "only issue here below book value, and the only one whose price does not assume the "
            "cycle continues. But it is a regional commodity steelmaker and an 8% expected "
            "listing gain is not worth the lock-up. If the 24th's anchor list carries real "
            "institutions — CLSA is on the book — a single retail lot becomes reasonable."
        ),
    ),
    IPO(
        name="Swastika Infra", call="SKIP — revisit", tone="warn",
        dates="23–25 Sep", band="₹185", size="₹161 Cr", split="80% fresh / 20% OFS",
        gmp="₹8", gmp_pct=4.3, expected="~+2%",
        apply_as="—", horizon="Post-listing study if the order book converts",
        book="—",
        flags=(("real growth", "pass"), ("contingent liab. 43% of cap", "fail")),
        stats=(("P/E", "15.2x"), ("RoNW", "35.4%"), ("order book", "₹917 Cr"),
               ("book/revenue", "1.8x"), ("contingent liab.", "₹273 Cr"), ("market cap", "₹631 Cr")),
        note=(
            "Power transmission and distribution EPC, Rajasthan-heavy. Revenue 211→506 Cr and "
            "PAT 14→41 Cr in two years is real growth at a fair multiple. But contingent "
            "liabilities of ₹273 Cr against a ₹631 Cr market cap, rising receivables and a 4% "
            "GMP: no listing edge and a balance-sheet question that the order book does not "
            "answer. Worth studying once listed and once a few quarters of conversion are visible."
        ),
    ),
    IPO(
        name="Runwal Enterprises", call="SKIP", tone="warn",
        dates="25–29 Sep", band="₹305", size="₹500 Cr", split="100% fresh",
        gmp="₹18", gmp_pct=5.9, expected="~+3%",
        apply_as="—", horizon="—",
        book="ICICI Sec + Jefferies",
        flags=(("D/E 3.29", "fail"), ("lumpy recognition", "fail"), ("one city", "warn")),
        stats=(("P/E post", "24.3x"), ("P/B", "5.0"), ("D/E", "3.29"),
               ("borrowings", "₹2,909 Cr"), ("FY24→26 income", "2,437→1,051→1,851 Cr")),
        note=(
            "Mumbai developer, #3 by launches and sales, #1 in Kalyan-Dombivli. FY26 income "
            "1,851 Cr and PAT 186 Cr look excellent until the three years are read together — "
            "2,437 / 1,051 / 1,851 Cr — which is revenue recognition, not a run-rate, so the "
            "+234% PAT year prices something that has not been earned twice. One reviewer "
            "computes the post-issue P/E at 95x on a different earnings base; when reviewers "
            "cannot agree on the base, the base is the risk. Only ₹100–325 Cr of proceeds go to "
            "debt against ₹2,909 Cr of borrowings."
        ),
    ),
    IPO(
        name="Varmora Granito", call="AVOID", tone="fail",
        dates="22–24 Sep", band="₹148", size="₹708 Cr", split="45% fresh / 55% OFS",
        gmp="₹5", gmp_pct=3.4, expected="~+1%",
        apply_as="—", horizon="—",
        book="0.15x on day 2 · QIB 0.00x · closes today",
        flags=(("book is voting no", "fail"), ("61x on 6.8% RoE", "fail")),
        stats=(("P/E post", "60.7x"), ("RoE", "6.8%"), ("P/B", "3.74"),
               ("Kajaria P/E", "~40x"), ("revenue 3 yrs", "1,473→1,563 Cr")),
        note=(
            "Morbi tiles. Revenue flat across three years, PAT 55 Cr, RoE 6.8% — and priced at "
            "61x against Kajaria's ~40x with double the return ratios. 55% OFS, with Katsura "
            "exiting, and every rupee of fresh money going to debt repayment rather than the "
            "business. Anand Rathi, Axis, Antique and Ventura said Subscribe; Canara said Avoid; "
            "the book has settled it at 0.15x on day two with QIB at zero."
        ),
    ),
    IPO(
        name="Elevate Campuses", call="AVOID at IPO", tone="fail",
        dates="23–25 Sep", band="₹362", size="₹2,100 Cr", split="100% fresh",
        gmp="₹5", gmp_pct=1.4, expected="~−1%",
        apply_as="—", horizon="Revisit below ~₹270 with verified debt reduction",
        book="anchors ₹945 Cr · retail quota only 10%",
        flags=(("₹1,100 Cr to sponsor's Singapore entities", "fail"), ("D/E 4.98", "fail"),
               ("one-off in PAT", "fail")),
        stats=(("P/E reported", "35.1x"), ("P/E normalised", "~68–89x"), ("D/E", "4.98"),
               ("borrowings", "1,207→4,121 Cr"), ("one-off in PAT", "₹105 Cr"), ("beds", "78,542")),
        note=(
            "Student housing plus K-12 schools — a good business (Value Research: \"good "
            "business, complicated issue\") inside an issue that is not. FY26 PAT of 174 Cr "
            "includes a ₹105 Cr one-time gain, so the real multiple is ~68x rather than 35x; "
            "borrowings went 1,207→4,121 Cr in a single year; and of the ₹2,100 Cr raised, "
            "₹1,100 Cr goes to the sponsor's Singapore entities to buy sixteen private school "
            "companies, with ₹750 Cr to debt. JM, IIFL and Morgan Stanley placed ₹945 Cr with "
            "anchors. Sushil and Ventura say Subscribe. Interesting below ~₹270 once the debt "
            "reduction is real; not at 362."
        ),
    ),
    IPO(
        name="AceVector (Snapdeal)", call="AVOID", tone="fail",
        dates="25–29 Sep", band="₹32", size="₹420 Cr", split="68% fresh / 32% OFS",
        gmp="₹0", gmp_pct=0.0, expected="~−7%",
        apply_as="—", horizon="—",
        book="anchor 24 Sep · SoftBank and Nexus selling",
        flags=(("loss-making", "fail"), ("zero GMP", "fail"), ("negative RoNW", "fail")),
        stats=(("FY26 revenue", "₹510 Cr (+29%)"), ("FY26 loss", "₹46–61 Cr"),
               ("valuation", "₹1,741 Cr"), ("EBITDA", "negative")),
        note=(
            "Snapdeal, Unicommerce and Stellaro Brands under one roof. The loss narrowed — FY25 "
            "126 Cr to FY26 46 Cr on the company's figures — but EBITDA is still negative, RoNW "
            "negative, and SoftBank's Starfish is selling up to 27.6M shares alongside Nexus. "
            "Zero grey-market premium, and our own base rate for a zero-GMP listing is −6.6% "
            "with only 29% of them listing positive. Nothing here to price a listing trade on."
        ),
    ),
]

# ── 24 September ────────────────────────────────────────────────────────────
# A refresh, not a rewrite. Eleven of thirteen were called yesterday; what
# changed overnight is the exchange book on the four issues closing tomorrow
# and the GMP on almost everything. Two names are new.

IPOS_2026_09_24 = [
    IPO(
        name="Adroit Industries", call="APPLIED — SELL ALL", tone="warn",
        dates="23–25 Sep (closes tomorrow)", band="₹134", size="₹151 Cr",
        split="88% fresh / 12% OFS",
        gmp="₹34", gmp_pct=25.4, expected="~+23%",
        apply_as="sHNI ₹2–10L (applied 23 Sep)",
        horizon="Sell the whole allotment at the open",
        book="day 2: 5.18x · retail 7.24x · HNI 7.2x · QIB 0.05x",
        flags=(("the flip condition fired", "fail"), ("QIB 0.05x on day 2", "fail"),
               ("retail 7.24x", "warn")),
        stats=(("QIB", "0.05x"), ("retail", "7.24x"), ("HNI", "7.2x"),
               ("overall", "5.18x"), ("GMP", "unchanged ₹34"), ("closes", "tomorrow")),
        note=(
            "<b>Yesterday's page wrote the condition down and today it is firing.</b> The note "
            "read: <em>QIB under 1x at Friday's close with retail above 5x is the weak-listing "
            "pattern — sell the whole allotment at the open.</em> On day 2 QIB is "
            "<b>0.05x</b> against retail <b>7.24x</b> and HNI <b>7.2x</b>. Institutions are "
            "absent and the book is being filled entirely by individuals, which is the shape "
            "that lists well and then fades. QIB lines do fill on the final day, so the "
            "condition is not formally met until tomorrow's close — but 0.05x with one session "
            "left is not a line that reaches 5x, and the horizon changes now rather than after "
            "the fact. The business case is unchanged and still good: 27.7% EBITDA margin "
            "against 11–16% for the peers, 88% fresh into capex. <b>This is a listing trade, "
            "not a holding.</b> The tranche-hold is off."
        ),
    ),
    IPO(
        name="Moneyview", call="APPLY", tone="pass",
        dates="24–28 Sep (opened today)", band="₹34", size="—",
        split="—",
        gmp="₹14", gmp_pct=41.2, expected="~+39%",
        apply_as="HNI — applied 24 Sep",
        horizon="Sell 70% on listing; hold 30% only on clean Q2 credit costs",
        book="opened today · GMP up from ₹11 (+32.4%) to ₹14",
        flags=(("best of the board", "pass"), ("GMP rising", "pass"),
               ("applied, HNI", "pass")),
        stats=(("GMP", "₹14"), ("was", "₹11 yesterday"), ("GMP %", "+41.2%"),
               ("expected", "~+39%"), ("status", "open today"), ("closes", "28 Sep")),
        note=(
            "<b>Applied 24 September, HNI.</b> The strongest grey market on the board and it "
            "strengthened overnight, ₹11 to ₹14, 32.4% to 41.2% — the only issue here whose "
            "expected listing clears +30% after the overstatement is taken off. Call and "
            "horizon unchanged from yesterday. The hold condition is still the credit-cost "
            "line in Q2 rather than the listing pop: a lender's listing gain tells you nothing "
            "about its book, and 30% of the allotment is the most that should ride on a "
            "quarter nobody has seen yet. "
            "<b>What to watch before Monday's close, and it is the Adroit lesson:</b> the QIB "
            "line. Adroit was applied for on the same reasoning and is closing at 0.05x QIB "
            "against 7.24x retail. If Moneyview's book takes the same shape — retail far "
            "ahead, institutions absent — the 30% hold comes off and the whole allotment is "
            "sold at the open."
        ),
    ),
    IPO(
        name="Orient Cables", call="APPLY", tone="pass",
        dates="25–29 Sep", band="₹272", size="—", split="—",
        gmp="₹45", gmp_pct=16.5, expected="~+14%",
        apply_as="Retail 1 lot; sHNI — the ₹30 condition is met",
        horizon="Sell half on listing, hold half",
        book="anchor 24 Sep · retail ₹193 Cr · GMP up from ₹34",
        flags=(("sHNI condition met", "pass"), ("GMP up 32%", "pass")),
        stats=(("GMP", "₹45"), ("was", "₹34"), ("GMP %", "+16.5%"),
               ("expected", "~+14%"), ("retail slice", "₹193 Cr"), ("opens", "tomorrow")),
        note=(
            "Yesterday's call carried a condition: <em>sHNI if GMP ≥ ₹30 on day 3</em>. It is "
            "₹45, up from ₹34, so the condition is met before the issue has even opened. "
            "Retail slice of ₹193 Cr is large enough that the odds do not collapse at a high "
            "multiple, which is the reason this is a better sHNI candidate than a ₹150 Cr "
            "issue at the same subscription."
        ),
    ),
    IPO(
        name="A-One Steels", call="APPLY, small", tone="pass",
        dates="24–28 Sep (opened today)", band="₹405", size="—", split="—",
        gmp="₹55", gmp_pct=13.6, expected="~+11%",
        apply_as="Retail 1 lot only",
        horizon="Listing-day sell, no hold",
        book="opened today · anchor 23 Sep, no names published",
        flags=(("GMP up", "pass"), ("anchors unnamed", "warn")),
        stats=(("GMP", "₹55"), ("was", "₹50"), ("GMP %", "+13.6%"),
               ("expected", "~+11%"), ("status", "open today"), ("closes", "28 Sep")),
        note=(
            "Unchanged call. GMP firmed from ₹50 to ₹55 but the percentage barely moved, 12.3% "
            "to 13.6%, because the band is high. The anchor book still has no published names, "
            "which is why this stays retail-only and does not get an sHNI cheque."
        ),
    ),
    IPO(
        name="German Green Steel", call="SKIP — watch after listing", tone="warn",
        dates="25–29 Sep", band="₹139", size="—", split="—",
        gmp="₹24", gmp_pct=17.3, expected="~+15%",
        apply_as="—",
        horizon="Buy post-listing only at or below book, if steel holds",
        book="anchor 24 Sep · Systematix, IIFL, CLSA · GMP up from ₹15",
        flags=(("GMP up 60%", "warn"), ("still a skip", "warn")),
        stats=(("GMP", "₹24"), ("was", "₹15"), ("GMP %", "+17.3%"),
               ("expected", "~+15%"), ("anchor", "24 Sep"), ("opens", "tomorrow")),
        note=(
            "The largest overnight GMP move on the board, ₹15 to ₹24, and the call does not "
            "change on that alone. <b>A grey-market quote is not a reason to apply to an issue "
            "skipped on its fundamentals</b> — it is the half of the evidence with no print "
            "behind it. What would change the call is the anchor list published today: domestic "
            "mutual funds rather than a row of small AIFs."
        ),
    ),
    IPO(
        name="ArMee Infotech", call="SKIP", tone="fail",
        dates="23–25 Sep (closes tomorrow)", band="₹375", size="—", split="—",
        gmp="₹55", gmp_pct=14.7, expected="~+12%",
        apply_as="—", horizon="—",
        book="day 2: 0.53x · QIB 0.93x · HNI 0.39x · retail 0.5x",
        flags=(("book under 1x", "fail"), ("GMP rising anyway", "warn"),
               ("retail quota 52.5%", "fail")),
        stats=(("overall", "0.53x"), ("QIB", "0.93x"), ("retail", "0.5x"),
               ("GMP", "₹55 (was ₹46)"), ("GMP %", "+14.7%"), ("closes", "tomorrow")),
        note=(
            "<b>The clearest divergence on the board and the reason the two columns are both "
            "printed.</b> The grey market marked this up from ₹46 to ₹55 overnight while the "
            "exchange book sits at <b>0.53x with one day left</b> — retail itself only 0.5x "
            "against a quota that is 52.5% retail. One of those numbers is an unregulated "
            "quote with no print behind it and the other is the exchange's own record of money "
            "actually bid. The skip stands on the verifiable half."
        ),
    ),
    IPO(
        name="Swastika Infra", call="SKIP — revisit", tone="warn",
        dates="23–25 Sep (closes tomorrow)", band="₹185", size="—", split="—",
        gmp="₹8", gmp_pct=4.3, expected="~+2%",
        apply_as="—", horizon="Post-listing study if the order book converts",
        book="day 2: 0.96x · QIB 0.69x · HNI 1.9x · retail 0.71x",
        flags=(("not yet 1x", "warn"),),
        stats=(("overall", "0.96x"), ("QIB", "0.69x"), ("HNI", "1.9x"),
               ("retail", "0.71x"), ("GMP", "₹8 unchanged"), ("closes", "tomorrow")),
        note=(
            "Unchanged on every number that matters — GMP still ₹8, book still under 1x on the "
            "second day with only the HNI line above water. Expected listing of about +2% does "
            "not pay for the application."
        ),
    ),
    IPO(
        name="Elevate Campuses", call="AVOID at IPO", tone="fail",
        dates="23–25 Sep (closes tomorrow)", band="₹362", size="—", split="—",
        gmp="₹3", gmp_pct=0.8, expected="~−2%",
        apply_as="—",
        horizon="Revisit below ~₹270 with verified debt reduction",
        book="day 2: 0.2x · QIB 0.18x · HNI 0.3x · retail 0.13x",
        flags=(("0.2x on day 2", "fail"), ("GMP collapsing", "fail"),
               ("₹1,100 Cr to sponsor's Singapore entities", "fail")),
        stats=(("overall", "0.2x"), ("QIB", "0.18x"), ("retail", "0.13x"),
               ("GMP", "₹3 (was ₹5)"), ("GMP %", "+0.8%"), ("expected", "~−2%")),
        note=(
            "The avoid is being confirmed by the tape. GMP fell from ₹5 to ₹3 and the book is "
            "<b>0.2x with one day left</b>, retail at 0.13x against a retail quota of only 10%. "
            "At a GMP of 0.8% the expected listing is already negative once the 2.6-point "
            "overstatement is taken off. The structural objection is unchanged and is the real "
            "one: ₹1,100 Cr of proceeds to the sponsor's Singapore entities."
        ),
    ),
    IPO(
        name="Varmora Granito", call="AVOID", tone="fail",
        dates="22–24 Sep (closes today)", band="₹148", size="—", split="—",
        gmp="₹0", gmp_pct=0.0, expected="~−6.6%",
        apply_as="—", horizon="—",
        book="final day: 0.27x · QIB 0.11x · HNI 0.17x · retail 0.4x",
        flags=(("GMP now zero", "fail"), ("0.27x on the final day", "fail")),
        stats=(("overall", "0.27x"), ("QIB", "0.11x"), ("retail", "0.4x"),
               ("GMP", "₹0 (was ₹5)"), ("expected", "~−6.6%"), ("closes", "today")),
        note=(
            "Closes today at <b>0.27x</b> with the grey market at zero, down from ₹5 yesterday. "
            "A zero GMP has averaged <b>−6.6%</b> on listing and listed positive 29% of the "
            "time across the 295 listings behind the lens. An issue that cannot fill its own "
            "book is the cleanest avoid on this page, and the valuation objection — 61x against "
            "Kajaria's 40x on half the RoE — was there before the book confirmed it."
        ),
    ),
    IPO(
        name="Runwal Enterprises", call="SKIP", tone="warn",
        dates="25–29 Sep", band="₹305", size="—", split="—",
        gmp="₹18", gmp_pct=5.9, expected="~+3%",
        apply_as="—", horizon="—",
        book="ICICI Sec + Jefferies · GMP unchanged",
        flags=(("unchanged", "warn"),),
        stats=(("GMP", "₹18"), ("GMP %", "+5.9%"), ("expected", "~+3%"),
               ("band", "₹305"), ("opens", "tomorrow"), ("change", "none")),
        note="Nothing moved overnight. Expected listing of about +3% does not pay for the lock-up.",
    ),
    IPO(
        name="AceVector (Snapdeal)", call="AVOID", tone="fail",
        dates="25–29 Sep", band="₹32", size="—", split="—",
        gmp="₹0", gmp_pct=0.0, expected="~−6.6%",
        apply_as="—", horizon="—",
        book="anchor 24 Sep · SoftBank and Nexus selling",
        flags=(("zero GMP", "fail"), ("sponsors exiting", "fail")),
        stats=(("GMP", "₹0"), ("expected", "~−6.6%"), ("band", "₹32"),
               ("opens", "tomorrow"), ("sellers", "SoftBank, Nexus"), ("change", "none")),
        note=(
            "Still zero in the grey market on the day before it opens. The objection is "
            "unchanged: SoftBank and Nexus are selling, which makes the issue an exit rather "
            "than a raise."
        ),
    ),
    IPO(
        name="SRIT India", call="AVOID", tone="fail",
        dates="28–30 Sep", band="₹123–130", size="₹218 Cr", split="100% fresh / no OFS",
        gmp="₹12", gmp_pct=9.2, expected="~+6.6%",
        apply_as="—",
        horizon="Revisit only after the Blossom transaction is closed and disclosed",
        book="new today · anchor bidding 25 Sep · sole BRLM Choice Capital",
        flags=(("related-party ₹140 Cr", "fail"), ("operating cash flow negative", "fail"),
               ("RoE 38.8% → 16.0%", "fail"), ("100% fresh, no OFS", "pass")),
        stats=(("P/E post", "19.3–24.8x"), ("RoE FY26", "30.2%"), ("RoE H1", "16.0%"),
               ("D/E", "0.23"), ("govt revenue", "~92%"), ("OCF FY25", "−₹58.9 Cr")),
        note=(
            "Bengaluru IT services for government — e-governance, healthcare, telecom; CMMI "
            "Level 5; ₹1,280 Cr order book at 3.3x revenue. The structure is the good part: "
            "<b>100% fresh, no OFS</b>, promoter 84.9% → 62.7%, D/E 0.23. "
            "<b>Three things override it.</b> First, the RHP discloses a conditional binding "
            "term sheet to buy 50% of Blossom Multi Specialty Hospital at an indicative ₹280 Cr "
            "valuation — <b>₹140 Cr for the stake, against a ₹218 Cr raise</b> — plus an "
            "inter-corporate deposit of up to ₹50 Cr, and the seller, Dr Chandan Dash, has been "
            "a non-executive director of SRIT since 10 August 2026 while the relationship is "
            "recorded as “Nil”. Whether IPO money funds it is not stated, and about 35% of "
            "gross proceeds is earmarked for <em>unidentified</em> acquisitions. Second, "
            "<b>profit is not becoming cash</b>: operating cash flow −₹58.9 Cr in FY25 and "
            "−₹17.5 Cr in H1 FY26 while PAT rose to ₹43.3 Cr, with cash down 69% to ₹7.6 Cr. "
            "Third, the headline 30% RoE is backward-looking — H1 FY26 is 16.0% RoE and 16.4% "
            "RoCE, and sub-contracting has gone from 61% of revenue to 73%. At 24.8x trailing "
            "against Mastek's 17.5x with worse margins and worse conversion, a +6.6% expected "
            "listing is not payment for any of that."
        ),
    ),
    IPO(
        name="Shah Investor’s Home", call="AVOID", tone="fail",
        dates="28–30 Sep", band="₹159–167", size="₹90 Cr", split="100% fresh / no OFS",
        gmp="₹10", gmp_pct=6.0, expected="~+3.4%",
        apply_as="—",
        horizon="Revisit only on two quarters of recovering revenue",
        book="new today · anchor 25–26 Sep · sole BRLM Beeline Capital",
        flags=(("PAT −44% into the issue", "fail"), ("27x on a falling base", "fail"),
               ("SME-heavy banker on a mainboard issue", "warn"), ("no OFS", "pass")),
        stats=(("P/E post", "26.9x"), ("revenue FY26", "−23%"), ("PAT FY26", "−44%"),
               ("RoE", "7.6% (was 14.7%)"), ("OCF FY26", "−₹19.7 Cr"), ("D/E", "0.10")),
        note=(
            "Gujarat and Maharashtra retail broker, 1994, eleven branches, ~38,000 active "
            "clients. No OFS, promoters stay at 62.8%, D/E 0.10, and a genuinely thick 30% "
            "EBITDA margin even in a bad year. <b>The problem is the direction of travel.</b> "
            "Revenue fell 23% and PAT fell 44% into the issue — ₹23.4 Cr to ₹13.1 Cr — RoE "
            "halved from 14.7% to 7.6%, and it is priced at <b>26.9x post-issue on that "
            "declining base</b>. Operating cash flow is −₹19.7 Cr against ~₹13 Cr of reported "
            "profit, and borrowings tripled to ₹18.5 Cr while the issue asks for ₹60 Cr of "
            "working capital. The sole banker, Beeline Capital, is predominantly an SME-IPO "
            "house with no retrievable mainboard listing record. A broking cycle turns and this "
            "may well be a trough — but the trough is being sold at a peak multiple, and a GMP "
            "of 6% that was zero yesterday is not conviction."
        ),
    ),
]

LEAD_24 = (
    "Thirteen mainboard issues on the board, read at 10:30 IST on 24 September across "
    "Trendlyne, Chittorgarh, the IPO Watch and InvestorGain GMP boards, and the exchange's own "
    "subscription figures. <strong>This is a refresh: eleven of the thirteen were called "
    "yesterday and the calls are carried forward unless a number moved.</strong> What moved: "
    "the exchange book on the four issues closing tomorrow, and the GMP on almost everything. "
    "<strong>Expected listing is the GMP percentage less 2.6 points</strong> — the "
    "overstatement <code>backtest_gmp</code> measured over 295 listings (r = 0.87); a zero GMP "
    "has averaged −6.6% and listed positive 29% of the time. <em>Applied: Adroit Industries sHNI ₹2L+ on 23 Sep; "
    "Moneyview HNI on 24 Sep. Held: NSE allotment, 120 shares at ₹1,785, listed today at "
    "₹1,862 and being held.</em>"
)

FOOTNOTE_24 = (
    "Two columns are printed for every open issue because they disagree today. The grey market "
    "marked ArMee up 20% overnight while its exchange book sits at 0.53x with a day to go, and "
    "marked German Green Steel up 60% on an issue that has not opened. GMP predicts the listing "
    "well in aggregate and has no print behind any single quote; the subscription figures are "
    "the exchange's own. Where they conflict, the call follows the book. Before tomorrow's "
    "close: Adroit's QIB line, and whether Varmora completes at all."
)

LEAD = (
    "Eleven mainboard issues open or opening, read at 11:45 and deepened at 12:45 IST on "
    "23 September across Trendlyne (detail pages and the brokerage-report list), Chittorgarh, "
    "the IPO Watch GMP board, Value Research, anchor circulars and independent reviews. "
    "<strong>Expected listing is the GMP percentage less 2.6 points</strong> — the "
    "overstatement <code>backtest_gmp</code> measured over 295 listings (r = 0.87); a zero GMP "
    "has averaged −6.6% and listed positive 29% of the time. <strong>Apply as:</strong> retail "
    "is one ₹15k lot by lottery; sHNI is ₹2–10L, one-third of the 15% NII quota, a lottery of "
    "one ₹2L lot; bHNI is above ₹10L and proportionate — and odds scale with the size of the "
    "category's book, so a ₹1,000 Cr issue beats a ₹150 Cr one at the same oversubscription. "
    "None of this touches the ₹60L. <em>Applied 23 Sep: Adroit Industries, HNI ₹2L+.</em>"
)

FOOTNOTE = (
    "Brokerage “Subscribe” notes — Ventura in particular — cover nearly every issue and are not "
    "a signal; a Neutral or an Avoid from any house is. Watch before the books close: Adroit’s "
    "QIB line on Friday, Moneyview’s and Orient’s anchor lists, and whether Varmora reaches 1x."
)



LEAD_25 = (
    "Twelve mainboard issues, read at 01:30 and <b>refreshed at 10:30 IST</b> on 25 September off "
    "the service's own "
    "board — which is working again: ipowatch dropped a column from its table overnight, "
    "every row stopped parsing, and <code>show_ipos</code> reported the board as "
    "<em>missing</em> rather than broken. Six issues were open at the time. The parser was "
    "fixed and deployed before this page was written; the subscription figures below are the "
    "exchange's own, at each issue's most recent close, and they are labelled by which day "
    "that was. Expected listing is the GMP percentage less 2.6 points — the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r = 0.87); a zero GMP has averaged "
    "&minus;6.6% and listed positive 29% of the time. Applied: Adroit Industries sHNI on "
    "23 Sep; Moneyview HNI on 24 Sep; <b>Orient Cables on 25 Sep</b>. "
    "Held: NSE, 120 shares at &#8377;1,785."
)

FOOTNOTE_25 = (
    "<b>Three issues close today</b> (Adroit, Swastika, Elevate, ArMee) and four open "
    "(Orient Cables, German Green Steel, Runwal, AceVector). The only decisions that need "
    "making before the open are the four that open; everything closing is already applied "
    "for or already refused. Subscription figures are each issue's latest exchange close, "
    "not intraday — at 01:30 IST there is no day-3 book for anything."
)

IPOS_2026_09_25 = [
    IPO(
        name="Adroit Industries", call="APPLIED — SELL AT OPEN", tone="warn",
        dates="23–25 Sep (closes today)", band="₹134", size="₹151 Cr",
        split="88% fresh / 12% OFS",
        gmp="₹34", gmp_pct=25.4, expected="~+23%",
        apply_as="sHNI ₹2–10L (applied 23 Sep)",
        horizon="Sell the whole allotment at the open",
        book="day 2 close: 18.07x · retail 23.43x · HNI 27.21x · QIB 1.82x",
        flags=(("yesterday's flip condition did NOT fire", "pass"),
               ("QIB came in at day-2 close", "pass"),
               ("27x HNI — expect a token allotment", "warn")),
        stats=(("overall", "18.07x"), ("QIB", "1.82x"), ("HNI", "27.21x"),
               ("retail", "23.43x"), ("GMP", "unchanged ₹34"), ("closes", "today")),
        note=(
            "<b>Yesterday's page was reading an intraday book and drew the wrong conclusion "
            "from it.</b> It saw QIB at 0.05x at 10:30 on day 2, declared the weak-listing "
            "pattern, and called for selling the whole allotment. By the day-2 close QIB was "
            "<b>1.82x</b> — institutions bid late, which is the ordinary shape of a book and "
            "not a surprise. The stated condition was <em>QIB under 1x at Friday's close with "
            "retail above 5x</em>. QIB is already above 1x with a day still to run, so the "
            "condition has not fired and will not unless bids are withdrawn. "
            "<b>The call lands in the same place for a different reason.</b> The original note "
            "said hold a tranche only if QIB clears 5x; at 1.82x it does not, so the whole "
            "allotment is sold at the open. At 27x on the HNI book the allotment will be a "
            "token in any case. What this costs if I am wrong: the upside beyond the first "
            "print on a small position."
        ),
    ),
    IPO(
        name="Moneyview", call="APPLIED — HOLD THE APPLICATION", tone="pass",
        dates="24–28 Sep", band="₹34", size="₹1,092 Cr",
        split="₹750 Cr fresh / ₹342 Cr OFS",
        gmp="₹14", gmp_pct=41.2, expected="~+39%",
        apply_as="HNI — applied 24 Sep",
        horizon="Sell 70% on listing; hold 30% only on clean Q2 credit costs",
        book="day 1 close: 1.44x · retail 1.79x · HNI 2.43x · QIB 0.05x",
        flags=(("best GMP on the board", "pass"), ("QIB 0.05x after day 1", "warn"),
               ("three days still to run", "pass")),
        stats=(("overall", "1.44x"), ("QIB", "0.05x"), ("HNI", "2.43x"),
               ("retail", "1.79x"), ("GMP", "₹14, from ₹5 on 21 Sep"), ("closes", "Mon 28 Sep")),
        note=(
            "GMP has climbed ₹5 → ₹11 → ₹14 across three sessions and is the highest on the "
            "board at +41.2%; the lens puts the listing near +39%. <b>QIB at 0.05x after day 1 "
            "is not the warning it looks like</b> — Adroit's book above is the same story one "
            "day further on, 0.05x intraday to 1.82x at the close. The number that matters is "
            "QIB at Monday's close, not today's. "
            "The application stands. The exit plan is unchanged: 70% at the listing print, and "
            "the remaining 30% held only if Q2 credit costs come in clean — a lender's listing "
            "premium is worth nothing if the book is deteriorating underneath it."
        ),
    ),
    IPO(
        name="Orient Cables", call="APPLIED — SELL HALF ON LISTING", tone="pass",
        dates="25–29 Sep (opens today)", band="₹272", size="₹528 Cr", split="fresh + OFS",
        gmp="₹113", gmp_pct=41.5, expected="~+39%",
        apply_as="applied 25 Sep",
        horizon="Sell half on listing, hold half",
        book="opens today · anchor book taken 24 Sep",
        flags=(("applied", "pass"), ("GMP ₹45 → ₹60 → ₹113 in a day", "pass"),
               ("joint best on the board", "pass")),
        stats=(("GMP 01:30", "₹60 (+22.1%)"), ("GMP 10:30", "₹113 (+41.5%)"),
               ("lot", "55 shares"), ("min retail", "₹14,960"),
               ("listing", "5 Oct"), ("band", "₹258–272")),
        note=(
            "Two decades in networking cable and passive equipment, and the grey market has "
            "<b>doubled into its own opening</b>: ₹45 at yesterday\u2019s read, ₹60 at 01:30 this "
            "morning, <b>₹113 by 10:30</b> — +41.5%, level with Moneyview at the top of the board "
            "and the largest single move on it. "
            "The call was APPLY yesterday on a weaker number and is unchanged, which is the "
            "point: the case was made before the premium moved, so the move is confirmation "
            "rather than the reason. "
            "<b>Applied on 25 September.</b> Half sold at the listing print, half held — the "
            "cable and wire sector has been the one place a listing premium has extended rather "
            "than faded this quarter. "
            "<b>What to watch before the book closes on the 29th:</b> QIB at the final close. "
            "Adroit is this week\u2019s lesson in both directions — QIB read 0.05x intraday on day "
            "2 and closed that same day at 1.82x, and Varmora finished at 3.16x against the 0.27x "
            "an intraday read had shown. An intraday subscription figure is not a book. "
            "<b>What would flip the hold half:</b> QIB under 1x at the 29 September close with "
            "retail above 5x — the weak-listing pattern — in which case the whole allotment goes "
            "at the open."
        ),
    ),
    IPO(
        name="German Green Steel", call="SKIP — watch after listing", tone="warn",
        dates="25–29 Sep (opens today)", band="₹139", size="₹304 Cr",
        split="₹290 Cr fresh / ₹14 Cr OFS",
        gmp="₹28", gmp_pct=20.1, expected="~+17%",
        apply_as="—",
        horizon="Buy post-listing only at or below the issue price, if steel holds",
        book="opens today · Systematix, IIFL, CLSA",
        flags=(("GMP up ₹24 → ₹28", "pass"), ("commodity input risk", "warn"),
               ("TMT bars — a price taker", "warn")),
        stats=(("GMP yesterday", "₹24 (+17.3%)"), ("GMP today", "₹28 (+20.1%)"),
               ("FY26 revenue", "+11%"), ("FY26 PAT", "+33%"),
               ("lot", "107 shares"), ("min retail", "₹14,873")),
        note=(
            "The GMP improved and the call does not, which is the discipline this page is for. "
            "<b>A grey-market quote is not a reason; it is a number the call has to survive.</b> "
            "The refusal was never about the premium — it is a TMT-bar maker in Gujarat, a price "
            "taker on iron ore and coal with FY26 revenue up 11% against PAT up 33%, which is "
            "margin expansion on input costs rather than on volume, and input costs revert. "
            "+20.1% would list well and might. Skipped anyway, and the condition for revisiting "
            "is written down: at or below ₹139 after listing, with steel prices holding."
        ),
    ),
    IPO(
        name="Runwal Enterprises", call="SKIP", tone="warn",
        dates="25–29 Sep (opens today)", band="₹305", size="₹500 Cr", split="100% fresh",
        gmp="₹30", gmp_pct=9.8, expected="~+7%",
        apply_as="—", horizon="—",
        book="opens today · ICICI Sec + Jefferies",
        flags=(("GMP doubled ₹18 → ₹35", "warn"), ("₹325 Cr of ₹500 Cr to debt", "fail")),
        stats=(("GMP 01:30", "₹35 (+11.5%)"), ("GMP 10:30", "₹30 (+9.8%)"),
               ("to debt repayment", "₹325 Cr"), ("to growth", "₹175 Cr"),
               ("lot", "49 shares"), ("listing", "5 Oct")),
        note=(
            "The premium doubled overnight and the case did not change with it. Mumbai real "
            "estate, founded 1978, all-fresh issue — and <b>₹325 Cr of the ₹500 Cr goes to "
            "repaying debt</b>, so under two fifths of what is raised reaches the business. "
            "That is a balance-sheet repair priced as a growth issue. "
            "A GMP that moves from +5.9% to +11.5% the night before an issue opens, with no "
            "news between, is the part of the grey market the 2.6-point haircut exists for. "
            "Skipped."
        ),
    ),
    IPO(
        name="AceVector (Snapdeal)", call="AVOID", tone="fail",
        dates="25–29 Sep (opens today)", band="₹32", size="₹420 Cr",
        split="₹287 Cr fresh / OFS 4.16 Cr shares",
        gmp="₹2", gmp_pct=6.2, expected="~+4%",
        apply_as="—", horizon="—",
        book="opens today · SoftBank and Nexus selling",
        flags=(("trackers disagree: ₹0 to ₹1.5", "fail"), ("negative EBITDA", "fail"),
               ("negative RoNW", "fail")),
        stats=(("GMP, our board", "₹1.5 (+4.7%)"), ("GMP, InvestorGain", "₹0 (0.0%)"),
               ("EBITDA", "negative"), ("RoNW", "negative"),
               ("lot", "468 shares"), ("band", "₹30–32")),
        note=(
            "<b>The two GMP boards disagree, and both readings are bad.</b> Ours has ₹1.5; "
            "InvestorGain had ₹0 on 24 September. A zero GMP has averaged \u22126.6% at "
            "listing across the 295 issues measured and listed positive 29% of the time, and "
            "+4.7% is inside the 2.6-point overstatement — neither number is a case. "
            "Losses are narrowing and revenue is growing, but EBITDA and RoNW are both still "
            "negative and the selling shareholders are SoftBank and Nexus. An OFS by the "
            "people who know the asset best, into a grey market that will not bid, is two "
            "independent opinions pointing the same way. Avoided."
        ),
    ),
    IPO(
        name="A-One Steels", call="SKIP — downgraded from apply", tone="fail",
        dates="24–28 Sep", band="₹405", size="₹650 Cr", split="fresh + OFS",
        gmp="₹49", gmp_pct=12.1, expected="~+10%",
        apply_as="— (was: retail 1 lot)", horizon="—",
        book="day 1 close: 0.58x · retail 0.77x · HNI 0.77x · QIB 0.09x",
        flags=(("GMP fell ₹55 → ₹45", "fail"), ("book under 1x after day 1", "fail"),
               ("every category under 1x", "fail")),
        stats=(("overall", "0.58x"), ("QIB", "0.09x"), ("HNI", "0.77x"),
               ("retail", "0.77x"), ("GMP yesterday", "₹55 (+13.6%)"),
               ("GMP today", "₹45 (+11.1%)")),
        note=(
            "<b>Downgraded.</b> Yesterday's call was apply, one retail lot, on a +13.6% "
            "premium. Two things moved against it overnight and they point the same way: the "
            "GMP fell to +11.1%, and the day-1 book closed at 0.58x with <em>no</em> category "
            "above 1x — retail 0.77x, HNI 0.77x, QIB 0.09x. "
            "An issue nobody has to compete for is an issue where the allotment is certain and "
            "worth having for exactly that reason — which is the trap. Full allotment on a "
            "book that will not fill, in the same steel complex as the issue skipped above, "
            "against a premium that is falling rather than rising. There are two apply-worthy "
            "issues on this board; this is not the third."
        ),
    ),
    IPO(
        name="ArMee Infotech", call="SKIP — GMP collapsed", tone="fail",
        dates="23–25 Sep (closes today)", band="₹375", size="₹235 Cr", split="fresh + OFS",
        gmp="₹20", gmp_pct=5.3, expected="~+3%",
        apply_as="—", horizon="—",
        book="day 2 close: 1.17x · retail 1.35x · HNI 0.86x · QIB 0.94x",
        flags=(("GMP fell ₹55 → ₹20 in a day", "fail"), ("−64% on the premium", "fail")),
        stats=(("GMP yesterday", "₹55 (+14.7%)"), ("GMP today", "₹20 (+5.3%)"),
               ("overall", "1.17x"), ("QIB", "0.94x"), ("HNI", "0.86x"), ("retail", "1.35x")),
        note=(
            "Skipped yesterday at +14.7% and the grey market has since agreed, hard: ₹55 to "
            "₹20, a 64% fall in the premium in a single session, with the book scraping past "
            "1x only on retail. <b>This is what the skip was for.</b> Nothing to do — it is "
            "recorded because a call that is later confirmed by the price is worth as much to "
            "read back as one that is contradicted, and only one of the two gets written down "
            "if the page is only updated when something is bought."
        ),
    ),
    IPO(
        name="Swastika Infra", call="SKIP", tone="warn",
        dates="23–25 Sep (closes today)", band="₹185", size="₹98 Cr", split="fresh",
        gmp="₹8", gmp_pct=4.3, expected="~+2%",
        apply_as="—", horizon="Post-listing study if the order book converts",
        book="day 2 close: 1.64x · retail 1.59x · HNI 2.58x · QIB 1.00x",
        flags=(("book improved 0.96x → 1.64x", "pass"), ("GMP flat at ₹8", "warn")),
        stats=(("overall", "1.64x"), ("QIB", "1.00x"), ("HNI", "2.58x"),
               ("retail", "1.59x"), ("GMP", "unchanged ₹8"), ("closes", "today")),
        note=(
            "The book filled out on day 2 — 0.96x to 1.64x, with QIB reaching exactly 1x — and "
            "the grey market did not move at all. +4.3% is +1.7% after the haircut, which is "
            "inside the noise of a listing print. The skip stands on arithmetic rather than on "
            "any view of the company: there is no premium here to sell into."
        ),
    ),
    IPO(
        name="Elevate Campuses", call="AVOID", tone="fail",
        dates="23–25 Sep (closes today)", band="₹362", size="₹362 Cr", split="fresh + OFS",
        gmp="₹3", gmp_pct=0.8, expected="~−2%",
        apply_as="—", horizon="Revisit below ~₹270 with verified debt reduction",
        book="day 2 close: 0.23x · retail 0.23x · HNI 0.33x · QIB 0.18x",
        flags=(("0.23x on the final eve", "fail"), ("every category under 0.35x", "fail"),
               ("expected listing negative", "fail")),
        stats=(("overall", "0.23x"), ("QIB", "0.18x"), ("HNI", "0.33x"),
               ("retail", "0.23x"), ("GMP", "₹3 (+0.8%)"), ("expected", "−1.8%")),
        note=(
            "Closing today with under a quarter of the book taken and a premium of +0.8%, "
            "which the lens turns negative. An issue this far short of its own book normally "
            "extends or withdraws; if it lists, it lists into no demand. Avoided at the IPO, "
            "and the revisit condition is unchanged — below about ₹270, with debt reduction "
            "that can be verified rather than promised."
        ),
    ),
    IPO(
        name="Varmora Granito", call="CLOSED — no action", tone="warn",
        dates="22–24 Sep (closed)", band="₹148", size="₹300 Cr", split="fresh + OFS",
        gmp="₹0", gmp_pct=0.0, expected="~−6.6%",
        apply_as="—", horizon="—",
        book="final: 1.58x · retail 1.00x · HNI 0.92x · QIB 3.16x",
        flags=(("QIB carried the book", "warn"), ("zero GMP into listing", "fail")),
        stats=(("overall", "1.58x"), ("QIB", "3.16x"), ("HNI", "0.92x"),
               ("retail", "1.00x"), ("GMP", "₹0"), ("base rate at zero GMP", "−6.6%")),
        note=(
            "Closed yesterday and avoided. Worth one line for the record: the <b>final</b> book "
            "was 1.58x on QIB at 3.16x, against the 0.27x this page quoted from an intraday "
            "read on its last morning. Institutions bid at the close — the same lesson Adroit "
            "taught at the top of this page, in the same week. An intraday subscription figure "
            "is not a book. The GMP stayed at zero regardless, which is where the avoid came "
            "from and where it stays: zero has averaged −6.6%."
        ),
    ),
    IPO(
        name="SRIT India", call="AVOID", tone="fail",
        dates="28–30 Sep", band="₹130", size="₹135 Cr", split="fresh + OFS",
        gmp="₹22", gmp_pct=16.9, expected="~+14%",
        apply_as="—", horizon="Revisit only after the Blossom transaction is closed and disclosed",
        book="anchor bidding 25 Sep · sole BRLM Choice Capital",
        flags=(("sole book-runner", "warn"), ("undisclosed related transaction", "fail")),
        stats=(("GMP 01:30", "₹13 (+10.0%)"), ("GMP 10:30", "₹22 (+16.9%)"),
               ("BRLM", "Choice Capital"), ("opens", "Mon 28 Sep")),
        note=(
            "Unchanged from yesterday and not decided today — it opens Monday. A sole "
            "book-runner and a related transaction that is referenced without being closed or "
            "disclosed. The premium went from +10.0% to <b>+16.9%</b> between 01:30 and 10:30 and "
            "the call does not move with it: the revisit condition is the transaction, not the "
            "premium. It opens Monday, so there is time for the disclosure to arrive."
        ),
    ),
    IPO(
        name="Shah Investor's Home", call="AVOID", tone="fail",
        dates="28–30 Sep", band="₹167", size="₹120 Cr", split="fresh + OFS",
        gmp="₹12", gmp_pct=7.2, expected="~+5%",
        apply_as="—", horizon="Revisit only on two quarters of recovering revenue",
        book="anchor 25–26 Sep · sole BRLM Beeline Capital",
        flags=(("sole book-runner", "warn"), ("revenue declining", "fail")),
        stats=(("GMP yesterday", "₹10 (+6.0%)"), ("GMP today", "₹12 (+7.2%)"),
               ("BRLM", "Beeline Capital"), ("opens", "Mon 28 Sep")),
        note=(
            "Unchanged, and opens Monday. A broking house coming to market on declining "
            "revenue with a sole book-runner; the premium has drifted up two rupees and "
            "changes nothing. Revisit on two quarters of recovery, not on a grey-market quote."
        ),
    ),
]


BY_DAY = {
    "2026-09-23": (IPOS_2026_09_23, LEAD, FOOTNOTE),
    "2026-09-24": (IPOS_2026_09_24, LEAD_24, FOOTNOTE_24),
    "2026-09-25": (IPOS_2026_09_25, LEAD_25, FOOTNOTE_25),
}


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-09-24"
    if day not in BY_DAY:
        print(f"no review written for {day}; known: {', '.join(sorted(BY_DAY))}")
        return 1
    issues, lead, footnote = BY_DAY[day]
    print(f"{day}: {len(issues)} issues")
    write(day, section(issues, lead, footnote))
    return 0


if __name__ == "__main__":
    sys.exit(main())
