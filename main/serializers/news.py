from rest_framework import serializers
from main.models.post import Post
from main.models.comment import Comment

class NewsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()  # "post_comment", "post_like", "comment_reply", "liked_comment", "liked_reply"
    content = serializers.CharField(source='content', read_only=True)
    created_at = serializers.DateTimeField()

    def to_representation(self, instance):
        if isinstance(instance, Post):
            if instance.comments.exists():
                return {
                    "id": instance.id,
                    "type": "post_comment",  # 댓글이 달린 경우
                    "content": instance.comments.first().content,  # 첫 번째 댓글 내용
                    "created_at": instance.updated_at  # 최신 댓글의 업데이트 시간
                }
            elif instance.hearts.exists():
                return {
                    "id": instance.id,
                    "type": "post_like",  # 좋아요가 달린 경우
                    "content": "좋아요",  # 좋아요는 '좋아요' 텍스트로 표시
                    "created_at": instance.updated_at
                }
        elif isinstance(instance, Comment):
            if instance.is_parent:
                # 댓글에 달린 좋아요가 있는 경우 처리
                if instance.hearts.exists():
                    return {
                        "id": instance.id,
                        "type": "liked_comment",  # 댓글에 달린 좋아요
                        "content": instance.content,
                        "created_at": instance.hearts.first().created_at if instance.hearts.exists() else instance.updated_at
                    }
                return {
                    "id": instance.id,
                    "type": "comment",  # 댓글
                    "content": instance.content,  # 댓글 내용
                    "created_at": instance.updated_at  # 댓글의 최신 업데이트 시간
                }
            else:
                # 대댓글에 달린 좋아요가 있는 경우 처리
                if instance.hearts.exists():
                    return {
                        "id": instance.id,
                        "type": "liked_reply",  # 대댓글에 달린 좋아요
                        "content": instance.content,
                        "created_at": instance.hearts.first().created_at if instance.hearts.exists() else instance.updated_at
                    }
                return {
                    "id": instance.id,
                    "type": "comment_reply",  # 대댓글
                    "content": instance.content,  # 대댓글 내용
                    "created_at": instance.updated_at  # 대댓글의 최신 업데이트 시간
                }

        return super().to_representation(instance)




