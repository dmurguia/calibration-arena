"""Private local export. Writes only to an explicit output path; refuses overwrite."""
import argparse
import json
from pathlib import Path
from app.db import SessionLocal
from app.routers.pilot import export_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        data = export_data(db)
    destination = Path(args.output)
    with destination.open('x') as output:
        destination.chmod(0o600)
        json.dump(data, output, indent=2)
    print(f'Private pilot export written to {destination.resolve()}')
