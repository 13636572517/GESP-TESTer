from rest_framework import serializers
from .models import UserKnowledgeMastery, DailyStudyLog


class MasterySerializer(serializers.ModelSerializer):
    knowledge_name = serializers.CharField(source='knowledge.name', read_only=True)
    chapter_name = serializers.CharField(source='knowledge.chapter.name', read_only=True)
    level_id = serializers.IntegerField(source='knowledge.chapter.level_id', read_only=True)
    accuracy = serializers.SerializerMethodField()

    class Meta:
        model = UserKnowledgeMastery
        fields = [
            'knowledge', 'knowledge_name', 'chapter_name', 'level_id',
            'total_attempts', 'correct_count', 'mastery_level', 'accuracy',
            'last_practiced',
        ]

    def get_accuracy(self, obj):
        if obj.total_attempts == 0:
            return 0
        return round(obj.correct_count / obj.total_attempts * 100, 1)


class DailyStudyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStudyLog
        fields = ['study_date', 'practice_count', 'correct_count', 'exam_count', 'study_minutes']
