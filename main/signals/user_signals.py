from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from ..models.profile import Profile

#장고의 signals를 사용
#새로운 사용자(User) 객체가 생성되었을 때 자동으로 해당 사용자와 연결된 Profile 객체를 생성하도록 설정
#사용자가 회원가입 시 자동으로 프로필을 생성하는 데 유용

#Signals: Django에서 특정 이벤트(예: 모델 저장, 삭제 등)가 발생했을 때 자동으로 실행되는 로직을 정의하는 데 사용
#post_save: 특정 모델의 인스턴스가 저장된 이후에 호출되는 신호
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs): #sender: 여기서는 customuser
    if created:  # 새 유저가 생성된 경우
        Profile.objects.create(
            user=instance, #user를 instance(생성된 사용자 객체)와 연결
            blog_name=f"{instance.id}님의 블로그",
            username=instance.id
        )
