#!/bin/bash

echo "========================================"
echo "   AI Study Companion - 一键部署脚本"
echo "========================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取项目根目录
PROJECT_DIR="/Users/liulinlang/Documents/liulinlang/ai-study-companion"

echo -e "${BLUE}步骤 1/5: 准备部署环境...${NC}"
echo "项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"
echo -e "${GREEN}✓ 进入项目目录${NC}"
echo ""

echo -e "${BLUE}步骤 2/5: 检查 Vercel CLI...${NC}"
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}正在安装 Vercel CLI...${NC}"
    npm install -g vercel
fi
echo -e "${GREEN}✓ Vercel CLI 已就绪${NC}"
echo ""

echo -e "${BLUE}步骤 3/5: 构建前端...${NC}"
cd frontend
npm install
npm run build
echo -e "${GREEN}✓ 前端构建完成${NC}"
echo ""

echo -e "${BLUE}步骤 4/5: 部署到 Vercel...${NC}"
echo ""
echo -e "${YELLOW}即将打开浏览器进行 Vercel 登录...${NC}"
echo "请按照浏览器提示完成以下操作："
echo "  1. 选择登录方式（推荐使用 GitHub 或 Email）"
echo "  2. 授权 Vercel 访问您的账户"
echo "  3. 返回终端继续部署"
echo ""

# 检查是否已登录
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}需要先登录 Vercel...${NC}"
    vercel login
fi

# 开始部署
echo ""
echo -e "${BLUE}开始部署...${NC}"
echo ""

# 部署命令
cd "$PROJECT_DIR/frontend"
vercel --prod --yes

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📱 您的微信分享链接：${NC}"
echo -e "${YELLOW}请查看上面的部署输出，会显示类似这样的地址：${NC}"
echo ""
echo -e "   ${GREEN}https://ai-study-companion-xxx.vercel.app${NC}"
echo ""
echo -e "${BLUE}📝 下一步：${NC}"
echo "   1. 复制上面的访问地址"
echo "   2. 在微信中发送给自己测试"
echo "   3. 确认可以正常打开"
echo ""
echo -e "${BLUE}🔧 配置后端 API（可选）：${NC}"
echo "   如果需要连接后端 API，请："
echo "   1. 编辑 frontend/.env.production 文件"
echo "   2. 添加: VITE_API_URL=https://your-backend-api.com"
echo "   3. 运行: vercel --prod --yes"
echo ""
echo -e "${GREEN}========================================${NC}"
