# modules/project_management_page.py

import streamlit as st
import pandas as pd
from modules.helpers import api_request, parse_hours_string, export_to_excel


from datetime import date, timedelta

def display_dashboard(token):
    """
    Render the Streamlit dashboard for visualizing project time summaries.

    Displays an overview of projects with filters (current week, last week, 
    current month, last month, or all time). Retrieves project summary data 
    from the API and displays it in both a table and a bar chart. Also provides 
    an option to export the data to Excel.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the dashboard UI directly in the Streamlit app.
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("Overview")

    with col3:
        filter_options = ["Current Week", "Last Week", "Current Month", "Last Month", "All Time"]
        selected_option = st.selectbox(
            "Filter by:",
            options=filter_options,
            index=0,
        )
    
    st.markdown("---")

    start_date, end_date = None, None
    today = date.today()

    if selected_option == "Current Week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    
    elif selected_option == "Last Week":
        start_of_this_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_last_week + timedelta(days=4)
        start_date = start_of_last_week
        end_date = end_of_last_week

    elif selected_option == "Current Month":
        start_date = today.replace(day=1)
        end_date = today

    elif selected_option == "Last Month":
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    
    endpoint = 'projects/summary/'
    if start_date and end_date:
        endpoint += f'?start_date={start_date}&end_date={end_date}'
    
    summary_data = api_request('get', endpoint, token)

    if not summary_data:
        st.info("No projects or time data to display for the selected period.")
        return

    df = pd.DataFrame(summary_data)
    df['total_hours'] = pd.to_numeric(df['total_hours'])
    df = df.drop(columns=['id'], errors='ignore')
    df_chart = df[df['total_hours'] > 0]

    if start_date and end_date:
        st.subheader(f"Hours Summary per Project ({start_date.strftime('%b %d')} to {end_date.strftime('%b %d')})")
    else:
        st.subheader("Hours Summary per Project (All Time)")

    # Display table without pyarrow using markdown
    table_html = "<table style='width:100%; border-collapse: collapse;'>"
    table_html += "<thead><tr style='background-color: #f0f2f6;'>"
    table_html += "<th style='padding: 12px; text-align: left; border-bottom: 2px solid #ddd;'>Project</th>"
    table_html += "<th style='padding: 12px; text-align: left; border-bottom: 2px solid #ddd;'>Total Hours</th>"
    table_html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        table_html += "<tr style='border-bottom: 1px solid #ddd;'>"
        table_html += f"<td style='padding: 12px;'>{row['name']}</td>"
        table_html += f"<td style='padding: 12px;'>{row['total_hours']:.2f} h</td>"
        table_html += "</tr>"

    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

    st.divider()
    if not df_chart.empty:
        # Display bar chart using HTML/CSS without pyarrow
        max_hours = df_chart['total_hours'].max()
        chart_html = "<div style='margin-top: 20px;'>"
        chart_html += "<p style='font-weight: bold; margin-bottom: 10px;'>Total hours</p>"

        for _, row in df_chart.iterrows():
            percentage = (row['total_hours'] / max_hours * 100) if max_hours > 0 else 0
            chart_html += f"<div style='margin-bottom: 10px;'>"
            chart_html += f"<div style='font-size: 14px; margin-bottom: 5px;'>{row['name']}</div>"
            chart_html += f"<div style='background-color: #f0f2f6; border-radius: 5px; overflow: hidden;'>"
            chart_html += f"<div style='background-color: #ff4b4b; height: 30px; width: {percentage}%; display: flex; align-items: center; padding-left: 10px; color: white; font-weight: bold; min-width: 60px;'>"
            chart_html += f"{row['total_hours']:.2f}h"
            chart_html += "</div></div></div>"

        chart_html += "</div>"
        st.markdown(chart_html, unsafe_allow_html=True)
    else:
        st.info("No projects have logged hours to display in the chart for the selected period.")
    st.divider()
    st.write("Click below to export the project hours for the selected period to Excel.")
    if st.button("Export"):
        export_to_excel(token, start_date, end_date)


def display_profile_page(token):
    """
    Render the Streamlit profile page for the authenticated user.

    Fetches the user's profile from the API and displays it in an editable form.
    Allows the user to update their name, company, team, and position, and 
    saves changes via a PATCH request. Provides navigation back to the dashboard.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the profile page UI directly in the Streamlit app.
    """
    st.header("Your Profile")

    profile_data = api_request('get', 'auth/profile/', token)

    if not profile_data:
        st.error("Could not load profile data. Please try again later.")
        return

    with st.form(key="profile_form"):        
        name = st.text_input("Full Name", value=profile_data.get('name', ''))
        company = st.text_input("Company", value=profile_data.get('company', ''))
        team = st.text_input("Team", value=profile_data.get('team', ''))
        position = st.text_input("Position / Role", value=profile_data.get('position', ''))
        
        submitted = st.form_submit_button("Save Changes")

        if submitted:
            payload = {
                "name": name,
                "company": company,
                "team": team,
                "position": position
            }
            response = api_request('patch', 'auth/profile/', token, json_data=payload)
            
            if response and 'name' in response:
                st.success("Profile updated successfully!")
                st.rerun()
            else:
                st.error("There was an error updating your profile.")

    if st.button("Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()


def display_manage_projects_page(token):
    """
    Render the Streamlit page for managing user projects.

    Displays a list of projects retrieved from the API and provides options to:
      - Create a new project (navigates to the create project page).
      - Edit an existing project (navigates to the edit project page).
      - Delete a project with confirmation.

    Projects are cached in `st.session_state['project_list']` to reduce API calls, 
    and the state is refreshed after project creation, editing, or deletion.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the project management UI directly in the Streamlit app.
    """
    st.header("Manage Projects")
    if st.button("➕ Create New Project"):
        st.session_state.page = 'create_project'
        if 'editing_project_id' in st.session_state:
            del st.session_state['editing_project_id']
        st.rerun()
    st.markdown("---")
    if 'project_list' not in st.session_state:
        st.session_state['project_list'] = api_request('get', 'projects/', token)
    projects = st.session_state.get('project_list')
    if not projects:
        st.info("No projects yet. Click the button above to create your first one!")
    else:
        for project in projects:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(project['name'])
                st.caption(project.get('description') or 'No description')
            with col2:
                if st.button("Edit", key=f"edit_proj_{project['id']}"):
                    st.session_state.page = 'edit_project'
                    st.session_state.editing_project_id = project['id']
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_proj_{project['id']}", type="secondary"):
                    st.session_state.confirm_delete_project_id = project['id']
            if st.session_state.get('confirm_delete_project_id') == project['id']:
                with st.warning(f"Are you sure you want to delete project '{project['name']}'?"):
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Delete", key=f"confirm_del_proj_{project['id']}", type="primary"):
                        if api_request('delete', f"projects/{project['id']}/", token):
                            st.success("Project deleted.")
                            del st.session_state.project_list
                            del st.session_state.confirm_delete_project_id
                            st.rerun()
                    if c2.button("Cancel", key=f"cancel_del_proj_{project['id']}"):
                        del st.session_state.confirm_delete_project_id
                        st.rerun()
            st.divider()


def display_project_form_page(token):
    """
    Render the Streamlit page for creating or editing a project.

    - If `st.session_state['editing_project_id']` is set, the form is pre-filled 
      with the existing project data and acts as an "Edit Project" page.
    - If not, it acts as a "Create New Project" page.

    On submission:
      - Validates required fields (project name).
      - Sends a POST request to create a project, or a PATCH request to update an existing one.
      - Clears cached project data from session state and redirects back to 
        the "Manage Projects" page.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the form directly in the Streamlit app.
    """
    editing_id = st.session_state.get('editing_project_id')
    project_data = {}
    if editing_id:
        st.header("Edit Project")
        if 'project_list' not in st.session_state:
            st.session_state.project_list = api_request('get', 'projects/', token)
        projects = st.session_state.get('project_list', [])
        project_data = next((p for p in projects if p['id'] == editing_id), {})
    else:
        st.header("Create New Project")
    with st.form(key="project_form"):
        name = st.text_input("Project Name", value=project_data.get('name', ''))
        description = st.text_area("Description", value=project_data.get('description', ''))
        submitted = st.form_submit_button("Save Changes" if editing_id else "Create Project")
        if submitted:
            if not name:
                st.error("Project Name is required.")
            else:
                payload = {'name': name, 'description': description}
                endpoint = f"projects/{editing_id}/" if editing_id else "projects/"
                method = 'patch' if editing_id else 'post'
                if api_request(method, endpoint, token, json_data=payload):
                    st.success(f"Project {'updated' if editing_id else 'created'} successfully.")
                    if 'project_list' in st.session_state:
                        del st.session_state.project_list
                    st.session_state.page = 'manage_projects'
                    if editing_id:
                        del st.session_state.editing_project_id
                    st.rerun()
    if st.button("Back to Project List"):
        st.session_state.page = 'manage_projects'
        if editing_id:
            del st.session_state.editing_project_id
        st.rerun()


def display_manage_tasks_page(token):
    """
    Render the Streamlit page for managing tasks within projects.

    Features:
      - Displays a dropdown to select one of the user's projects.
      - Lists tasks belonging to the selected project with their total logged hours.
      - Provides actions for each task:
          - Register time entry.
          - Edit task.
          - Delete task (with confirmation).
      - Allows creating a new task for the selected project.

    State management:
      - `st.session_state.project_list`: Cached list of projects.
      - `st.session_state.selected_project_id`: Currently selected project.
      - `st.session_state.time_entry_task_id`: Task for which a time entry is being registered.
      - `st.session_state.editing_task_id`: Task being edited.
      - `st.session_state.confirm_delete_task_id`: Task awaiting delete confirmation.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the task management UI directly in the Streamlit app.
    """
    st.header("Manage Tasks")
    if 'project_list' not in st.session_state:
        st.session_state.project_list = api_request('get', 'projects/', token)
    projects = st.session_state.get('project_list')
    if not projects:
        st.warning("Create a project first to be able to add tasks.")
        return
    project_map = {p['id']: p['name'] for p in projects}
    if 'selected_project_id' not in st.session_state:
        st.session_state.selected_project_id = list(project_map.keys())[0] if project_map else None
    selected_project_id = st.selectbox(
        "Select a project", options=list(project_map.keys()),
        format_func=lambda pid: project_map.get(pid, "Unknown"), key='selected_project_id'
    )
    st.button("➕ New Task", on_click=lambda: st.session_state.update({
        'page': 'create_task', 'project_for_new_task': selected_project_id
    }))
    if selected_project_id:
        tasks = api_request('get', f"projects/{selected_project_id}/tasks/", token)
        if not tasks:
            st.info("No tasks for this project.")
        for task in (tasks or []):
            task_id = task['id']
            response_data = api_request('get', f"tasks/{task_id}/time-entries/", token)
            total_hours = response_data.get('total_hours', 0.0) if response_data else 0.0
            formatted_total = parse_hours_string(total_hours)
            st.subheader(task['name'])
            st.caption(f"Total time: {formatted_total}")
            st.caption(task.get('description') or 'No description')
            col1, col2, col3 = st.columns([1, 1, 1])
            if col1.button("Register Time", key=f"register_time_{task_id}"):
                st.session_state.page = 'register_time'
                st.session_state.time_entry_task_id = task_id
                st.rerun()
            if col2.button("Edit", key=f"edit_task_{task_id}"):
                st.session_state.page = 'edit_task'
                st.session_state.editing_task_id = task_id
                st.rerun()
            if col3.button("Delete", key=f"delete_task_{task_id}", type="secondary"):
                st.session_state.confirm_delete_task_id = task_id
            if st.session_state.get('confirm_delete_task_id') == task_id:
                 with st.warning(f"Delete task '{task['name']}'? All time entries will be lost."):
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Delete", key=f"confirm_del_task_{task_id}", type="primary"):
                        if api_request('delete', f"tasks/{task_id}/", token):
                            st.success("Task deleted.")
                            del st.session_state.confirm_delete_task_id
                            st.rerun()
                    if c2.button("Cancel", key=f"cancel_del_task_{task_id}"):
                        del st.session_state.confirm_delete_task_id
                        st.rerun()
            st.divider()


def display_task_form_page(token):
    """
    Render the Streamlit page for creating or editing a task.

    - If `st.session_state['editing_task_id']` is set, the form is pre-filled 
      with the existing task data and acts as an "Edit Task" page.
    - If not, it acts as a "Create New Task" page.

    Requirements:
      - A project must be selected (`st.session_state['project_for_new_task']`).
        If no project is selected, the user is redirected back to the "Manage Tasks" page.

    On submission:
      - Validates required fields (task name).
      - Sends a POST request to create a new task under the selected project, 
        or a PATCH request to update an existing task.
      - Updates session state and navigates back to the "Manage Tasks" page.

    Session state keys used:
      - 'editing_task_id': The task currently being edited (if any).
      - 'project_for_new_task': The project ID where a new task will be created.
      - 'selected_project_id': Used when fetching tasks for editing.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the form directly in the Streamlit app.
    """
    editing_id = st.session_state.get('editing_task_id')
    project_id = st.session_state.get('project_for_new_task')
    task_data = {}
    if editing_id:
        st.header("Edit Task")
        project_id_for_fetch = st.session_state.get('selected_project_id')
        tasks = api_request('get', f"projects/{project_id_for_fetch}/tasks/", token)
        task_data = next((t for t in (tasks or []) if t['id'] == editing_id), {})
    else:
        st.header("Create New Task")
    if not project_id:
        st.error("A project must be selected to create a task. Please go back to the 'Manage Tasks' page.")
        if st.button("Back to Tasks"):
            st.session_state.page = 'manage_tasks'
            st.rerun()
        return
    with st.form(key="task_form"):
        name = st.text_input("Task Name", value=task_data.get('name', ''))
        description = st.text_area("Description (optional)", value=task_data.get('description', ''))
        submitted = st.form_submit_button("Save Changes" if editing_id else "Create Task")
        if submitted:
            if not name:
                st.error("Task Name is required.")
            else:
                payload = {'name': name, 'description': description, 'project': project_id}
                endpoint = f"tasks/{editing_id}/" if editing_id else f"projects/{project_id}/tasks/"
                method = 'patch' if editing_id else 'post'
                if api_request(method, endpoint, token, json_data=payload):
                    st.success(f"Task {'updated' if editing_id else 'created'} successfully.")
                    st.session_state.page = 'manage_tasks'
                    if 'project_for_new_task' in st.session_state:
                        del st.session_state.project_for_new_task
                    if editing_id:
                        del st.session_state.editing_task_id
                    st.rerun()
    if st.button("Back to Tasks"):
        st.session_state.page = 'manage_tasks'
        if 'project_for_new_task' in st.session_state:
            del st.session_state.project_for_new_task
        if editing_id:
           del st.session_state.editing_task_id
        st.rerun()


def display_time_entry_form(token):
    """
    Render the Streamlit page for registering and managing time entries for a task.

    Features:
      - Form for creating a new time entry:
          - Duration (string, e.g., "2h 30m")
          - Comment (optional)
          - Date
      - Submits a POST request to create the entry.
      - Handles validation errors returned by the API.
      - Lists existing time entries for the task with options to delete them.
      - Provides navigation back to the task management page.

    Session state keys used:
      - 'time_entry_task_id': The ID of the task for which entries are being managed.

    Args:
        token (str): Authentication token for the API request.

    Returns:
        None: Renders the form and entries list directly in the Streamlit app.
    """
    task_id = st.session_state.get('time_entry_task_id')
    if not task_id:
        st.error("Task ID not found.")
        return
    st.header("Register Time Entry")
    with st.form(f"time_entry_form_{task_id}"):
        duration = st.text_input("Duration (e.g., 2h 30m)")
        comment = st.text_area("Comment (optional)")
        date = st.date_input("Date")
        submitted = st.form_submit_button("Submit Time Entry")
        if submitted:
            if not duration.strip():
                st.error("Duration is required.")
            else:
                payload = {"duration": duration, "comment": comment, "date": str(date)}
                response = api_request('post', f"tasks/{task_id}/time-entries/", token, json_data=payload)
                if response is True or (isinstance(response, dict) and 'id' in response):
                    st.success("Time entry registered successfully!")
                    del st.session_state['time_entry_task_id']
                    st.session_state.page = 'manage_tasks'
                    st.rerun()
                elif isinstance(response, dict):
                    for field, messages in response.items():
                        st.error(f"Error in '{field.capitalize()}': {', '.join(messages)}")
                else:
                    st.error("An unknown error occurred. Please try again.")
    st.markdown("---")
    st.subheader("Registered Entries for this Task")
    response_data = api_request('get', f"tasks/{task_id}/time-entries/", token)
    if not response_data or not response_data.get('entries'):
        st.info("No time entries yet for this task.")
    else:
        for entry in response_data.get('entries', []):
            col1, col2, col3 = st.columns([2, 3, 1])
            col1.markdown(f"**{parse_hours_string(entry.get('hours'))}** on `{entry.get('date')}`")
            col2.markdown(entry.get('comment') or "*No comment*")
            if col3.button("🗑️", key=f"delete_entry_{entry['id']}", help="Delete this entry"):
                if api_request('delete', f"time-entries/{entry['id']}/", token):
                    st.success("Entry deleted.")
                    st.rerun()
    st.divider()
    if st.button("Back to All Tasks"):
        st.session_state.page = 'manage_tasks'
        del st.session_state['time_entry_task_id']
        st.rerun()


def main_page():
    """
    Render the main Streamlit application page with navigation.

    Handles:
      - Checking if the user is logged in (requires a token in session state).
      - Sidebar navigation between different sections of the app:
          - Dashboard
          - Manage Projects
          - Manage Tasks
          - Profile
          - Logout (clears session state and reruns)
      - Routes to the correct page renderer based on `st.session_state['page']`.

    Session state keys used:
      - 'token': Authentication token (required for accessing app content).
      - 'page': Current page identifier (defaults to 'dashboard').

    Returns:
        None: Renders the appropriate page directly in the Streamlit app.
    """
    token = st.session_state.get('token')
    if not token:
        st.warning("Please log in.")
        return
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    with st.sidebar:
        st.header("Navigation")
        st.divider()
        if st.button("Dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        if st.button("Manage Projects"):
            st.session_state.page = 'manage_projects'
            st.rerun()
        if st.button("Manage Tasks"):
            st.session_state.page = 'manage_tasks'
            st.rerun()
        if st.button("Profile"):
            st.session_state.page = "profile"
            st.rerun()
        st.divider()
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    page = st.session_state.get('page')
    
    if page == 'dashboard':
        display_dashboard(token)
    elif page == 'profile':
        display_profile_page(token)
    elif page == 'manage_projects':
        display_manage_projects_page(token)
    elif page in ['create_project', 'edit_project']:
        display_project_form_page(token)
    elif page == 'manage_tasks':
        display_manage_tasks_page(token)
    elif page in ['create_task', 'edit_task']:
        display_task_form_page(token)
    elif page == 'register_time':
        display_time_entry_form(token)
    else:
        st.session_state.page = 'dashboard'
        st.rerun()
