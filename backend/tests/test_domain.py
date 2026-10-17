import unittest
from datetime import date
from decimal import Decimal
from backend.app.domain import Transaction, parse_csv, reconcile

def tx(i='a', ref='R1', amount='100.00', day=1):
    return Transaction(i, ref, date(2026,10,day), Decimal(amount), 'INR', 'CREDIT')

class DomainTests(unittest.TestCase):
    def test_exact_and_conservation(self):
        result = reconcile((tx(), tx('missing','R2')), (tx('b'),))
        self.assertEqual(result.matches, (('a','b'),))
        self.assertEqual(2*len(result.matches)+len(result.exceptions), 3)
    def test_decimal_not_float(self):
        self.assertEqual(reconcile((tx(amount='0.30'),),(tx('b',amount='0.30'),)).matches, (('a','b'),))
        with self.assertRaises(ValueError):
            Transaction('a','R',date.today(),0.3,'INR','CREDIT')
    def test_ambiguous_never_pairs(self):
        result = reconcile((tx(),tx('a2')), (tx('b'),))
        self.assertEqual(result.matches, ())
        self.assertEqual(len(result.exceptions), 3)
        self.assertTrue(all(e[2]=='AMBIGUOUS_REFERENCE' for e in result.exceptions))
    def test_discrepancy(self):
        for other in (tx('b',amount='99'), tx('b',day=2)):
            result = reconcile((tx(),),(other,))
            self.assertFalse(result.matches)
            self.assertEqual(len(result.exceptions),2)
    def test_blank_reference(self):
        self.assertFalse(reconcile((tx(ref=''),),(tx('b',ref=''),)).matches)
    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError): reconcile((tx(),tx()),())
    def test_input_order_independent(self):
        a = (tx(),tx('a2','R2'))
        b = (tx('b'),tx('b2','R2'))
        self.assertEqual(reconcile(a,b),reconcile(tuple(reversed(a)),tuple(reversed(b))))
    def test_csv_atomic_rejection(self):
        header = 'record_id,reference,business_date,amount,currency,direction\n'
        for invalid in ('0','-1','NaN','1.001','1e2','10000000000000000'):
            with self.assertRaises(ValueError): parse_csv(header+f'a,R,2026-10-01,{invalid},INR,CREDIT\n')
        with self.assertRaises(ValueError): parse_csv(header+'a,R,2026-10-01,1,INR,CREDIT\na,R,2026-10-01,1,INR,CREDIT\n')
    def test_csv_valid(self):
        text='record_id,reference,business_date,amount,currency,direction\na, R ,2026-10-01,12.30,INR,CREDIT\n'
        self.assertEqual(parse_csv(text),(tx(amount='12.30',ref='R'),))
    def test_case_sensitive_reference(self):
        self.assertFalse(reconcile((tx(ref='abc'),),(tx('b',ref='ABC'),)).matches)

if __name__ == '__main__': unittest.main()
