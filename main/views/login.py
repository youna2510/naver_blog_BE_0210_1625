from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models.profile import Profile
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny  # 인증 없이 접근 가능하게 하기 위한 permission

User = get_user_model()

# Swagger 요청 스키마 정의
#요청 데이터 필드
login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_STRING, description='사용자 아이디'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
    },
    required=['id', 'password']
)

# Swagger 응답 스키마 정의
#응답 데이터 필드
login_success_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='성공 메시지'),
        'id': openapi.Schema(type=openapi.TYPE_STRING, description='사용자 아이디'),
        'profile_created': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='프로필 생성 여부'),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT 리프레시 토큰'),
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT 액세스 토큰'),
    }
)

#에러 처리
login_error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='오류 메시지'),
    }
)

class LoginView(APIView):
    permission_classes = [AllowAny]  # 인증 없이 접근 가능하도록 설정
    #Swagger UI에 이 API의 설명과 요청/응답 구조를 명확히 문서화
    @swagger_auto_schema(
        operation_summary="로그인",
        operation_description="사용자의 아이디와 비밀번호를 확인하여 JWT 토큰을 발급합니다.",
        request_body=login_request_schema,
        responses={
            200: openapi.Response(description="로그인 성공", schema=login_success_schema),
            401: openapi.Response(description="로그인 실패", schema=login_error_schema),
            500: openapi.Response(description="서버 오류", schema=login_error_schema),
        }
    )
    def post(self, request):
        """
        로그인 API
        사용자 인증 후 JWT 토큰과 프로필 생성 여부를 반환합니다.
        """
        try:
            data = request.data # 요청 데이터에서 id와 password를 추출
            id = data.get('id')
            password = data.get('password')

            user = authenticate(request, username=id, password=password) #Django의 인증 시스템을 사용해 사용자를 인증
            if user is not None:
                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)

                # 프로필 존재 여부 확인
                profile_created = Profile.objects.filter(user=user).exists()

                return JsonResponse({
                    'message': '로그인 성공!',
                    'id': user.id,
                    'profile_created': profile_created,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=200)
            else:
                return JsonResponse({'error': '로그인 실패. 아이디 또는 비밀번호를 확인하세요.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)
