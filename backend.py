# backend.py

import psycopg2
import streamlit as st
from datetime import datetime

# --- DATABASE CONNECTION ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=st.secrets["db_credentials"]["PMS"],
            user=st.secrets["db_credentials"]["postgres"],
            password=st.secrets["db_credentials"]["Vani@08"],
            host=st.secrets["db_credentials"]["localhost"],
            port=st.secrets["db_credentials"]["5432"]
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# --- TABLE SETUP ---
def create_tables():
    """Creates necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS goals (
                        goal_id SERIAL PRIMARY KEY,
                        employee_id INTEGER NOT NULL,
                        manager_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        due_date DATE NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id SERIAL PRIMARY KEY,
                        goal_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT NOT NULL,
                        FOREIGN KEY (goal_id) REFERENCES goals (goal_id) ON DELETE CASCADE
                    );
                ''')
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id SERIAL PRIMARY KEY,
                        goal_id INTEGER NOT NULL,
                        manager_id INTEGER NOT NULL,
                        employee_id INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        given_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (goal_id) REFERENCES goals (goal_id) ON DELETE CASCADE
                    );
                ''')
            conn.commit()
        except Exception as e:
            st.error(f"Error creating tables: {e}")
        finally:
            conn.close()

# --- CRUD Functions for Goals ---
def create_goal(employee_id, manager_id, description, due_date):
    """Adds a new goal to the database."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO goals (employee_id, manager_id, description, due_date, status) VALUES (%s, %s, %s, %s, %s)",
                            (employee_id, manager_id, description, due_date, 'Draft'))
            conn.commit()
        finally:
            conn.close()

def get_goals(employee_id=None, manager_id=None):
    """Fetches goals based on employee or manager ID."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                query = "SELECT * FROM goals"
                params = []
                if employee_id:
                    query += " WHERE employee_id = %s"
                    params.append(employee_id)
                elif manager_id:
                    query += " WHERE manager_id = %s"
                    params.append(manager_id)
                
                cur.execute(query, params)
                goals = cur.fetchall()
                return goals
        finally:
            conn.close()
    return []

def update_goal_status(goal_id, new_status):
    """Updates the status of a specific goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE goals SET status = %s WHERE goal_id = %s", (new_status, goal_id))
            conn.commit()
        finally:
            conn.close()

# --- CRUD Functions for Tasks ---
def create_task(goal_id, description):
    """Adds a new task for a goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO tasks (goal_id, description, status) VALUES (%s, %s, %s)",
                            (goal_id, description, 'Pending'))
            conn.commit()
        finally:
            conn.close()

def get_tasks_for_goal(goal_id):
    """Fetches all tasks for a specific goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE goal_id = %s", (goal_id,))
                tasks = cur.fetchall()
                return tasks
        finally:
            conn.close()
    return []

def update_task_status(task_id, new_status):
    """Updates the status of a specific task."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE tasks SET status = %s WHERE task_id = %s", (new_status, task_id))
            conn.commit()
        finally:
            conn.close()

# --- CRUD Functions for Feedback ---
def create_feedback(goal_id, manager_id, employee_id, content):
    """Adds new feedback for a goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO feedback (goal_id, manager_id, employee_id, content) VALUES (%s, %s, %s, %s)",
                            (goal_id, manager_id, employee_id, content))
            conn.commit()
        finally:
            conn.close()

def get_feedback_for_goal(goal_id):
    """Fetches feedback for a specific goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM feedback WHERE goal_id = %s", (goal_id,))
                feedback = cur.fetchall()
                return feedback
        finally:
            conn.close()
    return []

# --- Automated Feedback (Trigger-like Functionality) ---
def check_for_automated_feedback():
    """Checks for goals that are past due and provides automated feedback."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Find goals past their due date that haven't been completed or cancelled
                cur.execute("SELECT goal_id, employee_id, manager_id, description FROM goals WHERE due_date < NOW() AND status NOT IN ('Completed', 'Cancelled');")
                goals_to_review = cur.fetchall()
                
                for goal in goals_to_review:
                    # Check if automated feedback already exists to avoid duplicates
                    cur.execute("SELECT * FROM feedback WHERE goal_id = %s AND content LIKE 'Automated reminder:%'", (goal[0],))
                    existing_feedback = cur.fetchone()
                    
                    if not existing_feedback:
                        automated_message = f"Automated reminder: This goal '{goal[3]}' is past its due date."
                        cur.execute("INSERT INTO feedback (goal_id, manager_id, employee_id, content) VALUES (%s, %s, %s, %s)",
                                    (goal[0], goal[2], goal[1], automated_message))
                        conn.commit()
                        st.info(f"Automated feedback created for goal {goal[0]}")
        except Exception as e:
            st.error(f"Error in automated feedback check: {e}")
        finally:
            conn.close()

# Call this function once at the start of the app to ensure tables are created
create_tables()
