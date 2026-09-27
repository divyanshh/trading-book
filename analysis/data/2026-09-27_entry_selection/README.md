# Entry-selection evidence — 27 September 2026

Published study: [Why 86 trades were skipped](../../2026-09-27_entry_selection.html).

This package studies 127 supplied historical opportunities, entered April 1–September 11 and marked through September 22, 2026. All monetary CSV values are rupees, not lakhs. Candidate IDs are zero-based and remain stable across files.

## Fixed rules

Start with ₹6,000,000. Maximum ₹500,000 purchase value per lot, ₹40,000 initial structural risk, twelve simultaneous lots, no external cash. Separate lots in the same stock are allowed. Original row order breaks same-date ties unless a ranking policy explicitly overrides it. Primary runs reuse same-date sale proceeds. Cash/timing variants are separately labeled.

Initial structural stop is 92% of entry. Disaster protection is 95% of that stop. Close below the ratcheted structural stop exits at the next session's open. Trail is the greater of the existing stop and 97% of the mean of twenty post-entry closes, including the current close. No breakeven, target or eight-week hold. The entry session is excluded. Closed exits include 0.5% slippage; headline open gains are terminal marks, not liquidation proceeds.

## Files and scope

- `features-and-outcomes.csv`: all 127 opportunities, lagged features, source entry prices and frozen simulated exit outcomes. Feature `asof` is strictly before entry. `standalone_pnl` is not constrained by the portfolio's cash.
- `candidate-library.json`: the 59 first-screen policies, including baseline. All conditions are ANDed. Missing required features fail the filter and rank last.
- `all-policy-results.csv`: every first-screen result, including poor performers. Later-cohort results start a fresh account and cannot be added to the first-period results.
- `posthoc-sensitivity-checks.csv`: subsequent threshold, combination and history-only checks. Some repeat first-screen rules as controls. ADR 2%–4% was explored after the first screen.
- `*-decisions.csv`, `*-trades.csv`, `*-daily-equity.csv`: full ledgers and marked account paths. `holding_ids` refers to `id` in the feature/outcome file. Decisions release qualifying sale proceeds before evaluating the next candidate.
- `extended-robustness.csv`: costs, same-date proceeds restrictions, symbol-exclusion reruns, and 200 matched same-date queue permutations for headline policies.
- `paired-queue-tests.csv`: raw 200-queue comparisons for the selected initial policies. The later 2%–4% follow-up's aggregate is in `extended-robustness.csv`; do not assume it is in this earlier raw file.
- `independent-ledger-checks.csv`, `posthoc-independent-checks.csv`: results verified with the separate prior-audit ledger.
- `validation.json`: verification metadata, substitutions and hashes of original local sources. Machine-specific paths have been removed. Raw OHLC data and private service repositories are not included.
- `report.md`, `selection-results.png`: narrative and standalone figure.
- `manifest.json`: SHA256 hashes of public evidence files, excluding itself and the ZIP.

ADR20 is 100 times the mean of (high−low)/close over twenty completed prior sessions. It is not ATR or a close-to-close proxy. Relative strength is the difference from NIFTYBEES' 60-session return, not a universe percentile. Known share splits were normalized in the original analysis. Historical fill/data-quality limitations remain; this is not a replay of the complete production scanner.

## Public allocation verification

Download and extract `evidence.zip`, then run Python 3.9+:

```sh
python3 replay.py
```

The standard-library-only verifier checks the ₹60L cash ledger and reproduces P&L, accepted counts, and saved trade IDs for all 59 first-screen policies plus the post-screening 2%–4% rule. It uses the published frozen features and exits. It does **not** recompute features from OHLC, independently verify historical prices, rerun the stop engine, or reproduce the chronological strategy-selection experiments. Those checks used the original trusted local panels and service code. The verifier makes no network, database, broker or filesystem-write calls.

`build_page.py` renders the article inside a checkout of the trading-book repository and requires `markdown` and `beautifulsoup4`. It does not recalculate research results. Its paths assume this directory stays under `analysis/data/`.

The source book, selected exit strategy and filters reuse the same examined history. Queue permutations are not independent market samples. No untouched out-of-sample validation, statistical significance or forward return is claimed.
