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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    blog_name = models.CharField(max_length=20)
    blog_pic = models.ImageField(
        upload_to=blog_pic_upload_path,
        null=True,
        blank=True,
        default='default/blog_default.jpg'
    )
    username = models.CharField(max_length=15)
    user_pic = models.ImageField(
        upload_to=user_pic_upload_path,
        null=True,
        blank=True,
        default='default/user_default.jpg'
    )
    intro = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="간단한 자기소개를 입력해주세요 (최대 100자)"
    )

    def __str__(self):
        return f"{self.user.id} - Profile"

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Profile.objects.get(pk=self.pk)
            if old_instance.blog_pic and old_instance.blog_pic != self.blog_pic:
                if old_instance.blog_pic.name != 'default/blog_default.jpg':
                    old_instance.blog_pic.delete(save=False)
            if old_instance.user_pic and old_instance.user_pic != self.user_pic:
                if old_instance.user_pic.name != 'default/user_default.jpg':
                    old_instance.user_pic.delete(save=False)

        if not self.blog_pic:
            self.blog_pic = 'default/blog_default.jpg'
        if not self.user_pic:
            self.user_pic = 'default/user_default.jpg'

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("프로필은 삭제할 수 없습니다.")