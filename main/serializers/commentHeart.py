from rest_framework import serializers
from main.models.commentHeart import CommentHeart

class CommentHeartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentHeart
        fields = ['id', 'user', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'comment', 'created_at']
