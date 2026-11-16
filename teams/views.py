
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdministratorOrManager
from .models import Team
from .serializers import TeamSerializer


User = get_user_model()


class MemberIdsSerializer(serializers.Serializer):
    member_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True
    )


class TeamMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.none()
    serializer_class = TeamSerializer
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Team.objects.none()

        user = self.request.user

        qs = Team.objects.select_related(
            "created_by"
        ).prefetch_related("members")

        if user.role == "admin":
            return qs

        if user.role == "manager":
            return qs.filter(created_by=user) | qs.filter(members=user)

        return qs.filter(members=user)

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
                "You can only modify teams you created."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if (
            self.request.user.role != "admin"
            and instance.created_by_id != self.request.user.id
        ):
            raise PermissionDenied(
                "You can only delete teams you created."
            )

        instance.delete()

    def validate_member_management(self, team, user):
        if user.role != "admin" and team.created_by_id != user.id:
            raise PermissionDenied(
                "Only the team creator or an administrator "
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

    # GET: List team members
    @extend_schema(
        responses=TeamMemberSerializer(many=True)
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="members"
    )
    def members(self, request, pk=None):
        team = self.get_object()

        data = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in team.members.all()
        ]

        return Response(data)

    # POST: Add members without removing existing members
    @extend_schema(
        request=MemberIdsSerializer,
        responses={200: TeamSerializer}
    )
    @members.mapping.post
    def add_members(self, request, pk=None):
        team = self.get_object()

        self.validate_member_management(team, request.user)

        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_ids = serializer.validated_data["member_ids"]
        members = self.get_valid_members(member_ids)

        team.members.add(*members)

        return Response(TeamSerializer(team).data)

    # DELETE: Remove only selected members
    @extend_schema(
        request=MemberIdsSerializer,
        responses={200: TeamSerializer}
    )
    @members.mapping.delete
    def remove_members(self, request, pk=None):
        team = self.get_object()

        self.validate_member_management(team, request.user)

        serializer = MemberIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_ids = serializer.validated_data["member_ids"]
        members = self.get_valid_members(member_ids)

        team.members.remove(*members)

        return Response(TeamSerializer(team).data)
