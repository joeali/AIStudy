#!/bin/bash

# ========================================
# 公网SSH访问配置检查脚本
# ========================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置信息
REMOTE_USER="liulinlang"
LOCAL_IP="192.168.0.137"
PUBLIC_IP="125.118.5.207"
ROUTER_IP="192.168.0.1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  公网SSH访问配置检查工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查SSH服务状态
echo -e "${YELLOW}[1/6] 检查SSH服务状态...${NC}"
SSH_ENABLED=$(sudo systemsetup -getremotelogin 2>/dev/null)

if [[ "$SSH_ENABLED" == *"Remote Login: On"* ]]; then
    echo -e "${GREEN}✓ SSH服务已开启${NC}"
else
    echo -e "${RED}✗ SSH服务未开启${NC}"
    echo ""
    echo "请先开启SSH服务:"
    echo "  方法1 (图形界面):"
    echo "    系统设置 → 通用 → 共享 → 远程登录 → 开启"
    echo "  方法2 (命令行):"
    echo "    sudo systemsetup -setremotelogin on"
    echo ""
    exit 1
fi

# 2. 检查网络连接
echo -e "${YELLOW}[2/6] 检查网络连接...${NC}"

# 检查内网连接
if ping -c 1 -W 2 $LOCAL_IP >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 内网连接正常${NC} ($LOCAL_IP)"
else
    echo -e "${RED}✗ 内网连接失败${NC}"
    exit 1
fi

# 检查网关连接
if ping -c 1 -W 2 $ROUTER_IP >/dev/null 2>&1; then
    echo -e "${GREEN}✓ 路由器连接正常${NC} ($ROUTER_IP)"
else
    echo -e "${YELLOW}⚠ 无法连接到路由器${NC} ($ROUTER_IP)"
fi

# 检查公网连接
if curl -s --connect-timeout 5 ifconfig.me >/dev/null 2>&1; then
    CURRENT_PUBLIC_IP=$(curl -s ifconfig.me)
    echo -e "${GREEN}✓ 公网连接正常${NC} ($CURRENT_PUBLIC_IP)"

    if [ "$CURRENT_PUBLIC_IP" != "$PUBLIC_IP" ]; then
        echo -e "${YELLOW}  注意: 公网IP已变化${NC}"
        echo -e "${YELLOW}  旧IP: $PUBLIC_IP${NC}"
        echo -e "${YELLOW}  新IP: $CURRENT_PUBLIC_IP${NC}"
        PUBLIC_IP=$CURRENT_PUBLIC_IP
    fi
else
    echo -e "${RED}✗ 公网连接失败${NC}"
fi

# 3. 测试本地SSH
echo -e "${YELLOW}[3/6] 测试本地SSH服务...${NC}"

if ssh -o ConnectTimeout=5 -o BatchMode=yes localhost exit 2>/dev/null; then
    echo -e "${GREEN}✓ 本地SSH连接成功（已配置密钥）${NC}"
elif ssh -o ConnectTimeout=5 localhost exit 2>/dev/null; then
    echo -e "${GREEN}✓ 本地SSH连接成功（密码认证）${NC}"
else
    echo -e "${RED}✗ 本地SSH连接失败${NC}"
    echo "  请检查SSH服务是否正常运行"
fi

# 4. 检查防火墙
echo -e "${YELLOW}[4/6] 检查防火墙状态...${NC}"

if /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -q "enabled: 1"; then
    echo -e "${YELLOW}⚠ 系统防火墙已开启${NC}"

    if /usr/libexec/ApplicationFirewall/socketfilterfw --list 2>/dev/null | grep -q "sshd.*allow"; then
        echo -e "${GREEN}✓ SSH已被防火墙允许${NC}"
    else
        echo -e "${YELLOW}⚠ SSH可能被防火墙阻止${NC}"
        echo "  运行以下命令允许SSH:"
        echo "  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd"
        echo "  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/sbin/sshd"
    fi
else
    echo -e "${GREEN}✓ 防火墙未开启或已配置${NC}"
fi

# 5. 检查端口占用
echo -e "${YELLOW}[5/6] 检查端口占用情况...${NC}"

PORTS=(3000 8000)
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PROCESS=$(lsof -Pi :$PORT -sTCP:LISTEN -t | xargs ps -p | tail -1 | awk '{print $1}')
        echo -e "${GREEN}✓ 端口 $PORT 正在运行${NC} ($PROCESS)"
    else
        echo -e "${YELLOW}⚠ 端口 $PORT 未运行${NC}"
    fi
done

# 6. 测试公网SSH（可选）
echo -e "${YELLOW}[6/6] 测试公网SSH连接...${NC}"
echo -e "${YELLOW}注意: 此步骤需要路由器已配置端口转发${NC}"
echo ""
read -p "是否测试公网SSH连接? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在测试公网SSH连接到 $PUBLIC_IP..."

    if nc -z -w5 $PUBLIC_IP 22 2>/dev/null; then
        echo -e "${GREEN}✓ 公网SSH端口可达${NC}"
        echo "  可以建立SSH隧道！"
    else
        echo -e "${RED}✗ 公网SSH端口不可达${NC}"
        echo ""
        echo "请检查路由器端口转发配置:"
        echo "  1. 登录路由器: http://$ROUTER_IP"
        echo "  2. 找到'端口转发'或'虚拟服务器'设置"
        echo "  3. 添加以下规则:"
        echo "     外部端口: 22"
        echo "     内部IP: $LOCAL_IP"
        echo "     内部端口: 22"
        echo "     协议: TCP"
        echo "  4. 保存并重启路由器"
    fi
else
    echo "跳过公网SSH测试"
fi

# 生成配置报告
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  配置信息汇总${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "本机信息:"
echo "  用户名: $REMOTE_USER"
echo "  内网IP: $LOCAL_IP"
echo "  公网IP: $PUBLIC_IP"
echo "  路由器: $ROUTER_IP"
echo ""
echo "访问地址:"
echo "  内网前端: http://$LOCAL_IP:3000"
echo "  内网后端: http://$LOCAL_IP:8000"
echo ""
echo "SSH连接:"
echo "  内网: ssh $REMOTE_USER@$LOCAL_IP"
echo "  公网: ssh $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "隧道命令:"
echo "  # 前端隧道"
echo "  ssh -f -N -L 3000:localhost:3000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "  # 后端隧道"
echo "  ssh -f -N -L 8000:localhost:8000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "  # 同时建立前后端隧道"
echo "  ssh -f -N -L 3000:localhost:3000 -L 8000:localhost:8000 $REMOTE_USER@$PUBLIC_IP"
echo ""
echo "使用项目脚本:"
echo "  ./ssh-tunnel.sh public frontend"
echo "  ./ssh-tunnel.sh public both"
echo ""

# 提供下一步操作建议
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  下一步操作${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否完成所有配置
if [[ "$SSH_ENABLED" == *"Remote Login: On"* ]]; then
    if nc -z -w5 $PUBLIC_IP 22 2>/dev/null; then
        echo -e "${GREEN}✓ 公网访问已配置完成！${NC}"
        echo ""
        echo "您现在可以从互联网访问这台机器："
        echo ""
        echo "1. 在远程设备上建立SSH隧道:"
        echo "   ssh -f -N -L 3000:localhost:3000 $REMOTE_USER@$PUBLIC_IP"
        echo ""
        echo "2. 在浏览器访问:"
        echo "   http://localhost:3000"
        echo ""
        echo "或使用项目脚本:"
        echo "   ./ssh-tunnel.sh public both"
    else
        echo -e "${YELLOW}还需要配置路由器端口转发${NC}"
        echo ""
        echo "请按以下步骤操作:"
        echo ""
        echo "1. 打开浏览器访问: http://$ROUTER_IP"
        echo "2. 登录路由器管理界面"
        echo "3. 找到'端口转发'或'虚拟服务器'设置"
        echo "4. 添加SSH端口转发规则:"
        echo "   - 服务名称: SSH-Tunnel"
        echo "   - 外部端口: 22"
        echo "   - 内部IP: $LOCAL_IP"
        echo "   - 内部端口: 22"
        echo "   - 协议: TCP"
        echo "5. 保存并重启路由器"
        echo ""
        echo "配置完成后，运行此脚本再次测试:"
        echo "  ./setup-public-access.sh"
    fi
else
    echo -e "${YELLOW}还需要开启SSH服务${NC}"
    echo ""
    echo "请运行以下命令开启SSH:"
    echo "  sudo systemsetup -setremotelogin on"
    echo ""
    echo "或使用图形界面:"
    echo "  系统设置 → 通用 → 共享 → 远程登录 → 开启"
    echo ""
    echo "配置完成后，运行此脚本再次测试:"
    echo "  ./setup-public-access.sh"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo "详细配置说明请查看: PUBLIC_ACCESS_SETUP.md"
echo -e "${BLUE}========================================${NC}"
