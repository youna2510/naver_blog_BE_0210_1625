from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from main.models.comment import Comment
from main.models.commentHeart import CommentHeart
from main.serializers.commentHeart import CommentHeartSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ToggleCommentHeartView(generics.GenericAPIView):
    """ ✅ 댓글/대댓글 좋아요(하트) 추가/삭제 (토글 기능) """
    serializer_class = CommentHeartSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="댓글/대댓글 좋아요(하트) 추가/삭제",
        operation_description="특정 댓글 또는 대댓글의 좋아요(하트)를 추가하거나 취소합니다.",
        responses={
            200: openapi.Response(description="좋아요 취소됨", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING, description="응답 메시지"),
                    "like_count": openapi.Schema(type=openapi.TYPE_INTEGER, description="현재 좋아요 개수")
                }
            )),
            201: openapi.Response(description="좋아요 추가됨", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING, description="응답 메시지"),
                    "like_count": openapi.Schema(type=openapi.TYPE_INTEGER, description="현재 좋아요 개수")
                }
            )),
        }
    )
    def post(self, request, post_id, comment_id, *args, **kwargs):  # ✅ post_id 추가!
        comment = get_object_or_404(
            Comment.objects.select_related("post", "post__author", "post__author__profile"),
            id=comment_id, post_id=post_id  # ✅ post_id도 필터링에 추가!
        )
        user = request.user

        # ✅ '나만 보기' 게시글의 댓글이면 좋아요 불가능
        if comment.post.visibility == 'me':
            return Response({"error": "이 게시글의 댓글에는 좋아요를 누를 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 댓글 좋아요 가능
        if comment.post.visibility == 'mutual' and not comment.post.author.profile.neighbors.filter(id=user.profile.id).exists():
            return Response({"error": "서로 이웃만 이 게시글의 댓글에 좋아요를 누를 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ 비밀 댓글/대댓글은 좋아요 기능 없음
        if comment.is_private:
            return Response({"error": "비밀 댓글에는 좋아요 기능이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ 현재 유저가 이미 좋아요를 눌렀는지 확인
        heart, created = CommentHeart.objects.get_or_create(comment=comment, user=user)

        if not created:
            # ✅ 이미 좋아요를 눌렀다면 취소 (삭제)
            heart.delete()

        # ✅ 최신 좋아요 개수 동기화
        like_count = CommentHeart.objects.filter(comment=comment).count()

        return Response({
            "message": "좋아요 추가됨" if created else "좋아요 취소됨",
            "like_count": like_count
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)



class CommentHeartCountView(generics.RetrieveAPIView):
    """ ✅ 댓글/대댓글의 좋아요(하트) 개수 조회 """
    serializer_class = CommentHeartSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="댓글/대댓글 좋아요(하트) 개수 조회",
        operation_description="특정 댓글 또는 대댓글의 좋아요(하트) 개수를 반환합니다.",
        responses={
            200: openapi.Response(description="좋아요 개수 반환", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "like_count": openapi.Schema(type=openapi.TYPE_INTEGER, description="현재 좋아요 개수")
                }
            )),
            403: openapi.Response(description="조회 권한이 없습니다."),
        }
    )
    def get(self, request, post_id, comment_id, *args, **kwargs):
        comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
        user = request.user

        # ✅ 비로그인 사용자는 좋아요 개수 조회 불가
        if not user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ '나만 보기' 게시글이면 게시글 작성자 본인만 조회 가능
        if comment.post.visibility == 'me' and comment.post.author != user:
            return Response({"error": "이 게시글의 댓글 좋아요 개수를 조회할 수 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 좋아요 개수 조회 가능
        if comment.post.visibility == 'mutual' and not comment.post.author.profile.neighbors.filter(id=user.profile.id).exists():
            return Response({"error": "서로 이웃만 이 게시글의 댓글 좋아요 개수를 조회할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ 최신 좋아요 개수 동기화
        like_count = CommentHeart.objects.filter(comment=comment).count()

        return Response({"like_count": like_count}, status=status.HTTP_200_OK)


