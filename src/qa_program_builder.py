#!/usr/bin/env python3
"""EQAT QA Program Builder -- offline proof of concept.
No clinical connectivity. All criteria are UNAPPROVED_DRAFT.
Usage: python src/qa_program_builder.py [output_path.json]
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"

def load(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))

def evaluate_applicability(test, machine):
    """Distinguish machine capability from clinical approval and QA readiness."""
    features=machine["features"]
    section=test["section"]
    if section=="HEX":
        gate="hexapod"
    elif section=="SGRT":
        gate="catalyst"
    elif section=="ABC":
        gate="abc"
    elif section=="IMG":
        # Imaging capabilities remain unknown until documented per machine.
        # Individual tests will later use specific XVI/iView capability gates.
        gate="imaging_any"
    elif section=="VMAT":
        gate="vmat"
    elif section=="MLC":
        gate="agility_mlc"
    else:
        gate="linac"
    state=features.get(gate,"unknown")
    if state=="absent":
        return "not_applicable", f"Отсутствует функциональность: {gate}"
    if state=="unknown":
        return "pending_feature_confirmation", f"Не подтверждена функциональность: {gate}"
    if state!="present":
        raise ValueError(f"Unexpected feature state: {gate}={state}")
    return "eligible_draft", f"Функция {gate} есть; SOP/критерии не утверждены"

def generate(tests=None, machines=None):
    tests=tests if tests is not None else load("test_definitions.json")
    machines=machines if machines is not None else load("equipment_profiles.json")
    codes=[t["code"] for t in tests]
    if len(codes)!=len(set(codes)):
        raise ValueError("Repeated QA test codes")
    program={"schema_version":"0.2.0",
             "status":"DRAFT_NOT_FOR_CLINICAL_USE",
             "generated":date.today().isoformat(),
             "patient_data_included":False,
             "machine_programs":[]}
    for machine in machines:
        entries=[]
        for t in tests:
            state, reason=evaluate_applicability(t,machine)
            entries.append({"test_code":t["code"],"sop_version_id":t["sop_version_id"],
                            "applicability_status":state,"reason":reason,
                            "frequency_text_unverified":t["frequency_text"],
                            "acceptance_criterion_unapproved":t["action_limit_text"],
                            "baseline_status":"not_established",
                            "execution_readiness":"not_ready"})
        counts=Counter(x["applicability_status"] for x in entries)
        program["machine_programs"].append({
            "machine_id":machine["id"],"display_name":machine["display_name"],
            "summary":dict(counts),"items":entries
        })
    return program

def validate_catalog():
    tests=load("test_definitions.json")
    sops=load("sop_versions.json")
    codes={t["code"] for t in tests}
    sop_codes={s["test_code"] for s in sops}
    if len(tests)!=161 or len(sops)!=161 or len(codes)!=161 or codes!=sop_codes:
        raise ValueError("Catalog count or linkage mismatch")
    statuses=Counter(s["status"] for s in sops)
    if statuses["authoring_required"]!=23 or statuses["analysis_section_missing"]!=8:
        raise ValueError(f"Unexpected SOP status distribution: {statuses}")
    if any(t["criterion_approval"]!="UNAPPROVED_DRAFT" for t in tests):
        raise ValueError("Unexpected clinical approval")
    return True

def main():
    validate_catalog()
    result=generate()
    out=Path(sys.argv[1]) if len(sys.argv)>1 else (ROOT/"data"/"program_preview.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("program written:",out)
    for x in result["machine_programs"]:
        print(x["machine_id"],x["summary"])

if __name__=="__main__":
    main()
