
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministratorOrManager
from .models import Project
from .serializers import ProjectSerializer


User = get_user_model()


class MemberIdsSerializer(serializers.Serializer):
    member_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True
    )


class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.none()
    serializer_class = ProjectSerializer
    search_fields = ("name", "description")
    ordering_fields = ("name", "start_date", "end_date", "created_at")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()

        user = self.request.user

        qs = Project.objects.select_related(
            "team", "created_by"
        ).prefetch_related("members")

        if user.role == "admin":
            return qs

        if user.role == "manager":
            return (
                qs.filter(created_by=user)
                | qs.filter(members=user)
                | qs.filter(team__members=user)
            )

        return qs.filter(members=user) | qs.filter(team__members=user)

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "add_members",
            "remove_members"
        ):
            return [IsAdministratorOrManager()]

        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        if (
            self.request.user.role != "admin"
            and serializer.instance.created_by_id != self.request.user.id
        ):
            raise PermissionDenied(
                "You can only modify projects you created."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if (
            self.request.user.role != "admin"
            and instance.created_by_id != self.request.user.id
        ):
            raise PermissionDenied(
                "You can only delete projects you created."
            )

        instance.delete()

    def validate_member_management(self, project, user):
        if user.role != "admin" and project.created_by_id != user.id:
            raise PermissionDenied(
                "Only the project creator or an administrator "
                "can manage members."
            )

    def get_valid_members(self, member_ids):
        if len(member_ids) != len(set(member_ids)):
            raise ValidationError({
                "member_ids": "Duplicate user IDs are not allowed."
            })

        members = User.objects.filter(
            id__in=member_ids,
            is_active=True,
            role="member"
        )

        if members.count() != len(member_ids):
            raise ValidationError({
                "member_ids": (
                    "One or more users are invalid or are not members."
                )
            })

        return members

    # GET: List project members
    @extend_schema(
        responses=ProjectMemberSerializer(many=True)
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="members"
    )
    def members(self, request, pk=None):
        project = self.get_object()

        data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in project.members.all()
        ]

        return Response(data)

    # POST: Add members without removing existing members
    @extend_schema(
        request=MemberIdsSerializer,
        responses={200: ProjectSerializer}
    )
    @members.mapping.post
    def add_members(self, request, pk=None):
        project = self.get_object()

        self.validate_member_management(project, request.user)

        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_ids = serializer.validated_data["member_ids"]
        members = self.get_valid_members(member_ids)

        project.members.add(*members)

        return Response(ProjectSerializer(project).data)

    # DELETE: Remove only selected members
    @extend_schema(
        request=MemberIdsSerializer,
        responses={200: ProjectSerializer}
    )
    @members.mapping.delete
    def remove_members(self, request, pk=None):
        project = self.get_object()

        self.validate_member_management(project, request.user)

        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_ids = serializer.validated_data["member_ids"]
        members = self.get_valid_members(member_ids)

        project.members.remove(*members)

        return Response(ProjectSerializer(project).data)
