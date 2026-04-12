from rest_framework import serializers
from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    knowledge_point_ids = serializers.PrimaryKeyRelatedField(
        source='knowledge_points', many=True, read_only=True
    )

    class Meta:
        model = Question
        fields = [
            'id', 'level', 'level_name', 'question_type', 'type_display',
            'difficulty', 'difficulty_display', 'content', 'options',
            'answer', 'explanation', 'source', 'knowledge_point_ids',
            'is_active', 'created_at',
        ]


class QuestionCreateSerializer(serializers.ModelSerializer):
    knowledge_point_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )

    class Meta:
        model = Question
        fields = [
            'level', 'question_type', 'difficulty', 'content', 'options',
            'answer', 'explanation', 'source', 'knowledge_point_ids',
        ]

    def create(self, validated_data):
        kp_ids = validated_data.pop('knowledge_point_ids', [])
        validated_data['created_by'] = self.context['request'].user
        question = Question.objects.create(**validated_data)
        if kp_ids:
            question.knowledge_points.set(kp_ids)
        return question

    def update(self, instance, validated_data):
        kp_ids = validated_data.pop('knowledge_point_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if kp_ids is not None:
            instance.knowledge_points.set(kp_ids)
        return instance


class QuestionBriefSerializer(serializers.ModelSerializer):
    """练习/考试中展示的题目（不含答案）"""
    type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'question_type', 'type_display', 'content', 'options']
