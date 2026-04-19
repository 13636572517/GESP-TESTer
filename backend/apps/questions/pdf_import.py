"""
PDF 试卷 → 题目 JSON
使用 Qwen-VL（通义千问视觉版）通过 DashScope OpenAI 兼容接口提取题目。
"""
import base64
import json
import re
import fitz  # pymupdf
from openai import OpenAI
from django.conf import settings


EXTRACT_PROMPT = """你是 GESP C++ 竞赛试卷的题目提取专家。请从图片中提取所有选择题（单选题）和判断题，严格按照以下 JSON 格式输出，不要输出任何其他文字。

输出格式（JSON 数组）：
[
  {
    "question_type": "单选题",  // 或 "判断题"
    "difficulty": "简单",       // 简单 / 中等 / 困难
    "content": "题目正文（含代码用```包裹，行内代码用`包裹）",
    "option_a": "选项A内容",    // 判断题留空字符串
    "option_b": "选项B内容",
    "option_c": "选项C内容",
    "option_d": "选项D内容",
    "answer": "B",              // 单选填字母，判断题填 T 或 F
    "explanation": "简要解析（可空）"
  }
]

提取规则：
1. 单选题：提取题号、题干、选项 A~D、正确答案字母
2. 判断题：提取题号、题干、正确答案（正确=T，错误=F），option_a~d 留空字符串
3. 题干中的行内代码用反引号包裹：`int a = 1;`
4. 题干中的多行代码用三反引号包裹，换行用 \\n 表示
5. 难度判断：纯记忆/基础语法=简单；需要追踪运算/循环逻辑=中等；多步推导/复杂算法=困难
6. 如果图片中没有题目，返回空数组 []
7. 只提取题目，不提取大题标题、说明文字、分值信息
"""


def pdf_to_images(pdf_bytes: bytes, dpi: int = 100) -> list[bytes]:
    """将 PDF 每页转为 PNG 图片字节列表"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


def extract_questions_from_image(client: OpenAI, image_bytes: bytes, level: int, source: str) -> list[dict]:
    """调用 Qwen-VL 从单张图片提取题目"""
    b64 = base64.b64encode(image_bytes).decode()

    response = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                    {"type": "text", "text": EXTRACT_PROMPT},
                ],
            }
        ],
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # 从响应中提取 JSON
    # 优先匹配 ```json ... ``` 代码块，再尝试直接匹配 [...] 数组
    json_str = None
    code_block = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', raw)
    if code_block:
        json_str = code_block.group(1)
    else:
        array_match = re.search(r'\[[\s\S]*\]', raw)
        if array_match:
            json_str = array_match.group()

    if not json_str:
        # 模型未返回 JSON，记录原始内容方便调试
        raise ValueError(f"模型未返回JSON，原始内容: {raw[:300]}")

    try:
        questions = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {e}，内容片段: {json_str[:200]}")

    TYPE_MAP = {"单选题": 1, "判断题": 3}
    DIFF_MAP = {"简单": 1, "中等": 2, "困难": 3}

    results = []
    for q in questions:
        qtype = TYPE_MAP.get(q.get("question_type", ""), 1)
        options = []
        if qtype != 3:
            for key, field in [("A", "option_a"), ("B", "option_b"),
                                ("C", "option_c"), ("D", "option_d")]:
                text = q.get(field, "").strip()
                if text:
                    options.append({"key": key, "text": text})

        results.append({
            "level": level,
            "question_type": qtype,
            "difficulty": DIFF_MAP.get(q.get("difficulty", "简单"), 1),
            "content": q.get("content", "").strip(),
            "options": options,
            "answer": q.get("answer", "").strip().upper(),
            "explanation": q.get("explanation", "").strip(),
            "source": source,
        })
    return results


def extract_from_pdf(pdf_bytes: bytes, level: int, source: str) -> dict:
    """
    主入口：从 PDF 字节提取所有题目
    返回 {"questions": [...], "page_count": N, "errors": [...]}
    """
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key or api_key.startswith("sk-在这里"):
        raise ValueError("DASHSCOPE_API_KEY 未配置，请在 backend/.env 中填入 API Key")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=600,
    )

    images = pdf_to_images(pdf_bytes)
    all_questions = []
    errors = []

    for i, img_bytes in enumerate(images):
        try:
            qs = extract_questions_from_image(client, img_bytes, level, source)
            all_questions.extend(qs)
        except Exception as e:
            errors.append(f"第{i+1}页处理失败: {str(e)}")

    # 去重：content 相同的题目只保留一条（跨页重复）
    seen = set()
    unique = []
    for q in all_questions:
        key = q["content"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(q)

    return {
        "questions": unique,
        "page_count": len(images),
        "errors": errors,
    }
