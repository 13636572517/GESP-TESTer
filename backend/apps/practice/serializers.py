from rest_framework import serializers
from .models import PracticeSession, PracticeAnswer, MistakeRecord
from apps.questions.serializers import QuestionBriefSerializer, QuestionSerializer


class StartPracticeSerializer(serializers.Serializer):
    session_type = serializers.ChoiceField(choices=[1, 2, 3])
    level_id = serializers.IntegerField(required=False, allow_null=True)
    knowledge_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    count = serializers.IntegerField(min_value=1, max_value=100, default=20)
    difficulty = serializers.IntegerField(required=False, allow_null=True)


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(max_length=10)
    time_spent = serializers.IntegerField(min_value=0, default=0)


class PracticeAnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = PracticeAnswer
        fields = ['id', 'question', 'user_answer', 'is_correct', 'time_spent']


class PracticeSessionSerializer(serializers.ModelSerializer):
    accuracy = serializers.SerializerMethodField()

    class Meta:
        model = PracticeSession
        fields = ['id', 'session_type', 'level', 'total_count', 'correct_count', 'accuracy', 'finished_at', 'created_at']

    def get_accuracy(self, obj):
        if obj.total_count == 0:
            return 0
        return round(obj.correct_count / obj.total_count * 100, 1)


class MistakeRecordSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = MistakeRecord
        fields = [
            'id', 'question', 'wrong_count', 'last_wrong_answer',
            'is_mastered', 'consecutive_correct', 'last_practiced_at',
        ]
