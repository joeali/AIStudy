# 公网访问配置 - 快速开始

## 📋 当前状态

- ✅ 网络连接正常
- ❌ SSH服务未开启（需要开启）
- ⏳ 路由器端口转发（需要配置）

---

## 🚀 3步完成公网访问配置

### 第1步：开启Mac的SSH服务

#### 方法A：图形界面（最简单，推荐）

1. **打开系统设置**
   - 点击屏幕左上角  Apple 图标
   - 选择"系统设置"

2. **进入共享设置**
   - 点击左侧菜单的"通用"
   - 点击右侧的"共享"

3. **开启远程登录**
   - 找到"远程登录"选项
   - 点击右侧的开关，启用该功能
   - 选择"允许访问" → "这些用户：您电脑的用户"
   - 确认您的用户在列表中

4. **完成！**
   - 看到绿色的"远程登录：已开启"说明配置成功

#### 方法B：命令行（需要管理员密码）

打开终端，运行：
```bash
sudo systemsetup -setremotelogin on
```
输入Mac登录密码后完成。

---

### 第2步：配置路由器端口转发

1. **打开浏览器，访问路由器管理界面**
   ```
   http://192.168.0.1
   ```

2. **登录路由器**
   - 查看路由器背面的账号密码标签
   - 常见默认账号：
     - 用户名：`admin`  密码：`admin`
     - 用户名：`admin`  密码：`password`
     - 用户名：`root`   密码：`admin`

3. **找到端口转发设置**

   在路由器管理界面中，找到以下任一位置：
   - "端口转发" / "Port Forwarding"
   - "虚拟服务器" / "Virtual Server"
   - "NAT设置" / "NAT Settings"
   - "高级设置" → "端口转发"
   - "游戏设置" → "端口映射"

4. **添加SSH端口转发规则**

   填写以下信息：

   | 配置项 | 填写内容 |
   |-------|---------|
   | 服务名称 | SSH-Tunnel |
   | 外部端口(WAN) | 22 |
   | 内部IP地址 | 192.168.0.137 |
   | 内部端口 | 22 |
   | 协议 | TCP |
   | 状态 | 启用/生效 |

   **提示**：有些路由器可能只需要填写端口和IP，其他自动配置

5. **保存配置**
   - 点击"应用"、"保存"或"添加"
   - 重启路由器使配置生效（部分路由器需要）

---

### 第3步：测试公网访问

#### A. 运行配置检查脚本

```bash
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion
./setup-public-access.sh
```

脚本会自动检查：
- SSH服务状态
- 网络连接
- 防火墙配置
- 端口占用
- 公网SSH可达性

#### B. 手动测试公网SSH

**测试1：从本机测试SSH**
```bash
# 测试本地SSH
ssh localhost

# 应该提示登录，输入Mac密码后进入
# 输入 `exit` 退出
```

**测试2：从内网其他设备测试**
```bash
# 在同一WiFi的手机或另一台电脑上
ssh liulinlang@192.168.0.137
```

**测试3：从外网测试（手机4G/5G网络）**
```bash
# 断开WiFi，使用手机流量
# 或从朋友家、公司网络测试

ssh liulinlang@125.118.5.207
```

#### C. 建立公网SSH隧道

```bash
# 进入项目目录
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion

# 方法1：使用自动化脚本（推荐）
./ssh-tunnel.sh public frontend
# 或
./ssh-tunnel.sh public both

# 方法2：手动建立隧道
ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
```

#### D. 访问应用

建立隧道后，在浏览器打开：
```
http://localhost:3000
```

---

## 📱 从手机/其他设备访问

### iPhone/iPad

1. **下载SSH客户端App**
   - App Store搜索"Termius"（推荐）
   - 或"Blink Shell"、"Prompt"

2. **配置SSH连接**
   - Host: 125.118.5.207
   - Port: 22
   - Username: liulinlang
   - Password: [您的Mac密码]

3. **配置端口转发**
   - 在Termius中：Hosts → 选择您的Host → Local Port Forwarding
   - Local Port: 3000
   - Host: localhost
   - Port: 3000

4. **连接并访问**
   - 点击连接
   - 打开Safari浏览器
   - 访问：http://localhost:3000

### Android手机

1. **下载SSH客户端App**
   - Google Play搜索"Termius"（推荐）
   - 或"JuiceSSH"、"ConnectBot"

2. **配置与iOS相同**

3. **Chrome浏览器访问**
   - http://localhost:3000

### Windows电脑

1. **使用PowerShell或CMD**
   ```powershell
   ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
   ```

2. **使用PuTTY（推荐）**
   - 下载：https://www.putty.org/
   - Host: 125.118.5.207
   - Port: 22
   - Connection → SSH → Tunnels
   - Source port: 3000
   - Destination: localhost:3000
   - Click "Add"
   - Click "Open" to connect

3. **浏览器访问**
   - http://localhost:3000

---

## 🔒 安全建议（强烈推荐）

### 1. 使用SSH密钥代替密码

```bash
# 生成SSH密钥对
ssh-keygen -t ed25519

# 添加到authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys

# 设置权限
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### 2. 修改SSH默认端口

```bash
# 编辑SSH配置
sudo nano /etc/ssh/sshd_config

# 修改端口
Port 2222

# 重启SSH
sudo launchctl stop com.openssh.sshd
sudo launchctl start com.openssh.sshd
```

同时修改路由器端口转发：
- 外部端口：2222
- 内部端口：2222

连接时指定端口：
```bash
ssh -p 2222 liulinlang@125.118.5.207
```

### 3. 限制访问IP

```bash
# 编辑hosts.allow
sudo nano /etc/hosts.allow

# 添加允许的IP段
sshd: 192.168.0.0/24
sshd: 10.0.0.0/8

# 编辑hosts.deny
sudo nano /etc/hosts.deny

# 拒绝其他所有IP
sshd: ALL
```

---

## ❓ 常见问题

### Q1: 找不到路由器的端口转发设置？

**不同品牌路由器的位置可能不同：**

**TP-Link**:
- 转发规则 → 虚拟服务器

**华为/中兴**:
- 高级设置 → NAT → 端口映射

**小米**:
- 高级设置 → 端口转发

**华硕(ASUS)**:
- 外部网络(WAN) → 端口转发

**网件(Netgear)**:
- 高级 → 高级设置 → 端口转发/端口触发

**如果实在找不到**：
1. 查看路由器说明书
2. 访问路由器品牌官网支持页面
3. 搜索"路由器型号 + 端口转发"

### Q2: 配置后仍然无法从公网访问？

**检查清单：**

1. **确认SSH已开启**
   ```bash
   sudo systemsetup -getremotelogin
   # 应该显示: Remote Login: On
   ```

2. **检查端口转发是否保存**
   - 重新登录路由器确认配置存在

3. **重启路由器**
   - 有些路由器需要重启才生效

4. **检查防火墙**
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --list
   ```

5. **使用其他网络测试**
   - 不要用同一WiFi测试
   - 使用手机4G/5G网络
   - 或从朋友家测试

### Q3: 公网IP会变化吗？

**家庭宽带通常使用动态IP，可能会变化。**

解决方案：
1. **使用DDNS（动态域名）**
   - No-IP: https://www.noip.com/ （免费）
   - DuckDNS: https://www.duckdns.org/ （免费）
   - DNSPod: https://www.dnspod.cn/

2. **配置自动更新**
   ```bash
   # 安装ddclient
   brew install ddclient

   # 配置ddclient
   # 按服务商提供的说明配置
   ```

3. **定期检查IP**
   ```bash
   curl ifconfig.me
   ```

### Q4: 安全吗？

**SSH隧道本身是安全的（加密传输），但建议：**

✅ **推荐做法**：
- 使用SSH密钥认证
- 修改默认SSH端口
- 限制访问IP
- 定期检查登录日志
- 及时更新系统

❌ **避免**：
- 使用弱密码
- 长期开放22端口
- 从不受信任的网络访问
- 在公共电脑上保存密码

---

## 📞 获取帮助

如果遇到问题：

1. **查看详细配置指南**
   ```bash
   cat PUBLIC_ACCESS_SETUP.md
   ```

2. **运行诊断脚本**
   ```bash
   ./setup-public-access.sh
   ```

3. **查看SSH日志**
   ```bash
   log show --predicate 'process == "sshd"' --last 1h
   ```

4. **检查网络状态**
   ```bash
   # 查看网络连接
   netstat -an | grep :22

   # 查看路由
   netstat -nr
   ```

---

## ✅ 配置完成后的访问地址

### 本机访问
```
前端: http://localhost:3000
后端: http://localhost:8000
```

### 内网访问（同一WiFi）
```
前端: http://192.168.0.137:3000
后端: http://192.168.0.137:8000
SSH:  ssh liulinlang@192.168.0.137
```

### 公网访问（互联网任何地方）
```
通过SSH隧道:
1. ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
2. 浏览器访问: http://localhost:3000

或使用脚本:
./ssh-tunnel.sh public frontend
```

---

## 🎉 快速开始

```bash
# 1. 开启SSH（图形界面或命令行）
sudo systemsetup -setremotelogin on

# 2. 配置路由器端口转发
# 访问 http://192.168.0.1
# 添加规则: 外部端口22 → 内部IP 192.168.0.137:22

# 3. 运行检查脚本
./setup-public-access.sh

# 4. 测试公网SSH
ssh liulinlang@125.118.5.207

# 5. 建立隧道
./ssh-tunnel.sh public frontend

# 6. 浏览器访问
# http://localhost:3000
```

完成！🎊
