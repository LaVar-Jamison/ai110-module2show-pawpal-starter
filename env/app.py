"""Streamlit UI for PawPal+."""

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A smart pet care planner")

# Streamlit reruns the script on every click, so keep the Owner in session_state.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Pet Owner")
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

# ---- Add a pet ------------------------------------------------------------
st.subheader("1. Add a pet")
with st.form("pet_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    name = c1.text_input("Name")
    species = c2.selectbox("Species", ["dog", "cat", "bird", "other"])
    age = c3.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not name.strip():
            st.error("Please enter a pet name.")
        elif owner.get_pet(name):
            st.warning(f"{name} is already on your list.")
        else:
            owner.add_pet(Pet(name.strip(), species, int(age)))
            st.success(f"Added {name}!")

# ---- Schedule a task ------------------------------------------------------
st.subheader("2. Schedule a task")
if not owner.pets:
    st.info("Add a pet first to start scheduling.")
else:
    with st.form("task_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        pet_name = c1.selectbox("Pet", [p.name for p in owner.pets])
        desc = c2.text_input("Task description", placeholder="Morning walk")
        c3, c4, c5 = st.columns(3)
        time_val = c3.time_input("Time")
        freq = c4.selectbox("Frequency", ["once", "daily", "weekly"])
        prio = c5.selectbox("Priority", ["high", "medium", "low"], index=1)
        if st.form_submit_button("Add task"):
            if not desc.strip():
                st.error("Please describe the task.")
            else:
                owner.get_pet(pet_name).add_task(
                    Task(desc.strip(), time_val.strftime("%H:%M"), freq, priority=prio)
                )
                st.success(f"Scheduled '{desc}' for {pet_name}.")

# ---- Conflict warnings ----------------------------------------------------
for warning in scheduler.detect_conflicts():
    st.warning(f"⚠️ {warning}. Consider moving one of these tasks.")

# ---- Schedule view --------------------------------------------------------
st.subheader("3. Schedule")
f1, f2 = st.columns(2)
pet_filter = f1.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
status_filter = f2.selectbox("Filter by status", ["All", "Pending", "Completed"])

tasks = scheduler.filter_tasks(
    pet_name=None if pet_filter == "All" else pet_filter,
    completed={"All": None, "Pending": False, "Completed": True}[status_filter],
)
tasks = scheduler.sort_by_time(tasks)

if tasks:
    st.table([
        {"Date": str(t.due_date), "Time": t.time, "Pet": t.pet_name,
         "Task": t.description, "Frequency": t.frequency,
         "Priority": t.priority, "Status": "✅ Done" if t.completed else "⏳ Pending"}
        for t in tasks
    ])
else:
    st.info("No tasks match these filters.")

# ---- Complete a task ------------------------------------------------------
pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
if pending:
    st.subheader("4. Mark a task complete")
    labels = {f"{t.due_date} {t.time} | {t.pet_name}: {t.description}": t for t in pending}
    choice = st.selectbox("Task", list(labels))
    if st.button("Mark complete"):
        nxt = scheduler.mark_task_complete(labels[choice])
        if nxt:
            st.success(f"Done! Next {nxt.frequency} task scheduled for {nxt.due_date}.")
        else:
            st.success("Done!")
        st.rerun()