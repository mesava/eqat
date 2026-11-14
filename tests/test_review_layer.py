"""Review drafts must remain traceable and cannot silently become active SOPs."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


class ReviewLayerTests(unittest.TestCase):
    def setUp(self):
        self.tests = read('test_definitions.json')
        self.originals = read('sop_versions.json')
        self.drafts = read('review_v0_3/sop_drafts.json')
        self.evidence = read('review_v0_3/evidence.json')
        self.sources = {s['id']: s for s in read('review_v0_3/sources.json')}

    def test_review_covers_catalog_without_promoting_claims(self):
        self.assertEqual(len(self.evidence), len(self.tests))
        self.assertEqual({r['test_code'] for r in self.evidence}, {t['code'] for t in self.tests})
        for row in self.evidence:
            self.assertFalse(row['clinical_approval'])
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')
            if row['review_status'] == 'NOT_REVIEWED':
                self.assertEqual(row['claim_checks'], [])
            for check in row['claim_checks']:
                self.assertIn(check['grade'], {'VERIFIED', 'CONTRADICTION', 'UNRESOLVED', 'LOCALLY_DERIVED'})
                if check['grade'] in {'VERIFIED', 'CONTRADICTION'}:
                    self.assertTrue(check['references'])

    def test_drafts_cover_original_gaps_and_preserve_active_versions(self):
        gaps = {s['test_code'] for s in self.originals if s['status'] in {'authoring_required', 'analysis_section_missing'}}
        self.assertEqual(gaps, {s['test_code'] for s in self.drafts})
        self.assertEqual(len(self.drafts), len(gaps))
        original_by_code = {s['test_code']: s for s in self.originals}
        active_ids = {t['sop_version_id'] for t in self.tests}
        for draft in self.drafts:
            self.assertEqual(draft['parent_sop_version_id'], original_by_code[draft['test_code']]['id'])
            self.assertNotIn(draft['id'], active_ids)
            self.assertFalse(draft['clinical_approval'])
            self.assertEqual(draft['execution_readiness'], 'not_ready')
            self.assertTrue(draft['open_requirements'])
            if draft['status'] == 'BLOCKED_VENDOR_SOURCE':
                self.assertEqual(draft['steps'], [])

    def test_references_are_resolvable_and_pages_exist(self):
        references = [r for d in self.drafts for r in d['references']]
        references += [r for e in self.evidence for c in e['claim_checks'] for r in c['references']]
        for ref in references:
            source = self.sources[ref['source_id']]
            self.assertTrue(ref['section'])
            self.assertTrue(ref['pdf_pages'])
            for page in ref['pdf_pages']:
                self.assertIsInstance(page, int)
                self.assertGreaterEqual(page, 1)
                self.assertLessEqual(page, source['pages'])
            self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')

    def test_review_does_not_leak_private_drive_links(self):
        for path in (ROOT / 'data/review_v0_3').glob('*.json'):
            content = path.read_text(encoding='utf-8')
            self.assertNotIn('drive.google.com', content)
            self.assertNotIn('docs.google.com', content)

    def test_vendor_followup_preserves_blocked_execution_and_parentage(self):
        followups = read('review_v0_4/sop_drafts.json')
        findings = read('review_v0_4/vendor_findings.json')
        parents = {s['test_code']: s for s in self.drafts}
        blocked = {s['test_code'] for s in self.drafts if s['status'] == 'BLOCKED_VENDOR_SOURCE'}
        self.assertTrue(blocked <= {s['test_code'] for s in followups})
        self.assertEqual(len(followups), len({s['test_code'] for s in followups}))
        self.assertEqual({s['test_code'] for s in followups}, {s['test_code'] for s in findings})
        for draft in followups:
            self.assertEqual(draft['parent_sop_version_id'], parents[draft['test_code']]['id'])
            self.assertFalse(draft['clinical_approval'])
            self.assertEqual(draft['execution_readiness'], 'not_ready')
            self.assertEqual(draft['installed_version_match'], 'unknown')
            self.assertTrue(draft['open_requirements'])
            self.assertNotIn(draft['id'], {t['sop_version_id'] for t in self.tests})
            if draft['test_code'] in blocked:
                self.assertEqual(draft['steps'], [])

    def test_vendor_references_and_public_content(self):
        sources = {s['id']: s for s in read('review_v0_4/sources.json')}
        for row in read('review_v0_4/vendor_findings.json'):
            self.assertFalse(row['clinical_approval'])
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')
            for ref in row['references']:
                source = sources[ref['source_id']]
                self.assertTrue(ref['section'])
                self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')
                for page in ref['pdf_pages']:
                    self.assertGreaterEqual(page, 1)
                    self.assertLessEqual(page, source['pages'])
        for path in (ROOT / 'data/review_v0_4').glob('*.json'):
            content = path.read_text(encoding='utf-8')
            for private_marker in ['drive.google.com', 'docs.google.com', 'G:\\\\']:
                self.assertNotIn(private_marker, content)


class DosimetryMechanicsReviewTests(unittest.TestCase):
    def test_coverage_matches_unique_reviewed_codes(self):
        catalog = {r['code'] for r in read('test_definitions.json')}
        coverage = read('review_v0_5/coverage.json')
        reviewed = {r['test_code'] for r in read('review_v0_3/evidence.json')
                    if r['review_status'] == 'PARTIAL'}
        for file in ['review_v0_4/vendor_findings.json', 'review_v0_5/dosimetry_mechanics.json']:
            reviewed.update(r['test_code'] for r in read(file))
        self.assertEqual(len(coverage), len(catalog))
        self.assertEqual({r['test_code'] for r in coverage}, catalog)
        self.assertEqual({r['test_code'] for r in coverage if r['review_status'] == 'PARTIAL'}, reviewed)
        for row in coverage:
            self.assertFalse(row['clinical_approval'])
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')

    def test_findings_preserve_originals_and_resolve_references(self):
        catalog = {r['code']: r for r in read('test_definitions.json')}
        sources = {r['id']: r for r in read('review_v0_5/sources.json')}
        findings = read('review_v0_5/dosimetry_mechanics.json')
        self.assertEqual(len(findings), len({r['test_code'] for r in findings}))
        for row in findings:
            original = catalog[row['test_code']]
            self.assertEqual(row['original_frequency'], original['frequency_text'])
            self.assertEqual(row['original_action_criterion'], original['action_limit_text'])
            self.assertFalse(row['clinical_approval'])
            self.assertEqual(row['overall_grade'], 'UNRESOLVED')
            self.assertEqual(row['execution_readiness'], 'not_ready')
            self.assertTrue(row['remaining_requirements'])
            self.assertTrue(row['references'])
            for ref in row['references']:
                source = sources[ref['source_id']]
                self.assertTrue(ref['section'])
                self.assertTrue(ref['pdf_pages'])
                self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')
                for page in ref['pdf_pages']:
                    self.assertGreaterEqual(page, 1)
                    self.assertLessEqual(page, source['pages'])


if __name__ == '__main__':
    unittest.main()
