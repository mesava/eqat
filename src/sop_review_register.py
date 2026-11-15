"""Assemble the offline SOP amendment register from the documentary audit."""

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT_VERSION = 'documentary-amendment-v0.7'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def indexed(path, key='test_code'):
    rows = read(path)
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f'Duplicate {key} in {path}')
    return result


def build_register():
    catalog = indexed('data/test_definitions.json', 'code')
    originals = indexed('data/sop_versions.json')
    review_index = indexed('data/review_v0_6/review_index.json')
    initial_drafts = indexed('data/review_v0_3/sop_drafts.json')
    vendor_drafts = indexed('data/review_v0_4/sop_drafts.json')
    amendments = indexed('data/sop_review_v0_7/amendments.json')
    sources = indexed('data/review_v0_6/sources.json', 'id')

    if catalog.keys() != review_index.keys() or catalog.keys() != originals.keys():
        raise ValueError('The register, catalog and original SOPs must cover the same codes')
    if amendments.keys() - catalog.keys():
        raise ValueError('An amendment refers to a code outside the catalog')

    evidence_by_path = {
        path: indexed(path)
        for path in {path for entry in review_index.values() for path in entry['review_records']}
    }
    items = []
    for code, test in catalog.items():
        original = originals[code]
        if original['id'] != test['sop_version_id']:
            raise ValueError(f'Original SOP mismatch for {code}')
        audit = review_index[code]
        earlier_draft = vendor_drafts.get(code) or initial_drafts.get(code)
        amendment = amendments.get(code)
        if initial_drafts.get(code, {}).get('status') == 'BLOCKED_VENDOR_SOURCE':
            if amendment:
                raise ValueError(f'{code} requires a separate review of its vendor dependency')
            state = 'vendor_procedure_pending'
        elif amendment:
            state = 'amendment_draft'
        elif earlier_draft:
            state = 'earlier_draft_for_review'
        else:
            state = 'original_draft_for_review'

        references = []
        items_to_check = []
        for path in audit['review_records']:
            evidence = evidence_by_path[path][code]
            references.extend(evidence.get('references', []))
            items_to_check.extend(evidence.get('remaining_requirements', []))
            for check in evidence.get('claim_checks', []):
                references.extend(check['references'])
                if check.get('unresolved'):
                    items_to_check.append(check['unresolved'])
        if earlier_draft:
            references.extend(earlier_draft['references'])
            items_to_check.extend(earlier_draft['open_requirements'])
        if amendment:
            references.extend(amendment.get('additional_references', []))
            items_to_check.extend(amendment['local_requirements'])

        unique_references = []
        for ref in references:
            source = sources[ref['source_id']]
            if not ref['section'] or not ref['pdf_pages'] or any(
                type(page) is not int or not 1 <= page <= source['pages'] for page in ref['pdf_pages']
            ):
                raise ValueError(f'Invalid reference for {code}: {ref}')
            if ref not in unique_references:
                unique_references.append(ref)
        current_draft_id = earlier_draft['id'] if earlier_draft else None
        base_id = current_draft_id if amendment and current_draft_id else original['id']
        if earlier_draft and not amendment:
            base_id = earlier_draft['parent_sop_version_id']
        items.append({
            'test_code': code,
            'title': test['name'],
            'section': test['section'],
            'active_sop_id': original['id'],
            'base_sop_id': base_id,
            'candidate_id': f'{code}@{AMENDMENT_VERSION}' if amendment else current_draft_id,
            'state': state,
            'changes': amendment['changes'] if amendment else {},
            'remaining_sop_checks': list(dict.fromkeys(audit['next_actions'] + items_to_check)),
            'audit_records': audit['review_records'],
            'references': unique_references,
            'source_link_status': 'linked' if unique_references else 'local_basis_to_document',
            'full_sop_validation': 'pending',
            'clinical_approval': False,
        })
    return items


def main():
    parser = argparse.ArgumentParser(description='Просмотр черновых поправок к SOP и открытых вопросов')
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--test', metavar='CODE', help='Карточка одного теста')
    choice.add_argument('--all', action='store_true', help='Весь реестр')
    args = parser.parse_args()
    items = build_register()
    if args.test:
        found = next((item for item in items if item['test_code'] == args.test.upper()), None)
        if found is None:
            parser.error(f'Неизвестный код теста: {args.test}')
        result = found
    elif args.all:
        result = items
    else:
        result = {'total': len(items), 'states': dict(Counter(item['state'] for item in items))}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
