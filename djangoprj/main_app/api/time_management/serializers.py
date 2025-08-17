import re
from rest_framework import serializers
from decimal import Decimal
from main_app.api.time_management import models


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model.

    Exposes project fields such as id, name, description, and owner.
    The owner field is read-only and automatically set.
    """
    class Meta:
        model = models.Project
        fields = ['id', 'name', 'description', 'owner']
        read_only_fields = ['owner']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for the Task model.

    Exposes task fields such as id, name, and description.
    The project field is read-only, as tasks are created within a project context.
    """
    class Meta:
        model = models.Task
        fields = ['id', 'name', 'description']
        read_only_fields = ['project']


class TimeEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for the TimeEntry model.

    Includes a custom 'duration' field for user input (e.g., "1h 30m"),
    which is converted into decimal hours and stored in the 'hours' field.
    """
    duration = serializers.CharField(write_only=True)

    class Meta:
        model = models.TimeEntry
        fields = ['id', 'task', 'user', 'comment', 'date', 'hours', 'duration']
        read_only_fields = ['hours', 'task', 'user']

    def validate_duration(self, value):
        """
        Validate and parse the duration string.

        Args:
            value (str): The duration string (e.g., "1h 30m", "2h", "45m").

        Raises:
            serializers.ValidationError: If the format is invalid or minutes exceed 59.

        Returns:
            Decimal: The duration converted to decimal hours.
        """
        value = value.strip().lower()
        
        hours = 0
        minutes = 0

        # Match hours (e.g., "12h")
        hour_match = re.search(r'(\d+)\s*h', value)
        if hour_match:
            hours = int(hour_match.group(1))

        minute_match = re.search(r'(\d+)\s*m', value)
        if minute_match:
            minutes = int(minute_match.group(1))

        if not hour_match and not minute_match:
            raise serializers.ValidationError(
                "Invalid format. Use 'h' for hours and 'm' for minutes (e.g., '1h 30m', '1h', or '30m')."
            )
        
        if minutes >= 60:
            raise serializers.ValidationError("Minutes must be less than 60.")

        return Decimal(hours) + (Decimal(minutes) / 60)

    def create(self, validated_data):
        """
        Create a TimeEntry instance after converting duration to hours.

        Args:
            validated_data (dict): Validated serializer data.

        Returns:
            TimeEntry: The created TimeEntry instance.
        """
        validated_data['hours'] = validated_data.pop('duration')
        return super().create(validated_data)


    def create(self, validated_data):
        validated_data['hours'] = validated_data.pop('duration')
        return super().create(validated_data)


class ProjectSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for project summaries.

    Adds a computed field `total_hours` representing the sum of all time entries
    for a given project.
    """
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = models.Project
        fields = ['id', 'name', 'total_hours']