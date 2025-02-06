from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from main.models.post import Post
from main.models.comment import Comment
from main.serializers.activity import ActivitySerializer

class MyActivityView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer

    @swagger_auto_schema(
        operation_summary="내 활동 조회",
        operation_description="내가 좋아요 누른 게시물, 댓글, 대댓글을 최신순으로 조회",
        responses={200: ActivitySerializer(many=True)}
    )
    def get_queryset(self):
        user = self.request.user
        user_profile = user.profile

        # 내가 좋아요 누른 게시물 (CustomUser 기준)
        liked_posts = Post.objects.filter(
            hearts__user=user
        ).select_related('author').prefetch_related('hearts') \
                          .distinct().order_by('-hearts__created_at')[:5]

        # 내가 작성한 댓글/대댓글 (Profile 기준)
        my_comments = Comment.objects.filter(
            author=user_profile
        ).select_related('author').distinct().order_by('-created_at')[:5]

        # 내가 좋아요 누른 댓글/대댓글
        liked_comments = Comment.objects.filter(
            hearts__user=user
        ).select_related('author').prefetch_related('hearts') \
                          .distinct().order_by('-hearts__created_at')[:5]

        # 최신순 정렬
        combined_activity = sorted(
            list(liked_posts) + list(my_comments) + list(liked_comments),
            key=lambda obj: max(obj.created_at, obj.updated_at),
            reverse=True
        )[:5]

        return combined_activity
