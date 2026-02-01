@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title AI Study Companion

echo ==================================
echo    AI Study Companion 启动中...
echo ==================================
echo.

REM 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)
echo ✓ Python 已安装

REM 检查 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)
echo ✓ Node.js 已安装
echo.

REM ============ 后端设置 ============
echo [1/4] 配置后端服务...
cd backend

REM 创建虚拟环境
if not exist venv (
    echo   创建 Python 虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo   激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查依赖
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo   安装 Python 依赖（首次运行可能需要几分钟）...
    pip install -q -r requirements.txt
) else (
    echo   ✓ Python 依赖已安装
)

REM ============ 前端设置 ============
echo.
echo [2/4] 配置前端服务...
cd ..\frontend

REM 检查依赖
if not exist node_modules (
    echo   安装 npm 依赖（首次运行可能需要几分钟）...
    call npm install --silent --no-audit --no-fund
) else (
    echo   ✓ npm 依赖已安装
)

REM ============ 停止已运行的服务 ============
echo.
echo [3/4] 检查并停止已运行的服务...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do (
    echo   停止旧的后端服务 (PID: %%a)
    taskkill /F /PID %%a >nul 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000.*LISTENING"') do (
    echo   停止旧的前端服务 (PID: %%a)
    taskkill /F /PID %%a >nul 2>nul
)

REM ============ 启动服务 ============
echo.
echo [4/4] 启动服务...
echo.

REM 启动后端
cd ..\backend
echo ▶ 启动后端服务...
start "AI Study Companion - Backend" cmd /k "venv\Scripts\activate.bat && python main.py"
echo   后端服务已启动

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
cd ..\frontend
echo ▶ 启动前端服务...
start "AI Study Companion - Frontend" cmd /k "npm run dev"
echo   前端服务已启动

REM ============ 完成 ============
echo.
echo ==================================
echo    🎉 启动完成！
echo ==================================
echo.
echo 服务地址：
echo   • 前端界面: http://localhost:3000
echo   • 后端 API: http://localhost:8000
echo   • API 文档: http://localhost:8000/docs
echo.
echo 注意：
echo   • 关闭此窗口不会停止服务
echo   • 请分别关闭后端和前端窗口来停止服务
echo ==================================
echo.

pause
