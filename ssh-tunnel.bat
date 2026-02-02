@echo off
REM ========================================
REM SSH隧道快速启动脚本 (Windows)
REM ========================================

set REMOTE_USER=liulinlang
set REMOTE_IP=192.168.0.137
set REMOTE_IP_PUBLIC=125.118.5.207

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="frontend" goto frontend
if "%1"=="fe" goto frontend
if "%1"=="backend" goto backend
if "%1"=="be" goto backend
if "%1"=="both" goto both
if "%1"=="all" goto both
if "%1"=="public" goto public
if "%1"=="status" goto status
if "%1"=="stop" goto stop
goto unknown

:help
echo =========================================
echo   SSH隧道快速启动脚本 (Windows)
echo =========================================
echo.
echo 用法: ssh-tunnel.bat [选项]
echo.
echo 选项:
echo   frontend, fe   - 转发前端端口(3000)
echo   backend, be    - 转发后端端口(8000)
echo   both, all      - 同时转发前端和后端
echo   public         - 通过公网IP访问
echo   status         - 查看隧道状态
echo   stop           - 停止所有隧道
echo   help           - 显示此帮助信息
echo.
echo 示例:
echo   ssh-tunnel.bat frontend    # 转发前端
echo   ssh-tunnel.bat both        # 转发前后端
echo   ssh-tunnel.bat public both # 公网访问前后端
echo.
goto end

:frontend
echo =========================================
echo 建立前端SSH隧道 (端口 3000)
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP%...
echo.

ssh -f -N -L 3000:localhost:3000 %REMOTE_USER%@%REMOTE_IP%

echo.
echo ✓ 隧道已建立！
echo.
echo 访问地址: http://localhost:3000
echo.
echo 使用 'ssh-tunnel.bat status' 查看状态
echo 使用 'ssh-tunnel.bat stop' 停止隧道
goto end

:backend
echo =========================================
echo 建立后端SSH隧道 (端口 8000)
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP%...
echo.

ssh -f -N -L 8000:localhost:8000 %REMOTE_USER%@%REMOTE_IP%

echo.
echo ✓ 隧道已建立！
echo.
echo 访问地址: http://localhost:8000
echo.
echo 使用 'ssh-tunnel.bat status' 查看状态
echo 使用 'ssh-tunnel.bat stop' 停止隧道
goto end

:both
echo =========================================
echo 建立前后端SSH隧道
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP%...
echo.

ssh -f -N -L 3000:localhost:3000 %REMOTE_USER%@%REMOTE_IP%
ssh -f -N -L 8000:localhost:8000 %REMOTE_USER%@%REMOTE_IP%

echo.
echo ✓ 隧道已建立！
echo.
echo 前端: http://localhost:3000
echo 后端: http://localhost:8000
echo.
echo 使用 'ssh-tunnel.bat status' 查看状态
echo 使用 'ssh-tunnel.bat stop' 停止隧道
goto end

:public
if "%2"=="frontend" goto public_frontend
if "%2"=="fe" goto public_frontend
if "%2"=="backend" goto public_backend
if "%2"=="be" goto public_backend
if "%2"=="both" goto public_both
if "%2"=="all" goto public_both
if "%2"=="" goto public_both
goto unknown

:public_frontend
echo =========================================
echo 通过公网IP建立前端隧道
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP_PUBLIC%...
echo.

ssh -f -N -L 3000:localhost:3000 %REMOTE_USER%@%REMOTE_IP_PUBLIC%

echo.
echo ✓ 隧道已建立！
echo.
echo 访问地址: http://localhost:3000
goto end

:public_backend
echo =========================================
echo 通过公网IP建立后端隧道
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP_PUBLIC%...
echo.

ssh -f -N -L 8000:localhost:8000 %REMOTE_USER%@%REMOTE_IP_PUBLIC%

echo.
echo ✓ 隧道已建立！
echo.
echo 访问地址: http://localhost:8000
goto end

:public_both
echo =========================================
echo 通过公网IP建立前后端隧道
echo =========================================
echo.
echo 正在连接 %REMOTE_USER%@%REMOTE_IP_PUBLIC%...
echo.

ssh -f -N -L 3000:localhost:3000 %REMOTE_USER%@%REMOTE_IP_PUBLIC%
ssh -f -N -L 8000:localhost:8000 %REMOTE_USER%@%REMOTE_IP_PUBLIC%

echo.
echo ✓ 隧道已建立！
echo.
echo 前端: http://localhost:3000
echo 后端: http://localhost:8000
goto end

:status
echo =========================================
echo   SSH隧道状态
echo =========================================
echo.

netstat -ano | findstr ":3000.*LISTENING" >nul
if %errorlevel%==0 (
    echo 前端隧道(3000): 运行中
) else (
    echo 前端隧道(3000): 未运行
)

netstat -ano | findstr ":8000.*LISTENING" >nul
if %errorlevel%==0 (
    echo 后端隧道(8000): 运行中
) else (
    echo 后端隧道(8000): 未运行
)
echo.
goto end

:stop
echo =========================================
echo 停止所有SSH隧道
echo =========================================
echo.

taskkill /F /IM ssh.exe 2>nul

if %errorlevel%==0 (
    echo ✓ 已停止SSH隧道
) else (
    echo 没有运行的SSH隧道
)
goto end

:unknown
echo 错误: 未知选项 '%1'
echo.
echo 使用 'ssh-tunnel.bat help' 查看帮助
goto end

:end
