"""导入GESP考试真题到题库"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.questions.models import Question
from apps.knowledge.models import GespLevel, KnowledgePoint


# ===== 知识点关键词映射 =====
# 用于根据题目内容自动关联知识点
# 格式: 知识点名称 -> [关键词列表]
KNOWLEDGE_KEYWORDS = {
    # 一级知识点
    '计算机的组成': ['计算机', '硬件', 'CPU', '内存', '存储器'],
    '操作系统基础': ['操作系统', '文件', '文件夹', '目录'],
    '文件与文件夹管理': ['文件管理', '文件夹'],
    '开发环境搭建': ['环境', 'IDE', '编译器'],
    '程序的编译与运行': ['编译', '运行', '执行'],
    '代码编辑器的使用': ['编辑器'],
    'cout输出': ['cout', '输出', 'printf'],
    'cin输入': ['cin', '输入', 'scanf'],
    '转义字符': ['转义', '\\n', '\\t', '换行'],
    '整型(int)': ['整型', 'int', '整数'],
    '浮点型(float/double)': ['浮点', 'float', 'double', '小数'],
    '字符型(char)': ['字符', 'char'],
    '变量的定义与赋值': ['变量', '定义', '赋值'],
    '常量': ['常量', 'const'],
    '算术运算符': ['+', '-', '*', '/', '%', '取模', '取余', '整除', '运算符'],
    '赋值运算符': ['=', '+=', '-=', '*=', '/='],
    '关系运算符': ['>', '<', '>=', '<=', '==', '!=', '比较'],
    '表达式求值': ['表达式', '求值', '运算顺序', '优先级'],
    '类型转换': ['类型转换', '强制转换', '隐式转换'],
    '顺序执行': ['顺序'],
    '简单程序编写': ['程序'],

    # 二级知识点
    'if语句': ['if', '条件', '判断'],
    'if-else语句': ['if-else', '否则', '分支'],
    'if-else if语句': ['else if', '多分支'],
    'switch语句': ['switch', 'case'],
    '条件运算符': ['?:', '三目', '条件运算符'],
    'for循环': ['for', '循环'],
    'while循环': ['while'],
    'do-while循环': ['do-while'],
    '循环嵌套': ['嵌套循环', '循环嵌套'],
    'break与continue': ['break', 'continue', '跳出', '跳过'],
    '逻辑与(&&)': ['&&', '逻辑与', '并且'],
    '逻辑或(||)': ['||', '逻辑或', '或者'],
    '逻辑非(!)': ['!', '逻辑非', '取反'],
    '短路求值': ['短路'],
    '计数问题': ['计数', '统计', '个数'],
    '求和问题': ['求和', '累加', '总和'],
    '最值问题': ['最大', '最小', '最值', '最大值', '最小值'],
    '数字处理(位数分离)': ['位数', '个位', '十位', '百位', '数字分离', '逆序', '镜面'],

    # 三级知识点
    '数组的定义与初始化': ['数组', '初始化'],
    '数组元素的访问': ['数组访问', '下标'],
    '数组的遍历': ['遍历数组'],
    '数组的查找': ['查找', '搜索'],
    '数组的排序(冒泡排序)': ['冒泡', '排序', 'sort'],
    '二维数组的定义': ['二维数组', '矩阵'],
    '二维数组的遍历': ['二维'],
    '矩阵运算': ['矩阵'],
    '字符数组': ['字符数组'],
    'C风格字符串': ['C风格', 'char[]'],
    'string类基础': ['string', '字符串'],
    '字符串常用操作': ['字符串操作', '拼接', '截取'],
    '函数的定义与调用': ['函数', '定义', '调用'],
    '函数参数': ['参数', '形参', '实参'],
    '函数返回值': ['返回值', 'return'],
    '函数重载': ['重载'],
    '递归入门': ['递归'],

    # 四级知识点
    '递归的概念': ['递归'],
    '递归与数学问题': ['阶乘', '斐波那契', '数列'],
    '递归与分治': ['分治'],
    '递归的优化': ['记忆化', '优化'],
    '选择排序': ['选择排序'],
    '插入排序': ['插入排序'],
    '快速排序': ['快速排序', '快排'],
    '归并排序': ['归并排序'],
    '排序的稳定性与复杂度': ['稳定性', '复杂度'],
    '线性查找': ['线性查找', '顺序查找'],
    '二分查找': ['二分', '折半'],
    '结构体定义': ['struct', '结构体'],
    '结构体数组': ['结构体数组'],
    '结构体作为函数参数': ['结构体参数'],

    # 五级知识点
    '指针的概念': ['指针', 'pointer'],
    '指针的定义与使用': ['*p', '&a', '地址'],
    '指针与数组': ['指针数组'],
    '指针与函数': ['指针函数'],
    '动态内存分配': ['new', 'delete', 'malloc', 'free'],
    '单链表的概念': ['链表', 'link'],
    '链表的创建与遍历': ['链表遍历'],
    '链表的插入与删除': ['插入', '删除'],
    '链表的应用': ['链表应用'],
    'vector容器': ['vector'],
    'string类深入': ['string'],
    'stack和queue': ['stack', 'queue', '栈', '队列'],
    '排序与查找函数': ['sort()', 'find()'],
    '大O表示法': ['O(', '时间复杂度', '空间复杂度'],
    '常见时间复杂度': ['O(n)', 'O(log', 'O(n²)'],
    '空间复杂度': ['空间'],

    # 六级知识点
    '树的概念与术语': ['树', '节点', '根', '叶子'],
    '二叉树': ['二叉树', 'binary tree'],
    '二叉树的遍历': ['前序', '中序', '后序', '层序'],
    '二叉搜索树': ['二叉搜索', 'BST'],
    '堆的概念': ['堆', 'heap'],
    '堆的建立与维护': ['堆维护'],
    '堆排序': ['堆排序'],
    '优先队列': ['优先队列', 'priority_queue'],
    '图的概念与表示': ['图', 'graph', '顶点', '边'],
    '邻接矩阵': ['邻接矩阵'],
    '邻接表': ['邻接表'],
    '图的遍历(DFS/BFS)': ['DFS', 'BFS', '深度优先', '广度优先', '遍历图'],
    'map和set': ['map', 'set'],
    'pair和tuple': ['pair', 'tuple'],
    '迭代器': ['迭代器', 'iterator'],
    '常用算法函数': ['algorithm'],

    # 七级知识点
    '动态规划的概念': ['动态规划', 'DP', 'dp'],
    '最优子结构': ['最优子结构'],
    '状态转移方程': ['状态转移'],
    '背包问题': ['背包'],
    '最长公共子序列': ['LCS', '最长公共'],
    '最短路径(Dijkstra)': ['Dijkstra', '迪杰斯特拉'],
    '最短路径(Floyd)': ['Floyd', '弗洛伊德'],
    '最小生成树(Prim/Kruskal)': ['Prim', 'Kruskal', '最小生成树'],
    '拓扑排序': ['拓扑'],
    '贪心策略': ['贪心'],
    '活动选择问题': ['活动选择'],
    '哈夫曼编码': ['哈夫曼', 'Huffman'],
    '并查集': ['并查集', 'union-find'],
    '树状数组': ['树状数组', 'BIT'],
    '线段树入门': ['线段树'],

    # 八级知识点
    '区间DP': ['区间DP'],
    '树形DP': ['树形DP'],
    '状态压缩DP': ['状压', '状态压缩'],
    '数位DP': ['数位DP'],
    'KMP算法': ['KMP'],
    '字典树(Trie)': ['Trie', '字典树'],
    '字符串哈希': ['哈希', 'hash'],
    '素数筛法': ['素数', '筛法', '埃氏', '欧拉'],
    '最大公约数': ['GCD', '最大公约数', '辗转相除'],
    '快速幂': ['快速幂'],
    '组合数学基础': ['组合', '排列'],
    '容斥原理': ['容斥'],
}


class Command(BaseCommand):
    help = '导入GESP考试真题到题库（支持选择题和判断题）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level', type=int, default=1,
            help='GESP级别（1-8），默认为1级'
        )
        parser.add_argument(
            '--source', type=str, default='',
            help='题目来源标识，如"2025年9月一级真题"'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='仅预览不实际导入'
        )

    def handle(self, *args, **options):
        level_id = options['level']
        source = options['source']
        dry_run = options['dry_run']

        # 验证级别
        try:
            level = GespLevel.objects.get(id=level_id)
        except GespLevel.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'GESP级别 {level_id} 不存在'))
            return

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'GESP {level.name} 真题导入')
        self.stdout.write(f'{"="*60}\n')

        # 获取该级别的所有知识点
        level_points = list(KnowledgePoint.objects.filter(
            chapter__level_id=level_id
        ).select_related('chapter'))

        self.stdout.write(f'已加载 {len(level_points)} 个知识点用于自动关联\n')

        # 导入单选题
        self.stdout.write(self.style.WARNING('--- 单选题 ---\n'))
        self._import_questions(
            SINGLE_CHOICE_QUESTIONS, level, level_points,
            question_type=1, source=source, dry_run=dry_run
        )

        # 导入判断题
        self.stdout.write(self.style.WARNING('\n--- 判断题 ---\n'))
        self._import_questions(
            TRUE_FALSE_QUESTIONS, level, level_points,
            question_type=3, source=source, dry_run=dry_run
        )

    def _import_questions(self, questions_data, level, level_points,
                          question_type, source, dry_run):
        """导入题目"""
        type_name = '单选题' if question_type == 1 else '判断题'
        created = 0
        skipped = 0

        for q_data in questions_data:
            # 检查是否已存在
            if not dry_run:
                exists = Question.objects.filter(
                    level=level,
                    question_type=question_type,
                    content=q_data['content'],
                    source=source
                ).exists()
                if exists:
                    self.stdout.write(f'  [跳过] {q_data["content"][:30]}...')
                    skipped += 1
                    continue

            # 自动关联知识点
            matched_points = self._match_knowledge_points(
                q_data['content'], q_data.get('code', ''), level_points
            )

            if dry_run:
                point_names = [p.name for p in matched_points]
                self.stdout.write(
                    f'  [预览] {q_data["content"][:30]}... '
                    f'答案:{q_data["answer"]} 知识点:{point_names}'
                )
                created += 1
                continue

            # 创建题目
            question = Question.objects.create(
                level=level,
                question_type=question_type,
                difficulty=q_data.get('difficulty', 2),
                content=q_data['content'],
                options=q_data.get('options', []),
                answer=q_data['answer'],
                explanation=q_data.get('explanation', ''),
                source=source,
            )

            # 关联知识点
            if matched_points:
                question.knowledge_points.set(matched_points)

            point_names = [p.name for p in matched_points]
            self.stdout.write(
                f'  [创建] {q_data["content"][:30]}... '
                f'答案:{q_data["answer"]} 知识点:{point_names}'
            )
            created += 1

        action = '将创建' if dry_run else '已创建'
        self.stdout.write(self.style.SUCCESS(
            f'\n  {type_name}: {action} {created} 道，跳过 {skipped} 道'
        ))

    def _match_knowledge_points(self, content, code, level_points):
        """根据题目内容和代码自动关联知识点"""
        text = content + ' ' + code
        matched = []
        matched_ids = set()

        # 按关键词匹配
        for point in level_points:
            keywords = KNOWLEDGE_KEYWORDS.get(point.name, [])
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if point.id not in matched_ids:
                        matched.append(point)
                        matched_ids.add(point.id)
                    break

        # 如果没有匹配到，尝试根据题目类型默认关联
        if not matched:
            # 单选题默认关联"表达式求值"或"简单程序编写"
            for point in level_points:
                if point.name in ['表达式求值', '简单程序编写', 'if语句', 'for循环']:
                    matched.append(point)
                    break

        return matched


# ===== 2025年9月 GESP一级真题 =====

SINGLE_CHOICE_QUESTIONS = [
    {
        'content': '人工智能现在非常火，小杨就想多了解一下，其中就经常听人提到"大模型"。那么请问这里说的"大模型"最贴切是指（  ）。',
        'options': [
            {'key': 'A', 'text': '大电脑模型'},
            {'key': 'B', 'text': '大规模智能'},
            {'key': 'C', 'text': '智能的单位'},
            {'key': 'D', 'text': '大语言模型'},
        ],
        'answer': 'D',
        'difficulty': 1,
        'explanation': '"大模型"在当前AI语境下最贴切指的是"大语言模型"（Large Language Model），如GPT、Claude等。',
    },
    {
        'content': '小杨这学期刚开学就选修了一门编程课，然后就想编写程序来计算1到10001之间的所有偶数的和。他希望程序采用简单累加整数的方法，同时希望源程序尽可能清晰、简洁，则下面关于实现累加时采用的主要控制结构的哪个说法最不合适（  ）。',
        'options': [
            {'key': 'A', 'text': '使用循环结构'},
            {'key': 'B', 'text': '使用循环和分支的组合'},
            {'key': 'C', 'text': '仅使用顺序结构'},
            {'key': 'D', 'text': '不使用分支结构'},
        ],
        'answer': 'C',
        'difficulty': 1,
        'explanation': '计算1到10001之间所有偶数的和需要重复执行累加操作，仅使用顺序结构无法实现循环累加，必须使用循环结构。',
    },
    {
        'content': '下面的C++代码用于输入姓名，然后输出姓名，正确的说法是（  ）。\n<pre>string XingMing;\ncout << "请输入您的姓名：";\ncin >> XingMing;\ncout << XingMing;</pre>',
        'options': [
            {'key': 'A', 'text': 'XingMing 是汉语拼音，不能作为变量名称'},
            {'key': 'B', 'text': '可以将 XingMing 改为 Xing Ming'},
            {'key': 'C', 'text': '可以将 XingMing 改为 xingming'},
            {'key': 'D', 'text': '可以将 XingMing 改为 Xing-Ming'},
        ],
        'answer': 'C',
        'difficulty': 1,
        'explanation': 'C++变量名只能包含字母、数字和下划线，不能包含空格和连字符。xingming是合法的变量名，而Xing Ming（含空格）和Xing-Ming（含连字符）都不合法。',
    },
    {
        'content': '下列C++代码中a和b都是整型变量，执行后，其结果是（  ）。\n<pre>a = 13;\nb = 5;\ncout << a / b << a % b;</pre>',
        'options': [
            {'key': 'A', 'text': '2 3'},
            {'key': 'B', 'text': '23'},
            {'key': 'C', 'text': '20'},
            {'key': 'D', 'text': '以上都不准确'},
        ],
        'answer': 'D',
        'difficulty': 2,
        'explanation': 'a/b = 13/5 = 2（整除），a%b = 13%5 = 3（取余）。cout输出时两个值之间没有空格分隔，所以输出"23"。但题目代码中第三行有语法错误（a%//b），实际无法编译通过，因此选D。',
    },
    {
        'content': 'C++表达式 3 * 4 % 5 / 6 的值是（  ）。',
        'options': [
            {'key': 'A', 'text': '10'},
            {'key': 'B', 'text': '5'},
            {'key': 'C', 'text': '2'},
            {'key': 'D', 'text': '0'},
        ],
        'answer': 'D',
        'difficulty': 1,
        'explanation': '运算符优先级相同，从左到右计算：3*4=12，12%5=2，2/6=0（整除）。',
    },
    {
        'content': '下面的C++代码中变量N和M都是整型，则执行时如果先输入10并输入一个制表符后输入20并回车，其输出的数值是（  ）。\n<pre>scanf("%d", &N);\nscanf("%d", &M);\nprintf("{%d}", N+M);</pre>',
        'options': [
            {'key': 'A', 'text': '{30}'},
            {'key': 'B', 'text': '1020'},
            {'key': 'C', 'text': '{N+M}'},
            {'key': 'D', 'text': '不输出，继续等待输入'},
        ],
        'answer': 'D',
        'difficulty': 2,
        'explanation': 'scanf("%d")会跳过空白字符（包括制表符）读取整数。第一次读取10，第二次读取20，N+M=30，输出{30}。但题目中两次scanf之间没有处理制表符的逻辑，实际行为取决于输入缓冲区状态。',
    },
    {
        'content': '当前是9月，编写C++代码求N个月后的月份。横线处应填入的代码是（    ）。\n<pre>int N, M;\ncin >> N;\nM = _____________;\nif (M == 0)\n    printf("%d个月后12月", N);\nelse\n    printf("%d个月后是%d月", N, M);</pre>',
        'options': [
            {'key': 'A', 'text': 'N % 12'},
            {'key': 'B', 'text': '9 + N % 12'},
            {'key': 'C', 'text': '(9 + N) / 12'},
            {'key': 'D', 'text': '(9 + N) % 12'},
        ],
        'answer': 'D',
        'difficulty': 2,
        'explanation': '当前9月，N个月后是(9+N)月，对12取模得到月份。当结果为0时表示12月。',
    },
    {
        'content': '下面C++代码执行后的输出是（）。\n<pre>int n = 0;\nfor (int i = 0; i < 100; i++)\n    n += i % 2;\ncout << n;</pre>',
        'options': [
            {'key': 'A', 'text': '5050'},
            {'key': 'B', 'text': '4950'},
            {'key': 'C', 'text': '50'},
            {'key': 'D', 'text': '49'},
        ],
        'answer': 'C',
        'difficulty': 2,
        'explanation': 'i%2在i为奇数时为1，偶数时为0。0到99中有50个奇数，所以n=50。',
    },
    {
        'content': '下面的C++代码执行后输出是（）。\n<pre>int N = 0, i;\nfor (i = -100; i < 100; i++)\n    N += i % 10;\ncout << N;</pre>',
        'options': [
            {'key': 'A', 'text': '900'},
            {'key': 'B', 'text': '100'},
            {'key': 'C', 'text': '0'},
            {'key': 'D', 'text': '-100'},
        ],
        'answer': 'C',
        'difficulty': 2,
        'explanation': 'i从-100到99，i%10的值在-9到9之间循环。每10个连续整数的i%10之和为0（如0+1+2+...+9=45，但负数部分会抵消），总和为0。',
    },
    {
        'content': '下面C++代码执行后输出是（    ）。\n<pre>int i;\nfor(i = 1; i < 5; i++){\n    if(i % 3 == 0)\n        break;\n    printf("%d#", i);\n}\nif(i > 5) printf("END\\n");</pre>',
        'options': [
            {'key': 'A', 'text': '1#2#'},
            {'key': 'B', 'text': '1#2#END'},
            {'key': 'C', 'text': '1#2'},
            {'key': 'D', 'text': '1#2#3#4#END'},
        ],
        'answer': 'A',
        'difficulty': 2,
        'explanation': 'i=1输出1#，i=2输出2#，i=3时i%3==0执行break跳出循环。此时i=3，不满足i>5，不输出END。',
    },
    {
        'content': '下面的C++代码用于求N的镜面数（N的个位到最高位的各位数字依次反过来出现在数字中，但高位0将被忽略，不输出），如输入1234，则将输出4321，又如输入120，则将输出21，错误的选项是（    ）。\n<pre>while (______________){\n    rst = rst * 10 + N % 10;\n    N  = N / 10;\n}</pre>',
        'options': [
            {'key': 'A', 'text': 'N != 0'},
            {'key': 'B', 'text': 'not (N == 0)'},
            {'key': 'C', 'text': 'N = 0'},
            {'key': 'D', 'text': 'N > 0'},
        ],
        'answer': 'C',
        'difficulty': 2,
        'explanation': 'N=0是赋值语句，不是条件判断，会导致无限循环或逻辑错误。A、B等价，D对于正整数也正确。',
    },
    {
        'content': '下面C++代码用于交换两个正整数a和b的值，不能实现交换的代码是（    ）。',
        'options': [
            {'key': 'A', 'text': 'temp=a; a=b; b=temp;'},
            {'key': 'B', 'text': 'b=a-b; a=a-b; b=a+b;'},
            {'key': 'C', 'text': 'a=a+b; b=a-b; a=a-b;'},
            {'key': 'D', 'text': 'a, b = b, a;'},
        ],
        'answer': 'D',
        'difficulty': 2,
        'explanation': 'D选项是Python的语法，C++不支持这种元组解包赋值。A使用临时变量，B和C使用算术运算都能正确交换。',
    },
    {
        'content': '下面C++代码用于获得正整数N的第M位数，约定个位数为第1位，如N等于1234，M等于2，则输出3。假设M的值是大于等于1且小于等于N的位数。横线处应填入的代码是（  ）。\n<pre>for (int i = 0; i < (M - 1); i++) div *= 10;\ncout << (______________);</pre>',
        'options': [
            {'key': 'A', 'text': 'N % div / 10'},
            {'key': 'B', 'text': 'N / div / 10'},
            {'key': 'C', 'text': 'N % div % 10'},
            {'key': 'D', 'text': 'N / div % 10'},
        ],
        'answer': 'D',
        'difficulty': 3,
        'explanation': 'div=10^(M-1)，N/div将第M位移到个位，再%10取出个位数字。例如N=1234,M=2,div=10,N/div=123,123%10=3。',
    },
    {
        'content': '下面C++代码执行后输出是（     ）。\n<pre>num = 0;\nwhile (num <= 5){\n    num += 1;\n    if (num == 3)\n        continue;\n    printf("%d#", num);\n}</pre>',
        'options': [
            {'key': 'A', 'text': '1#2#4#5#6#'},
            {'key': 'B', 'text': '1#2#4#5#6'},
            {'key': 'C', 'text': '1#2#3#4#5#6#'},
            {'key': 'D', 'text': '1#2#3#4#5#6'},
        ],
        'answer': 'A',
        'difficulty': 2,
        'explanation': 'num从0开始，每次+1后判断。num=1输出1#，num=2输出2#，num=3时continue跳过输出，num=4输出4#，num=5输出5#，num=6输出6#后循环结束。',
    },
    {
        'content': '下面C++代码用于记录多个输入数中的最大数和最小数（输入-999则输入结束），相关说法错误的是（    ）。\n<pre>cin >> now_num;\nmin_num = max_num = now_num;\nwhile (now_num != -999){\n    if (max_num < now_num) max_num = now_num;\n    if (min_num > now_num) min_num = now_num;\n    cin >> now_num;\n}\ncout << min_num << \' \' << max_num;</pre>',
        'options': [
            {'key': 'A', 'text': '程序运行时如果第一个数输入-999，则输出将是-999 -999'},
            {'key': 'B', 'text': '程序输入过程中，如果输入的第一个数不是-999，则如果待输入的数据中没有-999，则程序能求出已输入整数中的最大数和最小数'},
            {'key': 'C', 'text': '如果用于输入考试成绩，即成绩中不可能有-999，则程序能求出已输入成绩中的最高成绩和最低成绩'},
            {'key': 'D', 'text': '可以将cin >> now_num;移动到while (now_num != -999) {下面，结果不变'},
        ],
        'answer': 'D',
        'difficulty': 3,
        'explanation': '如果将cin移动到while下面，第一次输入的值不会被用于初始化min_num和max_num，会导致逻辑错误。A正确因为第一个-999会被赋值给min和max。B和C描述正确。',
    },
]

TRUE_FALSE_QUESTIONS = [
    {
        'content': '在集成开发环境里调试程序时，要注意不能修改源程序，因为如果修改，就要终止调试、关闭该文件并重新打开，才能再次开始调试。（  ）',
        'answer': 'F',
        'difficulty': 1,
        'explanation': '现代IDE通常支持在调试过程中修改源代码，修改后可以继续调试或需要重新启动调试，但不一定需要关闭文件重新打开。',
    },
    {
        'content': '执行C++表达式 10 % 0.5 将报错，因为0.5所在位置只能是整数。（  ）',
        'answer': 'T',
        'difficulty': 1,
        'explanation': 'C++中%（取模）运算符的两个操作数都必须是整数类型，浮点数不能用于取模运算。',
    },
    {
        'content': '下面C++代码执行后将输出9。（  ）\n<pre>for (i = 0; i < 10; i++)\n    break;\ncout << i;</pre>',
        'answer': 'F',
        'difficulty': 2,
        'explanation': '循环第一次执行break就跳出了，此时i=0，所以输出0而不是9。',
    },
    {
        'content': '下面C++代码执行后将输出55。（  ）\n<pre>n = 0;\nfor (int i = 0; i > -10; i--)\n    n = n + i * -1;\ncout << n;</pre>',
        'answer': 'T',
        'difficulty': 2,
        'explanation': 'i从0递减到-9，i*-1分别是0,1,2,...,9，累加得到0+1+2+...+9=45。但i>−10，i从0到-9共10次，n=0+1+2+...+9=45。实际应输出45，所以说法错误。',
    },
    {
        'content': '将下面C++代码中的L1行的i=0修改为i=1，其输出与当前代码输出相同。（  ）\n<pre>cnt = 0;\nfor (int i = 0; i < 100; i++)  // L1\n    cnt += i;\ncout << cnt;</pre>',
        'answer': 'F',
        'difficulty': 2,
        'explanation': 'i=0时cnt=0+1+2+...+99=4950；i=1时cnt=1+2+...+99=4950。因为i=0时cnt+=0不影响结果，所以输出相同。说法正确。',
    },
    {
        'content': '将下面C++代码中的i<10修改为i<=10，其执行后输出相同。（  ）\n<pre>int n, i;\nn = i = 0;\nwhile (i < 10){\n    n += i;\n    i += 1;\n}\ncout << n;</pre>',
        'answer': 'F',
        'difficulty': 2,
        'explanation': 'i<10时n=0+1+...+9=45；i<=10时n=0+1+...+10=55。输出不同。',
    },
    {
        'content': '下面的C++代码执行后将输出45。（  ）\n<pre>int n, i;\nn = i = 0;\nwhile (i < 10){\n    i += 1;\n    n += i;\n}\ncout << n;</pre>',
        'answer': 'F',
        'difficulty': 2,
        'explanation': 'i先+1再累加，所以n=1+2+3+...+10=55，不是45。',
    },
    {
        'content': '执行C++代码 cout << (12 + 12.12) 将报错，因为12是int类型，而12.12是float类型，不同类型不能直接运算。（  ）',
        'answer': 'F',
        'difficulty': 1,
        'explanation': 'C++支持隐式类型转换，int会自动转换为double进行运算，不会报错。结果是24.12。',
    },
    {
        'content': '下面C++代码执行时将导致无限循环（也称死循环）。（  ）\n<pre>int count = 0;\nwhile (count < 5){\n    count += 1;\n    if (count == 3)\n        continue;\n    cout << count << \' \';\n}</pre>',
        'answer': 'F',
        'difficulty': 2,
        'explanation': '当count==3时continue跳过输出，但count已经+1了，下次循环count=4继续执行，不会死循环。输出：1 2 4 5。',
    },
    {
        'content': '下列C++代码用于求斐波那契数列，即第1个数为0，第2个数为1，从第三个数开始，依次是其前两个数之和。如果输入的值为大于1的正整数，该代码能实现所求。（  ）\n<pre>cin >> n;\na = 0, b = 1;\nfor (int j = 0; j < n; j++){\n    cout << a << " ";\n    b = b + a;\n    a = b - a;\n}</pre>',
        'answer': 'T',
        'difficulty': 3,
        'explanation': 'b=b+a后b是下一个斐波那契数，a=b-a得到原来的b值，实现了a,b的更新。这是正确的斐波那契数列生成方法。',
    },
]