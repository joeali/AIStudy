# AI Study Companion - 阿里云部署完整指南

> 本指南将帮助你将 AI Study Companion 部署到阿里云 ECS 服务器，实现通过公网链接访问。

## 📋 部署概览

```
前端 (React + Vite)
    ↓
Nginx (反向代理)
    ↓
后端 (Python FastAPI) :8000
    ↓
智谱 AI API
```

## 🎯 部署架构

- **前端**：Nginx 托管静态文件
- **后端**：FastAPI 服务运行在 8000 端口
- **反向代理**：Nginx 将 API 请求转发到后端
- **域名**：可选，建议配置便于访问

---

## 第一步：购买阿里云 ECS 服务器

### 1.1 访问阿里云控制台
- 登录 https://ecs.console.aliyun.com/
- 如果没有账号，先注册并实名认证

### 1.2 创建实例
点击「创建实例」，配置如下：

**基础配置**：
- **付费模式**：按量付费（测试）或 包年包月（生产）
- **地域**：选择离你最近的地区（如 华东1-杭州）
- **实例规格**：2核 vCPU + 4GB 内存（ecs.t6-c1m2.large 或类似）
  - 新用户通常有优惠套餐，约 50-100 元/年

**镜像选择**：
- **操作系统**：Ubuntu 22.04 或 24.04 LTS（推荐）或 CentOS 7/8
- **系统盘**：40GB SSD 超云盘

**网络配置**：
- **网络类型**：专有网络（VPC）
- **带宽计费**：按固定带宽（1Mbps 起步）或 按使用流量
- **公网 IP**：分配公网 IP

**安全组**：
- 创建新的安全组
- 后续会配置端口开放

**系统配置**：
- **实例名称**：ai-study-server（可自定义）
- **认证**：设置 root 密码或使用 SSH 密钥对

**确认订单**：
- 检查配置
- 同意服务条款
- 立即购买

### 1.3 等待实例创建
- 创建时间约 1-3 分钟
- 完成后在「实例列表」可以看到你的服务器

---

## 第二步：配置安全组

### 2.1 开放必要端口
在 ECS 控制台 → 实例详情 → 安全组 → 配置规则 → 入方向：

点击「手动添加」，添加以下规则：

| 协议类型 | 端口范围 | 授权对象 | 描述 |
|---------|---------|---------|------|
| TCP     | 22/22   | 0.0.0.0/0 | SSH 远程连接 |
| TCP     | 80/80   | 0.0.0.0/0 | HTTP 访问 |
| TCP     | 443/443 | 0.0.0.0/0 | HTTPS 访问 |
| TCP     | 8000/8000 | 0.0.0.0/0 | 后端 API（可选，调试用） |

⚠️ **安全提示**：生产环境建议将 0.0.0.0/0 改为你的 IP 地址

---

## 第三步：连接服务器

### 3.1 获取服务器信息
在 ECS 实例列表中，记录：
- **公网 IP 地址**：如 `47.97.xxx.xxx`
- **用户名**：通常是 `root`

### 3.2 使用 SSH 连接（Mac/Linux）
```bash
ssh root@你的公网IP
# 示例：ssh root@47.97.xxx.xxx
```

输入密码（创建实例时设置的密码），登录成功。

### 3.3 Windows 用户
- 使用 PowerShell 或 CMD
- 或者使用 SSH 客户端工具（如 PuTTY、MobaXterm）

---

## 第四步：安装服务器环境

登录服务器后，依次执行以下命令：

### 4.1 更新系统软件包
```bash
apt update && apt upgrade -y
```

### 4.2 安装必要工具
```bash
apt install -y curl wget git vim nginx python3-venv python3-pip
```

### 4.3 安装 Node.js（用于构建前端）
```bash
# 使用 NodeSource 仓库安装 Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 验证安装
node -v  # 应显示 v18.x.x
npm -v
```

### 4.4 验证 Python 版本
```bash
python3 --version  # 应显示 3.10+
pip3 --version
```

---

## 第五步：上传项目代码

### 5.1 方法一：使用 Git（推荐）
```bash
# 将你的项目推送到 GitHub/Gitee
# 然后在服务器上克隆

cd /var/www
git clone https://github.com/你的用户名/ai-study-companion.git
```

### 5.2 方法二：使用 SCP 从本地上传
在你的本地电脑执行：
```bash
# 压缩项目（排除 node_modules 和 venv）
cd ai-study-companion
tar -czf ai-study.tar.gz --exclude='node_modules' --exclude='venv' --exclude='.git' .

# 上传到服务器
scp ai-study.tar.gz root@你的公网IP:/tmp/

# 在服务器上解压（SSH 登录后）
mkdir -p /var/www/ai-study-companion
cd /var/www
tar -xzf /tmp/ai-study.tar.gz -C ai-study-companion
```

---

## 第六步：部署后端服务

### 6.1 创建 Python 虚拟环境
```bash
cd /var/www/ai-study-companion/backend
python3 -m venv venv
source venv/bin/activate
```

### 6.2 安装依赖
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6.3 配置环境变量
```bash
# 编辑 .env 文件
vim .env

# 确保包含以下内容（使用你的真实 API Key）
GLM_API_KEY=your_actual_api_key_here
```

### 6.4 测试后端运行
```bash
# 安装 uvicorn
pip install uvicorn[standard]

# 测试启动（查看是否有错误）
uvicorn main:app --host 0.0.0.0 --port 8000
```

如果看到 `Uvicorn running on http://0.0.0.0:8000`，说明后端正常。
按 `Ctrl+C` 停止测试。

### 6.5 创建 systemd 服务（后台运行）
```bash
vim /etc/systemd/system/ai-study-backend.service
```

粘贴以下内容：
```ini
[Unit]
Description=AI Study Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/ai-study-companion/backend
Environment="PATH=/var/www/ai-study-companion/backend/venv/bin"
ExecStart=/var/www/ai-study-companion/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
systemctl daemon-reload
systemctl enable ai-study-backend
systemctl start ai-study-backend
systemctl status ai-study-backend
```

查看状态应显示 `active (running)`。

---

## 第七步：部署前端应用

### 7.1 构建前端
```bash
cd /var/www/ai-study-companion/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，会在 `dist` 目录生成静态文件。

### 7.2 配置 Nginx

创建 Nginx 配置文件：
```bash
vim /etc/nginx/sites-available/ai-study
```

粘贴以下配置：
```nginx
server {
    listen 80;
    server_name 你的公网IP或域名;

    # 前端静态文件
    location / {
        root /var/www/ai-study-companion/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 启用 gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
}
```

启用配置：
```bash
# 创建符号链接
ln -s /etc/nginx/sites-available/ai-study /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
systemctl enable nginx
```

---

## 第八步：测试访问

### 8.1 测试后端 API
在浏览器访问：
```
http://你的公网IP/api/docs
```
应该能看到 FastAPI 的 Swagger 文档页面。

### 8.2 测试前端
在浏览器访问：
```
http://你的公网IP
```
应该能看到 AI Study Companion 的界面。

### 8.3 功能测试
1. 上传一张包含题目的图片
2. 测试题目识别功能
3. 测试 AI 解答功能

---

## 第九步：配置 SSL 证书（HTTPS）- 可选

### 9.1 安装 Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 9.2 申请证书
**如果你有域名**（如 example.com）：
```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**如果只用 IP 地址**：
免费证书不直接支持 IP，建议：
1. 购买便宜域名（如 .top、.xyz 约几元/年）
2. 在阿里云域名控制台解析域名到你的服务器 IP
3. 然后再申请证书

Certbot 会自动配置 Nginx，强制 HTTPS 跳转。

### 9.3 自动续期
Certbot 会自动创建定时任务续期证书。手动测试：
```bash
certbot renew --dry-run
```

---

## 第十步：配置域名（可选但推荐）

### 10.1 购买域名
- 在阿里云域名注册购买（如 `ai-study.top`）

### 10.2 配置 DNS 解析
1. 进入「云解析 DNS」控制台
2. 添加记录：
   - **记录类型**：A
   - **主机记录**：@（根域名）或 www
   - **记录值**：你的 ECS 公网 IP
   - **TTL**：10 分钟

### 10.3 更新 Nginx 配置
```bash
vim /etc/nginx/sites-available/ai-study
```

将 `server_name` 改为：
```nginx
server_name ai-study.top www.ai-study.top;
```

重启 Nginx：
```bash
nginx -t && systemctl restart nginx
```

---

## 🎉 完成！

现在你可以通过以下方式访问：
- **HTTP**：`http://你的公网IP` 或 `http://你的域名`
- **HTTPS**：`https://你的域名`（配置了 SSL 后）

---

## 📊 监控和维护

### 查看后端日志
```bash
journalctl -u ai-study-backend -f
```

### 查看后端状态
```bash
systemctl status ai-study-backend
```

### 重启后端服务
```bash
systemctl restart ai-study-backend
```

### 查看 Nginx 日志
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 更新代码
```bash
cd /var/www/ai-study-companion
git pull

# 后端更新
cd backend
source venv/bin/activate
pip install -r requirements.txt
systemctl restart ai-study-backend

# 前端更新
cd ../frontend
npm install
npm run build
systemctl restart nginx
```

---

## 🔧 常见问题

### 1. 无法访问网站
- 检查安全组是否开放 80 端口
- 检查 Nginx 是否运行：`systemctl status nginx`
- 检查防火墙：`ufw status`（如果是 Ubuntu）

### 2. 后端 API 不工作
- 检查后端服务：`systemctl status ai-study-backend`
- 查看日志：`journalctl -u ai-study-backend -n 50`
- 确认 8000 端口监听：`netstat -tuln | grep 8000`

### 3. API 密钥错误
- 检查 `.env` 文件是否正确配置
- 确认 API 密钥有效且余额充足

### 4. 前端页面空白
- 检查 `npm run build` 是否成功
- 确认 `dist` 目录存在且包含 `index.html`
- 检查 Nginx 配置中的 root 路径是否正确

### 5. 端口冲突
```bash
# 查看端口占用
netstat -tuln | grep 8000
lsof -i :8000
```

---

## 💰 成本估算

| 项目 | 月费用（按量） | 年费用（包年） |
|-----|--------------|--------------|
| ECS 服务器（2核4GB） | 约 50-100 元 | 约 200-400 元 |
| 域名（可选） | - | 约 10-50 元 |
| 流量费 | 较低 | 包含在套餐内 |

**总成本**：新用户通常有优惠，首年约 100-300 元即可。

---

## 🔐 安全建议

1. **修改 SSH 端口**：将默认 22 改为其他端口
2. **配置防火墙**：只开放必要端口
3. **定期备份**：使用阿里云快照功能
4. **监控资源**：设置 CPU/内存告警
5. **API 密钥安全**：不要将 `.env` 提交到 Git

---

## 📞 需要帮助？

如遇到问题，检查：
1. [项目文档](README.md)
2. 后端日志：`journalctl -u ai-study-backend -n 100`
3. Nginx 日志：`/var/log/nginx/error.log`

祝你部署顺利！🚀
