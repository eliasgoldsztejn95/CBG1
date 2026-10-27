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
from i18n import area_out, owner_out, status_out, t

st.set_page_config(page_title="לוח משימות / Task board", page_icon="🤖",
                   layout="centered", initial_sidebar_state="collapsed")

# Status roles: fixed palette, each with an icon and a word. See module docstring.
STATUS = {
    "הושלם":     {"icon": "✓", "color": "#0ca30c", "bg": "#e8f7e8", "order": 0},
    "בעבודה":    {"icon": "◐", "color": "#2a78d6", "bg": "#e7f0fc", "order": 1},
    "חסום":      {"icon": "✕", "color": "#d03b3b", "bg": "#fceaea", "order": 2},
    "טרם התחיל": {"icon": "○", "color": "#6b6a66", "bg": "#f0efec", "order": 3},
    "לא דווח":   {"icon": "?", "color": "#9a6b00", "bg": "#fdf3dc", "order": 4},
}
STATUS_ORDER = sorted(STATUS, key=lambda s: STATUS[s]["order"])
DONE, UNASSIGNED = "הושלם", i18n.UNASSIGNED_HE
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
def css(rtl: bool) -> str:
    d, align, far = ("rtl", "right", "left") if rtl else ("ltr", "left", "right")
    return f"""
<style>
  .stApp, .block-container {{ direction: {d}; }}
  .block-container {{ padding-top: .9rem; padding-bottom: 3rem; max-width: 840px; }}
  h1, h2, h3, h4, p, label, span, div, li {{ text-align: {align}; }}
  input[type="text"], textarea {{ direction: {d}; text-align: {align}; }}
  .stTabs [data-baseweb="tab-list"] {{ direction: {d}; }}

  .card {{ border: 1px solid #e4e3df; border-radius: 14px; padding: 12px 15px;
          margin-bottom: 9px; background: #fff; }}
  .card-top {{ display: flex; gap: 7px; align-items: center; flex-wrap: wrap;
              margin-bottom: 5px; }}
  .tid {{ font-family: ui-monospace, Menlo, monospace; font-size: 12px;
         color: #898781; }}
  .ttitle {{ font-weight: 650; font-size: 15.5px; color: #0b0b0b; line-height: 1.35; }}
  .meta {{ color: #52514e; font-size: 13px; margin-top: 5px; line-height: 1.75; }}
  .meta b {{ color: #0b0b0b; font-weight: 650; }}
  .sub {{ color: #898781; font-size: 11.5px; }}

  .chip {{ display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px;
          border-radius: 999px; font-size: 12.5px; font-weight: 650; white-space: nowrap; }}
  .chip .ic {{ font-size: 12px; line-height: 1; }}
  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px;
          font-size: 12px; background: #f0efec; color: #52514e; white-space: nowrap; }}
  .late {{ color: #c2410c; font-weight: 650; }}

  /* Label ABOVE a full-width bar, not beside it. Side by side, the label column
     was a fixed percentage that could not shrink, so at phone width the row
     overflowed its container and the Hebrew area and people names were clipped
     away -- the bar was all you could see. Stacked, nothing competes for
     horizontal space and the label can wrap, at any width and in either
     direction. space-between puts the value at the far end without needing to
     know which end that is. */
  .barrow {{ margin: 11px 0; }}
  .barhead {{ display: flex; justify-content: space-between; align-items: baseline;
             gap: 10px; margin-bottom: 5px; }}
  .barlab {{ font-size: 13.5px; font-weight: 600; color: #0b0b0b; min-width: 0;
            overflow-wrap: anywhere; }}
  .barval {{ flex: 0 0 auto; font-size: 12.5px; color: #52514e; white-space: nowrap;
            font-variant-numeric: tabular-nums; }}
  .bartrack {{ width: 100%; height: 9px; border-radius: 999px; background: #f0efec; }}
  .barfill {{ height: 9px; border-radius: 999px; background: #2a78d6; }}

  .kpi {{ border: 1px solid #e4e3df; border-radius: 13px; padding: 10px 4px;
         text-align: center; background: #fff; }}
  .kpi .n {{ font-size: 24px; font-weight: 700; line-height: 1.1; }}
  .kpi .l {{ font-size: 11px; color: #52514e; margin-top: 2px; text-align: center; }}
  .legend {{ display: flex; gap: 7px; flex-wrap: wrap; margin: 4px 0 10px; }}

  @media (max-width: 480px) {{
    .block-container {{ padding-left: .6rem; padding-right: .6rem; }}
    .barlab {{ font-size: 13px; }}
    .kpi .n {{ font-size: 20px; }}  .kpi .l {{ font-size: 10px; }}
  }}
</style>"""


def chip(status: str, lang: str) -> str:
    s = STATUS.get(status)
    label = esc(status_out(status, lang) or "—")
    if not s:
        return f'<span class="pill">{label}</span>'
    return (f'<span class="chip" style="background:{s["bg"]};color:{s["color"]}">'
            f'<span class="ic">{s["icon"]}</span>{label}</span>')


def bar(label: str, done: int, total: int) -> str:
    pct = (100 * done / total) if total else 0
    return (f'<div class="barrow"><div class="barhead">'
            f'<span class="barlab">{esc(label)}</span>'
            f'<span class="barval">{done}/{total} · {pct:.0f}%</span></div>'
            f'<div class="bartrack">'
            f'<div class="barfill" style="width:{pct:.0f}%"></div></div></div>')


def kpi(n, label, color="#0b0b0b") -> str:
    return (f'<div class="kpi"><div class="n" style="color:{color}">{n}</div>'
            f'<div class="l">{esc(label)}</div></div>')


def card(t_: dict, lang: str) -> str:
    dl, late = days_left(t_), is_late(t_)
    b = [f'<div class="card"><div class="card-top">'
         f'<span class="tid">{esc(t_["id"])}</span>{chip(t_.get("status"), lang)}'
         f'<span class="pill">{esc(area_out(t_.get("area"), lang))}</span></div>'
         f'<div class="ttitle">{esc(t_.get("title"))}</div><div class="meta">'
         f'{esc(t("l_owner", lang))}: '
         f'<b>{esc(owner_out(t_.get("owner") or UNASSIGNED, lang))}</b>']
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
        if t_.get(field):
            b.append(f'<br>{esc(t(key, lang))}: {esc(t_[field])}')
    if t_.get("updated_at") or t_.get("updated_by"):
        b.append(f'<br><span class="sub">{esc(t("updated", lang))} '
                 f'{esc(t_.get("updated_at"))} {esc(t("by", lang))} '
                 f'{esc(t_.get("updated_by"))}</span>')
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
                                 [owner_out(x, lang) for x in owner_opts],
                                 index=owner_opts.index(o))
        c3, c4 = st.columns(2)
        due = parse_due(t_.get("due", ""))
        new_due = c3.date_input(t("l_due", lang), value=due, format="YYYY-MM-DD")
        no_due = c4.checkbox(t("no_due", lang), value=due is None,
                             key=f"nd_{scope}_{t_['id']}")
        new_area = st.selectbox(t("l_area", lang), [area_out(a, lang) for a in AREAS],
                                index=AREAS.index(t_["area"]) if t_.get("area") in AREAS else 0)
        new_title = st.text_input(t("l_title", lang), value=t_.get("title", ""))
        new_deliv = st.text_area(t("l_deliv", lang), value=t_.get("deliverable", ""),
                                 height=68)
        c5, c6 = st.columns(2)
        new_dep = c5.text_input(t("l_dep", lang), value=t_.get("depends_on", ""))
        new_basis = c6.text_input(t("l_basis", lang), value=t_.get("basis", ""))
        new_notes = st.text_area(t("l_notes", lang), value=t_.get("notes", ""), height=68)

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
                "title": new_title.strip(), "deliverable": new_deliv.strip(),
                "depends_on": new_dep.strip(), "basis": new_basis.strip(),
                "notes": new_notes.strip(),
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
        new_title = st.text_input(t("l_title", lang))
        c1, c2 = st.columns(2)
        new_area = c1.selectbox(t("l_area", lang), [area_out(a, lang) for a in AREAS])
        owner_opts = [UNASSIGNED] + people
        new_owner = c2.selectbox(t("l_owner", lang),
                                 [owner_out(x, lang) for x in owner_opts])
        c3, c4 = st.columns(2)
        new_status = c3.selectbox(t("l_status", lang),
                                  [status_out(s, lang) for s in STATUS_ORDER],
                                  index=STATUS_ORDER.index("טרם התחיל"))
        new_due = c4.date_input(t("l_due", lang), value=None, format="YYYY-MM-DD")
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
                  "deliverable": new_deliv.strip(), "notes": new_notes.strip()})
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
def view_overview(tasks, people_rows, lang):
    total = len(tasks)
    done = sum(1 for x in tasks if x.get("status") == DONE)
    active = sum(1 for x in tasks if x.get("status") == "בעבודה")
    blocked = sum(1 for x in tasks if x.get("status") == "חסום")
    late = sum(1 for x in tasks if is_late(x))

    a, b, c = st.columns(3)
    a.markdown(kpi(total, t("kpi_total", lang)), unsafe_allow_html=True)
    b.markdown(kpi(done, t("kpi_done", lang), "#0ca30c"), unsafe_allow_html=True)
    c.markdown(kpi(active, t("kpi_active", lang), "#2a78d6"), unsafe_allow_html=True)
    d, e = st.columns(2)
    d.markdown(kpi(blocked, t("kpi_blocked", lang), "#d03b3b"), unsafe_allow_html=True)
    e.markdown(kpi(late, t("kpi_late", lang), "#c2410c"), unsafe_allow_html=True)

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
    own = [t("f_all", lang)] + [owner_out(p, lang) for p in people] + \
          [owner_out(UNASSIGNED, lang)]
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
                if f_own in [owner_out(o, lang) for o in owners_of(x)]]
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
            st.markdown(bar(owner_out(n, lang),
                            sum(1 for x in counts[n] if x.get("status") == DONE),
                            len(counts[n])), unsafe_allow_html=True)
    st.markdown("---")
    for n in sorted(names, key=lambda k: -len(counts[k])):
        mine = counts[n]
        if not mine:
            continue
        open_n = sum(1 for x in mine if x.get("status") != DONE)
        with st.expander(f"{owner_out(n, lang)} — {open_n}/{len(mine)}",
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
    st.markdown(css(i18n.RTL[lang]), unsafe_allow_html=True)

    tasks, people_rows, note = load_all(st.session_state.get("rev", 0))
    people = [p["name"] for p in people_rows if p.get("name")]

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
        view_overview(tasks, people_rows, lang)
    with tabs[1]:
        view_tasks(tasks, people, lang)
    with tabs[2]:
        view_people(tasks, people, lang)
    with tabs[3]:
        view_timeline(tasks, people, lang)


if __name__ == "__main__":
    main()
