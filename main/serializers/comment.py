from rest_framework import serializers
from main.models.comment import Comment

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    is_post_author = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'author_name', 'content', 'is_private', 'is_parent', 'is_post_author', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_parent', 'is_post_author', 'author_name']

    def get_author_name(self, obj):
        if obj.author and hasattr(obj.author, 'username'):
            return obj.author.username
        return None

    def get_is_post_author(self, obj):
        return obj.author == obj.post.author.profile

    def to_representation(self, instance):
        user = self.context['request'].user
        data = super().to_representation(instance)

        is_authenticated = user.is_authenticated
        is_author = is_authenticated and user.profile == instance.author
        is_post_author = is_authenticated and user.profile == instance.post.author.profile
        is_parent_author = is_authenticated and instance.parent and user.profile == instance.parent.author

        # ✅ 비밀 댓글 필터링
        if instance.is_private and not (is_author or is_post_author or is_parent_author):
            data['content'] = "비밀 댓글입니다."

        if instance.is_parent:
            replies = Comment.objects.filter(parent=instance)
            serialized_replies = CommentSerializer(replies, many=True, context=self.context).data
            for reply, reply_obj in zip(serialized_replies, replies):
                is_reply_author = is_authenticated and user.profile == reply_obj.author
                is_reply_post_author = is_authenticated and user.profile == reply_obj.post.author.profile
                is_reply_parent_author = is_authenticated and user.profile == instance.author
                if reply_obj.is_private and not (is_reply_author or is_reply_post_author or is_reply_parent_author):
                    reply['content'] = "비밀 댓글입니다."
            data['replies'] = serialized_replies

        return data