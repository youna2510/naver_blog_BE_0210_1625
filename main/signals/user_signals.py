from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from ..models.profile import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:  # 새 유저가 생성된 경우
        Profile.objects.create(
            user=instance,
            blog_name=f"{instance.id}님의 블로그",
            username=instance.id
        )
