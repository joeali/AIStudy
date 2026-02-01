#!/bin/bash

# AI Study Companion 停止脚本

echo "=================================="
echo "   停止 AI Study Companion"
echo "=================================="
echo ""

# 查找并停止后端
BACKEND_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$BACKEND_PID" ]; then
    echo "▶ 停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    sleep 1
    # 强制杀死（如果还在运行）
    kill -9 $BACKEND_PID 2>/dev/null || true
    echo "  ✓ 后端服务已停止"
else
    echo "  ℹ 后端服务未运行"
fi

# 查找并停止前端
FRONTEND_PID=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$FRONTEND_PID" ]; then
    echo "▶ 停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
    # 强制杀死（如果还在运行）
    kill -9 $FRONTEND_PID 2>/dev/null || true
    echo "  ✓ 前端服务已停止"
else
    echo "  ℹ 前端服务未运行"
fi

# 清理 PID 文件
rm -f /Users/liulinlang/Documents/liulinlang/ai-study-companion/.backend_pid
rm -f /Users/liulinlang/Documents/liulinlang/ai-study-companion/.frontend_pid

echo ""
echo "=================================="
echo "   ✅ 所有服务已停止"
echo "=================================="
