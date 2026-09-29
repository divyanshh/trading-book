#!/usr/bin/env python3
"""Verify the published admission ledgers using frozen features and exits.

Standard library only. Does not fetch data, calculate OHLC indicators, replay
stops, connect to a broker, or place orders. See README.md for scope.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    with (ROOT / name).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def typed(value):
    if value == '':
        return None
    if value in ('True', 'False'):
        return value == 'True'
    try:
        return float(value)
    except ValueError:
        return value


ROWS = [{key: typed(value) for key, value in row.items()}
        for row in read('features-and-outcomes.csv')]


def passes(row, policy):
    for key, operator, limit in policy['conditions']:
        value = row[key]
        if value is None:
            return False
        if operator == 'ge' and value < limit:
            return False
        if operator == 'le' and value > limit:
            return False
        if operator == 'eq' and value != limit:
            return False
    return True


def rank(row, policy):
    ranking = policy.get('rank')
    if not ranking:
        return 0
    key = {'turnover': 'median_turnover20_cr', 'low_extension': 'ext20'}.get(ranking, ranking)
    value = row[key]
    if value is None:
        return math.inf
    return value if ranking == 'low_extension' else -value


def replay(policy):
    cash = 6_000_000.0
    live, accepted = [], []
    for row in sorted(ROWS, key=lambda r: (r['entry_date'], rank(r, policy))):
        for holding in live[:]:
            if (holding['simulated_exit_reason'] != 'open'
                    and holding['simulated_exit_date'] <= row['entry_date']):
                cash += holding['quantity'] * holding['simulated_exit_price']
                live.remove(holding)
        if not passes(row, policy):
            continue
        if policy.get('no_duplicate') and any(h['symbol'] == row['symbol'] for h in live):
            continue
        cost = row['quantity'] * row['entry']
        assert row['quantity'] == int(500_000 / row['entry'])
        if len(live) >= 12 or cost > cash + 1e-7:
            continue
        cash -= cost
        accepted.append(row)
        live.append(row)
        assert cash >= -1e-6 and len(live) <= 12
        assert sum(h['quantity'] * h['entry'] for h in live) <= 6_000_000 + 1e-6
    return {
        'total': sum(r['quantity'] * (r['simulated_exit_price'] - r['entry']) for r in accepted),
        'taken': len(accepted),
        'ids': [int(r['id']) for r in accepted],
    }


def main():
    policies = json.loads((ROOT / 'candidate-library.json').read_text())['policies']
    expected = {r['name']: r for r in read('all-policy-results.csv')}
    policies.append({'name': 'posthoc_adr_2_to_4', 'conditions': [['adr20', 'ge', 2], ['adr20', 'le', 4]],
                     'rank': None, 'no_duplicate': False})
    expected.update({r['name']: r for r in read('posthoc-independent-checks.csv')})
    for policy in policies:
        actual = replay(policy)
        target = expected[policy['name']]
        assert abs(actual['total'] - float(target['total'])) < .01, (policy['name'], actual, target)
        assert actual['taken'] == int(target['taken'])
        ledger = ROOT / (policy['name'] + '-trades.csv')
        if ledger.exists():
            assert actual['ids'] == [int(r['id']) for r in read(ledger.name)]
        print(f"{policy['name']}: INR {actual['total']:,.2f}; {actual['taken']} lots; verified")
    print('All 59 first-screen policies and the post-screening 2%-4% portfolio match.')
    print('This verifies allocation from supplied features/exits, not those inputs against market data.')


if __name__ == '__main__':
    main()
