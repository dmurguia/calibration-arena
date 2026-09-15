"""Import a privately validated frozen model-output pack. Never generates approvals."""
import argparse
import json
from pathlib import Path
from app.db import SessionLocal, init_db
from app.pilot_study import import_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    document = json.loads(args.path.read_text())
    init_db()
    with SessionLocal() as db:
        pack = import_pack(db, document)
        print(f'Imported immutable pack {pack.id}: {len(pack.data["cases"])} cases; sha256={pack.sha256}')


if __name__ == '__main__':
    main()
