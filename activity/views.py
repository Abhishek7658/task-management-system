from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from projects.models import Project
from tasks.models import Task

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        projects = Project.objects.all()
        tasks = Task.objects.all()
        if user.role != "admin":
            if user.role == "manager":
                projects = projects.filter(
                    Q(created_by=user) | Q(members=user) | Q(team__members=user)
                ).distinct()
                tasks = tasks.filter(
                    Q(project__created_by=user) | Q(project__members=user) | Q(project__team__members=user)
                ).distinct()
            else:
                projects = projects.filter(Q(members=user) | Q(team__members=user)).distinct()
                tasks = tasks.filter(assignee=user)
        summary = tasks.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=Task.Status.TODO)),
            in_progress=Count("id", filter=Q(status=Task.Status.IN_PROGRESS)),
            completed=Count("id", filter=Q(status=Task.Status.COMPLETE)),
        )
        upcoming = tasks.filter(due_date__isnull=False).exclude(status=Task.Status.COMPLETE).order_by("due_date")[:5]
        return Response({
            "project_count": projects.count(),
            "tasks": summary,
            "upcoming_deadlines": [
                {"id": task.id, "title": task.title, "due_date": task.due_date, "project": task.project.name}
                for task in upcoming
            ],
        })
