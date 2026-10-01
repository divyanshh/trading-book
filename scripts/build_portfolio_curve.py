#!/usr/bin/env python3
"""Build the daily audited equity P&L curve shown on the public homepage.

The broker tradebook supplies every fill, so partial exits reduce the open
quantity on the day they happened.  The audited position book remains the
source of truth for realised P&L because it contains the final reconciled P&L
per position.  Open FIFO lots are marked to the daily close in the audit panel.
"""

from __future__ import annotations

import argparse
import pickle
from collections import defaultdict, deque
from pathlib import Path

import pandas as pd


CAPITAL = 2_000_000.0
EXCLUDED = {"LIQUIDCASE", "LIQUIDBEES"}
SYMBOL_ALIASES = {"GVTD": "GVT&D"}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fills", type=Path, required=True)
    parser.add_argument("--book", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--nifty", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def consume_fifo(lots: dict[str, deque[list[float]]], symbol: str, quantity: float) -> float:
    """Remove only inventory acquired inside the measurement window."""
    remaining = quantity
    consumed = 0.0
    while remaining > 1e-8 and lots[symbol]:
        take = min(remaining, lots[symbol][0][0])
        lots[symbol][0][0] -= take
        remaining -= take
        consumed += take
        if lots[symbol][0][0] <= 1e-8:
            lots[symbol].popleft()
    return consumed


def main() -> None:
    args = arguments()
    fills = pd.read_csv(args.fills)
    fills["date"] = pd.to_datetime(fills["trade_date"])
    fills["timestamp"] = pd.to_datetime(fills["order_execution_time"])
    fills["symbol"] = fills["symbol"].replace(SYMBOL_ALIASES)
    fills = fills[~fills["symbol"].isin(EXCLUDED)].sort_values(["timestamp", "trade_id"])

    book = pd.read_csv(args.book)
    book["symbol"] = book["symbol"].replace(SYMBOL_ALIASES)
    book["exit_date"] = pd.to_datetime(book["exit_date"])
    book = book[~book["symbol"].isin(EXCLUDED)].copy()
    if len(book) != 132:
        raise ValueError(f"Expected the audited 132-position cohort, found {len(book)}")

    with args.panel.open("rb") as handle:
        panel = pickle.load(handle)
    nifty = pd.read_csv(args.nifty, parse_dates=["date"]).sort_values("date")
    calendar = pd.DatetimeIndex(nifty["date"])

    # The downloaded broker tradebook ends on 10 September. Add the confirmed
    # later closes from the audited book, capped at the still-open broker
    # inventory so an audit-row quantity correction cannot create a short.
    last_fill_date = fills["date"].max()
    late = book[book["exit_date"] > last_fill_date].sort_values("exit_date")
    late_events: dict[pd.Timestamp, list[tuple[str, float]]] = defaultdict(list)
    for row in late.itertuples():
        late_events[row.exit_date].append((row.symbol, float(row.qty)))

    realised_by_day = book.groupby("exit_date")["pnl"].sum()
    lots: dict[str, deque[list[float]]] = defaultdict(deque)
    rows: list[dict[str, float | int | str]] = []
    realised = 0.0
    nifty_base = float(nifty.iloc[0]["close"])

    for day in calendar:
        for fill in fills[fills["date"] == day].itertuples():
            quantity = float(fill.quantity)
            if fill.trade_type == "buy":
                lots[fill.symbol].append([quantity, float(fill.price)])
            else:
                # Unmatched sells are opening inventory acquired before 1 April
                # and therefore outside this six-month cohort.
                consume_fifo(lots, fill.symbol, quantity)

        for symbol, quantity in late_events.get(day, []):
            consume_fifo(lots, symbol, quantity)

        realised += float(realised_by_day.get(day, 0.0))
        unrealised = 0.0
        open_positions = 0
        for symbol, symbol_lots in lots.items():
            quantity = sum(lot[0] for lot in symbol_lots)
            if quantity <= 1e-8:
                continue
            if symbol not in panel:
                raise KeyError(f"No daily close series for open symbol {symbol}")
            closes = panel[symbol].loc[panel[symbol].index <= day, "c"]
            if closes.empty:
                continue
            close = float(closes.iloc[-1])
            unrealised += sum(qty * (close - cost) for qty, cost in symbol_lots)
            open_positions += 1

        nifty_close = float(nifty.loc[nifty["date"] == day, "close"].iloc[0])
        total = realised + unrealised
        rows.append(
            {
                "date": day.date().isoformat(),
                "realised_pnl": round(realised, 2),
                "unrealised_pnl": round(unrealised, 2),
                "total_pnl": round(total, 2),
                "portfolio_return_pct": round(total / CAPITAL * 100, 4),
                "nifty_close": round(nifty_close, 2),
                "nifty_return_pct": round((nifty_close / nifty_base - 1) * 100, 4),
                "open_positions": open_positions,
            }
        )

    output = pd.DataFrame(rows)
    final_realised = float(output.iloc[-1]["realised_pnl"])
    if abs(final_realised - 363_934.46) > 0.01:
        raise ValueError(f"Audited final P&L changed: {final_realised}")
    if int(output.iloc[-1]["open_positions"]) != 0:
        raise ValueError("The audited cohort must have no open positions at the end")
    peak = output.loc[output["unrealised_pnl"].idxmax()]
    if not 500_000 <= float(peak["unrealised_pnl"]) <= 510_000:
        raise ValueError(f"Unexpected unrealised peak: {peak['unrealised_pnl']}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(
        f"wrote {len(output)} sessions; peak unrealised "
        f"₹{peak['unrealised_pnl']:,.2f} on {peak['date']}; "
        f"final realised ₹{final_realised:,.2f}"
    )


if __name__ == "__main__":
    main()
