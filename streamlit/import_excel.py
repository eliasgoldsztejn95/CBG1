#!/usr/bin/env python3
"""import_excel.py -- turn cbg1.xlsx into the CSV seed the app starts from.

Reads the workbook with the stdlib only (it is a zip of XML), so importing the
project's data never depends on openpyxl/pandas being installed first.

    python3 import_excel.py [cbg1.xlsx]   # -> tasks_seed.csv, people_seed.csv
"""
import csv
import datetime as dt
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

import storage          # stdlib-only at import time; keeps the column list single-source

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HERE = os.path.dirname(os.path.abspath(__file__))

# Taken from storage rather than restated, so the seed file always has exactly the
# columns the app writes. Stating them here independently left the seed two columns
# short (updated_at, updated_by) -- harmless, since the app fills blanks in, but it
# meant the committed data file changed shape on the first save.
TASK_COLS = storage.TASK_COLS
PEOPLE_COLS = storage.PEOPLE_COLS


def _col(ref):
    """'BC12' -> 55 (1-based column index)."""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
    return n


def _sheets(z):
    """Map sheet name -> worksheet part, via the workbook's relationships."""
    rels = {}
    rx = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    for r in rx:
        rels[r.attrib["Id"]] = r.attrib["Target"].lstrip("/")
    out = {}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    for s in wb.iter(NS + "sheet"):
        t = rels[s.attrib[rid]]
        out[s.attrib["name"]] = t if t.startswith("xl/") else "xl/" + t
    return out


def _rows(z, part, shared):
    """Worksheet -> {row number: {column number: text}}."""
    ws = ET.fromstring(z.read(part))
    out = {}
    for row in ws.iter(NS + "row"):
        cells = {}
        for c in row.iter(NS + "c"):
            t, v, inl = c.attrib.get("t"), c.find(NS + "v"), c.find(NS + "is")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr" and inl is not None:
                val = "".join(x.text or "" for x in inl.iter(NS + "t"))
            elif v is not None:
                val = v.text
            else:
                continue
            val = (val or "").strip()
            if val:
                cells[_col(c.attrib["r"])] = val
        if cells:
            out[int(row.attrib["r"])] = cells
    return out


def _serial_to_date(v):
    """Excel stores dates as a day count; the sheet's due dates arrive as those."""
    if not v or not v.isdigit():
        return ""
    return (dt.date(1899, 12, 30) + dt.timedelta(days=int(v))).isoformat()


def read_workbook(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss.iter(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    sheets = _sheets(z)

    tasks = []
    trows = _rows(z, sheets["משימות"], shared)
    for r in sorted(trows):
        c = trows[r]
        # The sheet carries blank "add a subtask here" rows under every area; they
        # have the area filled in and nothing else. Real rows are the ones with an id.
        if r < 7 or not c.get(1):
            continue
        tasks.append(storage.normalise({
            "id": c.get(1, ""), "area": c.get(2, ""), "title": c.get(3, ""),
            "owner": c.get(4, ""), "status": c.get(5, ""),
            "due": _serial_to_date(c.get(6, "")), "deliverable": c.get(7, ""),
            "depends_on": c.get(8, ""), "basis": c.get(9, ""), "notes": c.get(10, ""),
        }))

    people = []
    srows = _rows(z, sheets["תמונת מצב"], shared)
    seen = False
    for r in sorted(srows):
        c = srows[r]
        if c.get(1) == "שם":                      # roster header
            seen = True
            continue
        if not seen:
            continue
        if not c.get(1) or c.get(1) == "נקודות להשלמה":
            break                                  # roster ends at the notes block
        people.append({"name": c.get(1, ""), "role": c.get(2, ""),
                       "capacity": c.get(3, "")})
    return tasks, people


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "cbg1.xlsx")
    tasks, people = read_workbook(src)
    for rows, cols, name in ((tasks, TASK_COLS, "tasks_seed.csv"),
                             (people, PEOPLE_COLS, "people_seed.csv")):
        with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {name}: {len(rows)} rows")
    areas = sorted({t["area"] for t in tasks})
    print("areas:", ", ".join(areas))
    print("statuses:", ", ".join(sorted({t["status"] for t in tasks if t["status"]})))


if __name__ == "__main__":
    main()
