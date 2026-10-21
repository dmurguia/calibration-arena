"""Label existing projects: python -m app.label_backfill [--dry-run]

Gives each question thread created before project labels a takeaway title, category and topic,
using the same labeler as new questions. A title the person renamed is kept; the category still fills in.
"""
import asyncio
import sys

from sqlalchemy import select

from .db import SessionLocal
from .pilot_inference import inference_backend
from .pilot_labels import label_question
from .routers.pilot import Run, apply_labels


async def main(dry_run):
    db = SessionLocal()
    try:
        runs = [r for r in db.scalars(select(Run)).all() if r.data.get('kind') == 'ask']
        threads = {}
        for run in runs:
            threads.setdefault(run.data.get('root_run_id') or run.id, []).append(run)
        todo = [root for root, members in threads.items() if not any(m.data.get('label_source') for m in members)]
        print(f'{len(todo)} of {len(threads)} question threads need labels')
        for root in todo:
            members = threads[root]
            first = next((m for m in members if m.id == root), min(members, key=lambda m: m.created_at))
            update = apply_labels(await label_question(first.data['brief'], inference_backend()), first.data.get('workflow_id'))
            if any(m.data.get('title_source') == 'user' for m in members):
                update.pop('title', None)
                update.pop('title_source', None)
            print(f"  {first.data.get('title')!r} -> {update.get('title', '(title kept)')!r} [{update['category']}; {update.get('topic')}]")
            if not dry_run:
                for m in members:
                    m.data = {**m.data, **update}
                db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    asyncio.run(main('--dry-run' in sys.argv))
