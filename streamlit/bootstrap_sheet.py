#!/usr/bin/env python3
"""bootstrap_sheet.py -- push the CSV seed into the shared Google Sheet, once.

Run this after creating the sheet and sharing it with the service account, to load
the data that came out of cbg1.xlsx. After that the app owns the sheet and this
script is not needed again.

    export SHEET_KEY=1AbC...          # the id in the sheet's URL
    export GOOGLE_APPLICATION_CREDENTIALS=service_account.json
    python3 bootstrap_sheet.py [--force]

Refuses to run against a sheet that already holds tasks unless --force is given:
the whole point of the app is that people are editing that sheet, and overwriting
their work because somebody re-ran the importer would be unrecoverable.
"""
import csv
import json
import os
import sys

import storage

HERE = os.path.dirname(os.path.abspath(__file__))


def read_csv(name, cols):
    path = os.path.join(HERE, name)
    with open(path, encoding="utf-8") as f:
        return [[(r.get(c) or "").strip() for c in cols] for r in csv.DictReader(f)]


def main():
    force = "--force" in sys.argv
    key = os.environ.get("SHEET_KEY")
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key or not cred:
        raise SystemExit("set SHEET_KEY and GOOGLE_APPLICATION_CREDENTIALS")
    with open(cred, encoding="utf-8") as f:
        info = json.load(f)

    store = storage.SheetStore(info, key)
    existing = store.load_tasks()
    if existing and not force:
        raise SystemExit(f"sheet already has {len(existing)} tasks — "
                         "re-running would overwrite live edits. Pass --force "
                         "only if you are certain that is what you want.")

    for ws_name, csv_name, cols in (
            (storage.TASKS_WS, "tasks_seed.csv", storage.TASK_COLS),
            (storage.PEOPLE_WS, "people_seed.csv", storage.PEOPLE_COLS)):
        rows = read_csv(csv_name, cols)
        ws = store._ws(ws_name, cols)
        ws.clear()
        ws.update([cols] + rows, "A1")
        print(f"{ws_name}: wrote {len(rows)} rows")
    print("done — the app will pick these up on its next refresh")


if __name__ == "__main__":
    main()
