from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth.models import Group, Permission

# 사용자 관리 클래스
class CustomUserManager(BaseUserManager):
    def create_user(self, id, password=None, **extra_fields):
        if not id:
            raise ValueError("The ID field must be set")
        if not password:
            raise ValueError("The password field must be set")
        user = self.model(id=id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(id, password, **extra_fields)

# 사용자 모델
class CustomUser(AbstractUser):
    # 기본적으로 제공되는 username, first_name, last_name, email 필드는 사용하지 않음
    id = models.CharField(
        max_length=50,
        unique=True,  # 유니크 제약
        primary_key=True,  # 기본 키로 설정
        error_messages={
            'unique': '아이디가 중복되었습니다. 다시 입력해주세요.'  # 아이디 중복 에러 메시지
        }
    )
    username = None  # 사용하지 않음
    first_name = None  # 사용하지 않음
    last_name = None  # 사용하지 않음
    email = None  # 사용하지 않음

    # Group과 Permission과의 관계 설정
    groups = models.ManyToManyField(
        Group,
        blank=True,  # 기본적으로 빈 값 허용
        related_name="customuser_set",  # 'groups'와의 관계에 대한 이름 설정
        related_query_name="customuser"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="customuser_set",  # 'permissions'와의 관계에 대한 이름 설정
        related_query_name="customuser"
    )

    # 사용자 관리 객체
    objects = CustomUserManager()

    # 'id' 필드를 사용자 인증에 사용
    USERNAME_FIELD = 'id'  # 인증에 'id' 필드를 사용
    REQUIRED_FIELDS = []  # 추가 필드는 없음

    def __str__(self):
        return self.id
