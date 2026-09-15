"""Private invitation/exposure metadata; not a participant-facing signup form."""
import argparse
from datetime import datetime
from app.db import SessionLocal
from app.routers.pilot import Participant, emit
from app.pilot_study import Assignment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('participant_id')
    parser.add_argument('--alias', help='Private non-identifying invitation alias; never an API key')
    parser.add_argument('--preset-requested-at', help='ISO timestamp with timezone for David\'s request')
    parser.add_argument('--assignment-id')
    parser.add_argument('--exposure', choices=['not-reported', 'none-reported', 'validator', 'previously-seen'])
    args = parser.parse_args()
    if bool(args.assignment_id) != bool(args.exposure):
        parser.error('--assignment-id and --exposure must be supplied together')
    if args.preset_requested_at and not datetime.fromisoformat(args.preset_requested_at).tzinfo:
        parser.error('--preset-requested-at requires a timezone')
    with SessionLocal() as db:
        person = db.get(Participant, args.participant_id)
        if not person:
            parser.error('Participant not found in this database')
        changes = {}
        if args.alias:
            changes['cohort_alias'] = args.alias[:100]
        if args.preset_requested_at:
            changes['preset_requested_at'] = args.preset_requested_at
        if args.assignment_id:
            assignment = db.get(Assignment, args.assignment_id)
            if not assignment or assignment.participant_id != person.id:
                parser.error('Assignment is not owned by this participant')
            changes['assignment_exposure'] = {'assignment_id': assignment.id, 'before': assignment.exposure, 'after': args.exposure}
            assignment.exposure = args.exposure
        person.profile = {**person.profile, **{k: v for k, v in changes.items() if k != 'assignment_exposure'}}
        emit(db, person, 'operator_context_updated', data=changes)
        db.commit()
        print('Private participant context saved with an append-only change event.')


if __name__ == '__main__':
    main()
