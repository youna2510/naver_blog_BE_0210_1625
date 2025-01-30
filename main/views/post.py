from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Post, PostText, PostImage
from ..serializers import PostSerializer
import json
import os
import shutil

class PostListView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # ✅ JSONParser 제거 (Swagger 문제 해결)
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    @swagger_auto_schema(
        operation_summary="게시물 생성 (multipart/form-data 사용)",
        operation_description="게시물을 생성할 때 JSON 데이터와 이미지를 함께 업로드할 수 있습니다.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, description='게시물 제목', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('category', openapi.IN_FORM, description='카테고리', type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('visibility', openapi.IN_FORM, description='공개 범위', type=openapi.TYPE_STRING, enum=['everyone', 'mutual'], required=False),
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

        # ✅ 필수 데이터 검증 (is_complete가 false면 거부)
        if not title or not category:
            return Response({"error": "title과 category는 필수 항목입니다."}, status=400)
        if is_complete == "false":  # `false`일 경우 생성 불가
            return Response({"error": "is_complete가 true일 때만 게시물을 생성할 수 있습니다."}, status=400)

         # 대표 이미지 중복 검사 (한 개만 가능)
        if is_representative_flags.count(True) > 1:
            return Response({"error": "대표 이미지는 한 개만 설정할 수 있습니다."},status=400)

        # Post 객체 생성
        post = Post.objects.create(
            author=request.user,
            title=title,
            category=category,
            visibility=visibility,
            is_complete=is_complete
        )

        # PostImage 생성
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

        # 대표 이미지가 없을 경우 첫 번째 이미지를 대표로 설정
        if not any(img.is_representative for img in created_images) and created_images:
            created_images[0].is_representative = True
            created_images[0].save()

        # PostText 생성
        for text in texts:
            PostText.objects.create(post=post, content=text)

        # 직렬화 후 응답
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
                              enum=['everyone', 'mutual'], required=False),
            openapi.Parameter('texts', openapi.IN_FORM, description='텍스트 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('images', openapi.IN_FORM, description='이미지 파일 배열 (새 이미지 업로드)', type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_FILE), required=False),
            openapi.Parameter('captions', openapi.IN_FORM, description='이미지 캡션 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('is_representative', openapi.IN_FORM, description='대표 사진 여부 배열 (JSON 형식 문자열, id 포함 가능)',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('remove_images', openapi.IN_FORM, description='삭제할 이미지 ID 목록 (JSON 형식 문자열)',
                              type=openapi.TYPE_STRING, required=False),  # ✅ 추가됨
            openapi.Parameter('update_images', openapi.IN_FORM, description='수정할 이미지 ID 목록 (JSON 형식 문자열)',
                              type=openapi.TYPE_STRING, required=False),  # ✅ 추가됨
        ],
        responses={200: PostSerializer()},
    )
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        # ✅ 필수 데이터 검증 (is_complete=false면 거부)
        is_complete = request.data.get('is_complete', str(instance.is_complete)).lower()  # 기존 값 유지
        if is_complete == "false":  # `false`일 경우 부분 수정 불가
            return Response({"error": "is_complete가 true일 때만 게시물을 수정할 수 있습니다."}, status=400)

        # ✅ 기본 필드 업데이트
        if 'title' in request.data:
            instance.title = request.data.get('title')
        if 'category' in request.data:
            instance.category = request.data.get('category')
        if 'visibility' in request.data:
            instance.visibility = request.data.get('visibility')
        if 'is_complete' in request.data:
            instance.is_complete = request.data.get('is_complete')
        instance.save()

        # ✅ Swagger에서 form-data로 전달된 데이터 파싱
        images = request.FILES.getlist('images')  # 새로 업로드된 이미지 파일 리스트
        captions = json.loads(request.data.get('captions', '[]'))  # 캡션 배열
        is_representative_flags = json.loads(request.data.get('is_representative', '[]'))  # 대표 여부 배열
        remove_images = json.loads(request.data.get('remove_images', '[]'))  # 삭제할 이미지 ID 배열
        update_images = json.loads(request.data.get('update_images', '[]'))  # 기존 이미지 ID 리스트

        # ✅ 기존 이미지 삭제
        for image_id in remove_images:
            try:
                post_image = PostImage.objects.get(id=image_id, post=instance)
                post_image.image.delete()  # 실제 파일 삭제
                post_image.delete()  # DB 레코드 삭제
            except PostImage.DoesNotExist:
                continue  # 존재하지 않는 경우 무시

        # ✅ 기존 이미지 수정 (ID 유지) - 업로드된 파일과 ID 매칭
        for idx, image_id in enumerate(update_images):
            try:
                post_image = PostImage.objects.get(id=image_id, post=instance)
                if idx < len(images):  # 업로드된 이미지 파일이 있다면
                    post_image.image.delete()  # 기존 이미지 삭제
                    post_image.image = images[idx]  # 새로운 이미지 저장
                post_image.save()
            except PostImage.DoesNotExist:
                continue  # 존재하지 않으면 무시

        # ✅ 새 이미지 추가 (ID가 새로 생성됨)
        for idx, image in enumerate(images[len(update_images):]):  # 기존 이미지 수정 후 남은 파일들
            caption = captions[idx] if idx < len(captions) else None
            is_representative = (
                is_representative_flags[idx] if idx < len(is_representative_flags) else False
            )
            PostImage.objects.create(
                post=instance,
                image=image,
                caption=caption,
                is_representative=is_representative,
            )

        # ✅ 대표 이미지 중복 검사
        representative_images = instance.images.filter(is_representative=True)
        if representative_images.count() > 1:
            return Response(
                {"error": "대표 이미지는 한 개만 설정할 수 있습니다."},
                status=400,
            )

        # ✅ 대표 이미지가 없으면 첫 번째 이미지 자동 설정
        if representative_images.count() == 0 and instance.images.exists():
            first_image = instance.images.first()
            first_image.is_representative = True
            first_image.save()

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

        # ✅ 게시물 삭제
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