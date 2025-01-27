from django.db import models
from django.conf import settings
from slugify import slugify


def image_upload_path(instance, filename):
    """
    이미지 업로드 경로 설정.
    경로: main/media/post_pics/{user_id}/{category}/{title}/{filename}
    """
    user_id = instance.post.author.id
    category = slugify(instance.post.category)
    title = slugify(instance.post.title)
    return f"main/media/post_pics/{user_id}/{category}/{title}/{filename}"


class Post(models.Model):
    VISIBILITY_CHOICES = [
        ('everyone', '전체 공개'),
        ('mutual', '서로 이웃만 공개'),
    ]

    COMPLETE_CHOICES = [
        ('true', '작성 완료'),
        ('false', '임시 저장'),
    ]

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    category = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='everyone',
        verbose_name="공개 범위"
    )
    is_complete = models.CharField(
        max_length=5,
        choices=COMPLETE_CHOICES,
        default='false',  # 기본값은 임시 저장
        verbose_name="작성 상태"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} / {self.title} / {dict(self.COMPLETE_CHOICES).get(self.is_complete)}"


class PostText(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="texts")
    content = models.TextField()

    def __str__(self):
        return f"Text for {self.post.title}"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=image_upload_path)
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_representative = models.BooleanField(default=False, verbose_name="대표 사진 여부")

    def __str__(self):
        return f"Image for {self.post.title} (Representative: {self.is_representative})"
