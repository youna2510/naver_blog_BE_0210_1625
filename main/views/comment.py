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
        post_id = self.kwargs.get('post_id')
        user = self.request.user
        is_authenticated = user.is_authenticated
        post = get_object_or_404(Post, id=post_id)

        if post.visibility == 'me' and (not is_authenticated or post.author.profile != user.profile):
            return Comment.objects.none()

        queryset = Comment.objects.filter(post_id=post_id, is_parent=True)
        if not is_authenticated:
            return queryset  # ✅ 비밀 댓글도 포함한 상태로 반환

        return queryset  # ✅ 비밀 댓글을 제외하지 않고 전체 반환 후 직렬화 단계에서 필터링

    @swagger_auto_schema(
        operation_summary="댓글 작성",
        operation_description="게시글에 댓글 또는 대댓글을 작성합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='댓글 내용'),
                'is_private': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='비밀 댓글 여부', default=False),
                'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='부모 댓글 ID (대댓글인 경우)', nullable=True),
            },
            required=['content']
        ),
        responses={201: openapi.Response(description="작성 성공", schema=CommentSerializer())}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        user = self.request.user

        parent_id = self.request.data.get('parent')
        content = self.request.data.get('content')
        is_private = self.request.data.get('is_private', False)

        if post.visibility == 'me' and post.author.profile != user.profile:
            raise ValidationError("이 게시글에는 작성자 본인만 댓글을 작성할 수 있습니다.")

        is_post_author = user.profile == post.author.profile

        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)
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
    """
    특정 게시글의 댓글 상세 조회, 수정 및 삭제
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="댓글 상세 조회",
        operation_description="특정 댓글을 조회합니다. 비밀 댓글은 작성자 또는 게시글 작성자만 볼 수 있습니다.",
        responses={200: openapi.Response(description="조회 성공", schema=CommentSerializer())}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """ 특정 댓글 조회 (비밀 댓글 및 '나만 보기' 게시글 필터링) """
        post_id = self.kwargs.get('post_id')
        user = self.request.user
        post = get_object_or_404(Post, id=post_id)

        if post.visibility == 'me' and (not user.is_authenticated or post.author.profile != user.profile):
            return Comment.objects.none()

        queryset = Comment.objects.filter(post_id=post_id)
        return queryset

    @swagger_auto_schema(
        operation_summary="댓글 수정 (PATCH)",
        operation_description="특정 댓글을 수정합니다. (작성자만 가능)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'content': openapi.Schema(type=openapi.TYPE_STRING, description='수정할 댓글 내용')},
            required=['content']
        ),
        responses={200: openapi.Response(description="수정 성공", schema=CommentSerializer())}
    )
    def patch(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=self.kwargs['pk'], post_id=self.kwargs['post_id'])

        if comment.post.visibility == 'me' and comment.post.author != request.user:
            return Response({"error": "이 게시글의 댓글을 수정할 권한이 없습니다."}, status=403)

        if request.user.profile != comment.author:
            return Response({"error": "수정할 권한이 없습니다."}, status=403)

        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="PUT 요청 금지",
        operation_description="PUT 메서드는 허용되지 않습니다. 대신 PATCH를 사용하세요.",
        responses={405: openapi.Response(description="PUT method is not allowed. Use PATCH instead.")},
    )
    def put(self, request, *args, **kwargs):
        return Response({"error": "PUT method is not allowed. Use PATCH instead."}, status=405)

    @swagger_auto_schema(
        operation_summary="댓글 삭제",
        operation_description="특정 댓글을 삭제합니다. (댓글 작성자 또는 게시글 작성자만 가능)",
        responses={
            204: openapi.Response(description="댓글 삭제 성공"),
            403: openapi.Response(description="삭제할 권한이 없습니다."),
            404: openapi.Response(description="댓글을 찾을 수 없습니다."),
        }
    )
    def delete(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=self.kwargs['pk'], post_id=self.kwargs['post_id'])
        user_profile = self.request.user.profile

        if comment.post.visibility == 'me' and comment.post.author != request.user:
            return Response({"error": "이 게시글의 댓글을 삭제할 권한이 없습니다."}, status=403)

        if user_profile != comment.author and user_profile != comment.post.author:
            return Response({"error": "삭제할 권한이 없습니다."}, status=403)

        if comment.is_parent:
            comment.replies.all().delete()
        else:
            comment.content = "삭제된 대댓글입니다."
            comment.is_private = False
            comment.save()

        return super().delete(request, *args, **kwargs)
