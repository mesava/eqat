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
        for code in ["HEX-A3","SGRT-D3"]:
            self.assertEqual("eligible_draft",evaluate_applicability(self.by[code],a)[0])
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
        self.assertEqual(35,b["summary"]["not_applicable"])
        self.assertEqual(39,a["summary"]["pending_feature_confirmation"])
        self.assertEqual(39,b["summary"]["pending_feature_confirmation"])
    def test_baselines_missing(self):
        p=generate(self.tests,self.machines)
        for machine in p["machine_programs"]:
            self.assertTrue(all(x["baseline_status"]=="not_established" for x in machine["items"]))

if __name__ == "__main__":
    unittest.main()
