from django.urls import path
from main_app.api.time_management import views

"""
URL patterns for project, task, and time entry management.

Endpoints:
- /projects/                : List all projects or create a new one.
- /projects/<id>/           : Retrieve, update, or delete a specific project.
- /projects/summary/        : Get a summary of all projects with total tracked hours.

- /projects/<project_id>/tasks/ : List tasks for a project or create a new one.
- /tasks/<id>/                  : Retrieve, update, or delete a specific task.

- /tasks/<task_id>/time-entries/ : List or create time entries for a specific task.
- /time-entries/<id>/            : Retrieve, update, or delete a specific time entry.
"""

TIME_MANAGEMENT_URLS = [
    # Projects
    path('projects/', view=views.ProjectAPIView.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', view=views.ProjectAPIView.as_view(), name='project-detail'),
    path('projects/summary/', view=views.ProjectSummaryAPIView.as_view(), name='project-summary'),

    # Tasks within a specific project
    path('projects/<int:project_id>/tasks/', view=views.TaskAPIView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', view=views.TaskAPIView.as_view(), name='task-detail'),

    # Time entries within a specific task
    path('tasks/<int:task_id>/time-entries/', view=views.TimeEntryListCreateAPIView.as_view(), name='timeentry-list-create'),
    path('time-entries/<int:pk>/', view=views.TimeEntryDetailAPIView.as_view(), name='timeentry-detail'),
]
