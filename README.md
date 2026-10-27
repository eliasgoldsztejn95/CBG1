# לוח משימות הפרויקט · Project task board

A Streamlit board replacing `cbg1.xlsx`. Hebrew/English, phone-first, anyone may
edit, every edit stamped with who made it.

```
app.py              the board
i18n.py             Hebrew/English strings and vocabularies
storage.py          Google Sheets backend + local CSV fallback
import_excel.py     cbg1.xlsx  -> tasks_seed.csv, people_seed.csv
bootstrap_sheet.py  seed CSVs  -> the shared Google Sheet (run once)
```

## Run it locally

```bash
pip install -r requirements.txt
python3 -m streamlit run app.py
```

With no secrets configured it reads and writes `tasks_seed.csv` on disk and says
so at the top of the page. That is for development only — see the warning below.

## Deploy it so the team can use it

### 1. Create the sheet

Make a Google Sheet, note the id from its URL
(`docs.google.com/spreadsheets/d/<THIS>/edit`).

### 2. Create a service account

In Google Cloud Console: enable the **Google Sheets API** and **Google Drive API**,
create a service account, add a JSON key, download it. Then **share the sheet with
the service account's email address, as Editor** — this is the step people miss;
without it every read returns a permissions error.

### 3. Load the data, once

```bash
export SHEET_KEY=<the id from the URL>
export GOOGLE_APPLICATION_CREDENTIALS=service_account.json
python3 import_excel.py        # only if cbg1.xlsx changed
python3 bootstrap_sheet.py
```

### 4. Deploy

Push to GitHub, then on [share.streamlit.io](https://share.streamlit.io) point a new
app at `src/streamlit/app.py`. In **Settings → Secrets** paste:

```toml
sheet_key = "<the id from the URL>"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

(Copy the fields straight out of the JSON key. Keep the `\n` escapes in
`private_key`.) The header of the app will then read **Google Sheets — משותף**.

> **Never commit `service_account.json`.** Add it to `.gitignore`. Anyone holding
> that file can read and write the sheet.

## Things worth knowing before you change it

**The local CSV backend is not shared.** On Streamlit Community Cloud the disk is
wiped on restart and is not shared between viewers, so edits would be silently
lost. The app shows a yellow warning whenever it is on that backend, rather than
looking like it works. Only Google Sheets is safe for real use.

**Hebrew is the stored form.** Statuses and areas live in the sheet in Hebrew;
English is a display layer (`i18n.py`). Switching language never rewrites the
sheet, so two people on different languages cannot fight over stored values. Task
titles, deliverables, notes and people's names are free text and are *not*
translated — they render as somebody typed them, in both languages.

**Status is never colour alone.** On this palette "done" (`#0ca30c`) and "blocked"
(`#d03b3b`) measure ΔE 4.1 apart in OKLab under protanopia/deuteranopia —
indistinguishable to most colourblind viewers. Every status therefore carries an
icon and its word, and no chart encodes status by hue: the bars measure progress
and counts. Keep it that way if you add views.

**Writes are per row.** `storage.upsert_task` rewrites only the row that changed,
re-reading the id column at write time. Rewriting the whole sheet from the
snapshot taken at page load would throw away anything saved in between.

**Ids are max+1.** Deleting a middle task is safe. Deleting the *highest* id frees
that number for reuse — see the note in `storage.next_id` if that starts to matter.

## Not covered

- No undo. Google Sheets' own version history is the backstop (File → Version
  history), which is one reason to prefer it.
- The name picker is honour-system, as asked: anyone can pick any name. It records
  who *said* they made a change, not who did.
