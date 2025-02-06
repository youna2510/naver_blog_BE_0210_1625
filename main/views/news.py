from django.db.models import Q, Prefetch
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from main.models.post import Post
from main.models.comment import Comment
from main.serializers.news import NewsSerializer
from rest_framework import generics

class MyNewsView(ListAPIView):
    """
    내 소식 API (내 게시글에 달린 댓글, 좋아요 / 내 댓글에 달린 대댓글)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NewsSerializer

    @swagger_auto_schema(
        operation_summary="내 소식 조회",
        operation_description="내 게시물에 달린 댓글, 좋아요 및 내 댓글에 달린 대댓글을 최신순으로 조회",
        responses={200: NewsSerializer(many=True)}
    )
    def get_queryset(self):
        user = self.request.user  # CustomUser 가져오기
        user_profile = user.profile  # Profile 가져오기

        # 내가 작성한 게시글에 달린 "댓글"이나 "좋아요" 받은 것
        post_news = Post.objects.filter(
            Q(author=user) & (Q(comments__isnull=False) | Q(hearts__isnull=False))
        ).select_related('author').prefetch_related('comments', 'hearts') \
                        .distinct().order_by('-updated_at', '-created_at')[:5]

        # 내가 작성한 댓글에 달린 "대댓글" 받은 것
        comment_news = Comment.objects.filter(
            Q(author=user_profile) & Q(replies__isnull=False)
        ).select_related('author').prefetch_related('replies') \
                           .distinct().order_by('-updated_at', '-created_at')[:5]

        # 최신순으로 두 개의 결과를 합침
        combined_news = sorted(
            list(post_news) + list(comment_news),
            key=lambda obj: max(obj.updated_at, obj.created_at),  # 최신 시간으로 정렬
            reverse=True
        )[:5]  # 최대 5개만 반환

        return combined_news




