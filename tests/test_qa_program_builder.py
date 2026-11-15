import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from qa_program_builder import load, generate, validate_catalog, evaluate_applicability

class QAKnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.tests=load("test_definitions.json")
        self.machines=load("equipment_profiles.json")
        self.sops=load("sop_versions.json")
        self.by={x["code"]:x for x in self.tests}
    def test_exact_unique_codes(self):
        self.assertTrue(validate_catalog())
        self.assertEqual(161,len(self.by))
    def test_all_sops_linked(self):
        self.assertEqual(set(self.by),{x["test_code"] for x in self.sops})
    def test_machine_a_hex_sgrt(self):
        a=self.machines[0]
        for code in ["HEX-M1","SGRT-D3"]:
            self.assertEqual("eligible_draft",evaluate_applicability(self.by[code],a)[0])
        self.assertEqual("pending_feature_confirmation", evaluate_applicability(self.by["HEX-A3"],a)[0])
    def test_machine_b_hex_sgrt_not_applicable(self):
        b=self.machines[1]
        for code in ["HEX-A3","SGRT-D3"]:
            self.assertEqual("not_applicable",evaluate_applicability(self.by[code],b)[0])
    def test_no_ABC_assumption(self):
        for machine in self.machines:
            self.assertEqual("pending_feature_confirmation",evaluate_applicability(self.by["ABC-D1"],machine)[0])
    def test_imaging_unknown(self):
        for machine in self.machines:
            self.assertEqual("pending_feature_confirmation",evaluate_applicability(self.by["IMG-M3"],machine)[0])
    def test_catalog_not_clinically_approved(self):
        self.assertTrue(all(t["criterion_approval"]=="UNAPPROVED_DRAFT" for t in self.tests))
        self.assertTrue(all(not s["clinical_approval"] for s in self.sops))
    def test_program_sizes(self):
        p=generate(self.tests,self.machines)
        a,b=p["machine_programs"]
        self.assertEqual(161,len(a["items"]))
        self.assertEqual(161,len(b["items"]))
        self.assertEqual({"eligible_draft":90,"pending_feature_confirmation":69,"not_applicable":2},a["summary"])
        self.assertEqual({"eligible_draft":65,"pending_feature_confirmation":60,"not_applicable":36},b["summary"])

    def states(self, features, scope='linac', **profile):
        program = generate(machines=[{'id': 'sample', 'scope': scope, 'features': features, **profile}])
        return {row['test_code']: row['applicability_status'] for row in program['machine_programs'][0]['items']}

    def test_mixed_imaging_profile_keeps_systems_and_modes_distinct(self):
        states = self.states({'linac': 'present', 'iviewgt': 'present', 'xvi': 'absent'})
        self.assertEqual(states['IMG-D1'], 'eligible_draft')
        self.assertEqual(states['IMG-M2'], 'eligible_draft')
        self.assertEqual(states['IMG-M3'], 'not_applicable')
        states = self.states({'linac': 'present', 'xvi': 'present', 'xvi_3d': 'present'})
        self.assertEqual(states['IMG-M3'], 'eligible_draft')
        self.assertEqual(states['IMG-A6'], 'pending_feature_confirmation')
        self.assertEqual(states['IMG-M2'], 'pending_feature_confirmation')

    def test_multiple_features_and_alternative_clinical_modes(self):
        states = self.states({'linac': 'present', 'agility_mlc': 'absent', 'vmat': 'present',
                              'sbrt': 'present', 'abc': 'present', 'abc_automatic_interface': 'absent'})
        self.assertEqual(states['VMAT-M1'], 'not_applicable')
        self.assertEqual(states['MEC-SRS1'], 'eligible_draft')
        self.assertEqual(states['ABC-D1'], 'eligible_draft')
        self.assertEqual(states['ABC-D5'], 'not_applicable')

    def test_ct_scope_is_independent_of_treatment_room_catalyst(self):
        ct = self.states({'sentinel_ct': 'present', 'respiratory_4dct': 'present'}, scope='ct')
        self.assertEqual(ct['SGRT-M7'], 'eligible_draft')
        self.assertEqual(ct['SGRT-A8'], 'eligible_draft')
        self.assertEqual(ct['DOS-D1'], 'not_applicable')
        treatment = self.states({'linac': 'present', 'catalyst': 'present'})
        self.assertEqual(treatment['SGRT-D3'], 'eligible_draft')
        self.assertEqual(treatment['SGRT-A8'], 'not_applicable')

    def test_optional_profiles_need_no_acceptance_records_or_baselines(self):
        states = self.states({'linac': 'present'}, electron_energies_MeV=[])
        self.assertEqual(states['DOS-D1'], 'eligible_draft')
        self.assertEqual(states['DOS-M4'], 'not_applicable')
        self.assertEqual(self.states({'linac': 'present'})['DOS-M4'], 'pending_feature_confirmation')
    def test_baselines_missing(self):
        p=generate(self.tests,self.machines)
        for machine in p["machine_programs"]:
            self.assertTrue(all(x["baseline_status"]=="not_established" for x in machine["items"]))

if __name__ == "__main__":
    unittest.main()
