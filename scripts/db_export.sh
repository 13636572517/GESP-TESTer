#!/usr/bin/env bash
# =============================================================
#  GESP 训练平台 — 数据库导出脚本
#  用法：bash scripts/db_export.sh [输出目录]
#  默认输出到 scripts/backups/
# =============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
DB_FILE="$BACKEND_DIR/db.sqlite3"

# 输出目录：命令行第一个参数，默认为 scripts/backups/
OUTPUT_DIR="${1:-$SCRIPT_DIR/backups}"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$OUTPUT_DIR/backup_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "=================================================="
echo "  GESP 数据库导出"
echo "  时间：$TIMESTAMP"
echo "  输出：$BACKUP_DIR"
echo "=================================================="

# ── 1. 直接复制 SQLite 文件（最完整，可直接替换恢复）──────────
echo ""
echo "[1/2] 复制 SQLite 原始文件..."
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/db.sqlite3"
    SIZE=$(du -sh "$BACKUP_DIR/db.sqlite3" | cut -f1)
    echo "  ✓ db.sqlite3  ($SIZE)"
else
    echo "  ✗ 未找到数据库文件：$DB_FILE"
    exit 1
fi

# ── 2. Django fixtures JSON（可读、可跨数据库迁移）───────────
echo ""
echo "[2/2] 导出 Django fixtures (JSON)..."
cd "$BACKEND_DIR"

APPS=(
    "auth.user"
    "users.userprofile"
    "users.classroom"
    "users.classroommember"
    "knowledge.gesplevel"
    "knowledge.chapter"
    "knowledge.knowledgepoint"
    "questions.question"
    "exams.examtemplate"
    "exams.examtemplatequestion"
    "exams.examrecord"
    "exams.examanswer"
    "practice.practicesession"
    "practice.practiceanswer"
    "practice.mistakerecord"
    "stats.userknowledgemastery"
    "stats.dailystudylog"
)

for app_model in "${APPS[@]}"; do
    app_name=$(echo "$app_model" | tr '.' '_')
    out_file="$BACKUP_DIR/fixture_${app_name}.json"
    if PYTHONIOENCODING=utf-8 python manage.py dumpdata "$app_model" \
            --indent 2 > "$out_file" 2>/dev/null; then
        COUNT=$(python -c "
import json, sys
with open('$out_file', encoding='utf-8') as f:
    print(len(json.load(f)))
" 2>/dev/null || echo "?")
        echo "  ✓ $app_model  ($COUNT 条)"
    else
        echo "  - $app_model  (跳过，表可能不存在)"
        rm -f "$out_file"
    fi
done

# ── 3. 打包成 .tar.gz ─────────────────────────────────────
echo ""
echo "打包备份文件..."
cd "$OUTPUT_DIR"
tar -czf "backup_${TIMESTAMP}.tar.gz" "backup_$TIMESTAMP/"
ARCHIVE_SIZE=$(du -sh "backup_${TIMESTAMP}.tar.gz" | cut -f1)
echo "  ✓ backup_${TIMESTAMP}.tar.gz  ($ARCHIVE_SIZE)"

# 保留原始目录（方便直接查看），可选删除：
# rm -rf "$BACKUP_DIR"

echo ""
echo "=================================================="
echo "  导出完成！"
echo "  归档包：$OUTPUT_DIR/backup_${TIMESTAMP}.tar.gz"
echo "  原始目录：$BACKUP_DIR"
echo "=================================================="
