"""Independent expectation labels must change acceptance when an account changes."""
import copy
import unittest
from jacaranda_jev.score_controls import capture_controls, score


class TrialScoreControls(unittest.TestCase):
    def test_aggregate_approves_while_required_account_gate_rejects(self):
        result = score(capture_controls())
        self.assertEqual(result['conforming'], 4)
        self.assertEqual(result['total'], 5)
        self.assertEqual(result['illustrative_aggregate_rule'], 'APPROVE')
        self.assertEqual(result['required_account_gate'], 'REJECT')
        self.assertEqual(result['required_refusal_gate'], 'APPROVE')
        self.assertEqual(result['external_provider_requests'], 0)

    def test_fixing_actual_wrong_account_changes_the_decision(self):
        records = capture_controls()
        wrong = next(r for r in records if r['control'] == 'wrong_eligible')
        wrong['selected_account'] = 'A-CURRENT'
        wrong['account_reads'] = ['A-CURRENT']
        result = score(records)
        self.assertEqual(result['conforming'], 5)
        self.assertEqual(result['required_account_gate'], 'APPROVE')

    def test_corrupting_refusal_is_not_hidden_by_account_success(self):
        records = capture_controls()
        retired = next(r for r in records if r['control'] == 'retired_during_decision')
        retired['account_reads'] = ['A-CURRENT']
        result = score(records)
        self.assertEqual(result['required_refusal_gate'], 'REJECT')

    def test_duplicates_cannot_pad_the_denominator(self):
        records = capture_controls()
        with self.assertRaisesRegex(ValueError, 'five distinct'):
            score(records + [copy.deepcopy(records[1])])
