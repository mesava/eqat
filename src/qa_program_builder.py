#!/usr/bin/env python3
"""EQAT QA Program Builder -- offline proof of concept.
No clinical connectivity. All criteria are UNAPPROVED_DRAFT.
Usage: python src/qa_program_builder.py [output_path] [--profiles profiles.json]
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
FEATURE_LABELS = {
    'linac': 'линейный ускоритель', 'agility_mlc': 'MLC Agility', 'vmat': 'режим VMAT',
    'photons': 'фотонные пучки', 'electrons': 'электронные пучки',
    'imaging_any': 'система визуализации', 'xvi': 'XVI', 'iviewgt': 'iViewGT',
    'xvi_3d': '3D XVI', 'xvi_static_2d': 'статическая 2D-визуализация XVI',
    'xvi_fluoroscopy': 'флюороскопия XVI', 'xvi_imaging_gating': 'синхронизация визуализации XVI',
    'laser_igrt_reference': 'лазеры как эталон IGRT', 'hexapod': 'HexaPOD',
    'catalyst': 'Catalyst', 'sgrt_gating': 'дыхательная синхронизация SGRT',
    'sgrt_rotated_couch': 'SGRT с поворотом стола', 'sentinel_ct': 'Sentinel на КТ',
    'respiratory_4dct': 'дыхательная синхронизация 4DCT', 'abc': 'ABC',
    'abc_automatic_interface': 'автоматический интерфейс ABC–ускоритель',
    'abc_at_ct': 'ABC на КТ', 'abc_distinct_units': 'разные устройства ABC на КТ и ускорителе',
    'srs': 'SRS', 'sbrt': 'SBRT', 'sliding_window': 'sliding window IMRT',
    'arc_rotation': 'режим нединамической дуги', 'dynamic_jaws': 'динамические диафрагмы',
    'physical_graticule': 'физическая гратикула', 'crosshair_in_use': 'использование перекрестия',
    'odi_in_use': 'использование ODI', 'motorized_wedge': 'моторизованный клин',
    'external_wedge': 'внешний физический клин', 'electron_applicators': 'электронные аппликаторы',
    'head_accessories': 'аксессуары на головке', 'dose_modifying_accessories': 'дозомодифицирующие аксессуары',
}

def load(name):
    return json.loads((DATA/name).read_text(encoding="utf-8"))

def profile_features(machine):
    if not isinstance(machine['features'], dict):
        raise ValueError(f"{machine['id']}: поле features должно быть объектом")
    features = machine['features'].copy()
    for key, state in features.items():
        if state not in ('present', 'absent', 'unknown'):
            raise ValueError(f"{machine['id']}: unexpected feature state {key}={state}")
    for feature, field in [('photons', 'photon_energies'), ('electrons', 'electron_energies_MeV')]:
        energies = machine.get(field)
        if energies is not None and not isinstance(energies, list):
            raise ValueError(f"{machine['id']}: {field} must be an array")
        if feature not in features and energies is not None:
            features[feature] = 'present' if energies else 'absent'
    imaging = [features.get(name, 'unknown') for name in ('xvi', 'iviewgt')]
    if 'present' in imaging:
        if features.get('imaging_any') == 'absent':
            raise ValueError(f"{machine['id']}: imaging_any conflicts with xvi or iviewgt")
        features['imaging_any'] = 'present'
    elif imaging == ['absent', 'absent'] and features.get('imaging_any') != 'present':
        features['imaging_any'] = 'absent'
    return features


def applicability(test, scope, features, override):
    """Each requirement group needs one present feature. All groups are required."""
    required_scope = override.get('scope', 'linac')
    if scope != required_scope:
        label = {'ct': 'КТ', 'linac': 'ускорителя'}[required_scope]
        return 'not_applicable', f'Тест относится к профилю {label}', []
    required = override.get('replace_features', test.get('required_features') or ['linac'])
    groups = [[name] for name in dict.fromkeys(required + override.get('all_of', []))]
    groups.extend(override.get('any_of', []))
    checks = []
    for names in groups:
        states = {name: features.get(name, 'unknown') for name in names}
        if 'present' in states.values():
            outcome = 'present'
        elif 'unknown' in states.values():
            outcome = 'unknown'
        else:
            outcome = 'absent'
        checks.append({'any_of': states, 'outcome': outcome})
    for outcome, status, label in [
        ('absent', 'not_applicable', 'Отсутствует'),
        ('unknown', 'pending_feature_confirmation', 'Уточнить'),
    ]:
        names = [' или '.join(FEATURE_LABELS.get(name, name) for name in check['any_of'])
                 for check in checks if check['outcome'] == outcome]
        if names:
            return status, f'{label}: {", ".join(names)}', checks
    return 'eligible_draft', 'Профиль удовлетворяет условиям применимости', checks


def evaluate_applicability(test, machine):
    rules = load('applicability_rules.json')['overrides']
    state, reason, _ = applicability(test, machine.get('scope', 'linac'), profile_features(machine),
                                    rules.get(test['code'], {}))
    return state, reason

def generate(tests=None, machines=None):
    tests=tests if tests is not None else load("test_definitions.json")
    machines=list(machines) if machines is not None else load("equipment_profiles.json")
    codes=[t["code"] for t in tests]
    if len(codes)!=len(set(codes)):
        raise ValueError("Repeated QA test codes")
    rules = load('applicability_rules.json')
    machine_ids = [machine['id'] for machine in machines]
    if len(machine_ids) != len(set(machine_ids)):
        raise ValueError('Repeated equipment profile IDs')
    program={"schema_version":"0.3.0",
             "applicability_rules_version":rules['version'],
             "status":"DRAFT_NOT_FOR_CLINICAL_USE",
             "generated":date.today().isoformat(),
             "patient_data_included":False,
             "machine_programs":[]}
    for machine in machines:
        scope = machine.get('scope', 'linac')
        if scope not in ('linac', 'ct'):
            raise ValueError(f"{machine['id']}: unknown profile scope {scope}")
        features = profile_features(machine)
        entries=[]
        for t in tests:
            state, reason, checks = applicability(t, scope, features, rules['overrides'].get(t['code'], {}))
            entries.append({"test_code":t["code"],"sop_version_id":t["sop_version_id"],
                            "name":t.get('name', t['code']),"section":t['section'],
                            "category":t.get('category'),
                            "applicability_status":state,"reason":reason,
                            "requirements":checks,
                            "applicability_details":t.get('applicability_text'),
                            "post_service_text_unverified":t.get('post_service_text'),
                            "frequency_text_unverified":t["frequency_text"],
                            "acceptance_criterion_unapproved":t["action_limit_text"],
                            "baseline_status":"not_established",
                            "execution_readiness":"not_ready"})
        counts=Counter(x["applicability_status"] for x in entries)
        program["machine_programs"].append({
            "machine_id":machine["id"],"display_name":machine.get('display_name', machine['id']),
            "scope":scope,"evaluated_features":features,
            "photon_energies":machine.get('photon_energies'),
            "electron_energies_MeV":machine.get('electron_energies_MeV'),
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
    rules = load('applicability_rules.json')['overrides']
    if rules.keys() - codes:
        raise ValueError('Applicability rule refers to an unknown test code')
    for code, rule in rules.items():
        if rule.get('scope', 'linac') not in ('linac', 'ct'):
            raise ValueError(f'{code}: unknown rule scope')
        if any(not group for group in rule.get('any_of', [])):
            raise ValueError(f'{code}: empty group of alternative requirements')
    return True


def markdown(result):
    lines = ['# Предварительная программа контроля качества', '',
             'Периодичность приведена из каталога. Программа предназначена для проектирования и проверки состава ГК.', '']
    for profile in result['machine_programs']:
        lines.extend([f"## {profile['display_name']}", ''])
        for title, key in [('Фотоны', 'photon_energies'), ('Электроны, МэВ', 'electron_energies_MeV')]:
            values = profile[key]
            if values:
                lines.append(f'- {title} — {", ".join(map(str, values))}')
        lines.append('')
        for status, heading in [
            ('eligible_draft', 'Включено по профилю'),
            ('pending_feature_confirmation', 'Требуется уточнить оснащение или режим'),
            ('not_applicable', 'Вне профиля'),
        ]:
            entries = [item for item in profile['items'] if item['applicability_status'] == status]
            lines.extend([f'### {heading} ({len(entries)})', ''])
            for item in entries:
                detail = item['frequency_text_unverified'] if status == 'eligible_draft' else item['reason']
                lines.append(f"- **{item['test_code']}** — {item['name']}. {detail}")
            lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Составить программу ГК из профилей оборудования')
    parser.add_argument('output', nargs='?', type=Path, default=ROOT / 'data' / 'program_preview.json')
    parser.add_argument('--profiles', type=Path, help='JSON с одним профилем или списком профилей')
    args = parser.parse_args()
    validate_catalog()
    machines = None
    try:
        if args.profiles is not None:
            supplied = json.loads(args.profiles.read_text(encoding='utf-8-sig'))
            machines = [supplied] if isinstance(supplied, dict) else supplied
            if not isinstance(machines, list) or not machines:
                parser.error('Файл должен содержать профиль или непустой список профилей')
        result = generate(machines=machines)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        parser.error(str(exc))
    out = args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    content = markdown(result) if out.suffix.lower() == '.md' else json.dumps(result, ensure_ascii=False, indent=2)
    out.write_text(content,encoding="utf-8")
    print("program written:",out)
    for x in result["machine_programs"]:
        print(x["machine_id"],x["summary"])

if __name__=="__main__":
    main()
