from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    #사용자가 비밀번호를 확인할 때 사용하는 필드, wirte_only: 클라이언트가 데이터를 입력할 때만 사용
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User #user 모델과 매핑
        fields = ['id', 'password', 'password_confirm']
        extra_kwargs = {
            'password': {'write_only': True}, # password는 응답에서 제외
        }
    ## 비밀번호와 비밀번호 확인 일치 여부 확인하는 메서드
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data
    #검증된 데이터를 사용해 새로운 user 객체 생성하여 반환
    def create(self, validated_data):
        # password_confirm은 DB에 저장하지 않음
        validated_data.pop('password_confirm')
        validated_data['password'] = make_password(validated_data['password'])  # 비밀번호 암호화
        user = User.objects.create(**validated_data)
        return user
