from rest_framework import serializers
from .models import GespLevel, Chapter, KnowledgePoint


class KnowledgePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgePoint
        fields = ['id', 'name', 'description', 'sort_order']


class KnowledgePointDetailSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    level_name = serializers.CharField(source='chapter.level.name', read_only=True)

    class Meta:
        model = KnowledgePoint
        fields = ['id', 'name', 'description', 'content', 'sort_order', 'chapter_name', 'level_name']


class ChapterSerializer(serializers.ModelSerializer):
    points = KnowledgePointSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = ['id', 'name', 'sort_order', 'points']


class GespLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GespLevel
        fields = ['id', 'name', 'description', 'exam_duration', 'total_questions', 'pass_score']


class KnowledgeTreeSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = GespLevel
        fields = ['id', 'name', 'chapters']


class KnowledgeContentUpdateSerializer(serializers.Serializer):
    content = serializers.CharField()
