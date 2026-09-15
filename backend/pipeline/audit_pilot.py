"""Check private export joins/hashes without printing questions or credentials."""
import argparse
from collections import Counter
import json
from pathlib import Path
from app.pilot_audit import object_hash, text_hash


def audit(data):
    errors, warnings = [], []
    participants = {p['id']: p for p in data['participants']}
    runs = {r['id']: r for r in data['runs']}
    packs = {p['id']: p for p in data.get('close_packs', [])}
    assignments = {a['id']: a for a in data.get('assignments', [])}
    for pack in packs.values():
        if object_hash(pack['data']) != pack['sha256']:
            errors.append(f'Pack hash mismatch: {pack["id"]}')
    for assignment in assignments.values():
        if assignment['participant_id'] not in participants or assignment['pack_id'] not in packs:
            errors.append(f'Orphan assignment: {assignment["id"]}')
        if assignment.get('run_id'):
            run = runs.get(assignment['run_id'])
            if not run or run['participant_id'] != assignment['participant_id'] or run.get('assignment_id') != assignment['id']:
                errors.append(f'Assignment/run mismatch: {assignment["id"]}')
    for run in runs.values():
        rid = run['id']
        if run['participant_id'] not in participants:
            errors.append(f'Orphan run: {rid}')
        for field in ('source_run_id', 'retry_of_run_id'):
            parent = runs.get(run.get(field))
            if run.get(field) and (not parent or parent['participant_id'] != run['participant_id']):
                errors.append(f'Invalid {field}: {rid}')
        if run.get('evaluation_scope') == 'shared-close-case' and run.get('assignment_id') not in assignments:
            errors.append(f'Missing shared-case assignment: {rid}')
        if run.get('history') and run.get('evaluation_scope') != 'exploratory-followup':
            errors.append(f'Misclassified follow-up: {rid}')
        drafts = run.get('drafts', [])
        if run['status'] in ('review', 'completed') and len(drafts) != 2:
            errors.append(f'Incomplete displayed pair: {rid}')
        attempt_list = run.get('generation_attempts', [])
        attempts = {a['id']: a for a in attempt_list}
        if len(attempts) != len(attempt_list):
            errors.append(f'Duplicate attempt IDs: {rid}')
        artifact_ids = [d['artifact_id'] for d in drafts if d.get('artifact_id')]
        if len(set(artifact_ids)) != len(artifact_ids):
            errors.append(f'Duplicate artifact IDs: {rid}')
        for attempt in attempts.values():
            if attempt.get('request_sha256') != object_hash(attempt.get('request')):
                errors.append(f'Request hash mismatch: {rid}/{attempt["id"]}')
            if 'output_text' in attempt and attempt.get('output_sha256') != text_hash(attempt['output_text']):
                errors.append(f'Attempt output hash mismatch: {rid}/{attempt["id"]}')
        for draft in drafts:
            if draft.get('text_sha256') and draft['text_sha256'] != text_hash(draft['text']):
                errors.append(f'Artifact hash mismatch: {rid}')
            if run.get('version') in ('ask-v3', 'ask-local-v2') and draft.get('artifact_id') not in attempts:
                errors.append(f'Missing output attempt: {rid}')
            attempt = attempts.get(draft.get('artifact_id'))
            if attempt and (attempt.get('status') != 'complete'
                            or attempt.get('output_text') != draft['text']
                            or attempt.get('request_sha256') != draft.get('request_sha256')):
                errors.append(f'Artifact/attempt mismatch: {rid}')
        if run['status'] == 'failed' and not attempts:
            warnings.append(f'Failure before an auditable provider attempt: {rid}')
    for event in data['events']:
        run = runs.get(event.get('run_id'))
        if event['participant_id'] not in participants or (event.get('run_id') and (not run or run['participant_id'] != event['participant_id'])):
            errors.append(f'Orphan event: {event["id"]}')
    research_runs = [r for r in runs.values() if participants.get(r['participant_id'], {}).get('research_consent')
                     and not participants[r['participant_id']].get('source', '').startswith(('qa-', 'synthetic'))
                     and participants[r['participant_id']].get('dataset', '').startswith('cohort-')]
    return {'ok': not errors, 'errors': errors, 'warnings': warnings,
            'operational_runs': len(runs), 'research_eligible_runs': len(research_runs),
            'research_scopes': dict(Counter(r.get('evaluation_scope') or 'legacy-or-fixture' for r in research_runs)),
            'notice': 'Counts are records, not independent model trials or verified accountant identities. Publication permission is separate.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.export.read_text()))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
