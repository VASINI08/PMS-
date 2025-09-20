# frontend.py

import streamlit as st
import pandas as pd
from datetime import date
from backend import (
    create_goal, get_goals, update_goal_status,
    create_task, get_tasks_for_goal, update_task_status,
    create_feedback, get_feedback_for_goal, check_for_automated_feedback
)

# --- Mock User Login (for demo purposes) ---
st.sidebar.title("Login/User")
user_role = st.sidebar.radio("Select Role", ["Manager", "Employee"])
# Using default values for a quick demo
user_id = st.sidebar.number_input("Enter your ID", min_value=1, value=1 if user_role == "Manager" else 2)
st.sidebar.info("Use Manager ID: 1, Employee ID: 2")

# --- MAIN APP LAYOUT ---
st.title("📊 Performance Management System")

# Run the automated check every time the app loads
check_for_automated_feedback()

# --- Tabs for different functionalities ---
tab1, tab2, tab3, tab4 = st.tabs(["Goal Setting", "Progress Tracking", "Feedback", "Reporting"])

# 1. Goal Setting
with tab1:
    st.header("Goal & Task Setting")
    
    if user_role == "Manager":
        st.subheader("Set a New Goal")
        with st.form("new_goal_form"):
            employee_id = st.number_input("Employee ID", min_value=1, value=2, key='emp_id_input')
            description = st.text_area("Goal Description")
            due_date = st.date_input("Due Date", min_value=date.today())
            submitted = st.form_submit_button("Set Goal")
            if submitted:
                create_goal(employee_id, user_id, description, due_date)
                st.success("Goal set successfully!")
    
    st.subheader("Your Goals")
    
    if user_role == "Manager":
        goals_data = get_goals(manager_id=user_id)
    else: # Employee
        goals_data = get_goals(employee_id=user_id)
        
    if goals_data:
        # Convert list of tuples to a DataFrame for display
        df_goals = pd.DataFrame(goals_data, columns=["goal_id", "employee_id", "manager_id", "description", "due_date", "status", "created_at"])
        st.dataframe(df_goals, use_container_width=True)
    else:
        st.info("No goals found.")

# 2. Progress Tracking
with tab2:
    st.header("Progress Tracking")
    
    # Get a list of goals relevant to the user
    relevant_goals = get_goals(employee_id=user_id) if user_role == "Employee" else get_goals(manager_id=user_id)
    
    if not relevant_goals:
        st.info("No goals available for tracking.")
    else:
        goal_options = {goal[3]: goal[0] for goal in relevant_goals} # Map description to ID
        selected_goal_desc = st.selectbox("Select a Goal to Track", list(goal_options.keys()))
        selected_goal_id = goal_options[selected_goal_desc]
        
        st.subheader("Log a Task")
        with st.form("new_task_form"):
            task_description = st.text_input("Task Description")
            submitted_task = st.form_submit_button("Add Task")
            if submitted_task:
                create_task(selected_goal_id, task_description)
                st.success("Task submitted for manager approval!")
                
        st.subheader("Tasks for this Goal")
        tasks_data = get_tasks_for_goal(selected_goal_id)
        if tasks_data:
            df_tasks = pd.DataFrame(tasks_data, columns=["task_id", "goal_id", "description", "status"])
            st.dataframe(df_tasks, use_container_width=True)
            
            if user_role == "Manager":
                st.subheader("Update Task/Goal Status")
                task_to_update = st.selectbox("Select Task to Update", df_tasks['task_id'].tolist(), key='task_update_select')
                if task_to_update:
                    new_task_status = st.selectbox("New Task Status", ["Pending", "Approved", "Rejected", "Completed"], key='task_status_select')
                    if st.button("Update Task Status"):
                        update_task_status(task_to_update, new_task_status)
                        st.success("Task status updated!")
                        st.experimental_rerun()
                
                goal_status_update = st.selectbox("Update Goal Status", ["Draft", "In Progress", "Completed", "Cancelled"], key='goal_status_select')
                if st.button("Update Goal Status"):
                    update_goal_status(selected_goal_id, goal_status_update)
                    st.success("Goal status updated!")
                    st.experimental_rerun()
                
# 3. Feedback
with tab3:
    st.header("Feedback")
    
    relevant_goals_fb = get_goals(employee_id=user_id) if user_role == "Employee" else get_goals(manager_id=user_id)
    if not relevant_goals_fb:
        st.info("No goals available for feedback.")
    else:
        goal_options_fb = {goal[3]: goal[0] for goal in relevant_goals_fb}
        selected_goal_desc_fb = st.selectbox("Select a Goal for Feedback", list(goal_options_fb.keys()), key='fb_select')
        selected_goal_id_fb = goal_options_fb[selected_goal_desc_fb]

        if user_role == "Manager":
            st.subheader("Provide Feedback")
            with st.form("new_feedback_form"):
                feedback_content = st.text_area("Your Feedback")
                submitted_feedback = st.form_submit_button("Submit Feedback")
                if submitted_feedback:
                    # Retrieve employee_id from the selected goal's data
                    goal_info = next(g for g in relevant_goals_fb if g[0] == selected_goal_id_fb)
                    employee_id = goal_info[1]
                    create_feedback(selected_goal_id_fb, user_id, employee_id, feedback_content)
                    st.success("Feedback submitted!")

        st.subheader("Feedback on this Goal")
        feedback_data = get_feedback_for_goal(selected_goal_id_fb)
        if feedback_data:
            df_feedback = pd.DataFrame(feedback_data, columns=["feedback_id", "goal_id", "manager_id", "employee_id", "content", "given_at"])
            st.dataframe(df_feedback, use_container_width=True)
        else:
            st.info("No feedback yet.")

# 4. Reporting
with tab4:
    st.header("Performance History & Reporting")
    
    reporting_employee_id = st.number_input("Enter Employee ID for Report", min_value=1, value=user_id, key='report_id_input')
    
    st.subheader(f"Performance History for Employee ID: {reporting_employee_id}")
    
    employee_goals = get_goals(employee_id=reporting_employee_id)
    if employee_goals:
        for goal in employee_goals:
            st.write(f"#### Goal ID: {goal[0]} - {goal[3]}")
            st.write(f"**Status:** {goal[5]} | **Due Date:** {goal[4]}")
            
            st.markdown("##### Tasks")
            tasks = get_tasks_for_goal(goal[0])
            if tasks:
                df_tasks_report = pd.DataFrame(tasks, columns=["task_id", "goal_id", "description", "status"])
                st.dataframe(df_tasks_report, use_container_width=True)
            else:
                st.info("No tasks logged for this goal.")
            
            st.markdown("##### Feedback")
            feedback = get_feedback_for_goal(goal[0])
            if feedback:
                df_feedback_report = pd.DataFrame(feedback, columns=["feedback_id", "goal_id", "manager_id", "employee_id", "content", "given_at"])
                st.dataframe(df_feedback_report, use_container_width=True)
            else:
                st.info("No feedback for this goal.")
            
            st.markdown("---")
    else:
        st.info("No performance history found for this employee.")
