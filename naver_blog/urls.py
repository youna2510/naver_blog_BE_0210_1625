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
from django.urls import path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from main.views.signup import SignupView
from main.views.login import LoginView
from main.views.logout import LogoutView
from main.views.profile import ProfileDetailView, ProfilePublicView, ProfileUrlnameUpdateView
from main.views.post import PostDetailView,PostListView,DraftPostListView,DraftPostDetailView
from main.views.comment import CommentListView, CommentDetailView
from main.views.heart import ToggleHeartView, PostHeartUsersView, PostHeartCountView
from main.views.commentHeart import ToggleCommentHeartView, CommentHeartCountView
from main.views.neighbor import NeighborView,NeighborAcceptView,NeighborRejectView,NeighborRequestListView,PublicNeighborListView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

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

    # ✅ 회원가입 API
    path('signup/', SignupView.as_view(), name='signup'),

    # ✅ 내 프로필 관련 API
    path('profile/me/', ProfileDetailView.as_view(), name='profile-me'),  # 내 프로필 조회, 수정, 삭제
    path('profile/urlname/', ProfileUrlnameUpdateView.as_view(), name='profile-urlname-update'),  # urlname 변경 (한 번만 가능)

    # ✅ 타인 프로필 관련 API
    path('profile/<str:user_id>/', ProfilePublicView.as_view(), name='profile-public'),
    path('profile/<str:user_id>/neighbors/', PublicNeighborListView.as_view(), name='neighbor-list'),

    # ✅ 로그인 및 로그아웃 API
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # ✅ 서로이웃 관련 API
    path('neighbors/<str:to_user_id>/', NeighborView.as_view(), name='neighbor-request'),
    path('neighbors/requests/me', NeighborRequestListView.as_view(), name='neighbor-request-list'),
    path('neighbors/accept/<str:from_user_id>/', NeighborAcceptView.as_view(), name='neighbor-accept'),
    path('neighbors/reject/<str:from_user_id>/', NeighborRejectView.as_view(), name='neighbor-reject'),

    # ✅ 게시물 API (urlname 추가)
    path('posts/', PostListView.as_view(), name='post_list'),  # 특정 유저 게시물 조회 및 작성
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post_detail'),  # 특정 게시물 상세 조회, 수정, 삭제

    # ✅ 임시 저장된 게시물 API (urlname 추가)
    path('posts/drafts/', DraftPostListView.as_view(), name='draft_post_list'),  # 임시 저장된 게시물 목록 조회
    path('posts/drafts/<int:pk>/', DraftPostDetailView.as_view(), name='draft_post_detail'),
    # 특정 임시 저장 게시물 상세 조회

    # ✅ 특정 게시글의 댓글 목록 조회 & 댓글 작성
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # ✅ 공감(좋아요) 관련 API (urlname 추가)

    # 게시글 좋아요 추가/삭제
    path('posts/<int:post_id>/heart/', ToggleHeartView.as_view(), name='toggle-heart'),
    # 게시글 좋아요 누른 유저 목록 조회
    path('posts/<int:post_id>/heart/users/', PostHeartUsersView.as_view(), name='post-heart-users'),
    # 게시글 좋아요 개수 조회
    path('posts/<int:post_id>/heart/count/', PostHeartCountView.as_view(), name='post-heart-count'),

    # 댓글/대댓글 좋아요 추가/삭제 (`urlname` 포함)
    path('posts/<int:post_id>/comments/<int:comment_id>/heart/', ToggleCommentHeartView.as_view(),
         name='toggle-comment-heart'),
    # 댓글/대댓글 좋아요 개수 조회 (`urlname` 포함)
    path('posts/<int:post_id>/comments/<int:comment_id>/heart/count/', CommentHeartCountView.as_view(),
         name='comment-heart-count'),

    # ✅ Swagger 경로
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 미디어 파일 처리 (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)