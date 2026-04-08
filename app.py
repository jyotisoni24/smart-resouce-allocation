"""Streamlit prototype: Volunteer-Need Matching System for disaster relief."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from folium import Icon, Map, Marker, PolyLine
from streamlit_folium import st_folium

import database
import matching
from data import AREA_COORDS, DUMMY_NEEDS, DUMMY_VOLUNTEERS, get_area_coord``
# ---------- App bootstrap ----------
st.set_page_config(page_title="Volunteer-Need Matching", page_icon="🚨", layout="wide")
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

st.title("Delhi Flood Relief: Volunteer-Need Matching System")
st.caption("Simple local prototype using Streamlit + SQLite + Folium")

# ---------- Simulation (important requirement) ----------
if st.button("Simulate Flood Crisis", type="primary"):
    # Reset needs + assignments for a clean scenario run.
    database.clear_needs_and_assignments()

    # Seed volunteers if missing (INSERT OR IGNORE keeps existing unique phones safe).
    database.seed_dummy_volunteers(DUMMY_VOLUNTEERS)

    # Seed exactly 15 dummy needs and auto-run matching.
    database.seed_dummy_needs(DUMMY_NEEDS)
    created = matching.run_matching()
    st.success(
        f"Loaded 15 dummy Delhi flood needs. Matching completed with {created} assignment(s)."
    )

tab1, tab2, tab3 = st.tabs(
    ["Volunteer Registration", "Need Submission", "Coordinator Dashboard"]
)

# ---------- Volunteer Registration ----------
with tab1:
    st.subheader("Register Volunteer")
    with st.form("volunteer_form", clear_on_submit=True):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        skills = st.multiselect("Skills", SKILL_OPTIONS)
        area = st.selectbox("Area", AREA_OPTIONS)
        availability = st.selectbox("Availability", AVAILABILITY_OPTIONS)
        submitted = st.form_submit_button("Register Volunteer")

        if submitted:
            if not name.strip() or not phone.strip() or not skills:
                st.error("Please fill name, phone and at least one skill.")
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

    volunteers = database.get_volunteers()
    st.markdown("### Registered Volunteers")
    if volunteers:
        st.dataframe(pd.DataFrame(volunteers), use_container_width=True, hide_index=True)
    else:
        st.info("No volunteers registered yet.")

# ---------- Need Submission ----------
with tab2:
    st.subheader("Submit Need")
    with st.form("need_form", clear_on_submit=True):
        category = st.selectbox("Category", NEED_CATEGORIES)
        area = st.selectbox("Area", AREA_OPTIONS, key="need_area")
        urgency = st.selectbox("Urgency", URGENCY_LEVELS, index=2)
        description = st.text_area("Description")
        people_affected = st.number_input(
            "People Affected", min_value=1, max_value=10000, value=10, step=1
        )
        submitted_need = st.form_submit_button("Submit Need")

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

    needs_preview = database.get_needs(order_by_urgency=True)
    st.markdown("### Current Needs")
    if needs_preview:
        st.dataframe(
            pd.DataFrame(needs_preview), use_container_width=True, hide_index=True
        )
    else:
        st.info("No needs submitted yet.")

# ---------- Coordinator Dashboard ----------
with tab3:
    st.subheader("Coordinator Dashboard")

    col_left, col_right = st.columns([1, 1])
    with col_left:
        if st.button("Run Matching Engine"):
            created = matching.run_matching()
            st.success(f"Created {created} new assignment(s).")
    with col_right:
        if st.button("Refresh Dashboard"):
            st.rerun()

    needs = database.get_needs(order_by_urgency=True)
    volunteers = database.get_volunteers()
    assignments = database.get_assignments()
    urgency_counts = database.get_need_counts_by_urgency()

    # ---- Total needs by urgency ----
    st.markdown("### Total Needs by Urgency")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Critical", urgency_counts["Critical"])
    c2.metric("High", urgency_counts["High"])
    c3.metric("Medium", urgency_counts["Medium"])
    c4.metric("Low", urgency_counts["Low"])

    # ---- Needs sorted by urgency ----
    st.markdown("### Needs (Sorted by Urgency)")
    if needs:
        assignment_by_need = {a["need_id"]: a for a in assignments}
        need_rows = []
        for n in needs:
            assigned = assignment_by_need.get(n["id"])
            need_rows.append(
                {
                    "Need ID": n["id"],
                    "Category": n["category"],
                    "Urgency": n["urgency"],
                    "Area": n["area"],
                    "People Affected": n["people_affected"],
                    "Status": n["status"],
                    "Assigned Volunteer": assigned["volunteer_name"] if assigned else "-",
                    "Match Score": assigned["score"] if assigned else "-",
                    "Description": n["description"],
                }
            )
        st.dataframe(pd.DataFrame(need_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No needs available.")

    # ---- Mark task complete ----
    open_assigned_needs = [
        a for a in assignments if a["need_status"] == "Assigned"
    ]
    if open_assigned_needs:
        st.markdown("### Task Completion")
        complete_options = {
            f'Need #{a["need_id"]} ({a["need_category"]}, {a["need_area"]}) - {a["volunteer_name"]}': a[
                "need_id"
            ]
            for a in open_assigned_needs
        }
        selected_label = st.selectbox(
            "Mark one assigned task as completed",
            list(complete_options.keys()),
            key="complete_select",
        )
        if st.button("Mark Completed"):
            database.mark_need_completed(complete_options[selected_label])
            st.success("Task marked as completed.")
            st.rerun()

    # ---- Assigned volunteers ----
    st.markdown("### Assigned Volunteers")
    if assignments:
        assignment_rows = [
            {
                "Need ID": a["need_id"],
                "Need Category": a["need_category"],
                "Need Urgency": a["need_urgency"],
                "Need Area": a["need_area"],
                "Volunteer": a["volunteer_name"],
                "Volunteer Phone": a["volunteer_phone"],
                "Volunteer Skills": a["volunteer_skills"],
                "Volunteer Area": a["volunteer_area"],
                "Match Score": a["score"],
                "Need Status": a["need_status"],
            }
            for a in assignments
        ]
        st.dataframe(
            pd.DataFrame(assignment_rows), use_container_width=True, hide_index=True
        )
    else:
        st.info("No assignments yet. Run the matching engine.")

    # ---- Impact metrics ----
    st.markdown("### Impact Metrics")
    deployed_count = len({a["volunteer_id"] for a in assignments})
    tasks_completed = sum(1 for n in needs if n["status"] == "Completed")
    areas_covered = len({a["need_area"] for a in assignments})
    people_helped = sum(n["people_affected"] for n in needs if n["status"] == "Completed")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Volunteers Deployed", deployed_count)
    m2.metric("Tasks Completed", tasks_completed)
    m3.metric("Areas Covered", areas_covered)
    m4.metric("People Helped", people_helped)

    # ---- Map visualization ----
    st.markdown("### Map Visualization")
    flood_map = Map(location=[28.6139, 77.2090], zoom_start=11, tiles="cartodbpositron")

    # Red markers: needs
    for n in needs:
        coord = get_area_coord(n["area"])
        if not coord:
            continue
        Marker(
            location=list(coord),
            icon=Icon(color="red", icon="exclamation-sign"),
            tooltip=f'Need #{n["id"]}: {n["category"]} ({n["urgency"]})',
            popup=(
                f"Need #{n['id']}<br>"
                f"Category: {n['category']}<br>"
                f"Urgency: {n['urgency']}<br>"
                f"Area: {n['area']}<br>"
                f"People: {n['people_affected']}<br>"
                f"Status: {n['status']}"
            ),
        ).add_to(flood_map)

    # Blue markers: volunteers
    for v in volunteers:
        coord = get_area_coord(v["area"])
        if not coord:
            continue
        Marker(
            location=list(coord),
            icon=Icon(color="blue", icon="user"),
            tooltip=f'Volunteer: {v["name"]}',
            popup=(
                f"{v['name']}<br>"
                f"Skills: {v['skills']}<br>"
                f"Area: {v['area']}<br>"
                f"Availability: {v['availability']}"
            ),
        ).add_to(flood_map)

    # Green lines: assignments
    for a in assignments:
        need_coord = get_area_coord(a["need_area"])
        vol_coord = get_area_coord(a["volunteer_area"])
        if not need_coord or not vol_coord:
            continue
        PolyLine(
            locations=[list(need_coord), list(vol_coord)],
            color="green",
            weight=3,
            opacity=0.8,
            tooltip=f'Need #{a["need_id"]} -> {a["volunteer_name"]}',
        ).add_to(flood_map)

    st_folium(flood_map, use_container_width=True, height=550)

st.markdown("---")
st.code("streamlit run app.py", language="bash")
