from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Post, PostText, PostImage
from ..models.neighbor import Neighbor
from django.db.models import Q
from ..serializers import PostSerializer
import json
import os
import shutil

class PostListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ✅ JSONParser 제거 (Swagger 문제 해결)
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user
        public_posts = Q(visibility='everyone')
        my_posts = Q(author=user)

        from_neighbors = list(
            Neighbor.objects.filter(from_user=user, status="accepted").values_list('to_user', flat=True))
        to_neighbors = list(
            Neighbor.objects.filter(to_user=user, status="accepted").values_list('from_user', flat=True))

        # ✅ 두 리스트를 합치고 중복 제거
        neighbor_ids = set(from_neighbors + to_neighbors)

        # 🔥 본인의 ID는 제외
        neighbor_ids.discard(user.id)

        mutual_neighbor_posts = Q(visibility='mutual', author_id__in=neighbor_ids)

        # 본인의 ID는 제외
        neighbor_ids = set(neighbor_ids) - {user.id}


        return Post.objects.filter(
           public_posts | my_posts | mutual_neighbor_posts
        )

    @swagger_auto_schema(
        operation_summary="게시물 목록 조회",
        operation_description="로그인한 사용자가 볼 수 있는 게시물 목록을 반환합니다.",
        responses={200: PostSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="게시물 생성 (multipart/form-data 사용)",
        operation_description="게시물을 생성할 때 JSON 데이터와 이미지를 함께 업로드할 수 있습니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING, enum=['everyone', 'mutual', 'me'], required=False),
            openapi.Parameter('is_complete', openapi.IN_FORM, description='작성 상태', type=openapi.TYPE_STRING, enum=['true', 'false'], required=False),
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
        is_complete = request.data.get('is_complete', 'false')

        # JSON 문자열을 파싱해서 리스트로 변환
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

        # ✅ 필수 데이터 검증
        if not title or not category:
            return Response({"error": "title과 category는 필수 항목입니다."}, status=400)

        # ✅ 게시물 생성
        post = Post.objects.create(
            author=request.user,
            title=title,
            category=category,
            visibility=visibility,
            is_complete=is_complete  # ✅ 임시 저장 가능하도록 수정
        )

        # ✅ PostImage 생성 (이미지가 있을 경우)
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

        # ✅ 대표 이미지가 없을 경우 첫 번째 이미지를 대표로 설정
        if not any(img.is_representative for img in created_images) and created_images:
            created_images[0].is_representative = True
            created_images[0].save()

        # ✅ PostText 생성
        for text in texts:
            PostText.objects.create(post=post, content=text)

        # ✅ 응답 메시지 구분
        serializer = PostSerializer(post)
        if is_complete == "true":
            return Response({"message": "게시물이 성공적으로 생성되었습니다.", "post": serializer.data}, status=201)
        else:
            return Response({"message": "게시물이 임시 저장되었습니다.", "post": serializer.data}, status=201)


class PostDetailView(RetrieveUpdateDestroyAPIView):
    """
    게시물 상세 조회, 수정, 삭제 뷰
    """
    permission_classes = [IsAuthenticated]
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        my_posts = Q(author=user)

        # ✅ 서로이웃 ID 리스트 가져오기
        from_neighbors = list(
            Neighbor.objects.filter(from_user=user, status="accepted").values_list('to_user', flat=True))
        to_neighbors = list(
            Neighbor.objects.filter(to_user=user, status="accepted").values_list('from_user', flat=True))

        # ✅ 두 리스트를 합치고 중복 제거
        neighbor_ids = set(from_neighbors + to_neighbors)

        # 🔥 본인의 ID는 제외
        neighbor_ids.discard(user.id)

        mutual_neighbor_posts = Q(visibility='mutual', author_id__in=neighbor_ids)
        public_posts = Q(visibility='everyone')

        return Post.objects.filter(public_posts | my_posts | mutual_neighbor_posts)
    @swagger_auto_schema(
        operation_summary="게시물 상세 조회",
        operation_description="특정 게시물의 텍스트와 이미지를 포함한 상세 정보를 조회합니다.",
        responses={200: PostSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def parse_json_field(self, field):
        """ JSON 문자열을 리스트로 변환 """
        if field:
            try:
                return json.loads(field)
            except json.JSONDecodeError:
                return []
        return []

    @swagger_auto_schema(
        operation_summary="게시물 전체 수정 (사용 불가)",
        operation_description="PUT 메서드는 허용되지 않습니다. 대신 PATCH를 사용하세요.",
        responses={405: "PUT method is not allowed. Use PATCH instead."},
    )
    def put(self, request, *args, **kwargs):
        return Response({"error": "PUT method is not allowed. Use PATCH instead."}, status=405)

    @swagger_auto_schema(
        operation_summary="게시물 부분 수정 (PATCH)",
        operation_description="게시물의 특정 필드만 수정합니다. 제공된 데이터만 업데이트됩니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING,
                              required=False),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING,
                              enum=['everyone', 'mutual', 'me'], required=False),
            openapi.Parameter('is_complete', openapi.IN_FORM,
                              description='작성 상태 (true: 작성 완료, false: 임시 저장 → 변경 가능, 단 true → false 변경 불가)',
                              type=openapi.TYPE_STRING, enum=['true', 'false'], required=False),  # ✅ 설명 추가
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열 (새 이미지 업로드)', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_FILE), required=False),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('remove_images', openapi.IN_FORM, description='삭제할 이미지 ID 목록 (JSON 형식 문자열)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('update_images', openapi.IN_FORM, description='수정할 이미지 ID 목록 (JSON 형식 문자열)',
                              type=openapi.TYPE_STRING, required=False),
        ],
        responses={200: PostSerializer()},
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        # ✅ `is_complete=true`인 게시물은 `false`로 변경할 수 없음
        new_is_complete = request.data.get('is_complete', instance.is_complete)
        if instance.is_complete == "true" and new_is_complete == "false":
            return Response({"error": "작성 완료된 게시물은 다시 임시 저장 상태로 변경할 수 없습니다."}, status=400)

        # ✅ visibility 값 검증 및 업데이트
        new_visibility = request.data.get('visibility', instance.visibility)
        if new_visibility not in dict(Post.VISIBILITY_CHOICES):
            return Response({"error": "잘못된 공개 범위 값입니다."}, status=400)
        instance.visibility = new_visibility

        # ✅ 기본 필드 업데이트
        instance.title = request.data.get('title', instance.title)
        instance.category = request.data.get('category', instance.category)
        instance.is_complete = request.data.get('is_complete',
                                                instance.is_complete)  # is_complete 변경 허용 (true→false 불가)
        instance.save()

        # ✅ JSON 데이터 파싱 함수
        def parse_json_field(field):
            try:
                return json.loads(request.data.get(field, "[]"))
            except json.JSONDecodeError:
                return []

        images = request.FILES.getlist('images')  # 새로 업로드된 이미지 파일 리스트
        captions = parse_json_field('captions')  # 캡션 배열
        is_representative_flags = parse_json_field('is_representative')  # 대표 여부 배열
        remove_images = parse_json_field('remove_images')  # 삭제할 이미지 ID 배열
        update_images = parse_json_field('update_images')  # 기존 이미지 ID 리스트

        # ✅ 기존 이미지 삭제
        PostImage.objects.filter(id__in=remove_images, post=instance).delete()

        # ✅ 기존 이미지 수정 (ID 유지) - 업로드된 파일과 ID 매칭
        for idx, image_id in enumerate(update_images):
            try:
                post_image = PostImage.objects.get(id=image_id, post=instance)
                if idx < len(images):  # 업로드된 새 이미지가 있다면
                    post_image.image.delete()  # 기존 이미지 삭제
                    post_image.image = images[idx]  # 새로운 이미지 저장
                post_image.save()
            except PostImage.DoesNotExist:
                continue  # 존재하지 않으면 무시

        # ✅ 새 이미지 추가 (ID가 새로 생성됨)
        for idx, image in enumerate(images[len(update_images):]):  # 기존 이미지 수정 후 남은 파일들
            PostImage.objects.create(
                post=instance,
                image=image,
                caption=captions[idx] if idx < len(captions) else None,
                is_representative=is_representative_flags[idx] if idx < len(is_representative_flags) else False,
            )

        # ✅ 대표 이미지 중복 검사 및 자동 설정
        representative_images = instance.images.filter(is_representative=True)
        if representative_images.count() > 1:
            return Response({"error": "대표 이미지는 한 개만 설정할 수 있습니다."}, status=400)

        if representative_images.count() == 0 and instance.images.exists():
            first_image = instance.images.first()
            first_image.is_representative = True
            first_image.save()

        # ✅ 응답 반환
        serializer = PostSerializer(instance)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="게시물 삭제",
        operation_description="특정 게시물과 관련 이미지를 포함한 모든 데이터를 삭제합니다.",
        responses={204: "삭제 성공"},
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        # ✅ 폴더 경로 저장 (main/media/카테고리/제목)
        if instance.images.exists():
            folder_path = os.path.dirname(instance.images.first().image.path)

        # ✅ 관련 이미지 삭제
        for image in instance.images.all():
            if image.image:  # 이미지 파일이 있는 경우
                image.image.storage.delete(image.image.name)  # 물리적 파일 삭제
            image.delete()  # DB 레코드 삭제

        # ✅ 폴더 삭제 (비어 있다면)
        if folder_path and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)  # 폴더 삭제

        if instance.author != request.user:
            return Response({"error": "게시물을 삭제할 권한이 없습니다."}, status=403)

        instance.delete()
        return Response(status=204)

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
        return Post.objects.filter(author=self.request.user, is_complete='false')
