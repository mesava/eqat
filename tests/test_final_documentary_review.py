import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


class FinalDocumentaryReviewTests(unittest.TestCase):
    def test_every_catalog_code_has_actual_review_record(self):
        catalog = {t['code']: t for t in read('data/test_definitions.json')}
        index = read('data/review_v0_6/review_index.json')
        coverage = read('data/review_v0_6/coverage.json')
        self.assertEqual(len(index), len(catalog))
        self.assertEqual({r['test_code'] for r in index}, set(catalog))
        self.assertEqual(len(coverage), len(catalog))
        self.assertEqual({r['test_code'] for r in coverage}, set(catalog))
        for row in index:
            self.assertTrue(row['review_records'])
            for path in row['review_records']:
                matches = [r for r in read(path) if r['test_code'] == row['test_code']]
                self.assertEqual(len(matches), 1)
                self.assertNotEqual(matches[0].get('review_status'), 'NOT_REVIEWED')
                self.assertTrue(matches[0].get('references') or matches[0].get('claim_checks'))
            self.assertEqual(row['section'], catalog[row['test_code']]['section'])
            self.assertEqual(row['full_sop_validation'], 'PENDING')
            self.assertFalse(row['clinical_approval'])
            self.assertTrue(row['next_actions'])
        for row in coverage:
            self.assertEqual(row['review_status'], 'PARTIAL')
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')
            self.assertFalse(row['clinical_approval'])

    def test_new_batch_fills_only_previously_unreviewed_codes(self):
        pending = {r['test_code'] for r in read('data/review_v0_5/coverage.json')
                   if r['review_status'] == 'NOT_REVIEWED'}
        findings = read('data/review_v0_6/remaining_findings.json')
        self.assertEqual(len(findings), len(pending))
        self.assertEqual({r['test_code'] for r in findings}, pending)
        catalog = {r['code']: r for r in read('data/test_definitions.json')}
        sources = {r['id']: r for r in read('data/review_v0_6/sources.json')}
        for row in findings:
            self.assertEqual(row['original_frequency'], catalog[row['test_code']]['frequency_text'])
            self.assertEqual(row['original_action_criterion'], catalog[row['test_code']]['action_limit_text'])
            self.assertEqual(row['execution_readiness'], 'not_ready')
            self.assertFalse(row['clinical_approval'])
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')
            self.assertIn(row['claim_grade'], {'VERIFIED', 'LOCALLY_DERIVED', 'CONTRADICTION', 'UNRESOLVED'})
            self.assertTrue(row['finding'])
            self.assertTrue(row['proposed_change'])
            self.assertTrue(row['remaining_requirements'])
            self.assertTrue(row['references'])
            for ref in row['references']:
                source = sources[ref['source_id']]
                self.assertTrue(ref['section'])
                self.assertTrue(ref['pdf_pages'])
                self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')
                for page in ref['pdf_pages']:
                    self.assertIsInstance(page, int)
                    self.assertGreaterEqual(page, 1)
                    self.assertLessEqual(page, source['pages'])

    def test_published_summary_counts_are_derived_from_records(self):
        summary = read('data/review_v0_6/audit_summary.json')
        catalog = read('data/test_definitions.json')
        findings = read('data/review_v0_6/remaining_findings.json')
        coverage = read('data/review_v0_6/coverage.json')
        self.assertEqual(summary['catalog_count'], len(catalog))
        self.assertEqual(summary['new_findings'], len(findings))
        self.assertEqual(summary['unique_reviewed_codes'], len({r['test_code'] for r in coverage}))
        self.assertEqual(summary['not_reviewed_count'], sum(r['review_status'] == 'NOT_REVIEWED' for r in coverage))
        self.assertEqual(summary['new_claim_grades'], dict(Counter(r['claim_grade'] for r in findings)))
        self.assertEqual(summary['sections'], dict(Counter(r['section'] for r in catalog)))
        self.assertEqual(summary['clinical_execution_gate'], 'CLOSED')
        self.assertEqual(summary['fully_validated_sops'], 0)
        self.assertEqual(summary['clinical_approvals'], 0)
        for path in (ROOT / 'data/review_v0_6').glob('*.json'):
            content = path.read_text(encoding='utf-8')
            for marker in ['drive.google.com', 'docs.google.com', 'G:\\\\', 'C:\\\\Users']:
                self.assertNotIn(marker, content)


if __name__ == '__main__':
    unittest.main()
