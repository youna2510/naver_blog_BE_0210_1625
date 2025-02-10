from rest_framework import serializers
from main.models import CustomUser

class SignupSerializer(serializers.ModelSerializer):
    # 'password' 필드를 write-only로 설정하여 패스워드를 클라이언트에게만 전송하도록 설정
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'password', 'groups', 'user_permissions']  # id, password, groups, user_permissions 필드만 포함

    def create(self, validated_data):
        # 패스워드가 포함된 데이터를 받아서 사용자를 생성
        password = validated_data.pop('password')  # 패스워드 값을 추출
        user = CustomUser(**validated_data)  # 나머지 데이터로 사용자 객체 생성
        user.set_password(password)  # 패스워드를 해시 처리
        user.save()  # 사용자 저장
        return user
