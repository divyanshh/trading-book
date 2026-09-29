"""Publish the recovered April strategy audit from frozen local outputs."""

import html
import json
import re
import shutil
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RESEARCH = REPO.parent / "crypto-exact-manual-2026-09-28"
PAGE = REPO / "analysis/2026-09-28_exact_crypto.html"

template = (REPO / "analysis/2026-09-28_crypto_thresholds.html").read_text()
style = re.search(r"<style>.*?</style>", template, re.S)
if style is None:
    raise ValueError("site style not found")

report = (RESEARCH / "REPORT.md").read_text()
report = re.sub(r"^# .+?\n", "", report, count=1)
content = markdown.markdown(report, extensions=["tables", "fenced_code"])
content = content.replace(
    "<code>crypto_service/strategies/recovered_manual_tis.py</code>",
    '<a href="https://github.com/divyanshh/crypto-service/blob/main/crypto_service/strategies/recovered_manual_tis.py"><code>recovered_manual_tis.py</code></a>',
)

body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Exact April crypto fill reconciliation, recovered three-mode TIS selector, and a six-month $100-risk hourly backtest."><title>Can code reproduce the April crypto trades?</title>{style.group()}<link rel="stylesheet" href="2026-09-28_crypto_thresholds.css"></head><body><main class="wrap crypto-study">
<header class="top"><p class="eyebrow"><a href="../index.html">Morning Book</a> · crypto research / 28 September 2026</p><h1>Can code reproduce<br>the April crypto trades?</h1><p class="dek">An exact nine-position fill reconciliation, a symbol-blind three-mode strategy with 100% April candidate recall, and the six-month test that shows what the archive still cannot recover.</p><div class="meta"><span>Exact tape: 9 positions</span><span>Backtest: 6 months</span><span>Backtest risk: $100/trade</span><span>Live risk: $30/trade</span><span>Agents: 0 dynos</span></div></header>
<nav class="toc"><a href="#what-exact-can-and-cannot-mean">Exactness</a><a href="#the-recovered-entry-family">Rules</a><a href="#april-parity-test">April parity</a><a href="#six-month-backtest">Backtest</a><a href="#implementation-and-decision">Decision</a></nav>
<section id="report">{content}</section>
<footer>Research published 28 September 2026. Historical replay is not an expected return. <a href="../index.html">Morning Book index</a>.</footer></main></body></html>'''
PAGE.write_text(body)

HERE.mkdir(parents=True, exist_ok=True)
shutil.copyfile(RESEARCH / "results.json", HERE / "results.json")
for name in (
    "recovered_5r_025adr_6k.json",
    "recovered_8r_025adr_6k.json",
    "recovered_5r_050adr_6k.json",
    "recovered_5r_025adr_12k.json",
    "automatic_pullback_5r_025adr_6k.json",
    "automatic_pullback_8_5r_028dry_12k.json",
    "automatic_pullback_5r_028dry_12k.json",
):
    shutil.copyfile(RESEARCH / name, HERE / name)

results = json.loads((RESEARCH / "results.json").read_text())
summary = {
    "published_at": "2026-09-28",
    "exact_tape": results["exact_tape"],
    "selector_audit": {
        key: value
        for key, value in results["selector_audit"].items()
        if key != "candidate_days"
    },
    "variants": results["variants"],
    "live_status": "manual_tis_automatic_8_5r deployed at $30 risk/trade in cryptoo-service; agents kept at zero dynos",
}
(HERE / "summary.json").write_text(json.dumps(summary, indent=2))

index = REPO / "index.html"
text = index.read_text()
href = "analysis/2026-09-28_exact_crypto.html"
title = "Can code reproduce the April crypto trades?"
size = max(1, PAGE.stat().st_size // 1024)
if href not in text:
    row = (
        f'<tr><td class="l"><a href="{href}">{html.escape(title)}</a></td>'
        '<td class="l"><span class="badge">analysis</span></td>'
        f'<td class="l">2026-09-28</td><td class="l"></td><td>{size} KB</td></tr>'
    )
    marker = '<h2>Analysis</h2><div class="scroll"><table><thead>'
    start = text.index(marker)
    tbody = text.index("<tbody>", start) + len("<tbody>")
    text = text[:tbody] + row + text[tbody:]
else:
    text = re.sub(
        rf'({re.escape(href)}.*?<td class="l"></td><td>)\d+ KB',
        rf"\g<1>{size} KB",
        text,
        count=1,
    )
index.write_text(text)
print(PAGE)
