from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# CustomUserManager 정의
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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(id, password, **extra_fields)


# CustomUser 모델 정의
class CustomUser(AbstractUser):
    username = None  # username 필드 제거
    id = models.CharField(max_length=50, unique=True, primary_key=True)  # 고유 ID 필드 추가

    first_name = None  # 필요 없는 필드 제거
    last_name = None
    email = None

    objects = CustomUserManager()

    USERNAME_FIELD = 'id'  # 로그인에 사용할 필드
    REQUIRED_FIELDS = []  # 추가 필수 필드를 비워둠

    def __str__(self):
        return self.id
