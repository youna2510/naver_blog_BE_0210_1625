from rest_framework import serializers
from main.models.post import Post
from main.models.comment import Comment
from main.models.heart import Heart  # ✅ 게시글 좋아요 추가

class ActivitySerializer(serializers.Serializer):
    activity_id = serializers.SerializerMethodField()  # ✅ 고유한 activity_id 생성
    type = serializers.CharField()
    content = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    is_read = serializers.BooleanField(default=False)
    is_parent = serializers.SerializerMethodField()  # ✅ 댓글/대댓글 여부 추가

    def get_activity_id(self, obj):
        """ ✅ 각 객체에 대해 고유한 activity_id 부여 """
        if isinstance(obj, Heart):
            return f"heart_{obj.id}"  # ✅ 좋아요는 그대로 유지
        elif isinstance(obj, Comment):
            return f"comment_{obj.id}"  # ✅ 댓글/대댓글 모두 `comment_xx`로 통일
        return f"unknown_{obj.id}"  # 예외 처리 (이론상 발생하면 안 됨)

    def get_is_parent(self, obj):
        """ ✅ 댓글인지 대댓글인지 여부 추가 """
        return obj.is_parent if isinstance(obj, Comment) else None  # ✅ `True`면 댓글, `False`면 대댓글, `None`이면 Heart

    def to_representation(self, instance):
        return {
            "activity_id": self.get_activity_id(instance),  # ✅ 고유 ID (순서 기반)
            "type": "liked_post" if isinstance(instance, Heart) else
            ("written_comment" if instance.is_parent else "written_reply"),
            "content": f"'{instance.post.title}'을(를) 좋아합니다." if isinstance(instance, Heart) else instance.content,
            "created_at": instance.created_at,
            "is_read": instance.is_read,
            "is_parent": instance.is_parent if isinstance(instance, Comment) else None  # ✅ 댓글/대댓글 여부 추가
        }



