"""生成GESP C++ 示例题目数据"""
from django.core.management.base import BaseCommand
from apps.questions.models import Question
from apps.knowledge.models import GespLevel, KnowledgePoint


SAMPLE_QUESTIONS = [
    # ===== 一级 =====
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 1,
        'content': '以下哪个是C++的标准输出语句？',
        'options': [
            {'key': 'A', 'text': 'print("hello")'},
            {'key': 'B', 'text': 'cout << "hello"'},
            {'key': 'C', 'text': 'echo "hello"'},
            {'key': 'D', 'text': 'System.out.println("hello")'},
        ],
        'answer': 'B',
        'explanation': 'C++使用cout进行标准输出，需要包含<iostream>头文件。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 1,
        'content': 'C++源文件的扩展名通常是？',
        'options': [
            {'key': 'A', 'text': '.java'},
            {'key': 'B', 'text': '.py'},
            {'key': 'C', 'text': '.cpp'},
            {'key': 'D', 'text': '.html'},
        ],
        'answer': 'C',
        'explanation': 'C++源代码文件通常使用.cpp作为扩展名，也可以使用.cc、.cxx等。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 3, 'difficulty': 1,
        'content': 'C++程序的执行从main函数开始。',
        'options': [],
        'answer': 'T',
        'explanation': '每个C++程序都必须有一个main函数，程序从main函数的第一条语句开始执行。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 1,
        'content': '以下哪个是C++中的整型数据类型？',
        'options': [
            {'key': 'A', 'text': 'string'},
            {'key': 'B', 'text': 'int'},
            {'key': 'C', 'text': 'bool'},
            {'key': 'D', 'text': 'float'},
        ],
        'answer': 'B',
        'explanation': 'int是C++中的整型数据类型，用于存储整数。string是字符串，bool是布尔，float是浮点数。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 1,
        'content': '在C++中，用于从键盘输入数据的是？',
        'options': [
            {'key': 'A', 'text': 'cout'},
            {'key': 'B', 'text': 'cin'},
            {'key': 'C', 'text': 'input'},
            {'key': 'D', 'text': 'scanf'},
        ],
        'answer': 'B',
        'explanation': 'cin是C++标准输入流对象，配合>>运算符从键盘读取数据。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 3, 'difficulty': 1,
        'content': 'C++中，变量在使用之前必须先声明。',
        'options': [],
        'answer': 'T',
        'explanation': 'C++是强类型语言，所有变量必须先声明再使用。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 2,
        'content': '以下程序的输出是什么？\n<pre>int a = 10, b = 3;\ncout &lt;&lt; a / b;</pre>',
        'options': [
            {'key': 'A', 'text': '3'},
            {'key': 'B', 'text': '3.33'},
            {'key': 'C', 'text': '3.333333'},
            {'key': 'D', 'text': '4'},
        ],
        'answer': 'A',
        'explanation': '两个int类型相除，结果仍然是int类型，小数部分被截断，所以10/3=3。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 2,
        'content': '以下哪个运算符用于取余数？',
        'options': [
            {'key': 'A', 'text': '/'},
            {'key': 'B', 'text': '%'},
            {'key': 'C', 'text': '*'},
            {'key': 'D', 'text': '//'},
        ],
        'answer': 'B',
        'explanation': '%是取模（取余数）运算符。例如 10%3 的结果是 1。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 3, 'difficulty': 2,
        'content': '在C++中，"="和"=="的含义是相同的。',
        'options': [],
        'answer': 'F',
        'explanation': '"="是赋值运算符，将右边的值赋给左边的变量；"=="是相等比较运算符，判断两边的值是否相等。',
        'source': '一级模拟题',
    },
    {
        'level_id': 1, 'question_type': 1, 'difficulty': 1,
        'content': '#include &lt;iostream&gt; 的作用是？',
        'options': [
            {'key': 'A', 'text': '定义一个函数'},
            {'key': 'B', 'text': '包含输入输出流的头文件'},
            {'key': 'C', 'text': '声明一个变量'},
            {'key': 'D', 'text': '编写注释'},
        ],
        'answer': 'B',
        'explanation': '#include <iostream>是预处理指令，用于包含C++标准输入输出流头文件，使得程序可以使用cin和cout。',
        'source': '一级模拟题',
    },

    # ===== 二级 =====
    {
        'level_id': 2, 'question_type': 1, 'difficulty': 1,
        'content': '以下哪个是C++中的条件判断语句？',
        'options': [
            {'key': 'A', 'text': 'for'},
            {'key': 'B', 'text': 'if'},
            {'key': 'C', 'text': 'while'},
            {'key': 'D', 'text': 'do'},
        ],
        'answer': 'B',
        'explanation': 'if是C++中的条件判断语句，根据条件的真假来决定执行哪个分支的代码。',
        'source': '二级模拟题',
    },
    {
        'level_id': 2, 'question_type': 1, 'difficulty': 2,
        'content': '以下for循环执行后，i的值是多少？\n<pre>int i;\nfor(i = 0; i &lt; 5; i++) {}</pre>',
        'options': [
            {'key': 'A', 'text': '4'},
            {'key': 'B', 'text': '5'},
            {'key': 'C', 'text': '6'},
            {'key': 'D', 'text': '0'},
        ],
        'answer': 'B',
        'explanation': 'for循环中，当i=5时条件i<5为假，循环结束，此时i的值为5。',
        'source': '二级模拟题',
    },
    {
        'level_id': 2, 'question_type': 1, 'difficulty': 2,
        'content': '以下程序段的输出是？\n<pre>int sum = 0;\nfor(int i = 1; i &lt;= 10; i++) {\n  sum += i;\n}\ncout &lt;&lt; sum;</pre>',
        'options': [
            {'key': 'A', 'text': '45'},
            {'key': 'B', 'text': '55'},
            {'key': 'C', 'text': '10'},
            {'key': 'D', 'text': '100'},
        ],
        'answer': 'B',
        'explanation': '这是一个1到10的累加求和，1+2+3+...+10=55。',
        'source': '二级模拟题',
    },
    {
        'level_id': 2, 'question_type': 3, 'difficulty': 1,
        'content': 'switch语句中的每个case后面如果不加break，会继续执行下一个case的语句。',
        'options': [],
        'answer': 'T',
        'explanation': '这称为"穿透"(fall through)现象。如果case后没有break语句，程序会继续执行下一个case的语句，直到遇到break或switch语句结束。',
        'source': '二级模拟题',
    },
    {
        'level_id': 2, 'question_type': 1, 'difficulty': 2,
        'content': 'while(1) 表示什么？',
        'options': [
            {'key': 'A', 'text': '循环执行一次'},
            {'key': 'B', 'text': '无限循环'},
            {'key': 'C', 'text': '不执行循环'},
            {'key': 'D', 'text': '语法错误'},
        ],
        'answer': 'B',
        'explanation': 'while的条件为非零值时视为真，while(1)的条件永远为真，因此是无限循环（死循环）。',
        'source': '二级模拟题',
    },
    {
        'level_id': 2, 'question_type': 1, 'difficulty': 3,
        'content': '以下程序输出什么？\n<pre>int x = 10;\nif(x &gt; 5) {\n  if(x &gt; 8)\n    cout &lt;&lt; "A";\n  else\n    cout &lt;&lt; "B";\n} else {\n  cout &lt;&lt; "C";\n}</pre>',
        'options': [
            {'key': 'A', 'text': 'A'},
            {'key': 'B', 'text': 'B'},
            {'key': 'C', 'text': 'C'},
            {'key': 'D', 'text': 'AB'},
        ],
        'answer': 'A',
        'explanation': 'x=10 > 5成立，进入外层if。x=10 > 8也成立，输出"A"。',
        'source': '二级模拟题',
    },

    # ===== 三级 =====
    {
        'level_id': 3, 'question_type': 1, 'difficulty': 1,
        'content': 'C++中定义一个包含10个整数的数组，正确写法是？',
        'options': [
            {'key': 'A', 'text': 'int a(10);'},
            {'key': 'B', 'text': 'int a[10];'},
            {'key': 'C', 'text': 'array a[10];'},
            {'key': 'D', 'text': 'int[10] a;'},
        ],
        'answer': 'B',
        'explanation': 'C++中使用 类型名 数组名[大小] 的格式定义数组，所以int a[10]是正确的。',
        'source': '三级模拟题',
    },
    {
        'level_id': 3, 'question_type': 1, 'difficulty': 2,
        'content': '数组int a[5] = {1, 2, 3}; 中，a[4]的值是？',
        'options': [
            {'key': 'A', 'text': '3'},
            {'key': 'B', 'text': '0'},
            {'key': 'C', 'text': '未定义'},
            {'key': 'D', 'text': '5'},
        ],
        'answer': 'B',
        'explanation': '初始化列表不足时，剩余元素自动初始化为0。a[0]=1, a[1]=2, a[2]=3, a[3]=0, a[4]=0。',
        'source': '三级模拟题',
    },
    {
        'level_id': 3, 'question_type': 3, 'difficulty': 1,
        'content': 'C++中数组的下标从1开始。',
        'options': [],
        'answer': 'F',
        'explanation': 'C++中数组的下标从0开始。对于int a[5]，有效下标是0到4。',
        'source': '三级模拟题',
    },
    {
        'level_id': 3, 'question_type': 1, 'difficulty': 2,
        'content': '以下哪个函数可以求字符串的长度？',
        'options': [
            {'key': 'A', 'text': 'strlen()'},
            {'key': 'B', 'text': 'sizeof()'},
            {'key': 'C', 'text': 'length()'},
            {'key': 'D', 'text': 'A和C都可以'},
        ],
        'answer': 'D',
        'explanation': 'strlen()用于C风格字符串，string类的.length()方法用于C++ string对象，两者都可以求字符串长度。sizeof()返回的是变量/类型占用的内存大小。',
        'source': '三级模拟题',
    },
    {
        'level_id': 3, 'question_type': 1, 'difficulty': 3,
        'content': '对数组进行冒泡排序，下列代码的空白处应填入什么？\n<pre>for(int i = 0; i &lt; n-1; i++)\n  for(int j = 0; j &lt; ______; j++)\n    if(a[j] &gt; a[j+1])\n      swap(a[j], a[j+1]);</pre>',
        'options': [
            {'key': 'A', 'text': 'n'},
            {'key': 'B', 'text': 'n-1'},
            {'key': 'C', 'text': 'n-i-1'},
            {'key': 'D', 'text': 'n-i'},
        ],
        'answer': 'C',
        'explanation': '冒泡排序的内层循环每轮会将最大的元素"冒泡"到末尾，因此每轮减少一次比较。内层循环范围应为j < n-i-1。',
        'source': '三级模拟题',
    },

    # ===== 四级 =====
    {
        'level_id': 4, 'question_type': 1, 'difficulty': 1,
        'content': '以下哪个是定义函数的正确语法？',
        'options': [
            {'key': 'A', 'text': 'def add(int a, int b)'},
            {'key': 'B', 'text': 'int add(int a, int b)'},
            {'key': 'C', 'text': 'function add(int a, int b)'},
            {'key': 'D', 'text': 'add(int a, int b): int'},
        ],
        'answer': 'B',
        'explanation': 'C++中函数定义的格式为：返回类型 函数名(参数列表)。int add(int a, int b)是正确的。',
        'source': '四级模拟题',
    },
    {
        'level_id': 4, 'question_type': 1, 'difficulty': 2,
        'content': '关于递归函数，以下说法正确的是？',
        'options': [
            {'key': 'A', 'text': '递归函数不需要终止条件'},
            {'key': 'B', 'text': '递归函数必须有终止条件，否则会导致栈溢出'},
            {'key': 'C', 'text': '递归比循环一定更快'},
            {'key': 'D', 'text': '递归函数不能调用自身'},
        ],
        'answer': 'B',
        'explanation': '递归函数是直接或间接调用自身的函数，必须有明确的终止条件（基准情况），否则会导致无限递归，最终栈溢出(Stack Overflow)。',
        'source': '四级模拟题',
    },
    {
        'level_id': 4, 'question_type': 3, 'difficulty': 2,
        'content': '函数的形参和实参可以同名，不会产生冲突。',
        'options': [],
        'answer': 'T',
        'explanation': '形参是函数定义中的参数，实参是调用函数时传入的参数。它们在不同的作用域中，可以同名而不会冲突。',
        'source': '四级模拟题',
    },
    {
        'level_id': 4, 'question_type': 1, 'difficulty': 3,
        'content': '以下递归函数f(4)的返回值是？\n<pre>int f(int n) {\n  if(n &lt;= 1) return 1;\n  return n * f(n-1);\n}</pre>',
        'options': [
            {'key': 'A', 'text': '4'},
            {'key': 'B', 'text': '10'},
            {'key': 'C', 'text': '24'},
            {'key': 'D', 'text': '120'},
        ],
        'answer': 'C',
        'explanation': '这是一个求阶乘的递归函数。f(4)=4*f(3)=4*3*f(2)=4*3*2*f(1)=4*3*2*1=24。',
        'source': '四级模拟题',
    },
    {
        'level_id': 4, 'question_type': 1, 'difficulty': 2,
        'content': '以下关于引用传参的说法，正确的是？',
        'options': [
            {'key': 'A', 'text': '引用传参会复制实参的值'},
            {'key': 'B', 'text': '引用传参可以在函数内修改实参的值'},
            {'key': 'C', 'text': '引用传参和值传参效果完全相同'},
            {'key': 'D', 'text': '引用不能作为函数参数'},
        ],
        'answer': 'B',
        'explanation': '引用传参（pass by reference）将实参的引用传给形参，函数内对形参的修改会直接影响实参。这与值传参（传副本）不同。',
        'source': '四级模拟题',
    },

    # ===== 五级 =====
    {
        'level_id': 5, 'question_type': 1, 'difficulty': 2,
        'content': '以下关于指针的说法，错误的是？',
        'options': [
            {'key': 'A', 'text': '指针变量存储的是内存地址'},
            {'key': 'B', 'text': '*p可以访问指针p指向的值'},
            {'key': 'C', 'text': '&a可以获取变量a的地址'},
            {'key': 'D', 'text': '指针不需要初始化就可以安全使用'},
        ],
        'answer': 'D',
        'explanation': '未初始化的指针（野指针）指向随机内存地址，使用它是非常危险的，可能导致程序崩溃或产生未定义行为。',
        'source': '五级模拟题',
    },
    {
        'level_id': 5, 'question_type': 1, 'difficulty': 2,
        'content': '结构体struct Student { string name; int age; }; 定义变量s后，访问name的方式是？',
        'options': [
            {'key': 'A', 'text': 's->name'},
            {'key': 'B', 'text': 's.name'},
            {'key': 'C', 'text': 's[name]'},
            {'key': 'D', 'text': 'name.s'},
        ],
        'answer': 'B',
        'explanation': '结构体变量使用.运算符访问成员。s->name用于结构体指针。',
        'source': '五级模拟题',
    },
    {
        'level_id': 5, 'question_type': 1, 'difficulty': 3,
        'content': '二分查找的时间复杂度是？',
        'options': [
            {'key': 'A', 'text': 'O(n)'},
            {'key': 'B', 'text': 'O(n²)'},
            {'key': 'C', 'text': 'O(log n)'},
            {'key': 'D', 'text': 'O(1)'},
        ],
        'answer': 'C',
        'explanation': '二分查找每次将搜索范围缩小一半，所以时间复杂度为O(log n)。前提是数据已经排好序。',
        'source': '五级模拟题',
    },
    {
        'level_id': 5, 'question_type': 3, 'difficulty': 2,
        'content': '使用new关键字分配的内存，必须使用delete来释放。',
        'options': [],
        'answer': 'T',
        'explanation': 'new和delete是配对使用的。new分配的堆内存不会自动释放，必须用delete（或delete[]用于数组）手动释放，否则会导致内存泄漏。',
        'source': '五级模拟题',
    },

    # ===== 六级 =====
    {
        'level_id': 6, 'question_type': 1, 'difficulty': 2,
        'content': '以下哪个STL容器是基于红黑树实现的？',
        'options': [
            {'key': 'A', 'text': 'vector'},
            {'key': 'B', 'text': 'set'},
            {'key': 'C', 'text': 'queue'},
            {'key': 'D', 'text': 'stack'},
        ],
        'answer': 'B',
        'explanation': 'set和map在C++ STL中是基于红黑树（自平衡二叉搜索树）实现的，元素自动排序，查找/插入/删除的时间复杂度都是O(log n)。',
        'source': '六级模拟题',
    },
    {
        'level_id': 6, 'question_type': 1, 'difficulty': 2,
        'content': '栈（stack）的特点是？',
        'options': [
            {'key': 'A', 'text': '先进先出（FIFO）'},
            {'key': 'B', 'text': '先进后出（FILO）'},
            {'key': 'C', 'text': '随机访问'},
            {'key': 'D', 'text': '按优先级出队'},
        ],
        'answer': 'B',
        'explanation': '栈是一种先进后出（FILO, First In Last Out）的数据结构，只能在栈顶进行插入（push）和删除（pop）操作。',
        'source': '六级模拟题',
    },
    {
        'level_id': 6, 'question_type': 2, 'difficulty': 2,
        'content': '以下哪些是STL中的关联容器？（多选）',
        'options': [
            {'key': 'A', 'text': 'set'},
            {'key': 'B', 'text': 'map'},
            {'key': 'C', 'text': 'vector'},
            {'key': 'D', 'text': 'unordered_map'},
        ],
        'answer': 'ABD',
        'explanation': 'set、map是有序关联容器，unordered_map是无序关联容器。vector是序列容器。',
        'source': '六级模拟题',
    },
    {
        'level_id': 6, 'question_type': 1, 'difficulty': 3,
        'content': '用BFS（广度优先搜索）遍历图时，需要使用的辅助数据结构是？',
        'options': [
            {'key': 'A', 'text': '栈（stack）'},
            {'key': 'B', 'text': '队列（queue）'},
            {'key': 'C', 'text': '堆（heap）'},
            {'key': 'D', 'text': '链表（list）'},
        ],
        'answer': 'B',
        'explanation': 'BFS使用队列来实现层序遍历。DFS（深度优先搜索）则通常使用栈（或递归）。',
        'source': '六级模拟题',
    },

    # ===== 七级 =====
    {
        'level_id': 7, 'question_type': 1, 'difficulty': 2,
        'content': '动态规划的核心思想是？',
        'options': [
            {'key': 'A', 'text': '贪心选择'},
            {'key': 'B', 'text': '将问题分解为子问题，利用子问题的解来构造原问题的解'},
            {'key': 'C', 'text': '随机化搜索'},
            {'key': 'D', 'text': '穷举所有可能'},
        ],
        'answer': 'B',
        'explanation': '动态规划通过将问题分解为重叠子问题，并保存子问题的解（记忆化），避免重复计算，从而高效求解。',
        'source': '七级模拟题',
    },
    {
        'level_id': 7, 'question_type': 1, 'difficulty': 3,
        'content': '以下哪个问题不适合用动态规划求解？',
        'options': [
            {'key': 'A', 'text': '最长公共子序列'},
            {'key': 'B', 'text': '0/1背包问题'},
            {'key': 'C', 'text': '求数组最大值'},
            {'key': 'D', 'text': '最短路径问题'},
        ],
        'answer': 'C',
        'explanation': '求数组最大值只需遍历一次数组，时间复杂度O(n)，不需要动态规划。动态规划适用于具有最优子结构和重叠子问题性质的问题。',
        'source': '七级模拟题',
    },
    {
        'level_id': 7, 'question_type': 3, 'difficulty': 2,
        'content': '贪心算法总能得到全局最优解。',
        'options': [],
        'answer': 'F',
        'explanation': '贪心算法在每一步做出局部最优选择，但并不总是能得到全局最优解。只有满足贪心选择性质和最优子结构的问题，贪心算法才能保证得到最优解。',
        'source': '七级模拟题',
    },
    {
        'level_id': 7, 'question_type': 1, 'difficulty': 3,
        'content': '使用Dijkstra算法求最短路径时，如果图中存在负权边，结果会怎样？',
        'options': [
            {'key': 'A', 'text': '仍然正确'},
            {'key': 'B', 'text': '可能得到错误结果'},
            {'key': 'C', 'text': '程序会报错'},
            {'key': 'D', 'text': '时间复杂度会增加'},
        ],
        'answer': 'B',
        'explanation': 'Dijkstra算法不能处理负权边。如果存在负权边，应使用Bellman-Ford算法或SPFA算法。',
        'source': '七级模拟题',
    },

    # ===== 八级 =====
    {
        'level_id': 8, 'question_type': 1, 'difficulty': 3,
        'content': '线段树（Segment Tree）不能高效支持以下哪种操作？',
        'options': [
            {'key': 'A', 'text': '区间求和'},
            {'key': 'B', 'text': '区间最值查询'},
            {'key': 'C', 'text': '单点修改'},
            {'key': 'D', 'text': '区间插入新元素'},
        ],
        'answer': 'D',
        'explanation': '线段树擅长区间查询和单点/区间修改（O(log n)），但不支持在数组中间插入新元素。插入操作需要使用平衡树或其他数据结构。',
        'source': '八级模拟题',
    },
    {
        'level_id': 8, 'question_type': 1, 'difficulty': 3,
        'content': '以下哪种算法用于求解最大流问题？',
        'options': [
            {'key': 'A', 'text': 'Dijkstra算法'},
            {'key': 'B', 'text': 'Kruskal算法'},
            {'key': 'C', 'text': 'Ford-Fulkerson算法'},
            {'key': 'D', 'text': '拓扑排序'},
        ],
        'answer': 'C',
        'explanation': 'Ford-Fulkerson算法是求解最大流问题的经典算法。Dijkstra用于最短路径，Kruskal用于最小生成树，拓扑排序用于有向无环图排序。',
        'source': '八级模拟题',
    },
    {
        'level_id': 8, 'question_type': 3, 'difficulty': 3,
        'content': '时间复杂度为O(n log n)的排序算法一定比O(n²)的排序算法快。',
        'options': [],
        'answer': 'F',
        'explanation': '时间复杂度描述的是增长趋势，不代表实际运行时间。对于小规模数据，O(n²)的插入排序可能比O(n log n)的归并排序更快，因为常数因子更小。',
        'source': '八级模拟题',
    },
    {
        'level_id': 8, 'question_type': 2, 'difficulty': 3,
        'content': '以下哪些数据结构可以用于实现优先队列？（多选）',
        'options': [
            {'key': 'A', 'text': '二叉堆'},
            {'key': 'B', 'text': '有序数组'},
            {'key': 'C', 'text': '斐波那契堆'},
            {'key': 'D', 'text': '哈希表'},
        ],
        'answer': 'ABC',
        'explanation': '二叉堆是最常用的优先队列实现，有序数组也可以实现（但效率较低），斐波那契堆是高级实现。哈希表不具有优先级排序的特性，不适合实现优先队列。',
        'source': '八级模拟题',
    },
]


class Command(BaseCommand):
    help = '生成GESP C++示例题目数据'

    def handle(self, *args, **options):
        if Question.objects.exists():
            self.stdout.write(self.style.WARNING('题目表已有数据，跳过生成。如需重新生成请先清空题目表。'))
            return

        from django.contrib.auth.models import User
        admin = User.objects.filter(is_superuser=True).first()

        created = 0
        for q_data in SAMPLE_QUESTIONS:
            Question.objects.create(
                level_id=q_data['level_id'],
                question_type=q_data['question_type'],
                difficulty=q_data['difficulty'],
                content=q_data['content'],
                options=q_data['options'],
                answer=q_data['answer'],
                explanation=q_data.get('explanation', ''),
                source=q_data.get('source', ''),
                created_by=admin,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'成功创建 {created} 道示例题目'))
