from django.conf import settings
from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    team = models.ForeignKey("teams.Team", on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="projects", blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True) | models.Q(start_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")),
                name="project_end_date_after_start_date",
            )
        ]

    def __str__(self):
        return self.name
