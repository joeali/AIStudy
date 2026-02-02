# SSH隧道安全访问配置指南

## 第一步：在Mac上开启SSH服务

### 方法1：图形界面（推荐，最简单）

1. **打开系统设置**
   - 点击左上角  Apple 图标
   - 选择"系统设置"（System Settings）

2. **进入共享设置**
   - 点击左侧"通用"（General）
   - 点击"共享"（Sharing）

3. **开启远程登录**
   - 找到"远程登录"（Remote Login）
   - 点击右侧开关，设置为"开启"（On）

4. **配置访问权限**
   - 选择"所有用户"或"指定用户"
   - 记下Mac的用户名和IP地址

5. **完成！**
   - SSH服务已启动
   - 可以通过SSH远程访问

### 方法2：命令行（需要管理员权限）

```bash
# 开启SSH服务
sudo systemsetup -setremotelogin on

# 验证SSH服务状态
sudo systemsetup -getremotelogin

# 查看SSH服务运行状态
sudo launchctl list | grep ssh
```

---

## 第二步：获取本机信息

### 1. 查看用户名
```bash
whoami
# 输出示例: liulinlang
```

### 2. 查看内网IP
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
# 输出示例: inet 192.168.0.137 netmask 0xffffff00
```

### 3. 查看公网IP（外网访问需要）
```bash
curl ifconfig.me
# 输出示例: 125.118.5.207
```

---

## 第三步：设置SSH密钥（推荐，免密登录）

### 在Mac（服务器端）生成密钥对

```bash
# 1. 生成SSH密钥对（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按Enter使用默认路径
# 可以设置密码或直接按Enter跳过

# 2. 查看公钥
cat ~/.ssh/id_ed25519.pub
```

### 将公钥添加到授权密钥

```bash
# 1. 确保.ssh目录存在
mkdir -p ~/.ssh

# 2. 将公钥添加到authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# 3. 设置正确的权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 4. 验证配置
ls -la ~/.ssh/
```

### 复制私钥到远程设备

```bash
# 查看私钥（需要保密！）
cat ~/.ssh/id_ed25519

# 或通过安全方式传输
# 在远程设备上运行此命令（将Mac替换为你的IP）
ssh user@192.168.0.137 "cat ~/.ssh/id_ed25519.pub" >> ~/.ssh/authorized_keys
```

---

## 第四步：配置端口转发

### SSH隧道命令格式

```bash
# 基本格式
ssh -N -L [本地端口]:localhost:[远程端口] [用户名]@[服务器IP]

# 映射前端（3000端口）
ssh -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 映射后端（8000端口）
ssh -N -L 8000:localhost:8000 liulinlang@192.168.0.137

# 同时映射多个端口
ssh -N -L 3000:localhost:3000 -L 8000:localhost:8000 liulinlang@192.168.0.137
```

### 参数说明
- `-N`: 不执行远程命令，仅做端口转发
- `-L`: 本地端口转发
- `-f`: 后台运行（可选）
- `-C`: 压缩传输（可选，慢速网络有用）
- `-v`: 详细输出（调试用）

---

## 第五步：从不同设备访问

### 从Mac/Linux访问

#### 1. 终端建立SSH隧道
```bash
# 局域网访问
ssh -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 公网访问（需要配置路由器端口转发）
ssh -N -L 3000:localhost:3000 liulinlang@125.118.5.207 -p 22

# 后台运行
ssh -f -N -L 3000:localhost:3000 liulinlang@192.168.0.137
```

#### 2. 浏览器访问
```bash
# 在本地浏览器打开
open http://localhost:3000

# 或直接访问
http://localhost:3000
```

#### 3. 关闭SSH隧道
```bash
# 查找SSH进程
ps aux | grep "ssh.*3000"

# 结束进程
kill <PID>

# 或使用pkill
pkill -f "ssh.*3000"
```

### 从Windows访问

#### 方法1：使用PowerShell/CMD
```powershell
# 建立SSH隧道
ssh -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 浏览器访问
# http://localhost:3000
```

#### 方法2：使用PuTTY
1. 下载PuTTY: https://www.putty.org/
2. 配置Session:
   - Host Name: 192.168.0.137
   - Port: 22
3. 配置Tunnel:
   - Connection → SSH → Tunnels
   - Source port: 3000
   - Destination: localhost:3000
   - 点击"Add"
4. 点击"Open"建立连接
5. 浏览器访问: http://localhost:3000

### 从iPhone/iPad访问

#### 使用Termius（推荐）
1. App Store下载"Termius"
2. 添加Hosts:
   - Alias: MacBook
   - Hostname: 192.168.0.137
   - Port: 22
   - Username: liulinlang
   - Password: [或使用密钥]
3. 配置Local Port Forwarding:
   - Local Port: 3000
   - Host: localhost
   - Port: 3000
4. 保存并连接
5. Safari浏览器访问: http://localhost:3000

#### 使用Blink Shell
1. App Store下载"Blink Shell"
2. 配置SSH连接
3. 添加端口转发规则
4. 浏览器访问

### 从Android访问

#### 使用Termius（推荐）
1. Google Play下载"Termius"
2. 配置与iOS相同
3. 浏览器访问: http://localhost:3000

#### 使用JuiceSSH
1. Google Play下载"JuiceSSH"
2. 配置SSH连接
3. 添加端口转发

---

## 第六步：配置外网访问（可选）

### 需求：从互联网访问

#### 方案1：配置路由器端口转发

1. **登录路由器管理界面**
   - 地址通常是: http://192.168.0.1 或 http://192.168.1.1
   - 查看路由器背面的账号密码

2. **添加SSH端口转发规则**
   ```
   服务名称: SSH
   外部端口: 22
   内部IP: 192.168.0.137
   内部端口: 22
   协议: TCP
   状态: 启用
   ```

3. **测试公网SSH连接**
   ```bash
   ssh -N -L 3000:localhost:3000 liulinlang@125.118.5.207
   ```

#### 方案2：使用DDNS（动态域名）

**推荐服务：**
- No-IP: https://www.noip.com/
- DuckDNS: https://www.duckdns.org/
- DNSPod: https://www.dnspod.cn/

**配置步骤（以No-IP为例）：**
1. 注册No-IP账号
2. 创建免费域名（如: myhome.ddns.net）
3. 在Mac上安装ddclient
   ```bash
   brew install ddclient
   ```
4. 配置ddclient更新域名
5. 使用域名访问:
   ```bash
   ssh -N -L 3000:localhost:3000 liulinlang@myhome.ddns.net
   ```

---

## 实用脚本

### 快速建立SSH隧道脚本

创建文件 `ssh-tunnel.sh`:
```bash
#!/bin/bash

# 配置
REMOTE_USER="liulinlang"
REMOTE_IP="192.168.0.137"
LOCAL_PORT="3000"
REMOTE_PORT="3000"

# 建立SSH隧道
echo "正在建立SSH隧道..."
echo "本地端口: $LOCAL_PORT -> 远程端口: $REMOTE_PORT"

ssh -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_IP}

# 或者使用后台运行
# ssh -f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_IP}
```

使用方法：
```bash
chmod +x ssh-tunnel.sh
./ssh-tunnel.sh
```

### 自动重连脚本

创建文件 `ssh-tunnel-auto.sh`:
```bash
#!/bin/bash

REMOTE_USER="liulinlang"
REMOTE_IP="192.168.0.137"
LOCAL_PORT="3000"
REMOTE_PORT="3000"

while true; do
    echo "检查SSH隧道状态..."

    # 检查隧道是否存在
    if ! lsof -i :$LOCAL_PORT > /dev/null 2>&1; then
        echo "SSH隧道未运行，正在建立..."
        ssh -f -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_IP}
        echo "SSH隧道已建立"
    else
        echo "SSH隧道正在运行"
    fi

    # 每60秒检查一次
    sleep 60
done
```

---

## 安全建议

### 1. 使用密钥认证，禁用密码登录

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 修改以下配置
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# 重启SSH服务
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

### 2. 限制访问IP（可选）

```bash
# 编辑hosts.allow
sudo nano /etc/hosts.allow

# 添加允许的IP
sshd: 192.168.0.0/24
sshd: 10.0.0.0/8

# 编辑hosts.deny
sudo nano /etc/hosts.deny

# 拒绝所有其他IP
sshd: ALL
```

### 3. 修改SSH默认端口（可选）

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 修改端口
Port 2222

# 重启SSH服务
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd

# 连接时指定端口
ssh -p 2222 user@host
```

### 4. 安装Fail2ban防止暴力破解

```bash
# 安装Fail2ban
brew install fail2ban

# 配置jail
sudo nano /usr/local/etc/fail2ban/jail.local

[sshd]
enabled = true
port = ssh
logpath = /var/log/system.log
maxretry = 3
findtime = 600
bantime = 3600

# 启动服务
sudo brew services start fail2ban
```

---

## 故障排查

### 无法连接SSH？

```bash
# 1. 检查SSH服务状态
sudo systemsetup -getremotelogin

# 2. 检查SSH服务运行
ps aux | grep sshd

# 3. 检查防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --list

# 4. 测试SSH连接
ssh localhost

# 5. 查看SSH日志
log show --predicate 'process == "sshd"' --last 1h
```

### 端口转发不工作？

```bash
# 1. 检查本地端口是否被占用
lsof -i :3000

# 2. 查看SSH隧道进程
ps aux | grep "ssh.*-L"

# 3. 使用详细模式调试
ssh -v -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 4. 检查服务是否运行
curl http://localhost:3000
```

### 连接断开？

```bash
# 1. 添加keep-alive选项
ssh -o ServerAliveInterval=60 -N -L 3000:localhost:3000 user@host

# 2. 或在SSH配置中添加
echo "ServerAliveInterval 60" >> ~/.ssh/config
```

---

## 快速参考

### Mac本机信息
- **用户名**: liulinlang
- **内网IP**: 192.168.0.137
- **公网IP**: 125.118.5.207
- **SSH端口**: 22

### 常用命令

```bash
# 建立SSH隧道（局域网）
ssh -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 建立SSH隧道（公网）
ssh -N -L 3000:localhost:3000 liulinlang@125.118.5.207

# 后台运行
ssh -f -N -L 3000:localhost:3000 liulinlang@192.168.0.137

# 关闭隧道
pkill -f "ssh.*3000"

# 查看隧道状态
lsof -i :3000
```

### 访问地址

建立SSH隧道后，在浏览器访问：
```
http://localhost:3000
```

---

## 总结

SSH隧道访问的优势：
✅ 系统原生，无需额外软件
✅ 加密传输，安全可靠
✅ 灵活配置，端口转发
✅ 跨平台支持（Mac/Windows/Linux/手机）
✅ 免费使用

适用场景：
- 技术人员
- 需要频繁远程访问
- 对安全性要求高
- 需要访问多个服务
