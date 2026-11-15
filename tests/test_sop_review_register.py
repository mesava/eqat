import unittest

from src.sop_review_register import build_register, indexed


class SOPReviewRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {row['test_code']: row for row in build_register()}

    def test_register_covers_catalog_without_promoting_a_draft(self):
        catalog = indexed('data/test_definitions.json', 'code')
        self.assertEqual(self.rows.keys(), catalog.keys())
        self.assertEqual(len(self.rows), 161)
        for code, row in self.rows.items():
            self.assertEqual(row['active_sop_id'], catalog[code]['sop_version_id'])
            self.assertNotEqual(row['candidate_id'], row['active_sop_id'])
            self.assertEqual(row['full_sop_validation'], 'pending')
            self.assertFalse(row['clinical_approval'])
            self.assertTrue(row['remaining_sop_checks'])
        self.assertEqual({c for c, r in self.rows.items() if not r['references']}, {'HEX-Q2'})
        self.assertEqual(self.rows['HEX-Q2']['source_link_status'], 'local_basis_to_document')

    def test_amendment_preserves_lineage_and_carries_previous_evidence(self):
        amendments = indexed('data/sop_review_v0_7/amendments.json')
        self.assertEqual({c for c, r in self.rows.items() if r['state'] == 'amendment_draft'}, amendments.keys())
        self.assertEqual(self.rows['MEC-M3']['base_sop_id'], self.rows['MEC-M3']['active_sop_id'])
        mlc = self.rows['MLC-M2']
        self.assertEqual(mlc['base_sop_id'], indexed('data/review_v0_4/sop_drafts.json')['MLC-M2']['id'])
        self.assertEqual({r['source_id'] for r in mlc['references']}, {'TG198', 'ELEKTA_VMAT_CAT'})
        vm = self.rows['VMAT-M1']
        self.assertIn('MPPG9B', {r['source_id'] for r in vm['references']})

    def test_vendor_dependencies_remain_visible_after_manuals_are_found(self):
        original_blocks = {code for code, row in indexed('data/review_v0_3/sop_drafts.json').items()
                           if row['status'] == 'BLOCKED_VENDOR_SOURCE'}
        self.assertEqual({code for code, row in self.rows.items() if row['state'] == 'vendor_procedure_pending'},
                         original_blocks)
        for code in original_blocks:
            self.assertEqual(self.rows[code]['changes'], {})
            self.assertEqual(self.rows[code]['candidate_id'], indexed('data/review_v0_4/sop_drafts.json')[code]['id'])
