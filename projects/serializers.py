
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Project

User = get_user_model()


class ProjectSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(is_active=True),
        required=False
    )
    member_details = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id", "name", "description", "start_date", "end_date",
            "team", "members", "member_details", "created_by",
            "created_at", "updated_at"
        )
        read_only_fields = (
            "id", "created_by", "created_at",
            "updated_at", "member_details"
        )

    def validate_members(self, value):
        for user in value:
            if user.role != "member":
                raise serializers.ValidationError(
                    "Only users with the member role can be assigned to projects."
                )
        return value

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))

        if start and end and end < start:
            raise serializers.ValidationError({
                "end_date": "End date must be on or after the start date."
            })

        return attrs

    def get_member_details(self, obj):
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email
            }
            for u in obj.members.all()
        ]
