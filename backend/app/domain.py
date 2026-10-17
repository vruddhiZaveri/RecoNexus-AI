"""Pure INR prototype. No database writes or AI decisions."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import csv
import io
import re
from collections import Counter, defaultdict

@dataclass(frozen=True)
class Transaction:
    record_id: str
    reference: str
    business_date: date
    amount: Decimal
    currency: str
    direction: str

    def __post_init__(self):
        if not isinstance(self.amount, Decimal) or not self.amount.is_finite():
            raise ValueError('amount must be a finite Decimal')
        if self.amount <= 0 or self.amount >= Decimal('10000000000000000') or self.amount.as_tuple().exponent < -2:
            raise ValueError('amount must be positive, within NUMERIC(18,2), with at most two decimals')
        if self.currency != 'INR' or self.direction not in ('CREDIT', 'DEBIT'):
            raise ValueError('unsupported currency or direction')
        if not self.record_id.strip() or not isinstance(self.business_date, date):
            raise ValueError('invalid identity or date')
        if self.reference != self.reference.strip():
            raise ValueError('reference must be normalized')

@dataclass(frozen=True)
class Outcome:
    matches: tuple[tuple[str, str], ...]
    exceptions: tuple[tuple[str, str, str], ...]  # side, record ID, reason

HEADERS = ['record_id', 'reference', 'business_date', 'amount', 'currency', 'direction']

def parse_csv(text: str) -> tuple[Transaction, ...]:
    if len(text.encode('utf-8')) > 10 * 1024 * 1024:
        raise ValueError('file exceeds 10 MB')
    reader = csv.DictReader(io.StringIO(text), strict=True)
    if reader.fieldnames != HEADERS:
        raise ValueError('headers must exactly match template')
    rows, seen = [], set()
    for number, row in enumerate(reader, start=2):
        try:
            if number > 100001:
                raise ValueError('row limit exceeded')
            if None in row or any(value is None for value in row.values()):
                raise ValueError('incorrect column count')
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['business_date']):
                raise ValueError('date must be YYYY-MM-DD')
            if not re.fullmatch(r'\d+(?:\.\d{1,2})?', row['amount']):
                raise ValueError('amount must be a positive decimal string, at most two fractional digits')
            identity = row['record_id'].strip()
            if identity in seen:
                raise ValueError('duplicate record_id within source')
            record = Transaction(identity, row['reference'].strip(), date.fromisoformat(row['business_date']),
                                 Decimal(row['amount']), row['currency'], row['direction'])
            seen.add(identity)
            rows.append(record)
        except ValueError as exc:
            raise ValueError(f'row {number}: {exc}') from exc
    if not rows:
        raise ValueError('empty batch')
    return tuple(rows)

def reconcile(left: tuple[Transaction, ...], right: tuple[Transaction, ...]) -> Outcome:
    """Conservative exact-v1: any reused reference within a side is ambiguous.

    Inputs represent one sealed source pair and period. Persistent scope locking,
    duplicate delivery prevention and audit are responsibilities of future services.
    """
    for records in (left, right):
        if len({r.record_id for r in records}) != len(records):
            raise ValueError('duplicate source identity')
    counts = [Counter(r.reference for r in records) for records in (left, right)]
    indexes = []
    for records in (left, right):
        index = defaultdict(list)
        for r in records:
            index[r.reference].append(r)
        indexes.append(index)
    matches, exceptions, used = [], [], set()
    for a in sorted(left, key=lambda r: r.record_id):
        if not a.reference:
            exceptions.append(('A', a.record_id, 'INSUFFICIENT_REFERENCE'))
        elif counts[0][a.reference] > 1 or counts[1][a.reference] > 1:
            exceptions.append(('A', a.record_id, 'AMBIGUOUS_REFERENCE'))
        elif not indexes[1][a.reference]:
            exceptions.append(('A', a.record_id, 'NO_REFERENCE_COUNTERPART'))
        else:
            b = indexes[1][a.reference][0]
            if (a.amount, a.currency, a.direction, a.business_date) == (b.amount, b.currency, b.direction, b.business_date):
                matches.append((a.record_id, b.record_id))
                used.add(b.record_id)
            else:
                exceptions.append(('A', a.record_id, 'FIELD_DISCREPANCY'))
    for b in sorted(right, key=lambda r: r.record_id):
        if b.record_id in used:
            continue
        reason = ('INSUFFICIENT_REFERENCE' if not b.reference else
                  'AMBIGUOUS_REFERENCE' if counts[0][b.reference] > 1 or counts[1][b.reference] > 1 else
                  'NO_REFERENCE_COUNTERPART' if not indexes[0][b.reference] else 'FIELD_DISCREPANCY')
        exceptions.append(('B', b.record_id, reason))
    return Outcome(tuple(matches), tuple(exceptions))
