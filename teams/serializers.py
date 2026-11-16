
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Team

User = get_user_model()


class TeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(is_active=True),
        required=False
    )
    member_details = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = (
            "id", "name", "description", "created_by",
            "members", "member_details", "created_at", "updated_at"
        )
        read_only_fields = (
            "id", "created_by", "created_at",
            "updated_at", "member_details"
        )

    def validate_members(self, value):
        for user in value:
            if user.role != "member":
                raise serializers.ValidationError(
                    "Only users with the member role can be assigned to teams."
                )
        return value

    def get_member_details(self, obj):
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email
            }
            for u in obj.members.all()
        ]
