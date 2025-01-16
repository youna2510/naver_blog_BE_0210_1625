from django.db import models
from django.conf import settings
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models.profile import Profile  # 이미 정의된 Profile 모델을 가져옴
from ..serializers.profile import ProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.openapi import Parameter, TYPE_FILE, TYPE_STRING, Schema

class ProfileDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        """
        현재 로그인된 사용자의 프로필만 반환
        """
        return Profile.objects.get(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 조회",
        operation_description="현재 로그인된 사용자의 프로필 정보를 반환합니다.",
        responses={
            200: openapi.Response(
                description="성공적으로 프로필 반환",
                schema=ProfileSerializer()
            )
        }
    )
    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 전체 수정",
        operation_description="현재 로그인된 사용자의 프로필 정보를 전체 수정합니다.",
        manual_parameters=[
            openapi.Parameter(
                'blog_name', openapi.IN_FORM, description='블로그 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'blog_pic', openapi.IN_FORM, description='블로그 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'username', openapi.IN_FORM, description='사용자 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'user_pic', openapi.IN_FORM, description='프로필 사진', type=openapi.TYPE_FILE
            ),
        ],
        responses={
            200: openapi.Response(
                description="성공적으로 프로필 전체 수정",
                schema=ProfileSerializer()
            ),
            400: openapi.Response(description="잘못된 요청"),
        }
    )
    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 부분 수정",
        operation_description="현재 로그인된 사용자의 프로필만 수정 가능합니다.",
        manual_parameters=[
            openapi.Parameter(
                'blog_name', openapi.IN_FORM, description='블로그 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'blog_pic', openapi.IN_FORM, description='블로그 사진', type=openapi.TYPE_FILE
            ),
            openapi.Parameter(
                'username', openapi.IN_FORM, description='사용자 이름', type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'user_pic', openapi.IN_FORM, description='프로필 사진', type=openapi.TYPE_FILE
            ),
        ],
        responses={
            200: openapi.Response(
                description="성공적으로 프로필 수정",
                schema=ProfileSerializer()
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    def delete(self, request, *args, **kwargs):
        """
        프로필 삭제는 지원되지 않음
        """
        return Response({"detail": "프로필은 삭제할 수 없습니다."}, status=403)


#ex: patch
    #1. get_object로 수정할 객체를 가져옴.
    #2. 요청 데이터를 serializer로 검증.
    #3. 검증된 데이터를 저장 (perform_update 호출).
    #4. 수정된 데이터를 직렬화하여 클라이언트에 반환.

