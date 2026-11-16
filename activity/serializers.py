from rest_framework import serializers
from .models import Comment, Activity

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "author_name", "body", "created_at", "updated_at")
        read_only_fields = ("id", "task", "author", "author_name", "created_at", "updated_at")

class ActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Activity
        fields = ("id", "task", "actor", "actor_name", "action", "description", "created_at")
