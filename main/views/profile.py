from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import models
from ..models.profile import Profile
from ..serializers.profile import ProfileSerializer

#사용자의 서로 이웃 목록 반환
class NeighborListView(ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        현재 사용자를 제외한 이웃 목록 반환
        """
        user_profile = Profile.objects.get(user=self.request.user)
        neighbors_ids = user_profile.neighbors  # 이웃의 ID 리스트로 가정
        return Profile.objects.filter(user__id__in=neighbors_ids)

    @swagger_auto_schema(
        operation_summary="이웃 목록 조회",
        operation_description="현재 로그인된 사용자를 제외한 이웃(neighbors) 목록을 반환합니다.",
        responses={
            200: openapi.Response(
                description="성공적으로 이웃 목록 반환",
                schema=ProfileSerializer(many=True)
            ),
            401: openapi.Response(description="인증 실패"),
        }
    )
    def get(self, request, *args, **kwargs):
        """
        이웃 목록 반환 API
        """
        return super().get(request, *args, **kwargs)


# DetailView - 특정 사용자의 프로필 조회 및 현재 사용자만 수정/삭제 가능
class ProfileDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        현재 로그인된 사용자의 프로필만 반환
        """
        return Profile.objects.get(user=self.request.user)

    def perform_update(self, serializer):
        """
        현재 로그인된 사용자의 프로필만 수정 가능
        """
        serializer.save()

    def perform_destroy(self, instance):
        """
        현재 로그인된 사용자의 프로필만 삭제 가능
        """
        instance.delete()

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
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 수정",
        operation_description="현재 로그인된 사용자의 프로필만 수정 가능합니다.",
        request_body=ProfileSerializer,
        responses={
            200: openapi.Response(
                description="성공적으로 프로필 수정",
                schema=ProfileSerializer()
            ),
            400: openapi.Response(description="잘못된 요청")
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="현재 사용자 프로필 삭제",
        operation_description="현재 로그인된 사용자의 프로필만 삭제 가능합니다.",
        responses={
            204: openapi.Response(description="프로필 삭제 성공")
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
