# AI Study Companion - 微信分享部署指南

## 🚀 快速部署方案（推荐）

### 方案1: 使用 Vercel + 内网穿透（最简单，5分钟完成）

#### 优点
- ✅ 完全免费
- ✅ 自动HTTPS
- ✅ 全球CDN加速
- ✅ 微信可直接访问

#### 步骤

**1. 部署前端到 Vercel**

```bash
# 进入前端目录
cd frontend

# 安装 Vercel CLI
npm install -g vercel

# 登录 Vercel（首次使用）
vercel login

# 部署
vercel

# 按提示操作：
# - Set up and deploy: N
# - Which scope: 选择你的账号
# - Link to existing project: N
# - Project name: ai-study-companion
# - Directory: ./ (当前目录)
# - Override settings: N

# 部署完成后，Vercel 会提供一个访问地址，如：
# https://ai-study-companion.vercel.app
```

**2. 配置后端 API 地址**

创建 `frontend/.env.production`：
```env
VITE_API_URL=https://your-backend-api.com
```

重新部署：
```bash
vercel --prod
```

**3. 后端 API 部署**

选择以下任一方案：

**A. 使用 Railway（免费，推荐）**

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 创建项目
railway init

# 部署后端
railway up

# 设置环境变量
railway variables set GLM_API_KEY "your_api_key_here"

# 获取分配的地址，如：
# https://ai-study-backend.railway.app
```

**B. 使用 Render（免费）**

访问：https://render.com/
- 创建新的 Web Service
- 连接 GitHub 仓库
- 配置构建命令和启动命令
- 设置环境变量 `GLM_API_KEY`

**C. 使用内网穿透（本地开发）**

```bash
# 安装 ngrok
brew install ngrok  # macOS
# 或访问 https://ngrok.com/ 下载

# 启动后端
cd backend
source venv/bin/activate
python main.py

# 在另一个终端启动 ngrok
ngrok http 8000

# ngrok 会提供一个公网地址，如：
# https://abc123.ngrok.io
```

**4. 最终配置**

将 `frontend/.env.production` 中的 API 地址改为实际的后端地址：
```env
VITE_API_URL=https://your-backend.railway.app
```

重新部署前端：
```bash
vercel --prod
```

**5. 生成微信分享链接**

最终地址：
```
https://ai-study-companion.vercel.app
```

这个地址：
- ✅ 支持HTTPS
- ✅ 微信可以直接访问
- ✅ 全球CDN加速
- ✅ 完全免费

---

### 方案2: 使用 Cloudflare Pages（完全免费）

#### 步骤

**1. 准备 GitHub 仓库**

```bash
# 初始化 Git 仓库（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 推送到 GitHub
# 先在 GitHub 创建新仓库，然后：
git remote add origin https://github.com/你的用户名/ai-study-companion.git
git branch -M main
git push -u origin main
```

**2. 部署到 Cloudflare Pages**

- 访问：https://pages.cloudflare.com/
- 连接 GitHub 账号
- 选择仓库：ai-study-companion
- 构建设置：
  - 构建命令：`npm run build`（在 frontend 目录）
  - 构建输出目录：`frontend/dist`
  - 根目录：`/frontend`
- 环境变量：`VITE_API_URL=https://your-backend-api.com`

**3. 获取访问地址**

部署成功后，Cloudflare 会提供：
```
https://ai-study-companion.pages.dev
```

---

### 方案3: 使用自己的服务器（如果您有）

#### 步骤

**1. 准备服务器**
- 购买云服务器（阿里云、腾讯云等）
- 安装 Nginx + Python 环境

**2. 配置 Nginx**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**3. 配置 HTTPS（使用 Let's Encrypt）**

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com
```

---

## 📱 微信分享配置

### 生成分享链接

部署成功后，您的访问地址格式：

```
https://your-project.vercel.app
```

### 微信分享设置（可选）

如果需要在微信中自定义分享标题和描述，在前端添加：

```javascript
// 在 frontend/src/main.jsx 中添加
document.addEventListener('DOMContentLoaded', () => {
  // 设置分享标题
  document.title = 'AI Study Companion - 智能学习助手';

  // 设置分享描述（meta标签）
  const metaDescription = document.createElement('meta');
  metaDescription.name = 'description';
  metaDescription.content = 'AI驱动的学习助手，提供智能错题分析、苏格拉底式引导等功能';
  document.head.appendChild(metaDescription);
});
```

---

## 🎯 推荐方案对比

| 方案 | 难度 | 成本 | 速度 | 推荐度 |
|-----|------|------|------|--------|
| **Vercel + Railway** | ⭐ 简单 | 免费 | 快 | ⭐⭐⭐⭐⭐ |
| **Cloudflare Pages** | ⭐ 简单 | 免费 | 快 | ⭐⭐⭐⭐⭐ |
| **自己的服务器** | ⭐⭐⭐ 复杂 | 付费 | 中 | ⭐⭐⭐ |

---

## ⚡ 最快方案（10分钟）

### 如果您想要最快的方案：

**1. 部署前端（5分钟）**
```bash
cd frontend
npm install -g vercel
vercel login
vercel
# 完成后获得地址：https://ai-study-companion.vercel.app
```

**2. 使用 ngrok 暴露后端（3分钟）**
```bash
# 新终端
cd backend
source venv/bin/activate
python main.py

# 另一个终端
ngrok http 8000
# 获得地址：https://xxx.ngrok.io
```

**3. 配置前端 API（2分钟）**
```bash
# 创建 frontend/.env.production
echo "VITE_API_URL=https://xxx.ngrok.io" > frontend/.env.production

# 重新部署
vercel --prod
```

**完成！** 您的微信分享链接：
```
https://ai-study-companion.vercel.app
```

---

## 📋 部署检查清单

部署前确认：
- [ ] 已配置 API Key（`backend/.env`）
- [ ] 后端可以正常运行
- [ ] 前端构建成功（`npm run build`）
- [ ] 已有 GitHub 账号（如果使用 Cloudflare Pages）

部署后验证：
- [ ] 前端可以正常访问
- [ ] API 请求可以正常工作
- [ ] 图片上传功能正常
- [ ] 微信中可以打开链接
- [ ] 所有功能正常使用

---

## 🔗 快速部署脚本

创建 `deploy.sh`：
```bash
#!/bin/bash
echo "=== AI Study Companion 快速部署 ==="

# 检查环境
echo "1. 检查环境..."
command -v node >/dev/null 2>&1 || { echo "❌ 需要先安装 Node.js"; exit 1; }
command -v vercel >/dev/null 2>&1 || { echo "📦 正在安装 Vercel CLI..."; npm install -g vercel; }

# 构建前端
echo "2. 构建前端..."
cd frontend
npm install
npm run build

# 部署
echo "3. 部署到 Vercel..."
vercel

echo "✅ 部署完成！"
echo "📱 您的微信分享链接："
echo "   https://ai-study-companion.vercel.app (或类似的地址)"
```

使用：
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 💡 提示

1. **首次部署推荐使用 Vercel**，最简单且完全免费
2. **后端 API 可以先用 ngrok** 测试，后续再迁移到 Railway
3. **域名配置**：Vercel 支持绑定自定义域名（需要验证DNS）
4. **HTTPS 自动配置**：Vercel 和 Cloudflare 都会自动配置 HTTPS

---

## 📞 需要帮助？

如果部署过程中遇到问题：
1. 检查防火墙设置
2. 查看部署日志
3. 确认 API 地址配置正确
4. 验证环境变量是否设置

**预计部署时间**：10-20分钟 ⏱️

**预计成本**：完全免费 💰
