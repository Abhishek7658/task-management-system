from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from accounts.permissions import IsAdministratorOrManager
from activity.models import Activity
from activity.serializers import CommentSerializer
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filterset_fields = ("status", "priority", "project", "assignee", "due_date")
    search_fields = ("title", "description")
    ordering_fields = ("due_date", "priority", "status", "created_at")

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related("project", "assignee", "created_by")
        if user.role == "admin":
            return qs
        if user.role == "manager":
            return qs.filter(
                Q(project__created_by=user) | Q(project__members=user) | Q(project__team__members=user)
            ).distinct()
        return qs.filter(assignee=user)

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdministratorOrManager()]
        return super().get_permissions()

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if self.request.user.role != "admin" and project.created_by_id != self.request.user.id:
            raise PermissionDenied("You can create tasks only in projects you manage.")
        task = serializer.save(created_by=self.request.user)
        Activity.objects.create(task=task, actor=self.request.user, action="created", description=f"Created task: {task.title}")

    def perform_update(self, serializer):
        task = serializer.instance
        user = self.request.user
        if user.role == "member":
            allowed = {"status"}
            if set(self.request.data.keys()) - allowed:
                raise PermissionDenied("Members can only update the status of their assigned tasks.")
            if task.assignee_id != user.id:
                raise PermissionDenied("You can only update tasks assigned to you.")
        old_status = task.status
        updated = serializer.save()
        if old_status != updated.status:
            Activity.objects.create(task=updated, actor=user, action="status_changed", description=f"Status changed from {old_status} to {updated.status}")

    def perform_destroy(self, instance):
        if self.request.user.role != "admin" and instance.project.created_by_id != self.request.user.id:
            raise PermissionDenied("You can only delete tasks in projects you manage.")
        instance.delete()

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        from activity.models import Activity
        from activity.serializers import ActivitySerializer
        task = self.get_object()
        entries = Activity.objects.filter(task=task).select_related("actor")
        return Response(ActivitySerializer(entries, many=True).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            from activity.models import Comment
            comments = Comment.objects.filter(task=task).select_related("author")
            return Response(CommentSerializer(comments, many=True).data)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        Activity.objects.create(task=task, actor=request.user, action="commented", description="Added a task comment")
        return Response(CommentSerializer(comment).data, status=201)
