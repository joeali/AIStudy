#!/bin/bash

# ========================================
# 公网SSH访问配置 - 自动化测试脚本
# ========================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  公网SSH访问配置测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 网络信息
REMOTE_USER="liulinlang"
LOCAL_IP="192.168.0.137"
PUBLIC_IP="125.118.5.207"
ROUTER_IP="192.168.0.1"

# 1. 显示当前配置信息
echo -e "${YELLOW}[1] 当前网络信息${NC}"
echo "  本机用户: $REMOTE_USER"
echo "  内网IP: $LOCAL_IP"
echo "  路由器: $ROUTER_IP"
echo "  公网IP: $PUBLIC_IP"
echo ""

# 2. 检查网络连接
echo -e "${YELLOW}[2] 测试网络连接${NC}"

# 测试本地回环
if ping -c 1 127.0.0.1 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 本地回环正常${NC}"
else
    echo -e "${RED}✗ 本地回环失败${NC}"
fi

# 测试网关
if ping -c 1 -W 2 $ROUTER_IP >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 路由器连接正常${NC} ($ROUTER_IP)"
else
    echo -e "${YELLOW}⚠ 无法连接路由器${NC}"
fi

# 测试公网
if curl -s --connect-timeout 5 ifconfig.me >/dev/null 2>&1; then
    CURRENT_IP=$(curl -s ifconfig.me)
    echo -e "${GREEN}✓ 公网连接正常${NC} ($CURRENT_IP)"
else
    echo -e "${RED}✗ 公网连接失败${NC}"
fi
echo ""

# 3. 检查SSH服务（尝试多种方式）
echo -e "${YELLOW}[3] 检查SSH服务状态${NC}"

SSH_RUNNING=false

# 方法1：检查进程
if pgrep -x sshd >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH服务正在运行${NC} (进程检测)"
    SSH_RUNNING=true
fi

# 方法2：尝试本地连接
if timeout 3 bash -c "echo > /dev/tcp/localhost/22" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH端口22正在监听${NC} (端口检测)"
    SSH_RUNNING=true
fi

# 方法3：使用netstat
if netstat -an | grep "\.22 " | grep LISTEN >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH端口22正在监听${NC} (netstat检测)"
    SSH_RUNNING=true
fi

if ! $SSH_RUNNING; then
    echo -e "${RED}✗ SSH服务未运行${NC}"
    echo ""
    echo "请手动开启SSH服务："
    echo ""
    echo "方法1 - 图形界面（推荐）："
    echo "  1. 点击左上角 Apple 图标"
    echo "  2. 选择'系统设置'"
    echo "  3. 点击'通用' → '共享'"
    echo "  4. 开启'远程登录'"
    echo ""
    echo "方法2 - 命令行："
    echo "  sudo systemsetup -setremotelogin on"
    echo ""
    read -p "SSH服务已开启？按Enter继续..."
fi
echo ""

# 4. 测试本地SSH
echo -e "${YELLOW}[4] 测试本地SSH连接${NC}"

if $SSH_RUNNING; then
    if timeout 3 ssh -o BatchMode=yes -o ConnectTimeout=2 localhost exit 2>/dev/null; then
        echo -e "${GREEN}✓ 本地SSH连接成功（密钥认证）${NC}"
    elif timeout 3 ssh -o ConnectTimeout=2 localhost "echo test" 2>/dev/null | grep -q test; then
        echo -e "${GREEN}✓ 本地SSH连接成功（密码认证）${NC}"
    else
        echo -e "${YELLOW}⚠ SSH服务运行但连接测试失败${NC}"
        echo "  可能需要首次连接确认"
    fi
else
    echo -e "${RED}✗ SSH服务未运行，跳过测试${NC}"
fi
echo ""

# 5. 检查应用服务
echo -e "${YELLOW}[5] 检查应用服务状态${NC}"

# 检查前端
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行中${NC} (端口3000)"
else
    echo -e "${YELLOW}⚠ 前端服务未运行${NC} (端口3000)"
fi

# 检查后端
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行中${NC} (端口8000)"
else
    echo -e "${YELLOW}⚠ 后端服务未运行${NC} (端口8000)"
fi
echo ""

# 6. 生成配置指南
echo -e "${YELLOW}[6] 生成路由器配置指南${NC}"
echo ""
echo "请在路由器中配置以下端口转发规则："
echo ""
echo "┌─────────────────────────────────────┐"
echo "│  SSH端口转发（必需）              │"
echo "├─────────────────────────────────────┤"
echo "│  服务名称: SSH-Tunnel              │"
echo "│  外部端口: 22                       │"
echo "│  内部IP:   192.168.0.137           │"
echo "│  内部端口: 22                       │"
echo "│  协议:    TCP                       │"
echo "└─────────────────────────────────────┘"
echo ""
echo "配置步骤："
echo "  1. 打开浏览器访问: http://$ROUTER_IP"
echo "  2. 登录路由器（查看路由器背面的账号密码）"
echo "  3. 找到'端口转发'或'虚拟服务器'设置"
echo "  4. 添加上述规则并保存"
echo "  5. 重启路由器使配置生效"
echo ""

# 7. 测试公网SSH（可选）
echo -e "${YELLOW}[7] 测试公网SSH可达性${NC}"
read -p "是否测试公网SSH连接？(需要路由器已配置) (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在测试公网SSH连接到 $PUBLIC_IP..."

    if timeout 5 bash -c "echo > /dev/tcp/$PUBLIC_IP/22" 2>/dev/null; then
        echo -e "${GREEN}✓ 公网SSH端口可达！${NC}"
        echo ""
        echo "🎉 恭喜！公网SSH访问配置成功！"
        echo ""
        echo "现在可以从互联网建立SSH隧道："
        echo ""
        echo "  # 建立前端隧道"
        echo "  ssh -f -N -L 3000:localhost:3000 $REMOTE_USER@$PUBLIC_IP"
        echo ""
        echo "  # 使用自动化脚本"
        echo "  ./ssh-tunnel.sh public frontend"
        echo ""
        echo "  # 浏览器访问"
        echo "  http://localhost:3000"
    else
        echo -e "${RED}✗ 公网SSH端口不可达${NC}"
        echo ""
        echo "可能的原因："
        echo "  1. 路由器端口转发未配置或配置错误"
        echo "  2. 路由器未重启"
        echo "  3. 防火墙阻止了连接"
        echo ""
        echo "请检查路由器配置后重试"
    fi
else
    echo "跳过公网测试"
fi
echo ""

# 8. 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  配置总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "访问地址："
echo "  本机:     http://localhost:3000"
echo "  内网:     http://$LOCAL_IP:3000"
echo "  公网:     通过SSH隧道访问"
echo ""
echo "SSH连接："
echo "  内网:     ssh $REMOTE_USER@$LOCAL_IP"
echo "  公网:     ssh $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "隧道命令："
echo "  # 前端"
echo "  ssh -f -N -L 3000:localhost:3000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "  # 后端"
echo "  ssh -f -N -L 8000:localhost:8000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "  # 前后端"
echo "  ssh -f -N -L 3000:localhost:3000 -L 8000:localhost:8000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "使用项目脚本："
echo "  ./ssh-tunnel.sh public frontend"
echo "  ./ssh-tunnel.sh public both"
echo ""
echo "📚 详细文档："
echo "  - QUICK_PUBLIC_ACCESS.md (快速开始)"
echo "  - PUBLIC_ACCESS_SETUP.md (完整手册)"
echo ""
