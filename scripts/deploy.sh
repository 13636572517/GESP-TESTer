#!/bin/bash
# 服务器端一键部署脚本
# 用法：bash /opt/gesp/scripts/deploy.sh

set -e

REPO_DIR="/opt/gesp"
FRONTEND_DIR="$REPO_DIR/frontend"
BACKEND_DIR="$REPO_DIR/backend"

echo "========================================"
echo "  GESP 考试模拟器 - 一键部署"
echo "========================================"

# 1. 拉取最新代码
echo ""
echo "[1/4] 拉取最新代码..."
cd "$REPO_DIR"
git pull origin main
echo "✓ 代码已更新"

# 2. 后端：数据库迁移 + 重启服务
echo ""
echo "[2/4] 执行数据库迁移..."
cd "$BACKEND_DIR"
source "$REPO_DIR/venv/bin/activate" 2>/dev/null || true
python manage.py migrate --no-input
echo "✓ 数据库迁移完成"

# 3. 前端：构建
echo ""
echo "[3/4] 构建前端..."
cd "$FRONTEND_DIR"
sudo npm run build
echo "✓ 前端构建完成"

# 4. 重启服务
echo ""
echo "[4/4] 重启服务..."
sudo systemctl restart gesp
sudo systemctl status gesp --no-pager -l | head -20
echo "✓ 服务已重启"

echo ""
echo "========================================"
echo "  部署完成！"
echo "========================================"
