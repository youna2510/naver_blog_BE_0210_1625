"""
URL configuration for naver_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from main.views.signup import SignupView
from main.views.profile import ProfileDetailView
from main.views.profile import NeighborListView
from main.views.login import LoginView
from main.views.logout import LogoutView

# 간소화된 Swagger 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Naver Blog API",
        default_version='v1',
        description="Naver Blog API Documentation",
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # 회원가입 API
    path('signup/', SignupView.as_view(), name='signup'),

    #프로필 관련 API
    path('neighbors/', NeighborListView.as_view(), name='neighbor-list'),  # 이웃 목록 조회
    path('profile/me/', ProfileDetailView.as_view(), name='profile-me'), # 내 프로필 조회, 수정, 삭제

    # 로그인 및 로그아웃 API
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Swagger 경로
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

