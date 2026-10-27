"""storage.py -- where the task board lives.

Two backends behind one interface:

  gsheet  a Google Sheet, used whenever st.secrets carries a service account.
          This is the shared one: several people edit at once, and the team can
          still open the sheet directly if the app is down.
  local   tasks_seed.csv / people_seed.csv on disk, used when there are no
          secrets. For developing on your laptop ONLY -- on Streamlit Community
          Cloud the disk is wiped on restart and is not shared between viewers,
          so edits made there would quietly vanish.

Writes are PER ROW, not whole-sheet rewrites. Several people are expected to be
editing at once, and rewriting the sheet from a snapshot taken when the page
loaded would silently throw away anything saved in between. Updating only the
row that changed narrows that window to the single row, and `updated_at` /
`updated_by` record who last touched it.
"""
from __future__ import annotations

import csv
import datetime as dt
import os
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))

TASK_COLS = ["id", "area", "title", "owner", "status", "due", "deliverable",
             "depends_on", "basis", "notes", "updated_at", "updated_by"]
PEOPLE_COLS = ["name", "role", "capacity"]

TASKS_WS, PEOPLE_WS = "tasks", "people"


# --------------------------------------------------------------------- helpers --
def _blank_task() -> dict[str, str]:
    return {c: "" for c in TASK_COLS}


def normalise(row: dict[str, Any]) -> dict[str, str]:
    """Every row carries exactly TASK_COLS, as strings.

    The sheet is hand-edited, so columns go missing, arrive in a different order
    and come back as numbers. Pinning the shape here means the rest of the app
    never has to guess."""
    out = _blank_task()
    for k, v in (row or {}).items():
        k = str(k).strip()
        if k in out:
            out[k] = "" if v is None else str(v).strip()
    return out


def next_id(tasks: list[dict]) -> str:
    """T01, T02, ... continuing past the highest number already in use.

    Max+1, not count+1: ids are referenced by the depends_on column, so an id that
    collides with a live task would silently re-point dependencies, and count+1
    does exactly that as soon as any middle task is deleted.

    It is NOT collision-proof against deletion of the HIGHEST id -- delete T16 and
    the next new task is T16 again. Fixing that needs a tombstone or a stored
    counter; with deletions rare and behind a confirmation tick, the simpler rule
    is the better trade. If you start deleting often, store the high-water mark."""
    nums = []
    for t in tasks:
        tid = (t.get("id") or "").strip().upper()
        if tid.startswith("T") and tid[1:].isdigit():
            nums.append(int(tid[1:]))
    return f"T{(max(nums) + 1) if nums else 1:02d}"


def stamp(row: dict, who: str) -> dict:
    row = dict(row)
    row["updated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    row["updated_by"] = who or ""
    return row


# ----------------------------------------------------------------- local files --
class LocalStore:
    """CSV on disk. Development only -- see the module docstring."""

    kind = "local"
    shared = False

    def __init__(self, tasks_path=None, people_path=None):
        self.tasks_path = tasks_path or os.path.join(HERE, "tasks_seed.csv")
        self.people_path = people_path or os.path.join(HERE, "people_seed.csv")

    def load_tasks(self) -> list[dict]:
        if not os.path.exists(self.tasks_path):
            return []
        with open(self.tasks_path, encoding="utf-8") as f:
            return [normalise(r) for r in csv.DictReader(f)]

    def load_people(self) -> list[dict]:
        if not os.path.exists(self.people_path):
            return []
        with open(self.people_path, encoding="utf-8") as f:
            return [{c: (r.get(c) or "").strip() for c in PEOPLE_COLS}
                    for r in csv.DictReader(f)]

    def _write(self, rows):
        with open(self.tasks_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=TASK_COLS)
            w.writeheader()
            w.writerows(rows)

    def upsert_task(self, task: dict) -> None:
        task = normalise(task)
        rows = self.load_tasks()
        for i, r in enumerate(rows):
            if r["id"] == task["id"]:
                rows[i] = task
                break
        else:
            rows.append(task)
        self._write(rows)

    def delete_task(self, task_id: str) -> None:
        self._write([r for r in self.load_tasks() if r["id"] != task_id])


# -------------------------------------------------------------- google sheets --
class SheetStore:
    """A Google Sheet, one worksheet per table."""

    kind = "gsheet"
    shared = True

    def __init__(self, service_account_info: dict, sheet_key: str):
        import gspread
        self._gc = gspread.service_account_from_dict(service_account_info)
        self._sh = self._gc.open_by_key(sheet_key)

    def _ws(self, title: str, cols: list[str]):
        """Fetch a worksheet, creating it with a header row if it is missing."""
        import gspread
        try:
            return self._sh.worksheet(title)
        except gspread.WorksheetNotFound:
            ws = self._sh.add_worksheet(title=title, rows=200, cols=max(len(cols), 12))
            ws.update([cols], "A1")
            return ws

    def load_tasks(self) -> list[dict]:
        rows = self._ws(TASKS_WS, TASK_COLS).get_all_records()
        return [normalise(r) for r in rows if (r.get("id") or "").strip()]

    def load_people(self) -> list[dict]:
        rows = self._ws(PEOPLE_WS, PEOPLE_COLS).get_all_records()
        out = []
        for r in rows:
            name = str(r.get("name") or "").strip()
            if name:
                out.append({c: str(r.get(c) or "").strip() for c in PEOPLE_COLS})
        return out

    def upsert_task(self, task: dict) -> None:
        task = normalise(task)
        ws = self._ws(TASKS_WS, TASK_COLS)
        # Re-read the id column at write time, not from a cached snapshot: the row
        # this task sits on may have moved since the page was rendered.
        ids = ws.col_values(TASK_COLS.index("id") + 1)
        values = [[task[c] for c in TASK_COLS]]
        if task["id"] in ids[1:]:
            r = ids.index(task["id"], 1) + 1
            ws.update(values, f"A{r}")
        else:
            ws.append_row(values[0], value_input_option="USER_ENTERED")

    def delete_task(self, task_id: str) -> None:
        ws = self._ws(TASKS_WS, TASK_COLS)
        ids = ws.col_values(TASK_COLS.index("id") + 1)
        if task_id in ids[1:]:
            ws.delete_rows(ids.index(task_id, 1) + 1)


# ------------------------------------------------------------------- selection --
def get_store():
    """Google Sheets when secrets are configured, otherwise local CSV.

    Returns (store, note) -- `note` is a human-readable line the app shows so it is
    never ambiguous which backend is live. Silently falling back to local storage on
    a deployed app would look like it was working while losing every edit."""
    try:
        import streamlit as st
        secrets = st.secrets
    except Exception:
        return LocalStore(), "אחסון מקומי (קובץ CSV) — ללא הגדרות Streamlit"

    try:
        if "gcp_service_account" in secrets and "sheet_key" in secrets:
            info = dict(secrets["gcp_service_account"])
            return SheetStore(info, secrets["sheet_key"]), "Google Sheets — משותף"
    except Exception as e:                       # bad creds, no network, no sheet
        return LocalStore(), f"אחסון מקומי — החיבור ל-Google Sheets נכשל: {e}"
    return LocalStore(), "אחסון מקומי (קובץ CSV) — לא הוגדר Google Sheets"
