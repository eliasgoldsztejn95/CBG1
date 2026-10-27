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

Pick one shared backend. Both are free. **Option A is much less setup** and is the
right choice when edits are occasional, which is the usual case for a task board.

---

### Option A — GitHub (recommended)

The task CSV lives in your own repo and every edit becomes a commit. No second
service, no Google Cloud project: one token and you are done. You also get history
and undo for free, which is otherwise the app's weakest point.

**1. Make a `data` branch.** The data must NOT live on the branch Streamlit deploys
from — Community Cloud redeploys on every push to that branch, so each save would
restart the app and kick everyone off.

```bash
git switch --orphan data        # an empty branch, no code on it
mkdir -p data && cp tasks_seed.csv data/tasks.csv \
                   && cp people_seed.csv data/people.csv
git add data && git commit -m "task board data" && git push -u origin data
git switch main
```

**2. Make a fine-grained token.** GitHub → Settings → Developer settings →
Personal access tokens → Fine-grained tokens. Scope it to **this repository only**,
with **Repository permissions → Contents: Read and write**. Nothing else. Copy it.

**3. Put it in Streamlit secrets:**

```toml
[github]
token = "github_pat_..."
repo = "your-user/your-repo"
branch = "data"
tasks_path = "data/tasks.csv"
people_path = "data/people.csv"
```

The header will then read **GitHub — משותף**.

> The token can write to that repo. Keep it in Streamlit secrets only, never in the
> code, and revoke it from GitHub if it ever leaks.

---

### Option B — Google Sheets

Choose this if you want the team to be able to edit the data as a spreadsheet as
well as through the app. It is more setup.

**1.** Create a Google Sheet; note the id from its URL
(`docs.google.com/spreadsheets/d/<THIS>/edit`).

**2.** In Google Cloud Console: enable the **Google Sheets API** and **Google Drive
API**, create a service account, add a JSON key, download it. Then **share the sheet
with the service account's email as Editor** — the step people miss; without it
every read fails with a permissions error.

**3.** Load the data once:

```bash
export SHEET_KEY=<the id from the URL>
export GOOGLE_APPLICATION_CREDENTIALS=service_account.json
python3 bootstrap_sheet.py
```

**4.** Streamlit secrets:

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

(Copy the fields straight out of the JSON key; keep the `\n` escapes in
`private_key`.) The header will read **Google Sheets — משותף**.

> **Never commit `service_account.json`** — it is already in `.gitignore`.

---

### Then deploy

Push to GitHub and point a new app on [share.streamlit.io](https://share.streamlit.io)
at `src/streamlit/app.py`, adding the secrets above under **Settings → Secrets**.
`storage.get_store()` picks GitHub if it is configured, else Google Sheets, else
local files — and the header always says which, so a misconfiguration shows up
rather than looking like it works.

`requirements.txt` may sit either beside the entrypoint or at the repository root —
Community Cloud searches the entrypoint's own directory first, then the root. So a
copy next to `app.py` is enough; a root copy is not needed.

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

**Concurrent saves.** On Google Sheets only the changed row is written, re-reading
the id column at write time, so edits to different tasks cannot clobber each other;
two people on the SAME task is last-write-wins. On GitHub the file's SHA makes a
stale write fail outright, and the change is re-applied to the fresh file and
retried — so the loser of a race still lands rather than being silently dropped.

**Ids are max+1.** Deleting a middle task is safe. Deleting the *highest* id frees
that number for reuse — see the note in `storage.next_id` if that starts to matter.

## Not covered

- No undo in the app. The backend is the backstop: on GitHub every edit is a commit
  (`git revert`, or the file's history on github.com); on Google Sheets it is File →
  Version history.
- The name picker is honour-system, as asked: anyone can pick any name. It records
  who *said* they made a change, not who did.
