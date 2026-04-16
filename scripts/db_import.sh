#!/usr/bin/env bash
# =============================================================
#  GESP 训练平台 — 数据库导入脚本
#  用法：
#    方式一（推荐）：bash scripts/db_import.sh scripts/backups/backup_20250415_120000.tar.gz
#    方式二（目录）：bash scripts/db_import.sh scripts/backups/backup_20250415_120000/
#    方式三（SQLite）：bash scripts/db_import.sh path/to/db.sqlite3
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
DB_FILE="$BACKEND_DIR/db.sqlite3"

INPUT="${1:-}"

if [ -z "$INPUT" ]; then
    echo "用法：bash scripts/db_import.sh <备份文件或目录>"
    echo ""
    echo "可用备份："
    ls "$SCRIPT_DIR/backups/" 2>/dev/null | grep "backup_" || echo "  (无备份)"
    exit 1
fi

echo "=================================================="
echo "  GESP 数据库导入"
echo "  来源：$INPUT"
echo "=================================================="

# ── 解析输入类型 ────────────────────────────────────────────
WORK_DIR=""

if [[ "$INPUT" == *.tar.gz ]]; then
    # 解压 tar.gz
    echo ""
    echo "解压备份包..."
    EXTRACT_DIR="$SCRIPT_DIR/backups/_import_tmp"
    rm -rf "$EXTRACT_DIR"
    mkdir -p "$EXTRACT_DIR"
    tar -xzf "$INPUT" -C "$EXTRACT_DIR"
    # 找到解压出的第一个 backup_ 子目录
    WORK_DIR=$(find "$EXTRACT_DIR" -maxdepth 2 -type d -name "backup_*" | head -1)
    if [ -z "$WORK_DIR" ]; then
        WORK_DIR="$EXTRACT_DIR"
    fi
    echo "  ✓ 解压到：$WORK_DIR"
elif [ -d "$INPUT" ]; then
    WORK_DIR="$INPUT"
elif [[ "$INPUT" == *.sqlite3 ]]; then
    # 直接替换 SQLite 文件
    WORK_DIR=""
else
    echo "错误：不支持的输入格式 $INPUT"
    exit 1
fi

# ── 安全确认 ────────────────────────────────────────────────
echo ""
echo "⚠️  警告：此操作将覆盖当前数据库！"
echo "   当前数据库：$DB_FILE"
read -p "   确认继续？(输入 yes 继续) " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "已取消。"
    exit 0
fi

# ── 自动备份当前数据库 ──────────────────────────────────────
echo ""
echo "自动备份当前数据库..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
AUTO_BACKUP="$SCRIPT_DIR/backups/auto_before_import_${TIMESTAMP}.sqlite3"
mkdir -p "$SCRIPT_DIR/backups"
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$AUTO_BACKUP"
    echo "  ✓ 当前数据库已备份到：$AUTO_BACKUP"
fi

# ── 方式一：直接替换 SQLite 文件（最快）────────────────────
SQLITE_SRC=""
if [[ "$INPUT" == *.sqlite3 ]]; then
    SQLITE_SRC="$INPUT"
elif [ -n "$WORK_DIR" ] && [ -f "$WORK_DIR/db.sqlite3" ]; then
    SQLITE_SRC="$WORK_DIR/db.sqlite3"
fi

if [ -n "$SQLITE_SRC" ]; then
    echo ""
    echo "还原 SQLite 数据库文件..."
    cp "$SQLITE_SRC" "$DB_FILE"
    SIZE=$(du -sh "$DB_FILE" | cut -f1)
    echo "  ✓ 数据库已还原  ($SIZE)"
    echo ""
    echo "=================================================="
    echo "  导入完成（SQLite 文件替换）"
    echo "  请重启后端服务使更改生效。"
    echo "=================================================="
    # 清理临时目录
    [ -d "$SCRIPT_DIR/backups/_import_tmp" ] && rm -rf "$SCRIPT_DIR/backups/_import_tmp"
    exit 0
fi

# ── 方式二：通过 fixtures JSON 导入 ─────────────────────────
echo ""
echo "通过 Django fixtures 导入数据..."
cd "$BACKEND_DIR"

# 重置数据库（清空所有表，重新迁移）
echo "  重置数据库结构..."
rm -f "$DB_FILE"
python manage.py migrate --run-syncdb -v 0
echo "  ✓ 数据库结构已重建"

# 按顺序导入（注意外键依赖顺序）
FIXTURE_ORDER=(
    "fixture_auth_user.json"
    "fixture_users_userprofile.json"
    "fixture_users_classroom.json"
    "fixture_users_classroommember.json"
    "fixture_knowledge_gesplevel.json"
    "fixture_knowledge_chapter.json"
    "fixture_knowledge_knowledgepoint.json"
    "fixture_questions_question.json"
    "fixture_exams_examtemplate.json"
    "fixture_exams_examtemplatequestion.json"
    "fixture_exams_examrecord.json"
    "fixture_exams_examanswer.json"
    "fixture_practice_practicesession.json"
    "fixture_practice_practiceanswer.json"
    "fixture_practice_mistakerecord.json"
    "fixture_stats_userknowledgemastery.json"
    "fixture_stats_dailystudylog.json"
)

for fname in "${FIXTURE_ORDER[@]}"; do
    fpath="$WORK_DIR/$fname"
    if [ -f "$fpath" ]; then
        if python manage.py loaddata "$fpath" 2>/dev/null; then
            COUNT=$(python -c "import json; d=json.load(open('$fpath')); print(len(d))" 2>/dev/null || echo "?")
            echo "  ✓ $fname  ($COUNT 条)"
        else
            echo "  ✗ $fname  导入失败，请检查"
        fi
    else
        echo "  - $fname  (文件不存在，跳过)"
    fi
done

# 清理临时目录
[ -d "$SCRIPT_DIR/backups/_import_tmp" ] && rm -rf "$SCRIPT_DIR/backups/_import_tmp"

echo ""
echo "=================================================="
echo "  导入完成！"
echo "  请重启后端服务使更改生效。"
echo "=================================================="
