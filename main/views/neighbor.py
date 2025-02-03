from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models.neighbor import Neighbor
from ..models.profile import Profile
from ..serializers.neighbor import NeighborSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import models
from django.db.models import Q


class NeighborView(APIView):
    """
    ✅ 서로이웃 신청 (POST)
    ✅ 서로이웃 요청 목록 조회 (GET)
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="서로이웃 신청 (버튼 방식)",
        operation_description="특정 사용자의 프로필에서 서로이웃 추가 버튼을 누르면 해당 사용자를 대상으로 신청을 보냅니다.",
        responses={
            201: openapi.Response(
                description="서로이웃 신청 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "neighbor_request": openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: openapi.Response(description="잘못된 요청"),
        },
    )
    def post(self, request, to_user_id):
        """
        ✅ 서로이웃 신청 (POST /api/neighbors/{to_user_id}/)
        """
        from_user = request.user
        to_user = get_object_or_404(Profile, user_id=to_user_id).user  # `Profile`에서 `User` 가져오기

        # ✅ 자기 자신에게 신청 불가
        if from_user.id == to_user.id:
            return Response({"message": "자기 자신에게 서로이웃 신청할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 기존 신청 확인 (중복 신청 방지)
        if Neighbor.objects.filter(from_user=from_user, to_user=to_user, status='pending').exists():
            return Response({"message": "이미 보낸 서로이웃 요청이 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if Neighbor.objects.filter(from_user=from_user, to_user=to_user, status='accepted').exists():
            return Response({"message": "이미 서로이웃 관계입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 서로이웃 신청 생성
        neighbor_request = Neighbor.objects.create(from_user=from_user, to_user=to_user, status="pending")

        return Response({
            "message": "서로이웃 신청이 완료되었습니다.",
            "neighbor_request": NeighborSerializer(neighbor_request).data
        }, status=status.HTTP_201_CREATED)


class NeighborRequestListView(ListAPIView):
    """
    ✅ 자신에게 서로이웃 요청을 보낸 사람들의 목록 조회 (GET /api/neighbors/requests/)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NeighborSerializer

    @swagger_auto_schema(
        operation_summary="받은 서로이웃 요청 목록 조회",
        operation_description="현재 로그인한 사용자가 받은 서로이웃 요청 목록을 조회합니다.",
        responses={
            200: openapi.Response(
                description="서로이웃 요청 목록 반환",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "requests": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "from_username": openapi.Schema(type=openapi.TYPE_STRING,
                                                                    description="요청 보낸 사용자 닉네임"),
                                    "from_user_pic": openapi.Schema(type=openapi.TYPE_STRING, format="url",
                                                                    description="요청 보낸 사용자 프로필 사진"),
                                }
                            )
                        )
                    }
                )
            ),
            200: openapi.Response(description="받은 서로이웃 요청이 없습니다."),
        }
    )
    def list(self, request, *args, **kwargs):
        """
        ✅ 받은 서로이웃 요청이 없는 경우 적절한 메시지를 반환
        """
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response({"message": "받은 서로이웃 요청이 없습니다.", "requests": []}, status=200)

        request_list = [
            {
                "from_username": neighbor.from_user.profile.username,
                "from_user_pic": neighbor.from_user.profile.user_pic.url if neighbor.from_user.profile.user_pic else None
            }
            for neighbor in queryset
        ]

        return Response({"requests": request_list}, status=200)

    def get_queryset(self):
        """
        ✅ 자신에게 서로이웃 요청을 보낸 사람들(QuerySet) 반환
        """
        user = self.request.user
        return Neighbor.objects.filter(to_user=user, status="pending").select_related("from_user__profile")


class NeighborAcceptView(APIView):
    """
    ✅ 서로이웃 요청 수락 (PUT /api/neighbors/accept/{neighbor_id}/)
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="서로이웃 요청 수락",
        operation_description="받은 서로이웃 신청을 수락합니다.",
        responses={
            200: openapi.Response(description="서로이웃 요청 수락됨"),
            400: openapi.Response(description="이미 수락된 요청"),
            404: openapi.Response(description="요청을 찾을 수 없음"),
        }
    )
    def put(self, request, *args, **kwargs):
        """
        ✅ 서로이웃 요청을 보낸 사용자의 ID (`from_user_id`)를 기반으로 수락
        """
        from_user_id = kwargs.get("from_user_id")
        to_user = request.user  # 현재 로그인한 사용자

        # ✅ 서로이웃 요청 찾기 (from_user_id → 현재 로그인한 사용자로 요청한 것)
        neighbor_request = get_object_or_404(
            Neighbor, from_user__id=from_user_id, to_user=to_user, status="pending"
        )

        if neighbor_request.status == "accepted":
            return Response({"message": "이미 서로이웃 상태입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 서로이웃 요청 수락
        neighbor_request.status = "accepted"
        neighbor_request.save()

        return Response({"message": "서로이웃 요청이 수락되었습니다."}, status=status.HTTP_200_OK)

class NeighborRejectView(APIView):
    """
    ✅ 서로이웃 요청 거절 (DELETE /api/neighbors/reject/{from_user_id}/)
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="서로이웃 요청 거절",
        operation_description="서로이웃 요청을 보낸 사용자의 ID로 조회하여 거절합니다.",
        responses={
            200: openapi.Response(description="서로이웃 요청 거절됨"),
            400: openapi.Response(description="이미 수락된 요청"),
            404: openapi.Response(description="요청을 찾을 수 없음"),
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        ✅ 서로이웃 요청을 보낸 사용자의 ID (`from_user_id`)를 기반으로 거절
        """
        from_user_id = kwargs.get("from_user_id")
        to_user = request.user  # 현재 로그인한 사용자

        # ✅ 서로이웃 요청 찾기 (from_user_id → 현재 로그인한 사용자로 요청한 것)
        neighbor_request = get_object_or_404(
            Neighbor, from_user__id=from_user_id, to_user=to_user, status="pending"
        )

        if neighbor_request.status == "accepted":
            return Response({"message": "이미 수락된 요청은 거절할 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 서로이웃 요청 거절 (삭제)
        neighbor_request.delete()

        return Response({"message": "서로이웃 요청이 거절되었습니다."}, status=status.HTTP_200_OK)


class PublicNeighborListView(APIView):
    """
    ✅ 서로이웃 목록 조회 (GET /api/profile/{user_id}/neighbors/)
    - 프로필이 존재하지 않으면 404 반환.
    - 프로필 소유자가 서로이웃 목록을 비공개로 설정한 경우 `"비공개입니다"` 반환.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="서로이웃 목록 조회",
        operation_description="특정 사용자의 서로이웃 목록을 조회합니다.",
        responses={
            200: openapi.Response(
                description="서로이웃 목록 반환",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "username": openapi.Schema(type=openapi.TYPE_STRING),
                        "neighbors": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                                    "user_pic": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="프로필 이미지 URL"),
                                }
                            )
                        )
                    }
                )
            ),
            403: openapi.Response(description="비공개입니다."),
            404: openapi.Response(description="사용자를 찾을 수 없음"),
        }
    )
    def get(self, request, user_id):
        profile = get_object_or_404(Profile, user_id=user_id)

        # ✅ 서로이웃 목록이 비공개인 경우
        if not profile.neighbor_visibility:
            return Response({"message": "비공개입니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ `Neighbor` 모델을 사용하여 관계 조회
        neighbors = Neighbor.objects.filter(
            Q(from_user=profile.user) | Q(to_user=profile.user),
            status="accepted"
        ).select_related("from_user", "to_user")

        neighbor_list = []
        for neighbor in neighbors:
            if neighbor.from_user == profile.user:
                neighbor_profile = Profile.objects.get(user=neighbor.to_user)
            else:
                neighbor_profile = Profile.objects.get(user=neighbor.from_user)

            neighbor_list.append({
                "username": neighbor_profile.username,
                "user_pic": neighbor_profile.user_pic.url if neighbor_profile.user_pic else None
            })

        return Response({
            "username": profile.username,
            "neighbors": neighbor_list
        }, status=status.HTTP_200_OK)