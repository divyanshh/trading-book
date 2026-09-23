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


def write(day: str, markup: str) -> None:
    standalone = ROOT / "extras" / f"{day}_ipo_review.html"
    override = ROOT / "overrides" / f"{day}.html"
    page = override.read_text(encoding="utf-8") if override.exists() else ""
    style = re.search(r"<style>.*?</style>", page, re.S)
    if style:
        standalone.write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>IPO review — {day}</title>{style.group(0)}</head><body>"
            f'<div class="wrap"><p class="eyebrow">equity-service · cortex · {day}</p>'
            f"{markup}"
            "<footer>Hand-written under <code>cortex/checklists/ipo_checklist.md</code>. "
            f'Also a section of <a href="{day}.html#ipo-review">the day\'s report</a>.'
            "</footer></div></body></html>",
            encoding="utf-8",
        )
    if page:
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


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-09-23"
    write(day, section(IPOS_2026_09_23, LEAD, FOOTNOTE))
    print(f"{day}: {len(IPOS_2026_09_23)} issues written to extras/ and overrides/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
