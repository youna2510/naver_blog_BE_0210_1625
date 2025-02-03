import re
from rest_framework import generics
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from main.models.comment import Comment
from main.models.post import Post
from main.serializers.comment import CommentSerializer
from main.models.profile import Profile  # ✅ Profile 모델 임포트
from django.contrib.auth import get_user_model

User = get_user_model()  # Django 기본 User 모델 가져오기

class CommentListView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="댓글 목록 조회",
        operation_description="게시글의 댓글 및 대댓글을 조회합니다. 비밀 댓글은 작성자 또는 게시글 작성자만 볼 수 있습니다.",
        responses={200: openapi.Response(description="조회 성공", schema=CommentSerializer(many=True))}
    )
    def get(self, request, *args, **kwargs):
        self.queryset = self.get_queryset()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        ✅ 특정 댓글 조회 (비밀 댓글 및 'mutual' 게시글 제한)
        """
        if getattr(self, 'swagger_fake_view', False):  # ✅ Swagger 문서 생성 중이라면 예외 방지
            return Comment.objects.none()

        post_id = self.kwargs.get('post_id')
        user = self.request.user
        post = get_object_or_404(Post, id=post_id)

        # ✅ '나만 보기' 게시글이면 작성자 본인만 조회 가능
        if post.visibility == 'me' and (not user.is_authenticated or post.author.profile != user.profile):
            return Comment.objects.none()

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 댓글 조회 가능
        if post.visibility == 'mutual' and (
                not user.is_authenticated or not post.author.profile.is_mutual(user.profile)):
            return Comment.objects.none()

        return Comment.objects.filter(post_id=post_id)

    @swagger_auto_schema(
        operation_summary="댓글 작성",
        operation_description="게시글에 댓글 또는 대댓글을 작성합니다. 서로 이웃만 댓글을 작성할 수 있습니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='댓글 내용'),
                'is_private': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='비밀 댓글 여부', default=False),
                'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='부모 댓글 ID (대댓글인 경우)', nullable=True),
            },
            required=['content']
        ),
        responses={
            201: openapi.Response(description="작성 성공", schema=CommentSerializer()),
            403: openapi.Response(description="서로 이웃만 댓글을 작성할 수 있습니다."),
            400: openapi.Response(description="잘못된 요청입니다."),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        ✅ 댓글 및 대댓글 저장 로직
        - `mutual` 게시글의 경우 서로 이웃만 댓글 작성 가능
        - `me` 게시글의 경우 작성자 본인만 댓글 작성 가능
        """
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = self.request.user

        parent_id = self.request.data.get('parent')
        is_private = self.request.data.get('is_private', False)

        # ✅ '나만 보기' 게시글이면 작성자 본인만 댓글 가능
        if post.visibility == 'me' and post.author.profile != user.profile:
            raise ValidationError("이 게시글에는 작성자 본인만 댓글을 작성할 수 있습니다.")

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 댓글 가능 (is_mutual() 대신 neighbors 필드 직접 사용)
        if post.visibility == 'mutual' and not post.author.profile.neighbors.filter(id=user.profile.id).exists():
            raise ValidationError("서로 이웃만 이 게시글에 댓글을 작성할 수 있습니다.")

        is_post_author = user.profile == post.author.profile

        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)

            # ✅ 부모 댓글도 `mutual` 제한을 따름
            if parent_comment.post.visibility == 'mutual' and not parent_comment.post.author.profile.neighbors.filter(
                    id=user.profile.id).exists():
                raise ValidationError("서로 이웃만 이 게시글에 대댓글을 작성할 수 있습니다.")

            serializer.save(
                post=post,
                author=user.profile,
                author_name=user.profile.username,
                parent=parent_comment,
                is_parent=False,
                is_post_author=is_post_author,
                is_private=is_private
            )
        else:
            serializer.save(
                post=post,
                author=user.profile,
                author_name=user.profile.username,
                is_parent=True,
                is_post_author=is_post_author,
                is_private=is_private
            )
class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="댓글 상세 조회",
        operation_description="특정 댓글을 조회합니다. 비밀 댓글은 작성자 또는 게시글 작성자만 볼 수 있습니다.",
        responses={
            200: openapi.Response(description="조회 성공", schema=CommentSerializer()),
            403: openapi.Response(description="조회 권한이 없습니다."),
            404: openapi.Response(description="댓글을 찾을 수 없습니다."),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        ✅ 특정 댓글 조회 (비밀 댓글 및 'mutual' 게시글 제한)
        """
        post_id = self.kwargs.get('post_id')

        # ✅ Swagger 요청이면 빈 QuerySet 반환
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()

        try:
            post = get_object_or_404(Post, id=post_id)
        except Http404:
            return Comment.objects.none()

        # ✅ '나만 보기' 게시글이면 작성자 본인만 조회 가능
        if post.visibility == 'me' and (not user.is_authenticated or post.author.profile != user.profile):
            return Comment.objects.none()

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 댓글 조회 가능
        if post.visibility == 'mutual' and not post.author.profile.neighbors.filter(id=user.profile.id).exists():
            return Comment.objects.none()

        return Comment.objects.filter(post_id=post_id)

    @swagger_auto_schema(
        operation_summary="댓글 수정 (PATCH)",
        operation_description="특정 댓글을 수정합니다. (작성자만 가능)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'content': openapi.Schema(type=openapi.TYPE_STRING, description='수정할 댓글 내용')},
            required=['content']
        ),
        responses={
            200: openapi.Response(description="수정 성공", schema=CommentSerializer()),
            403: openapi.Response(description="수정 권한이 없습니다."),
            404: openapi.Response(description="댓글을 찾을 수 없습니다."),
        }
    )
    def patch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=self.kwargs['pk'], post_id=self.kwargs['post_id'])

        # ✅ '나만 보기' 게시글이면 본인만 수정 가능
        if comment.post.visibility == 'me' and comment.post.author.profile != request.user.profile:
            return Response({"error": "이 게시글의 댓글을 수정할 권한이 없습니다."}, status=403)

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 수정 가능
        if comment.post.visibility == 'mutual' and not comment.post.author.profile.neighbors.filter(id=request.user.profile.id).exists():
            return Response({"error": "서로 이웃만 이 게시글의 댓글을 수정할 수 있습니다."}, status=403)

        if request.user.profile != comment.author:
            return Response({"error": "수정할 권한이 없습니다."}, status=403)

        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="댓글 삭제",
        operation_description="특정 댓글을 삭제합니다. (댓글 작성자 또는 게시글 작성자만 가능)",
        responses={
            204: openapi.Response(description="댓글 삭제 성공"),
            403: openapi.Response(description="삭제 권한이 없습니다."),
            404: openapi.Response(description="댓글을 찾을 수 없습니다."),
        }
    )
    def delete(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=self.kwargs['pk'], post_id=self.kwargs['post_id'])
        user_profile = self.request.user.profile

        # ✅ '나만 보기' 게시글이면 본인만 삭제 가능
        if comment.post.visibility == 'me' and comment.post.author.profile != user_profile:
            return Response({"error": "이 게시글의 댓글을 삭제할 권한이 없습니다."}, status=403)

        # ✅ '서로 이웃 공개' 게시글이면 서로 이웃만 삭제 가능
        if comment.post.visibility == 'mutual' and not comment.post.author.profile.neighbors.filter(id=user_profile.id).exists():
            return Response({"error": "서로 이웃만 이 게시글의 댓글을 삭제할 수 있습니다."}, status=403)

        # ✅ 댓글 작성자 또는 게시글 작성자만 삭제 가능
        if user_profile != comment.author and user_profile != comment.post.author.profile:
            return Response({"error": "삭제할 권한이 없습니다."}, status=403)

        if comment.is_parent:
            # ✅ 부모 댓글이면 "삭제된 댓글입니다."로 변경 (대댓글은 그대로 남김)
            comment.content = "삭제된 댓글입니다."
            comment.is_private = False  # ✅ 삭제된 댓글은 비공개 처리 해제
            comment.save()
        else:
            # ✅ 대댓글이면 완전히 삭제
            comment.delete()

        return Response({"message": "댓글이 삭제되었습니다."}, status=204)
