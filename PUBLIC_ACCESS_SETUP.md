# 公网SSH访问配置完整指南

## 当前网络信息

- **本机用户名**: liulinlang
- **内网IP**: 192.168.0.137
- **公网IP**: 125.118.5.207
- **路由器地址**: 192.168.0.1
- **SSH端口**: 22

---

## 配置步骤

### 第一步：在Mac上开启SSH服务

#### 方法1：图形界面（推荐）

1. 打开"系统设置"
   - 点击左上角  Apple 图标
   - 选择"系统设置"

2. 进入"共享"设置
   - 点击左侧"通用"
   - 点击"共享"

3. 开启"远程登录"
   - 找到"远程登录"
   - 点击右侧开关，设置为"开启"

4. 配置访问权限
   - 选择"允许访问" → "这些用户"
   - 添加您的用户账号
   - 或选择"所有用户"

5. 验证SSH已开启
   ```bash
   # 应该看到SSH服务运行
   sudo systemsetup -getremotelogin
   ```

#### 方法2：命令行

```bash
# 开启SSH服务
sudo systemsetup -setremotelogin on

# 验证
sudo systemsetup -getremotelogin
# 应该输出: Remote Login: On
```

---

### 第二步：配置路由器端口转发

#### 登录路由器管理界面

1. **打开浏览器访问路由器**
   ```
   http://192.168.0.1
   ```

2. **输入路由器账号密码**
   - 查看路由器背面标签
   - 常见默认账号:
     - 用户名: `admin` 密码: `admin`
     - 用户名: `admin` 密码: `password`
     - 用户名: `root` 密码: `admin`

3. **如果忘记密码，重置路由器**
   - 长按路由器背面Reset按钮10秒
   - 重新设置WiFi和密码

#### 配置端口转发规则

找到以下位置之一：
- "端口转发" / "Port Forwarding"
- "虚拟服务器" / "Virtual Server"
- "NAT设置" / "NAT Settings"
- "高级设置" → "端口转发"

**添加SSH端口转发规则：**

| 配置项 | 值 |
|-------|-----|
| 服务名称 | SSH-Tunnel |
| 外部端口 (WAN) | 22 |
| 内部IP (LAN) | 192.168.0.137 |
| 内部端口 | 22 |
| 协议 | TCP |
| 状态 | 启用/开启 |

**如果需要同时访问前端和后端，添加以下规则：**

**前端服务（3000端口）：**
| 配置项 | 值 |
|-------|-----|
| 服务名称 | AIStudy-Frontend |
| 外部端口 | 3000 |
| 内部IP | 192.168.0.137 |
| 内部端口 | 3000 |
| 协议 | TCP |

**后端服务（8000端口）：**
| 配置项 | 值 |
|-------|-----|
| 服务名称 | AIStudy-Backend |
| 外部端口 | 8000 |
| 内部IP | 192.168.0.137 |
| 内部端口 | 8000 |
| 协议 | TCP |

4. **保存并重启路由器**
   - 点击"应用"或"保存"
   - 重启路由器使配置生效

---

### 第三步：配置Mac防火墙

```bash
# 允许SSH通过防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/sbin/sshd
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/sbin/sshd

# 或在系统设置中配置
# 系统设置 → 网络 → 防火墙 → 防火墙选项
# 添加"远程登录"并允许传入连接
```

---

### 第四步：测试公网SSH连接

#### 1. 从本机测试

```bash
# 测试本地SSH
ssh localhost

# 应该看到登录成功提示
# 输入Mac登录密码后进入Shell
```

#### 2. 从内网其他设备测试

```bash
# 在同一WiFi的其他设备上测试
ssh liulinlang@192.168.0.137
```

#### 3. 从外网测试（需要手机4G/5G网络）

```bash
# 断开WiFi，使用手机网络
# 或从朋友的网络测试

ssh liulinlang@125.118.5.207
```

**如果连接超时：**
- 检查路由器端口转发是否正确
- 检查防火墙是否允许
- 确认SSH服务已开启

**如果连接被拒绝：**
- 确认用户名正确
- 检查SSH服务状态

---

### 第五步：使用公网SSH隧道

#### 配置公网SSH隧道脚本

使用项目中的脚本：

```bash
# 进入项目目录
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion

# 通过公网建立前端隧道
./ssh-tunnel.sh public frontend

# 通过公网建立前后端隧道
./ssh-tunnel.sh public both
```

#### 手动建立SSH隧道

```bash
# 前端隧道
ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207

# 后端隧道
ssh -f -N -L 8000:localhost:8000 liulinlang@125.118.5.207

# 同时建立前后端隧道
ssh -f -N -L 3000:localhost:3000 -L 8000:localhost:8000 liulinlang@125.118.5.207
```

#### 访问应用

建立隧道后，在浏览器访问：
```
http://localhost:3000  # 前端
http://localhost:8000  # 后端API
```

---

## 安全加固（强烈推荐）

### 1. 修改SSH默认端口

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 修改端口（改为不常见的端口）
# Port 22
Port 2222

# 重启SSH服务
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

**修改路由器端口转发：**
- 外部端口改为: 2222
- 内部端口改为: 2222

**连接时指定端口：**
```bash
ssh -p 2222 liulinlang@125.118.5.207
```

### 2. 配置SSH密钥认证

```bash
# 生成SSH密钥对
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥到authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# 设置正确权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 3. 禁用密码登录（仅密钥）

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 修改以下配置
PasswordAuthentication no
PubkeyAuthentication yes

# 重启SSH
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

### 4. 限制SSH访问IP

```bash
# 配置TCP包装器
sudo nano /etc/hosts.allow

# 添加允许的IP（可以是整个网段）
sshd: 192.168.0.0/24
sshd: 10.0.0.0/8

sudo nano /etc/hosts.deny

# 拒绝所有其他IP
sshd: ALL
```

### 5. 安装Fail2ban防暴力破解

```bash
# 安装
brew install fail2ban

# 创建配置
sudo nano /usr/local/etc/fail2ban/jail.local

[sshd]
enabled = true
port = 22
logpath = /var/log/system.log
maxretry = 3
findtime = 600
bantime = 3600

# 启动服务
sudo brew services start fail2ban
```

---

## 常见问题

### Q1: 路由器找不到端口转发设置？

**尝试以下位置：**
1. "高级设置" → "端口转发"
2. "NAT" → "端口映射"
3. "虚拟服务器"
4. "游戏设置" → "端口映射"

### Q2: 配置后仍然无法连接？

**检查清单：**
```bash
# 1. 确认SSH服务开启
sudo systemsetup -getremotelogin

# 2. 检查SSH服务运行
ps aux | grep sshd

# 3. 检查防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --list

# 4. 检查端口监听
netstat -an | grep :22

# 5. 测试本地SSH
ssh localhost
```

### Q3: 如何知道公网IP变化了？

```bash
# 查看当前公网IP
curl ifconfig.me

# 配置DDNS（动态域名）
# 推荐: No-IP, DuckDNS, DNSPod
```

### Q4: 连接速度慢怎么办？

```bash
# 启用SSH压缩
ssh -C -N -L 3000:localhost:3000 liulinlang@125.118.5.207

# 或在SSH配置中添加
echo "Compression yes" >> ~/.ssh/config
```

---

## 端口转发配置示例（常见路由器品牌）

### TP-Link路由器

1. 登录: http://192.168.0.1
2. "转发规则" → "虚拟服务器"
3. 点击"添加新条目"
4. 填写：
   - 服务端口: 22
   - 内部端口: 22
   - IP地址: 192.168.0.137
   - 协议: TCP
   - 状态: 生效

### 华硕/ASUS路由器

1. 登录: http://192.168.0.1
2. "外部网络(WAN)" → "端口转发"
3. 添加端口转发配置
4. 勾选"启用端口转发"

### 小米路由器

1. 登录: http://192.168.0.1
2. "高级设置" → "端口转发"
3. 添加规则
4. 保存并应用

### 网件(Netgear)路由器

1. 登录: http://192.168.0.1
2. "高级" → "高级设置" → "端口转发/端口触发"
3. 添加自定义服务
4. 保存

### 腾达/TP-Link企业级

1. 登录: http://192.168.0.1
2. "NAT" → "NAT设置" → "虚拟服务器"
3. 添加新条目
4. 保存

---

## 完成配置后的访问地址

### 内网访问（局域网内）
```
前端: http://192.168.0.137:3000
后端: http://192.168.0.137:8000
SSH:  ssh liulinlang@192.168.0.137
```

### 外网访问（互联网）
```
通过SSH隧道访问:
1. 建立隧道: ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
2. 浏览器访问: http://localhost:3000

直接访问（如果配置了3000端口转发）:
前端: http://125.118.5.207:3000
后端: http://125.118.5.207:8000
```

---

## 维护建议

1. **定期检查SSH日志**
   ```bash
   log show --predicate 'process == "sshd"' --last 1d
   ```

2. **监控异常登录**
   ```bash
   last | head -20
   ```

3. **定期更新系统**
   ```bash
   softwareupdate -l  # 检查更新
   softwareupdate -i -a  # 安装更新
   ```

4. **定期更换密码**
   ```bash
   # 修改Mac用户密码
   # 系统设置 → 用户与群组 → 更改密码
   ```

---

## 快速参考

### 本机信息
- 用户名: liulinlang
- 内网IP: 192.168.0.137
- 公网IP: 125.118.5.207
- SSH端口: 22

### 常用命令

```bash
# 开启SSH
sudo systemsetup -setremotelogin on

# 检查SSH状态
sudo systemsetup -getremotelogin

# 测试SSH连接
ssh localhost

# 建立公网SSH隧道
ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207

# 查看SSH进程
ps aux | grep ssh

# 停止SSH隧道
pkill -f "ssh.*-N.*-L"

# 查看公网IP
curl ifconfig.me
```

### 使用脚本

```bash
# 进入项目目录
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion

# 公网访问前端
./ssh-tunnel.sh public frontend

# 公网访问前后端
./ssh-tunnel.sh public both

# 查看状态
./ssh-tunnel.sh status

# 停止隧道
./ssh-tunnel.sh stop
```
