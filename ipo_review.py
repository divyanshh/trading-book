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
from dataclasses import dataclass, field, replace
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



LEAD_26 = (
    "Ten mainboard issues, read on Saturday 26 September off the service's own board, "
    "with the fundamentals taken from each RHP. <strong>Monday is the decision day</strong>: "
    "Moneyview and A-One Steels close, SRIT India and Shah Investor's Home open. "
    "Expected listing is the GMP percentage less 2.6 points &mdash; the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87); a zero GMP has "
    "averaged &minus;6.6% and listed positive 29% of the time. "
    "<strong>Applied so far:</strong> Adroit Industries sHNI on 23 Sep (listed, sold); "
    "Moneyview HNI on 24 Sep; Orient Cables on 25 Sep. "
    "<strong>Held:</strong> NSE, 120 shares at &#8377;1,785 &mdash; still untracked and "
    "still without a stop."
)

FOOTNOTE_26 = (
    "Subscription figures are the exchange's own at Friday's close, so the two issues that "
    "opened on Thursday have had two days and the ones that opened Friday have had one. "
    "<strong>QIB reads low on almost everything and that is normal</strong> &mdash; "
    "institutions bid on the final day, so a QIB number taken before an issue closes says "
    "very little. It is the reason no call below rests on it. "
    "German Green Steel has a grey-market quote and no exchange book matched: the two "
    "sources name companies differently and a name is never guessed at."
)

IPOS_2026_09_26 = [
    IPO(
        name="Moneyview", call="APPLIED — HNI", tone="pass",
        dates="24–28 Sep (closes Monday)", band="₹32–34", size="₹1,092 Cr",
        split="₹750 Cr fresh / ₹342 Cr OFS",
        gmp="₹14", gmp_pct=41.2, expected="~+39%",
        apply_as="HNI (applied 24 Sep)",
        horizon="Sell at the open. The case is the discount, not the franchise.",
        book="Fri close: 6.01x · HNI 15.41x · retail 5.18x · QIB 0.25x",
        flags=(("best GMP on the board", "pass"), ("HNI 15.4x", "pass"),
               ("PAT flat on +43% revenue", "warn"), ("D/E 2.27x", "warn")),
        stats=(("P/E post", "8.61x"), ("RoE", "15.98%"), ("D/E", "2.27x"),
               ("FY26 revenue", "₹3,404 Cr"), ("FY26 PAT", "₹243 Cr"),
               ("retail min", "₹14,994"), ("sHNI min", "₹2.10L"), ("bHNI min", "₹10.05L")),
        note=(
            "The cheapest thing on the board at 8.6x, and the reason is visible in the "
            "accounts: revenue grew 43% to ₹3,404 Cr while profit went from ₹240 Cr to "
            "₹243 Cr. That is a lender buying growth with margin, funded at 2.27x debt to "
            "equity. It is priced for that. Fifteen times on the HNI book with a 41% GMP is "
            "the market agreeing the discount is too wide for a listing pop, and nothing "
            "more &mdash; hold this past the open and you own the margin question."
        ),
    ),
    IPO(
        name="SRIT India", call="APPLY — the pick of the new two", tone="pass",
        dates="28–30 Sep (opens Monday)", band="₹123–130", size="₹218 Cr",
        split="100% fresh, no OFS",
        gmp="₹32", gmp_pct=24.6, expected="~+22%",
        apply_as="Retail, and sHNI if the day-1 book clears 3x",
        horizon="Listing-day sell; a tranche can ride if QIB is 5x or better",
        book="opens Monday · anchors allotted, Abakkus among them",
        flags=(("no OFS — every rupee goes in", "pass"), ("RoE 30.2%", "pass"),
               ("21x post-issue", "pass"), ("₹218 Cr — small", "warn")),
        stats=(("P/E post", "20.97x"), ("RoE", "30.23%"), ("RoCE", "28.79%"),
               ("revenue CAGR", "28.8% FY24→26"), ("PAT CAGR", "22.0%"),
               ("FY26 revenue", "₹450 Cr"), ("FY26 PAT", "₹43.3 Cr"), ("lot", "115 sh")),
        note=(
            "The only issue here with no offer for sale: the whole ₹218 Cr goes into the "
            "company rather than to selling holders, which is the one structural signal in "
            "an IPO that cannot be dressed. Thirty percent return on equity at twenty-one "
            "times, growing revenue at a 29% CAGR and profit at 22% &mdash; profit growing "
            "slower than revenue is worth watching, but from these returns it is a "
            "quibble. Marquee anchors are allotted. Of everything opening this week this is "
            "the one worth the application."
        ),
    ),
    IPO(
        name="Orient Cables", call="APPLIED — hold to listing", tone="pass",
        dates="25–29 Sep (closes Tuesday)", band="₹258–272", size="₹552 Cr",
        split="₹320 Cr fresh / ₹232 Cr OFS",
        gmp="₹80", gmp_pct=29.4, expected="~+27%",
        apply_as="Retail (applied 25 Sep)",
        horizon="Sell at the open unless QIB finishes above 5x",
        book="Fri close: 1.96x · HNI 3.48x · retail 2.43x · QIB 0.01x",
        flags=(("RoE 25.8%", "pass"), ("GMP ₹80", "pass"),
               ("QIB 0.01x with one day left", "warn"), ("23.6x post-issue", "warn")),
        stats=(("P/E post", "23.61x"), ("RoE", "25.84%"), ("RoCE", "23.82%"),
               ("working capital", "~48 days"), ("market cap", "₹3,095 Cr"),
               ("lot", "55 sh"), ("listing", "5 Oct")),
        note=(
            "Good business at a fair-to-full price &mdash; 26% return on equity, a 48-day "
            "working-capital cycle, in cables where the demand story is real. The number to "
            "watch on Monday and Tuesday is QIB at 0.01x. Institutions bid on the last day "
            "so it is not yet a verdict, but if it finishes under 1x on a ₹552 Cr issue the "
            "retail and HNI books carried it alone, and that is a listing to sell into "
            "rather than hold."
        ),
    ),
    IPO(
        name="German Green Steel", call="WATCH — no book to read", tone="warn",
        dates="25–29 Sep (closes Tuesday)", band="₹132–139", size="₹304 Cr",
        split="₹290 Cr fresh / ₹14 Cr OFS",
        gmp="₹28", gmp_pct=20.1, expected="~+18%",
        apply_as="Retail only, and only on a day-3 book above 2x",
        horizon="Listing-day sell",
        book="no exchange book matched — the name differs between sources",
        flags=(("GMP 20%", "pass"), ("no subscription visible", "fail"),
               ("steel, cyclical", "warn")),
        stats=(("issue", "₹304 Cr"), ("fresh", "95%"), ("band", "₹132–139"),
               ("listing", "5 Oct")),
        note=(
            "A 20% grey-market premium and no exchange book this page can verify &mdash; "
            "ipowatch and the NSE name the company differently and the parser will not "
            "guess. That is the whole call: the half of the evidence that can be checked is "
            "missing, and GMP alone has never been enough here. Read the book directly on "
            "Monday before deciding."
        ),
    ),
    IPO(
        name="A-One Steels", call="SKIP", tone="fail",
        dates="24–28 Sep (closes Monday)", band="₹385–405", size="₹405 Cr",
        split="₹355 Cr fresh / ₹50 Cr OFS",
        gmp="₹51", gmp_pct=12.6, expected="~+10%",
        apply_as="—", horizon="—",
        book="Fri close: 1.35x · HNI 2.07x · retail 1.76x · QIB 0.09x",
        flags=(("24.6x for a steel maker", "fail"), ("RoE 14.7%", "warn"),
               ("QIB 0.09x on day 2", "warn")),
        stats=(("P/E post", "24.55x"), ("P/E pre", "21.76x"), ("RoE", "14.70%"),
               ("RoCE", "12.86%"), ("RoNW", "15.43%"), ("lot", "37 sh"),
               ("retail min", "₹14,985")),
        note=(
            "Twenty-four and a half times earnings for a backward-integrated long-products "
            "steel maker returning 14.7% on equity and 12.9% on capital. Steel is a "
            "cyclical that the market pays single digits for through a cycle; this is priced "
            "as though the cycle does not exist. A 12.6% premium is thin compensation for "
            "that, the book is barely covered at 1.35x with a day to run, and 0.09x QIB on "
            "day two of three is not the shape of an issue institutions want."
        ),
    ),
    IPO(
        name="Runwal Enterprises", call="SKIP", tone="fail",
        dates="25–29 Sep (closes Tuesday)", band="₹290–305", size="₹500 Cr",
        split="100% fresh",
        gmp="₹30", gmp_pct=9.8, expected="~+7%",
        apply_as="—", horizon="—",
        book="Fri close: 0.42x · QIB 0.96x · HNI 0.28x · retail 0.18x",
        flags=(("retail 0.18x", "fail"), ("under-subscribed overall", "fail"),
               ("realty at a 10% premium", "warn")),
        stats=(("issue", "₹500 Cr"), ("fresh", "100%"), ("band", "₹290–305"),
               ("lot", "—")),
        note=(
            "Retail has taken 18% of its quota and the issue as a whole is at 0.42x. A "
            "₹500 Cr realty issue that the retail book is ignoring, with a 9.8% grey-market "
            "premium that leaves about seven points after the measured overstatement. QIB "
            "at 0.96x is the only part holding up. There is no version of this worth an "
            "application at ₹305."
        ),
    ),
    IPO(
        name="Acevector", call="AVOID", tone="fail",
        dates="25–29 Sep (closes Tuesday)", band="₹30–32", size="₹420 Cr",
        split="₹287 Cr fresh / ₹133 Cr OFS",
        gmp="₹2", gmp_pct=6.2, expected="~+4%",
        apply_as="—", horizon="—",
        book="Fri close: 0.23x · HNI 0.42x · retail 0.62x · QIB 0x",
        flags=(("QIB literally zero", "fail"), ("0.23x overall", "fail"),
               ("Snapdeal's parent", "warn")),
        stats=(("issue", "₹420 Cr"), ("OFS share", "32%"), ("band", "₹30–32"),
               ("GMP", "₹2")),
        note=(
            "Snapdeal's parent, at 0.23x with two days gone and not one rupee of QIB. A ₹2 "
            "premium on a ₹32 issue is four points after the overstatement, which is inside "
            "the noise of a listing day. Every part of the book that can be read says the "
            "market does not want it at this price."
        ),
    ),
    IPO(
        name="Shah Investor’s Home", call="AVOID", tone="fail",
        dates="28–30 Sep (opens Monday)", band="₹159–167", size="₹90 Cr",
        split="100% fresh",
        gmp="₹12", gmp_pct=7.2, expected="~+5%",
        apply_as="—", horizon="—",
        book="opens Monday",
        flags=(("PAT −44%", "fail"), ("RoE 14.7% → 7.6%", "fail"),
               ("operating cash flow −₹19.7 Cr", "fail"), ("26.9x for all of it", "fail")),
        stats=(("P/E post", "26.94x"), ("P/E pre", "20.07x"), ("RoE", "7.59%"),
               ("RoCE", "10.61%"), ("FY26 income", "₹72.4 Cr, −23%"),
               ("FY26 PAT", "₹13.1 Cr, −44%"), ("op. cash flow", "−₹19.7 Cr"),
               ("lot", "85 sh")),
        note=(
            "Revenue down 23%, profit down 44%, return on equity halved from 14.7% to 7.6%, "
            "return on capital from 20.4% to 10.6%, and operating cash flow negative ₹19.7 "
            "Cr &mdash; and the ask is 26.9 times post-issue earnings, a higher multiple "
            "than the business earned when it was twice as profitable. A broker listing into "
            "a market that entered a Downtrend on Thursday, at the top of its own valuation "
            "range, on shrinking numbers. The 7.2% premium is the market's politeness."
        ),
    ),
    IPO(
        name="Vishal Nirmiti", call="AVOID — zero GMP", tone="fail",
        dates="30 Sep–5 Oct", band="₹220", size="—", split="—",
        gmp="₹0", gmp_pct=0.0, expected="~−7%",
        apply_as="—", horizon="—", book="not open",
        flags=(("zero GMP", "fail"),),
        stats=(("band", "₹220"), ("opens", "30 Sep")),
        note=(
            "No grey-market premium at all. Measured over 295 listings a zero GMP has "
            "averaged &minus;6.6% and listed positive 29% of the time, which is a coin flip "
            "weighted against you for the privilege of locked funds."
        ),
    ),
    IPO(
        name="Nityas Gems", call="AVOID — zero GMP", tone="fail",
        dates="30 Sep–5 Oct", band="₹75", size="—", split="—",
        gmp="₹0", gmp_pct=0.0, expected="~−7%",
        apply_as="—", horizon="—", book="not open",
        flags=(("zero GMP", "fail"),),
        stats=(("band", "₹75"), ("opens", "30 Sep")),
        note="Same as above, and gems and jewellery on top of it.",
    ),
]


LEAD_27 = (
    "Sunday 27 September. <strong>Nothing on the board has moved since Friday's close</strong> "
    "&mdash; the exchange was shut, so every subscription figure below is the same one the "
    "26 September review carried, and the grey-market quotes have not been re-read. The calls "
    "are unchanged and are repeated here rather than left on yesterday's page, because "
    "<strong>tomorrow is the day they are acted on</strong>: Moneyview and A-One Steels close, "
    "SRIT India and Shah Investor's Home open. "
    "Expected listing is the GMP percentage less 2.6 points &mdash; the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87). "
    "<strong>Applied so far:</strong> Adroit Industries sHNI on 23 Sep (listed, sold); "
    "Moneyview HNI on 24 Sep; Orient Cables on 25 Sep. "
    "<strong>Held:</strong> NSE, 120 shares at &#8377;1,785 &mdash; still untracked, still "
    "without a stop, into a market that turned Downtrend on Thursday."
)

FOOTNOTE_27 = (
    "<strong>Read the books again on Monday before applying.</strong> The two issues closing "
    "tomorrow have one day left and the QIB column is where it will show: institutions bid on "
    "the final day, so Moneyview at 0.25x and A-One at 0.09x are not yet verdicts. Orient "
    "Cables at 0.01x with two days left is the one to watch &mdash; on a &#8377;552 Cr issue, a "
    "QIB book that finishes under 1x means retail and HNI carried it alone, and that is a "
    "listing to sell into rather than hold. "
    "German Green Steel still has a grey-market quote and no exchange book matched: the two "
    "sources name the company differently and a name is never guessed at."
)


LEAD_28 = (
    "Monday 28 September, read again at 09:00 after the pre-open mail. "
    "<strong>Overnight the grey market moved and two of the moves matter.</strong> "
    "Runwal Enterprises has halved, &#8377;30 to &#8377;14 &mdash; 9.8% to 4.6%, which after the "
    "2.6-point overstatement is about two points and inside the noise of a listing day; the SKIP "
    "hardens. Orient Cables firmed &#8377;80 to &#8377;90, 29.4% to 33.1%, which is the market "
    "disagreeing with that 0.01x QIB book. SRIT India edged up to 25.4% and Shah Investor's Home "
    "down to 6.0% &mdash; both in the direction the calls already point. Moneyview and A-One are "
    "unchanged. Subscription figures are still Friday's close; the exchange book updates through "
    "the session. "
    "<strong>Today is the day four of these change "
    "status</strong>: SRIT India and Shah Investor's Home open, Moneyview and A-One Steels "
    "close. The subscription figures below are still Friday's close &mdash; the exchange book "
    "updates through the session, so re-read it before applying rather than acting on these. "
    "Expected listing is the GMP percentage less 2.6 points, the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87). "
    "<strong>Applied:</strong> Adroit sHNI 23 Sep (listed, sold); Moneyview HNI 24 Sep; "
    "Orient Cables 25 Sep. <strong>Held:</strong> NSE, 120 at &#8377;1,785, still without a "
    "stop, in a market that has been in a Downtrend since Thursday."
)

FOOTNOTE_28 = (
    "<strong>The one number to read again before applying to SRIT is its day-one book.</strong> "
    "A no-OFS issue at 21x with 30% return on equity is the best structure on this board, and "
    "an opening-day book under 1x would say the market disagrees with that reading. "
    "For the two closing today, QIB is now decisive rather than indicative: institutions bid on "
    "the final day, so Moneyview at 0.25x and A-One at 0.09x are Friday's picture, not the "
    "verdict. Orient Cables closes tomorrow with QIB at 0.01x &mdash; on a &#8377;552 Cr issue a "
    "book that finishes under 1x means retail and HNI carried it alone, and that is a listing "
    "to sell into rather than hold."
)

def _for_28() -> list[IPO]:
    """The 26 September calls, restated for the day they are acted on.

    The research is the same research — nothing moved over a shut weekend — so
    the stats, flags and notes are reused rather than retyped, which is what
    keeps a correction to one of them from living in only one copy. What is
    rewritten is the part that is about *today*: which issues open, which close,
    and what a reader is supposed to do about it this morning.
    """
    today = {
        "Moneyview": ("APPLIED — closes today", "24–28 Sep (CLOSES TODAY)"),
        "A-One Steels": ("SKIP — closes today", "24–28 Sep (CLOSES TODAY)"),
        "SRIT India": ("APPLY — opens today", "28–30 Sep (OPENS TODAY)"),
        "Shah Investor’s Home": ("AVOID — opens today", "28–30 Sep (OPENS TODAY)"),
        "Orient Cables": ("APPLIED — closes tomorrow", "25–29 Sep (closes tomorrow)"),
        "Acevector": ("AVOID", "25–29 Sep (closes tomorrow)"),
        "German Green Steel": ("WATCH — no book to read", "25–29 Sep (closes tomorrow)"),
        "Runwal Enterprises": ("SKIP", "25–29 Sep (closes tomorrow)"),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        if ipo.name in today:
            call, dates = today[ipo.name]
            out.append(replace(ipo, call=call, dates=dates))
        else:
            out.append(ipo)
    return out


IPOS_2026_09_28 = _for_28()

LEAD_29 = (
    "Tuesday 29 September, re-read at 09:15 against the live book. "
    "<strong>Monday was ugly and it matters here.</strong> The Nifty fell 360 points to 22,780, "
    "a six-month low, under 23,000 for the first time since April, decliners beating advancers "
    "about 2.5 to 1 &mdash; Trump rejected Iran&rsquo;s Hormuz offer and crude went to $107. "
    "The Rally Attempt that began on 25 September is dead: yesterday&rsquo;s new low at 22,762 "
    "ended it, and the new condition is holding above 22,762 for three sessions. India is now "
    "one of thirteen countries in a Downtrend, up from ten. "
    "<strong>Four issues close today</strong>: Orient Cables, Acevector, German Green Steel and "
    "Runwal. "
    "<strong>The number of the day is Orient Cables&rsquo; QIB at 0.06x</strong> with hours "
    "left, on an 8.32x book carried by HNI at 17.37x and retail at 9.16x. Moneyview went 0.25x "
    "to 58.68x on its own final day, so this is not yet settled &mdash; but it is the last day "
    "it can move. "
    "<strong>Two corrections to yesterday.</strong> Acevector covered, 0.96x to 1.15x with QIB "
    "at 1.03x, so the under-subscription risk I flagged is gone; the AVOID now rests on the "
    "6.2% GMP alone. And SRIT India cleared 1x on day two with retail at 1.61x, which does not "
    "restore the sHNI leg &mdash; that needed a 3x day-one book and got 0.67x &mdash; but it "
    "does say the retail call was the right half to keep. "
    "Expected listing is the GMP percentage less 2.6 points, the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87). "
    "<strong>Applied:</strong> Adroit sHNI 23 Sep (listed, sold); Moneyview HNI 24 Sep "
    "(closed 44.17x, QIB 58.68x); Orient Cables retail 25 Sep. "
    "<strong>Held:</strong> nothing in equities &mdash; NSE was sold Monday at &#8377;1,767.30 "
    "and the proceeds parked in LIQUIDCASE, which on a day the index lost 1.56% was the "
    "accidental right place to be."
)

FOOTNOTE_29 = (
    "<strong>What today actually decides.</strong> Three of the four closing are already "
    "called and need nothing: Runwal at 0.71x with retail at 0.42x and about two points of "
    "expected listing, Acevector covered but thin, German Green Steel closing without ever "
    "publishing a readable book &mdash; which is the whole reason it stayed a WATCH and never "
    "became a call. The live one is Orient Cables, and the plan is unchanged: sell into the "
    "listing unless QIB finishes above 5x. "
    "<strong>The honest counterweight</strong> is that Moneyview just proved a flat "
    "penultimate-day institutional book means nothing, so 0.06x is not evidence of absence "
    "yet. If it finishes there, an issue carried to 8x by HNI and retail with institutions "
    "out is a supply problem waiting for the first week of trading, and 5 October is the date "
    "to have an exit ready for. "
    "<strong>And the market is the bigger fact.</strong> A six-month low with crude at $107 "
    "is a poor tape to list into, whatever the book says. Nothing on this page is a reason to "
    "hold a listing gain past the open."
)


def _for_29() -> list[IPO]:
    """Monday's closing books and grey-market marks, on Tuesday's calls.

    Unlike ``_for_28``, this does not reuse the prior stats: Monday was a live
    session and the subscription figures moved materially on every open issue —
    Moneyview's QIB alone went 0.25x to 58.68x. Reusing them would restate
    Friday's picture under Tuesday's date, which is the failure the
    ``_for_28`` docstring is guarding against in the other direction.
    """
    # (call, dates, gmp, gmp_pct, expected, book) — None leaves the field alone.
    today: dict[str, dict[str, object]] = {
        "Moneyview": dict(
            call="APPLIED — closed, awaiting allotment",
            dates="24–28 Sep (CLOSED)",
            book="Final: 44.17x · QIB 58.68x · HNI 92.71x · retail 15.31x",
            flags=(("best GMP on the board", "pass"), ("QIB 58.7x — the case made", "pass"),
                   ("PAT flat on +43% revenue", "warn"), ("D/E 2.27x", "warn")),
        ),
        "A-One Steels": dict(
            call="SKIP — closed",
            dates="24–28 Sep (CLOSED)",
            gmp="₹40", gmp_pct=9.9, expected="~+7%",
            book="Final: 7.14x · QIB 0.42x · HNI 16.77x · retail 6.91x",
            flags=(("24.6x for a steel maker", "fail"), ("RoE 14.7%", "warn"),
                   ("QIB finished 0.42x", "fail"), ("GMP faded 13.8% → 9.9%", "warn")),
        ),
        "Orient Cables": dict(
            call="APPLIED — closes today",
            dates="25–29 Sep (CLOSES TODAY)",
            gmp="₹72", gmp_pct=26.5, expected="~+24%",
            book="Tue 09:00: 8.32x · QIB 0.06x · HNI 17.37x · retail 9.16x",
            flags=(("RoE 25.8%", "pass"), ("8.32x overall", "pass"),
                   ("QIB 0.06x with hours left", "fail"), ("GMP ₹90 → ₹80 → ₹72", "warn")),
        ),
        "Acevector": dict(
            call="AVOID — it covered, the call still stands",
            dates="25–29 Sep (CLOSES TODAY)",
            book="Tue 09:00: 1.15x · QIB 1.03x · HNI 1.25x · retail 1.36x",
            flags=(("covered — the under-subscription risk is gone", "pass"),
                   ("1.15x is thin for a ₹420 Cr issue", "warn"),
                   ("GMP 6.2% → ~+4% after overstatement", "warn")),
        ),
        "German Green Steel": dict(
            call="WATCH — closes today, no book to read",
            dates="25–29 Sep (CLOSES TODAY)",
            gmp="₹25", gmp_pct=18.0, expected="~+15%",
            book="No subscription figures published, on its closing day",
        ),
        "Runwal Enterprises": dict(
            call="SKIP — closes today",
            dates="25–29 Sep (CLOSES TODAY)",
            gmp="₹14", gmp_pct=4.6, expected="~+2%",
            book="Tue 09:00: 0.71x · QIB 1.05x · HNI 0.94x · retail 0.42x",
            flags=(("retail 0.42x", "fail"), ("0.71x on the final day", "fail"),
                   ("GMP back to ₹14 — still ~+2% after overstatement", "warn")),
        ),
        "SRIT India": dict(
            call="APPLY, retail only — downgraded on its own test",
            dates="28–30 Sep (closes tomorrow)",
            gmp="₹33", gmp_pct=25.4, expected="~+23%",
            book="Day 2: 1.00x · retail 1.61x · HNI 0.90x · QIB 0x",
            apply_as="Retail only — the sHNI leg needed a 3x day-1 book and got 0.67x",
            flags=(("no OFS — every rupee goes in", "pass"), ("RoE 30.2%", "pass"),
                   ("cleared 1x on day 2", "pass"), ("QIB still absent with a day left", "warn")),
        ),
        "Shah Investor’s Home": dict(
            call="AVOID — confirmed by the book",
            dates="28–30 Sep (closes tomorrow)",
            gmp="₹14", gmp_pct=8.4, expected="~+6%",
            book="Day 2: 0.31x · QIB 0.5x · HNI 0.25x · retail 0.24x",
        ),
        "Nityas Gems": dict(
            call="WATCH — opens tomorrow",
            dates="30 Sep–5 Oct (opens tomorrow)",
            gmp="₹9", gmp_pct=12.0, expected="~+9%",
            flags=(("GMP ₹0 → ₹5 → ₹9 in two sessions", "warn"), ("no book until it opens", "warn")),
        ),
        "Vishal Nirmiti": dict(
            call="AVOID — opens tomorrow at a near-zero GMP",
            dates="30 Sep–5 Oct (opens tomorrow)",
            gmp="₹2", gmp_pct=0.9, expected="~−2%",
        ),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        change = today.get(ipo.name)
        out.append(replace(ipo, **change) if change else ipo)  # type: ignore[arg-type]
    return out


IPOS_2026_09_29 = _for_29()


LEAD_30 = (
    "Wednesday 30 September, read at 10:30 against the live book. "
    "<strong>Tomorrow is the first listing day, and it is the one that matters.</strong> "
    "Moneyview lists 1 October at a grey-market premium of &#8377;13, 38.2% &mdash; about "
    "36% after the 2.6-point overstatement &mdash; having closed at 44.17x with QIB at "
    "58.68x. The plan has not changed since the day it was applied for: <strong>sell at the "
    "open</strong>. The case was the discount, not the franchise, and holding past the open "
    "means owning the margin question on a lender whose profit went nowhere on 43% revenue "
    "growth. A-One Steels lists the same day at 8.6%; we skipped it and that is fine either "
    "way. "
    "<strong>SRIT India closed today at 4.16x &mdash; and repeated the Orient Cables "
    "pattern.</strong> Retail 6.04x, HNI 5.25x, <strong>QIB 0.03x</strong>. That is the "
    "second issue this week carried entirely by retail and high-net-worth money with "
    "institutions absent, and it converts the retail-only call into a listing-day sell "
    "rather than anything to hold. "
    "<strong>Two skips were paid for today.</strong> Runwal&rsquo;s premium collapsed to "
    "&#8377;2, 0.7%, and German Green Steel halved to 9.4% &mdash; both called on structure "
    "rather than on GMP, one for never covering its retail book and one for never publishing "
    "a book at all. "
    "Expected listing is the GMP percentage less 2.6 points, the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87). "
    "<strong>Applied:</strong> Moneyview HNI 24 Sep (lists tomorrow); Orient Cables retail "
    "25 Sep (lists 5 Oct). <strong>Held:</strong> nothing in equities &mdash; the book is "
    "LIQUIDCASE and nothing else, on a day our own breadth reading fell to 36%."
)

FOOTNOTE_30 = (
    "<strong>Orient Cables firmed rather than faded: &#8377;72 to &#8377;85, 31.3%, with "
    "five sessions still to run before it lists.</strong> Its QIB book never arrived &mdash; "
    "0.06x against 8.32x overall &mdash; so the test set on Monday was not met and the plan "
    "stands: sell into the listing. It is worth being clear that the grey market is "
    "disagreeing with that reading, and the grey market has an r of 0.87 with realised "
    "listing gains. What it does not price is the week after, which is where an issue "
    "carried by HNI at 17x with institutions absent has to find real holders. "
    "<strong>Shah Investor&rsquo;s Home covered, at 1.1x with QIB at 1.08x.</strong> The "
    "AVOID was never about coverage &mdash; it was profit down 44% and return on equity "
    "halving from 14.7% to 7.6% &mdash; so the call stands, but the book came in better "
    "than the one-in-four subscription it opened with and that is worth recording rather "
    "than quietly dropping."
)


def _for_30() -> list[IPO]:
    """Tuesday&rsquo;s closes, Wednesday&rsquo;s listings, and two new issues open.

    Six of the ten are now closed and waiting to list, so their subscription
    books are final and are labelled as such. The grey-market marks moved
    materially on four of them overnight, which is the reason this is rebuilt
    rather than pointed at yesterday&rsquo;s list.
    """
    today: dict[str, dict[str, object]] = {
        "Moneyview": dict(
            call="APPLIED — LISTS TOMORROW, sell at the open",
            dates="listed 1 Oct · closed 44.17x",
            gmp="₹13", gmp_pct=38.2, expected="~+36%",
            book="Final: 44.17x · QIB 58.68x · HNI 92.71x · retail 15.31x",
        ),
        "A-One Steels": dict(
            call="SKIPPED — lists tomorrow",
            dates="listed 1 Oct · closed 7.14x",
            gmp="₹35", gmp_pct=8.6, expected="~+6%",
        ),
        "Orient Cables": dict(
            call="APPLIED — sell into the listing",
            dates="lists 5 Oct · closed 8.32x",
            gmp="₹85", gmp_pct=31.3, expected="~+29%",
            book="Final: 8.32x · QIB 0.06x · HNI 17.37x · retail 9.16x",
            flags=(("RoE 25.8%", "pass"), ("GMP firmed ₹72 → ₹85", "pass"),
                   ("QIB finished 0.06x", "fail"), ("HNI and retail carried it alone", "warn")),
        ),
        "Runwal Enterprises": dict(
            call="SKIPPED — and the premium collapsed",
            dates="lists 5 Oct · closed 0.71x",
            gmp="₹2", gmp_pct=0.7, expected="~−2%",
            flags=(("GMP ₹14 → ₹2 in a session", "fail"), ("never covered", "fail")),
        ),
        "German Green Steel": dict(
            call="WATCH — never published a book, premium halved",
            dates="lists 5 Oct",
            gmp="₹13", gmp_pct=9.4, expected="~+7%",
            flags=(("GMP ₹25 → ₹13", "fail"), ("no subscription figures, ever", "fail")),
        ),
        "Acevector": dict(
            call="AVOIDED — covered, listed at a thin premium",
            dates="lists 5 Oct · closed 1.15x",
            gmp="₹2", gmp_pct=6.3, expected="~+4%",
        ),
        "SRIT India": dict(
            call="APPLIED retail — closed today, sell at the open",
            dates="28–30 Sep (CLOSED TODAY)",
            gmp="₹31", gmp_pct=23.8, expected="~+21%",
            book="Final: 4.16x · retail 6.04x · HNI 5.25x · QIB 0.03x",
            apply_as="Retail only — the sHNI leg needed a 3x day-1 book and got 0.67x",
            flags=(("no OFS — every rupee goes in", "pass"), ("RoE 30.2%", "pass"),
                   ("4.16x overall", "pass"), ("QIB 0.03x — the Orient pattern again", "fail")),
        ),
        "Shah Investor’s Home": dict(
            call="AVOID — it covered, the call was never about coverage",
            dates="28–30 Sep (CLOSED TODAY)",
            gmp="₹15", gmp_pct=9.0, expected="~+6%",
            book="Final: 1.10x · QIB 1.08x · HNI 1.59x · retail 0.90x",
            flags=(("covered at 1.1x", "pass"), ("PAT −44%", "fail"),
                   ("RoE 14.7% → 7.6%", "fail"), ("retail stayed under 1x", "warn")),
        ),
        "Vishal Nirmiti": dict(
            call="AVOID — opened today, premium still near nothing",
            dates="30 Sep–5 Oct (OPENS TODAY)",
            gmp="₹6", gmp_pct=2.7, expected="~0%",
            flags=(("GMP ₹0 → ₹2 → ₹6", "warn"), ("still under 3%", "fail")),
        ),
        "Nityas Gems": dict(
            call="WATCH — opened today, no book matched yet",
            dates="30 Sep–5 Oct (OPENS TODAY)",
            gmp="₹5", gmp_pct=6.7, expected="~+4%",
        ),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        change = today.get(ipo.name)
        out.append(replace(ipo, **change) if change else ipo)  # type: ignore[arg-type]
    return out


IPOS_2026_09_30 = _for_30()


LEAD_01 = (
    "Thursday 1 October, written at 08:00 before the bell. "
    "<strong>Two calls were overturned on the final day, both the same way, and that is the "
    "note worth reading.</strong> SRIT India finished with QIB at <strong>91.84x</strong>, "
    "HNI at 312.99x and retail at 63.7x. On Tuesday it sat at 0.03x and this page called it "
    "&ldquo;the Orient Cables pattern again&rdquo; &mdash; an issue carried by retail with "
    "institutions absent. It was nothing of the kind. Shah Investor&rsquo;s Home, carrying an "
    "AVOID, closed at QIB 28.05x and HNI 95.54x from 1.1x the day before. "
    "<strong>That is the second and third time this week the same mistake was made.</strong> "
    "Moneyview went 0.25x to 58.68x on its own last day; the lesson was written down and then "
    "applied as a warning to SRIT anyway. Institutions bid on the final day. A low QIB book "
    "with a day left is <em>not information</em>, and this page should stop treating it as any. "
    "<strong>Moneyview and A-One Steels list today.</strong> Moneyview at a grey-market premium "
    "of &#8377;13, 38.2%, about 36% after the overstatement &mdash; the plan from the day it "
    "was applied for is unchanged: sell at the open. The case was the discount, not the "
    "franchise. "
    "Expected listing is the GMP percentage less 2.6 points, the overstatement "
    "<code>backtest_gmp</code> measured over 295 listings (r&nbsp;=&nbsp;0.87). "
    "<strong>Applied:</strong> Moneyview HNI 24 Sep (lists today); Orient Cables retail 25 Sep "
    "(lists 5 Oct); SRIT India retail 28 Sep (lists 6 Oct). "
    "<strong>Held:</strong> nothing in equities. The Nifty closed September 6% lower at 22,620, "
    "a six-month-low close, on Day 2 of a rally attempt."
)

FOOTNOTE_01 = (
    "<strong>What the three reversals actually teach.</strong> Orient Cables, Moneyview, SRIT "
    "India and Shah Investor&rsquo;s Home all showed a thin or absent QIB book on the "
    "penultimate day. Three of the four finished with institutional books between 28x and 92x. "
    "The exception is Orient, which finished at 0.06x &mdash; so the signal is not useless, it "
    "is simply far weaker than this page has been treating it, and it cannot be read before "
    "the final day closes. The rule going forward: <strong>quote the QIB book, do not forecast "
    "from it.</strong> "
    "<strong>Orient Cables is still the one to watch</strong>, and for the opposite reason to "
    "the one stated on Monday. It is the only issue this week whose institutional book never "
    "arrived, it lists 5 October at a 31% premium, and an issue carried to 8.32x by HNI at "
    "17.37x with QIB at 0.06x has to find real holders in the first week of trading. The plan "
    "is unchanged and now rests on evidence rather than on a pattern that turned out not to "
    "be one."
)


def _for_01() -> list[IPO]:
    """Final books for everything that closed, and two listings today.

    Rebuilt rather than pointed at the 30th because the final-day subscription
    figures landed overnight and reversed two calls. Reusing yesterday's list
    would restate the reading that was wrong.
    """
    today: dict[str, dict[str, object]] = {
        "Moneyview": dict(
            call="APPLIED — LISTS TODAY, sell at the open",
            dates="lists 1 Oct · closed 44.17x",
            gmp="₹13", gmp_pct=38.2, expected="~+36%",
        ),
        "A-One Steels": dict(
            call="SKIPPED — lists today",
            dates="lists 1 Oct · closed 7.14x",
            gmp="₹35", gmp_pct=8.6, expected="~+6%",
        ),
        "SRIT India": dict(
            call="APPLIED retail — the QIB warning was wrong",
            dates="lists 6 Oct · closed with QIB 91.84x",
            book="Final: QIB 91.84x · HNI 312.99x · retail 63.70x",
            flags=(("no OFS — every rupee goes in", "pass"), ("RoE 30.2%", "pass"),
                   ("QIB 0.03x → 91.84x on the last day", "pass"),
                   ("this page called it a retail-only book — wrong", "fail")),
        ),
        "Shah Investor’s Home": dict(
            call="AVOIDED — and the book says the market disagreed",
            dates="lists 6 Oct · closed with QIB 28.05x",
            book="Final: QIB 28.05x · HNI 95.54x · retail 19.26x",
            flags=(("QIB 0.5x → 28.05x on the last day", "pass"),
                   ("PAT −44%", "fail"), ("RoE 14.7% → 7.6%", "fail"),
                   ("avoided on fundamentals, not on the book", "warn")),
        ),
        "Orient Cables": dict(
            call="APPLIED — the only book that never arrived",
            dates="lists 5 Oct · closed 8.32x",
            gmp="₹85", gmp_pct=31.3, expected="~+29%",
        ),
        "Vishal Nirmiti": dict(
            call="AVOID — open, and the book is not there",
            dates="30 Sep–5 Oct (open)",
            book="Day 2: 0.05x · QIB 0.96x · HNI 0.01x · retail 0.06x",
            flags=(("0.05x on day two", "fail"), ("GMP 2.7%", "fail")),
        ),
        "Nityas Gems": dict(
            call="WATCH — open, no book matched yet",
            dates="30 Sep–5 Oct (open)",
            gmp="₹5", gmp_pct=6.7, expected="~+4%",
        ),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        change = today.get(ipo.name)
        out.append(replace(ipo, **change) if change else ipo)  # type: ignore[arg-type]
    return out


IPOS_2026_10_01 = _for_01()


LEAD_05 = (
    "Monday 5 October, written at 10:45. "
    "<strong>Orient Cables finished at 97.28x and lists today.</strong> On the morning of its "
    "final day this page had it at 8.32x with QIB at 0.06x and called that the number of the "
    "day. The grey-market premium has since risen &#8377;85 to &#8377;110, an indicative "
    "listing near &#8377;382 against a &#8377;272 band &mdash; about +40%. "
    "<strong>That is the fourth time the same mistake would have been made</strong>, after "
    "Moneyview (0.25x to 58.68x), SRIT India (0.03x to 91.84x) and Shah Investor&rsquo;s Home "
    "(1.1x to 28.05x). The rule written here on 1 October &mdash; <em>quote the QIB book, do "
    "not forecast from it</em> &mdash; has now been tested four times and held every time. "
    "<strong>Nothing was allotted.</strong> The broker shows no Orient Cables, no Moneyview and "
    "no A-One Steels; the account holds LIQUIDCASE and nothing else. At 97.28x overall and "
    "44.17x for Moneyview, retail and HNI allotment is a lottery and this is the ordinary "
    "outcome, not a failure &mdash; but it should be confirmed against the Console rather than "
    "inferred from an empty holdings list. "
    "<strong>The generated board is unavailable today.</strong> <code>show_ipos</code> reports "
    "that the source has restructured and carries no Mainboard GMP table at all, so the numbers "
    "above are read from the exchange and grey-market pages directly. The parser needs fixing "
    "before that section is trusted again."
)

FOOTNOTE_05 = (
    "<strong>What four reversals in one week actually establish.</strong> Every issue this page "
    "flagged for a thin institutional book &mdash; Moneyview, SRIT, Shah Investor&rsquo;s Home, "
    "Orient Cables &mdash; closed with a heavy one. Not one exception. A QIB figure read before "
    "the final session closes is not weak evidence; on this sample it is anti-evidence, and the "
    "only honest use of it is to report the number and wait. "
    "The sell-into-the-listing plan for Orient rested on QIB finishing under 5x. It finished far "
    "above, so the plan&rsquo;s premise is gone &mdash; which is moot here, since nothing was "
    "allotted, but it would not have been moot at ten lakh. "
    "<strong>The market it lists into is the other half.</strong> The Nifty closed 1 October at "
    "22,421.95, invalidating the second rally attempt in a week, and twenty-seven countries are "
    "now in a MarketSmith Downtrend against nine in a confirmed uptrend. A 40% indicative "
    "premium is a grey-market quote, not a print."
)


def _for_05() -> list[IPO]:
    """Listing day for the 25–29 September cohort.

    The subscription figures here are final and come from the exchange rather
    than from the generated board, which is down.
    """
    today: dict[str, dict[str, object]] = {
        "Orient Cables": dict(
            call="LISTS TODAY — not allotted",
            dates="lists 5 Oct · closed 97.28x",
            gmp="₹110", gmp_pct=40.4, expected="~+38%",
            book="Final: 97.28x overall — from 8.32x on the final morning",
            flags=(("RoE 25.8%", "pass"), ("97.28x final book", "pass"),
                   ("the 0.06x QIB read was wrong, as it was three times before", "fail")),
        ),
        "Moneyview": dict(
            call="LISTED 1 Oct — not allotted",
            dates="listed 1 Oct · closed 44.17x",
        ),
        "A-One Steels": dict(
            call="LISTED 1 Oct — skipped",
            dates="listed 1 Oct · closed 7.14x",
        ),
        "SRIT India": dict(
            call="LISTS 6 Oct — QIB 91.84x",
            dates="lists 6 Oct",
        ),
        "Shah Investor’s Home": dict(
            call="LISTS 6 Oct — avoided, QIB 28.05x",
            dates="lists 6 Oct",
        ),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        change = today.get(ipo.name)
        out.append(replace(ipo, **change) if change else ipo)  # type: ignore[arg-type]
    return out


IPOS_2026_10_05 = _for_05()


LEAD_06 = (
    "Tuesday 6 October, written at 09:45. "
    "<strong>SRIT India and Shah Investor&rsquo;s Home list today, and neither was "
    "allotted.</strong> The broker holds LIQUIDCASE and nothing else; at a 91.84x QIB book "
    "for SRIT, retail allotment was always a lottery. SRIT&rsquo;s grey-market premium has run "
    "from &#8377;31 to <strong>&#8377;62, 47.7%</strong> &mdash; roughly +45% after the "
    "2.6-point overstatement &mdash; which is the fifth time in a fortnight that an issue this "
    "page flagged for a thin institutional book has ended up in demand. "
    "<strong>The whole September cohort is now settled and the scoreboard is one-sided.</strong> "
    "Moneyview 0.25x&rarr;58.68x, SRIT 0.03x&rarr;91.84x, Shah 1.1x&rarr;28.05x, Orient Cables "
    "8.32x&rarr;97.28x. Every single one. The rule written here on 1 October &mdash; "
    "<em>quote the QIB book, do not forecast from it</em> &mdash; has not been wrong once. "
    "<strong>Jio Platform is the next real decision</strong>, 21&ndash;23 October, already "
    "quoted at a &#8377;160 premium with no band published. It is the only name left on the "
    "board and it deserves proper work before it opens, not a GMP read on the morning. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_06 = (
    "<strong>Nothing was applied for and nothing was allotted this cycle</strong>, so the four "
    "reversals cost nothing in money. They cost something in method, which is the more useful "
    "loss: a number this page treated as decisive turned out to be noise until the final "
    "session closed, four times out of four, and it took the fourth before the rule was "
    "written down rather than merely noticed. "
    "<strong>The board itself is thinner than it looks.</strong> The four closed issues have "
    "dropped off the source entirely now that they have listed, so the only live row is Jio "
    "Platform in a fortnight. That is a gap worth using: the next decision is a large one and "
    "there is time to do the fundamentals properly instead of reading a grey-market quote at "
    "08:00 on the opening morning."
)


def _for_06() -> list[IPO]:
    """Listing day for SRIT and Shah; the cohort closes out."""
    today: dict[str, dict[str, object]] = {
        "SRIT India": dict(
            call="LISTS TODAY — not allotted",
            dates="lists 6 Oct · closed with QIB 91.84x",
            gmp="₹62", gmp_pct=47.7, expected="~+45%",
        ),
        "Shah Investor’s Home": dict(
            call="LISTS TODAY — avoided, not allotted",
            dates="lists 6 Oct · closed with QIB 28.05x",
            gmp="₹17", gmp_pct=10.2, expected="~+8%",
        ),
        "Orient Cables": dict(call="LISTED 5 Oct — not allotted", dates="listed 5 Oct · 97.28x"),
        "Moneyview": dict(call="LISTED 1 Oct — not allotted", dates="listed 1 Oct · 44.17x"),
        "A-One Steels": dict(call="LISTED 1 Oct — skipped", dates="listed 1 Oct · 7.14x"),
        "Vishal Nirmiti": dict(call="CLOSED — avoided", dates="closed 5 Oct · 0.05x"),
        "Nityas Gems": dict(call="CLOSED — watched, never applied", dates="closed 5 Oct"),
    }
    out = []
    for ipo in IPOS_2026_09_26:
        change = today.get(ipo.name)
        out.append(replace(ipo, **change) if change else ipo)  # type: ignore[arg-type]
    return out


IPOS_2026_10_06 = _for_06()


LEAD_07 = (
    "Wednesday 7 October, written at 09:30. "
    "<strong>Nothing is open for application today and nothing is held.</strong> The September "
    "cohort has listed out and dropped off the source; the board is down to two forward names, "
    "neither of which has a published price band. That is the gap the 6 October footnote asked "
    "for, so this entry spends it on <strong>Jio Platform&rsquo;s accounts rather than its "
    "grey-market quote</strong> &mdash; the largest IPO India has run, open 21&ndash;23 October. "
    "The numbers are now in: <strong>FY26 revenue &#8377;1,46,885 Cr (+14.6%), EBITDA "
    "&#8377;76,255 Cr at a 51.9% margin, PAT &#8377;30,049 Cr (+15.1%)</strong>, 524.4 M "
    "subscribers, ARPU &#8377;214. At the reported &#8377;13 lakh crore equity value that is "
    "<strong>about 43&times; FY26 earnings for 15% profit growth</strong>. "
    "Two structural facts cut opposite ways and both matter: the issue is "
    "<strong>100% fresh with no offer for sale</strong> &mdash; the one signal in an IPO that "
    "cannot be dressed, and the same one that made SRIT the pick last month &mdash; but "
    "<strong>&#8377;27,500 Cr of roughly &#8377;33,000 Cr goes to repaying borrowings</strong>, "
    "so it is a deleveraging, not an expansion. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_07 = (
    "<strong>HD Fire Protect&rsquo;s zero GMP is not a signal today and must not be read as "
    "one.</strong> Its band is not published until about 9 October, and a premium is a quote "
    "against a price: with no price there is nothing to quote. Our own calibration &mdash; a "
    "zero GMP has averaged &minus;6.6% over 295 listings &mdash; is drawn from issues whose "
    "band existed and whose grey market declined to bid. This is not that, and treating the two "
    "as the same number is precisely the error this page made four times in September when it "
    "called thin institutional books decisive and was wrong every time. "
    "<strong>The one genuinely new argument for Jio is allotment odds, not price.</strong> On a "
    "&#8377;218 Cr issue a retail application is a lottery &mdash; SRIT closed at 91.84&times; "
    "QIB and nothing came. The retail quota of a &#8377;33,000 Cr issue is larger in absolute "
    "rupees by more than two orders of magnitude, so for the first time this quarter an "
    "application has a real chance of being filled. That changes the arithmetic of applying "
    "far more than a 14% grey-market premium does."
)


def _for_07() -> list[IPO]:
    """Board down to two forward names; the Jio fundamentals, done early."""
    return [
        IPO(
            name="Jio Platform", call="WORK DONE EARLY — decide when the band prints", tone="warn",
            dates="21–23 Oct · allotment 26 Oct · lists 28 Oct",
            band="not published · reported ₹1,150–1,220",
            size="~₹33,000 Cr (reports range to ₹37,800 Cr)",
            split="100% fresh, no OFS — up to 27 Cr shares, FV ₹10",
            gmp="₹167", gmp_pct=13.7, expected="~+11%",
            apply_as="Retail — and this is the first issue this quarter where that is worth doing",
            horizon="Undecided until the band prints. 43× is not a listing-pop multiple.",
            book="opens 21 Oct · DRHP 19 Jun 2026",
            flags=(("no OFS — every rupee goes in", "pass"),
                   ("51.9% EBITDA margin", "pass"),
                   ("retail allotment actually plausible", "pass"),
                   ("~43× FY26 for 15% growth", "warn"),
                   ("₹27,500 Cr of it repays debt", "warn"),
                   ("band unpublished", "warn")),
            stats=(("FY26 revenue", "₹1,46,885 Cr"), ("FY26 EBITDA", "₹76,255 Cr"),
                   ("EBITDA margin", "51.9%"), ("FY26 PAT", "₹30,049 Cr"),
                   ("PAT growth", "+15.1%"), ("revenue growth", "+14.6%"),
                   ("subscribers", "524.4 M"), ("ARPU", "₹214/mo")),
            note=(
                "The quality is not in question &mdash; a 51.9% EBITDA margin on "
                "&#8377;1.47 lakh crore of revenue is a utility with a moat. The price is. "
                "Forty-three times earnings for 15% profit growth is a PEG near 2.9, and the "
                "growth that would justify it has to come from tariffs rather than "
                "subscribers: ARPU moved &#8377;206 to &#8377;214 in a year, under 4%, on a "
                "base of 524 million where there is not much of India left to add. Several "
                "houses expect the listing itself to trigger a tariff cycle, which is a "
                "reasonable thesis and an unproven one. "
                "<strong>Note what the fresh-issue structure does and does not say.</strong> "
                "No promoter is selling, which is genuinely rare at this size and removes the "
                "usual exit-at-the-top read. But 83% of the money repays borrowings. That "
                "lifts earnings by removing interest rather than by building anything, and a "
                "deleveraging is worth paying for at a lower multiple than a growth raise, "
                "not a higher one. "
                "No call today, by design: the band is the whole decision and it is not out."
            ),
        ),
        IPO(
            name="HD Fire Protect", call="WATCH — nothing to judge yet", tone="warn",
            dates="13–15 Oct · allotment 16 Oct · lists 21 Oct",
            band="announced ~9 Oct", size="₹700–750 Cr",
            split="100% OFS — 2.6 Cr shares, no fresh capital",
            gmp="₹0", gmp_pct=0.0, expected="—",
            apply_as="Undecided — no band, no book, no basis",
            horizon="Revisit 9 October when the band prints",
            book="opens 13 Oct",
            flags=(("100% OFS — nothing goes to the company", "fail"),
                   ("band unpublished", "warn"),
                   ("zero GMP is uninformative here, not bearish", "warn"),
                   ("Saudi Aramco among its customers", "pass")),
            stats=(("issue", "₹700–750 Cr"), ("shares offered", "2.6 Cr"),
                   ("fresh capital", "nil"), ("opens", "13 Oct"),
                   ("band due", "~9 Oct"), ("lists", "21 Oct")),
            note=(
                "The exact inverse of Jio on the one structural axis that matters: every "
                "rupee of this goes to selling shareholders and none to the business. That "
                "is not disqualifying &mdash; a clean OFS of a profitable niche manufacturer "
                "is an ordinary way to list &mdash; but it removes the only unfakeable "
                "signal an IPO offers, and it means the sellers chose this price. "
                "Fire-protection equipment with Saudi Aramco on the customer list is a real "
                "business with a real export book. None of that can be priced until 9 "
                "October, so there is no call here and will not be one until there is."
            ),
        ),
    ]


IPOS_2026_10_07 = _for_07()


BY_DAY = {
    "2026-09-23": (IPOS_2026_09_23, LEAD, FOOTNOTE),
    "2026-09-24": (IPOS_2026_09_24, LEAD_24, FOOTNOTE_24),
    "2026-09-25": (IPOS_2026_09_25, LEAD_25, FOOTNOTE_25),
    "2026-09-26": (IPOS_2026_09_26, LEAD_26, FOOTNOTE_26),
    # Same ten issues, unchanged because the market was shut. Pointed at the
    # same list rather than copied: a duplicate would drift the moment one
    # number was corrected in only one of them.
    "2026-09-27": (IPOS_2026_09_26, LEAD_27, FOOTNOTE_27),
    "2026-09-28": (IPOS_2026_09_28, LEAD_28, FOOTNOTE_28),
    "2026-09-29": (IPOS_2026_09_29, LEAD_29, FOOTNOTE_29),
    "2026-09-30": (IPOS_2026_09_30, LEAD_30, FOOTNOTE_30),
    "2026-10-01": (IPOS_2026_10_01, LEAD_01, FOOTNOTE_01),
    "2026-10-05": (IPOS_2026_10_05, LEAD_05, FOOTNOTE_05),
    "2026-10-06": (IPOS_2026_10_06, LEAD_06, FOOTNOTE_06),
    "2026-10-07": (IPOS_2026_10_07, LEAD_07, FOOTNOTE_07),
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
