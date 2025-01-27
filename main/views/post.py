from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Post, PostText, PostImage
from ..serializers import PostSerializer

class PostListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="게시물 생성",
        operation_description="새 게시물을 생성합니다. 텍스트와 이미지를 함께 업로드할 수 있습니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING, enum=['everyone', 'mutual']),
            openapi.Parameter('is_complete', openapi.IN_FORM, description='작성 상태', type=openapi.TYPE_STRING, enum=['true', 'false']),
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열', type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열', type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_FILE)),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열', type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부', type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_BOOLEAN)),
        ],
        responses={201: PostSerializer()},
    )
    def post(self, request, *args, **kwargs):
        title = request.data.get('title')
        category = request.data.get('category')
        visibility = request.data.get('visibility', 'everyone')
        is_complete = request.data.get('is_complete', 'false')
        texts = request.data.getlist('texts', [])
        images = request.FILES.getlist('images', [])
        captions = request.data.getlist('captions', [])
        is_representative_flags = request.data.getlist('is_representative', [])

        if isinstance(captions, list) and len(captions) == 1 and ',' in captions[0]:
            captions = [caption.strip() for caption in captions[0].split(',') if caption.strip()]

        post = Post.objects.create(
            author=request.user,
            title=title,
            category=category,
            visibility=visibility,
            is_complete=is_complete
        )

        created_images = []
        for idx, image in enumerate(images):
            caption = captions[idx] if idx < len(captions) else None
            is_representative = (is_representative_flags[idx].lower() == 'true') if idx < len(is_representative_flags) else False
            post_image = PostImage.objects.create(
                post=post,
                image=image,
                caption=caption,
                is_representative=is_representative
            )
            created_images.append(post_image)

        # Check if no image is marked as representative, set the first one as representative
        if not any(image.is_representative for image in created_images) and created_images:
            created_images[0].is_representative = True
            created_images[0].save()

        for text in texts:
            PostText.objects.create(post=post, content=text)

        serializer = PostSerializer(post)
        return Response(serializer.data, status=201)


class PostDetailView(RetrieveUpdateDestroyAPIView):
    """
    게시물 상세 조회, 수정, 삭제 뷰
    """
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="게시물 상세 조회",
        operation_description="특정 게시물의 텍스트와 이미지를 포함한 상세 정보를 조회합니다.",
        responses={200: PostSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="게시물 전체 수정",
        operation_description="특정 게시물의 모든 필드를 수정합니다. 모든 필드를 제공해야 합니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING,
                              enum=['everyone', 'mutual']),
            openapi.Parameter('is_complete', openapi.IN_FORM, description='작성 상태', type=openapi.TYPE_STRING,
                              enum=['true', 'false']),
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_FILE)),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING)),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_BOOLEAN)),
        ],
        responses={200: PostSerializer()},
    )
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="게시물 일부분 수정",
        operation_description="특정 게시물의 텍스트와 이미지를 수정합니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING,
                              required=False),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING,
                              enum=['everyone', 'mutual'], required=False),
            openapi.Parameter('is_complete', openapi.IN_FORM, description='작성 상태', type=openapi.TYPE_STRING,
                              enum=['true', 'false'], required=False),
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING), required=False),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_FILE), required=False),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING), required=False),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_BOOLEAN), required=False),
        ],
        responses={200: PostSerializer()},
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        # Update instance with partial data
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Handle representative image logic if provided
        if 'is_representative' in request.data:
            images = instance.images.all()
            for image in images:
                image.is_representative = False
                image.save()

            created_images = []
            for idx, image in enumerate(images):
                created_images.append(image)

            # Check if no image is marked as representative, set the first one as representative
            if not any(image.is_representative for image in created_images) and created_images:
                created_images[0].is_representative = True
                created_images[0].save()

        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="게시물 삭제",
        operation_description="특정 게시물을 삭제합니다.",
        responses={204: "삭제 성공"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

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