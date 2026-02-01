#!/bin/bash

# AI Study Companion - 快速部署脚本
# 使用方法: chmod +x quick-deploy.sh && ./quick-deploy.sh

set -e

echo "========================================"
echo "  AI Study Companion - 快速部署工具"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Node.js
echo -e "${BLUE}1. 检查环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 需要先安装 Node.js${NC}"
    echo "请访问 https://nodejs.org/ 下载安装"
    exit 1
fi
echo -e "${GREEN}✓ Node.js 已安装: $(node -v)${NC}"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm 已安装: $(npm -v)${NC}"

echo ""

# 检查是否安装了 Vercel CLI
echo -e "${BLUE}2. 检查 Vercel CLI...${NC}"
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}📦 正在安装 Vercel CLI...${NC}"
    npm install -g vercel
    echo -e "${GREEN}✓ Vercel CLI 安装完成${NC}"
else
    echo -e "${GREEN}✓ Vercel CLI 已安装${NC}"
fi

echo ""

# 进入前端目录
echo -e "${BLUE}3. 准备前端文件...${NC}"
cd frontend
echo -e "${GREEN}✓ 当前目录: $(pwd)${NC}"

# 安装依赖
echo -e "${BLUE}4. 安装依赖...${NC}"
npm install
echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo ""

# 构建前端
echo -e "${BLUE}5. 构建前端...${NC}"
npm run build
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 前端构建成功${NC}"
else
    echo -e "${RED}❌ 前端构建失败${NC}"
    exit 1
fi

echo ""

# 部署到 Vercel
echo -e "${BLUE}6. 部署到 Vercel...${NC}"
echo -e "${YELLOW}即将打开 Vercel 登录页面...${NC}"
echo -e "${YELLOW}请按照提示操作：${NC}"
echo "  1. 登录或注册 Vercel 账号"
echo "  2. 选择项目设置（使用默认值即可）"
echo "  3. 等待部署完成"
echo ""

sleep 2

# 部署
vercel --prod

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📱 您的微信分享链接：${NC}"
echo -e "   ${YELLOW}https://ai-study-companion.vercel.app${NC}"
echo "   (实际地址请查看上面的部署输出)"
echo ""
echo -e "${BLUE}📝 下一步：${NC}"
echo "   1. 配置后端 API 地址（见下方说明）"
echo "   2. 将生成的链接分享到微信"
echo "   3. 享受您的 AI 学习助手！"
echo ""
echo -e "${BLUE}🔧 后端 API 配置：${NC}"
echo "   如果已有后端 API 地址，请创建 frontend/.env.production："
echo "   echo 'VITE_API_URL=https://your-backend-api.com' > frontend/.env.production"
echo "   然后运行: vercel --prod"
echo ""
echo -e "${GREEN}========================================${NC}"
