#!/bin/bash

# AI Study Companion 启动脚本
# 自动安装依赖并启动前后端服务

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================="
echo "   AI Study Companion 启动中..."
echo "=================================="
echo "项目目录: $PROJECT_DIR"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi
echo "✓ Python3: $(python3 --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js"
    exit 1
fi
echo "✓ Node.js: $(node --version)"
echo ""

# ============ 后端设置 ============
echo "[1/4] 配置后端服务..."
cd "$PROJECT_DIR/backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "  创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "  激活虚拟环境..."
source venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import fastapi" 2>/dev/null; then
    echo "  安装 Python 依赖（首次运行可能需要几分钟）..."
    pip install -q -r requirements.txt
else
    echo "  ✓ Python 依赖已安装"
fi

# ============ 前端设置 ============
echo "[2/4] 配置前端服务..."
cd "$PROJECT_DIR/frontend"

# 检查依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo "  安装 npm 依赖（首次运行可能需要几分钟）..."
    npm install --silent --no-audit --no-fund
else
    echo "  ✓ npm 依赖已安装"
fi

# ============ 停止已存在的服务 ============
echo "[3/4] 检查并停止已运行的服务..."
# 查找并停止已运行的后端
BACKEND_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PID" ]; then
    echo "  停止旧的后端服务 (PID: $BACKEND_PID)"
    kill $BACKEND_PID 2>/dev/null || true
    sleep 1
fi

# 查找并停止已运行的前端
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$FRONTEND_PID" ]; then
    echo "  停止旧的前端服务 (PID: $FRONTEND_PID)"
    kill $FRONTEND_PID 2>/dev/null || true
    sleep 1
fi

# ============ 启动服务 ============
echo "[4/4] 启动服务..."
echo ""

# 启动后端
cd "$PROJECT_DIR/backend"
source venv/bin/activate
echo "▶ 启动后端服务..."
python main.py > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务启动成功"
else
    echo "  ❌ 后端服务启动失败，查看日志: $PROJECT_DIR/backend.log"
    cat "$PROJECT_DIR/backend.log"
    exit 1
fi

# 启动前端
cd "$PROJECT_DIR/frontend"
echo "▶ 启动前端服务..."
npm run dev > "$PROJECT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "  前端 PID: $FRONTEND_PID"

# 等待前端启动
sleep 3

# 检查前端是否启动成功
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "  ✓ 前端服务启动成功"
else
    echo "  ⚠ 前端服务启动中，请稍候..."
fi

# ============ 完成 ============
echo ""
echo "=================================="
echo "   🎉 启动完成！"
echo "=================================="
echo ""
echo "服务地址："
echo "  • 前端界面: http://localhost:3000"
echo "  • 后端 API: http://localhost:8000"
echo "  • API 文档: http://localhost:8000/docs"
echo ""
echo "日志文件："
echo "  • 后端日志: $PROJECT_DIR/backend.log"
echo "  • 前端日志: $PROJECT_DIR/frontend.log"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=================================="
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > "$PROJECT_DIR/.backend_pid"
echo "$FRONTEND_PID" > "$PROJECT_DIR/.frontend_pid"

# 清理函数
cleanup() {
    echo ""
    echo "停止服务..."
    if [ -f "$PROJECT_DIR/.backend_pid" ]; then
        kill $(cat "$PROJECT_DIR/.backend_pid") 2>/dev/null || true
    fi
    if [ -f "$PROJECT_DIR/.frontend_pid" ]; then
        kill $(cat "$PROJECT_DIR/.frontend_pid") 2>/dev/null || true
    fi
    rm -f "$PROJECT_DIR/.backend_pid" "$PROJECT_DIR/.frontend_pid"
    echo "服务已停止"
    exit 0
}

# 捕获退出信号
trap cleanup INT TERM

# 保持脚本运行
wait
