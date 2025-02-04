from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Post, PostText, PostImage,CustomUser,Profile
from ..models.neighbor import Neighbor
from django.db.models import Q
from ..serializers import PostSerializer
import json
import os
import shutil
from django.shortcuts import get_object_or_404
from django.utils.timezone import now, timedelta

def to_boolean(value):
    """
    'true', 'false', 1, 0 같은 값을 실제 Boolean(True/False)로 변환
    """
    if isinstance(value, bool):  # 이미 Boolean이면 그대로 반환
        return value
    if isinstance(value, str):
        return value.lower() == "true"  # "true" → True, "false" → False
    if isinstance(value, int):
        return bool(value)  # 1 → True, 0 → False
    return False  # 기본적으로 False 처리

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class PostListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        urlname = self.request.query_params.get('urlname', None)
        category = self.request.query_params.get('category', None)
        pk = self.request.query_params.get('pk', None)

        user = self.request.user
        if urlname:
            try:
                profile = Profile.objects.get(urlname=urlname)
                user = profile.user
            except Profile.DoesNotExist:
                return Post.objects.none()

        my_posts = Q(author=user)
        from_neighbors = list(
            Neighbor.objects.filter(from_user=user, status="accepted").values_list('to_user', flat=True)
        )
        to_neighbors = list(
            Neighbor.objects.filter(to_user=user, status="accepted").values_list('from_user', flat=True)
        )
        neighbor_ids = set(from_neighbors + to_neighbors)
        neighbor_ids.discard(user.id)

        mutual_neighbor_posts = Q(visibility='mutual', author_id__in=neighbor_ids)
        public_posts = Q(visibility='everyone')

        queryset = Post.objects.filter(
            (public_posts | my_posts | mutual_neighbor_posts) & Q(is_complete=True)
        )

        if category:
            queryset = queryset.filter(category=category)

        if pk:
            queryset = queryset.filter(pk=pk)

        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('urlname', openapi.IN_QUERY, description="조회할 사용자의 고유 ID", required=False, type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="조회할 게시물 카테고리", required=False, type=openapi.TYPE_STRING),
            openapi.Parameter('pk', openapi.IN_QUERY, description="조회할 게시물 ID", required=False, type=openapi.TYPE_INTEGER),
        ],
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        pk = self.request.query_params.get('pk', None)
        if pk:
            post = get_object_or_404(queryset, pk=pk)
            serializer = self.get_serializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PostCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ✅ POST 요청에서 multipart/form-data 처리
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="게시물 생성 (multipart/form-data 사용)",
        operation_description="게시물을 생성할 때 JSON 데이터와 이미지를 함께 업로드할 수 있습니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING, enum=['everyone', 'mutual', 'me'], required=False),
            openapi.Parameter('is_complete', openapi.IN_FORM, description='작성 상태', type=openapi.TYPE_BOOLEAN, enum=['true', 'false'], required=False),
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열 (JSON 형식 문자열)', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열', type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE), required=False),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열 (JSON 형식 문자열)', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부 배열 (JSON 형식 문자열)', type=openapi.TYPE_STRING, required=False),
        ],
        responses={201: PostSerializer()},
    )
    def post(self, request, *args, **kwargs):
        title = request.data.get('title')
        category = request.data.get('category')
        visibility = request.data.get('visibility', 'everyone')
        is_complete = to_boolean(request.data.get('is_complete', False))

        # JSON 문자열을 리스트로 변환하는 함수
        def parse_json_field(field):
            if field:
                try:
                    return json.loads(field)  # ✅ JSON 문자열을 리스트로 변환
                except json.JSONDecodeError:
                    return []
            return []

        texts = parse_json_field(request.data.get('texts'))
        captions = parse_json_field(request.data.get('captions'))
        is_representative_flags = parse_json_field(request.data.get('is_representative'))
        images = request.FILES.getlist('images', [])

        if not title or not category:
            return Response({"error": "title과 category는 필수 항목입니다."}, status=400)

        post = Post.objects.create(
            author=request.user,
            title=title,
            category=category,
            visibility=visibility,
            is_complete=is_complete
        )

        # 이미지 저장
        created_images = []
        for idx, image in enumerate(images):
            caption = captions[idx] if idx < len(captions) else None
            is_representative = is_representative_flags[idx] if idx < len(is_representative_flags) else False
            post_image = PostImage.objects.create(
                post=post,
                image=image,
                caption=caption,
                is_representative=is_representative
            )
            created_images.append(post_image)

        if not any(img.is_representative for img in created_images) and created_images:
            created_images[0].is_representative = True
            created_images[0].save()

        for text in texts:
            PostText.objects.create(post=post, content=text)

        serializer = PostSerializer(post)
        if is_complete:
            return Response({"message": "게시물이 성공적으로 생성되었습니다.", "post": serializer.data}, status=201)
        else:
            return Response({"message": "게시물이 임시 저장되었습니다.", "post": serializer.data}, status=201)

class PostMyView(ListAPIView):
    """
    로그인된 유저가 작성한 모든 게시물 목록을 조회하는 API
    쿼리 파라미터로 category와 pk를 통해 필터링 가능
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user
        category = self.request.query_params.get('category', None)
        pk = self.request.query_params.get('pk', None)

        # 로그인된 유저가 작성한 게시물만 필터링
        queryset = Post.objects.filter(author=user)

        # 'category' 파라미터가 있으면 해당 카테고리로 필터링
        if category:
            queryset = queryset.filter(category=category)

        # 'pk' 파라미터가 있으면 해당 게시물 ID로 필터링
        if pk:
            queryset = queryset.filter(pk=pk)

        return queryset

    @swagger_auto_schema(
        operation_summary="내가 작성한 게시물 목록 조회",
        operation_description="로그인된 유저가 작성한 모든 게시물 목록을 반환합니다. 쿼리 파라미터로 category와 pk를 통해 필터링 가능합니다.",
        responses={200: PostSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="게시물의 카테고리로 필터링합니다. 예: 'Travel', 'Food' 등.",
                required=False,
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'pk',
                openapi.IN_QUERY,
                description="게시물 ID로 필터링합니다.",
                required=False,
                type=openapi.TYPE_INTEGER
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PostMutualView(ListAPIView):
    """
    서로 이웃(mutual)인 사람들의 최근 1주일 이내 게시물 목록을 조회하는 API
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user

        # ✅ 서로이웃 ID 리스트 가져오기
        from_neighbors = list(
            Neighbor.objects.filter(from_user=user, status="accepted").values_list('to_user', flat=True)
        )
        to_neighbors = list(
            Neighbor.objects.filter(to_user=user, status="accepted").values_list('from_user', flat=True)
        )
        neighbor_ids = set(from_neighbors + to_neighbors)
        neighbor_ids.discard(user.id)

        mutual_neighbor_posts = Q(visibility='mutual', author_id__in=neighbor_ids)
        one_week_ago = now() - timedelta(days=7)

        # ✅ 최근 1주일 이내 작성된 서로 이웃의 게시물만 반환
        queryset = Post.objects.filter(
            mutual_neighbor_posts & Q(is_complete=True) & Q(created_at__gte=one_week_ago)
        )

        return queryset

    @swagger_auto_schema(
        operation_summary="서로 이웃 게시물 목록 조회",
        operation_description="서로 이웃(mutual)인 사람들의 최근 1주일 이내 게시물 목록을 반환합니다.",
        responses={200: PostSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DraftPostListView(ListAPIView):
    """
    임시 저장된 게시물만 반환하는 뷰
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="임시 저장된 게시물 목록 조회",
        operation_description="로그인한 사용자의 임시 저장된 게시물만 반환합니다.",
        responses={200: PostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        요청한 사용자의 임시 저장된 게시물만 반환
        """
        return Post.objects.filter(author=self.request.user, is_complete='false')


class DraftPostDetailView(RetrieveAPIView):
    """
    특정 임시 저장된 게시물 1개 반환하는 뷰
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="임시 저장된 게시물 상세 조회",
        operation_description="특정 임시 저장된 게시물의 상세 정보를 반환합니다.",
        responses={200: PostSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        요청한 사용자의 특정 임시 저장된 게시물만 반환
        """
        return Post.objects.filter(author=self.request.user, is_complete=False)
class DraftPostListView(ListAPIView):
    """
    임시 저장된 게시물만 반환하는 뷰
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="임시 저장된 게시물 목록 조회",
        operation_description="로그인한 사용자의 임시 저장된 게시물만 반환합니다.",
        responses={200: PostSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        요청한 사용자의 임시 저장된 게시물만 반환
        """
        return Post.objects.filter(author=self.request.user, is_complete=False)  # ✅ Boolean 값으로 필터링

