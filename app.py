"""Streamlit prototype: Volunteer-Need Matching System for disaster relief."""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st
from folium import Icon, Map, Marker, PolyLine
from streamlit_folium import st_folium

import database
import matching
from data import AREA_COORDS, DUMMY_NEEDS, DUMMY_VOLUNTEERS, get_area_coord

st.set_page_config(
    page_title="Smart Resource allocation",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed",
)
database.init_db()

SKILL_OPTIONS = ["Medical", "Food", "Rescue", "Shelter", "Driving"]
NEED_CATEGORIES = ["Food", "Medical", "Shelter", "Rescue"]
URGENCY_LEVELS = ["Low", "Medium", "High", "Critical"]
AVAILABILITY_OPTIONS = [
    "Available now",
    "Within 2 hours",
    "Today",
    "Tomorrow",
    "Not available",
]
AREA_OPTIONS = sorted(AREA_COORDS.keys())
URGENCY_COLORS = {
    "Critical": "#d92d20",
    "High": "#f79009",
    "Medium": "#0ea5a8",
    "Low": "#667085",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f7f2;
            --card: rgba(255, 255, 255, 0.9);
            --card-border: rgba(15, 23, 42, 0.08);
            --text: #122019;
            --muted: #5b6b61;
            --brand: #1f9d74;
            --brand-dark: #16795a;
            --brand-soft: #dff5eb;
            --danger-soft: #fde7e4;
            --warning-soft: #fff2dd;
            --shadow: 0 18px 45px rgba(23, 37, 30, 0.08);
            --radius: 22px;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(33, 166, 117, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(245, 158, 11, 0.14), transparent 24%),
                linear-gradient(180deg, #eef6f0 0%, #f8faf8 34%, #f4f7f2 100%);
            color: var(--text);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2.25rem;
            padding-bottom: 3.25rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.02em;
        }

        [data-testid="stTabs"] {
            margin-top: 1.4rem;
            margin-bottom: 1.35rem;
        }

        [data-testid="stTabs"] button[role="tab"] {
            border-radius: 999px;
            padding: 0.72rem 1.1rem;
            margin-right: 0.45rem;
            border: 1px solid rgba(31, 157, 116, 0.16);
            background: rgba(255, 255, 255, 0.72);
        }

        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.7rem;
            padding-bottom: 0.65rem;
            border-bottom: 1px solid rgba(18, 32, 25, 0.1);
        }

        [data-testid="stTabs"] button[aria-selected="true"] {
            background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
            color: white;
            border-color: transparent;
        }

        div[data-testid="stForm"],
        div[data-testid="stVerticalBlock"] > div:has(> div.app-card),
        div[data-testid="stVerticalBlock"] > div:has(> div.hero-shell) {
            width: 100%;
        }

        .hero-shell {
            background: linear-gradient(135deg, #0f8d68 0%, #21a675 55%, #9fd4ab 120%);
            border-radius: 32px;
            padding: 1.8rem 1.8rem 1.65rem 1.8rem;
            color: white;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
            margin: 0.75rem 0 1.75rem 0;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -5% -42% auto;
            width: 280px;
            height: 280px;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 50%;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            font-size: 0.8rem;
            font-weight: 600;
        }

        .hero-title {
            font-size: clamp(2rem, 3.4vw, 2.9rem);
            line-height: 1.08;
            margin: 0.9rem 0 0.55rem 0;
            max-width: 16ch;
        }

        .hero-copy {
            max-width: 62ch;
            color: rgba(255, 255, 255, 0.88);
            margin-bottom: 0;
            font-size: 0.98rem;
            line-height: 1.65;
        }

        .app-card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: var(--radius);
            padding: 1.45rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
            margin-bottom: 1.5rem;
        }

        .section-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--brand-dark);
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .section-title {
            margin: 0;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .section-copy {
            color: var(--muted);
            margin: 0.55rem 0 0 0;
            font-size: 0.95rem;
            line-height: 1.65;
        }

        .stat-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(239,247,242,0.95) 100%);
            border: 1px solid rgba(19, 83, 61, 0.08);
            border-radius: 20px;
            padding: 1.15rem;
            min-height: 120px;
            box-shadow: 0 14px 32px rgba(22, 44, 31, 0.06);
            margin-bottom: 1.4rem;
        }

        .stat-value {
            font-size: clamp(1.85rem, 3vw, 2.5rem);
            font-weight: 800;
            line-height: 1;
            margin-top: 0.3rem;
            color: var(--text);
        }

        .stat-label {
            color: var(--muted);
            font-weight: 600;
            margin-top: 0.5rem;
        }

        .need-card {
            border: 1px solid rgba(18, 32, 25, 0.08);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.92);
            padding: 1.1rem 1.1rem 1rem 1.1rem;
            box-shadow: 0 12px 26px rgba(15, 23, 42, 0.04);
            margin-bottom: 1rem;
        }

        .need-topline {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.45rem;
        }

        .need-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            margin: 0;
        }

        .need-meta {
            color: var(--muted);
            font-size: 0.9rem;
            margin: 0.25rem 0 0 0;
        }

        .need-description {
            color: #32443b;
            margin-top: 0.65rem;
            font-size: 0.94rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.01em;
        }

        .timeline-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-top: 1.1rem;
        }

        .timeline-pill {
            padding: 0.55rem 0.8rem;
            border-radius: 14px;
            background: rgba(31, 157, 116, 0.08);
            color: #215543;
            font-size: 0.86rem;
            font-weight: 600;
        }

        .stButton,
        .stForm {
            margin-bottom: 1.2rem;
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 14px;
            border: 0;
            min-height: 2.9rem;
            font-weight: 700;
            padding: 0.65rem 1rem;
            box-shadow: none;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
            color: white;
        }

        .stButton > button[kind="secondary"],
        .stFormSubmitButton > button[kind="secondary"] {
            background: white;
            color: var(--text);
            border: 1px solid rgba(18, 32, 25, 0.1);
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            border-radius: 14px !important;
            background: rgba(255, 255, 255, 0.96) !important;
            border-color: rgba(18, 32, 25, 0.1) !important;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid rgba(18, 32, 25, 0.08);
            padding: 1rem;
            border-radius: 18px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stDataFrame"] {
            margin-top: 0.7rem;
        }

        .element-container {
            margin-bottom: 0.35rem;
        }

        .footer-note {
            color: var(--muted);
            text-align: center;
            margin-top: 2rem;
            font-size: 0.9rem;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.4rem;
                padding-bottom: 2.4rem;
            }

            .hero-shell {
                padding: 1.3rem;
                border-radius: 26px;
            }

            .app-card,
            .stat-card {
                padding: 1rem;
                margin-bottom: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_intro(label: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="app-card">
            <div class="section-label">{html.escape(label)}</div>
            <h3 class="section-title">{html.escape(title)}</h3>
            <p class="section-copy">{html.escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: int, tone: str = "brand") -> None:
    color = {
        "danger": "#d92d20",
        "warning": "#b54708",
        "success": "#2f7d32",
        "brand": "#16795a",
    }.get(tone, "#16795a")
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="section-label" style="color:{color};">{html.escape(label)}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-label">live updates from the relief queue</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def urgency_pill(urgency: str) -> str:
    bg = {
        "Critical": "#fde7e4",
        "High": "#fff2dd",
        "Medium": "#dff5eb",
        "Low": "#eef2f6",
    }.get(urgency, "#eef2f6")
    fg = URGENCY_COLORS.get(urgency, "#475467")
    return (
        f'<span class="pill" style="background:{bg}; color:{fg};">'
        f"{html.escape(urgency)}</span>"
    )


def status_pill(status: str) -> str:
    tone = {
        "Open": ("#fff3cf", "#946200"),
        "Assigned": ("#dff5eb", "#16795a"),
        "Completed": ("#e3efff", "#175cd3"),
    }.get(status, ("#eef2f6", "#475467"))
    return (
        f'<span class="pill" style="background:{tone[0]}; color:{tone[1]};">'
        f"{html.escape(status)}</span>"
    )


def render_need_card(need: dict, assignment: dict | None = None) -> None:
    volunteer_line = (
        f"Assigned to {html.escape(assignment['volunteer_name'])}"
        if assignment
        else "Awaiting volunteer assignment"
    )
    st.markdown(
        f"""
        <div class="need-card">
            <div class="need-topline">
                <p class="need-title">{html.escape(need["category"])} / {html.escape(need["area"])}</p>
                <div>{urgency_pill(need["urgency"])} {status_pill(need["status"])}</div>
            </div>
            <p class="need-meta">{need["people_affected"]} people affected / {volunteer_line}</p>
            <div class="need-description">{html.escape(need["description"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assignment_card(assignment: dict) -> None:
    st.markdown(
        f"""
        <div class="need-card">
            <div class="need-topline">
                <p class="need-title">{html.escape(assignment["need_category"])} / {html.escape(assignment["need_area"])}</p>
                <div>{urgency_pill(assignment["need_urgency"])} {status_pill(assignment["need_status"])}</div>
            </div>
            <p class="need-meta">
                {html.escape(assignment["volunteer_name"])} / {html.escape(assignment["volunteer_area"])}
                / score {assignment["score"]}
            </p>
            <div class="need-description">{html.escape(assignment["need_description"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_map(needs: list[dict], volunteers: list[dict], assignments: list[dict]) -> None:
    flood_map = Map(location=[28.6139, 77.2090], zoom_start=11, tiles="cartodbpositron")

    for need in needs:
        coord = get_area_coord(need["area"])
        if not coord:
            continue
        Marker(
            location=list(coord),
            icon=Icon(color="red", icon="exclamation-sign"),
            tooltip=f'Need #{need["id"]}: {need["category"]} ({need["urgency"]})',
            popup=(
                f"Need #{need['id']}<br>"
                f"Category: {need['category']}<br>"
                f"Urgency: {need['urgency']}<br>"
                f"Area: {need['area']}<br>"
                f"People: {need['people_affected']}<br>"
                f"Status: {need['status']}"
            ),
        ).add_to(flood_map)

    for volunteer in volunteers:
        coord = get_area_coord(volunteer["area"])
        if not coord:
            continue
        Marker(
            location=list(coord),
            icon=Icon(color="blue", icon="user"),
            tooltip=f'Volunteer: {volunteer["name"]}',
            popup=(
                f"{volunteer['name']}<br>"
                f"Skills: {volunteer['skills']}<br>"
                f"Area: {volunteer['area']}<br>"
                f"Availability: {volunteer['availability']}"
            ),
        ).add_to(flood_map)

    for assignment in assignments:
        need_coord = get_area_coord(assignment["need_area"])
        vol_coord = get_area_coord(assignment["volunteer_area"])
        if not need_coord or not vol_coord:
            continue
        PolyLine(
            locations=[list(need_coord), list(vol_coord)],
            color="#1f9d74",
            weight=3,
            opacity=0.9,
            tooltip=f'Need #{assignment["need_id"]} -> {assignment["volunteer_name"]}',
        ).add_to(flood_map)

    st_folium(flood_map, use_container_width=True, height=460)


inject_styles()

if st.button("Simulate Flood Crisis", type="primary", use_container_width=True):
    database.clear_needs_and_assignments()
    database.seed_dummy_volunteers(DUMMY_VOLUNTEERS)
    database.seed_dummy_needs(DUMMY_NEEDS)
    created = matching.run_matching()
    st.success(
        f"Loaded 15 dummy Delhi flood needs and created {created} assignment(s)."
    )

st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-kicker">Relief operations dashboard</div>
        <h1 class="hero-title">Faster reporting, clearer coordination, calmer response.</h1>
        <p class="hero-copy">
            A cleaner disaster response interface for registering volunteers, submitting
            urgent needs, and tracking field assignments without the cramped layout.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

needs = database.get_needs(order_by_urgency=True)
volunteers = database.get_volunteers()
assignments = database.get_assignments()
urgency_counts = database.get_need_counts_by_urgency()
assignment_by_need = {assignment["need_id"]: assignment for assignment in assignments}

tab_register, tab_report, tab_mission, tab_impact = st.tabs(
    ["Register", "Report Need", "Mission Control", "Impact"]
)

with tab_register:
    intro_col, stats_col = st.columns([1.25, 1], gap="large")
    with intro_col:
        section_intro(
            "Volunteer onboarding",
            "Register people who can help right now.",
            "The form is cleaner, touch-friendly, and easier to use on smaller screens while keeping the same data flow.",
        )
    with stats_col:
        stat_a, stat_b = st.columns(2, gap="small")
        with stat_a:
            render_stat_card("Registered", len(volunteers), tone="brand")
        with stat_b:
            available_now = sum(
                1 for volunteer in volunteers if volunteer["availability"] == "Available now"
            )
            render_stat_card("Ready now", available_now, tone="success")

    form_col, list_col = st.columns([1.05, 0.95], gap="large")
    with form_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Volunteer details")
        with st.form("volunteer_form", clear_on_submit=True):
            name = st.text_input("Full name", placeholder="Aman Verma")
            phone = st.text_input("Phone", placeholder="9810010001")
            skills = st.multiselect("Skills", SKILL_OPTIONS, placeholder="Choose skills")
            area = st.selectbox("Base location", AREA_OPTIONS)
            availability = st.selectbox("Availability", AVAILABILITY_OPTIONS)
            submitted = st.form_submit_button(
                "Register volunteer", type="primary", use_container_width=True
            )

            if submitted:
                if not name.strip() or not phone.strip() or not skills:
                    st.error("Please fill name, phone, and at least one skill.")
                else:
                    ok, msg = database.add_volunteer(
                        name=name.strip(),
                        phone=phone.strip(),
                        skills=",".join(skills),
                        area=area,
                        availability=availability,
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)

    with list_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Recently registered")
        if volunteers:
            volunteer_rows = [
                {
                    "Name": volunteer["name"],
                    "Skills": volunteer["skills"],
                    "Area": volunteer["area"],
                    "Availability": volunteer["availability"],
                }
                for volunteer in volunteers[:8]
            ]
            st.dataframe(
                pd.DataFrame(volunteer_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No volunteers registered yet.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_report:
    top_left, top_right = st.columns([1.1, 0.9], gap="large")
    with top_left:
        section_intro(
            "Community needs",
            "Submit a need in a layout that feels closer to a real mobile app.",
            "This section uses better spacing, clearer labels, and stronger urgency cues inspired by your reference screen.",
        )
    with top_right:
        quick_1, quick_2 = st.columns(2, gap="small")
        with quick_1:
            open_needs = sum(1 for need in needs if need["status"] == "Open")
            render_stat_card("Open needs", open_needs, tone="warning")
        with quick_2:
            critical_needs = urgency_counts["Critical"]
            render_stat_card("Critical", critical_needs, tone="danger")

    report_col, queue_col = st.columns([1.02, 0.98], gap="large")
    with report_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Need intake")
        with st.form("need_form", clear_on_submit=True):
            category = st.selectbox("Category", NEED_CATEGORIES)
            area = st.selectbox("Location", AREA_OPTIONS, key="need_area")
            people_affected = st.number_input(
                "People affected", min_value=1, max_value=10000, value=10, step=1
            )
            urgency = st.selectbox("Urgency", URGENCY_LEVELS, index=2)
            description = st.text_area(
                "Description",
                placeholder="Elderly residents need insulin, no pharmacy open since flood.",
                height=120,
            )
            submitted_need = st.form_submit_button(
                "Submit need", type="primary", use_container_width=True
            )

            if submitted_need:
                if not description.strip():
                    st.error("Please provide a short description.")
                else:
                    database.add_need(
                        category=category,
                        area=area,
                        urgency=urgency,
                        description=description.strip(),
                        people_affected=int(people_affected),
                    )
                    st.success("Need submitted.")
        st.markdown("</div>", unsafe_allow_html=True)

    with queue_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Pending needs")
        if needs:
            for need in needs[:6]:
                render_need_card(need, assignment_by_need.get(need["id"]))
        else:
            st.info("No needs submitted yet.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_mission:
    section_intro(
        "Mission control",
        "Prioritize incidents, run matching, and review active assignments.",
        "The dashboard is organized into scan-friendly cards so coordinators can act faster on desktop and mobile widths.",
    )

    action_left, action_right = st.columns(2, gap="small")
    with action_left:
        if st.button("Run matching engine", type="primary", use_container_width=True):
            created = matching.run_matching()
            st.success(f"Created {created} new assignment(s).")
    with action_right:
        if st.button("Refresh dashboard", use_container_width=True):
            st.rerun()

    stats_1, stats_2, stats_3, stats_4 = st.columns(4, gap="small")
    with stats_1:
        render_stat_card("Critical", urgency_counts["Critical"], tone="danger")
    with stats_2:
        render_stat_card("High", urgency_counts["High"], tone="warning")
    with stats_3:
        completed_count = sum(1 for need in needs if need["status"] == "Completed")
        render_stat_card("Done", completed_count, tone="success")
    with stats_4:
        assigned_count = sum(1 for need in needs if need["status"] == "Assigned")
        render_stat_card("Assigned", assigned_count, tone="brand")

    queue_col, assign_col = st.columns([1.05, 0.95], gap="large")
    with queue_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Priority queue")
        if needs:
            for need in needs[:8]:
                render_need_card(need, assignment_by_need.get(need["id"]))
        else:
            st.info("No needs available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with assign_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Active assignments")
        if assignments:
            for assignment in assignments[:6]:
                render_assignment_card(assignment)
        else:
            st.info("No assignments yet. Run the matching engine.")
        st.markdown("</div>", unsafe_allow_html=True)

    open_assigned_needs = [
        assignment for assignment in assignments if assignment["need_status"] == "Assigned"
    ]
    if open_assigned_needs:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Mark field task completed")
        complete_options = {
            (
                f'Need #{assignment["need_id"]} / {assignment["need_category"]} / '
                f'{assignment["need_area"]} / {assignment["volunteer_name"]}'
            ): assignment["need_id"]
            for assignment in open_assigned_needs
        }
        selected_label = st.selectbox(
            "Select assigned task",
            list(complete_options.keys()),
            key="complete_select",
        )
        if st.button("Mark completed", use_container_width=True):
            database.mark_need_completed(complete_options[selected_label])
            st.success("Task marked as completed.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with tab_impact:
    deployed_count = len({assignment["volunteer_id"] for assignment in assignments})
    tasks_completed = sum(1 for need in needs if need["status"] == "Completed")
    areas_covered = len({assignment["need_area"] for assignment in assignments})
    people_helped = sum(
        need["people_affected"] for need in needs if need["status"] == "Completed"
    )

    section_intro(
        "Impact and coverage",
        "See what has moved from request to response.",
        "This page keeps the map and operational metrics together so the outcome of the matching flow is easier to understand at a glance.",
    )

    impact_1, impact_2, impact_3, impact_4 = st.columns(4, gap="small")
    with impact_1:
        render_stat_card("Volunteers deployed", deployed_count, tone="brand")
    with impact_2:
        render_stat_card("Tasks completed", tasks_completed, tone="success")
    with impact_3:
        render_stat_card("Areas covered", areas_covered, tone="warning")
    with impact_4:
        render_stat_card("People helped", people_helped, tone="danger")

    map_col, table_col = st.columns([1.2, 0.8], gap="large")
    with map_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Relief map")
        render_map(needs, volunteers, assignments)
        st.markdown("</div>", unsafe_allow_html=True)

    with table_col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown("### Assignment summary")
        if assignments:
            assignment_rows = [
                {
                    "Need": f'#{assignment["need_id"]}',
                    "Category": assignment["need_category"],
                    "Volunteer": assignment["volunteer_name"],
                    "Score": assignment["score"],
                    "Status": assignment["need_status"],
                }
                for assignment in assignments
            ]
            st.dataframe(
                pd.DataFrame(assignment_rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Assignments will appear here after matching.")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<p class="footer-note">Run locally with <code>streamlit run app.py</code></p>',
    unsafe_allow_html=True,
)
