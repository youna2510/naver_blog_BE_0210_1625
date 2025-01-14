from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # 인증된 사용자만 접근 가능
from rest_framework_simplejwt.authentication import JWTAuthentication  # JWT 인증
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Swagger 요청 스키마 정의
logout_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='리프레시 토큰')
    },
    required=['refresh']
)

# Swagger 응답 스키마 정의
logout_success_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='성공 메시지')
    }
)

logout_error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='오류 메시지')
    }
)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 로그아웃 가능
    authentication_classes = [JWTAuthentication]  # JWT 토큰을 통한 인증

    @swagger_auto_schema(
        operation_summary="로그아웃",
        operation_description="클라이언트에서 전달한 refresh 토큰을 블랙리스트에 추가하여 로그아웃 처리합니다.",
        request_body=logout_request_schema,
        responses={
            200: openapi.Response(description="로그아웃 성공", schema=logout_success_schema),
            400: openapi.Response(description="로그아웃 실패", schema=logout_error_schema),
            500: openapi.Response(description="서버 오류", schema=logout_error_schema),
        }
    )
    def post(self, request):
        """
        로그아웃 API
        클라이언트에서 전달한 refresh 토큰을 블랙리스트에 추가하여 로그아웃 처리합니다.
        """
        try:
            # 클라이언트에서 받은 refresh 토큰
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return JsonResponse({'error': '리프레시 토큰이 필요합니다.'}, status=400)

            # RefreshToken 인스턴스를 생성하고 블랙리스트에 추가
            token = RefreshToken(refresh_token)
            token.blacklist()

            return JsonResponse({'message': '로그아웃 성공!'}, status=200)
        except TokenError as e:
            return JsonResponse({'error': f'토큰 오류: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


