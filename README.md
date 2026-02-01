# AI Study Companion

AI 伴学助手 - 智能学习辅助系统

## 项目介绍

这是一个前后端分离的 AI 学习助手应用，整合了两个项目的优势：

- **工程 1**：React 前端界面，包含 AI 解题、错题本、学习分析、练习生成等功能
- **工程 2**：Python 后端 OCR 服务，使用 GLM-4V 进行智能试卷识别

## 功能特性

### 1. AI 引导解题
- 上传题目图片或输入问题
- AI 老师通过启发式提问引导独立思考
- 支持多轮对话，逐步深入

### 2. 智能错题本
- 自动识别上传的错题图片
- 提取题目信息、正确答案、错误原因
- 记录复习历史

### 3. 学习分析报告
- 周学习数据统计
- 分学科正确率分析
- 薄弱知识点诊断
- 个性化提分方案

### 4. 个性化练习生成
- 根据薄弱点生成针对性练习题
- 可选择学科、难度、数量
- 智能推荐练习重点

## 技术栈

### 前端
- React 18
- Vite
- Tailwind CSS
- Lucide Icons

### 后端
- Python 3.8+
- FastAPI
- GLM-4V (智谱 AI)

## 快速开始

### 方式一：使用启动脚本（推荐）

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 方式二：手动启动

#### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端将在 `http://localhost:8000` 启动

API 文档: `http://localhost:8000/docs`

#### 2. 启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 项目结构

```
ai-study-companion/
├── backend/                # 后端服务
│   ├── main.py            # FastAPI 主程序
│   └── requirements.txt   # Python 依赖
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── App.jsx        # 主应用组件
│   │   ├── main.jsx       # 入口文件
│   │   └── index.css      # 样式文件
│   ├── index.html         # HTML 模板
│   ├── package.json       # npm 依赖
│   └── vite.config.js     # Vite 配置
├── start.sh               # Linux/macOS 启动脚本
├── start.bat              # Windows 启动脚本
└── README.md              # 项目说明
```

## API 接口

### POST `/api/ocr/exam`
试卷 OCR 识别

### POST `/api/analyze/question`
题目分析

### POST `/api/chat`
AI 对话

## 配置说明

### 后端配置

在 `backend/main.py` 中修改 API Key:

```python
GLM_API_KEY = "your_api_key_here"
```

### 前端配置

在 `frontend/.env` 中修改后端地址:

```
VITE_API_URL=http://localhost:8000
```

## 依赖安装

### Python 依赖
```bash
pip install fastapi uvicorn pillow numpy requests python-multipart pydantic
```

### Node.js 依赖
```bash
npm install react react-dom lucide-react
```

## 注意事项

1. 需要先获取智谱 AI 的 API Key
2. 确保 Python 3.8+ 和 Node.js 16+ 已安装
3. 后端默认端口 8000，前端默认端口 3000
4. 如遇端口冲突，请修改相应配置

## 许可证

MIT License
