from rest_framework import serializers
from ..models.profile import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['blog_name', 'blog_pic', 'username', 'user_pic', 'neighbors']
        read_only_fields = []  # 수정 가능한 상태로 설정

    def validate_blog_name(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("블로그 이름은 최소 1자 이상이어야 합니다.")
        return value

    def validate_username(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("사용자 이름은 최소 1자 이상이어야 합니다.")
        return value
