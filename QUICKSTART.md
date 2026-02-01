# AI Study Companion - 快速启动指南

## 🎯 一键启动

### macOS / Linux

```bash
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion
./start.sh
```

### Windows

```cmd
cd C:\Users\liulinlang\Documents\liulinlang\ai-study-companion
start.bat
```

## 📍 访问地址

启动成功后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端界面** | http://localhost:3000 | 主要使用界面 |
| **后端 API** | http://localhost:8000 | API 服务 |
| **API 文档** | http://localhost:8000/docs | Swagger 文档 |

## ✅ 部署验证

所有测试已通过：

```
✓ 健康检查测试 - 通过
✓ 根路径测试 - 通过
✓ OCR 识别测试 - 通过
✓ 对话 API 测试 - 通过
```

## 🛠️ 手动启动（如遇问题）

### 启动后端

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

### 启动前端

```bash
cd frontend
npm run dev
```

## 🔧 故障排除

### 端口被占用

```bash
# 查找占用 8000 端口的进程
lsof -ti:8000 | xargs kill -9

# 查找占用 3000 端口的进程
lsof -ti:3000 | xargs kill -9
```

### Windows 端口被占用

```cmd
netstat -aon | findstr ":8000"
taskkill /F /PID <进程ID>
```

### 重新安装依赖

```bash
# 后端
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
rm -rf node_modules
npm install
```

## 📦 项目结构

```
ai-study-companion/
├── backend/           # Python 后端
│   ├── main.py       # FastAPI 主程序
│   ├── venv/         # Python 虚拟环境
│   └── requirements.txt
├── frontend/         # React 前端
│   ├── src/
│   │   ├── App.jsx   # 主组件
│   │   └── ...
│   ├── node_modules/
│   └── package.json
├── start.sh          # macOS/Linux 启动脚本
├── start.bat         # Windows 启动脚本
├── test_api.py       # API 测试脚本
├── backend.log       # 后端日志
└── frontend.log      # 前端日志
```

## 🎨 功能说明

### 1. AI 解题
- 上传题目图片或输入文字
- AI 老师启发式引导解题

### 2. 智能错题本
- 上传错题图片自动识别
- 记录复习历史

### 3. 学习分析
- 周学习数据统计
- 分学科提分方案

### 4. 练习生成
- 根据薄弱点生成练习题
- 可选择学科、难度、数量

## 📝 注意事项

1. **API Key**: 需要配置智谱 AI 的 API Key（已在代码中配置）
2. **网络**: 需要能访问智谱 AI API (https://open.bigmodel.cn)
3. **端口**: 确保 8000 和 3000 端口未被占用

## 🎉 开始使用

打开浏览器访问: **http://localhost:3000**

祝学习愉快！
