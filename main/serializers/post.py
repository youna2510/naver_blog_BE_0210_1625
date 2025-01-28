from rest_framework import serializers
from ..models.post import Post, PostText, PostImage


class PostTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostText
        fields = ['id', 'content']  # 'id' 필드를 추가


class PostImageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'caption','is_representative']


class PostSerializer(serializers.ModelSerializer):
    texts = PostTextSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source='author.id')

    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'category', 'visibility', 'is_complete', 'texts', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

