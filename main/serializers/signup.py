from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'password', 'password_confirm']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        # 비밀번호와 비밀번호 확인 일치 여부 확인
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data

    def create(self, validated_data):
        # password_confirm은 DB에 저장하지 않음
        validated_data.pop('password_confirm')
        validated_data['password'] = make_password(validated_data['password'])  # 비밀번호 암호화
        user = User.objects.create(**validated_data)
        return user
