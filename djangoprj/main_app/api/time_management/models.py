# main_app/models.py
from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    """
    Represents a project created by a user.

    Attributes:
        name (str): The name of the project.
        description (str): An optional description of the project.
        owner (User): The user who owns the project.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True) 
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")

    def __str__(self):
        return self.name

class Task(models.Model):
    """
    Represents a task that belongs to a project.

    Attributes:
        project (Project): The project this task belongs to.
        name (str): The name of the task.
        description (str): An optional description of the task.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class TimeEntry(models.Model):
    """
    Represents a time entry logged by a user for a specific task.

    Attributes:
        task (Task): The task this time entry is associated with.
        user (User): The user who logged the time.
        hours (Decimal): The number of hours spent.
        comment (str): An optional comment about the work done.
        date (date): The date when the work was done.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="time_entries")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    comment = models.TextField(blank=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.hours}h on {self.task.name} by {self.user.username}"
