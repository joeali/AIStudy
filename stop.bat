@echo off
chcp 65001 >nul
title 停止 AI Study Companion

echo ==================================
echo    停止 AI Study Companion
echo ==================================
echo.

REM 停止后端
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do (
    echo ▶ 停止后端服务 ^(PID: %%a^)...
    taskkill /F /PID %%a >nul 2>nul
    echo   ✓ 后端服务已停止
)

REM 停止前端
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000.*LISTENING"') do (
    echo ▶ 停止前端服务 ^(PID: %%a^)...
    taskkill /F /PID %%a >nul 2>nul
    echo   ✓ 前端服务已停止
)

echo.
echo ==================================
echo    ✅ 所有服务已停止
echo ==================================
echo.

pause
