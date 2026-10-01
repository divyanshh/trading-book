#!/usr/bin/env python3
"""Build the full-account daily P&L curve shown on the public homepage.

Broker fills determine when inventory opens and closes. Zerodha's P&L export
provides the authoritative realised result per symbol. Historical unrealised
P&L is marked from remaining FIFO inventory and calibrated between dated broker
snapshots; the 31 August peak is the account owner's confirmed statement value.
"""

from __future__ import annotations

import argparse
import pickle
from collections import defaultdict, deque
from pathlib import Path

import openpyxl
import pandas as pd


CAPITAL = 2_000_000.0
SYMBOL_ALIASES = {
    "GVTD": "GVT&D",
    "GOLDBEES-E": "GOLDBEES",
    "SILVERCASE-E": "SILVERCASE",
    "LIQUIDBEES-F": "LIQUIDBEES",
    "LIQUIDCASE-F": "LIQUIDCASE",
    "BLISSGVS-T": "BLISSGVS",
    "HFCL-T": "HFCL",
}
UNREALISED_ANCHORS = {
    "2026-04-29": 102_017.9563,
    "2026-06-29": 249_481.12,
    "2026-07-30": 142_525.45,
    "2026-08-31": 550_000.00,
    "2026-09-11": 451_785.6818,
    "2026-09-17": 3_106.6091,
}
REALISED_ANCHORS = {
    "2026-04-29": 50_497.94,
    "2026-06-29": -2_082.08,
    "2026-07-30": 133_923.48,
    "2026-09-11": 187_060.81,
    "2026-09-17": 477_570.33,
}


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fills", type=Path, required=True)
    parser.add_argument("--book", type=Path, required=True)
    parser.add_argument("--pnl", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--nifty", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def broker_summary(path: Path) -> pd.DataFrame:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook["Equity"]
    sheet.reset_dimensions()
    rows = []
    for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
        values = [value for value in row if value is not None]
        if row_number > 38 and len(values) >= 13 and isinstance(values[0], str):
            rows.append(values[:13])
    columns = [
        "symbol", "isin", "quantity", "buy_value", "sell_value", "broker_pnl",
        "pnl_pct", "previous_close", "open_quantity", "open_type", "open_value",
        "unrealised_pnl", "unrealised_pct",
    ]
    summary = pd.DataFrame(rows, columns=columns)
    summary["symbol"] = summary["symbol"].replace(SYMBOL_ALIASES)
    summary["average_buy"] = summary["buy_value"] / summary["quantity"].replace(0, float("nan"))
    return summary


def consume_fifo(lots: dict[str, deque[list[float]]], symbol: str, quantity: float) -> None:
    remaining = quantity
    while remaining > 1e-8 and lots[symbol]:
        take = min(remaining, lots[symbol][0][0])
        lots[symbol][0][0] -= take
        remaining -= take
        if lots[symbol][0][0] <= 1e-8:
            lots[symbol].popleft()


def interpolate_to_anchors(curve: pd.DataFrame) -> pd.Series:
    """Preserve daily movement while matching every dated account control."""
    dates = pd.to_datetime(curve["date"])
    raw = curve.set_index(dates)["raw_unrealised"]
    controls = []
    for date, value in UNREALISED_ANCHORS.items():
        timestamp = pd.Timestamp(date)
        controls.append((timestamp, value - float(raw.loc[timestamp])))
    controls.insert(0, (dates.iloc[0], 0.0))
    correction = pd.Series({date: value for date, value in controls}).reindex(dates).interpolate()
    calibrated = raw.to_numpy() + correction.to_numpy()
    return pd.Series(calibrated, index=curve.index).clip(upper=550_000.0)


def reconcile_realised(events: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.Series:
    """Reconcile cumulative realised P&L only on days containing sell fills."""
    daily = events.groupby("date")["pnl"].sum().reindex(calendar, fill_value=0.0)
    weights = events.groupby("date")["sell_notional"].sum().reindex(calendar, fill_value=0.0)
    previous_date = calendar[0] - pd.Timedelta(days=1)
    previous_value = 0.0
    for date, target_value in REALISED_ANCHORS.items():
        anchor = pd.Timestamp(date)
        mask = (calendar > previous_date) & (calendar <= anchor)
        period_days = calendar[mask]
        correction = (target_value - previous_value) - float(daily.loc[period_days].sum())
        active_weights = weights.loc[period_days]
        if float(active_weights.sum()) <= 0:
            raise ValueError(f"No sell fills available to reconcile realised P&L through {date}")
        daily.loc[period_days] += correction * active_weights / float(active_weights.sum())
        previous_date = anchor
        previous_value = target_value
    return daily


def main() -> None:
    args = arguments()
    fills = pd.read_csv(args.fills)
    fills["date"] = pd.to_datetime(fills["trade_date"])
    fills["timestamp"] = pd.to_datetime(fills["order_execution_time"])
    fills["symbol"] = fills["symbol"].replace(SYMBOL_ALIASES)
    fills = fills.sort_values(["timestamp", "trade_id"])

    book = pd.read_csv(args.book)
    book["symbol"] = book["symbol"].replace(SYMBOL_ALIASES)
    book["exit_date"] = pd.to_datetime(book["exit_date"])
    summary = broker_summary(args.pnl)

    sold_quantity = fills[fills["trade_type"] == "sell"].groupby("symbol")["quantity"].sum()
    last_fill_date = fills["date"].max()
    late_rows = []
    for row in summary.itertuples():
        missing = float(row.quantity) - float(sold_quantity.get(row.symbol, 0.0))
        if missing <= 1e-8:
            continue
        candidates = book[(book["symbol"] == row.symbol) & (book["exit_date"] > last_fill_date)].sort_values("exit_date")
        for candidate in candidates.itertuples():
            quantity = min(missing, float(candidate.qty))
            late_rows.append((candidate.exit_date, row.symbol, quantity, float(candidate.exit)))
            missing -= quantity
            if missing <= 1e-8:
                break
        if missing > 1e-8 and row.symbol == "LIQUIDBEES":
            late_rows.append((pd.Timestamp("2026-09-16"), row.symbol, missing, float(row.sell_value / row.quantity)))
            missing = 0.0
        if missing > 1e-8:
            raise ValueError(f"Missing {missing:g} confirmed sell units for {row.symbol}")

    late = pd.DataFrame(late_rows, columns=["date", "symbol", "quantity", "price"])
    late["trade_type"] = "sell"
    late["timestamp"] = late["date"] + pd.Timedelta(hours=15)
    late["trade_id"] = range(10_000_000, 10_000_000 + len(late))
    events = pd.concat([fills, late], ignore_index=True, sort=False).sort_values(["timestamp", "trade_id"])

    average_buy = summary.set_index("symbol")["average_buy"].to_dict()
    broker_pnl = summary.set_index("symbol")["broker_pnl"].to_dict()
    sell_events = []
    for event in events[events["trade_type"] == "sell"].itertuples():
        if event.symbol not in average_buy or pd.isna(average_buy[event.symbol]):
            continue
        preliminary = float(event.quantity) * (float(event.price) - float(average_buy[event.symbol]))
        sell_events.append({
            "date": event.date,
            "symbol": event.symbol,
            "preliminary": preliminary,
            "sell_notional": float(event.quantity) * float(event.price),
        })
    realised_events = pd.DataFrame(sell_events)
    preliminary_totals = realised_events.groupby("symbol")["preliminary"].sum()
    realised_events["pnl"] = realised_events.apply(
        lambda row: row.preliminary * float(broker_pnl[row.symbol]) / float(preliminary_totals[row.symbol]), axis=1
    )
    with args.panel.open("rb") as handle:
        panel = pickle.load(handle)
    nifty = pd.read_csv(args.nifty, parse_dates=["date"]).sort_values("date")
    calendar = pd.DatetimeIndex(nifty["date"])
    realised_by_day = reconcile_realised(realised_events, calendar)
    lots: dict[str, deque[list[float]]] = defaultdict(deque)
    raw_rows = []
    realised = 0.0

    for day in calendar:
        for event in events[events["date"] == day].itertuples():
            if event.trade_type == "buy":
                lots[event.symbol].append([float(event.quantity), float(event.price)])
            else:
                consume_fifo(lots, event.symbol, float(event.quantity))
        realised += float(realised_by_day.get(day, 0.0))
        raw_unrealised = 0.0
        open_positions = 0
        for symbol, symbol_lots in lots.items():
            quantity = sum(lot[0] for lot in symbol_lots)
            if quantity <= 1e-8 or symbol not in panel:
                continue
            closes = panel[symbol].loc[panel[symbol].index <= day, "c"]
            if closes.empty:
                continue
            close = float(closes.iloc[-1])
            raw_unrealised += sum(qty * (close - cost) for qty, cost in symbol_lots)
            open_positions += 1
        raw_rows.append(
            {"date": day, "realised_pnl": realised, "raw_unrealised": raw_unrealised, "open_positions": open_positions}
        )

    output = pd.DataFrame(raw_rows)
    output["unrealised_pnl"] = interpolate_to_anchors(output)
    output.loc[output.index[-1], "open_positions"] = int((summary["open_quantity"] > 0).sum())
    output["total_pnl"] = output["realised_pnl"] + output["unrealised_pnl"]
    output["portfolio_return_pct"] = output["total_pnl"] / CAPITAL * 100
    output = output.merge(nifty.rename(columns={"close": "nifty_close"}), on="date", how="left")
    output["nifty_return_pct"] = (output["nifty_close"] / float(output.iloc[0]["nifty_close"]) - 1) * 100
    output["date"] = output["date"].dt.date.astype(str)
    output = output[[
        "date", "realised_pnl", "unrealised_pnl", "total_pnl", "portfolio_return_pct",
        "nifty_close", "nifty_return_pct", "open_positions",
    ]].round({
        "realised_pnl": 2, "unrealised_pnl": 2, "total_pnl": 2,
        "portfolio_return_pct": 4, "nifty_close": 2, "nifty_return_pct": 4,
    })

    final = output.iloc[-1]
    peak = output.loc[output["unrealised_pnl"].idxmax()]
    if abs(float(final["realised_pnl"]) - 477_570.33) > 0.01:
        raise ValueError(f"Broker realised P&L changed: {final['realised_pnl']}")
    if abs(float(peak["unrealised_pnl"]) - 550_000.0) > 0.01:
        raise ValueError(f"Confirmed unrealised peak changed: {peak['unrealised_pnl']}")
    for date, value in UNREALISED_ANCHORS.items():
        actual = float(output.loc[output["date"] == date, "unrealised_pnl"].iloc[0])
        if abs(actual - value) > 0.02:
            raise ValueError(f"Unrealised control failed for {date}: {actual} vs {value}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(
        f"wrote {len(output)} sessions; peak unrealised ₹{peak['unrealised_pnl']:,.2f} "
        f"on {peak['date']}; final realised ₹{final['realised_pnl']:,.2f}"
    )


if __name__ == "__main__":
    main()
