"""
AI 服务：使用 Qwen（通义千问）实现知识点标注和题目生成。
通过 DashScope OpenAI 兼容接口调用。
配置（API Key、模型）优先从数据库 AIConfig 读取，回退到 .env 文件。
每次调用自动记录用量到 AIUsageLog。

API Key 加密方案：
  用 Django SECRET_KEY 的 SHA-256 哈希派生 Fernet 密钥，对数据库中的 API Key 做
  对称加密（AES-128-CBC + HMAC-SHA256）。即使数据库被脱库，没有 SECRET_KEY 也无法
  还原明文。源代码中不保存任何密钥。
"""
import base64
import hashlib
import json
import re
import time
from openai import OpenAI
from django.conf import settings


# ─── API Key 加密 / 解密 ──────────────────────────────────

def _fernet():
    """用 Django SECRET_KEY 派生 Fernet 实例（每次调用都重新派生，无状态）"""
    from cryptography.fernet import Fernet
    raw = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt_api_key(plain: str) -> str:
    """加密明文 API Key，返回可存数据库的密文字符串"""
    if not plain:
        return ''
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_api_key(cipher: str) -> str:
    """解密数据库中的 API Key 密文，返回明文；解密失败返回原值（兼容旧明文）"""
    if not cipher:
        return ''
    try:
        return _fernet().decrypt(cipher.encode()).decode()
    except Exception:
        return cipher  # 兼容尚未加密的历史记录

# ─── 配置缓存（避免每次 AI 调用都查数据库）─────────────────
_config_cache: dict = {'obj': None, 'ts': 0.0}
_CACHE_TTL = 60  # 秒


def _get_ai_config():
    """读取 AIConfig（60s 缓存）"""
    now = time.time()
    if now - _config_cache['ts'] < _CACHE_TTL:
        return _config_cache['obj']
    try:
        from .models import AIConfig
        cfg = AIConfig.objects.first()
        _config_cache['obj'] = cfg
        _config_cache['ts'] = now
        return cfg
    except Exception:
        return None


def invalidate_config_cache():
    """保存配置后主动失效缓存，下次调用立即重新读取"""
    _config_cache['ts'] = 0.0


AVAILABLE_MODELS = [
    {'value': 'qwen-turbo', 'label': 'qwen-turbo（快速，适合标注）'},
    {'value': 'qwen-plus',  'label': 'qwen-plus（均衡，推荐）'},
    {'value': 'qwen-max',   'label': 'qwen-max（最强，适合复杂出题）'},
    {'value': 'qwen-long',  'label': 'qwen-long（长文本）'},
]


def _get_user_client(user) -> OpenAI:
    """获取指定用户的 OpenAI 客户端（使用用户自己的 API Key）"""
    try:
        from apps.users.models import UserAIConfig
        cfg = UserAIConfig.objects.get(user=user)
        if cfg.api_key:
            api_key = decrypt_api_key(cfg.api_key)
        else:
            api_key = ''
    except Exception:
        api_key = ''
    if not api_key:
        raise ValueError("请先在右上角「AI 设置」中配置您自己的 API Key")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def _get_user_model(user, model_type: str = 'gen') -> str:
    """获取用户配置的模型名，model_type='gen'|'tag'"""
    try:
        from apps.users.models import UserAIConfig
        cfg = UserAIConfig.objects.get(user=user)
        return (cfg.gen_model if model_type == 'gen' else cfg.tag_model) or 'qwen-plus'
    except Exception:
        return 'qwen-plus'


def call_qwen_for_user(
    user,
    messages: list,
    temperature: float = 0.3,
    model: str | None = None,
    operation: int | None = None,
) -> str:
    """
    以指定用户身份调用 Qwen，使用用户自己的 API Key。
    用量记录到 AIUsageLog，并关联 user。
    """
    from .models import AIUsageLog
    if model is None:
        model = _get_user_model(user, 'gen')

    client   = _get_user_client(user)
    start_ms = int(time.time() * 1000)
    prompt_tokens = completion_tokens = total_tokens = 0
    success = False
    error_msg = ''
    content = ''

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
        )
        content = resp.choices[0].message.content.strip()
        if resp.usage:
            prompt_tokens     = resp.usage.prompt_tokens     or 0
            completion_tokens = resp.usage.completion_tokens or 0
            total_tokens      = resp.usage.total_tokens      or 0
        success = True
        return content
    except Exception as e:
        error_msg = str(e)[:500]
        raise
    finally:
        latency_ms = int(time.time() * 1000) - start_ms
        if operation is not None:
            try:
                AIUsageLog.objects.create(
                    operation=operation, model=model,
                    prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                    total_tokens=total_tokens, success=success,
                    latency_ms=latency_ms, error_msg=error_msg,
                    user=user,
                )
            except Exception:
                pass


EXPLAIN_SYSTEM = """你是一位耐心、专业的 GESP C++ 竞赛辅导老师，正在帮助学生复习考试错题。

当学生请求讲解时，请按以下结构回答：
1. **答题情况**：指出学生答对/答错，若答错说明学生选了什么
2. **知识点解析**：这道题考察了哪个知识点，给出详细解释
3. **正确答案解析**：逐步分析为什么正确答案是对的
4. **错误原因分析**（仅答错时）：学生答错的常见误区和可能原因
5. **记忆技巧**：帮助记住这类知识点的方法或口诀

之后学生可能继续追问，请耐心、简洁地回答。
语言亲切清晰，适合中学生。代码示例用 ```cpp``` 包裹。"""


def _get_client() -> OpenAI:
    cfg = _get_ai_config()
    # 优先用数据库配置（解密后），否则回退到 .env
    if cfg and cfg.api_key:
        api_key = decrypt_api_key(cfg.api_key)
    else:
        api_key = getattr(settings, 'DASHSCOPE_API_KEY', '')
    if not api_key:
        raise ValueError("API Key 未配置，请在管理页面 → AI设置 中填入，或在 backend/.env 中设置 DASHSCOPE_API_KEY")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


# ─── 核心调用（带用量记录）────────────────────────────────
def _call_qwen(
    messages: list,
    temperature: float = 0.3,
    model: str | None = None,
    operation: int | None = None,   # AIUsageLog.OP_TAG / OP_GEN / OP_TEST
) -> str:
    """
    调用 Qwen 模型，返回文本内容。
    - model: 未指定时使用 AIConfig.tag_model（或默认 qwen-plus）
    - operation: 若提供则写入 AIUsageLog
    """
    if model is None:
        cfg = _get_ai_config()
        model = (cfg.tag_model if cfg else None) or 'qwen-plus'

    client   = _get_client()
    start_ms = int(time.time() * 1000)

    prompt_tokens = completion_tokens = total_tokens = 0
    success   = False
    error_msg = ''
    content   = ''

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
        )
        content = resp.choices[0].message.content.strip()
        if resp.usage:
            prompt_tokens     = resp.usage.prompt_tokens     or 0
            completion_tokens = resp.usage.completion_tokens or 0
            total_tokens      = resp.usage.total_tokens      or 0
        success = True
        return content
    except Exception as e:
        error_msg = str(e)[:500]
        raise
    finally:
        latency_ms = int(time.time() * 1000) - start_ms
        if operation is not None:
            try:
                from .models import AIUsageLog
                AIUsageLog.objects.create(
                    operation         = operation,
                    model             = model,
                    prompt_tokens     = prompt_tokens,
                    completion_tokens = completion_tokens,
                    total_tokens      = total_tokens,
                    success           = success,
                    latency_ms        = latency_ms,
                    error_msg         = error_msg,
                )
            except Exception:
                pass  # 日志失败不影响主流程


def _extract_json(text: str):
    """从模型输出中提取 JSON（兼容 ```json...``` 和裸 JSON）"""
    block = re.search(r'```(?:json)?\s*([\[\{][\s\S]*?[\]\}])\s*```', text)
    if block:
        return json.loads(block.group(1))
    arr = re.search(r'(\[[\s\S]*\])', text)
    if arr:
        return json.loads(arr.group(1))
    obj = re.search(r'(\{[\s\S]*\})', text)
    if obj:
        return json.loads(obj.group(1))
    raise ValueError(f"模型未返回有效 JSON，原始内容: {text[:300]}")


# ─── 知识点标注 ───────────────────────────────────────────

_TAG_SYSTEM = """你是 GESP C++ 竞赛题目的知识点分类专家。
给你一道题目和一个知识点列表（包含多个级别），请从列表中选出最相关的 1~3 个知识点。

重要规则：
1. 知识点可以跨级别选择——高级别的题目完全可以考察低级别的知识点
2. 如果确实找不到合适的知识点，请选择对应级别的"其他/无法分类"知识点（若列表中存在）
3. 只返回知识点 ID 组成的 JSON 数组，不要输出任何解释

示例输出：[12, 35]"""


def suggest_tags_for_question(
    question_content: str,
    knowledge_points: list[dict],
    question_level: int | None = None,
    model: str | None = None,
) -> list[int]:
    """
    为单道题目建议知识点标签，支持跨级标注。
    knowledge_points: [{"id":1,"chapter":"顺序结构","name":"变量定义","level":1,"level_name":"GESP1级",...}]
    """
    if model is None:
        cfg = _get_ai_config()
        model = (cfg.tag_model if cfg else None) or 'qwen-plus'

    kp_lines = "\n".join(
        f"{kp['id']}. [{kp.get('level_name', '')} | {kp['chapter']}] {kp['name']}"
        + (f"：{kp['description']}" if kp.get('description') else "")
        for kp in knowledge_points
    )
    level_hint = (
        f"注意：该题目属于 GESP{question_level}级，但知识点可能来自更低级别，请跨级别匹配。\n\n"
        if question_level else ""
    )
    user_msg = f"{level_hint}知识点列表：\n{kp_lines}\n\n题目：\n{question_content}"

    from .models import AIUsageLog
    raw = _call_qwen(
        [{"role": "system", "content": _TAG_SYSTEM},
         {"role": "user",   "content": user_msg}],
        model=model,
        operation=AIUsageLog.OP_TAG,
    )
    result = _extract_json(raw)
    if isinstance(result, list):
        return [int(x) for x in result if str(x).isdigit() or isinstance(x, int)]
    return []


# ─── 题目生成 ─────────────────────────────────────────────

_GEN_SYSTEM = """你是 GESP C++ 竞赛题目出题专家。
请根据给定的知识点和示例题目，生成指定数量的新题目。
严格按照以下 JSON 数组格式输出，不要输出任何其他内容。

输出格式：
[
  {
    "question_type": "单选题",   // 单选题 / 判断题
    "difficulty": "简单",        // 简单 / 中等 / 困难
    "content": "题目正文（含代码用```包裹，行内代码用`包裹）",
    "option_a": "选项A",         // 判断题留空字符串
    "option_b": "选项B",
    "option_c": "选项C",
    "option_d": "选项D",
    "answer": "B",               // 单选填字母，判断题填 T 或 F
    "explanation": "解析"
  }
]

要求：
1. 题目要紧扣知识点，考察具体 C++ 语法或算法知识
2. 不要与示例题目完全相同，但可以类似风格
3. 代码题目中的代码要正确可运行
4. 答案必须是正确的
"""


def generate_questions(
    knowledge_point_name: str,
    knowledge_point_desc: str,
    chapter_name: str,
    level_name: str,
    question_type: int,
    count: int,
    examples: list[dict],
    model: str | None = None,
) -> list[dict]:
    """生成题目草稿列表（不入库）"""
    if model is None:
        cfg = _get_ai_config()
        model = (cfg.gen_model if cfg else None) or 'qwen-plus'

    type_name = "单选题" if question_type == 1 else "判断题"
    example_text = ""
    if examples:
        lines = [f"示例{i+1}：{q['content'][:200]}" for i, q in enumerate(examples[:3])]
        example_text = "\n\n参考示例题目（风格参考，勿照抄）：\n" + "\n".join(lines)

    user_msg = (
        f"级别：{level_name}\n"
        f"章节：{chapter_name}\n"
        f"知识点：{knowledge_point_name}\n"
        f"知识点说明：{knowledge_point_desc or '（无）'}\n"
        f"题目类型：{type_name}\n"
        f"需要生成：{count} 道"
        f"{example_text}"
    )

    from .models import AIUsageLog
    raw = _call_qwen(
        [{"role": "system", "content": _GEN_SYSTEM},
         {"role": "user",   "content": user_msg}],
        temperature=0.7,
        model=model,
        operation=AIUsageLog.OP_GEN,
    )

    questions_raw = _extract_json(raw)
    if not isinstance(questions_raw, list):
        raise ValueError("模型返回格式错误")

    TYPE_MAP = {"单选题": 1, "判断题": 3}
    DIFF_MAP = {"简单": 1, "中等": 2, "困难": 3}

    results = []
    for q in questions_raw:
        qtype   = TYPE_MAP.get(q.get("question_type", ""), question_type)
        options = []
        if qtype != 3:
            for key, field in [("A", "option_a"), ("B", "option_b"),
                                ("C", "option_c"), ("D", "option_d")]:
                text = (q.get(field) or "").strip()
                if text:
                    options.append({"key": key, "text": text})
        results.append({
            "question_type":  qtype,
            "difficulty":     DIFF_MAP.get(q.get("difficulty", "简单"), 1),
            "content":        (q.get("content") or "").strip(),
            "options":        options,
            "answer":         (q.get("answer") or "").strip().upper(),
            "explanation":    (q.get("explanation") or "").strip(),
            "source":         f"AI生成-{knowledge_point_name}",
            "source_type":    2,
        })
    return results
