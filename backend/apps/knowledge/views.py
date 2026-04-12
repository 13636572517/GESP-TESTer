from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import GespLevel, Chapter, KnowledgePoint
from .serializers import (
    GespLevelSerializer, ChapterSerializer,
    KnowledgePointSerializer, KnowledgePointDetailSerializer,
    KnowledgeTreeSerializer, KnowledgeContentUpdateSerializer,
)


class LevelListView(generics.ListAPIView):
    queryset = GespLevel.objects.all()
    serializer_class = GespLevelSerializer
    permission_classes = [AllowAny]


class ChapterListView(generics.ListAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Chapter.objects.filter(level_id=self.kwargs['level_id']).prefetch_related('points')


class KnowledgePointListView(generics.ListAPIView):
    serializer_class = KnowledgePointSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return KnowledgePoint.objects.filter(chapter_id=self.kwargs['chapter_id'])


class KnowledgePointDetailView(generics.RetrieveAPIView):
    queryset = KnowledgePoint.objects.select_related('chapter__level')
    serializer_class = KnowledgePointDetailSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def knowledge_tree(request):
    levels = GespLevel.objects.prefetch_related('chapters__points').all()
    serializer = KnowledgeTreeSerializer(levels, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_knowledge_content(request, pk):
    """管理员编辑知识点讲解内容"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
        return Response({'detail': '无权限'}, status=403)

    try:
        point = KnowledgePoint.objects.get(pk=pk)
    except KnowledgePoint.DoesNotExist:
        return Response({'detail': '知识点不存在'}, status=404)

    serializer = KnowledgeContentUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    point.content = serializer.validated_data['content']
    point.save(update_fields=['content'])
    return Response({'detail': '更新成功'})
