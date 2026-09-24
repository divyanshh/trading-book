# Fixed capital replay, 24 September 2026

Capital ₹60 lakh, up to ₹5 lakh per entry in whole shares, 12 positions, one holding per stock. Historical dates and prices retained; original quantities ignored. All 132 opportunities considered without new scanner admission gates. This is a conditional exit and portfolio replay, not validation of the entire current scanner pipeline.

The service's production trailing function is imported at the commit in manifest.json. Historical daily OHLC panel is a required local input, not redistributed here. SHA256 hashes identify the exact panel and published inputs. Obtain the same trusted local panel; never load an untrusted pickle. Install the service's normal dependencies, then run replay.py with --service, --panel and --output. The published script does not fetch prices. Without the panel this package is inspectable but not self-contained.

Unknown initial stops remain unknown. Baseline assumes 5% below entry for 39 missing values; 8 of those candidates execute in baseline. inputs.csv preserves empty originals. new_stop is a precomputed structural alternative for a separate sensitivity, not recovered history; it follows the earlier entry-stop audit's source-to-strategy mapping.

Daily-bar approximation: prior-session MA20; 8% breakeven; 97% MA20 trail through production next_stop; close stop breach exits next session open; disaster line 95% of stop uses worse of open/line; entry-day low excluded unless sensitivity requests it. Defensive regime disabled in baseline because its historical sequence is unavailable. High-sampled and always-defensive cases are sensitivities, not reconstructed intraday executions. No forced 60-session exit in baseline. Share adjustment factors are explicit in script. End marks at 22 September are not closed profit.

Costs: 0.25% of entry value round-trip estimate reserved on entry; 0.5% exit/terminal-mark slippage. Morning close-stop exit proceeds can fund same-day entries; other proceeds release next date. Within a date the baseline sorts by record ID, not a known historical arrival order. 500 deterministic random orderings vary only this ordering. These are sensitivity cases, not a probability distribution of market returns. No result is a forecast or out-of-sample validation. No post-hoc best ordering is recommended.

all_132.csv explains every baseline candidate. highest/median_example decision ledgers likewise cover 132. CSV monetary values are rupees, not lakhs. Same-stock separate lots and zero-cost cases intentionally relax baseline assumptions; they are not production-compliant recommendations.

Known price/date anomalies are retained and must be resolved against source contract notes before accepting a precise result. WELCORP 22 May is flagged as a duplicate/date-price inconsistency; its modeled open gain materially affects totals. RUBICON's large gain in the highest ordering uses an assumed missing stop.
