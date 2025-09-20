import streamlit as st
import pandas as pd
from datetime import date
from backend import (
    create_tables, create_goal, get_goals, update_goal_status,
    create_task, get_tasks_for_goal, update_task_status,
    create_feedback, get_feedback_for_goal, check_for_automated_feedback
)

# Initialize database
create_tables()

# --- Mock User Login (for demo purposes) ---
# In a real app, this would be a proper login system.
st.sidebar.title("Login/User")
user_role = st.sidebar.radio("Select Role", ["Manager", "Employee"])
user_id = st.sidebar.number_input("Enter your ID", min_value=1)
st.sidebar.info("Use Manager ID: 1, Employee ID: 2")

# --- MAIN APP LAYOUT ---
st.title("📊 Performance Management System")

# --- Tabs for different functionalities ---
tab1, tab2, tab3, tab4 = st.tabs(["Goal Setting", "Progress Tracking", "Feedback", "Reporting"])

# 1. Goal Setting
with tab1:
    st.header("Goal & Task Setting")
    
    if user_role == "Manager":
        st.subheader("Set a New Goal")
        with st.form("new_goal_form"):
            employee_id = st.number_input("Employee ID", min_value=1, value=2)
            description = st.text_area("Goal Description", placeholder="e.g., Increase sales by 15% this quarter.")
            due_date = st.date_input("Due Date", min_value=date.today())
            submitted = st.form_submit_button("Set Goal")
            if submitted:
                create_goal(employee_id, user_id, description, due_date)
                st.success("Goal set successfully!")
    
    st.subheader("Your Goals")
    
    if user_role == "Manager":
        goals = get_goals(manager_id=user_id)
        st.write("### Goals You've Set")
    else: # Employee
        goals = get_goals(employee_id=user_id)
        st.write("### Your Assigned Goals")
        
    if goals:
        df_goals = pd.DataFrame(goals, columns=["ID", "Employee ID", "Manager ID", "Description", "Due Date", "Status", "Created At"])
        st.dataframe(df_goals, use_container_width=True)
    else:
        st.info("No goals found.")

# 2. Progress Tracking
with tab2:
    st.header("Progress Tracking")
    
    selected_goal_id = st.selectbox("Select a Goal to Track", [g['goal_id'] for g in get_goals(employee_id=user_id) or get_goals(manager_id=user_id)])
    
    if selected_goal_id:
        st.subheader("Log a Task")
        with st.form("new_task_form"):
            task_description = st.text_input("Task Description")
            submitted_task = st.form_submit_button("Add Task")
            if submitted_task:
                create_task(selected_goal_id, task_description)
                st.success("Task submitted for manager approval!")
        
        st.subheader("Tasks for this Goal")
        tasks = get_tasks_for_goal(selected_goal_id)
        if tasks:
            df_tasks = pd.DataFrame(tasks, columns=["Task ID", "Goal ID", "Description", "Status"])
            st.dataframe(df_tasks, use_container_width=True)
            
            # Manager-only options for updating status
            if user_role == "Manager":
                st.subheader("Update Task/Goal Status")
                task_to_update = st.selectbox("Select Task to Update", [t['task_id'] for t in tasks])
                if task_to_update:
                    new_task_status = st.selectbox("New Task Status", ["Pending", "Approved", "Rejected", "Completed"])
                    if st.button("Update Task"):
                        update_task_status(task_to_update, new_task_status)
                        st.success("Task status updated!")
                        st.experimental_rerun()
                
                new_goal_status = st.selectbox("Update Goal Status", ["Draft", "In Progress", "Completed", "Cancelled"])
                if st.button("Update Goal Status"):
                    update_goal_status(selected_goal_id, new_goal_status)
                    st.success("Goal status updated!")
                    st.experimental_rerun()

# 3. Feedback
with tab3:
    st.header("Feedback")
    
    selected_goal_id_fb = st.selectbox("Select a Goal for Feedback", [g['goal_id'] for g in get_goals(employee_id=user_id) or get_goals(manager_id=user_id)], key="fb_select")
    
    if selected_goal_id_fb:
        # Managers can give feedback
        if user_role == "Manager":
            st.subheader("Provide Feedback")
            with st.form("new_feedback_form"):
                feedback_content = st.text_area("Your Feedback")
                submitted_feedback = st.form_submit_button("Submit Feedback")
                if submitted_feedback:
                    # Assuming a way to get employee_id for the selected goal
                    goal_info = [g for g in get_goals(manager_id=user_id) if g['goal_id'] == selected_goal_id_fb][0]
                    create_feedback(selected_goal_id_fb, user_id, goal_info['employee_id'], feedback_content)
                    st.success("Feedback submitted!")

        # Display feedback for the selected goal
        st.subheader("Feedback on this Goal")
        feedback_list = get_feedback_for_goal(selected_goal_id_fb)
        if feedback_list:
            df_feedback = pd.DataFrame(feedback_list, columns=["ID", "Goal ID", "Manager ID", "Employee ID", "Content", "Date"])
            st.dataframe(df_feedback, use_container_width=True)
        else:
            st.info("No feedback yet.")

# 4. Reporting
with tab4:
    st.header("Performance History & Reporting")
    
    reporting_employee_id = st.number_input("Enter Employee ID for Report", min_value=1, value=user_id)
    
    st.subheader(f"Performance History for Employee ID: {reporting_employee_id}")
    
    # Get all goals (past and present)
    employee_goals = get_goals(employee_id=reporting_employee_id)
    if employee_goals:
        for goal in employee_goals:
            st.write(f"#### Goal ID: {goal['goal_id']} - {goal['description']}")
            st.write(f"**Status:** {goal['status']} | **Due Date:** {goal['due_date']}")
            
            # Show associated tasks
            st.markdown("##### Tasks")
            tasks = get_tasks_for_goal(goal['goal_id'])
            if tasks:
                df_tasks_report = pd.DataFrame(tasks, columns=["Task ID", "Goal ID", "Description", "Status"])
                st.dataframe(df_tasks_report, use_container_width=True)
            else:
                st.info("No tasks logged for this goal.")
            
            # Show associated feedback
            st.markdown("##### Feedback")
            feedback = get_feedback_for_goal(goal['goal_id'])
            if feedback:
                df_feedback_report = pd.DataFrame(feedback, columns=["ID", "Goal ID", "Manager ID", "Employee ID", "Content", "Date"])
                st.dataframe(df_feedback_report, use_container_width=True)
            else:
                st.info("No feedback for this goal.")
            
            st.markdown("---")
    else:
        st.info("No performance history found for this employee.")
