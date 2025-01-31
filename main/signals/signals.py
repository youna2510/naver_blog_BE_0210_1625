from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from main.models.profile import Profile
from main.models.comment import Comment



# 🚀 로그 확인용: signals.py가 실행되는지 확인
print("✅ signals/signals.py 로드됨!")


# 🛠 새로운 사용자가 생성될 때 자동으로 Profile 생성
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            blog_name=f"{instance.id}님의 블로그",
            username=instance.id
        )
        print(f"🚀 프로필 생성됨: {instance.id}님의 블로그")  # ✅ 확인용 로그

# ✅ 프로필 변경 전에 기존 값을 저장하는 딕셔너리
old_usernames = {}

@receiver(pre_save, sender=Profile)
def store_old_username(sender, instance, **kwargs):
    """ ✅ 프로필이 변경되기 전에 기존 username 저장 """
    try:
        old_instance = Profile.objects.get(pk=instance.pk)
        old_usernames[instance.pk] = old_instance.username  # ✅ 기존 username 저장
    except Profile.DoesNotExist:
        old_usernames[instance.pk] = None  # 새 프로필인 경우

@receiver(post_save, sender=Profile)
def update_comment_author_name(sender, instance, **kwargs):
    """ ✅ 프로필의 username이 변경되었을 경우, 기존 댓글의 author_name을 업데이트 """
    old_username = old_usernames.get(instance.pk)

    if old_username and old_username != instance.username:
        print(f"🚀 username 변경됨: {old_username} -> {instance.username}")  # ✅ 변경 확인 로그

        # ✅ 기존 댓글을 찾아 author_name을 업데이트
        comments = Comment.objects.filter(author=instance)
        for comment in comments:
            print(f"🔄 댓글 {comment.id} 업데이트 전 author_name: {comment.author_name}")  # ✅ 디버깅용
            comment.author_name = instance.username
            comment.save()  # ✅ 개별 저장
            print(f"✅ 댓글 {comment.id} 업데이트 후 author_name: {comment.author_name}")  # ✅ 디버깅용

        print(f"✅ {instance.username}의 기존 댓글 {comments.count()}개 author_name 자동 업데이트 완료")  # ✅ 업데이트 확인 로그

        # ✅ 업데이트 후 기존 데이터 삭제
        del old_usernames[instance.pk]