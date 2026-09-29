"""Build the public crypto threshold report from frozen local research outputs."""

import html
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RESEARCH = REPO.parent / "crypto-gate-optimization-2026-09-28"
PAGE = REPO / "analysis/2026-09-28_crypto_thresholds.html"

template = (REPO / "analysis/2026-09-27_entry_selection.html").read_text()
style = re.search(r"<style>.*?</style>", template, re.S)
if style is None:
    raise ValueError("site style not found")

frontier = json.loads((RESEARCH / "expanded-hourly-frontier-full.json").read_text())
stress = json.loads((RESEARCH / "expanded-hourly-finalist-stress.json").read_text())
locked = json.loads((RESEARCH / "expanded-hourly-locked-results.json").read_text())[0]
balanced = next(row for row in frontier if row["id"] == "expanded_high_r_156")
profit = next(row for row in frontier if row["id"] == "expanded_high_r_226")


def money(value: str) -> str:
    return f"${float(value):+,.2f}"


def pct(value: str) -> str:
    return f"{float(value):.1f}%"


def metric(row: dict, label: str) -> str:
    return (
        f"<article><b>{html.escape(label)}</b><strong>{money(row['net'])}</strong>"
        f"<span>{row['wins']}/{row['closed_positions']} wins · {pct(row['win_rate_pct'])}</span></article>"
    )


stress_rows = "".join(
    "<tr>"
    f"<td>{html.escape(row['id'].removeprefix('expanded_high_r_'))} / {html.escape(row['scenario'])}</td>"
    f"<td>{row['closed_positions']}</td><td>{row['wins']}</td>"
    f"<td>{pct(row['win_rate_pct'])}</td><td>{money(row['closed_net'])}</td>"
    f"<td>{money(row['open_net'])}</td><td>{money(row['net'])}</td>"
    f"<td>{float(row['profit_factor']):.2f}</td>"
    f"<td>{pct(row['max_hour_close_drawdown_pct'])}</td></tr>"
    for row in stress
)

frontier_rows = "".join(
    "<tr>"
    f"<td>{html.escape(row['id'])}</td><td>{row['closed_positions']}</td>"
    f"<td>{row['wins']}</td><td>{pct(row['win_rate_pct'])}</td>"
    f"<td>{money(row['closed_net'])}</td><td>{money(row['net'])}</td>"
    f"<td>{float(row['profit_factor']):.2f}</td>"
    f"<td>{pct(row['max_hour_close_drawdown_pct'])}</td></tr>"
    for row in frontier
)

body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A seeded crypto threshold search porting equity's eight-gate logic, with exact-hourly validation, $100 risk and full disclosure of the failed locked selection."><title>Crypto thresholds: what survived the six-month replay</title>{style.group()}<link rel="stylesheet" href="2026-09-28_crypto_thresholds.css"></head><body><main class="wrap crypto-study">
<header class="top"><p class="eyebrow"><a href="../index.html">Morning Book</a> · crypto research / 28 September 2026</p><h1>Crypto thresholds:<br>what survived the six-month replay</h1><p class="dek">1,536 seeded threshold profiles, exact hourly trade and mark execution, $100 risk per trade, and a locked-period failure that changes the conclusion.</p><div class="meta"><span>Period 27 Mar–26 Sep 2026</span><span>Capital $6,000</span><span>Risk up to $100</span><span>Published 28 Sep 2026</span></div></header>
<nav class="toc"><a href="#answer">Answer</a><a href="#rules">Rules</a><a href="#results">Results</a><a href="#validation">Validation</a><a href="#evidence">Evidence</a></nav>
<section id="answer"><h2>The answer</h2><p class="warning"><strong>There is no honestly validated optimum yet.</strong> The automatically selected development winner lost <strong>{money(locked['closed_net'])}</strong> in the locked August–September period. The balanced profile below is the best paper candidate after inspecting the complete six months; it is not ready for live capital.</p><div class="stats">{metric(balanced, 'Balanced high-R')}{metric(profit, 'Profit-oriented')}</div><p>The balanced candidate produced <strong>20 closed trades, nine wins (45%), {money(balanced['closed_net'])} closed profit</strong>, {money(balanced['open_net'])} open P&amp;L after reserved exit costs, profit factor {float(balanced['profit_factor']):.2f}, and {pct(balanced['max_hour_close_drawdown_pct'])} maximum hourly-close drawdown. It preserves the requested high reward/risk: a six-historical-ADR target and at least 4R at plan and simulated fill.</p></section>
<section id="rules"><h2>The crypto numbers</h2><div class="scroll"><table><thead><tr><th>Gate</th><th>Balanced crypto threshold</th><th>Logic retained</th></tr></thead><tbody>
<tr><td>G1</td><td>Close ≤2% above SMA10</td><td>Do not chase the short moving average</td></tr>
<tr><td>G2</td><td>Close ≤8% above SMA20; forgive through 12% when momentum ≥30%</td><td>Cap extension but allow exceptional strength</td></tr>
<tr><td>G3</td><td>30-day return ≥0%</td><td>Mandatory trend direction</td></tr>
<tr><td>G4</td><td>Daily base and contraction ≤8%</td><td>Mandatory, objectively bounded setup</td></tr>
<tr><td>G5</td><td>30-day return minus BTC ≥−10 points</td><td>Crypto leadership context</td></tr>
<tr><td>G6</td><td>Last completed funding observation ≥−0.01%</td><td>Historical setup-time context; missing blocks</td></tr>
<tr><td>G7</td><td>30-day universe percentile ≥60</td><td>Cross-sectional leadership proxy</td></tr>
<tr><td>G8</td><td>Historical ADR20 between 1% and 8%</td><td>Volatility at entry, never today's ADR written backward</td></tr>
<tr><td>Admission</td><td>G1–G4 mandatory; at least 6/8</td><td>Current equity tolerance shape; missing inputs never pass</td></tr>
<tr><td>Exit</td><td>6 ADR target; minimum 4R</td><td>High reward/risk requested by the user</td></tr>
</tbody></table></div><p>Every ADR reading uses only the twenty completed daily UTC candles available at that historical signal. BTC-relative strength, return percentile and funding are likewise frozen at the setup timestamp.</p></section>
<section id="results"><h2>Full six-month results and stress</h2><p>All results use 5bps fees and 5bps adverse slippage on each side plus 3bps/day adverse funding unless the row says doubled costs. The $1,200 notional cap and integer contracts often reduce actual structural risk below $100.</p><div class="scroll"><table><thead><tr><th>Profile / scenario</th><th>Closed</th><th>Wins</th><th>Win rate</th><th>Closed net</th><th>Open net</th><th>Total</th><th>PF</th><th>Drawdown</th></tr></thead><tbody>{stress_rows}</tbody></table></div><p class="good">The balanced candidate retained <strong>{money(next(r for r in stress if r['id'].endswith('_156') and r['scenario']=='double_costs')['closed_net'])}</strong> closed profit under doubled costs and <strong>{money(next(r for r in stress if r['id'].endswith('_156') and r['scenario']=='one_hour_later')['closed_net'])}</strong> with entry delayed one hour.</p></section>
<section id="validation"><h2>Why this is still paper-only</h2><p>The first 768 profiles copied equity-scale ranges. None qualified. The June–July development section had only five BTC-above-EMA50 dates, so treating each calendar half as if it should trade equally was wrong.</p><p>The expanded search tested another 384 runners and 384 high-R profiles. Exact-hourly development ended on 31 July. A profile needed at least 15 closed trades, positive closed profit, profit factor at least 1.2, drawdown no more than 25%, and a positive one-sided 90% lower confidence score. No equity-style uncapped runner qualified. Eight high-R profiles did.</p><p>The locked winner had 20 development trades, six wins, +$623.83 closed profit and 8.0% drawdown. In August–September it produced six closed trades, one win and <strong>{money(locked['closed_net'])}</strong> closed profit. Two open positions marked at {money(locked['open_net'])}, leaving total P&amp;L {money(locked['net'])}. That is a failed locked test.</p><p>Seven other qualifying profiles were positive in the locked-period diagnostic, but selecting among them after seeing those outcomes would be data snooping. The balanced candidate is therefore a frozen forward-paper hypothesis. Changing its thresholds during forward observation restarts validation.</p><h3>All eight development-qualified profiles over the complete, already-inspected six months</h3><div class="scroll"><table><thead><tr><th>Profile</th><th>Closed</th><th>Wins</th><th>Win rate</th><th>Closed net</th><th>Total</th><th>PF</th><th>Drawdown</th></tr></thead><tbody>{frontier_rows}</tbody></table></div></section>
<section id="evidence"><h2>Reproduction and evidence</h2><p>The offline command now accepts crypto-specific SMA extension, momentum, BTC-relative, funding, percentile, ADR, gate-count, mandatory-gate and reward/risk parameters. The balanced command reproduced the saved summary exactly: 20 closed, nine wins and {money(balanced['net'])} total P&amp;L.</p><p>Verification: 808 tests passed with one existing skip. Changed source files pass Ruff and strict mypy. The repository-wide Ruff check is blocked by a pre-existing long line in <code>crypto_service/tasks.py</code>; repository-wide mypy is blocked by two pre-existing errors in <code>backtest_tis_chop.py</code>.</p><p>Downloads: <a href="data/2026-09-28_crypto_thresholds/summary.json">summary</a> · <a href="data/2026-09-28_crypto_thresholds/frontier-full.json">full finalist table</a> · <a href="data/2026-09-28_crypto_thresholds/frontier-validation.json">locked frontier diagnostic</a> · <a href="data/2026-09-28_crypto_thresholds/finalist-stress.json">cost and latency stress</a> · <a href="data/2026-09-28_crypto_thresholds/selection-lock.json">selection lock</a> · <a href="data/2026-09-28_crypto_thresholds/cli-verification.json">command replay</a>.</p><p>Production configuration was not changed, no order was placed, and both agent processes remain intended to stay at zero dynos.</p></section>
<footer>Research published 28 September 2026. Historical replay is not an expected return. <a href="../index.html">Morning Book index</a>.</footer></main></body></html>'''

PAGE.write_text(body)
HERE.mkdir(parents=True, exist_ok=True)
copies = {
    "expanded-hourly-frontier-full.json": "frontier-full.json",
    "expanded-hourly-frontier-validation.json": "frontier-validation.json",
    "expanded-hourly-finalist-stress.json": "finalist-stress.json",
    "expanded-hourly-selection-lock.json": "selection-lock.json",
    "balanced-cli-verification.json": "cli-verification.json",
}
for source, target in copies.items():
    shutil.copyfile(RESEARCH / source, HERE / target)

summary = {
    "published_at": "2026-09-28",
    "currency": "USD",
    "capital": "6000",
    "risk_budget_per_trade": "100",
    "balanced_profile": balanced,
    "profit_profile": profit,
    "locked_selected_profile": locked,
    "conclusion": "balanced profile is paper-only because it was synthesized after locked validation",
}
(HERE / "summary.json").write_text(json.dumps(summary, indent=2))

index = REPO / "index.html"
index_text = index.read_text()
href = "analysis/2026-09-28_crypto_thresholds.html"
if href not in index_text:
    row = (
        f'<tr><td class="l"><a href="{href}">Crypto thresholds: what survived the six-month replay</a></td>'
        '<td class="l"><span class="badge">analysis</span></td><td class="l">2026-09-28</td>'
        '<td class="l"></td><td>29 KB</td></tr>'
    )
    marker = '<h2>Analysis</h2><div class="scroll"><table><thead><tr><th class="l">document</th>'
    start = index_text.index(marker)
    tbody = index_text.index("<tbody>", start) + len("<tbody>")
    index.write_text(index_text[:tbody] + row + index_text[tbody:])
else:
    index.write_text(
        re.sub(
            r'(2026-09-28_crypto_thresholds\.html.*?<td class="l"></td><td>)\d+ KB',
            r'\g<1>29 KB',
            index_text,
            count=1,
        )
    )

print(PAGE)
