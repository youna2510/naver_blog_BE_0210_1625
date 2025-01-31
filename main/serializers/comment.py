from rest_framework import serializers
from main.models.comment import Comment

class CommentSerializer(serializers.ModelSerializer):
    is_parent = serializers.BooleanField(read_only=True)
    is_post_author = serializers.SerializerMethodField()  # ✅ 게시글 작성자 여부 반환
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'author_name', 'content', 'is_private', 'is_parent', 'is_post_author', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_parent', 'is_post_author']

    def update(self, instance, validated_data):
        """ ✅ author_name도 업데이트 가능하도록 설정 """
        instance.author_name = validated_data.get('author_name', instance.author_name)
        instance.content = validated_data.get('content', instance.content)
        instance.is_private = validated_data.get('is_private', instance.is_private)
        instance.save()
        return instance

    def get_is_post_author(self, obj):
        """ ✅ 게시글 작성자 여부 확인 (Profile과 CustomUser 타입 일치) """
        return obj.author == obj.post.author.profile  # 🔥 Profile 비교

    def to_representation(self, instance):
        """ ✅ 비밀 댓글 및 '나만 보기' 게시글 댓글 필터링 적용 """
        user = self.context['request'].user
        data = super().to_representation(instance)

        # ✅ 비로그인 사용자 처리 (AnonymousUser)
        is_authenticated = user.is_authenticated  # 로그인 여부 확인

        # ✅ '나만 보기' 게시글의 댓글은 작성자 본인만 볼 수 있도록 처리
        if instance.post.visibility == 'me' and (not is_authenticated or instance.post.author != user):
            return None  # 게시글 작성자가 아니면 댓글 숨김

        # ✅ 비밀 댓글 필터링 (비로그인 사용자는 무조건 숨김)
        if instance.is_private:
            if not is_authenticated:  # 🔥 비로그인 사용자는 비밀 댓글 볼 수 없음
                return None
            if hasattr(user, "profile"):  # ✅ `profile` 속성 확인 후 참조
                if user.profile not in [instance.author, instance.post.author]:
                    return None  # 🔥 작성자가 아니면 댓글 숨김

        # ✅ 대댓글 (replies) 필터링 적용
        if instance.is_parent:
            replies = CommentSerializer(instance.replies.all(), many=True, context=self.context).data
            data['replies'] = [reply for reply in replies if reply is not None]  # None 값 필터링

        return data




