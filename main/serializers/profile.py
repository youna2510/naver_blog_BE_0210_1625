from rest_framework import serializers
from ..models.profile import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['blog_name', 'blog_pic', 'username', 'user_pic', 'intro']  # intro 필드 추가
        extra_kwargs = {
            'blog_pic': {'required': False, 'allow_null': True},
            'user_pic': {'required': False, 'allow_null': True},
            'intro': {'required': False, 'allow_blank': True}  # intro는 선택사항
        }

    def validate_blog_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("블로그 이름은 공백일 수 없습니다.")
        if len(value) > 20:
            raise serializers.ValidationError("블로그 이름은 최대 20자까지 입력 가능합니다.")
        return value

    def validate_username(self, value):
        if not value.strip():
            raise serializers.ValidationError("사용자 이름은 공백일 수 없습니다.")
        if len(value) > 15:
            raise serializers.ValidationError("사용자 이름은 최대 15자까지 입력 가능합니다.")
        return value

    def validate_blog_pic(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("블로그 사진은 5MB 이하의 파일만 업로드할 수 있습니다.")
            if value.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError("블로그 사진은 JPEG 또는 PNG 형식만 지원됩니다.")
        return value

    def validate_user_pic(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("프로필 사진은 5MB 이하의 파일만 업로드할 수 있습니다.")
            if value.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError("프로필 사진은 JPEG 또는 PNG 형식만 지원됩니다.")
        return value

    def validate_intro(self, value):  # intro 유효성 검사
        if value and len(value) > 100:
            raise serializers.ValidationError("자기소개는 최대 100자까지 입력 가능합니다.")
        return value
        if len(value) > 15:
            raise serializers.ValidationError("사용자 이름은 최대 15자까지 입력 가능합니다.")
        return value

    # 블로그 이미지 유효성 검증
    def validate_blog_pic(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB 크기 제한
                raise serializers.ValidationError("블로그 사진은 5MB 이하의 파일만 업로드할 수 있습니다.")
            if value.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError("블로그 사진은 JPEG 또는 PNG 형식만 지원됩니다.")
        return value

    # 프로필 이미지 유효성 검증
    def validate_user_pic(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB 크기 제한
                raise serializers.ValidationError("프로필 사진은 5MB 이하의 파일만 업로드할 수 있습니다.")
            if value.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError("프로필 사진은 JPEG 또는 PNG 형식만 지원됩니다.")
        return value


