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
    "explanation": "简要解析（可空）",
    "incomplete": false,        // 若该题在页面底部被截断（题干或选项不完整），设为 true
    "is_continuation": false    // 若该题是上一页截断题目的续文（如页面开头直接是选项或代码），设为 true
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
8. 跨页检测：若页面最后一道题的题干或选项在图片底部被截断（内容不完整），将其 incomplete 设为 true
9. 续文检测：若页面第一道题看起来是上一页的续文（如直接从选项B/C/D开始，或代码块开头没有题号），将其 is_continuation 设为 true
"""

BOUNDARY_PROMPT = """你是 GESP C++ 竞赛试卷的题目提取专家。
以下两张图片是同一份试卷的相邻两页，第一张图片末尾有一道题目被截断，第二张图片开头是该题的续文。
请将两页内容合并，只提取这道跨页的完整题目，严格按照以下 JSON 格式输出，不要输出任何其他文字。

输出格式（JSON 数组，通常只含 1 道题）：
[
  {
    "question_type": "单选题",
    "difficulty": "简单",
    "content": "完整题目正文",
    "option_a": "选项A",
    "option_b": "选项B",
    "option_c": "选项C",
    "option_d": "选项D",
    "answer": "B",
    "explanation": ""
  }
]

提取规则：
1. 只提取跨越两页边界的那道题，不提取其他完整题目
2. 合并两页中该题的所有内容（题干 + 选项 + 答案）
3. 题干中的代码用三反引号包裹，行内代码用反引号包裹
4. 如果实际上没有跨页题目，返回空数组 []
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


def _parse_response(raw: str, level: int, source: str, keep_markers: bool = False) -> list[dict]:
    """解析模型返回的 JSON，转为标准题目列表"""
    json_str = None
    code_block = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', raw)
    if code_block:
        json_str = code_block.group(1)
    else:
        array_match = re.search(r'\[[\s\S]*\]', raw)
        if array_match:
            json_str = array_match.group()

    if not json_str:
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

        item = {
            "level": level,
            "question_type": qtype,
            "difficulty": DIFF_MAP.get(q.get("difficulty", "简单"), 1),
            "content": q.get("content", "").strip(),
            "options": options,
            "answer": q.get("answer", "").strip().upper(),
            "explanation": q.get("explanation", "").strip(),
            "source": source,
        }
        if keep_markers:
            item["incomplete"] = bool(q.get("incomplete", False))
            item["is_continuation"] = bool(q.get("is_continuation", False))
        results.append(item)
    return results


def extract_questions_from_image(client: OpenAI, image_bytes: bytes, level: int, source: str, model: str = "qwen-vl-max") -> list[dict]:
    """调用 Qwen-VL 从单张图片提取题目（保留跨页标记）"""
    b64 = base64.b64encode(image_bytes).decode()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": EXTRACT_PROMPT},
            ],
        }],
        max_tokens=4096,
    )
    raw = response.choices[0].message.content.strip()
    return _parse_response(raw, level, source, keep_markers=True)


def extract_boundary_questions(client: OpenAI, img_a: bytes, img_b: bytes, level: int, source: str, model: str = "qwen-vl-max") -> list[dict]:
    """调用 Qwen-VL 从相邻两页图片中提取跨页完整题目"""
    b64_a = base64.b64encode(img_a).decode()
    b64_b = base64.b64encode(img_b).decode()
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_a}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_b}"}},
                {"type": "text", "text": BOUNDARY_PROMPT},
            ],
        }],
        max_tokens=2048,
    )
    raw = response.choices[0].message.content.strip()
    return _parse_response(raw, level, source, keep_markers=False)


def extract_from_pdf(pdf_bytes: bytes, level: int, source: str) -> dict:
    """
    主入口：从 PDF 字节提取所有题目
    返回 {"questions": [...], "page_count": N, "errors": [...]}
    """
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key or api_key.startswith("sk-在这里"):
        raise ValueError("DASHSCOPE_API_KEY 未配置，请在 backend/.env 中填入 API Key")

    from .models import AIConfig
    try:
        config = AIConfig.objects.first()
        pdf_model = config.pdf_model if config and config.pdf_model else 'qwen-vl-max'
        if config and config.api_key:
            api_key = config.api_key
    except Exception:
        pdf_model = 'qwen-vl-max'

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=600,
    )

    images = pdf_to_images(pdf_bytes)
    errors = []

    # 第一阶段：逐页提取，保留跨页标记
    page_results = []
    for i, img_bytes in enumerate(images):
        try:
            qs = extract_questions_from_image(client, img_bytes, level, source, model=pdf_model)
            page_results.append(qs)
        except Exception as e:
            errors.append(f"第{i+1}页处理失败: {str(e)}")
            page_results.append([])

    # 第二阶段：检测跨页边界，按需补充合并提取
    continuation_pages = set()  # 这些页的第一道题已被边界合并，需跳过
    boundary_replacements = {}  # page_index -> 合并后的题目列表

    for i, qs in enumerate(page_results):
        if not qs:
            continue
        last_q = qs[-1]
        if last_q.get("incomplete") and i + 1 < len(images):
            try:
                boundary_qs = extract_boundary_questions(
                    client, images[i], images[i + 1], level, source, model=pdf_model
                )
                boundary_replacements[i] = boundary_qs
                # 标记下一页第一道题（续文）需跳过
                next_qs = page_results[i + 1]
                if next_qs and next_qs[0].get("is_continuation"):
                    continuation_pages.add(i + 1)
            except Exception as e:
                errors.append(f"第{i+1}-{i+2}页边界处理失败: {str(e)}")

    # 第三阶段：组合最终题目列表
    all_questions = []
    for i, qs in enumerate(page_results):
        # 跳过续文（已被边界提取覆盖）
        start_idx = 1 if (i in continuation_pages and qs and qs[0].get("is_continuation")) else 0
        page_qs = qs[start_idx:]

        if i in boundary_replacements:
            # 用合并题替换末尾残缺题
            all_questions.extend(page_qs[:-1])
            all_questions.extend(boundary_replacements[i])
        else:
            all_questions.extend(page_qs)

    # 清除内部标记字段
    for q in all_questions:
        q.pop("incomplete", None)
        q.pop("is_continuation", None)

    # 去重：content 相同的题目只保留一条
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
