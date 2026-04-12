from django.core.management.base import BaseCommand
from apps.knowledge.models import GespLevel, Chapter, KnowledgePoint

GESP_DATA = {
    1: {
        'name': 'GESP一级',
        'description': 'C++入门基础',
        'chapters': {
            '计算机基础知识': [
                '计算机的组成', '操作系统基础', '文件与文件夹管理',
            ],
            'C++编程环境': [
                '开发环境搭建', '程序的编译与运行', '代码编辑器的使用',
            ],
            '基本输入输出': [
                'cout输出', 'cin输入', '转义字符',
            ],
            '变量与数据类型': [
                '整型(int)', '浮点型(float/double)', '字符型(char)',
                '变量的定义与赋值', '常量',
            ],
            '运算符与表达式': [
                '算术运算符', '赋值运算符', '关系运算符',
                '表达式求值', '类型转换',
            ],
            '顺序结构': [
                '顺序执行', '简单程序编写',
            ],
        },
    },
    2: {
        'name': 'GESP二级',
        'description': '分支与循环',
        'chapters': {
            '分支结构': [
                'if语句', 'if-else语句', 'if-else if语句',
                'switch语句', '条件运算符',
            ],
            '循环结构': [
                'for循环', 'while循环', 'do-while循环',
                '循环嵌套', 'break与continue',
            ],
            '逻辑运算': [
                '逻辑与(&&)', '逻辑或(||)', '逻辑非(!)',
                '短路求值',
            ],
            '简单应用': [
                '计数问题', '求和问题', '最值问题',
                '数字处理(位数分离)',
            ],
        },
    },
    3: {
        'name': 'GESP三级',
        'description': '数组与函数',
        'chapters': {
            '一维数组': [
                '数组的定义与初始化', '数组元素的访问', '数组的遍历',
                '数组的查找', '数组的排序(冒泡排序)',
            ],
            '二维数组': [
                '二维数组的定义', '二维数组的遍历', '矩阵运算',
            ],
            '字符数组与字符串': [
                '字符数组', 'C风格字符串', 'string类基础',
                '字符串常用操作',
            ],
            '函数': [
                '函数的定义与调用', '函数参数', '函数返回值',
                '函数重载', '递归入门',
            ],
        },
    },
    4: {
        'name': 'GESP四级',
        'description': '递归与排序',
        'chapters': {
            '递归': [
                '递归的概念', '递归与数学问题', '递归与分治',
                '递归的优化',
            ],
            '排序算法': [
                '选择排序', '插入排序', '快速排序',
                '归并排序', '排序的稳定性与复杂度',
            ],
            '查找算法': [
                '线性查找', '二分查找', '查找的应用',
            ],
            '结构体': [
                '结构体定义', '结构体数组', '结构体作为函数参数',
            ],
        },
    },
    5: {
        'name': 'GESP五级',
        'description': '指针与链表',
        'chapters': {
            '指针基础': [
                '指针的概念', '指针的定义与使用', '指针与数组',
                '指针与函数', '动态内存分配',
            ],
            '链表': [
                '单链表的概念', '链表的创建与遍历', '链表的插入与删除',
                '链表的应用',
            ],
            'STL入门': [
                'vector容器', 'string类深入', 'stack和queue',
                '排序与查找函数',
            ],
            '时间复杂度分析': [
                '大O表示法', '常见时间复杂度', '空间复杂度',
            ],
        },
    },
    6: {
        'name': 'GESP六级',
        'description': '树与图基础',
        'chapters': {
            '树的基础': [
                '树的概念与术语', '二叉树', '二叉树的遍历',
                '二叉搜索树',
            ],
            '堆': [
                '堆的概念', '堆的建立与维护', '堆排序',
                '优先队列',
            ],
            '图的基础': [
                '图的概念与表示', '邻接矩阵', '邻接表',
                '图的遍历(DFS/BFS)',
            ],
            'STL进阶': [
                'map和set', 'pair和tuple', '迭代器',
                '常用算法函数',
            ],
        },
    },
    7: {
        'name': 'GESP七级',
        'description': '动态规划与图算法',
        'chapters': {
            '动态规划基础': [
                '动态规划的概念', '最优子结构', '状态转移方程',
                '背包问题', '最长公共子序列',
            ],
            '图的高级算法': [
                '最短路径(Dijkstra)', '最短路径(Floyd)',
                '最小生成树(Prim/Kruskal)', '拓扑排序',
            ],
            '贪心算法': [
                '贪心策略', '活动选择问题', '哈夫曼编码',
            ],
            '高级数据结构': [
                '并查集', '树状数组', '线段树入门',
            ],
        },
    },
    8: {
        'name': 'GESP八级',
        'description': '高级算法与综合应用',
        'chapters': {
            '动态规划进阶': [
                '区间DP', '树形DP', '状态压缩DP',
                '数位DP',
            ],
            '字符串算法': [
                'KMP算法', '字典树(Trie)', '字符串哈希',
            ],
            '数学算法': [
                '素数筛法', '最大公约数', '快速幂',
                '组合数学基础', '容斥原理',
            ],
            '综合应用': [
                '复杂模拟题', '综合算法设计', '竞赛题训练',
            ],
        },
    },
}


class Command(BaseCommand):
    help = '预置GESP知识点大纲数据'

    def handle(self, *args, **options):
        for level_id, level_data in GESP_DATA.items():
            level, _ = GespLevel.objects.update_or_create(
                id=level_id,
                defaults={
                    'name': level_data['name'],
                    'description': level_data['description'],
                },
            )
            self.stdout.write(f'  级别: {level.name}')

            for ch_order, (ch_name, points) in enumerate(level_data['chapters'].items()):
                chapter, _ = Chapter.objects.update_or_create(
                    level=level,
                    name=ch_name,
                    defaults={'sort_order': ch_order},
                )

                for pt_order, pt_name in enumerate(points):
                    KnowledgePoint.objects.update_or_create(
                        chapter=chapter,
                        name=pt_name,
                        defaults={'sort_order': pt_order},
                    )

        total_points = KnowledgePoint.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'完成！共创建 8 个级别，{Chapter.objects.count()} 个章节，{total_points} 个知识点'
        ))
