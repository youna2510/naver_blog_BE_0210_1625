from rest_framework import serializers
from ..models.post import Post, PostText, PostImage


class PostTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostText
        fields = ['id', 'content', 'font', 'font_size', 'is_bold']


class PostImageSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'caption','is_representative']


class PostSerializer(serializers.ModelSerializer):
    texts = PostTextSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.profile.username', read_only=True)
    visibility = serializers.ChoiceField(choices=Post.VISIBILITY_CHOICES)
    class Meta:
        model = Post
        fields = ['id', 'author_name', 'title', 'category', 'visibility', 'is_complete', 'texts', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author_name', 'created_at', 'updated_at']

