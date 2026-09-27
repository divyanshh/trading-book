#!/usr/bin/env python3
"""Render the public article from its frozen research evidence.

Requires markdown and beautifulsoup4. No network or trading-service calls.
"""
import csv
import html
import json
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

D = Path(__file__).resolve().parent
REPO = D.parents[2]
PAGE = REPO / 'analysis/2026-09-27_entry_selection.html'
PREFIX = 'data/2026-09-27_entry_selection/'


def rows(name):
    with (D / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def esc(value):
    return html.escape(str(value))


def lakh(value):
    return f'₹{float(value)/100000:,.2f}L'


def rupees(value):
    return f'₹{float(value):,.0f}'


def table(headers, data, table_id=None):
    identity = f' id="{table_id}"' if table_id else ''
    return '<div class="tbl-scroll" tabindex="0" role="region" aria-label="Scrollable data table"><table'+identity+'><thead><tr>'+''.join('<th scope="col">'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join(data)+'</tbody></table></div>'


FIELDS = {'adr20': 'ADR20 (%)', 'mom20': '20-session return (%)', 'mom60': '60-session return (%)',
          'rs60': '60-session return minus NIFTYBEES (pp)', 'ext20': 'Extension above SMA20 (%)',
          'ext50': 'Extension above SMA50 (%)', 'ma20_over_50': 'SMA20 > SMA50',
          'ma50_rising': 'SMA50 rising over 20 sessions', 'near_high20': 'Close / 20-session high (%)',
          'near_high60': 'Close / 60-session high (%)', 'volume_ratio': 'Prior volume / preceding 20 mean',
          'dryup5': '5-session mean volume / 20-session mean', 'median_turnover20_cr': '20-session median turnover (₹Cr)',
          'is_etf': 'ETF', 'history': 'Prior sessions'}
RANKS = {'rs60': 'Rank relative 60-session return, highest first', 'mom20': 'Rank 20-session return, highest first',
         'mom60': 'Rank 60-session return, highest first', 'turnover': 'Rank turnover, highest first',
         'low_extension': 'Rank signed MA20 extension, lowest first', 'near_high20': 'Rank proximity to 20-session high, highest first'}


def explain(policy):
    parts = []
    for key, op, value in policy['conditions']:
        if isinstance(value, bool):
            parts.append(FIELDS[key] + (' required' if value else ' excluded'))
        else:
            parts.append(FIELDS[key] + ' ' + {'ge': '≥', 'le': '≤', 'eq': '='}[op] + ' ' + str(value))
    if policy.get('rank'):
        parts.append(RANKS[policy['rank']])
    if policy.get('no_duplicate'):
        parts.append('One held lot per stock')
    return '; '.join(parts) or 'No extra entry filter; original row order'


def main():
    policies = {p['name']: p for p in json.loads((D / 'candidate-library.json').read_text())['policies']}
    features = {int(r['id']): r for r in rows('features-and-outcomes.csv')}
    decisions = {name: {int(r['id']): r for r in rows(name+'-decisions.csv')}
                 for name in ['baseline', 'adr_2_to_5', 'posthoc_adr_2_to_4']}
    base_ids = {int(r['id']) for r in rows('baseline-trades.csv')}
    results = rows('all-policy-results.csv')

    library = '<section id="all-filters"><h2>All 59 first-screen results</h2><p>Every declared candidate is shown, including weak and negative results. Rows are sorted by full-period P&amp;L; this ordering was not known before testing. “Later cohort” uses a fresh ₹60L account for July–September entries and cannot be added to the first-period result.</p>'
    result_rows = []
    for number, r in enumerate(results, 1):
        style = ' class="baseline-row"' if r['name'] == 'baseline' else ''
        result_rows.append('<tr'+style+'>'+''.join('<td>'+esc(v)+'</td>' for v in [number, explain(policies[r['name']]), lakh(r['total']), r['taken'], r['filtered'], lakh(r['train_pnl']), lakh(r['later_pnl'])])+'</tr>')
    library += table(['#', 'Entry rule (all inputs lagged)', 'Full P&L', 'Taken', 'Filtered', 'Apr–Jun', 'Later cohort'], result_rows, 'policy-table')
    library += '<p>Relative strength here is the difference between two 60-session percentage returns, not a point-in-time universe percentile. Volume and turnover use completed prior sessions. Missing required features fail a gate and rank last. Multiple conditions in a row are ANDed. The exact machine-readable definitions are in <a href="'+PREFIX+'candidate-library.json">candidate-library.json</a>.</p></section>'

    skipped = [r for r in features.values() if r['baseline_decision'] != 'taken']
    skipped.sort(key=lambda r: float(r['standalone_pnl']), reverse=True)
    skip_rows = []
    for r in skipped:
        i = int(r['id']); b = decisions['baseline'][i]
        d5, d4 = decisions['adr_2_to_5'][i]['decision'], decisions['posthoc_adr_2_to_4'][i]['decision']
        attrs = f' data-search="{esc(r["symbol"]+" "+r["entry_date"])}" data-band5="{d5}" data-band4="{d4}" data-positive="{str(float(r["standalone_pnl"])>0).lower()}"'
        cells = [str(i),r['symbol'],r['entry_date'],b['decision'],b['slots_used'],rupees(b['cash_before']),
                 f'{float(r["adr20"]):.2f}%' if r['adr20'] else 'Unavailable',lakh(r['standalone_pnl']),d5,d4]
        skip_rows.append('<tr'+attrs+'>'+''.join('<td>'+esc(v)+'</td>' for v in cells)+'</tr>')
    explorer = '''<section id="skipped-explorer"><h2>Explore all 86 skipped trades</h2>
<p>Sorted by hypothetical standalone outcome for explanation only. These outcomes include open marks and are not jointly fundable. “Slots” is the first recorded rejection; it can overlap a cash shortage. “Filter” means the new entry gate rejected the setup. A different admission path can keep a qualifying trade out for lack of capacity.</p>
<div class="explorer-controls"><label for="trade-search">Stock or entry date<input id="trade-search" type="search" placeholder="e.g. LAURUSLABS or 2026-07" autocomplete="off"></label>
<label for="trade-view">Show<select id="trade-view"><option value="all">All skipped trades</option><option value="band5">Admitted by ADR 2%–5%</option><option value="band4">Admitted by ADR 2%–4%</option><option value="positive">Positive standalone outcome</option><option value="negative">Negative standalone outcome</option></select></label></div>
<p id="trade-count" role="status" aria-live="polite">86 of 86 skipped trades shown.</p>'''
    explorer += table(['ID','Stock','Entry date','Baseline reason','Slots used','Cash before','Prior ADR','Standalone P&L','With 2%–5%','With 2%–4%'],skip_rows,'skipped-table')+'</section>'

    substitutions = '<section id="substitutions"><h2>Every added and displaced lot</h2><p>These are portfolio substitutions, not one-to-one swaps. Earlier decisions change which later lots can fit. Removed trades can be profitable; newly admitted trades can lose. Amounts use the same modeled exits and September 22 mark.</p>'
    for name, label in [('adr_2_to_5','ADR 2%–5%'),('posthoc_adr_2_to_4','ADR 2%–4% (post-screening)')]:
        ids = {int(r['id']) for r in rows(name+'-trades.csv')}
        for title, group in [('Newly admitted',ids-base_ids),('Displaced baseline',base_ids-ids)]:
            sr = []
            for i in sorted(group, key=lambda i:float(features[i]['standalone_pnl']), reverse=True):
                r=features[i]
                sr.append('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [r['symbol'],r['entry_date'],f'{float(r["adr20"]):.2f}%' if r['adr20'] else 'Unavailable',lakh(r['standalone_pnl']),r['simulated_exit_reason'],decisions[name][i]['decision']])+'</tr>')
            total=sum(float(features[i]['standalone_pnl']) for i in group)
            substitutions += f'<details><summary>{label}: {title.lower()} — {len(group)} lots, {lakh(total)} contribution</summary>'
            substitutions += table(['Stock','Entry date','Prior ADR','Lot P&L','Exit / mark status','New decision'],sr)+'</details>'
    substitutions += '</section>'

    downloads = '<section id="downloads"><h2>Download the evidence</h2><p><a class="download-button" href="'+PREFIX+'evidence.zip" download>Download the complete evidence package (ZIP)</a> <a href="'+PREFIX+'README.md">Read the package notes</a></p><p>The package contains the 127 frozen feature/outcome rows, all decision and trade ledgers, daily equity, all filter results, costs and timing checks, the public allocation verifier, and file hashes. It does not contain raw historical OHLC panels, credentials, account identifiers or private service source code.</p><details><summary>Browse individual files</summary><ul>'
    for file in sorted(D.iterdir()):
        if file.suffix not in ('.csv','.json','.md','.py','.png') or file.name=='build_page.py':continue
        downloads += '<li><a href="'+PREFIX+file.name+'">'+esc(file.name)+'</a></li>'
    downloads += '</ul></details></section>'

    source=(D/'report.md').read_text().split('\n',1)[1]
    article=BeautifulSoup(markdown.markdown(source, extensions=['tables','fenced_code','toc']), 'html.parser')
    for tag in article.find_all(['a','img']):
        attr='href' if tag.name=='a' else 'src'
        target=tag.get(attr,'')
        if target and not target.startswith(('https://','http://','#')):
            tag[attr]=PREFIX+target
    for t in article.find_all('table'):
        container=article.new_tag('div',attrs={'class':'tbl-scroll','tabindex':'0','role':'region','aria-label':'Scrollable comparison table'})
        t.wrap(container)
        for th in t.find_all('th'):th['scope']='col'
    for img in article.find_all('img'):
        img['loading']='lazy';img['width']='2280';img['height']='952'
    # Insert deep evidence beside the narrative it supports.
    target=article.find('h2',id='costs-cash-timing-and-entry-order')
    target.insert_before(BeautifulSoup(explorer+substitutions,'html.parser'))
    target=article.find('h2',id='reproduction-and-verification')
    target.insert_before(BeautifulSoup(library,'html.parser'))
    article.append(BeautifulSoup(downloads,'html.parser'))

    style=re.search(r'<style>.*?</style>',(REPO/'index.html').read_text(),re.S).group(0)
    style=style[:-8]+(REPO/'analysis/_bridge.css').read_text()+'</style>'
    title='₹60L entry filters: why 86 trades were skipped'
    header='''<header class="top"><p class="eyebrow"><a href="../index.html">Morning Book</a> · research / 27 September 2026</p>
<div class="rule-top"></div><h1>86 skipped trades.<br>Could entry filters improve the result?</h1>
<p class="lede">A detailed audit of the ₹21.94L backtest: capacity failures, 59 entry rules, changed holdings, and what survives the cost and timing checks.</p>
<div class="meta"><span>Fixed ₹60 lakh</span><span>127 historical opportunities</span><span>1 April–22 September 2026</span><span>Same no-breakeven exit policy</span></div></header>
<div class="stats"><div class="stat"><div class="k">Original portfolio</div><div class="v">₹21.94L</div><div class="s">₹10.18L realized · ₹11.76L open</div></div>
<div class="stat"><div class="k">ADR 2%–5% · first screen</div><div class="v">₹24.12L</div><div class="s">₹11.06L realized · ₹13.06L open</div></div>
<div class="stat"><div class="k">ADR 2%–4% · explored afterward</div><div class="v">₹26.96L</div><div class="s">₹7.07L realized · ₹19.89L open</div></div></div>
<nav class="toc" aria-label="Report sections"><a href="#why-the-original-86-were-skipped">Why skipped</a><a href="#portfolio-results-with-the-exits-held-fixed">Results</a><a href="#the-actual-filters">Exact rules</a><a href="#skipped-explorer">All 86 trades</a><a href="#costs-cash-timing-and-entry-order">Stress checks</a><a href="#all-filters">All 59 filters</a><a href="#downloads">Evidence</a></nav>'''
    footer='<footer>Research published 27 September 2026. This is a conditional historical replay, not an expected production return. Related: <a href="2026-09-25_ms_vs_ours.html">MarketSmith exits versus ours</a> · <a href="2026-09-24_fixed_book_replay.html">Earlier fixed-capital replay</a> · <a href="../index.html">Morning Book index</a>.</footer>'
    PAGE.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Why 86 historical trades were skipped under a ₹60 lakh cap; a detailed audit of 59 entry filters, ADR tests, capital constraints and open profit."><title>'+title+'</title>'+style+'<link rel="stylesheet" href="2026-09-27_entry_selection.css"></head><body><main class="wrap entry-study">'+header+str(article)+footer+'</main><script src="2026-09-27_entry_selection.js" defer></script></body></html>',encoding='utf-8')
    print(PAGE)


if __name__=='__main__':main()
