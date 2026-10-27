"""app.py -- לוח משימות הפרויקט / Project task board.

A Streamlit board over the data that used to live in cbg1.xlsx. Bilingual
(Hebrew/English, direction flips with the language) and laid out for a phone
first: one column of cards, because a wide table is unreadable at 390 px and that
is where this will mostly be read.

Three things drive the design:

  * WHO OWNS WHAT must be answerable at a glance. There is a tab grouped by person,
    and every card names its owner first.
  * ANYONE MAY EDIT. No login. Each visitor picks their name once and it is stamped
    onto whatever they change, so edits stay open but traceable.
  * STATUS IS NEVER COLOUR ALONE. Measured on this palette, "done" (#0ca30c) and
    "blocked" (#d03b3b) sit 4.1 apart in OKLab under protanopia/deuteranopia --
    indistinguishable to most colourblind viewers. So every status carries an icon
    AND its word, and no chart encodes status by hue: the bars measure progress
    (one blue ramp) and counts, never state.

    python3 -m streamlit run app.py
"""
from __future__ import annotations

import datetime as dt
import html

import streamlit as st

import i18n
import storage
from i18n import area_out, status_out, t

st.set_page_config(page_title="לוח משימות / Task board", page_icon="🤖",
                   layout="centered", initial_sidebar_state="collapsed")

# Status roles. The hue is fixed per role; the two themes carry their own step of it
# (see THEME below). Each ships with an icon and a word -- in LIGHT mode "done"
# (#0ca30c) and "blocked" (#d03b3b) measure only 4.1 apart in OKLab under protanopia
# and deuteranopia, so colour can never be the thing that tells them apart. Dark mode
# separates them better (7.9) but is still inside the warn band, so the rule holds in
# both themes.
STATUS = {
    "הושלם":     {"icon": "✓", "cls": "s-done",  "order": 0},
    "בעבודה":    {"icon": "◐", "cls": "s-prog",  "order": 1},
    "חסום":      {"icon": "✕", "cls": "s-block", "order": 2},
    "טרם התחיל": {"icon": "○", "cls": "s-none",  "order": 3},
    "לא דווח":   {"icon": "?", "cls": "s-unk",   "order": 4},
}
STATUS_ORDER = sorted(STATUS, key=lambda s: STATUS[s]["order"])
DONE, UNASSIGNED = "הושלם", i18n.UNASSIGNED_HE
# Hebrew name -> English, read from people.csv at the top of each run. People's names
# are data, not a vocabulary, so the English lives in the sheet where the team can fix
# a transliteration without touching code.
NAMES: dict[str, str] = {}


def name_out(value: str, lang: str) -> str:
    v = (value or "").strip()
    if lang != "en":
        return v
    if v == UNASSIGNED:
        return i18n.UNASSIGNED_EN
    # A multi-owner field ("שירה ו פנחס") is mapped piece by piece.
    parts = owners_of({"owner": v})
    if len(parts) > 1:
        return " & ".join(NAMES.get(p, p) for p in parts)
    return NAMES.get(v, v)


def loc(row, field, lang):
    return storage.localised(row, field, lang)


def lang_pair(lang, field):
    """(field for the current language, field for the other one)."""
    en = storage.LOCALISED[field]
    return (en, field) if lang == "en" else (field, en)


AREAS = list(i18n.AREA_EN)


# ------------------------------------------------------------------- utilities --
def esc(s) -> str:
    return html.escape(str(s or ""))


def parse_due(s):
    try:
        return dt.date.fromisoformat((s or "").strip())
    except Exception:
        return None


def days_left(t_):
    d = parse_due(t_.get("due", ""))
    return None if d is None else (d - dt.date.today()).days


def is_late(t_) -> bool:
    n = days_left(t_)
    return n is not None and n < 0 and t_.get("status") != DONE


def owners_of(t_) -> list[str]:
    """One owner field, occasionally several people ('שירה ו פנחס')."""
    raw = (t_.get("owner") or "").strip()
    if not raw:
        return [UNASSIGNED]
    for sep in (" ו ", " ו־", ",", "/", "&", " and "):
        if sep in raw:
            return [p.strip() for p in raw.split(sep) if p.strip()]
    return [raw]


# ------------------------------------------------------------------ data access --
@st.cache_resource
def _store():
    return storage.get_store()


@st.cache_data(ttl=60, show_spinner=False)
def load_all(rev: int):
    """Tasks + people. `rev` must NOT start with an underscore: Streamlit skips
    hashing underscore-prefixed arguments, so a cache-buster named `_rev` would
    never bust anything and saves would sit invisible until the TTL expired."""
    store, note = _store()
    return store.load_tasks(), store.load_people(), note


def bump():
    st.session_state.rev = st.session_state.get("rev", 0) + 1


def save(task: dict):
    store, _ = _store()
    store.upsert_task(storage.stamp(task, st.session_state.get("me", "")))
    bump()


def remove(task_id: str):
    store, _ = _store()
    store.delete_task(task_id)
    bump()


# ----------------------------------------------------------------------- markup --
# Every colour the board paints lives here, once per theme, as CSS custom properties.
# Dark values were validated against the dark card surface (#171b22): every ink clears
# 4.5:1, the weakest being "blocked" at 6.2.
LIGHT = {
    "--page": "#ffffff", "--card": "#ffffff", "--line": "#e4e3df",
    "--ink": "#0b0b0b", "--muted": "#52514e", "--sub": "#898781",
    "--track": "#f0efec", "--fill": "#2a78d6", "--pill-bg": "#f0efec",
    "--pill-ink": "#52514e", "--late": "#c2410c",
    "--done": "#0ca30c", "--done-bg": "#e8f7e8",
    "--prog": "#2a78d6", "--prog-bg": "#e7f0fc",
    "--block": "#d03b3b", "--block-bg": "#fceaea",
    "--none": "#6b6a66", "--none-bg": "#f0efec",
    "--unk": "#9a6b00", "--unk-bg": "#fdf3dc",
}
DARK = {
    "--page": "#0e1117", "--card": "#171b22", "--line": "#2b313b",
    "--ink": "#e6e6e3", "--muted": "#a9a9a2", "--sub": "#898781",
    "--track": "#2b313b", "--fill": "#60a5fa", "--pill-bg": "#23262d",
    "--pill-ink": "#a9a9a2", "--late": "#fb923c",
    "--done": "#4ade80", "--done-bg": "#11291a",
    "--prog": "#60a5fa", "--prog-bg": "#132235",
    "--block": "#f87171", "--block-bg": "#2d1618",
    "--none": "#a9a9a2", "--none-bg": "#23262d",
    "--unk": "#fab219", "--unk-bg": "#2b2312",
}


def _vars(d):
    return "".join(f"{k}:{v};" for k, v in d.items())


def css(rtl: bool, theme: str | None) -> str:
    """Stylesheet for one direction and one theme.

    Three layers, because no single mechanism covers every case:
      1. light values on :root  -- the default;
      2. a prefers-color-scheme block -- follows the OS when Streamlit is on
         "Use system setting", which is what the app ships with;
      3. an explicit override when st.context.theme.type tells us the ACTIVE theme --
         this is what catches a viewer who flipped Streamlit's own theme toggle, since
         that choice never reaches prefers-color-scheme and the two would otherwise
         disagree (Streamlit chrome dark, these cards still white).
    Outside a browser the API reports None and layers 1-2 carry it.
    """
    d, align, far = ("rtl", "right", "left") if rtl else ("ltr", "left", "right")
    override = ""
    if theme == "dark":
        override = f":root{{{_vars(DARK)}}}"
    elif theme == "light":
        override = f":root{{{_vars(LIGHT)}}}"
    return f"""
<style>
  :root{{{_vars(LIGHT)}}}
  @media (prefers-color-scheme: dark) {{ :root{{{_vars(DARK)}}} }}
  {override}

  .stApp, .block-container {{ direction: {d}; }}
  .block-container {{ padding-top: .9rem; padding-bottom: 3rem; max-width: 840px; }}
  h1, h2, h3, h4, p, label, span, div, li {{ text-align: {align}; }}
  input[type="text"], textarea {{ direction: {d}; text-align: {align}; }}
  .stTabs [data-baseweb="tab-list"] {{ direction: {d}; }}

  .card {{ border: 1px solid var(--line); border-radius: 14px; padding: 12px 15px;
          margin-bottom: 9px; background: var(--card); }}
  .card-top {{ display: flex; gap: 7px; align-items: center; flex-wrap: wrap;
              margin-bottom: 5px; }}
  .tid {{ font-family: ui-monospace, Menlo, monospace; font-size: 12px;
         color: var(--sub); }}
  .ttitle {{ font-weight: 650; font-size: 15.5px; color: var(--ink); line-height: 1.35; }}
  .meta {{ color: var(--muted); font-size: 13px; margin-top: 5px; line-height: 1.75; }}
  .meta b {{ color: var(--ink); font-weight: 650; }}
  .sub {{ color: var(--sub); font-size: 11.5px; }}

  .chip {{ display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px;
          border-radius: 999px; font-size: 12.5px; font-weight: 650; white-space: nowrap; }}
  .chip .ic {{ font-size: 12px; line-height: 1; }}
  .s-done {{ background: var(--done-bg); color: var(--done); }}
  .s-prog {{ background: var(--prog-bg); color: var(--prog); }}
  .s-block {{ background: var(--block-bg); color: var(--block); }}
  .s-none {{ background: var(--none-bg); color: var(--none); }}
  .s-unk {{ background: var(--unk-bg); color: var(--unk); }}
  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
          font-size: 12px; background: var(--pill-bg); color: var(--pill-ink);
          white-space: nowrap; }}
  .late {{ color: var(--late); font-weight: 650; }}

  .barrow {{ margin: 11px 0; }}
  .barhead {{ display: flex; justify-content: space-between; align-items: baseline;
             gap: 10px; margin-bottom: 5px; }}
  .barlab {{ font-size: 13.5px; font-weight: 600; color: var(--ink); min-width: 0;
            overflow-wrap: anywhere; }}
  .barval {{ flex: 0 0 auto; font-size: 12.5px; color: var(--muted); white-space: nowrap;
            font-variant-numeric: tabular-nums; }}
  .bartrack {{ width: 100%; height: 9px; border-radius: 999px; background: var(--track); }}
  .barfill {{ height: 9px; border-radius: 999px; background: var(--fill); }}

  .kpi {{ border: 1px solid var(--line); border-radius: 13px; padding: 10px 4px;
         text-align: center; background: var(--card); }}
  .kpi .n {{ font-size: 24px; font-weight: 700; line-height: 1.1; color: var(--ink); }}
  .kpi .n.k-done {{ color: var(--done); }}
  .kpi .n.k-prog {{ color: var(--prog); }}
  .kpi .n.k-block {{ color: var(--block); }}
  .kpi .n.k-late {{ color: var(--late); }}
  .kpi .l {{ font-size: 11px; color: var(--muted); margin-top: 2px; text-align: center; }}
  .legend {{ display: flex; gap: 7px; flex-wrap: wrap; margin: 4px 0 10px; }}

  @media (max-width: 480px) {{
    .block-container {{ padding-left: .6rem; padding-right: .6rem; }}
    .barlab {{ font-size: 13px; }}
    .kpi .n {{ font-size: 20px; }}  .kpi .l {{ font-size: 10px; }}
  }}
</style>"""


def chip(status: str, lang: str) -> str:
    st_ = STATUS.get(status)
    label = esc(status_out(status, lang) or "—")
    if not st_:
        return f'<span class="pill">{label}</span>'
    return (f'<span class="chip {st_["cls"]}">'
            f'<span class="ic">{st_["icon"]}</span>{label}</span>')


def bar(label: str, done: int, total: int) -> str:
    pct = (100 * done / total) if total else 0
    return (f'<div class="barrow"><div class="barhead">'
            f'<span class="barlab">{esc(label)}</span>'
            f'<span class="barval">{done}/{total} · {pct:.0f}%</span></div>'
            f'<div class="bartrack">'
            f'<div class="barfill" style="width:{pct:.0f}%"></div></div></div>')


def kpi(n, label, cls="") -> str:
    return (f'<div class="kpi"><div class="n {cls}">{n}</div>'
            f'<div class="l">{esc(label)}</div></div>')


def card(t_: dict, lang: str) -> str:
    dl, late = days_left(t_), is_late(t_)
    b = [f'<div class="card"><div class="card-top">'
         f'<span class="tid">{esc(t_["id"])}</span>{chip(t_.get("status"), lang)}'
         f'<span class="pill">{esc(area_out(t_.get("area"), lang))}</span></div>'
         f'<div class="ttitle">{esc(loc(t_, "title", lang))}</div><div class="meta">'
         f'{esc(t("l_owner", lang))}: '
         f'<b>{esc(name_out(t_.get("owner") or UNASSIGNED, lang))}</b>']
    if t_.get("due"):
        if late:
            b.append(f'<br>{esc(t("l_due", lang))}: <span class="late">'
                     f'{esc(t_["due"])} — {esc(t("late_by", lang, n=abs(dl)))}</span>')
        else:
            tail = (f' ({t("in_days", lang, n=dl)})'
                    if dl is not None and t_.get("status") != DONE else "")
            b.append(f'<br>{esc(t("l_due", lang))}: <b>{esc(t_["due"])}</b>{esc(tail)}')
    for key, field in (("l_deliv", "deliverable"), ("l_dep", "depends_on"),
                       ("l_notes", "notes")):
        val = loc(t_, field, lang) if field in storage.LOCALISED else t_.get(field, "")
        if val:
            b.append(f'<br>{esc(t(key, lang))}: {esc(val)}')
    if t_.get("basis"):
        b.append(f'<br>{esc(t("l_basis", lang))}: '
                 f'{esc(i18n.basis_out(t_["basis"], lang))}')
    if t_.get("updated_at") or t_.get("updated_by"):
        b.append(f'<br><span class="sub">{esc(t("updated", lang))} '
                 f'{esc(t_.get("updated_at"))} {esc(t("by", lang))} '
                 f'{esc(name_out(t_.get("updated_by", ""), lang))}</span>')
    b.append("</div></div>")
    return "".join(b)


# ------------------------------------------------------------------ edit forms --
def edit_form(t_: dict, people: list[str], lang: str, scope: str) -> None:
    """Inline editor for one task. Everything is editable, because the sheet it
    replaces was.

    `scope` namespaces the widget keys. The same task is rendered by more than one
    view -- and a task owned by two people appears under both of them -- so keying
    widgets on the task id alone collides and Streamlit refuses to draw the page."""
    with st.form(f"edit_{scope}_{t_['id']}", clear_on_submit=False):
        c1, c2 = st.columns(2)
        status_opts = [status_out(s, lang) for s in STATUS_ORDER]
        cur = t_.get("status") if t_.get("status") in STATUS_ORDER else STATUS_ORDER[-1]
        new_status = c1.selectbox(t("l_status", lang), status_opts,
                                  index=STATUS_ORDER.index(cur))
        owner_opts = [UNASSIGNED] + people
        o = t_.get("owner") or UNASSIGNED
        if o not in owner_opts:
            owner_opts.append(o)          # keeps 'שירה ו פנחס' and ad-hoc names
        new_owner = c2.selectbox(t("l_owner", lang),
                                 [name_out(x, lang) for x in owner_opts],
                                 index=owner_opts.index(o))
        c3, c4 = st.columns(2)
        due = parse_due(t_.get("due", ""))
        new_due = c3.date_input(t("l_due", lang), value=due, format="YYYY-MM-DD")
        no_due = c4.checkbox(t("no_due", lang), value=due is None,
                             key=f"nd_{scope}_{t_['id']}")
        new_area = st.selectbox(t("l_area", lang), [area_out(a, lang) for a in AREAS],
                                index=AREAS.index(t_["area"]) if t_.get("area") in AREAS else 0)
        other = "he" if lang == "en" else "en"
        # Current language first, the other one right under it. Both are editable so
        # whoever makes a change can keep the two boards saying the same thing; the
        # second is optional and falls back to the first when left empty.
        tp, ts = lang_pair(lang, "title")
        new_title_p = st.text_input(t("l_title", lang), value=t_.get(tp, ""))
        new_title_s = st.text_input(f'{t("l_title", other)} · {i18n.LANGS[other]}',
                                    value=t_.get(ts, ""))
        dp, ds = lang_pair(lang, "deliverable")
        new_deliv_p = st.text_area(t("l_deliv", lang), value=t_.get(dp, ""), height=68)
        new_deliv_s = st.text_area(f'{t("l_deliv", other)} · {i18n.LANGS[other]}',
                                   value=t_.get(ds, ""), height=68)
        c5, c6 = st.columns(2)
        new_dep = c5.text_input(t("l_dep", lang), value=t_.get("depends_on", ""))
        new_basis = c6.text_input(t("l_basis", lang),
                                  value=i18n.basis_out(t_.get("basis", ""), lang))
        np_, ns_ = lang_pair(lang, "notes")
        new_notes_p = st.text_area(t("l_notes", lang), value=t_.get(np_, ""), height=68)
        new_notes_s = st.text_area(f'{t("l_notes", other)} · {i18n.LANGS[other]}',
                                   value=t_.get(ns_, ""), height=68)

        if st.form_submit_button(t("save", lang), type="primary",
                                 use_container_width=True):
            if not st.session_state.get("me"):
                st.warning(t("need_name", lang))
                return
            upd = dict(t_)
            upd.update({
                "status": i18n.status_in(new_status, lang),
                "owner": (UNASSIGNED
                          if new_owner in (UNASSIGNED, i18n.UNASSIGNED_EN)
                          else new_owner),
                "area": i18n.area_in(new_area, lang),
                "due": "" if no_due or not new_due else new_due.isoformat(),
                "depends_on": new_dep.strip(),
                "basis": i18n.basis_in(new_basis.strip(), lang),
                tp: new_title_p.strip(), ts: new_title_s.strip(),
                dp: new_deliv_p.strip(), ds: new_deliv_s.strip(),
                np_: new_notes_p.strip(), ns_: new_notes_s.strip(),
            })
            save(upd)
            st.success(t("saved", lang))
            st.rerun()

    # Delete sits outside the form and behind a tick, so a mis-tap cannot drop a
    # task that other people's work depends on.
    with st.expander(t("delete", lang)):
        if st.checkbox(t("confirm_del", lang), key=f"del_{scope}_{t_['id']}"):
            if st.button(t("delete", lang), key=f"delbtn_{scope}_{t_['id']}",
                         use_container_width=True):
                remove(t_["id"])
                st.rerun()


def add_form(tasks: list[dict], people: list[str], lang: str) -> None:
    with st.form("add_task", clear_on_submit=True):
        other = "he" if lang == "en" else "en"
        tp, ts = lang_pair(lang, "title")
        new_title = st.text_input(t("l_title", lang))
        new_title_o = st.text_input(f'{t("l_title", other)} · {i18n.LANGS[other]}')
        c1, c2 = st.columns(2)
        new_area = c1.selectbox(t("l_area", lang), [area_out(a, lang) for a in AREAS])
        owner_opts = [UNASSIGNED] + people
        new_owner = c2.selectbox(t("l_owner", lang),
                                 [name_out(x, lang) for x in owner_opts])
        c3, c4 = st.columns(2)
        new_status = c3.selectbox(t("l_status", lang),
                                  [status_out(s, lang) for s in STATUS_ORDER],
                                  index=STATUS_ORDER.index("טרם התחיל"))
        new_due = c4.date_input(t("l_due", lang), value=None, format="YYYY-MM-DD")
        dp, ds = lang_pair(lang, "deliverable")
        np_, ns_ = lang_pair(lang, "notes")
        new_deliv = st.text_area(t("l_deliv", lang), height=68)
        new_notes = st.text_area(t("l_notes", lang), height=68)
        if st.form_submit_button(t("add_do", lang), type="primary",
                                 use_container_width=True):
            if not st.session_state.get("me"):
                st.warning(t("need_name", lang))
                return
            if not new_title.strip():
                st.warning(t("l_title", lang))
                return
            save({**{c: "" for c in storage.TASK_COLS},
                  "id": storage.next_id(tasks),
                  "title": new_title.strip(),
                  "area": i18n.area_in(new_area, lang),
                  "owner": (UNASSIGNED if new_owner in (UNASSIGNED, i18n.UNASSIGNED_EN)
                            else new_owner),
                  "status": i18n.status_in(new_status, lang),
                  "due": new_due.isoformat() if new_due else "",
                  tp: new_title.strip(), ts: new_title_o.strip(),
                  dp: new_deliv.strip(), np_: new_notes.strip()})
            st.success(t("saved", lang))
            st.rerun()


def task_list(rows: list[dict], people: list[str], lang: str, scope: str) -> None:
    if not rows:
        st.info(t("no_tasks", lang))
        return
    for t_ in rows:
        st.markdown(card(t_, lang), unsafe_allow_html=True)
        with st.expander(f'{t("edit", lang)} · {t_["id"]}'):
            edit_form(t_, people, lang, scope)


# ----------------------------------------------------------------------- views --
def view_overview(tasks, people_rows, people, lang):
    total = len(tasks)
    done = sum(1 for x in tasks if x.get("status") == DONE)
    active = sum(1 for x in tasks if x.get("status") == "בעבודה")
    blocked = sum(1 for x in tasks if x.get("status") == "חסום")
    late = sum(1 for x in tasks if is_late(x))

    a, b, c = st.columns(3)
    a.markdown(kpi(total, t("kpi_total", lang)), unsafe_allow_html=True)
    b.markdown(kpi(done, t("kpi_done", lang), "k-done"), unsafe_allow_html=True)
    c.markdown(kpi(active, t("kpi_active", lang), "k-prog"), unsafe_allow_html=True)
    d, e = st.columns(2)
    d.markdown(kpi(blocked, t("kpi_blocked", lang), "k-block"), unsafe_allow_html=True)
    e.markdown(kpi(late, t("kpi_late", lang), "k-late"), unsafe_allow_html=True)

    st.markdown(f"#### {t('progress', lang)}")
    st.markdown(bar(t("kpi_done", lang), done, total), unsafe_allow_html=True)

    st.markdown(f"#### {t('by_area', lang)}")
    for area in AREAS:
        rows = [x for x in tasks if x.get("area") == area]
        if rows:
            st.markdown(bar(area_out(area, lang),
                            sum(1 for x in rows if x.get("status") == DONE), len(rows)),
                        unsafe_allow_html=True)

    # A legend is always present: status is identified by icon + word, so the colour
    # is never doing the work on its own.
    st.markdown(f"#### {t('legend', lang)}")
    st.markdown('<div class="legend">'
                + "".join(chip(s, lang) for s in STATUS_ORDER)
                + "</div>", unsafe_allow_html=True)
    st.caption(f'⚠ {t("overdue_note", lang)}')

    # Every subtask, grouped by its status. The KPI row above deliberately shows only
    # done/active/blocked plus the overdue flag, which between them account for 7 of
    # 15 here -- "not started" and "not reported" had no representation on this page
    # at all, so most of the board was invisible from the overview.
    st.markdown(f"#### {t('by_status', lang)}")
    st.caption(t("tap_open", lang))
    shown = 0
    for si, stat in enumerate(STATUS_ORDER):
        rows = [x for x in tasks if x.get("status") == stat]
        shown += len(rows)
        if not rows:
            continue
        info = STATUS[stat]
        with st.expander(f'{info["icon"]}  {status_out(stat, lang)} — {len(rows)}'):
            task_list(rows, people, lang, f"ov{si}")
    # Anything with a status outside the five known ones would vanish silently; it is
    # better to show it under its own heading than to lose it.
    other = [x for x in tasks if x.get("status") not in STATUS_ORDER]
    if other:
        with st.expander(f'? — {len(other)}'):
            task_list(other, people, lang, "ovx")
        shown += len(other)
    st.caption(f"{shown} / {len(tasks)}")

    if people_rows:
        with st.expander(f'{t("tab_people", lang)} ({len(people_rows)})'):
            for p in people_rows:
                cap = f' · {t("l_capacity", lang)} {p["capacity"]}' if p.get("capacity") else ""
                st.markdown(
                    f'<div class="meta"><b>{esc(p["name"])}</b> — '
                    f'{esc(i18n.role_out(p.get("role", ""), lang))}{esc(cap)}</div>',
                    unsafe_allow_html=True)


def view_tasks(tasks, people, lang):
    c1, c2 = st.columns(2)
    areas = [t("f_all", lang)] + [area_out(a, lang) for a in AREAS]
    f_area = c1.selectbox(t("f_area", lang), areas)
    stat = [t("f_all", lang)] + [status_out(s, lang) for s in STATUS_ORDER]
    f_stat = c2.selectbox(t("f_status", lang), stat)
    c3, c4 = st.columns(2)
    own = [t("f_all", lang)] + [name_out(p, lang) for p in people] + \
          [name_out(UNASSIGNED, lang)]
    f_own = c3.selectbox(t("f_owner", lang), own)
    f_text = c4.text_input(t("f_search", lang), "")
    only_late = st.checkbox(t("f_late_only", lang), value=False)

    rows = tasks
    if f_area != t("f_all", lang):
        rows = [x for x in rows if area_out(x.get("area"), lang) == f_area]
    if f_stat != t("f_all", lang):
        rows = [x for x in rows if status_out(x.get("status"), lang) == f_stat]
    if f_own != t("f_all", lang):
        rows = [x for x in rows
                if f_own in [name_out(o, lang) for o in owners_of(x)]]
    if only_late:
        rows = [x for x in rows if is_late(x)]
    if f_text.strip():
        q = f_text.strip().lower()
        rows = [x for x in rows
                if any(q in str(x.get(k, "")).lower()
                       for k in ("id", "title", "deliverable", "notes", "owner"))]

    st.caption(f"{len(rows)} / {len(tasks)}")
    task_list(rows, people, lang, "tasks")
    st.markdown("---")
    with st.expander(f'➕ {t("add", lang)}'):
        add_form(tasks, people, lang)


def view_people(tasks, people, lang):
    """Who is in charge of what -- the question this board exists to answer."""
    names = people + [UNASSIGNED]
    counts = {}
    for n in names:
        mine = [x for x in tasks if n in owners_of(x)]
        counts[n] = mine
    st.markdown(f"#### {t('by_person', lang)}")
    for n in sorted(names, key=lambda k: -len(counts[k])):
        if counts[n]:
            st.markdown(bar(name_out(n, lang),
                            sum(1 for x in counts[n] if x.get("status") == DONE),
                            len(counts[n])), unsafe_allow_html=True)
    st.markdown("---")
    for n in sorted(names, key=lambda k: -len(counts[k])):
        mine = counts[n]
        if not mine:
            continue
        open_n = sum(1 for x in mine if x.get("status") != DONE)
        with st.expander(f"{name_out(n, lang)} — {open_n}/{len(mine)}",
                         expanded=(n == st.session_state.get("me"))):
            task_list(mine, people, lang, f"ppl_{abs(hash(n)) % 10**6}")


def view_timeline(tasks, people, lang):
    today = dt.date.today()
    buckets = [
        ("⚠ " + t("kpi_late", lang), lambda x: is_late(x)),
        ("📅 7", lambda x: (days_left(x) is not None and 0 <= days_left(x) <= 7
                            and x.get("status") != DONE)),
        ("📆 30", lambda x: (days_left(x) is not None and 7 < days_left(x) <= 30
                             and x.get("status") != DONE)),
        ("🕓 30+", lambda x: (days_left(x) is not None and days_left(x) > 30
                              and x.get("status") != DONE)),
        ("— " + t("no_due", lang), lambda x: (days_left(x) is None
                                              and x.get("status") != DONE)),
        ("✓ " + t("kpi_done", lang), lambda x: x.get("status") == DONE),
    ]
    for i, (label, pred) in enumerate(buckets):
        rows = sorted([x for x in tasks if pred(x)],
                      key=lambda x: (x.get("due") or "9999"))
        if not rows:
            continue
        st.markdown(f"#### {label} ({len(rows)})")
        task_list(rows, people, lang, f"tl{i}")


# ------------------------------------------------------------------------ main --
def main():
    st.session_state.setdefault("lang", "he")
    st.session_state.setdefault("me", "")
    lang = st.session_state["lang"]
    # The ACTIVE theme, not the configured one: a viewer who flipped Streamlit's own
    # toggle must get matching cards. Reports None outside a browser.
    try:
        theme = st.context.theme.type
    except Exception:
        theme = None
    st.markdown(css(i18n.RTL[lang], theme), unsafe_allow_html=True)

    tasks, people_rows, note = load_all(st.session_state.get("rev", 0))
    people = [p["name"] for p in people_rows if p.get("name")]
    NAMES.clear()
    NAMES.update({p["name"]: (p.get("name_en") or p["name"])
                  for p in people_rows if p.get("name")})

    st.title(t("title", lang))
    c1, c2, c3 = st.columns([1, 1.4, 0.7])
    c1.selectbox(t("lang", lang), list(i18n.LANGS),
                 format_func=lambda k: i18n.LANGS[k], key="lang")
    c2.selectbox(t("who", lang), [""] + people, key="me", help=t("who_help", lang))
    if c3.button(t("refresh", lang), use_container_width=True):
        bump()
        st.rerun()
    # The page was already styled for `lang` read at the top of main(); if the
    # selectbox just changed it, redraw so the direction flips with the words.
    if st.session_state.get("lang", "he") != lang:
        st.rerun()

    store, _ = _store()
    (st.caption if store.shared else st.warning)(f'{t("storage", lang)}: {note}')
    if not st.session_state.get("me"):
        st.info(t("need_name", lang))

    tabs = st.tabs([t("tab_overview", lang), t("tab_tasks", lang),
                    t("tab_people", lang), t("tab_time", lang)])
    with tabs[0]:
        view_overview(tasks, people_rows, people, lang)
    with tabs[1]:
        view_tasks(tasks, people, lang)
    with tabs[2]:
        view_people(tasks, people, lang)
    with tabs[3]:
        view_timeline(tasks, people, lang)


if __name__ == "__main__":
    main()
