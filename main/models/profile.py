from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # CustomUser 모델과 연결
        on_delete=models.CASCADE,
        related_name='profile'
    )
    blog_name = models.CharField(max_length=20, blank=True)
    blog_pic = models.ImageField(upload_to='blog_pics/', null=True, blank=True, default=None)
    username = models.CharField(max_length=10, blank=True)
    user_pic = models.ImageField(upload_to='user_pics/', null=True, blank=True, default=None)
    neighbors = models.JSONField(default=list, blank=True)  # 이웃 리스트를 JSON 필드로 저장

    def __str__(self):
        return f"{self.user.id} - Profile"
