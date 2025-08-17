from decimal import Decimal
from django.db.models import Sum, Q, DecimalField, FilteredRelation
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from main_app.api.time_management.models import Project, Task, TimeEntry
from main_app.api.time_management.serializers import (
    ProjectSerializer, 
    TaskSerializer, 
    TimeEntrySerializer, 
    ProjectSummarySerializer
)


class ProjectAPIView(generics.GenericAPIView):
    """
    API endpoint for managing projects.

    Supports authenticated users in creating, retrieving, updating, 
    and deleting their own projects.
    """
    serializer_class = ProjectSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit the queryset to projects owned by the authenticated user.

        Returns:
            QuerySet: Projects belonging to the current user.
        """
        return Project.objects.filter(owner=self.request.user)

    def get(self, request, pk=None):
        """
        Handle GET requests.

        Args:
            request (Request): The HTTP request object.
            pk (int, optional): Primary key of the project (if provided).

        Returns:
            Response: Serialized project data.
        """
        if pk:
            project = generics.get_object_or_404(self.get_queryset(), pk=pk)
            serializer = self.serializer_class(project)
            return Response(serializer.data)
        projects = self.get_queryset()
        serializer = self.serializer_class(projects, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Handle POST requests to create a new project.

        Args:
            request (Request): The HTTP request containing project data.

        Returns:
            Response: Serialized project data if created successfully,
                      or validation errors otherwise.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Handle PATCH requests to update an existing project.

        Args:
            request (Request): The HTTP request containing partial project data.
            pk (int): Primary key of the project to update.

        Returns:
            Response: Updated project data or validation errors.
        """
        project = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Handle DELETE requests to remove a project.

        Args:
            request (Request): The HTTP request object.
            pk (int): Primary key of the project to delete.

        Returns:
            Response: 204 No Content if deletion succeeds.
        """
        project = generics.get_object_or_404(self.get_queryset(), pk=pk)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectSummaryAPIView(generics.GenericAPIView):
    """
    API endpoint for retrieving a summary of projects with total tracked hours.

    Authenticated users can request summaries of their projects. Optionally, 
    a date range (`start_date`, `end_date`) can be provided to filter the 
    time entries considered in the summary.
    """
    serializer_class = ProjectSummarySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit the queryset to projects owned by the authenticated user.

        Returns:
            QuerySet: Projects belonging to the current user.
        """
        return Project.objects.filter(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve project summaries.

        Args:
            request (Request): The HTTP request object. May include optional
                query parameters:
                - start_date (str): Filter start date (YYYY-MM-DD).
                - end_date (str): Filter end date (YYYY-MM-DD).
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A list of projects with their total tracked hours.
        """
        base_qs = self.get_queryset()

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            base_qs = base_qs.annotate(
                filtered_time_entries=FilteredRelation(
                    'tasks__time_entries',
                    condition=Q(tasks__time_entries__date__range=[start_date, end_date])
                )
            )

            summary_qs = base_qs.annotate(
                total_hours=Coalesce(
                    Sum('filtered_time_entries__hours'),
                    Decimal('0.00'),
                    output_field=DecimalField()
                )
            )
        else:
            # All time
            summary_qs = base_qs.annotate(
                total_hours=Coalesce(
                    Sum('tasks__time_entries__hours'),
                    Decimal('0.00'),
                    output_field=DecimalField()
                )
            )

        summary_qs = summary_qs.order_by('-total_hours')
        serializer = self.get_serializer(summary_qs, many=True)
        return Response(serializer.data)


class TaskAPIView(generics.GenericAPIView):
    """
    API endpoint for managing tasks within projects.

    Supports authenticated users in creating, retrieving, updating, 
    and deleting tasks that belong to their own projects.
    """
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit the queryset to tasks belonging to projects owned by the authenticated user.

        Returns:
            QuerySet: Tasks linked to the current user's projects.
        """
        return Task.objects.filter(project__owner=self.request.user)

    def get(self, request, pk=None, project_id=None):
        """
        Handle GET requests for tasks.

        Args:
            request (Request): The HTTP request object.
            pk (int, optional): Primary key of a task to retrieve.
            project_id (int, optional): ID of a project to list its tasks.

        Returns:
            Response: 
                - Serialized task if `pk` is provided.  
                - List of tasks if `project_id` is provided.  
                - Empty list otherwise.
        """
        queryset = self.get_queryset()
        if pk:
            task = generics.get_object_or_404(queryset, pk=pk)
            serializer = self.serializer_class(task)
            return Response(serializer.data)
        if project_id:
            tasks = queryset.filter(project_id=project_id)
            serializer = self.serializer_class(tasks, many=True)
            return Response(serializer.data)
        return Response([])

    def post(self, request, project_id=None):
        """
        Handle POST requests to create a new task within a project.

        Args:
            request (Request): The HTTP request containing task data.
            project_id (int): ID of the project where the task will be created.

        Returns:
            Response: Serialized task data if created successfully,
                      or validation errors otherwise.
        """
        project = generics.get_object_or_404(Project, pk=project_id, owner=request.user)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Handle PATCH requests to update an existing task.

        Args:
            request (Request): The HTTP request containing partial task data.
            pk (int): Primary key of the task to update.

        Returns:
            Response: Updated task data or validation errors.
        """
        task = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Handle DELETE requests to remove a task.

        Args:
            request (Request): The HTTP request object.
            pk (int): Primary key of the task to delete.

        Returns:
            Response: 204 No Content if deletion succeeds.
        """
        task = generics.get_object_or_404(self.get_queryset(), pk=pk)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimeEntryListCreateAPIView(generics.GenericAPIView):
    """
    API endpoint for listing and creating time entries within a task.

    Authenticated users can:
    - List all time entries for a given task they own (GET).
    - Create a new time entry for a given task (POST).
    """
    serializer_class = TimeEntrySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit the queryset to time entries belonging to tasks
        within projects owned by the authenticated user.

        Returns:
            QuerySet: Time entries owned by the current user.
        """
        return TimeEntry.objects.filter(task__project__owner=self.request.user)

    def get(self, request, task_id):
        """
        Handle GET requests to list all time entries for a task.

        Args:
            request (Request): The HTTP request object.
            task_id (int): ID of the task for which to retrieve time entries.

        Returns:
            Response: JSON object containing:
                - entries (list): Serialized time entry data.
                - total_hours (float): Sum of all hours tracked for the task.
        """
        queryset = self.get_queryset().filter(task_id=task_id)
        serializer = self.serializer_class(queryset, many=True)
        total_hours = queryset.aggregate(Sum('hours'))['hours__sum'] or Decimal('0.00')
        return Response({'entries': serializer.data, 'total_hours': float(total_hours)})

    def post(self, request, task_id):
        """
        Handle POST requests to create a new time entry for a task.

        Args:
            request (Request): The HTTP request containing time entry data.
            task_id (int): ID of the task where the entry will be created.

        Returns:
            Response: Serialized time entry data if created successfully,
                      or validation errors otherwise.
        """
        task = generics.get_object_or_404(Task, pk=task_id, project__owner=request.user)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimeEntryDetailAPIView(generics.GenericAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific time entry.

    Authenticated users can:
    - Retrieve a single time entry (GET).
    - Update a time entry partially (PATCH).
    - Delete a time entry (DELETE).
    """
    serializer_class = TimeEntrySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Limit the queryset to time entries belonging to tasks
        within projects owned by the authenticated user.

        Returns:
            QuerySet: Time entries owned by the current user.
        """
        return TimeEntry.objects.filter(task__project__owner=self.request.user)

    def get(self, request, pk):
        """
        Handle GET requests to retrieve a specific time entry.

        Args:
            request (Request): The HTTP request object.
            pk (int): Primary key of the time entry to retrieve.

        Returns:
            Response: Serialized time entry data.
        """
        entry = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(entry)
        return Response(serializer.data)

    def patch(self, request, pk):
        """
        Handle PATCH requests to update a specific time entry.

        Args:
            request (Request): The HTTP request containing updated fields.
            pk (int): Primary key of the time entry to update.

        Returns:
            Response: Updated serialized time entry data,
                      or validation errors if invalid.
        """
        entry = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.serializer_class(entry, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Handle DELETE requests to remove a specific time entry.

        Args:
            request (Request): The HTTP request object.
            pk (int): Primary key of the time entry to delete.

        Returns:
            Response: 204 No Content if deletion succeeds.
        """
        entry = generics.get_object_or_404(self.get_queryset(), pk=pk)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        