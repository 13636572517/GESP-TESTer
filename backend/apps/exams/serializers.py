from rest_framework import serializers
from .models import ExamTemplate, ExamTemplateQuestion, ExamRecord, ExamAnswer
from apps.questions.serializers import QuestionBriefSerializer, QuestionSerializer


class ExamTemplateQuestionSerializer(serializers.ModelSerializer):
    question = QuestionBriefSerializer(read_only=True)

    class Meta:
        model = ExamTemplateQuestion
        fields = ['id', 'question', 'score', 'sort_order']


class ExamTemplateSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = ExamTemplate
        fields = [
            'id', 'name', 'level', 'level_name', 'duration',
            'total_score', 'pass_score', 'template_type',
            'question_count', 'is_active',
        ]

    def get_question_count(self, obj):
        return obj.template_questions.count()


class ExamTemplateCreateSerializer(serializers.ModelSerializer):
    question_items = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = ExamTemplate
        fields = ['name', 'level', 'duration', 'total_score', 'pass_score', 'template_type', 'question_items']

    def create(self, validated_data):
        items = validated_data.pop('question_items', [])
        template = ExamTemplate.objects.create(**validated_data)
        for i, item in enumerate(items):
            ExamTemplateQuestion.objects.create(
                template=template,
                question_id=item['question_id'],
                score=item.get('score', 2),
                sort_order=i,
            )
        return template


class SaveAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(max_length=10, allow_blank=True)
    time_spent = serializers.IntegerField(min_value=0, default=0)


class ExamAnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ExamAnswer
        fields = ['id', 'question', 'user_answer', 'is_correct', 'score', 'time_spent']


class ExamRecordSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True, default='')

    class Meta:
        model = ExamRecord
        fields = [
            'id', 'template', 'template_name', 'level', 'level_name',
            'exam_type', 'duration', 'start_time', 'end_time',
            'total_score', 'earned_score', 'status', 'switch_count',
        ]
