#!/bin/bash

# ========================================
# SSH隧道快速启动脚本
# ========================================

# 配置信息
REMOTE_USER="liulinlang"
REMOTE_IP="192.168.0.137"
REMOTE_IP_PUBLIC="125.118.5.207"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "========================================="
    echo "  SSH隧道快速启动脚本"
    echo "========================================="
    echo ""
    echo "用法: ./ssh-tunnel.sh [选项]"
    echo ""
    echo "选项:"
    echo "  frontend, fe   - 转发前端端口(3000)"
    echo "  backend, be    - 转发后端端口(8000)"
    echo "  both, all      - 同时转发前端和后端"
    echo "  public         - 通过公网IP访问"
    echo "  status         - 查看隧道状态"
    echo "  stop           - 停止所有隧道"
    echo "  help           - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./ssh-tunnel.sh frontend    # 转发前端"
    echo "  ./ssh-tunnel.sh both        # 转发前后端"
    echo "  ./ssh-tunnel.sh public both # 公网访问前后端"
    echo ""
}

# 检查SSH服务状态
check_ssh() {
    echo -e "${YELLOW}检查SSH服务...${NC}"

    if pgrep -x "sshd" > /dev/null; then
        echo -e "${GREEN}✓ SSH服务正在运行${NC}"
        return 0
    else
        echo -e "${RED}✗ SSH服务未运行${NC}"
        echo ""
        echo "请先开启SSH服务:"
        echo "  系统设置 -> 通用 -> 共享 -> 远程登录 -> 开启"
        return 1
    fi
}

# 建立SSH隧道
create_tunnel() {
    local local_port=$1
    local remote_port=$2
    local remote_ip=$3

    echo -e "${YELLOW}正在建立SSH隧道...${NC}"
    echo "  本地端口: $local_port"
    echo "  远程端口: $remote_port"
    echo "  远程IP: $remote_ip"
    echo ""

    # 检查端口是否已被占用
    if lsof -Pi :$local_port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ 端口 $local_port 已被占用${NC}"
        echo "  使用 './ssh-tunnel.sh status' 查看详情"
        echo "  使用 './ssh-tunnel.sh stop' 停止所有隧道"
        return 1
    fi

    # 建立SSH隧道
    ssh -f -N -L ${local_port}:localhost:${remote_port} ${REMOTE_USER}@${remote_ip}

    # 等待连接建立
    sleep 2

    # 验证隧道是否建立成功
    if lsof -Pi :$local_port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✓ SSH隧道建立成功！${NC}"
        echo ""
        echo "  访问地址: http://localhost:${local_port}"
        echo ""
        echo "使用 './ssh-tunnel.sh status' 查看状态"
        echo "使用 './ssh-tunnel.sh stop' 停止隧道"
        return 0
    else
        echo -e "${RED}✗ SSH隧道建立失败${NC}"
        echo "  请检查:"
        echo "  1. SSH服务是否开启"
        echo "  2. 网络连接是否正常"
        echo "  3. 用户名和IP是否正确"
        return 1
    fi
}

# 查看隧道状态
show_status() {
    echo "========================================="
    echo "  SSH隧道状态"
    echo "========================================="
    echo ""

    local frontend=$(lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 && echo "运行中" || echo "未运行")
    local backend=$(lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 && echo "运行中" || echo "未运行")

    echo "前端隧道(3000): $frontend"
    echo "后端隧道(8000): $backend"
    echo ""

    echo "SSH隧道进程:"
    ps aux | grep "ssh.*-f.*-N" | grep -v grep | awk '{print "  PID:", $2, $11, $12, $13, $14, $15}'
}

# 停止所有隧道
stop_tunnels() {
    echo -e "${YELLOW}正在停止所有SSH隧道...${NC}"

    local count=0
    pkill -f "ssh.*-f.*-N.*-L" && count=$((count + 1))

    if [ $count -gt 0 ]; then
        echo -e "${GREEN}✓ 已停止 $count 个SSH隧道${NC}"
    else
        echo -e "${YELLOW}没有运行的SSH隧道${NC}"
    fi
}

# 主程序
main() {
    case "$1" in
        frontend|fe)
            check_ssh && create_tunnel 3000 3000 $REMOTE_IP
            ;;
        backend|be)
            check_ssh && create_tunnel 8000 8000 $REMOTE_IP
            ;;
        both|all)
            check_ssh && create_tunnel 3000 3000 $REMOTE_IP && create_tunnel 8000 8000 $REMOTE_IP
            ;;
        public)
            case "$2" in
                frontend|fe)
                    check_ssh && create_tunnel 3000 3000 $REMOTE_IP_PUBLIC
                    ;;
                backend|be)
                    check_ssh && create_tunnel 8000 8000 $REMOTE_IP_PUBLIC
                    ;;
                both|all|"")
                    check_ssh && create_tunnel 3000 3000 $REMOTE_IP_PUBLIC && create_tunnel 8000 8000 $REMOTE_IP_PUBLIC
                    ;;
                *)
                    echo -e "${RED}错误: 未知选项 '$2'${NC}"
                    echo "使用 './ssh-tunnel.sh help' 查看帮助"
                    exit 1
                    ;;
            esac
            ;;
        status)
            show_status
            ;;
        stop)
            stop_tunnels
            ;;
        help|"")
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知选项 '$1'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
