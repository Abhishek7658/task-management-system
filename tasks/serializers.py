from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Task

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    assignee_details = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Task
        fields = ("id", "project", "project_name", "title", "description", "status", "priority", "due_date", "assignee", "assignee_details", "created_by", "created_at", "updated_at")
        read_only_fields = ("id", "created_by", "created_at", "updated_at", "assignee_details", "project_name")

    def validate_assignee(self, value):
        if value and value.role != User.Role.MEMBER:
            raise serializers.ValidationError("Tasks can only be assigned to team members.")
        return value

    def get_assignee_details(self, obj):
        if not obj.assignee:
            return None
        return {"id": obj.assignee_id, "username": obj.assignee.username, "email": obj.assignee.email}
