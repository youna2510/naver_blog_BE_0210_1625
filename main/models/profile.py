from django.db import models
from django.conf import settings
import os

# 업로드 경로를 처리하는 함수
def blog_pic_upload_path(instance, filename):
    return f"blog_pics/{instance.user.id}/{filename}"

def user_pic_upload_path(instance, filename):
    return f"user_pics/{instance.user.id}/{filename}"

# Profile: 사용자(CustomUser)와 연결된 추가적인 프로필 정보를 저장
class Profile(models.Model):
    user = models.OneToOneField(  # 사용자와 1대 1로 연결
        settings.AUTH_USER_MODEL,  # CustomUser 모델과 연결
        on_delete=models.CASCADE,  # 사용자가 삭제되면 해당 Profile도 삭제됨
        related_name='profile'  # 역참조 시 user.profile로 접근 가능
    )
    blog_name = models.CharField(max_length=20)
    blog_pic = models.ImageField(
        upload_to=blog_pic_upload_path,
        null=True,
        blank=True,
        default='default/blog_default.jpg'  # 기본 블로그 사진 경로
    )
    username = models.CharField(max_length=15)
    user_pic = models.ImageField(
        upload_to=user_pic_upload_path,
        null=True,
        blank=True,
        default='default/user_default.jpg'  # 기본 프로필 사진 경로
    )

    def __str__(self):
        return f"{self.user.id} - Profile"

    def save(self, *args, **kwargs):
        # 기존 이미지 파일 삭제 로직: 새 이미지로 대체하거나 기본 이미지로 변경 시
        if self.pk:  # 기존 인스턴스가 있는 경우
            old_instance = Profile.objects.get(pk=self.pk)
            # blog_pic 변경 시 기존 파일 삭제
            if old_instance.blog_pic and old_instance.blog_pic != self.blog_pic:
                if old_instance.blog_pic.name != 'default/blog_default.jpg':
                    old_instance.blog_pic.delete(save=False)
            # user_pic 변경 시 기존 파일 삭제
            if old_instance.user_pic and old_instance.user_pic != self.user_pic:
                if old_instance.user_pic.name != 'default/user_default.jpg':
                    old_instance.user_pic.delete(save=False)

        # 기본 이미지로 재설정
        if not self.blog_pic:
            self.blog_pic = 'default/blog_default.jpg'
        if not self.user_pic:
            self.user_pic = 'default/user_default.jpg'

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("프로필은 삭제할 수 없습니다.")