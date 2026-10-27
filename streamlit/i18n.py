"""i18n.py -- Hebrew / English for the board.

The DATA stays Hebrew. Statuses and areas are stored in the sheet in Hebrew and
that is the canonical form; English is a display layer only. Two reasons:

  * switching language must never rewrite the sheet, or two people on different
    languages would fight over the stored values;
  * the sheet is still hand-edited by people who type Hebrew.

So `status_out`/`area_out` translate on the way to the screen and
`status_in`/`area_in` translate back on the way to storage.

FREE TEXT IS NOT TRANSLATED. Task titles, deliverables, notes and people's names
are whatever somebody typed. Machine-translating them here would invent wording
nobody wrote and quietly misreport the project, so they render as entered in both
languages.
"""
from __future__ import annotations

LANGS = {"he": "עברית", "en": "English"}
RTL = {"he": True, "en": False}

# Controlled vocabularies: canonical Hebrew -> English.
STATUS_EN = {
    "הושלם": "Done",
    "בעבודה": "In progress",
    "חסום": "Blocked",
    "טרם התחיל": "Not started",
    "לא דווח": "Not reported",
}
AREA_EN = {
    "זיהוי ותפיסה": "Detection & grasping",
    "לוקאליזציה במרחב": "Localization",
    "ניווט לוקאלי": "Local navigation",
    "אינטגרציה והדגמה": "Integration & demo",
}
ROLE_EN = {
    "תלמיד תיכון": "High-school student",
    "סטודנט לתואר שני": "MSc student",
    "דוקטורנט": "PhD student",
    "פוסטדוק": "Postdoc",
}
BASIS_EN = {
    "נמסר": "Given",
    "נמסר כעתידי": "Given as future work",
    "נמסר כיעד": "Given as a goal",
    "פירוק מוצע": "Proposed breakdown",
}
UNASSIGNED_EN = "Unassigned"
UNASSIGNED_HE = "טרם נקבע"

STRINGS = {
    "title":        {"he": "לוח משימות הפרויקט",      "en": "Project task board"},
    "tab_overview": {"he": "סקירה",                    "en": "Overview"},
    "tab_tasks":    {"he": "משימות",                   "en": "Tasks"},
    "tab_people":   {"he": "לפי אחראי",                "en": "By owner"},
    "tab_time":     {"he": "לוח זמנים",                "en": "Timeline"},

    "kpi_total":    {"he": "סה״כ",                     "en": "Total"},
    "kpi_done":     {"he": "הושלמו",                   "en": "Done"},
    "kpi_active":   {"he": "בעבודה",                   "en": "Active"},
    "kpi_blocked":  {"he": "חסומות",                   "en": "Blocked"},
    "kpi_late":     {"he": "באיחור",                   "en": "Overdue"},

    "by_area":      {"he": "התקדמות לפי תחום",         "en": "Progress by area"},
    "by_person":    {"he": "עומס לפי אחראי",           "en": "Load by owner"},
    "by_status":    {"he": "כל תתי־המשימות לפי סטטוס",  "en": "All subtasks by status"},
    "tap_open":     {"he": "לחצו על סטטוס כדי לראות את המשימות שבו.",
                     "en": "Tap a status to see the tasks in it."},
    "progress":     {"he": "אחוז השלמה",               "en": "Completion"},
    "no_tasks":     {"he": "אין משימות התואמות לסינון.", "en": "No tasks match the filter."},

    "f_area":       {"he": "תחום",                     "en": "Area"},
    "f_owner":      {"he": "אחראי",                    "en": "Owner"},
    "f_status":     {"he": "סטטוס",                    "en": "Status"},
    "f_search":     {"he": "חיפוש חופשי",              "en": "Search"},
    "f_all":        {"he": "הכול",                     "en": "All"},
    "f_late_only":  {"he": "רק באיחור",                "en": "Overdue only"},

    "l_owner":      {"he": "אחראי",                    "en": "Owner"},
    "l_status":     {"he": "סטטוס",                    "en": "Status"},
    "l_due":        {"he": "מועד יעד",                 "en": "Due"},
    "l_deliv":      {"he": "תוצר צפוי",                "en": "Deliverable"},
    "l_dep":        {"he": "תלוי ב",                   "en": "Depends on"},
    "l_basis":      {"he": "בסיס המשימה",              "en": "Basis"},
    "l_notes":      {"he": "הערות",                    "en": "Notes"},
    "l_area":       {"he": "תחום",                     "en": "Area"},
    "l_title":      {"he": "תת־משימה",                 "en": "Subtask"},
    "l_role":       {"he": "תפקיד",                    "en": "Role"},
    "l_capacity":   {"he": "היקף",                     "en": "Capacity"},

    "edit":         {"he": "עריכה",                    "en": "Edit"},
    "save":         {"he": "שמירה",                    "en": "Save"},
    "saved":        {"he": "נשמר",                     "en": "Saved"},
    "add":          {"he": "הוספת משימה",              "en": "Add task"},
    "add_do":       {"he": "הוספה",                    "en": "Add"},
    "delete":       {"he": "מחיקה",                    "en": "Delete"},
    "confirm_del":  {"he": "לאשר מחיקה",               "en": "Confirm delete"},
    "refresh":      {"he": "רענון",                    "en": "Refresh"},

    "who":          {"he": "מי אתם?",                  "en": "Who are you?"},
    "who_help":     {"he": "נשמר כדי לסמן מי עדכן. ללא סיסמה.",
                     "en": "Recorded as who made each change. No password."},
    "updated":      {"he": "עודכן",                    "en": "updated"},
    "by":           {"he": "ע״י",                      "en": "by"},
    "late_by":      {"he": "באיחור {n} ימים",          "en": "{n} days overdue"},
    "in_days":      {"he": "בעוד {n} ימים",            "en": "in {n} days"},
    "no_due":       {"he": "ללא מועד יעד",             "en": "No due date"},
    "unassigned":   {"he": UNASSIGNED_HE,              "en": UNASSIGNED_EN},

    "storage":      {"he": "אחסון",                    "en": "Storage"},
    "lang":         {"he": "שפה",                      "en": "Language"},
    "need_name":    {"he": "בחרו את שמכם כדי לערוך.",  "en": "Pick your name to edit."},
    "legend":       {"he": "מקרא סטטוסים",             "en": "Status legend"},
    "overdue_note": {"he": "משימה שמועד היעד שלה חלף ואינה מסומנת כהושלמה.",
                     "en": "A task past its due date and not marked done."},
}


def t(key: str, lang: str, **kw) -> str:
    s = STRINGS.get(key, {}).get(lang, STRINGS.get(key, {}).get("he", key))
    return s.format(**kw) if kw else s


def status_out(value: str, lang: str) -> str:
    return STATUS_EN.get(value, value) if lang == "en" else value


def status_in(value: str, lang: str) -> str:
    if lang != "en":
        return value
    back = {v: k for k, v in STATUS_EN.items()}
    return back.get(value, value)


def area_out(value: str, lang: str) -> str:
    return AREA_EN.get(value, value) if lang == "en" else value


def area_in(value: str, lang: str) -> str:
    if lang != "en":
        return value
    back = {v: k for k, v in AREA_EN.items()}
    return back.get(value, value)


def basis_out(value: str, lang: str) -> str:
    return BASIS_EN.get(value, value) if lang == "en" else value


def basis_in(value: str, lang: str) -> str:
    if lang != "en":
        return value
    return {v: k for k, v in BASIS_EN.items()}.get(value, value)


def role_out(value: str, lang: str) -> str:
    return ROLE_EN.get(value, value) if lang == "en" else value


def owner_out(value: str, lang: str) -> str:
    """Only the 'unassigned' placeholder is a vocabulary term; real names are free
    text and stay exactly as somebody typed them."""
    if lang == "en" and (value or "").strip() == UNASSIGNED_HE:
        return UNASSIGNED_EN
    return value
