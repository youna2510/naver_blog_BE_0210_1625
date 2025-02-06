from rest_framework import serializers
from main.models.post import Post
from main.models.comment import Comment

class ActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()  # "liked_post", "written_comment", "written_reply", "liked_comment"
    content = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()

    def to_representation(self, instance):
        if isinstance(instance, Post):
            return {
                "id": instance.id,
                "type": "liked_post",  # 좋아요를 누른 게시글
                "content": instance.title,  # 게시글 제목을 "content"로 사용
                "created_at": instance.hearts.first().created_at if instance.hearts.exists() else instance.updated_at
            }
        elif isinstance(instance, Comment):
            if instance.is_parent:
                return {
                    "id": instance.id,
                    "type": "written_comment",  # 내가 작성한 댓글
                    "content": instance.content,
                    "created_at": instance.created_at
                }
            else:
                return {
                    "id": instance.id,
                    "type": "written_reply",  # 내가 작성한 대댓글
                    "content": instance.content,
                    "created_at": instance.created_at
                }
        # 내가 좋아요 누른 댓글에 대한 직렬화
        elif isinstance(instance, Comment):
            if instance.hearts.filter(user=self.context['request'].user).exists():
                return {
                    "id": instance.id,
                    "type": "liked_comment",  # 내가 좋아요를 누른 댓글
                    "content": instance.content,
                    "created_at": instance.hearts.first().created_at if instance.hearts.exists() else instance.updated_at
                }

        return super().to_representation(instance)
