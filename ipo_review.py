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


LEAD_08 = (
    "Thursday 8 October, written at 09:45. "
    "<strong>HD Fire Protect published its band and the picture changed.</strong> "
    "&#8377;258&ndash;271, opening Monday 13 October, and the grey market moved from "
    "nothing to <strong>&#8377;80 &mdash; 29.5%</strong> within a day of the price existing. "
    "Yesterday this page refused to read its zero GMP as bearish, on the grounds that a "
    "premium is a quote against a price and there was no price. That was the right call and "
    "the board has now said so. "
    "<strong>The issue itself is harder than its grey market.</strong> At the top of the band "
    "the company lists at <strong>&#8377;4,749 Cr against FY26 profit of &#8377;116.79 Cr "
    "&mdash; 40.7&times; earnings for 6.4% profit growth</strong>, and every rupee of the "
    "&#8377;712 Cr goes to the promoter couple selling it. "
    "<strong>Jio Platform&rsquo;s premium keeps climbing</strong> &mdash; &#8377;185 now, from "
    "&#8377;167 yesterday and &#8377;160 on Monday &mdash; with the band still unpublished. "
    "<strong>Held:</strong> nothing in equities. Nothing is open for application today."
)

FOOTNOTE_08 = (
    "<strong>Two GMP sources disagree on HD Fire Protect today</strong>, one quoting "
    "&#8377;80 and one still showing zero, and that is worth stating rather than resolving "
    "by picking the one that suits. A grey-market quote has no print behind it; when the "
    "feeds diverge on the first day of a band, the honest reading is that the market has not "
    "settled, not that it has settled at the higher number. "
    "<strong>The structural case is the one this page keeps returning to.</strong> SRIT was "
    "worth applying for because every rupee went into the company. This is the inverse: a "
    "pure secondary sale by two promoters at forty times earnings, where the people who know "
    "the business best are the sellers and the proceeds build nothing. That is not "
    "disqualifying &mdash; a 30.75% EBITDA margin and Saudi Aramco on the customer list are "
    "real &mdash; but it means the entire case rests on the listing pop, and a listing pop is "
    "the one thing this page has been wrong about four times running when it tried to "
    "forecast it from the institutional book. Quote the QIB number on day two; do not "
    "predict it."
)


def _for_08() -> list[IPO]:
    """HD Fire Protect prices; Jio's premium keeps climbing on no band."""
    return [
        IPO(
            name="HD Fire Protect", call="DECIDE MONDAY — the band is out, the case is split",
            tone="warn",
            dates="13–15 Oct · anchors 12 Oct · allotment 16 Oct · lists 21 Oct",
            band="₹258–271", size="₹712 Cr at the top of the band",
            split="100% OFS — 2.62 Cr shares, both sellers are the promoters",
            gmp="₹80", gmp_pct=29.5, expected="~+27%",
            apply_as="Retail if applying at all — ₹14,905 at 55 shares",
            horizon="Listing-day sell. At 40.7× for 6.4% growth there is no hold case.",
            book="opens 13 Oct · anchors 12 Oct",
            flags=(("GMP 29.5% from a standing start", "pass"),
                   ("EBITDA margin 30.75%", "pass"),
                   ("100% OFS — nothing to the company", "fail"),
                   ("40.7× FY26 for 6.4% PAT growth", "fail"),
                   ("PAT growing slower than revenue", "warn"),
                   ("two GMP feeds disagree today", "warn")),
            stats=(("P/E post", "40.7×"), ("market cap", "₹4,749 Cr"),
                   ("FY26 revenue", "₹489.28 Cr"), ("revenue growth", "+13.0%"),
                   ("FY26 PAT", "₹116.79 Cr"), ("PAT growth", "+6.4%"),
                   ("EBITDA margin", "30.75%"), ("retail min", "₹14,905")),
            note=(
                "A good business at a price that needs the grey market to be right. "
                "Revenue grew 13% and profit 6.4%, so margin is compressing even at 30.75% "
                "&mdash; and the market is being asked for forty times earnings on that. "
                "Both sellers are the promoters and the company receives nothing, which is "
                "the exact inverse of the structure that made SRIT worth applying for last "
                "month. "
                "<strong>So the case is entirely the listing pop.</strong> A 29.5% premium "
                "appearing within a day of the band is genuine demand and not nothing; "
                "&#8377;712 Cr is also small enough that retail allotment is a real "
                "possibility rather than the lottery a &#8377;218 Cr issue was. The decision "
                "belongs on Monday with the anchor book in hand, and the QIB number on day "
                "two is the thing to read &mdash; not forecast."
            ),
        ),
        IPO(
            name="Jio Platform", call="WORK DONE — waiting on the band", tone="warn",
            dates="21–23 Oct · allotment 26 Oct · lists 28 Oct",
            band="still unpublished · reported ₹1,150–1,220",
            size="~₹33,000 Cr", split="100% fresh, no OFS — up to 27 Cr shares, FV ₹10",
            gmp="₹185", gmp_pct=15.2, expected="~+13%",
            apply_as="Retail — the one issue this quarter where allotment is plausible",
            horizon="Undecided until the band prints. 43× is not a listing-pop multiple.",
            book="opens 21 Oct · DRHP 19 Jun 2026",
            flags=(("no OFS — every rupee goes in", "pass"),
                   ("51.9% EBITDA margin", "pass"),
                   ("GMP ₹160 → ₹167 → ₹185 in three sessions", "pass"),
                   ("~43× FY26 for 15% growth", "warn"),
                   ("₹27,500 Cr of it repays debt", "warn"),
                   ("band still unpublished", "warn")),
            stats=(("FY26 revenue", "₹1,46,885 Cr"), ("FY26 EBITDA", "₹76,255 Cr"),
                   ("EBITDA margin", "51.9%"), ("FY26 PAT", "₹30,049 Cr"),
                   ("PAT growth", "+15.1%"), ("subscribers", "524.4 M"),
                   ("ARPU", "₹214/mo"), ("GMP", "₹185")),
            note=(
                "Unchanged from yesterday's work except the premium, which has risen for a "
                "third session &mdash; &#8377;160, &#8377;167, &#8377;185 &mdash; against a "
                "band nobody has published. At the reported &#8377;1,220 top that is 15.2%, "
                "so roughly 13% expected after the overstatement. "
                "A rising premium on an unpublished band is sentiment rather than "
                "information, and the thing that will actually decide this is still the "
                "number Reliance prints. Forty-three times earnings for 15% growth needs the "
                "tariff cycle several houses expect; 83% of the raise repays borrowings, "
                "which lifts earnings by removing interest rather than by building anything."
            ),
        ),
    ]


IPOS_2026_10_08 = _for_08()


LEAD_09 = (
    "Friday 9 October, written at 10:00. "
    "<strong>The market reverted to a Downtrend overnight and the grey market "
    "repriced both issues within a session.</strong> HD Fire Protect&rsquo;s premium fell "
    "from &#8377;80 to <strong>&#8377;55 &mdash; 29.5% to 20.3%</strong> &mdash; and Jio "
    "Platform&rsquo;s from &#8377;185 to &#8377;177. "
    "Nifty breached 22,217.30 intraday on Thursday and printed a fresh 52-week low of "
    "22,179.90; MarketSmith moved the status back to Downtrend this morning. "
    "<strong>This matters more for HD Fire than for Jio, because HD Fire opens on "
    "Monday.</strong> Its entire case was the listing pop &mdash; 40.7&times; FY26 earnings "
    "for 6.4% profit growth, 100% offer for sale, the company receives nothing &mdash; and the "
    "pop estimate has just fallen by a third before a single bid is placed. "
    "<strong>Held:</strong> nothing in equities. Nothing is open for application today."
)

FOOTNOTE_09 = (
    "<strong>A premium that moves 9.2 points in one session is telling you how much of it "
    "was sentiment.</strong> Nothing about HD Fire Protect changed yesterday: same band, same "
    "promoters selling, same 30.75% margin, same forty times earnings. What changed was the "
    "market, and a fifth of the expected listing gain went with it. That is worth holding "
    "against the number on the morning it opens, when the grey market will quote something "
    "again and it will feel like information. "
    "<strong>The anchor book on Monday is the first verifiable thing on this issue</strong>, "
    "and it is also where this page has been wrong four times in a row &mdash; flagging thin "
    "institutional demand as decisive and watching the issue run. So: read the anchor "
    "allocation, read the QIB number on day two, quote both, forecast neither."
)


def _for_09() -> list[IPO]:
    """The Downtrend reprices both premiums; HD Fire opens Monday."""
    return [
        IPO(
            name="HD Fire Protect", call="MONDAY — and the case got thinner overnight",
            tone="warn",
            dates="13–15 Oct · anchors 12 Oct · allotment 16 Oct · lists 21 Oct",
            band="₹258–271", size="₹712 Cr at the top of the band",
            split="100% OFS — 2.62 Cr shares, both sellers are the promoters",
            gmp="₹55", gmp_pct=20.3, expected="~+18%",
            apply_as="Retail if at all — ₹14,905 at 55 shares",
            horizon="Listing-day sell. At 40.7× for 6.4% growth there is no hold case.",
            book="anchors Monday 12 Oct · opens 13 Oct",
            flags=(("GMP ₹80 → ₹55 in one session", "fail"),
                   ("opens into a Downtrend", "fail"),
                   ("100% OFS — nothing to the company", "fail"),
                   ("40.7× FY26 for 6.4% PAT growth", "fail"),
                   ("EBITDA margin 30.75%", "pass"),
                   ("anchor book Monday — the first verifiable number", "warn")),
            stats=(("GMP yesterday", "₹80 · 29.5%"), ("GMP today", "₹55 · 20.3%"),
                   ("P/E post", "40.7×"), ("market cap", "₹4,749 Cr"),
                   ("FY26 revenue", "₹489.28 Cr"), ("FY26 PAT", "₹116.79 Cr"),
                   ("PAT growth", "+6.4%"), ("retail min", "₹14,905")),
            note=(
                "Nothing about the company changed yesterday. Same band, same promoters "
                "selling the whole of it, same 30.75% margin, same forty times earnings for "
                "single-digit growth. What changed was the market, and a fifth of the "
                "expected listing gain went with it. "
                "<strong>An issue whose only case is the pop is exactly the issue a "
                "Downtrend damages most.</strong> The valuation argument was already "
                "uncomfortable and it has not improved; what has gone is the compensation "
                "for taking it. "
                "No call until the anchor allocation prints on Monday. If the premium keeps "
                "sliding into the open, the honest answer is to skip it &mdash; this page "
                "does not need to own every issue it has written about."
            ),
        ),
        IPO(
            name="Jio Platform", call="WAITING — band still unpublished, two weeks out",
            tone="warn",
            dates="21–23 Oct · allotment 26 Oct · lists 28 Oct",
            band="still unpublished · reports now conflict: ₹1,150–1,220 or ₹1,350–1,450",
            size="~₹33,000 Cr", split="100% fresh, no OFS — up to 27 Cr shares, FV ₹10",
            gmp="₹177", gmp_pct=14.5, expected="~+12%",
            apply_as="Retail — allotment is plausible at this size",
            horizon="Undecided. The band is the whole decision and it is not out.",
            book="opens 21 Oct · DRHP 19 Jun 2026",
            flags=(("no OFS — every rupee goes in", "pass"),
                   ("51.9% EBITDA margin", "pass"),
                   ("GMP ₹185 → ₹177", "warn"),
                   ("band reports now disagree by 18%", "warn"),
                   ("₹27,500 Cr of it repays debt", "warn")),
            stats=(("FY26 revenue", "₹1,46,885 Cr"), ("FY26 EBITDA", "₹76,255 Cr"),
                   ("EBITDA margin", "51.9%"), ("FY26 PAT", "₹30,049 Cr"),
                   ("PAT growth", "+15.1%"), ("subscribers", "524.4 M"),
                   ("ARPU", "₹214/mo"), ("GMP", "₹177")),
            note=(
                "The premium gave back a little with the market, which is the least "
                "interesting thing about it. The band is the issue. Reports that said "
                "&#8377;1,150&ndash;1,220 on Monday now also say "
                "&#8377;1,350&ndash;1,450 &mdash; an eighteen percent spread between "
                "sources on the single number that decides this, and at the higher end "
                "today&rsquo;s &#8377;177 is 12.6% rather than 14.5%. "
                "Two weeks out, with nothing official, the correct position is to hold the "
                "fundamental work done on 7 October and wait. Reliance fell 2.46% on "
                "Thursday, the heaviest single drag on the index, three weeks before "
                "floating its own subsidiary; that is worth watching without being read as "
                "a signal."
            ),
        ),
    ]


IPOS_2026_10_09 = _for_09()


LEAD_12 = (
    "Monday 12 October, written at 10:15. "
    "<strong>The board went from two names to seven over the weekend, and Jio&rsquo;s band is "
    "finally real.</strong> &#8377;1,065&ndash;1,119, raising about &#8377;30,213 Cr, lot of 13 "
    "shares at &#8377;14,547, anchors 19 October. "
    "<strong>That is below the &#8377;1,150&ndash;1,220 the early reports carried and far below "
    "the &#8377;1,350&ndash;1,450 one source ran last week</strong>, so the valuation is better "
    "than the work on this page assumed on 7 October &mdash; which is the right direction for a "
    "rumour to have been wrong in. "
    "<strong>HD Fire Protect takes anchors today and opens tomorrow</strong>, and its premium "
    "recovered with Friday&rsquo;s market: &#8377;55 back to <strong>&#8377;86, 31.7%</strong>, "
    "above where it was before Thursday&rsquo;s fall. "
    "And five more open together on 15 October &mdash; Bonfiglioli, Tonbo Imaging, Zetwerk, "
    "Sahjanand Medical and Fusion CX &mdash; with bands announced today. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_12 = (
    "<strong>Seven mainboard issues in one week, into a market MarketSmith classes as a "
    "Downtrend, is itself the story.</strong> Jio alone takes &#8377;30,213 Cr and Zetwerk "
    "&#8377;5,000 Cr; that money is drawn out of the same pool that has just seen four "
    "consecutive weekly falls in forex reserves and &#8377;12,943 Cr of foreign selling in a "
    "single session. A primary-market rush is not usually what a weak secondary market needs, "
    "and the sequencing matters for us: whatever is decided about HD Fire tomorrow is decided "
    "before any of the five that follow has shown a book. "
    "<strong>What this page does not yet have on those five is their accounts</strong>, and it "
    "will not pretend otherwise. The structures are known and they are the half that cannot be "
    "dressed: Bonfiglioli is <em>100% OFS</em> by its Italian parent, Tonbo is an OFS of up to "
    "1.22 Cr shares, Zetwerk is mixed &mdash; &#8377;2,600 Cr fresh against an OFS of 9.68 Cr "
    "shares. Revenue, profit and the multiples come before any call on them, and that work is "
    "owed by Wednesday morning, not Thursday."
)


def _for_12() -> list[IPO]:
    """Jio prices; HD Fire takes anchors; five more arrive for the 15th."""
    return [
        IPO(
            name="HD Fire Protect", call="ANCHORS TODAY, OPENS TOMORROW — decide on the book",
            tone="warn",
            dates="13–15 Oct · anchors today · allotment 16 Oct · lists 21 Oct",
            band="₹258–271", size="₹712 Cr at the top of the band",
            split="100% OFS — 2.62 Cr shares, both sellers are the promoters",
            gmp="₹86", gmp_pct=31.7, expected="~+29%",
            apply_as="Retail — ₹14,905 at 55 shares",
            horizon="Listing-day sell. At 40.7× for 6.4% growth there is no hold case.",
            book="anchors today · opens 13 Oct",
            flags=(("GMP recovered ₹55 → ₹86", "pass"),
                   ("EBITDA margin 30.75%", "pass"),
                   ("100% OFS — nothing to the company", "fail"),
                   ("40.7× FY26 for 6.4% PAT growth", "fail"),
                   ("opens into a Downtrend", "warn"),
                   ("five more issues open three days later", "warn")),
            stats=(("GMP 9 Oct", "₹55 · 20.3%"), ("GMP today", "₹86 · 31.7%"),
                   ("P/E post", "40.7×"), ("market cap", "₹4,749 Cr"),
                   ("FY26 revenue", "₹489.28 Cr"), ("FY26 PAT", "₹116.79 Cr"),
                   ("PAT growth", "+6.4%"), ("retail min", "₹14,905")),
            note=(
                "The premium has now been &#8377;0, &#8377;80, &#8377;55 and &#8377;86 in four "
                "sessions, tracking the market rather than the company &mdash; which is the "
                "clearest evidence available that it is a sentiment number and not a forecast. "
                "Nothing in the accounts has moved: forty times earnings for 6.4% profit "
                "growth, with both sellers the promoters and the company receiving none of the "
                "&#8377;712 Cr. "
                "<strong>The anchor allocation prints today and it is the first verifiable "
                "number this issue has produced.</strong> Read it, and read the QIB book on day "
                "two. This page called thin institutional demand decisive four times in "
                "September and was wrong four times; the lesson taken was to quote those "
                "numbers rather than forecast from them, and that still holds when the premium "
                "is rising."
            ),
        ),
        IPO(
            name="Jio Platform", call="BAND IS OUT — and it came in below the rumours",
            tone="warn",
            dates="21–23 Oct · anchors 19 Oct · allotment 26 Oct · lists 28 Oct",
            band="₹1,065–1,119", size="~₹30,213 Cr",
            split="100% fresh, no OFS — up to 27 Cr shares, FV ₹10",
            gmp="₹172", gmp_pct=15.4, expected="~+13%",
            apply_as="Retail — 13 shares, ₹14,547. Quota 50% QIB / 35% retail / 15% HNI",
            horizon="Worth deciding properly now that the number exists.",
            book="anchors 19 Oct · opens 21 Oct",
            flags=(("band below the ₹1,150–1,220 reports", "pass"),
                   ("no OFS — every rupee goes in", "pass"),
                   ("51.9% EBITDA margin", "pass"),
                   ("35% retail quota on a ₹30,213 Cr issue", "pass"),
                   ("₹27,500 Cr of it repays debt", "warn"),
                   ("ARPU grew under 4% on 524 M subscribers", "warn")),
            stats=(("band", "₹1,065–1,119"), ("raise", "~₹30,213 Cr"),
                   ("lot", "13 sh · ₹14,547"), ("FY26 revenue", "₹1,46,885 Cr"),
                   ("EBITDA margin", "51.9%"), ("FY26 PAT", "₹30,049 Cr"),
                   ("PAT growth", "+15.1%"), ("GMP", "₹172 · 15.4%")),
            note=(
                "<strong>The band is the thing this page has been waiting on since 7 October "
                "and it is friendlier than expected.</strong> Reports carried "
                "&#8377;1,150&ndash;1,220 and one ran &#8377;1,350&ndash;1,450; it priced at "
                "&#8377;1,065&ndash;1,119. On FY26 profit of &#8377;30,049 Cr that is a "
                "materially lower multiple than the ~43&times; the earlier valuation talk "
                "implied &mdash; the exact figure depends on the final share count, which the "
                "RHP settles, and this page will state it once rather than estimate it twice. "
                "<strong>What has not changed is where the money goes.</strong> The issue is "
                "entirely fresh, which is the one structural signal that cannot be dressed, but "
                "&#8377;27,500 Cr of roughly &#8377;30,213 Cr repays borrowings. That lifts "
                "earnings by removing interest rather than by building anything, and a "
                "deleveraging deserves a lower multiple than a growth raise, not a higher one. "
                "A 35% retail quota on an issue this size makes allotment genuinely plausible "
                "&mdash; still the strongest practical argument for applying."
            ),
        ),
        IPO(
            name="The 15 October five", call="BANDS TODAY — accounts owed by Wednesday",
            tone="warn",
            dates="15–19 Oct · Bonfiglioli · Tonbo · Zetwerk · Sahjanand Medical · Fusion CX",
            band="announced today", size="Zetwerk ~₹5,000 Cr; others to confirm",
            split="Bonfiglioli 100% OFS · Tonbo OFS 1.22 Cr sh · Zetwerk ₹2,600 Cr fresh + 9.68 Cr OFS",
            gmp="see note", gmp_pct=0.0, expected="—",
            apply_as="Undecided — no accounts read yet",
            horizon="Revisit Wednesday with revenue, profit and the multiples",
            book="opens 15 Oct",
            flags=(("Tonbo GMP 38.6% — highest on the board", "pass"),
                   ("Bonfiglioli 100% OFS by its Italian parent", "fail"),
                   ("Zetwerk is the only one with fresh capital", "pass"),
                   ("no accounts read on any of them", "warn"),
                   ("five issues competing on one day", "warn")),
            stats=(("Tonbo", "band 700 · GMP ₹270 · 38.6%"),
                   ("Bonfiglioli", "band 586 · GMP ₹175 · 29.9%"),
                   ("Zetwerk", "band 151 · GMP ₹30 · 19.9%"),
                   ("Sahjanand Medical", "band 344 · GMP ₹40 · 11.6%"),
                   ("Fusion CX", "band 289 · GMP ₹25 · 8.7%")),
            note=(
                "One card rather than five, because five calls cannot honestly be made from "
                "grey-market quotes and a structure. <strong>What is known is the structure, "
                "and it is the half that matters most to this page.</strong> Bonfiglioli is a "
                "pure secondary sale by Bonfiglioli S.p.A. of Italy &mdash; 4.32 Cr shares, the "
                "company receives nothing. Tonbo is an offer for sale of up to 1.22 Cr shares. "
                "Zetwerk is the only one raising real capital: &#8377;2,600 Cr fresh against an "
                "offer for sale of 9.68 Cr shares. "
                "<strong>The premiums already disagree sharply</strong> &mdash; 38.6% on Tonbo "
                "against 8.7% on Fusion CX &mdash; which is a spread worth understanding rather "
                "than following. Revenue, profit, margin and the multiple come before any call, "
                "and that work is owed Wednesday morning, with two clear sessions before the "
                "books open."
            ),
        ),
    ]


IPOS_2026_10_12 = _for_12()


LEAD_13 = (
    "Tuesday 13 October, written at 09:20. "
    "<strong>HD Fire Protect opens this morning, and the anchor book answered the "
    "question this page set yesterday.</strong> It called the anchor allocation &ldquo;the "
    "first verifiable number this issue has produced&rdquo;, and it came in strong: "
    "<strong>&#8377;213.11 Cr from 25 funds, allotted at the top of the band at "
    "&#8377;271</strong>, with Indian mutual funds taking 71.88% of it. That is the full "
    "anchor allocation taken up, by domestic institutions, at the highest price on offer. "
    "<strong>The other half of the board moved the opposite way overnight.</strong> Tonbo "
    "Imaging&rsquo;s premium went from &#8377;270 to <strong>&#8377;427, a 61% expected "
    "listing gain</strong>, while Zetwerk&rsquo;s halved from &#8377;30 to &#8377;16 and "
    "Bonfiglioli, Sahajanand and Fusion CX all softened. One name is being bid and the rest "
    "are being sold. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_13 = (
    "<strong>What the anchor book does and does not settle.</strong> It settles that "
    "institutions would pay &#8377;271 for HD Fire in this tape &mdash; 25 of them, mostly "
    "domestic mutual funds, taking the whole allocation at the ceiling rather than the "
    "floor. It does not settle the valuation, which is unchanged: forty times earnings for "
    "6.4% profit growth, margins compressing, a cash conversion cycle stretched to 102 days, "
    "and both sellers the promoters taking the entire &#8377;712 Cr out. "
    "<strong>This page has been wrong about institutional demand before</strong> &mdash; it "
    "called thin QIB books decisive four times in September and was wrong four times &mdash; "
    "and the lesson taken was to quote those numbers rather than forecast from them. So: the "
    "number is strong, it is quoted, and it is a reason to apply rather than a reason to "
    "hold. "
    "<strong>Tonbo is the one to be careful about.</strong> A 61% grey-market premium on an "
    "issue that is <em>entirely</em> an offer for sale, at a &#8377;4,010 Cr valuation, with "
    "no published profit figure this page has yet read, is not a bargain being spotted. It is "
    "a theme being bought &mdash; defence, in the week Goodluck India was named sole supplier "
    "of 155&nbsp;mm shells and Zen Technologies chased a &#8377;6,000 Cr tender. The accounts "
    "are owed tomorrow, before the 15 October books open, and no call belongs on it until "
    "they are read."
)


def _for_13() -> list[IPO]:
    """HD Fire opens on a full anchor book; Tonbo's premium runs away."""
    return [
        IPO(
            name="HD Fire Protect", call="OPEN TODAY — apply retail, sell on listing",
            tone="good",
            dates="13–15 Oct · allotment 16 Oct · lists 21 Oct",
            band="₹258–271", size="₹712.31 Cr, entirely OFS",
            split="100% OFS — 2,62,84,500 shares, both sellers are the promoters",
            gmp="₹86", gmp_pct=31.7, expected="~+29%",
            apply_as="Retail — ₹14,905 at 55 shares. One lot.",
            horizon="Listing-day sell. Nothing here supports a hold at 40×.",
            book="opens today · closes 15 Oct",
            flags=(("anchor book FULL at the top band", "pass"),
                   ("25 funds, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("EBITDA margin 30.75%", "pass"),
                   ("40.7× FY26 for 6.4% PAT growth", "fail"),
                   ("100% OFS — company receives nothing", "fail"),
                   ("cash conversion cycle out to 102 days", "warn"),
                   ("Middle East export exposure, Brent above $100", "warn")),
            stats=(("anchor raise", "₹213.11 Cr"), ("anchor price", "₹271 — top of band"),
                   ("anchor funds", "25"), ("domestic MF share", "71.88%"),
                   ("GMP", "₹86 · 31.7%"), ("P/E post", "40.7×"),
                   ("FY26 PAT", "₹116.79 Cr"), ("PAT growth", "+6.4%"),
                   ("RoCE", "40.33%"), ("retail min", "₹14,905")),
            note=(
                "<strong>Yesterday this page said the anchor allocation was the first "
                "verifiable number the issue would produce, and to read it rather than "
                "forecast from it. Here it is.</strong> &#8377;213.11 Cr, which is the full "
                "anchor allocation, placed with 25 funds at &#8377;271 &mdash; the top of "
                "the band, not the bottom &mdash; and 71.88% of it went to Indian mutual "
                "funds rather than to foreign money that can leave on Thursday. Bajaj Life "
                "and Allianz Global are named among them. "
                "<strong>That is a genuine institutional vote, and it is the only hard "
                "evidence this issue has.</strong> It does not touch the arithmetic: 40.7 "
                "times earnings for 6.4% profit growth is still a PEG above six, margins "
                "still compressed from 31.89% to 30.75%, working capital still deteriorated "
                "to a 102-day cycle, and the company still receives none of the "
                "&#8377;712 Cr because both sellers are the promoters. "
                "<strong>The business is genuinely good</strong> &mdash; RoE 30%, RoCE 40%, "
                "a 23% net margin in a niche it leads &mdash; which is why it will find "
                "buyers. The price is what is wrong, and a listing pop is the only part of "
                "it worth owning. <strong>One lot, retail, sold on day one.</strong> Do not "
                "scale to sHNI: &#8377;2 L into a forty-times stock with decelerating "
                "earnings, in a market MarketSmith still calls a Downtrend, is a position "
                "rather than a cheap option."
            ),
        ),
        IPO(
            name="Tonbo Imaging India", call="PREMIUM RAN 58% OVERNIGHT — accounts owed before any call",
            tone="warn",
            dates="15–19 Oct", band="₹665–700", size="₹852 Cr",
            split="100% OFS — 1.22 Cr shares, no fresh capital",
            gmp="₹427", gmp_pct=61.0, expected="not forecast — see note",
            apply_as="Undecided. No published profit figure read yet.",
            horizon="Revisit tomorrow with the accounts, before the book opens",
            book="opens 15 Oct",
            flags=(("GMP ₹270 → ₹427 in one session", "warn"),
                   ("highest premium on the board by 29pp", "warn"),
                   ("100% OFS at a ₹4,010 Cr valuation", "fail"),
                   ("no published PAT figure read yet", "fail"),
                   ("defence theme bid hard this week", "warn")),
            stats=(("band", "₹665–700"), ("raise", "₹852 Cr"),
                   ("valuation sought", "₹4,010 Cr"), ("shares offered", "1.22 Cr"),
                   ("GMP 12 Oct", "₹270 · 38.6%"), ("GMP today", "₹427 · 61.0%"),
                   ("fresh capital", "nil")),
            note=(
                "<strong>A premium that moves 58% in one session is information about "
                "sentiment, not about the company</strong>, and the company has not "
                "published anything in that window. Nothing changed at Tonbo overnight; what "
                "changed is that defence became the thing to own, in the same week Goodluck "
                "India&rsquo;s arm was named sole supplier of 155&nbsp;mm M1A4 shells to "
                "Munitions India and Zen Technologies was reported chasing &#8377;6,000 Cr "
                "of a &#8377;20,000 Cr tender. "
                "<strong>The structure is the part that is knowable and it is the "
                "unflattering half.</strong> &#8377;852 Cr, every rupee of it an offer for "
                "sale of 1.22 Cr shares, at a valuation of &#8377;4,010 Cr. The company "
                "raises nothing and builds nothing; existing holders are selling into "
                "enthusiasm. That is not disqualifying on its own &mdash; HD Fire is the "
                "same shape and this page is applying for it &mdash; but HD Fire has "
                "published accounts and an anchor book, and Tonbo has neither here yet. "
                "<strong>No call until the revenue, the profit and the multiple are read.</strong> "
                "That work is owed tomorrow, which leaves one clear session before the book "
                "opens on the 15th. A 61% premium is a reason to hurry it, not a reason to "
                "skip it."
            ),
        ),
        IPO(
            name="The rest of the 15 October book", call="SOFTENING WHILE TONBO RUNS",
            tone="warn",
            dates="15–19 Oct · Bonfiglioli · Zetwerk · Sahajanand · Fusion CX",
            band="see stats", size="Zetwerk ~₹5,000 Cr; others to confirm",
            split="Bonfiglioli 100% OFS · Zetwerk ₹2,600 Cr fresh + 9.68 Cr OFS",
            gmp="all four fell", gmp_pct=0.0, expected="—",
            apply_as="Undecided — accounts owed tomorrow",
            horizon="With Tonbo, tomorrow",
            book="opens 15 Oct",
            flags=(("Zetwerk GMP halved, 30 → 16", "fail"),
                   ("Bonfiglioli 175 → 155", "warn"),
                   ("Sahajanand 40 → 36", "warn"),
                   ("Fusion CX 25 → 20", "warn"),
                   ("Zetwerk is the only one raising real capital", "pass")),
            stats=(("Bonfiglioli", "586 · ₹155 · 26.5%"),
                   ("Zetwerk", "151 · ₹16 · 10.6%"),
                   ("Sahajanand Medical", "344 · ₹36 · 10.5%"),
                   ("Fusion CX", "289 · ₹20 · 6.9%"),
                   ("Tonbo, for contrast", "700 · ₹427 · 61.0%")),
            note=(
                "<strong>Every one of these four fell overnight while Tonbo rose 58%.</strong> "
                "That is the useful observation on the day: this is not a rising tide under "
                "the primary market, it is money concentrating into one name and leaving the "
                "others. Zetwerk is the sharpest &mdash; its premium halved, from &#8377;30 "
                "to &#8377;16 &mdash; and it is the <em>only</em> issue in the whole cluster "
                "raising real capital, &#8377;2,600 Cr of fresh money against an offer for "
                "sale of 9.68 Cr shares. "
                "The grey market is paying up for the pure secondary sale and marking down "
                "the one that funds a business, which is worth noticing even though it "
                "decides nothing. <strong>Accounts on all four are owed tomorrow</strong>, "
                "with Tonbo, before the books open on the 15th."
            ),
        ),
        IPO(
            name="Jio Platform", call="BAND HOLDING — premium firm while the rest soften",
            tone="warn",
            dates="21–23 Oct · anchors 19 Oct · lists 28 Oct",
            band="₹1,065–1,119", size="~₹30,213 Cr",
            split="100% fresh, no OFS",
            gmp="₹182", gmp_pct=16.3, expected="~+14%",
            apply_as="Retail — 13 shares, ₹14,547. 35% retail quota.",
            horizon="Decide at the anchor book on 19 October",
            book="anchors 19 Oct",
            flags=(("GMP firmed 172 → 182 while four others fell", "pass"),
                   ("no OFS — every rupee goes in", "pass"),
                   ("35% retail quota makes allotment plausible", "pass"),
                   ("₹27,500 Cr of it repays debt", "warn"),
                   ("₹30,213 Cr drawn from a thin market", "warn")),
            stats=(("band", "₹1,065–1,119"), ("raise", "~₹30,213 Cr"),
                   ("lot", "13 sh · ₹14,547"), ("GMP 12 Oct", "₹172 · 15.4%"),
                   ("GMP today", "₹182 · 16.3%"), ("anchors", "19 Oct")),
            note=(
                "Quietly the second-best news on the board: <strong>Jio&rsquo;s premium "
                "firmed from &#8377;172 to &#8377;182 on a night when four of the six other "
                "issues fell.</strong> On a &#8377;30,213 Cr issue that is harder to move "
                "than on a small one, so it carries more weight than the percentage suggests. "
                "The case is unchanged from yesterday: entirely fresh capital, which is the "
                "one structural signal that cannot be dressed, but &#8377;27,500 Cr of it "
                "repays borrowings rather than building anything &mdash; a deleveraging "
                "deserves a lower multiple than a growth raise, not a higher one. The 35% "
                "retail quota remains the strongest practical argument for applying. "
                "<strong>Its own anchor book prints on 19 October</strong>, and on the "
                "evidence of HD Fire this morning, that is the number to decide on."
            ),
        ),
    ]


IPOS_2026_10_13 = _for_13()


LEAD_14 = (
    "Wednesday 14 October, written at 10:05. "
    "<strong>Tonbo Imaging&rsquo;s accounts are in, and they are the opposite of what a 69% "
    "grey-market premium implies.</strong> Revenue fell 22.7% in FY26, profit fell 30%, "
    "operating cash flow was negative in both FY25 and FY26 <em>while the company reported "
    "profits</em>, working capital stretched from 152 days to 517, and Q1 FY27 closed with a "
    "&#8377;17.74 Cr loss. At &#8377;700 that is about <strong>79 times earnings that are "
    "going backwards</strong>. This page owed these numbers today and they arrive as a "
    "refusal. "
    "<strong>HD Fire&rsquo;s first real book is also in</strong>, and it is good: "
    "<strong>4.62&times; on day one</strong>, with HNI at 11.38&times; and retail at "
    "3.78&times;. It closes tomorrow. "
    "<strong>Fusion CX opened today</strong> &mdash; its dates moved from 15&ndash;19 to "
    "14&ndash;16 October, so the window is live now rather than next week. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_14 = (
    "<strong>The two issues on this page are the same structure and opposite businesses, and "
    "the grey market has them the wrong way round.</strong> Both are 100% offers for sale by "
    "existing holders; neither company receives a rupee. HD Fire earns 30% on equity and 40% "
    "on capital, converts its profit into cash, and asks 40.7&times; for 6.4% growth &mdash; "
    "expensive, which is why this page says sell it on listing rather than hold it. Tonbo "
    "asks roughly 79&times; for earnings that fell 30%, having burned cash in both of the "
    "last two years and with a quarter of losses already on the board. The premium on the "
    "second is more than double the premium on the first. "
    "<strong>That is what a theme does to a price.</strong> Defence has been the thing to own "
    "since Goodluck India was named sole supplier of 155&nbsp;mm shells and Zen Technologies "
    "went after a &#8377;20,000 Cr tender, and Tonbo is the only listed-adjacent way to buy "
    "it this week. None of that is in the accounts. "
    "<strong>Four days ago this page wrote that a premium moving 58% in a session is "
    "information about sentiment and not about the company.</strong> The accounts have now "
    "confirmed which of the two it was."
)


def _for_14() -> list[IPO]:
    """Tonbo's accounts arrive and refuse it; HD Fire's book opens strong."""
    return [
        IPO(
            name="Tonbo Imaging India", call="AVOID — 79× for earnings falling 30%",
            tone="bad",
            dates="15–19 Oct", band="₹665–700", size="₹852.18 Cr",
            split="100% OFS — 1,21,74,046 shares. The company receives nothing.",
            gmp="₹485", gmp_pct=69.3, expected="not a forecast — see note",
            apply_as="Do not apply.",
            horizon="No horizon. The accounts refuse it at any holding period.",
            book="opens 15 Oct",
            flags=(("revenue −22.7% in FY26", "fail"),
                   ("PAT −30% in FY26", "fail"),
                   ("Q1 FY27 a ₹17.74 Cr LOSS", "fail"),
                   ("negative operating cash flow FY25 AND FY26", "fail"),
                   ("working capital 152 → 280 → 517 days", "fail"),
                   ("~79× FY26 earnings", "fail"),
                   ("78.6% of FY26 revenue in H2", "warn"),
                   ("gross margin 51.05%", "pass")),
            stats=(("FY25 revenue", "₹469.08 Cr"), ("FY26 revenue", "₹362.65 Cr"),
                   ("FY25 PAT", "₹72.76 Cr"), ("FY26 PAT", "₹50.88 Cr"),
                   ("FY26 EBITDA", "₹104.62 Cr"), ("EBITDA margin", "28.85%"),
                   ("WC days FY26", "517"), ("Q1 FY27", "−₹17.74 Cr"),
                   ("diluted EPS FY26", "₹8.88"), ("P/E at ₹700", "~79×"),
                   ("GMP", "₹485 · 69.3%")),
            note=(
                "<strong>This page said on 13 October that no call belonged on Tonbo until "
                "the revenue, the profit and the multiple were read, and that a 61% premium "
                "was a reason to hurry that rather than skip it. Here they are, and they are "
                "bad in every line that matters.</strong> "
                "Revenue did not slow, it <em>fell</em>: &#8377;469.08 Cr to &#8377;362.65 Cr, "
                "down 22.7%. Profit fell 30%, from &#8377;72.76 Cr to &#8377;50.88 Cr. "
                "<strong>Q1 FY27 is already a loss of &#8377;17.74 Cr</strong>, so the "
                "decline is continuing into the year being sold. "
                "<strong>The cash tells the sharper story.</strong> Operating cash flow was "
                "negative in <em>both</em> FY25 and FY26 while the company reported profits "
                "in both &mdash; profit that does not become cash &mdash; and working-capital "
                "days went 152, then 280, then 517. A business taking seventeen months to "
                "convert working capital is financing its customers, and 78.6% of FY26 "
                "revenue landing in the second half says the order flow is lumpy as well. "
                "<strong>At &#8377;700 the multiple is about 79 times earnings that are going "
                "backwards</strong>, for a &#8377;4,010 Cr valuation, in an issue where every "
                "rupee of the &#8377;852 Cr goes to existing holders and none to the company. "
                "The grey market is bidding +69%. The accounts and the premium are telling "
                "opposite stories and only one of them is audited."
            ),
        ),
        IPO(
            name="HD Fire Protect", call="BOOK IS STRONG — closes tomorrow, call stands",
            tone="good",
            dates="13–15 Oct · closes tomorrow · lists 21 Oct",
            band="₹258–271", size="₹712.31 Cr, entirely OFS",
            split="100% OFS — 2,62,84,500 shares, both sellers are the promoters",
            gmp="₹91", gmp_pct=33.6, expected="~+31%",
            apply_as="Retail — ₹14,905 at 55 shares. One lot.",
            horizon="Listing-day sell, unchanged.",
            book="day 1: 4.62× · QIB 1.04× · HNI 11.38× · retail 3.78×",
            flags=(("day-1 book 4.62× overall", "pass"),
                   ("HNI 11.38× on day one", "pass"),
                   ("anchor FULL at the top band, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("40.7× for 6.4% PAT growth", "fail"),
                   ("100% OFS", "fail"),
                   ("QIB only 1.04× so far", "warn")),
            stats=(("subscribed day 1", "4.62×"), ("QIB", "1.04×"),
                   ("HNI", "11.38×"), ("retail", "3.78×"),
                   ("anchor", "₹213.11 Cr at ₹271"), ("GMP", "₹91 · 33.6%"),
                   ("P/E post", "40.7×"), ("closes", "15 Oct")),
            note=(
                "<strong>The exchange book is the half that can be verified, and day one came "
                "in at 4.62&times;.</strong> HNI at 11.38&times; is the number doing the work; "
                "retail at 3.78&times; on the first day of a three-day window is comfortable. "
                "QIB at 1.04&times; looks thin but is not: institutions routinely bid on the "
                "final day, and the anchor book &mdash; &#8377;213.11 Cr placed at the top of "
                "the band, 71.88% of it with domestic mutual funds &mdash; already showed up. "
                "<strong>Nothing changes in the call.</strong> It is still 40.7 times for 6.4% "
                "profit growth, still entirely a promoter exit, and the business underneath "
                "it is still genuinely good: 30% on equity, 40% on capital, and profit that "
                "becomes cash &mdash; which, set beside Tonbo on this same page, is worth "
                "saying out loud. One lot, retail, sold on listing. The window shuts tomorrow."
            ),
        ),
        IPO(
            name="Fusion CX", call="OPENED TODAY — dates moved forward",
            tone="warn",
            dates="14–16 Oct (was 15–19)", band="₹289", size="to confirm",
            split="to confirm", gmp="₹34", gmp_pct=11.8, expected="~+9%",
            apply_as="Undecided — accounts not read",
            horizon="—",
            book="open now",
            flags=(("dates moved 15–19 → 14–16 Oct", "warn"),
                   ("GMP 20 → 34 overnight", "pass"),
                   ("lowest premium on the board", "warn"),
                   ("accounts not read", "fail")),
            stats=(("band", "289"), ("GMP 13 Oct", "₹20 · 6.9%"),
                   ("GMP today", "₹34 · 11.8%"), ("window", "14–16 Oct")),
            note=(
                "<strong>Flagged because the dates moved and this page had it down for next "
                "week.</strong> It opened this morning, not on the 15th, so the window is "
                "live now and shuts on Friday. Its premium rose from &#8377;20 to &#8377;34 "
                "overnight along with everything else on the board, which followed "
                "yesterday&rsquo;s 1.60% move in the Nifty rather than anything "
                "company-specific. <strong>No call: the accounts have not been read</strong>, "
                "and with Tonbo having just demonstrated what a premium can conceal, a number "
                "going up is not a reason to apply."
            ),
        ),
        IPO(
            name="Jio Platform", call="FIRMING — anchors Monday",
            tone="warn",
            dates="21–23 Oct · anchors 19 Oct · lists 28 Oct",
            band="₹1,065–1,119", size="~₹30,213 Cr",
            split="100% fresh, no OFS",
            gmp="₹218", gmp_pct=19.5, expected="~+17%",
            apply_as="Retail — 13 shares, ₹14,547",
            horizon="Decide on the anchor book, 19 October",
            book="anchors 19 Oct",
            flags=(("GMP 172 → 182 → 218 over three sessions", "pass"),
                   ("no OFS — the only one on the board", "pass"),
                   ("35% retail quota", "pass"),
                   ("₹27,500 Cr of it repays debt", "warn")),
            stats=(("band", "₹1,065–1,119"), ("GMP 12 Oct", "₹172 · 15.4%"),
                   ("GMP 13 Oct", "₹182 · 16.3%"), ("GMP today", "₹218 · 19.5%"),
                   ("lot", "13 sh · ₹14,547"), ("anchors", "19 Oct")),
            note=(
                "Three sessions of a rising premium &mdash; &#8377;172, &#8377;182, "
                "&#8377;218 &mdash; on a &#8377;30,213 Cr issue, which takes far more money to "
                "move than any other name here. <strong>It remains the only issue on the "
                "board raising fresh capital rather than paying an existing holder.</strong> "
                "That it also spends &#8377;27,500 Cr of the raise repaying borrowings is the "
                "standing caveat, and a deleveraging earns a lower multiple than a growth "
                "raise, not a higher one. The anchor book prints Monday 19 October, and on "
                "the evidence of HD Fire this week that is the number worth waiting for."
            ),
        ),
    ]


IPOS_2026_10_14 = _for_14()


LEAD_15 = (
    "Thursday 15 October, written at 11:20. "
    "<strong>Four issues opened this morning, HD Fire closes tonight, and with every "
    "prospectus now read the grey market has the cluster ranked almost exactly upside "
    "down.</strong> The highest premium on the board, Tonbo at 71.4%, belongs to the only "
    "company here whose revenue and profit both <em>fell</em>. The best set of accounts "
    "&mdash; Bonfiglioli, growing 29%, debt-free, 34% on capital &mdash; carries 30%. The "
    "loss-making one carries 15%. "
    "<strong>HD Fire is 16.51&times; subscribed with one session left</strong>, NII at "
    "48.71&times; and retail at 11.36&times;, which is a strong book and also means retail "
    "allotment is now roughly a one-in-twelve lottery. "
    "<strong>Held:</strong> nothing in equities."
)

FOOTNOTE_15 = (
    "<strong>Four prospectuses, one pattern.</strong> Ranked by what the accounts say, the "
    "order is Bonfiglioli, then Sahajanand, then Tonbo and Zetwerk nowhere. Ranked by what "
    "the grey market will pay, it is Tonbo, then Bonfiglioli, then Zetwerk, then Sahajanand. "
    "The only name the two orderings agree on is Bonfiglioli, and it is the one with no "
    "story attached &mdash; an Italian parent selling down a gearbox manufacturer. "
    "<strong>Tonbo is the live test of this page&rsquo;s judgement and it is going the wrong "
    "way so far.</strong> The premium was 38.6% when the accounts were still unread, 61% "
    "when this page said no call belonged on it, 69.3% when the accounts arrived and the "
    "call became avoid, and 71.4% this morning. Nothing in the filings has changed: revenue "
    "down 22.7%, profit down 30%, a &#8377;17.74 Cr loss in Q1 FY27, operating cash flow "
    "negative in both of the last two years while profits were reported, and working capital "
    "out to 517 days. The call stands on those numbers and will be wrong if it lists well. "
    "Recording that now, before the print, is the only way the record is worth anything."
)


def _for_15() -> list[IPO]:
    """Four open, HD Fire closes, and the premiums invert the accounts."""
    return [
        IPO(
            name="HD Fire Protect", call="FINAL DAY — book strong, allotment now a lottery",
            tone="good",
            dates="13–15 Oct · CLOSES TODAY · allotment 16 Oct · lists 21 Oct",
            band="₹258–271", size="₹712.31 Cr, entirely OFS",
            split="100% OFS — both sellers are the promoters",
            gmp="₹89", gmp_pct=32.8, expected="~+31%",
            apply_as="Retail — ₹14,905 at 55 shares. One lot, today.",
            horizon="Listing-day sell. Unchanged since the anchor book.",
            book="day 2: 16.51× · QIB 1.49× · NII 48.71× · retail 11.36×",
            flags=(("16.51× with a session still to run", "pass"),
                   ("NII 48.71×", "pass"),
                   ("anchor FULL at the top band, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("retail 11.36× — allotment ~1 in 12", "warn"),
                   ("QIB only 1.49× going into the last day", "warn"),
                   ("40.7× for 6.4% PAT growth", "fail")),
            stats=(("day 1", "4.62×"), ("day 2", "16.51×"),
                   ("QIB", "1.49×"), ("NII", "48.71×"), ("retail", "11.36×"),
                   ("anchor", "₹213.11 Cr at ₹271"), ("GMP", "₹89 · 32.8%"),
                   ("P/E post", "40.7×")),
            note=(
                "<strong>The book more than tripled on day two</strong>, 4.62&times; to "
                "16.51&times;, with NII doing the lifting at 48.71&times;. Retail at "
                "11.36&times; is the number that changes what applying means: a single lot is "
                "now roughly a one-in-twelve draw, and it will lengthen again today. That is "
                "not a reason to skip &mdash; the expected value of a free option on a 33% "
                "premium is still positive &mdash; but it is a reason not to plan around "
                "receiving shares. "
                "<strong>QIB at 1.49&times; with one session left is the only soft spot</strong>, "
                "and institutions overwhelmingly bid on the final day, so tonight's number is "
                "the one worth reading. The anchor book already answered the question in "
                "advance: &#8377;213.11 Cr placed at the top of the band, 71.88% with domestic "
                "mutual funds. Nothing in the accounts has moved &mdash; 40.7 times for 6.4% "
                "growth, entirely a promoter exit &mdash; so the call is unchanged. One lot, "
                "retail, sold on listing."
            ),
        ),
        IPO(
            name="Bonfiglioli Transmissions", call="THE BEST ACCOUNTS ON THE BOARD",
            tone="good",
            dates="15–19 Oct · opened today",
            band="₹558–586", size="~₹2,534 Cr", split="100% OFS by the Italian parent",
            gmp="₹178", gmp_pct=30.4, expected="~+26%",
            apply_as="Retail — 25 shares, ₹14,650. Retail quota 35%.",
            horizon="Worth a hold case, which nothing else here earns.",
            book="opened today",
            flags=(("PAT +29.2% to ₹148.58 Cr", "pass"),
                   ("revenue +17.9% to ₹1,139.17 Cr", "pass"),
                   ("DEBT-FREE, no borrowings since CY24", "pass"),
                   ("ROCE 24.53% → 34.05%", "pass"),
                   ("H1 FY27 EBITDA ₹223.87 Cr vs ₹176.43 Cr", "pass"),
                   ("~46.3× at the upper band", "warn"),
                   ("100% OFS — the parent is selling", "fail")),
            stats=(("band", "₹558–586"), ("size", "~₹2,534 Cr"),
                   ("market cap", "~₹11,017 Cr"), ("FY26 revenue", "₹1,139.17 Cr"),
                   ("FY26 PAT", "₹148.58 Cr"), ("PAT growth", "+29.2%"),
                   ("ROCE", "34.05%"), ("P/E upper", "~46.3×"),
                   ("GMP", "₹178 · 30.4%"), ("lot", "25 sh · ₹14,650")),
            note=(
                "<strong>Set beside the other three, this is the only one that reads like a "
                "business rather than a theme.</strong> Profit up 29.2%, revenue up 17.9%, "
                "<em>no borrowings at all since CY24</em>, and return on capital employed that "
                "went from 24.53% to 34.05% &mdash; a company earning more on less. H1 FY27 "
                "EBITDA is already &#8377;223.87 Cr against &#8377;176.43 Cr a year earlier, so "
                "the growth is continuing into the year being sold, which is precisely what "
                "Tonbo cannot say. "
                "<strong>It is not cheap and it is still a full exit.</strong> 46.3 times at "
                "the top is a growth multiple, not a bargain, and every rupee of the "
                "&#8377;2,534 Cr goes to Bonfiglioli S.p.A. rather than into the company. "
                "A parent selling a profitable subsidiary at 46&times; is doing something "
                "rational for itself. "
                "But a 29% grower with no debt and 34% on capital is the only name on this "
                "board where holding past the listing is an argument rather than a hope, and "
                "it is carrying less than half Tonbo&rsquo;s premium."
            ),
        ),
        IPO(
            name="Tonbo Imaging India", call="AVOID — the premium is rising, the accounts are not",
            tone="bad",
            dates="15–19 Oct · opened today", band="₹665–700", size="₹852.18 Cr",
            split="100% OFS — the company receives nothing",
            gmp="₹500", gmp_pct=71.4, expected="~+61% implied",
            apply_as="Do not apply.",
            horizon="None.",
            book="opened today",
            flags=(("revenue −22.7% in FY26", "fail"),
                   ("PAT −30% in FY26", "fail"),
                   ("Q1 FY27 a ₹17.74 Cr LOSS", "fail"),
                   ("negative operating cash flow FY25 AND FY26", "fail"),
                   ("working capital 152 → 280 → 517 days", "fail"),
                   ("~79× earnings that are falling", "fail"),
                   ("highest premium on the board", "warn")),
            stats=(("GMP 12 Oct", "38.6%"), ("GMP 13 Oct", "61.0%"),
                   ("GMP 14 Oct", "69.3%"), ("GMP today", "71.4%"),
                   ("FY26 revenue", "₹362.65 Cr (−22.7%)"),
                   ("FY26 PAT", "₹50.88 Cr (−30%)"),
                   ("Q1 FY27", "−₹17.74 Cr"), ("WC days", "517"),
                   ("P/E at ₹700", "~79×")),
            note=(
                "<strong>The premium has gone 38.6%, 61%, 69.3%, 71.4% across four sessions "
                "and not one line of the accounts has changed in that time.</strong> Revenue "
                "fell 22.7%. Profit fell 30%. The first quarter of the year being sold is "
                "already a &#8377;17.74 Cr loss. Operating cash flow was negative in both FY25 "
                "and FY26 while the company reported profits in both, and working capital "
                "stretched from 152 days to 517 &mdash; seventeen months to turn stock and "
                "receivables back into cash. "
                "<strong>What is being bought is the word defence</strong>, in the week "
                "Goodluck India was named sole supplier of 155&nbsp;mm shells and Zen "
                "Technologies went after a &#8377;20,000 Cr tender. Nothing in the filings "
                "participates in that. At &#8377;700 the multiple is roughly 79 times earnings "
                "that are going backwards, for a &#8377;4,010 Cr valuation, in an issue where "
                "every rupee of the &#8377;852 Cr goes to existing holders. "
                "<strong>This call will be wrong if it lists at +60%, and it is recorded "
                "before the print rather than after.</strong>"
            ),
        ),
        IPO(
            name="Zetwerk & Sahajanand", call="ZETWERK LOSS-MAKING · SAHAJANAND EXPENSIVE BUT IMPROVING",
            tone="warn",
            dates="15–19 Oct · both opened today",
            band="Zetwerk ₹151 · Sahajanand ₹344",
            size="Zetwerk ~₹5,000 Cr · Sahajanand to confirm",
            split="Zetwerk ₹2,600 Cr fresh + 9.68 Cr OFS · Sahajanand OFS",
            gmp="₹23 / ₹42", gmp_pct=15.2, expected="~+13% / +12%",
            apply_as="Zetwerk: no. Sahajanand: thin edge at best.",
            horizon="Neither earns a hold.",
            book="opened today",
            flags=(("Zetwerk FY26 LOSS of ₹1,606.17 Cr", "fail"),
                   ("Zetwerk is the only fresh capital on the board", "pass"),
                   ("Zetwerk order book ₹13,062 Cr, 1.39× revenue", "pass"),
                   ("Sahajanand PAT ₹25.15 Cr → ₹69.08 Cr", "pass"),
                   ("Sahajanand ~53× FY26 diluted", "warn"),
                   ("Sahajanand 73.87% of revenue from outside India", "warn")),
            stats=(("Zetwerk FY26 income", "₹16,100.63 Cr"),
                   ("Zetwerk FY26 result", "−₹1,606.17 Cr"),
                   ("Zetwerk order book", "₹13,062.40 Cr"),
                   ("Zetwerk mfg EBITDA margin", "6.56% Q1FY27 vs 4.83%"),
                   ("Sahajanand FY26 revenue", "₹1,210.50 Cr (+18.11%)"),
                   ("Sahajanand FY26 PAT", "₹69.08 Cr (was ₹25.15 Cr)"),
                   ("Sahajanand P/E", "~53×")),
            note=(
                "<strong>Zetwerk is the only issue on this board raising real money and the "
                "only one losing it.</strong> &#8377;16,100.63 Cr of income for a loss of "
                "&#8377;1,606.17 Cr &mdash; a tenth of revenue, burned. The order book at "
                "&#8377;13,062 Cr is genuine and manufacturing EBITDA margin improved to 6.56% "
                "from 4.83%, so the direction is right; the distance is enormous. A business "
                "that must triple its margin to break even is not a listing-day trade and is "
                "not yet an investment. The grey market agrees for once, at 15.2%. "
                "<strong>Sahajanand is the more interesting of the two.</strong> Revenue up "
                "18.11% to &#8377;1,210.50 Cr and profit from &#8377;25.15 Cr to "
                "&#8377;69.08 Cr &mdash; nearly tripled. Cardiac implants sold into 77 "
                "countries, with 73.87% of revenue earned outside India, which is both the "
                "strength and the currency risk. At roughly 53 times it is priced for that "
                "tripling to continue. The 12.2% premium is the lowest on the board, which is "
                "the market saying it does not believe it will."
            ),
        ),
    ]


IPOS_2026_10_15 = _for_15()


LEAD_16 = (
    "Friday 16 October, written at 09:55. "
    "<strong>The grey market marked down every issue on this board overnight except the "
    "one whose revenue and profit are both falling.</strong> Bonfiglioli went 30.4% to "
    "23.9%, Zetwerk 15.2% to 9.9%, Fusion CX 12% to 7.6%, HD Fire 32.8% to 31.4%. Tonbo "
    "held at 71.4%. "
    "<strong>The subscription books say the same thing from the other side.</strong> Tonbo "
    "is 4&times; done with QIB already at 3.92&times;; Bonfiglioli &mdash; debt-free, "
    "growing 29%, 34% on capital &mdash; is 0.48&times; with QIB at <em>0.08&times;</em>. "
    "<strong>HD Fire&rsquo;s final book settled the one doubt this page had about it:</strong> "
    "QIB closed at 256.65&times; against 1.49&times; with a session to run. Allotment is "
    "finalised today and retail at 30.49&times; makes it about a one-in-thirty draw. "
    "<strong>Fusion CX closes tonight at 1.16&times; with QIB at 0.05&times;.</strong> "
    "<strong>Held:</strong> nothing in equities. Entries are blocked on breadth."
)

FOOTNOTE_16 = (
    "<strong>There is a mechanical explanation for the empty books and it opens on "
    "Tuesday.</strong> Jio Platforms takes &#8377;1,065&ndash;1,119 a share for roughly "
    "&#8377;30,000 Cr on 21&ndash;23 October &mdash; comfortably the largest issue this "
    "market has seen. An institution that intends to bid for it does not tie up funds in a "
    "&#8377;2,534 Cr gearbox manufacturer the week before. That fits Bonfiglioli&rsquo;s "
    "QIB at 0.08&times; far better than anything in its accounts does, and it means a weak "
    "book this week is weaker evidence about the company than it would usually be. "
    "<strong>It does not rescue the Tonbo call, and this page is not going to pretend "
    "otherwise.</strong> The same cash shortage should have emptied Tonbo&rsquo;s book too "
    "and did not: QIB 3.92&times;, NII 5.96&times;, retail 3.2&times;, premium unmoved at "
    "71.4% for a company whose revenue fell 22.7%, whose profit fell 30%, which lost "
    "&#8377;17.74 Cr in Q1 FY27 and which has run negative operating cash flow for two "
    "years. Institutions are choosing to be there. The avoid call was made on 13 October at "
    "61% and is recorded again here at 71.4%, unchanged and so far losing. "
    "<strong>Two live scorecards now run on this page</strong> &mdash; Tonbo, where it says "
    "avoid and the market says 71.4%, and Bonfiglioli, where it says the accounts are the "
    "best on the board and the book says 0.48&times;. Both print within a fortnight."
)


def _for_16() -> list[IPO]:
    """HD Fire allots, Fusion CX closes, and Jio is about to drain the room."""
    return [
        IPO(
            name="HD Fire Protect", call="ALLOTMENT TODAY — the QIB doubt resolved emphatically",
            tone="good",
            dates="13\u201315 Oct \u00b7 CLOSED \u00b7 allotment today \u00b7 lists 21 Oct",
            band="\u20b9258\u2013271", size="\u20b9712.31 Cr, entirely OFS",
            split="100% OFS \u2014 both sellers are the promoters",
            gmp="\u20b985", gmp_pct=31.4, expected="~+29%",
            apply_as="Closed. Nothing to do but check allotment.",
            horizon="Listing-day sell on 21 Oct. Unchanged throughout.",
            book="FINAL \u00b7 QIB 256.65\u00d7 \u00b7 NII 203.21\u00d7 \u00b7 retail 30.49\u00d7",
            flags=(("QIB 256.65\u00d7 \u2014 the day-2 worry was wrong", "pass"),
                   ("NII 203.21\u00d7", "pass"),
                   ("anchor FULL at the top band, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("retail 30.49\u00d7 \u2014 allotment ~1 in 30", "warn"),
                   ("GMP eased \u20b989 \u2192 \u20b985", "warn"),
                   ("40.7\u00d7 for 6.4% PAT growth", "fail")),
            stats=(("day 1", "4.62\u00d7"), ("day 2", "16.51\u00d7"), ("FINAL", "see QIB/NII"),
                   ("QIB", "256.65\u00d7"), ("NII", "203.21\u00d7"), ("retail", "30.49\u00d7"),
                   ("GMP", "\u20b985 \u00b7 31.4%"), ("P/E post", "40.7\u00d7")),
            note=(
                "<strong>Yesterday this page flagged QIB at 1.49&times; as the issue&rsquo;s "
                "only soft spot and said institutions bid on the last day. They closed at "
                "256.65&times;.</strong> That is not a marginal improvement, it is a different "
                "book: NII finished at 203.21&times; and retail at 30.49&times;, against "
                "16.51&times; overall with a session still to run. "
                "<strong>The consequence is arithmetic.</strong> Retail at 30.49&times; makes a "
                "single lot roughly a one-in-thirty draw, so the realistic outcome for most "
                "applicants is no shares at all. That was always the plan&rsquo;s weakness and "
                "it is now its shape: a free option that usually does not pay out. "
                "The premium eased from &#8377;89 to &#8377;85 &mdash; worth noting, not worth "
                "acting on, and on the measured overstatement that still implies about +29%. "
                "Nothing in the accounts moved: 40.7 times for 6.4% growth, every rupee to the "
                "promoters. <strong>If allotted, sell on 21 October.</strong>"
            ),
        ),
        IPO(
            name="Fusion CX", call="SKIP \u2014 closes tonight and QIB never showed up",
            tone="bad",
            dates="14\u201316 Oct \u00b7 CLOSES TODAY \u00b7 lists 22 Oct",
            band="\u20b9275\u2013289", size="\u20b9702 Cr",
            split="\u20b9500 Cr fresh + \u20b9202 Cr OFS (69.90 lakh sh)",
            gmp="\u20b922", gmp_pct=7.6, expected="~+5%",
            apply_as="Do not apply.",
            horizon="None.",
            book="day 3 \u00b7 1.16\u00d7 \u00b7 QIB 0.05\u00d7 \u00b7 NII 1.45\u00d7 \u00b7 retail 3.73\u00d7",
            flags=(("QIB 0.05\u00d7 on the final day", "fail"),
                   ("overall 1.16\u00d7 \u2014 barely covered", "fail"),
                   ("GMP \u20b936.50 \u2192 \u20b922 across three sessions", "fail"),
                   ("~+5% expected after the measured overstatement", "fail"),
                   ("retail 3.73\u00d7 is the only bid here", "warn"),
                   ("\u20b9500 Cr of it is fresh capital", "pass")),
            stats=(("GMP 14 Oct", "\u20b936.50"), ("GMP 15 Oct", "\u20b922"),
                   ("GMP today", "\u20b922 \u00b7 7.6%"),
                   ("overall", "1.16\u00d7"), ("QIB", "0.05\u00d7"),
                   ("NII", "1.45\u00d7"), ("retail", "3.73\u00d7"),
                   ("expected listing", "~+5%")),
            note=(
                "<strong>QIB at 0.05&times; going into the close is as close to a total "
                "institutional refusal as a mainboard book gets.</strong> Five per cent of the "
                "institutional portion, on the last day, when institutions bid late &mdash; HD "
                "Fire went from 1.49&times; to 256.65&times; in that same window, which is what "
                "a final session looks like when the demand exists. "
                "<strong>The premium has been falling the whole way</strong>, &#8377;36.50 on "
                "day one to &#8377;22 now. At 7.6%, after the 2.6-point overstatement this page "
                "applies to every GMP, the expectation is about +5% &mdash; and a 1.16&times; "
                "book has no retail scarcity behind it, so allotment is near-certain for anyone "
                "who applies. <strong>That is the wrong combination:</strong> you get the shares "
                "you asked for, in the issue nobody wanted, for five per cent. The one thing in "
                "its favour is that &#8377;500 Cr of the &#8377;702 Cr is fresh money going into "
                "the business rather than out to sellers. It is not enough tonight."
            ),
        ),
        IPO(
            name="Bonfiglioli Transmissions", call="APPLY \u2014 best accounts here, and the book is empty",
            tone="good",
            dates="15\u201319 Oct \u00b7 day 2 of 5",
            band="\u20b9558\u2013586", size="~\u20b92,534 Cr",
            split="100% OFS by the Italian parent",
            gmp="\u20b9140", gmp_pct=23.9, expected="~+21%",
            apply_as="Retail \u2014 25 shares, \u20b914,650. Three sessions left.",
            horizon="The only name here where holding past listing is an argument.",
            book="day 2 \u00b7 0.48\u00d7 \u00b7 QIB 0.08\u00d7 \u00b7 NII 0.78\u00d7 \u00b7 retail 0.57\u00d7",
            flags=(("PAT +29.2% to \u20b9148.58 Cr", "pass"),
                   ("DEBT-FREE, no borrowings since CY24", "pass"),
                   ("ROCE 24.53% \u2192 34.05%", "pass"),
                   ("H1 FY27 EBITDA \u20b9223.87 Cr vs \u20b9176.43 Cr", "pass"),
                   ("retail 0.57\u00d7 \u2014 allotment near-certain", "pass"),
                   ("QIB 0.08\u00d7 on day 2", "fail"),
                   ("GMP 30.4% \u2192 23.9% overnight", "warn"),
                   ("100% OFS \u2014 the parent is selling", "fail")),
            stats=(("band", "\u20b9558\u2013586"), ("size", "~\u20b92,534 Cr"),
                   ("FY26 PAT", "\u20b9148.58 Cr (+29.2%)"),
                   ("ROCE", "34.05%"), ("P/E upper", "~46.3\u00d7"),
                   ("day 2 book", "0.48\u00d7"), ("QIB", "0.08\u00d7"),
                   ("retail", "0.57\u00d7"),
                   ("GMP 15 Oct", "30.4%"), ("GMP today", "23.9%")),
            note=(
                "<strong>The accounts have not changed and the market&rsquo;s opinion of them "
                "has halved.</strong> Profit up 29.2%, no borrowings at all since CY24, return "
                "on capital employed from 24.53% to 34.05%, H1 FY27 EBITDA already ahead of last "
                "year &mdash; and the book is 0.48&times; on day two with institutions at "
                "0.08&times;, while the premium fell from 30.4% to 23.9% overnight. "
                "<strong>The footnote below argues this is about Jio rather than about "
                "Bonfiglioli</strong>, and the honest position is that it is partly both: a "
                "&#8377;2,534 Cr full exit by a parent, at 46 times, three sessions before the "
                "largest IPO in this market&rsquo;s history, is a hard week to come to market in. "
                "<strong>For a retail applicant the weak book is an advantage, not a warning.</strong> "
                "Retail at 0.57&times; means a lot is near-certain rather than a one-in-thirty "
                "draw &mdash; the exact inverse of HD Fire. That changes what this application is: "
                "not a lottery ticket on a listing pop, but the one name on this board worth "
                "owning after it lists. Apply for the business; do not count on the pop."
            ),
        ),
        IPO(
            name="Tonbo Imaging India", call="AVOID STANDS \u2014 and the call is losing",
            tone="bad",
            dates="15\u201319 Oct \u00b7 day 2 of 5", band="\u20b9665\u2013700",
            size="\u20b9852.18 Cr",
            split="100% OFS \u2014 the company receives nothing",
            gmp="\u20b9500", gmp_pct=71.4, expected="~+69% implied",
            apply_as="Do not apply.",
            horizon="None.",
            book="day 2 \u00b7 4\u00d7 \u00b7 QIB 3.92\u00d7 \u00b7 NII 5.96\u00d7 \u00b7 retail 3.2\u00d7",
            flags=(("QIB 3.92\u00d7 on day 2 \u2014 institutions are bidding", "warn"),
                   ("the ONLY issue whose GMP did not fall", "warn"),
                   ("revenue \u221222.7% in FY26", "fail"),
                   ("PAT \u221230% in FY26", "fail"),
                   ("Q1 FY27 a \u20b917.74 Cr LOSS", "fail"),
                   ("negative operating cash flow FY25 AND FY26", "fail"),
                   ("working capital 152 \u2192 280 \u2192 517 days", "fail"),
                   ("~79\u00d7 earnings that are falling", "fail")),
            stats=(("GMP 12 Oct", "38.6%"), ("GMP 13 Oct", "61.0%"),
                   ("GMP 14 Oct", "69.3%"), ("GMP 15 Oct", "71.4%"),
                   ("GMP today", "71.4%"),
                   ("day 2 book", "4\u00d7"), ("QIB", "3.92\u00d7"),
                   ("NII", "5.96\u00d7"),
                   ("FY26 revenue", "\u20b9362.65 Cr (\u221222.7%)"),
                   ("Q1 FY27", "\u2212\u20b917.74 Cr"), ("WC days", "517")),
            note=(
                "<strong>Every other issue on this board was marked down overnight. This one "
                "was not, and its institutional book is 3.92&times; while Bonfiglioli&rsquo;s "
                "is 0.08&times;.</strong> If the week&rsquo;s weak books were purely about cash "
                "being held back for Jio, this book would be weak too. It is not. Institutions "
                "are actively choosing to be here. "
                "<strong>The accounts are unchanged and they are bad.</strong> Revenue "
                "&minus;22.7%, profit &minus;30%, a &#8377;17.74 Cr loss in the first quarter of "
                "the year being sold, operating cash flow negative in both FY25 and FY26 while "
                "profits were reported in both, working capital out to 517 days, and roughly 79 "
                "times earnings that are going backwards &mdash; for an issue where the company "
                "receives nothing. "
                "<strong>This page said avoid on 13 October at a 61% premium. It is 71.4% now "
                "and the book is strong.</strong> The call is unchanged and it is currently "
                "wrong. It is left standing, and recorded, because a call that is quietly "
                "revised once the market disagrees is not a record of anything."
            ),
        ),
        IPO(
            name="Jio Platforms", call="OPENS TUESDAY \u2014 the issue that is draining this week",
            tone="warn",
            dates="21\u201323 Oct \u00b7 lists 28 Oct",
            band="\u20b91,065\u20131,119", size="~\u20b930,000 Cr (27 Cr fresh shares)",
            split="Fresh issue",
            gmp="\u20b9230", gmp_pct=20.6, expected="~+18%",
            apply_as="Retail \u2014 12 shares, \u20b913,428 at the top band.",
            horizon="Decide before Tuesday; the book will be enormous.",
            book="opens 21 Oct",
            flags=(("the largest IPO this market has listed", "warn"),
                   ("fresh issue \u2014 the money goes into the company", "pass"),
                   ("GMP 20.6% and firm", "pass"),
                   ("size alone makes a big listing pop unlikely", "warn"),
                   ("it is absorbing the liquidity the others wanted", "warn")),
            stats=(("band", "\u20b91,065\u20131,119"), ("size", "~\u20b930,000 Cr"),
                   ("fresh shares", "27 Cr"), ("lot", "12 sh \u00b7 \u20b913,428"),
                   ("GMP", "\u20b9230 \u00b7 20.6%"),
                   ("opens", "21 Oct"), ("lists", "28 Oct")),
            note=(
                "<strong>This is the week&rsquo;s most important issue and it has not opened "
                "yet.</strong> Roughly &#8377;30,000 Cr across 21&ndash;23 October at "
                "&#8377;1,065&ndash;1,119, a fresh issue, listing 28 October. The premium is "
                "&#8377;230 and has been firm, which after the measured overstatement implies "
                "about +18%. "
                "<strong>Two things follow for the rest of this page.</strong> The first is that "
                "a &#8377;30,000 Cr call on the market three sessions out is the most plausible "
                "reason Bonfiglioli&rsquo;s institutional book is at 0.08&times;. The second is "
                "that size cuts both ways here: an issue this large is hard to squeeze, so the "
                "listing-day move is likely to be more orderly than the premium suggests, and "
                "retail allotment on a book this size will be its own lottery. "
                "<strong>No call yet.</strong> The prospectus detail that matters &mdash; what "
                "the fresh capital is for, and the margin trajectory &mdash; gets read before "
                "Tuesday, and the call goes on this page before the book opens rather than after."
            ),
        ),
        IPO(
            name="Paras Healthcare", call="OPENS TUESDAY \u2014 band just set, book not yet open",
            tone="warn",
            dates="21\u201323 Oct",
            band="up to \u20b9693", size="\u20b91,800 Cr",
            split="\u20b9500 Cr fresh + \u20b91,300 Cr OFS",
            gmp="\u20b9100", gmp_pct=14.4, expected="~+12%",
            apply_as="No call yet.",
            horizon="Read the prospectus before Tuesday.",
            book="opens 21 Oct",
            flags=(("\u20b9500 Cr is fresh capital", "pass"),
                   ("\u20b91,300 Cr of \u20b91,800 Cr is a seller exiting", "warn"),
                   ("GMP 14.4%, mid-table", "warn"),
                   ("opens the same day as Jio", "warn")),
            stats=(("band", "up to \u20b9693"), ("size", "\u20b91,800 Cr"),
                   ("fresh", "\u20b9500 Cr"), ("OFS", "\u20b91,300 Cr"),
                   ("GMP", "\u20b9100 \u00b7 14.4%"), ("opens", "21 Oct")),
            note=(
                "<strong>A hospital chain raising &#8377;1,800 Cr, of which &#8377;1,300 Cr is a "
                "shareholder leaving.</strong> The DRHP went in on 5 June and the band has only "
                "just been set, so the accounts get read properly before Tuesday rather than "
                "summarised from a price band here. "
                "<strong>The timing is the first thing to say about it.</strong> It opens on the "
                "same morning as a &#8377;30,000 Cr issue. Whatever its merits, it is competing "
                "for attention and for money with the largest listing this market has run, and "
                "the 14.4% premium is being quoted into that. No call until the prospectus is read."
            ),
        ),
        IPO(
            name="Zetwerk & Sahajanand", call="BOTH MARKED DOWN \u00b7 ZETWERK STILL LOSS-MAKING",
            tone="warn",
            dates="15\u201319 Oct \u00b7 day 2 of 5",
            band="Zetwerk \u20b9151 \u00b7 Sahajanand \u20b9344",
            size="Zetwerk ~\u20b95,000 Cr \u00b7 Sahajanand to confirm",
            split="Zetwerk \u20b92,600 Cr fresh + 9.68 Cr OFS \u00b7 Sahajanand OFS",
            gmp="\u20b915 / \u20b945", gmp_pct=9.9, expected="~+7% / +11%",
            apply_as="Zetwerk: no. Sahajanand: thin edge at best.",
            horizon="Neither earns a hold.",
            book="neither book has matched the exchange feed yet",
            flags=(("Zetwerk GMP 15.2% \u2192 9.9% overnight", "fail"),
                   ("Zetwerk FY26 LOSS of \u20b91,606.17 Cr", "fail"),
                   ("Zetwerk order book \u20b913,062 Cr, 1.39\u00d7 revenue", "pass"),
                   ("Sahajanand GMP held, 12.2% \u2192 13.1%", "pass"),
                   ("Sahajanand PAT \u20b925.15 Cr \u2192 \u20b969.08 Cr", "pass"),
                   ("Sahajanand ~53\u00d7 FY26 diluted", "warn"),
                   ("no exchange book for either \u2014 cannot verify demand", "warn")),
            stats=(("Zetwerk GMP 15 Oct", "15.2%"), ("Zetwerk GMP today", "9.9%"),
                   ("Zetwerk FY26 result", "\u2212\u20b91,606.17 Cr"),
                   ("Zetwerk order book", "\u20b913,062.40 Cr"),
                   ("Sahajanand GMP today", "13.1%"),
                   ("Sahajanand FY26 PAT", "\u20b969.08 Cr (was \u20b925.15 Cr)"),
                   ("Sahajanand P/E", "~53\u00d7")),
            note=(
                "<strong>Zetwerk lost a third of its premium overnight</strong>, 15.2% to 9.9%, "
                "which is the sharpest markdown on the board. Nothing in the filings changed: "
                "&#8377;16,100.63 Cr of income for a &#8377;1,606.17 Cr loss, an order book of "
                "&#8377;13,062 Cr that is real, and a manufacturing EBITDA margin improving to "
                "6.56% from 4.83%. A business that must triple its margin to break even was "
                "never a listing-day trade, and at 9.9% the grey market has stopped pretending "
                "it is one. "
                "<strong>Sahajanand is the only issue besides Tonbo whose premium did not "
                "fall</strong>, edging 12.2% to 13.1% &mdash; profit from &#8377;25.15 Cr to "
                "&#8377;69.08 Cr, cardiac implants into 77 countries, 73.87% of revenue earned "
                "abroad, priced at roughly 53 times for that to continue. "
                "<strong>Neither has matched the exchange&rsquo;s subscription feed yet</strong>, "
                "so for both of these the demand side is unverified and the premium is the only "
                "signal available &mdash; which is exactly the signal this page trusts least."
            ),
        ),
    ]


IPOS_2026_10_16 = _for_16()


LEAD_19 = (
    "Monday 19 October, written Saturday evening and <strong>refreshed at 11:00 Monday "
    "with live grey-market quotes</strong>. The subscription columns are still Friday's "
    "close &mdash; the exchange only aggregates today's bids this evening, and today is "
    "the last session for four of these. "
    "<strong>Four issues close tonight and the inversion this page has tracked all week "
    "got wider, not narrower.</strong> Tonbo &mdash; revenue down 22.7%, profit down 30%, "
    "a &#8377;17.74 Cr loss in Q1 &mdash; is now <strong>7.78&times; subscribed</strong> "
    "with QIB at 3.95&times; and NII at 14.35&times;, and its premium rose again to 73.7%. "
    "Bonfiglioli &mdash; debt-free, growing 29%, 34% on capital &mdash; is "
    "<strong>0.99&times;</strong>, QIB <strong>0.16&times;</strong>, with one session left. "
    "<strong>Zetwerk's premium has collapsed from 15.2% to 4.6% in four sessions</strong>, "
    "which after the measured overstatement is roughly two per cent. "
    "<strong>HD Fire lists Tuesday</strong> on a final book of QIB 256.65&times;. "
    "Jio and Paras open Wednesday. "
    "<strong>Held:</strong> nothing in equities; entries blocked on breadth."
)

FOOTNOTE_19 = (
    "<strong>Is Bonfiglioli&rsquo;s book a verdict or just early? This board already "
    "answered that once.</strong> HD Fire sat at QIB 1.49&times; with one session to run "
    "and this page called it the issue&rsquo;s only soft spot. It closed at "
    "<strong>256.65&times;</strong>. Institutions bid on the last day, so 0.16&times; on a "
    "Friday is not the number to judge an issue by &mdash; tonight&rsquo;s is. What would "
    "make it a verdict is the same figure at the close. "
    "<strong>Two live calls settle this week and both are recorded before the print.</strong> "
    "Tonbo: avoid, made 13 October at a 61% premium, restated at 71.4% and now at 73.7% "
    "against a 7.78&times; book. It is losing and it is not being revised, because a call "
    "quietly rewritten once the market disagrees is not a record. Bonfiglioli: the best "
    "accounts on the board, carrying a third of Tonbo&rsquo;s premium and a book a "
    "fiftieth the size. One of those two readings of the same week is wrong and the "
    "listings will say which. "
    "<strong>The one thing that has gone exactly as written is HD Fire</strong>, where the "
    "day-2 QIB worry was called wrong in public on the 16th and the final book proved it."
)


def _for_19() -> list[IPO]:
    """Final day for four; HD Fire lists Tuesday; Jio opens Wednesday."""
    return [
        IPO(
            name="Bonfiglioli Transmissions", call="FINAL DAY \u2014 best accounts here, and the book is the question",
            tone="good",
            dates="15\u201319 Oct \u00b7 CLOSES TODAY \u00b7 lists ~24 Oct",
            band="\u20b9558\u2013586", size="~\u20b92,534 Cr",
            split="100% OFS by the Italian parent",
            gmp="\u20b9130", gmp_pct=22.2, expected="~+20%",
            apply_as="Retail \u2014 25 shares, \u20b914,650. Today or not at all.",
            horizon="The only name here where holding past listing is an argument.",
            book="day 3 \u00b7 0.99\u00d7 \u00b7 QIB 0.16\u00d7 \u00b7 NII 1.71\u00d7 \u00b7 retail 1.16\u00d7",
            flags=(("PAT +29.2% to \u20b9148.58 Cr", "pass"),
                   ("DEBT-FREE, no borrowings since CY24", "pass"),
                   ("ROCE 24.53% \u2192 34.05%", "pass"),
                   ("H1 FY27 EBITDA \u20b9223.87 Cr vs \u20b9176.43 Cr", "pass"),
                   ("book doubled 0.48\u00d7 \u2192 0.99\u00d7", "pass"),
                   ("retail 1.16\u00d7 \u2014 allotment still near-certain", "pass"),
                   ("QIB 0.16\u00d7 with one session left", "fail"),
                   ("GMP 30.4% \u2192 23.9% \u2192 22.2%", "warn"),
                   ("100% OFS \u2014 the parent is selling", "fail")),
            stats=(("FY26 PAT", "\u20b9148.58 Cr (+29.2%)"), ("ROCE", "34.05%"),
                   ("P/E upper", "~46.3\u00d7"),
                   ("day 1", "0.48\u00d7"), ("day 3", "0.99\u00d7"),
                   ("QIB", "0.16\u00d7"), ("retail", "1.16\u00d7"),
                   ("GMP 15 Oct", "30.4%"), ("GMP today", "22.2%")),
            note=(
                "<strong>The accounts have not moved all week and the book has barely "
                "cleared one times.</strong> Profit up 29.2%, no borrowings since CY24, "
                "return on capital from 24.53% to 34.05%, H1 FY27 EBITDA already ahead of "
                "last year &mdash; and 0.99&times; on day three with institutions at "
                "0.16&times;. "
                "<strong>The footnote argues this is not yet a verdict, and the evidence is "
                "on this same board.</strong> HD Fire was at QIB 1.49&times; with one "
                "session left and closed at 256.65&times;. Institutions bid last. So the "
                "number that matters is tonight&rsquo;s, not Friday&rsquo;s. "
                "<strong>For a retail applicant the weak book remains an advantage.</strong> "
                "Retail at 1.16&times; means a lot is close to certain, the inverse of HD "
                "Fire&rsquo;s one-in-thirty. That is what this application is: not a lottery "
                "ticket on a pop, but the one name on this board worth owning after it "
                "lists. <strong>Apply for the business. Do not count on the pop, and be "
                "willing to be refunded if the book does not close.</strong>"
            ),
        ),
        IPO(
            name="Tonbo Imaging India", call="AVOID STANDS \u2014 final day, and the call is losing badly",
            tone="bad",
            dates="15\u201319 Oct \u00b7 CLOSES TODAY", band="\u20b9665\u2013700",
            size="\u20b9852.18 Cr",
            split="100% OFS \u2014 the company receives nothing",
            gmp="\u20b9520", gmp_pct=74.3, expected="~+72% implied",
            apply_as="Do not apply.",
            horizon="None.",
            book="day 3 \u00b7 7.78\u00d7 \u00b7 QIB 3.95\u00d7 \u00b7 NII 14.35\u00d7 \u00b7 retail 7.13\u00d7",
            flags=(("7.78\u00d7 with a session still to run", "warn"),
                   ("NII 14.35\u00d7 \u2014 more than doubled overnight", "warn"),
                   ("the only premium that has risen all week", "warn"),
                   ("revenue \u221222.7% in FY26", "fail"),
                   ("PAT \u221230% in FY26", "fail"),
                   ("Q1 FY27 a \u20b917.74 Cr LOSS", "fail"),
                   ("negative operating cash flow FY25 AND FY26", "fail"),
                   ("working capital 152 \u2192 280 \u2192 517 days", "fail"),
                   ("~79\u00d7 earnings that are falling", "fail")),
            stats=(("GMP 12 Oct", "38.6%"), ("GMP 15 Oct", "71.4%"),
                   ("GMP today", "74.3%"),
                   ("day 2 book", "4\u00d7"), ("day 3 book", "7.78\u00d7"),
                   ("QIB", "3.95\u00d7"), ("NII", "14.35\u00d7"),
                   ("FY26 revenue", "\u20b9362.65 Cr (\u221222.7%)"),
                   ("Q1 FY27", "\u2212\u20b917.74 Cr"), ("WC days", "517")),
            note=(
                "<strong>The book nearly doubled again and the premium rose for the fifth "
                "session running.</strong> 7.78&times; overall, NII 14.35&times;, QIB "
                "3.95&times; &mdash; on a company whose revenue fell 22.7%, whose profit "
                "fell 30%, which lost &#8377;17.74 Cr in the first quarter of the year being "
                "sold, whose operating cash flow was negative in both FY25 and FY26 while "
                "profits were reported, and whose working capital runs to 517 days. The "
                "company receives none of the &#8377;852 Cr. "
                "<strong>This page said avoid on 13 October at 61%. It is 73.7% now.</strong> "
                "The call is unchanged and it is losing. It is recorded here, before the "
                "print, for the same reason it was recorded then: the only version of this "
                "page worth keeping is one where a wrong call stays wrong on the record."
            ),
        ),
        IPO(
            name="HD Fire Protect", call="LISTS TUESDAY \u2014 sell on listing",
            tone="good",
            dates="13\u201315 Oct \u00b7 allotted \u00b7 LISTS 21 OCT",
            band="\u20b9258\u2013271", size="\u20b9712.31 Cr, entirely OFS",
            split="100% OFS \u2014 both sellers are the promoters",
            gmp="\u20b985", gmp_pct=31.4, expected="~+29%",
            apply_as="Closed and allotted. Nothing to do until Tuesday.",
            horizon="Sell on listing day, 21 October. Unchanged throughout.",
            book="FINAL \u00b7 QIB 256.65\u00d7 \u00b7 NII 203.21\u00d7 \u00b7 retail 30.49\u00d7",
            flags=(("QIB 256.65\u00d7 final", "pass"),
                   ("anchor FULL at the top band, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("retail 30.49\u00d7 \u2014 most applicants got nothing", "warn"),
                   ("40.7\u00d7 for 6.4% PAT growth", "fail")),
            stats=(("QIB", "256.65\u00d7"), ("NII", "203.21\u00d7"),
                   ("retail", "30.49\u00d7"), ("GMP", "\u20b985 \u00b7 31.4%"),
                   ("P/E post", "40.7\u00d7"), ("lists", "21 Oct")),
            note=(
                "<strong>The one call on this board that has gone exactly as written.</strong> "
                "On 15 October this page flagged QIB at 1.49&times; as the issue&rsquo;s only "
                "soft spot and said institutions bid on the final day; the book closed at "
                "256.65&times;, and the 16th recorded that the worry had been wrong. "
                "Nothing has changed in the accounts &mdash; 40.7 times for 6.4% growth, "
                "every rupee to the promoters &mdash; so the plan is the plan: "
                "<strong>sell into the listing on Tuesday.</strong> A 31.4% premium implies "
                "about +29% after the overstatement this page applies, and a book this size "
                "means most retail applicants are holding nothing to sell."
            ),
        ),
        IPO(
            name="Zetwerk", call="NO \u2014 the premium has collapsed to almost nothing",
            tone="bad",
            dates="15\u201319 Oct \u00b7 CLOSES TODAY", band="\u20b9151",
            size="~\u20b95,000 Cr",
            split="\u20b92,600 Cr fresh + 9.68 Cr OFS",
            gmp="\u20b95", gmp_pct=3.3, expected="~+1%",
            apply_as="Do not apply.",
            horizon="None.",
            book="no exchange book matched",
            flags=(("GMP 15.2% \u2192 9.9% \u2192 4.6% \u2192 3.3%", "fail"),
                   ("under +1% after the measured overstatement", "fail"),
                   ("FY26 LOSS of \u20b91,606.17 Cr", "fail"),
                   ("the only issue raising real money", "pass"),
                   ("order book \u20b913,062 Cr, 1.39\u00d7 revenue", "pass"),
                   ("no exchange book \u2014 demand unverified", "warn")),
            stats=(("GMP 15 Oct", "15.2%"), ("GMP 16 Oct", "9.9%"),
                   ("GMP today", "3.3%"),
                   ("FY26 income", "\u20b916,100.63 Cr"),
                   ("FY26 result", "\u2212\u20b91,606.17 Cr"),
                   ("order book", "\u20b913,062.40 Cr")),
            note=(
                "<strong>Two thirds of the premium is gone in four sessions</strong> &mdash; "
                "15.2% to 9.9% to 4.6% &mdash; and at 4.6%, after the 2.6-point "
                "overstatement this page applies to every GMP, the expectation is about two "
                "per cent. That is not a listing trade; it is a coin toss with costs. "
                "Nothing in the filings changed: &#8377;16,100.63 Cr of income for a "
                "&#8377;1,606.17 Cr loss, a real &#8377;13,062 Cr order book, and a "
                "manufacturing margin improving from 4.83% to 6.56%. A business that must "
                "triple its margin to break even was never a listing-day trade, and the grey "
                "market has now stopped pretending otherwise."
            ),
        ),
        IPO(
            name="Sahajanand Medical", call="THIN \u2014 final day, premium still fading",
            tone="warn",
            dates="15\u201319 Oct \u00b7 CLOSES TODAY", band="\u20b9344",
            size="OFS", split="OFS",
            gmp="\u20b925", gmp_pct=7.3, expected="~+5%",
            apply_as="Thin edge at best.",
            horizon="Does not earn a hold.",
            book="no exchange book matched",
            flags=(("PAT \u20b925.15 Cr \u2192 \u20b969.08 Cr", "pass"),
                   ("revenue +18.11% to \u20b91,210.50 Cr", "pass"),
                   ("GMP 13.1% \u2192 10.2% \u2192 7.3%", "warn"),
                   ("~53\u00d7 FY26 diluted", "warn"),
                   ("73.87% of revenue earned outside India", "warn"),
                   ("no exchange book \u2014 demand unverified", "warn")),
            stats=(("FY26 revenue", "\u20b91,210.50 Cr (+18.11%)"),
                   ("FY26 PAT", "\u20b969.08 Cr (was \u20b925.15 Cr)"),
                   ("P/E", "~53\u00d7"), ("GMP 16 Oct", "13.1%"),
                   ("GMP today", "7.3%")),
            note=(
                "<strong>The better business of the two closing quietly tonight, and the "
                "market is not paying for it.</strong> Profit from &#8377;25.15 Cr to "
                "&#8377;69.08 Cr, revenue up 18.11%, cardiac implants sold into 77 countries "
                "&mdash; priced at roughly 53 times for that near-tripling to continue, with "
                "73.87% of revenue earned abroad carrying the currency with it. "
                "The premium has eased from 13.1% to 10.2% and no exchange book has matched, "
                "so the demand side is unverified and the premium is the only signal "
                "available. It is also the signal this page trusts least. Eight per cent "
                "expected, on an unverified book, is a thin edge."
            ),
        ),
        IPO(
            name="Jio Platforms", call="OPENS WEDNESDAY \u2014 read the prospectus before it does",
            tone="warn",
            dates="21\u201323 Oct \u00b7 lists 28 Oct",
            band="\u20b91,065\u20131,119", size="~\u20b930,000 Cr (27 Cr fresh shares)",
            split="Fresh issue",
            gmp="\u20b9250", gmp_pct=22.3, expected="~+20%",
            apply_as="Retail \u2014 12 shares, \u20b913,428 at the top band.",
            horizon="Decide by Tuesday night.",
            book="opens 21 Oct",
            flags=(("the largest IPO this market has listed", "warn"),
                   ("fresh issue \u2014 the money goes into the company", "pass"),
                   ("GMP firming, 20.6% \u2192 20.1% \u2192 22.3%", "pass"),
                   ("size alone makes a large pop unlikely", "warn")),
            stats=(("band", "\u20b91,065\u20131,119"), ("size", "~\u20b930,000 Cr"),
                   ("lot", "12 sh \u00b7 \u20b913,428"),
                   ("GMP 16 Oct", "20.6%"), ("GMP today", "22.3%"),
                   ("opens", "21 Oct"), ("lists", "28 Oct")),
            note=(
                "<strong>Still no call, and the prospectus gets read before there is "
                "one.</strong> The premium has held near 20% for a week, which after the "
                "measured overstatement implies about +18%, and the issue is fresh capital "
                "rather than an exit &mdash; the only one of the week that can say so "
                "besides Zetwerk. "
                "<strong>Its shadow over this week is the thing to carry forward.</strong> A "
                "&#8377;30,000 Cr call on the market two days out remains the most plausible "
                "reason Bonfiglioli&rsquo;s institutional book sat at 0.16&times; on Friday. "
                "If that is right, tonight&rsquo;s Bonfiglioli close should still be weak and "
                "that will be an argument about liquidity rather than about the company."
            ),
        ),
        IPO(
            name="Paras Healthcare", call="OPENS WEDNESDAY \u2014 no call yet",
            tone="warn",
            dates="21\u201323 Oct",
            band="up to \u20b9693", size="\u20b91,800 Cr",
            split="\u20b9500 Cr fresh + \u20b91,300 Cr OFS",
            gmp="\u20b995", gmp_pct=13.7, expected="~+11%",
            apply_as="No call yet.",
            horizon="Read the prospectus before Wednesday.",
            book="opens 21 Oct",
            flags=(("\u20b9500 Cr is fresh capital", "pass"),
                   ("\u20b91,300 Cr of \u20b91,800 Cr is a seller exiting", "warn"),
                   ("GMP 14.4% \u2192 13.7%", "warn"),
                   ("opens the same morning as Jio", "warn")),
            stats=(("band", "up to \u20b9693"), ("size", "\u20b91,800 Cr"),
                   ("fresh", "\u20b9500 Cr"), ("OFS", "\u20b91,300 Cr"),
                   ("GMP 16 Oct", "14.4%"), ("GMP today", "13.7%")),
            note=(
                "<strong>A hospital chain raising &#8377;1,800 Cr, of which &#8377;1,300 Cr "
                "is a shareholder leaving.</strong> The accounts get read properly before "
                "Wednesday rather than summarised from a price band here. "
                "The timing remains the first thing to say about it: it opens on the same "
                "morning as a &#8377;30,000 Cr issue, and the 13.7% premium &mdash; easing, "
                "not firming &mdash; is being quoted into that."
            ),
        ),
    ]


IPOS_2026_10_19 = _for_19()


LEAD_21 = (
    "Wednesday 21 October, written at 10:15. "
    "<strong>Jio opens today at &#8377;30,213 Cr, the largest issue this market has ever "
    "run, and its premium is the only one that has risen every session this week</strong> "
    "&mdash; 20.6%, 20.1%, 22.3%, now 25.0%. "
    "<strong>The detail that decides how to read it: &#8377;27,500 Cr of the proceeds go to "
    "repaying debt.</strong> It is a fresh issue, so the money does reach the company, but "
    "nine rupees in ten are deleveraging rather than expansion. "
    "<strong>Paras opened beside it and the market marked it down on the day</strong>, "
    "13.7% to 7.2%. "
    "<strong>HD Fire lists today</strong> on a final book of QIB 256.65&times;. The four "
    "that closed Monday price their books tonight. "
    "<strong>Held:</strong> nothing in equities; breadth has collapsed to 22.38% against a "
    "33.93% mean and the gate is shut by a wide margin."
)

FOOTNOTE_21 = (
    "<strong>Two scorecards, one settled and one still open.</strong> HD Fire is the settled "
    "one and it went as written: this page called QIB 1.49&times; the only soft spot on 15 "
    "October, said institutions bid last, recorded on the 16th that the worry had been "
    "wrong when the book closed at 256.65&times;, and the plan has been sell-on-listing "
    "throughout. Today is the listing. "
    "<strong>The open one is Bonfiglioli against Tonbo, and tonight&rsquo;s final books "
    "settle the first half of it.</strong> On Saturday this page staked the Bonfiglioli "
    "read on a falsifiable claim &mdash; that QIB at 0.16&times; on a Friday was not a "
    "verdict, because HD Fire had gone 1.49&times; to 256.65&times; on its own final "
    "session. If Bonfiglioli closed near 1&times; with institutions still absent, that "
    "claim was wrong and the weak book was about the company rather than about Jio draining "
    "the room. Tonbo&rsquo;s avoid, made on 13 October at a 61% premium and restated three "
    "times since at 71.4%, 73.7% and 74.3%, settles on its listing. "
    "<strong>Neither is being revised now that the result is close.</strong>"
)


def _for_21() -> list[IPO]:
    """Jio and Paras open, HD Fire lists, Monday's four price tonight."""
    return [
        IPO(
            name="Jio Platforms", call="APPLY \u2014 one lot, retail, sell on listing",
            tone="good",
            dates="21\u201323 Oct \u00b7 OPENS TODAY \u00b7 allotment 26 Oct \u00b7 lists 28 Oct",
            band="\u20b91,065\u20131,119", size="\u20b930,213 Cr \u2014 the largest ever here",
            split="100% FRESH ISSUE, 27 Cr shares, no OFS",
            gmp="\u20b9280", gmp_pct=25.0, expected="~+22%",
            apply_as="Retail \u2014 12 shares, \u20b913,428 at the top band. One lot.",
            horizon="Listing-day sell on 28 October.",
            book="opens today \u00b7 anchors bid 19 Oct",
            flags=(("100% fresh issue \u2014 nobody is cashing out", "pass"),
                   ("the only premium that rose every session this week", "pass"),
                   ("20.6% \u2192 20.1% \u2192 22.3% \u2192 25.0%", "pass"),
                   ("retail quota on \u20b930,213 Cr is large in absolute terms", "pass"),
                   ("\u20b927,500 Cr of proceeds repays DEBT, not growth", "warn"),
                   ("size makes a violent listing pop unlikely", "warn")),
            stats=(("band", "\u20b91,065\u20131,119"), ("size", "\u20b930,213 Cr"),
                   ("fresh shares", "27 Cr"), ("lot", "12 sh \u00b7 \u20b913,428"),
                   ("for debt repayment", "\u20b927,500 Cr"),
                   ("GMP 16 Oct", "20.6%"), ("GMP 19 Oct", "22.3%"),
                   ("GMP today", "25.0%"), ("lists", "28 Oct")),
            note=(
                "<strong>The call this page owed before the open, and it is apply.</strong> "
                "Three things carry it. It is <em>entirely</em> fresh capital &mdash; alone "
                "on this month&rsquo;s board in that, where Bonfiglioli, Tonbo and HD Fire "
                "were all full or partial exits and the money left the company. The premium "
                "has risen every single session for a week while every other issue on the "
                "board except Tonbo was marked down, which is the one direction that matters "
                "going into an open. And the retail quota of a &#8377;30,213 Cr issue is "
                "enormous in absolute terms, so allotment is a better bet here than on a "
                "small hot issue &mdash; the inverse of HD Fire&rsquo;s one-in-thirty. "
                "<strong>The caveat is what the money does, and it is not small.</strong> "
                "&#8377;27,500 Cr of the &#8377;30,213 Cr repays debt. That is real and it "
                "is good for the company &mdash; interest cost comes down, the balance sheet "
                "improves &mdash; but anyone buying this as a growth issue should know that "
                "nine rupees in ten are retiring borrowings rather than building anything. "
                "<strong>And size cuts the upside.</strong> An issue this large is hard to "
                "squeeze, so the listing is likely to be more orderly than a 25% premium "
                "implies; ~+22% after the overstatement this page applies is the expectation, "
                "not a floor. One lot, retail, sold into the listing on 28 October. "
                "<strong>No hold case is being made</strong> &mdash; that needs the "
                "prospectus financials read properly, and this is a call about an "
                "application closing Friday."
            ),
        ),
        IPO(
            name="Paras Healthcare", call="SKIP \u2014 marked down on its own opening day",
            tone="bad",
            dates="21\u201323 Oct \u00b7 OPENS TODAY",
            band="up to \u20b9693", size="\u20b91,800 Cr",
            split="\u20b9500 Cr fresh + \u20b91,300 Cr OFS",
            gmp="\u20b950", gmp_pct=7.2, expected="~+5%",
            apply_as="Do not apply.",
            horizon="None.",
            book="opens today",
            flags=(("GMP 14.4% \u2192 13.7% \u2192 7.2% \u2014 halved on the open", "fail"),
                   ("~+5% after the measured overstatement", "fail"),
                   ("\u20b91,300 Cr of \u20b91,800 Cr is a seller exiting", "fail"),
                   ("opens against a \u20b930,213 Cr issue", "fail"),
                   ("\u20b9500 Cr is fresh capital", "pass")),
            stats=(("band", "up to \u20b9693"), ("size", "\u20b91,800 Cr"),
                   ("OFS share", "72%"),
                   ("GMP 16 Oct", "14.4%"), ("GMP 19 Oct", "13.7%"),
                   ("GMP today", "7.2%")),
            note=(
                "<strong>The premium halved on the morning it opened</strong>, 13.7% to 7.2%, "
                "which after the 2.6-point overstatement leaves about five per cent. A grey "
                "market that marks an issue down <em>as it opens</em> is saying something "
                "about the book it expects. "
                "<strong>Seventy-two per cent of the raise is a shareholder leaving.</strong> "
                "&#8377;1,300 Cr of &#8377;1,800 Cr goes to the selling holder and "
                "&#8377;500 Cr to the company. Set against the issue opening the same "
                "morning &mdash; wholly fresh capital, premium rising &mdash; this is the "
                "worse of the two in every respect that can be checked before a book exists. "
                "<strong>Skip.</strong> The prospectus work this page promised is moot: the "
                "market answered first and the structure was never attractive."
            ),
        ),
        IPO(
            name="HD Fire Protect", call="LISTS TODAY \u2014 sell into it",
            tone="good",
            dates="13\u201315 Oct \u00b7 LISTING TODAY, 21 Oct",
            band="\u20b9258\u2013271", size="\u20b9712.31 Cr, entirely OFS",
            split="100% OFS \u2014 both sellers are the promoters",
            gmp="\u20b985", gmp_pct=31.4, expected="~+29%",
            apply_as="Allotted or not \u2014 nothing further to apply for.",
            horizon="Sell on the listing. Unchanged since 15 October.",
            book="FINAL \u00b7 QIB 256.65\u00d7 \u00b7 NII 203.21\u00d7 \u00b7 retail 30.49\u00d7",
            flags=(("QIB closed at 256.65\u00d7", "pass"),
                   ("anchor FULL at the top band, 71.88% domestic MFs", "pass"),
                   ("RoE 30.17%, RoCE 40.33%", "pass"),
                   ("retail 30.49\u00d7 \u2014 most applicants hold nothing", "warn"),
                   ("40.7\u00d7 for 6.4% PAT growth", "fail")),
            stats=(("QIB", "256.65\u00d7"), ("NII", "203.21\u00d7"),
                   ("retail", "30.49\u00d7"), ("GMP", "\u20b985 \u00b7 31.4%"),
                   ("P/E post", "40.7\u00d7"), ("lists", "today")),
            note=(
                "<strong>The one call on this month&rsquo;s board that has gone exactly as "
                "written, start to finish.</strong> Apply one lot, retail, sell on listing "
                "&mdash; said on 15 October and unchanged through a day-2 QIB scare this "
                "page called wrong in public on the 16th, before the final book settled it at "
                "256.65&times;. "
                "Nothing in the accounts moved: 40.7 times for 6.4% profit growth, every "
                "rupee of &#8377;712.31 Cr to the promoters. The premium implies about +29%. "
                "<strong>Sell into the listing.</strong> And note what the book means for "
                "most people reading this: retail at 30.49&times; made it roughly a "
                "one-in-thirty draw, so the likeliest position today is no position at all."
            ),
        ),
        IPO(
            name="Bonfiglioli, Tonbo, Zetwerk, Sahajanand", call="CLOSED MONDAY \u2014 final books price tonight",
            tone="warn",
            dates="15\u201319 Oct \u00b7 all four closed",
            band="see each", size="\u20b92,534 / \u20b9852 / ~\u20b95,000 / OFS Cr",
            split="three exits, one fresh (Zetwerk)",
            gmp="last seen 22.2 / 74.3 / 3.3 / 7.3%", gmp_pct=74.3,
            expected="settles on listing",
            apply_as="Closed. Nothing to do.",
            horizon="Tonbo's avoid and Bonfiglioli's apply both settle here.",
            book="final figures not yet published",
            flags=(("Bonfiglioli last seen 0.99\u00d7, QIB 0.16\u00d7", "warn"),
                   ("Tonbo last seen 7.78\u00d7, QIB 3.95\u00d7", "warn"),
                   ("Zetwerk GMP fell 15.2% \u2192 3.3%", "fail"),
                   ("Sahajanand GMP fell 13.1% \u2192 7.3%", "fail"),
                   ("final books not yet in the public record", "warn")),
            stats=(("Bonfiglioli day 2", "0.99\u00d7"), ("its QIB", "0.16\u00d7"),
                   ("Tonbo day 2", "7.78\u00d7"), ("its QIB", "3.95\u00d7"),
                   ("Zetwerk GMP", "3.3%"), ("Sahajanand GMP", "7.3%")),
            note=(
                "<strong>All four closed Monday and the closing books are not in the public "
                "record yet.</strong> This entry exists so the page does not quietly skip the "
                "session its own calls turn on. "
                "<strong>What is being waited for, precisely.</strong> Bonfiglioli&rsquo;s "
                "final QIB: this page argued on Saturday that 0.16&times; on a Friday was not "
                "a verdict, because HD Fire had gone from 1.49&times; to 256.65&times; on its "
                "own last session. If Bonfiglioli closed near 1&times; with institutions still "
                "away, that argument was wrong and the empty book was about the company, not "
                "about Jio taking the room. And Tonbo&rsquo;s listing, which settles an avoid "
                "made at a 61% premium and restated at 71.4%, 73.7% and 74.3% without "
                "revision. "
                "<strong>Both are written down before the answer arrives, which is the only "
                "arrangement under which either is worth anything.</strong>"
            ),
        ),
    ]


IPOS_2026_10_21 = _for_21()


LEAD_22 = (
    "Thursday 22 October, written at 09:30. "
    "<strong>Both calls this page staked last weekend have answers, and they split.</strong> "
    "HD Fire listed at &#8377;335 against a &#8377;271 issue price, <strong>+23.62%</strong>, "
    "on a final book of 131.70&times;. The call was apply one lot and sell into the listing, "
    "made on 15 October and never changed. "
    "<strong>Bonfiglioli closed at 46.04&times; with QIB at 120.78&times;</strong> &mdash; "
    "from 0.16&times; with one session to run. The argument that Friday&rsquo;s empty book "
    "was not a verdict because institutions bid last was right, and the margin was not "
    "close. "
    "<strong>One sub-claim inside it was wrong and is corrected below.</strong> "
    "Tonbo closed at 135.90&times;, QIB 293.56&times;, and lists tomorrow &mdash; the avoid "
    "settles then, and it is not going to settle well. "
    "<strong>Held:</strong> nothing. The regime read bear this morning, breadth 12.05% "
    "against a 31.66% mean, 322 stocks at 52-week lows."
)

FOOTNOTE_22 = (
    "<strong>What the two results actually teach, separately from whether they felt "
    "good.</strong> "
    "<strong>One: the GMP model overstated by three times its historical margin.</strong> "
    "This page applies a 2.6-point haircut to every grey-market premium, measured over 295 "
    "listings. HD Fire quoted 31.4% and listed at 23.62% &mdash; an overstatement of 7.8 "
    "points. The call was still right and the direction was still right, but anyone sizing "
    "on &ldquo;~+29%&rdquo; got three quarters of it. One listing is not a reason to change "
    "the haircut; it is a reason to write the miss down and watch whether it repeats, "
    "because a model that is wrong in the same direction twice is a model with a bias "
    "rather than noise. "
    "<strong>Two: a weak book on day two says almost nothing.</strong> Bonfiglioli went "
    "0.16&times; to 120.78&times; on QIB in one session, which is the second time this month "
    "the same pattern printed &mdash; HD Fire went 1.49&times; to 256.65&times;. Two for two "
    "is not proof, but it is now the base case here, and a page that reads Friday&rsquo;s "
    "institutional number as a verdict will keep being wrong in the same direction. "
    "<strong>And the correction.</strong> The 19 October entry said retail allotment was "
    "&ldquo;near-certain&rdquo; because retail sat at 1.16&times;. It closed at 5.89&times;. "
    "That is roughly one lot in six, not a near-certainty, and the error was treating a "
    "day-two retail figure as settled while arguing in the very same entry that a day-two "
    "QIB figure was not. The argument was right; it simply was not applied to both columns."
)


def _for_22() -> list[IPO]:
    """HD Fire listed, Bonfiglioli's book settled the argument, Tonbo lists tomorrow."""
    return [
        IPO(
            name="HD Fire Protect", call="LISTED +23.62% \u2014 the call went as written",
            tone="good",
            dates="13\u201315 Oct \u00b7 LISTED 21 Oct at \u20b9335",
            band="\u20b9258\u2013271", size="\u20b9712.31 Cr, entirely OFS",
            split="100% OFS \u2014 both sellers are the promoters",
            gmp="was \u20b985", gmp_pct=31.4, expected="predicted ~+29%, got +23.62%",
            apply_as="Done. Sold into the listing.",
            horizon="Closed.",
            book="FINAL 131.70\u00d7 \u00b7 QIB 256.65\u00d7 \u00b7 NII 203.21\u00d7 \u00b7 retail 30.49\u00d7",
            flags=(("listed \u20b9335 vs \u20b9271 \u2014 +23.62%", "pass"),
                   ("call unchanged from 15 Oct", "pass"),
                   ("the day-2 QIB worry was called wrong in public, and was", "pass"),
                   ("GMP implied ~+29%, actual +23.62%", "warn"),
                   ("retail 30.49\u00d7 \u2014 most applicants held nothing", "warn")),
            stats=(("issue price", "\u20b9271"), ("listed at", "\u20b9335"),
                   ("gain", "+23.62%"), ("predicted", "~+29%"),
                   ("miss", "5.4 points"),
                   ("final book", "131.70\u00d7"), ("QIB", "256.65\u00d7"),
                   ("retail", "30.49\u00d7")),
            note=(
                "<strong>Listed at &#8377;335 on the NSE against a &#8377;271 issue price, a "
                "premium of 23.62%.</strong> One lot of 55 shares went from &#8377;14,905 to "
                "&#8377;18,425. The call was made on 15 October &mdash; apply one lot retail, "
                "sell into the listing &mdash; and was never revised, including through a "
                "day-two QIB reading this page flagged as the issue&rsquo;s only soft spot "
                "and then recorded as wrong on the 16th when the book closed at 256.65&times;. "
                "<strong>The part worth keeping is the miss, not the win.</strong> The "
                "premium implied about +29% after this page&rsquo;s standard 2.6-point "
                "haircut. It listed at +23.62%. The haircut was three times too small on this "
                "issue. The direction was right and the trade was right; the number was not, "
                "and the footnote says what that does and does not justify changing."
            ),
        ),
        IPO(
            name="Bonfiglioli Transmissions", call="CLOSED 46.04\u00d7 \u2014 QIB went 0.16\u00d7 to 120.78\u00d7",
            tone="good",
            dates="15\u201319 Oct \u00b7 closed \u00b7 listing shortly",
            band="\u20b9558\u2013586", size="~\u20b92,534 Cr",
            split="100% OFS by the Italian parent",
            gmp="was \u20b9130", gmp_pct=22.2, expected="~+20% at the close",
            apply_as="Applied. Retail closed at 5.89\u00d7 \u2014 about one lot in six.",
            horizon="The hold case stands or falls on the listing.",
            book="FINAL 46.04\u00d7 \u00b7 QIB 120.78\u00d7 \u00b7 NII 40.38\u00d7 \u00b7 retail 5.89\u00d7",
            flags=(("QIB 0.16\u00d7 \u2192 120.78\u00d7 in one session", "pass"),
                   ("46.04\u00d7 overall, from 0.99\u00d7", "pass"),
                   ("the refund risk never materialised", "pass"),
                   ("PAT +29.2%, debt-free, ROCE 34.05%", "pass"),
                   ("retail 5.89\u00d7 \u2014 NOT the near-certainty claimed", "fail"),
                   ("100% OFS \u2014 the parent is selling", "fail")),
            stats=(("day 2", "0.99\u00d7"), ("FINAL", "46.04\u00d7"),
                   ("QIB day 2", "0.16\u00d7"), ("QIB final", "120.78\u00d7"),
                   ("NII", "40.38\u00d7"), ("retail", "5.89\u00d7"),
                   ("bids", "139.43 Cr shares"), ("offered", "3.03 Cr shares")),
            note=(
                "<strong>The book went from 0.99&times; to 46.04&times; on its final session, "
                "and institutions from 0.16&times; to 120.78&times;.</strong> On Saturday this "
                "page argued, against the obvious reading, that an empty Friday book was not a "
                "verdict &mdash; because HD Fire had gone 1.49&times; to 256.65&times; on its "
                "own last day and institutions bid late. That argument was right and it was "
                "not close. The refund risk the entry warned about never arrived. "
                "<strong>The sub-claim was wrong and it is the useful part.</strong> The same "
                "entry said retail allotment was &ldquo;near-certain&rdquo; on the strength of "
                "retail sitting at 1.16&times;. Retail closed at 5.89&times; &mdash; roughly "
                "one lot in six. The mistake was treating a day-two retail figure as settled "
                "in the very paragraph that refused to treat a day-two QIB figure as settled. "
                "The reasoning was sound and was applied to one column only."
            ),
        ),
        IPO(
            name="Tonbo Imaging India", call="AVOID \u2014 settles tomorrow, and settles badly",
            tone="bad",
            dates="15\u201319 Oct \u00b7 closed \u00b7 LISTS 23 OCT",
            band="\u20b9665\u2013700", size="\u20b9852.18 Cr",
            split="100% OFS \u2014 the company receives nothing",
            gmp="was \u20b9520", gmp_pct=74.3, expected="~+72% implied",
            apply_as="Did not apply.",
            horizon="None. The call is on the record and the record is about to judge it.",
            book="FINAL 135.90\u00d7 \u00b7 QIB 293.56\u00d7 \u00b7 NII 170.94\u00d7 \u00b7 retail 31.07\u00d7",
            flags=(("135.90\u00d7 final \u2014 the market wanted it badly", "warn"),
                   ("QIB 293.56\u00d7", "warn"),
                   ("premium held above 70% to the close", "warn"),
                   ("revenue \u221222.7%, PAT \u221230% in FY26", "fail"),
                   ("Q1 FY27 a \u20b917.74 Cr LOSS", "fail"),
                   ("negative operating cash flow FY25 AND FY26", "fail"),
                   ("working capital 517 days", "fail")),
            stats=(("day 2", "7.78\u00d7"), ("FINAL", "135.90\u00d7"),
                   ("QIB", "293.56\u00d7"), ("NII", "170.94\u00d7"),
                   ("retail", "31.07\u00d7"),
                   ("GMP at close", "74.3%"), ("lists", "23 Oct")),
            note=(
                "<strong>135.90&times; subscribed, institutions at 293.56&times;, and it "
                "lists tomorrow.</strong> This page called avoid on 13 October at a 61% "
                "premium and restated it four times without revision &mdash; 71.4%, 73.7%, "
                "74.3% &mdash; against accounts that have not moved: revenue down 22.7%, "
                "profit down 30%, a &#8377;17.74 Cr loss in Q1 FY27, operating cash flow "
                "negative in both FY25 and FY26 while profits were reported, working capital "
                "at 517 days, and the company receiving none of the &#8377;852 Cr. "
                "<strong>A book of 135.90&times; and a 74% premium do not list badly very "
                "often.</strong> The call is almost certainly about to be wrong, it is not "
                "being revised the day before the print, and tomorrow&rsquo;s entry will say "
                "so in whatever terms the result deserves. That was the arrangement when it "
                "was made at 61% and it does not change now that the answer is visible."
            ),
        ),
        IPO(
            name="Jio Platforms", call="APPLY STANDS \u2014 day 2 of 3",
            tone="good",
            dates="21\u201323 Oct \u00b7 day 2 \u00b7 allotment 26 Oct \u00b7 lists 28 Oct",
            band="\u20b91,065\u20131,119", size="\u20b930,213 Cr \u2014 the largest ever here",
            split="100% FRESH ISSUE, 27 Cr shares",
            gmp="\u20b9280", gmp_pct=25.0, expected="~+22%, and see the footnote on that",
            apply_as="Retail \u2014 12 shares, \u20b913,428. Closes tomorrow.",
            horizon="Listing-day sell on 28 October.",
            book="day 2 \u00b7 figures not yet published",
            flags=(("100% fresh issue", "pass"),
                   ("premium rose every session of the week before it opened", "pass"),
                   ("\u20b927,500 Cr of proceeds repays DEBT", "warn"),
                   ("size makes a violent pop unlikely", "warn"),
                   ("the GMP haircut just proved too small on HD Fire", "warn")),
            stats=(("band", "\u20b91,065\u20131,119"), ("size", "\u20b930,213 Cr"),
                   ("lot", "12 sh \u00b7 \u20b913,428"),
                   ("for debt", "\u20b927,500 Cr"),
                   ("GMP today", "25.0%"), ("closes", "23 Oct")),
            note=(
                "<strong>The call is unchanged: one lot, retail, sold into the listing.</strong> "
                "Entirely fresh capital, a premium that rose every session of the week before "
                "it opened, and a retail quota large enough in absolute terms that allotment "
                "is a better bet than on a small hot issue. "
                "<strong>Two caveats carried forward, one of them new.</strong> "
                "&#8377;27,500 Cr of the &#8377;30,213 Cr repays debt rather than building "
                "anything &mdash; stated when the call was made and still the main thing a "
                "buyer should know. And HD Fire listed 7.8 points below what its premium "
                "implied, three times this page&rsquo;s standard haircut, so &ldquo;~+22%&rdquo; "
                "here should be read as the top of a range rather than a target."
            ),
        ),
    ]


IPOS_2026_10_22 = _for_22()


LEAD_23 = (
    "Friday 23 October, written at 11:00. "
    "<strong>Tonbo listed at &#8377;1,162 against a &#8377;700 issue price. A 66% "
    "premium. This page said avoid, four times, and was wrong.</strong> The entry below "
    "says why in the terms the result deserves, because that was the arrangement when the "
    "call was made at 61% and it does not get softened now. "
    "<strong>Jio closes today</strong> at 5.81&times; with QIB 13.31&times; and retail "
    "1.67&times;; the apply stands. "
    "<strong>Paras closes today at 0.34&times; with QIB at 0.06&times;</strong> and a "
    "premium down to 2.2% &mdash; the skip stands and barely needed saying. "
    "<strong>Held:</strong> breadth 10.07% against a 26.81% mean, regime bear, entries "
    "blocked for a fourth week."
)

FOOTNOTE_23 = (
    "<strong>The Tonbo call was not unlucky. It answered the wrong question, and this page "
    "can prove it answered the right one eight days earlier.</strong> "
    "On 15 October it wrote of HD Fire: <em>40.7 times for 6.4% growth, entirely a promoter "
    "exit</em> &mdash; and said apply one lot and sell on listing anyway, because the book "
    "and the premium said it would list well. That was right, +23.62%. "
    "On Tonbo it had the same two signals pointing the same way, harder &mdash; a "
    "135.90&times; book, QIB 293.56&times;, a premium above 70% for five sessions &mdash; "
    "and overrode them with the accounts. Same evidence structure, opposite conclusion, and "
    "the only difference was that Tonbo&rsquo;s accounts were worse. "
    "<strong>For a listing-day trade the accounts are not the evidence.</strong> &ldquo;Is "
    "this a good business at this price&rdquo; and &ldquo;will this open above &#8377;700 on "
    "Friday&rdquo; are different questions, and a 517-day working-capital cycle answers the "
    "first and says almost nothing about the second. The accounts earn their place on a "
    "HOLD, where this page never proposed to be. "
    "<strong>The GMP model had a good day and that is worth recording against "
    "Wednesday&rsquo;s bad one.</strong> It implied 64% and Tonbo listed at 66% &mdash; "
    "understated by two points, where HD Fire was overstated by 7.8. Two misses in opposite "
    "directions in one week is noise around the published 2.6-point haircut, not a bias in "
    "it, and the haircut stays."
)


def _for_23() -> list[IPO]:
    """Tonbo lists at +66% and the avoid was wrong; Jio and Paras close."""
    return [
        IPO(
            name="Tonbo Imaging India", call="LISTED +66% \u2014 THE AVOID WAS WRONG",
            tone="bad",
            dates="15\u201319 Oct \u00b7 LISTED TODAY at \u20b91,162",
            band="\u20b9665\u2013700", size="\u20b9852.18 Cr",
            split="100% OFS \u2014 the company received nothing",
            gmp="was \u20b9520", gmp_pct=74.3, expected="GMP implied +64%, listed +66%",
            apply_as="This page said do not apply. That cost the trade.",
            horizon="Closed, and recorded as a loss for the page rather than the book.",
            book="FINAL 135.90\u00d7 \u00b7 QIB 293.56\u00d7 \u00b7 NII 170.94\u00d7 \u00b7 retail 31.07\u00d7",
            flags=(("listed \u20b91,162 vs \u20b9700 \u2014 +66%", "fail"),
                   ("avoid called 13 Oct at 61%, restated four times", "fail"),
                   ("a 135.90\u00d7 book was the signal and was overridden", "fail"),
                   ("QIB 293.56\u00d7 was the signal and was overridden", "fail"),
                   ("the accounts were accurate and were the wrong question", "warn"),
                   ("retail 31.07\u00d7 \u2014 roughly one lot in thirty either way", "warn")),
            stats=(("issue price", "\u20b9700"), ("listed BSE", "\u20b91,162"),
                   ("listed NSE", "\u20b91,160"), ("premium", "+66%"),
                   ("GMP implied", "+64%"), ("final book", "135.90\u00d7"),
                   ("QIB", "293.56\u00d7"), ("this page said", "AVOID")),
            note=(
                "<strong>&#8377;1,162 against &#8377;700. Sixty-six per cent. The call was "
                "avoid and it was wrong.</strong> It was made on 13 October at a 61% premium "
                "and restated on the 16th, 19th, 21st and 22nd at 71.4%, 73.7%, 74.3% and "
                "again &mdash; every time with the book getting larger and the premium "
                "holding. "
                "<strong>The accounts quoted in support of it were all true and none of them "
                "mattered.</strong> Revenue did fall 22.7%. Profit did fall 30%. Q1 FY27 was "
                "a &#8377;17.74 Cr loss, operating cash flow was negative in FY25 and FY26 "
                "while profits were reported, working capital did run to 517 days, and the "
                "company did receive none of the &#8377;852 Cr. All of that describes a "
                "business. None of it describes what a stock does on its first morning when "
                "135.90&times; of money wants it. "
                "<strong>The footnote sets out the actual error</strong>, which is that this "
                "page applied one standard to HD Fire on 15 October and the opposite to Tonbo "
                "with the same signals in front of it."
            ),
        ),
        IPO(
            name="Jio Platforms", call="APPLY \u2014 closes today, book is strong",
            tone="good",
            dates="21\u201323 Oct \u00b7 CLOSES TODAY \u00b7 allotment 26 Oct \u00b7 lists 28 Oct",
            band="\u20b91,065\u20131,119", size="\u20b930,213 Cr \u2014 the largest ever here",
            split="100% FRESH ISSUE, 27 Cr shares",
            gmp="\u20b9245", gmp_pct=21.9, expected="~+19%, and read it as a range",
            apply_as="Retail \u2014 12 shares, \u20b913,428. Today or not at all.",
            horizon="Listing-day sell on 28 October.",
            book="day 3 \u00b7 5.81\u00d7 \u00b7 QIB 13.31\u00d7 \u00b7 NII 6.72\u00d7 \u00b7 retail 1.67\u00d7",
            flags=(("QIB 13.31\u00d7 and institutions bid last", "pass"),
                   ("100% fresh issue \u2014 nobody is cashing out", "pass"),
                   ("book 3.74\u00d7 \u2192 5.81\u00d7 overnight", "pass"),
                   ("retail 1.67\u00d7 and RISING \u2014 not a near-certainty", "warn"),
                   ("\u20b927,500 Cr of proceeds repays DEBT", "warn"),
                   ("GMP eased 25.0% \u2192 21.9% across two sessions", "warn")),
            stats=(("day 2", "3.74\u00d7"), ("day 3", "5.81\u00d7"),
                   ("QIB", "13.31\u00d7"), ("NII", "6.72\u00d7"),
                   ("retail", "1.67\u00d7"),
                   ("for debt", "\u20b927,500 Cr"),
                   ("GMP today", "21.9%"), ("lists", "28 Oct")),
            note=(
                "<strong>The call is unchanged and today is the last day to act on it.</strong> "
                "Institutions are at 13.31&times; and bid latest of all, the book has gone "
                "3.74&times; to 5.81&times; overnight, and it is the only wholly fresh issue "
                "of the month. "
                "<strong>Retail at 1.67&times; is rising and this page is not calling "
                "allotment likely.</strong> It made exactly that mistake on Bonfiglioli at "
                "1.16&times;, which closed at 5.89&times;. Apply expecting a draw. "
                "<strong>Two caveats carried from the day the call was made.</strong> "
                "&#8377;27,500 Cr of &#8377;30,213 Cr repays debt rather than building "
                "anything, and the premium has eased from 25.0% to 21.9% over two sessions. "
                "Treat ~+19% as the top of a range."
            ),
        ),
        IPO(
            name="Paras Healthcare", call="SKIP \u2014 closes today at 0.34\u00d7",
            tone="bad",
            dates="21\u201323 Oct \u00b7 CLOSES TODAY",
            band="up to \u20b9693", size="\u20b91,800 Cr",
            split="\u20b9500 Cr fresh + \u20b91,300 Cr OFS",
            gmp="\u20b915", gmp_pct=2.2, expected="nothing after the haircut",
            apply_as="Do not apply.",
            horizon="None.",
            book="day 3 \u00b7 0.34\u00d7 \u00b7 QIB 0.06\u00d7 \u00b7 NII 0.25\u00d7 \u00b7 retail 1.31\u00d7",
            flags=(("0.34\u00d7 on the final day", "fail"),
                   ("QIB 0.06\u00d7 \u2014 institutions have not come", "fail"),
                   ("GMP 14.4% \u2192 2.2% in seven sessions", "fail"),
                   ("nothing left after the 2.6-point haircut", "fail"),
                   ("72% of the raise is a seller exiting", "fail")),
            stats=(("day 2", "0.23\u00d7"), ("day 3", "0.34\u00d7"),
                   ("QIB", "0.06\u00d7"), ("retail", "1.31\u00d7"),
                   ("GMP 16 Oct", "14.4%"), ("GMP today", "2.2%")),
            note=(
                "<strong>0.34&times; on its final day with institutions at "
                "0.06&times;.</strong> The premium has fallen 14.4% to 2.2% in seven "
                "sessions, which after the haircut this page applies is nothing at all. "
                "<strong>And the Tonbo lesson cuts the other way here, which is worth being "
                "explicit about.</strong> The argument that a weak book is not a verdict "
                "because institutions bid last is real &mdash; Bonfiglioli went 0.16&times; "
                "to 120.78&times; on its last session. So this book may yet fill. It does not "
                "change the call, because the reason to apply was never the book: it was the "
                "expected gain, and at 2.2% there is none to have even if every institution "
                "in the country arrives this afternoon."
            ),
        ),
    ]


IPOS_2026_10_23 = _for_23()


LEAD_26 = (
    "Monday 26 October, written at 11:45. "
    "<strong>Jio&rsquo;s allotment is finalised today and it lists Wednesday the 28th</strong> "
    "&mdash; the apply call made on the 21st settles then, on a book that closed 5.81&times; "
    "with QIB at 13.31&times;. "
    "<strong>Four new issues arrive this week and the exchange book is unavailable for all "
    "of them</strong>: Trendlyne returned 405 this morning, so the only figure on the board "
    "is the grey-market premium, which is the weaker half of the pair and the half this page "
    "trusts least. "
    "<strong>EAAA India Alternatives opened today at a 3.0% premium.</strong> BLS Polymers "
    "opens tomorrow at 25.3%, the strongest quote of the five. "
    "<strong>Held:</strong> breadth 7.78% against a 21.16% mean, regime bear, 11 of 28 "
    "sectors with not one name above its own 20-day average."
)

FOOTNOTE_26 = (
    "<strong>No call is being made on any of the four new issues today, and the reason is "
    "the missing column rather than caution.</strong> Trendlyne did not answer, so there is "
    "no subscription book for any of them &mdash; and the two lessons this month both came "
    "from that column, not from the premium. Bonfiglioli&rsquo;s QIB went 0.16&times; to "
    "120.78&times; on its final session, which is why an empty early book is not a verdict. "
    "Tonbo closed at 135.90&times; with QIB 293.56&times; and listed +66% against this "
    "page&rsquo;s avoid, which is why the book outranks the accounts for a listing-day trade. "
    "Both of those are facts about subscription, and today there is none. "
    "<strong>A premium alone has been wrong in both directions inside ten days</strong> "
    "&mdash; HD Fire quoted 31.4% and listed at 23.62%, Tonbo quoted 74.3% and listed at 66% "
    "after a page-long argument that it should not have. Quoting a GMP and calling it "
    "analysis would be the same mistake with better manners. "
    "<strong>The calls come when the books open.</strong> BLS at 25.3% is the one worth "
    "reading the prospectus for before tomorrow."
)


def _for_26() -> list[IPO]:
    """Jio allots today; four new issues open with no subscription data."""
    return [
        IPO(
            name="Jio Platforms", call="ALLOTMENT TODAY \u2014 lists Wednesday, sell into it",
            tone="good",
            dates="21\u201323 Oct \u00b7 allotment TODAY \u00b7 LISTS 28 OCT",
            band="\u20b91,065\u20131,119", size="\u20b930,213 Cr \u2014 the largest ever here",
            split="100% FRESH ISSUE, 27 Cr shares",
            gmp="last \u20b9245", gmp_pct=21.9, expected="~+19%, read as the top of a range",
            apply_as="Closed. Check allotment; nothing further to do until Wednesday.",
            horizon="Listing-day sell on 28 October.",
            book="FINAL \u00b7 5.81\u00d7 \u00b7 QIB 13.31\u00d7 \u00b7 NII 6.72\u00d7 \u00b7 retail 1.67\u00d7",
            flags=(("QIB 13.31\u00d7 \u2014 institutions came", "pass"),
                   ("100% fresh issue", "pass"),
                   ("\u20b927,500 Cr of proceeds repays DEBT", "warn"),
                   ("retail 1.67\u00d7 \u2014 a draw, not a delivery", "warn"),
                   ("GMP eased 25.0% \u2192 21.9% over the final two sessions", "warn")),
            stats=(("final book", "5.81\u00d7"), ("QIB", "13.31\u00d7"),
                   ("retail", "1.67\u00d7"), ("for debt", "\u20b927,500 Cr"),
                   ("GMP at close", "21.9%"), ("lists", "28 Oct")),
            note=(
                "<strong>The call settles on Wednesday and it is unchanged: sell into the "
                "listing.</strong> The book finished 5.81&times; with institutions at "
                "13.31&times;, which is the signal this page has learned to weight above "
                "everything else, twice, the hard way. "
                "<strong>Two things to carry into Wednesday.</strong> The premium eased from "
                "25.0% to 21.9% over the last two sessions, which is the wrong direction "
                "going into a listing. And &#8377;27,500 Cr of the &#8377;30,213 Cr repays "
                "debt rather than building anything &mdash; that was stated when the call was "
                "made and it has not stopped being true. After HD Fire listed 7.8 points "
                "below what its premium implied, ~+19% here is the top of a range."
            ),
        ),
        IPO(
            name="EAAA India Alternatives", call="NO CALL \u2014 opened today, 3.0% and no book",
            tone="warn",
            dates="26\u201328 Oct \u00b7 OPENED TODAY",
            band="\u20b91,665", size="to confirm", split="to confirm",
            gmp="\u20b950", gmp_pct=3.0, expected="nothing meaningful after the haircut",
            apply_as="No call.",
            horizon="None yet.",
            book="exchange book unavailable \u2014 Trendlyne returned 405",
            flags=(("3.0% premium \u2014 under the 2.6pt haircut, near zero", "fail"),
                   ("no subscription data at all", "warn"),
                   ("quoted 0.0% as recently as 23 Oct", "warn")),
            stats=(("band", "\u20b91,665"), ("GMP 21 Oct", "0.0%"),
                   ("GMP 23 Oct", "0.0%"), ("GMP today", "3.0%"),
                   ("book", "unavailable")),
            note=(
                "<strong>A 3.0% premium on an issue that quoted zero as recently as "
                "Friday.</strong> After the 2.6-point haircut this page applies to every GMP "
                "there is essentially nothing left, and there is no exchange book to check it "
                "against. "
                "That is not a verdict &mdash; a quiet premium on day one says little, as "
                "Bonfiglioli proved &mdash; but there is no case to make either. The "
                "prospectus gets read if the book shows institutional interest when the "
                "subscription feed returns."
            ),
        ),
        IPO(
            name="BLS Polymers", call="OPENS TOMORROW \u2014 the one worth reading tonight",
            tone="warn",
            dates="27\u201329 Oct", band="\u20b9150", size="to confirm", split="to confirm",
            gmp="\u20b938", gmp_pct=25.3, expected="~+23% implied, unverified",
            apply_as="No call until the prospectus is read.",
            horizon="Decide before tomorrow's open.",
            book="opens 27 Oct",
            flags=(("25.3% \u2014 the strongest quote on the board", "pass"),
                   ("premium FIRMED 20.0% \u2192 25.3% over the weekend", "pass"),
                   ("no subscription data yet", "warn"),
                   ("a small issue: a premium moves easily on little volume", "warn")),
            stats=(("band", "\u20b9150"), ("GMP 21 Oct", "20.0%"),
                   ("GMP 23 Oct", "25.3%"), ("GMP today", "25.3%"),
                   ("opens", "27 Oct")),
            note=(
                "<strong>The only one of the five with a premium worth the reading time, and "
                "it firmed over the weekend</strong> &mdash; 20.0% to 25.3% &mdash; where "
                "every other issue this month has faded into its open. "
                "<strong>The caution is size.</strong> On a &#8377;150 band this is a small "
                "issue, and a grey-market quote on a small issue moves on very little money; "
                "it is a thinner signal than the same number on a &#8377;2,500 Cr book. "
                "The prospectus gets read tonight and the call goes on this page before the "
                "book opens, not after."
            ),
        ),
        IPO(
            name="SFC Environmental, M.K.Sons, Bombay Coated", call="QUEUED \u2014 nothing to decide yet",
            tone="warn",
            dates="SFC 27\u201329 \u00b7 M.K.Sons 28\u201330 \u00b7 Bombay Coated 29\u20132 Nov",
            band="\u20b9330 \u00b7 \u20b9162 \u00b7 \u20b982",
            size="to confirm", split="to confirm",
            gmp="9.7% \u00b7 4.9% \u00b7 9.8%", gmp_pct=9.8,
            expected="~+7% at best on the measured haircut",
            apply_as="No calls.",
            horizon="Read in order of opening.",
            book="none open yet",
            flags=(("SFC eased 9.1% \u2192 6.4% \u2192 9.7%", "warn"),
                   ("M.K.Sons 4.9% \u2014 thin", "warn"),
                   ("Bombay Coated 9.8% on an \u20b982 band", "warn"),
                   ("no subscription data for any of them", "warn")),
            stats=(("SFC GMP", "9.7%"), ("M.K.Sons GMP", "4.9%"),
                   ("Bombay Coated GMP", "9.8%"),
                   ("SFC opens", "27 Oct"), ("M.K.Sons opens", "28 Oct"),
                   ("Bombay Coated opens", "29 Oct")),
            note=(
                "<strong>Three issues in single digits, none open, no books.</strong> At "
                "these premiums the measured 2.6-point haircut leaves about seven per cent at "
                "best, which is not enough to carry an application on its own &mdash; and all "
                "three are small enough that the quote is thin. "
                "They are listed here so the week&rsquo;s calendar is on the page rather than "
                "discovered on the morning each opens. Each gets read before its own open."
            ),
        ),
    ]


IPOS_2026_10_26 = _for_26()


LEAD_27 = (
    "Tuesday 27 October, written at 09:40. "
    "<strong>BLS Polymers opened this morning and this page owed a call before it did. "
    "It is late, and the call is apply.</strong> &#8377;255 Cr, every rupee of it fresh, "
    "&#8377;77.56 Cr of that into plant capacity &mdash; the only issue this month whose "
    "money buys something rather than repaying a lender or paying a seller. "
    "<strong>Jio lists tomorrow</strong> on a final book of 5.81&times;, QIB 13.31&times;; "
    "the apply made on the 21st settles then. "
    "<strong>The exchange book has been unavailable for a second day</strong> &mdash; "
    "Trendlyne returned 405 again &mdash; so every figure below except the terms is a "
    "grey-market quote, and this month has shown a quote alone wrong in both directions. "
    "<strong>Held:</strong> breadth 8.97% against a 16.99% mean. It rose for the first time "
    "in five weeks and the gate is still shut."
)

FOOTNOTE_27 = (
    "<strong>The BLS call is made on structure, not on the premium, and the distinction "
    "matters after this month.</strong> What is checkable: &#8377;255 Cr entirely fresh, "
    "1.70 Cr shares, a stated use of proceeds that puts &#8377;77.56 Cr into plant capacity "
    "and &#8377;89.50 Cr into working capital, and roughly 25 times FY26 diluted earnings of "
    "&#8377;5.99 at the top of the band. Those are facts from the terms. "
    "<strong>What is not checkable, and is said rather than hidden:</strong> no revenue, "
    "profit or margin figures could be read this morning, and there is no subscription book "
    "for a second day. So this is a call on how the issue is built and what the money does, "
    "with two of the three columns missing. "
    "<strong>It is also late.</strong> On the 26th this page wrote that the prospectus would "
    "be read overnight and the call would go up <em>before</em> the book opened. It did not. "
    "The issue runs to Thursday so the application is still live, but the commitment was "
    "missed and saying so is cheaper than pretending the timing was always Tuesday."
)


def _for_27() -> list[IPO]:
    """BLS opens and gets its call; Jio lists tomorrow."""
    return [
        IPO(
            name="BLS Polymers", call="APPLY \u2014 one lot, the only issue whose money builds something",
            tone="good",
            dates="27\u201329 Oct \u00b7 OPEN \u00b7 allotment 30 Oct \u00b7 lists 3 Nov",
            band="\u20b9142\u2013150", size="\u20b9255 Cr",
            split="100% FRESH ISSUE \u2014 1.70 Cr shares, no OFS",
            gmp="\u20b940", gmp_pct=26.7, expected="~+24% implied, unverified",
            apply_as="Retail \u2014 100 shares, \u20b915,000 at the top band. Closes Thursday.",
            horizon="Listing-day sell on 3 November.",
            book="no exchange book \u2014 Trendlyne 405 for a second day",
            flags=(("100% fresh issue, no seller taking money out", "pass"),
                   ("\u20b977.56 Cr into PLANT CAPACITY \u2014 real capex", "pass"),
                   ("~25\u00d7 FY26 diluted EPS of \u20b95.99", "pass"),
                   ("premium FIRMED 20.0% \u2192 25.3% \u2192 26.7% while others faded", "pass"),
                   ("\u20b989.50 Cr is working capital, not growth", "warn"),
                   ("no revenue, profit or margin figures readable", "warn"),
                   ("no subscription book, second day", "warn"),
                   ("\u20b9255 Cr is small \u2014 a quote moves on little money", "warn")),
            stats=(("band", "\u20b9142\u2013150"), ("size", "\u20b9255 Cr"),
                   ("fresh shares", "1.70 Cr"), ("lot", "100 sh \u00b7 \u20b915,000"),
                   ("plant capacity", "\u20b977.56 Cr"),
                   ("working capital", "\u20b989.50 Cr"),
                   ("FY26 diluted EPS", "\u20b95.99"), ("P/E at \u20b9150", "~25\u00d7"),
                   ("GMP today", "26.7%"), ("lists", "3 Nov")),
            note=(
                "<strong>Set against everything else this month, the structure is the "
                "argument.</strong> HD Fire was a full promoter exit. Tonbo was a full exit "
                "where the company received nothing. Bonfiglioli was a full exit by an "
                "Italian parent. Jio is fresh but nine rupees in ten repay debt. This is "
                "&#8377;255 Cr entirely fresh with &#8377;77.56 Cr going into plant capacity "
                "&mdash; the only issue on the month&rsquo;s board where a meaningful share "
                "of the money buys productive assets. "
                "<strong>And it is not expensive.</strong> About 25 times FY26 diluted "
                "earnings of &#8377;5.99 at the top of the band, against Tonbo&rsquo;s 79 "
                "times falling earnings and HD Fire&rsquo;s 40.7 times for 6.4% growth. "
                "<strong>What is missing is said plainly.</strong> No revenue, profit or "
                "margin figures could be read this morning, and there is no subscription "
                "book for a second day &mdash; which is the column this month taught twice "
                "is the one that matters for a listing. &#8377;89.50 Cr of the raise is "
                "working capital, which for a compounder funds inventory and receivables "
                "rather than growth. "
                "<strong>One lot, retail, &#8377;15,000, sold into the 3 November "
                "listing.</strong> If the book appears and institutions are absent at the "
                "close on Thursday, that is a reason to revisit before the money moves."
            ),
        ),
        IPO(
            name="Jio Platforms", call="LISTS TOMORROW \u2014 sell into it",
            tone="good",
            dates="21\u201323 Oct \u00b7 allotted \u00b7 LISTS 28 OCT",
            band="\u20b91,065\u20131,119", size="\u20b930,213 Cr",
            split="100% FRESH ISSUE, 27 Cr shares",
            gmp="last \u20b9245", gmp_pct=21.9, expected="~+19%, the top of a range",
            apply_as="Closed and allotted. Nothing to do until tomorrow.",
            horizon="Listing-day sell, 28 October.",
            book="FINAL \u00b7 5.81\u00d7 \u00b7 QIB 13.31\u00d7 \u00b7 NII 6.72\u00d7 \u00b7 retail 1.67\u00d7",
            flags=(("QIB 13.31\u00d7 \u2014 institutions came", "pass"),
                   ("100% fresh issue", "pass"),
                   ("\u20b927,500 Cr of proceeds repays DEBT", "warn"),
                   ("premium eased 25.0% \u2192 21.9% into the close", "warn"),
                   ("retail 1.67\u00d7 \u2014 a draw", "warn")),
            stats=(("final book", "5.81\u00d7"), ("QIB", "13.31\u00d7"),
                   ("retail", "1.67\u00d7"), ("for debt", "\u20b927,500 Cr"),
                   ("GMP at close", "21.9%"), ("lists", "28 Oct")),
            note=(
                "<strong>The call settles tomorrow and does not change tonight.</strong> "
                "Sell into the listing. The book finished 5.81&times; with institutions at "
                "13.31&times;, which after Tonbo is the number this page weights above the "
                "accounts for a listing-day trade. "
                "<strong>Two things that argue for selling rather than holding.</strong> The "
                "premium eased from 25.0% to 21.9% over the final two sessions, which is the "
                "wrong direction into a listing; and &#8377;27,500 Cr of the &#8377;30,213 Cr "
                "repays debt, so the balance sheet improves but nothing gets built. "
                "After HD Fire listed 7.8 points below what its premium implied, ~+19% is "
                "the top of a range rather than a target."
            ),
        ),
        IPO(
            name="SFC Environmental, EAAA, M.K.Sons, Bombay Coated", call="NO \u2014 premiums too thin to carry an application",
            tone="bad",
            dates="SFC + EAAA open \u00b7 M.K.Sons 28\u201330 \u00b7 Bombay Coated 29\u20132 Nov",
            band="\u20b9330 \u00b7 \u20b91,665 \u00b7 \u20b9162 \u00b7 \u20b982",
            size="to confirm", split="to confirm",
            gmp="6.7% \u00b7 1.2% \u00b7 4.9% \u00b7 11.0%", gmp_pct=11.0,
            expected="~+8% at the very best, mostly nothing",
            apply_as="Do not apply to any of them.",
            horizon="None.",
            book="no exchange book for any \u2014 Trendlyne 405",
            flags=(("EAAA 3.0% \u2192 1.2% on its second day", "fail"),
                   ("SFC 9.7% \u2192 6.7% as it opened", "fail"),
                   ("M.K.Sons 4.9% \u2014 nothing after the haircut", "fail"),
                   ("Bombay Coated 11.0% but does not open until Thursday", "warn"),
                   ("no subscription data for any of the four", "warn")),
            stats=(("SFC GMP 26 Oct", "9.7%"), ("SFC today", "6.7%"),
                   ("EAAA 26 Oct", "3.0%"), ("EAAA today", "1.2%"),
                   ("M.K.Sons", "4.9%"), ("Bombay Coated", "11.0%")),
            note=(
                "<strong>Both issues that opened this week faded as they opened.</strong> "
                "EAAA has gone 3.0% to 1.2% on its second day and SFC 9.7% to 6.7% on its "
                "first. After the 2.6-point haircut this page applies to every quote, EAAA "
                "is negative and SFC is about four per cent. "
                "A premium that falls into its own open is the one pattern this month that "
                "has been reliable &mdash; Paras went 14.4% to 2.2% and closed at "
                "0.34&times; with institutions at 0.06&times;. "
                "<strong>Bombay Coated at 11.0% is the only one of the four worth looking at "
                "again</strong>, and it does not open until Thursday, so there is time to do "
                "it properly rather than from a price band."
            ),
        ),
    ]


IPOS_2026_10_27 = _for_27()


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
    "2026-10-08": (IPOS_2026_10_08, LEAD_08, FOOTNOTE_08),
    "2026-10-09": (IPOS_2026_10_09, LEAD_09, FOOTNOTE_09),
    "2026-10-12": (IPOS_2026_10_12, LEAD_12, FOOTNOTE_12),
    "2026-10-13": (IPOS_2026_10_13, LEAD_13, FOOTNOTE_13),
    "2026-10-14": (IPOS_2026_10_14, LEAD_14, FOOTNOTE_14),
    "2026-10-15": (IPOS_2026_10_15, LEAD_15, FOOTNOTE_15),
    "2026-10-16": (IPOS_2026_10_16, LEAD_16, FOOTNOTE_16),
    "2026-10-19": (IPOS_2026_10_19, LEAD_19, FOOTNOTE_19),
    "2026-10-21": (IPOS_2026_10_21, LEAD_21, FOOTNOTE_21),
    "2026-10-22": (IPOS_2026_10_22, LEAD_22, FOOTNOTE_22),
    "2026-10-23": (IPOS_2026_10_23, LEAD_23, FOOTNOTE_23),
    "2026-10-26": (IPOS_2026_10_26, LEAD_26, FOOTNOTE_26),
    "2026-10-27": (IPOS_2026_10_27, LEAD_27, FOOTNOTE_27),
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
