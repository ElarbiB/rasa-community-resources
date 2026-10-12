"""Illustrative acceptance rules over five scripted application controls.

This is a tutorial scoring counterexample, not live model or population data.
"""
import contextlib
import io
import json
from . import demo

EXPECTED = {
    'unoffered_wire_choice': ('invalid_decision', []),
    'current': ('transactions', ['A-CURRENT']),
    'retired_during_decision': ('stale_options', []),
    'clarify': ('needs_account', []),
    'wrong_eligible': ('transactions', ['A-CURRENT']),
}


def capture_controls():
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        demo.main()
    return [json.loads(line) for line in output.getvalue().splitlines()]


def score(records):
    by_name = {r['control']: r for r in records}
    if len(records) != len(EXPECTED) or set(by_name) != set(EXPECTED):
        raise ValueError('Score exactly the five distinct declared controls')
    cases = []
    for name, (expected_status, expected_reads) in EXPECTED.items():
        record = by_name[name]
        status = record.get('status', record.get('application_status'))
        cases.append({'case': name, 'expected_status': expected_status,
                      'expected_reads': expected_reads, 'actual_status': status,
                      'actual_reads': record['account_reads'],
                      'conforms': status == expected_status and record['account_reads'] == expected_reads})
    passed = sum(r['conforms'] for r in cases)
    # Deliberately inadequate example threshold: it can average away a wrong account.
    aggregate = passed >= 4
    required_request = all(r['conforms'] for r in cases if r['case'] in {'current', 'wrong_eligible'})
    required_refusals = all(r['conforms'] for r in cases if r['case'] not in {'current', 'wrong_eligible'})
    return {'cases': cases, 'conforming': passed, 'total': len(cases),
            'illustrative_aggregate_rule': 'APPROVE' if aggregate else 'REJECT',
            'required_account_gate': 'APPROVE' if required_request else 'REJECT',
            'required_refusal_gate': 'APPROVE' if required_refusals else 'REJECT',
            'external_provider_requests': sum(r['external_provider_requests'] for r in records)}


def main():
    result = score(capture_controls())
    for case in result['cases']:
        print(f"{case['case']}: conforms={str(case['conforms']).lower()}; expected_reads={json.dumps(case['expected_reads'])}; actual_reads={json.dumps(case['actual_reads'])}")
    print(f"controlled_fixture_outcomes: {result['conforming']}/{result['total']}")
    for key in ['illustrative_aggregate_rule', 'required_account_gate', 'required_refusal_gate', 'external_provider_requests']:
        print(f"{key}: {result[key]}")


if __name__ == '__main__':
    main()
