from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from main.models.post import Post
from main.models.comment import Comment
from main.models.heart import Heart
from main.serializers.activity import ActivitySerializer
from django.db.models import Q
from django.shortcuts import redirect


class MyActivityListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return self.get_latest_unread_activity(self.request.user)  # ✅ self 사용 가능하도록 수정

    def list(self, request, *args, **kwargs):
        queryset = self.get_latest_unread_activity(request.user)  # ✅ index_map 제거
        serializer = self.get_serializer(queryset, many=True)  # ✅ context 제거
        return Response(serializer.data)

    @staticmethod
    def get_latest_unread_activity(user):
        profile = user.profile

        # ✅ 내가 좋아요 누른 게시글 (Heart에서 직접 필터링)
        liked_posts = list(Heart.objects.filter(user=user, is_read=False)
                           .select_related('post', 'user')
                           .order_by('-created_at'))

        # ✅ 내가 작성한 댓글 (Comment에서 Profile 기준으로 필터링)
        my_comments = list(Comment.objects.filter(
            author=profile, is_read=False, is_parent=True
        ).select_related('author').order_by('-created_at'))

        # ✅ 내가 작성한 대댓글 (Comment에서 Profile 기준으로 필터링)
        my_replies = list(Comment.objects.filter(
            author=profile, is_read=False, is_parent=False
        ).select_related('author').order_by('-created_at'))

        # ✅ 최신순 정렬 후 최대 5개 반환
        combined_activity = sorted(
            liked_posts + my_comments + my_replies,
            key=lambda obj: obj.created_at,
            reverse=True
        )[:5]

        return combined_activity

