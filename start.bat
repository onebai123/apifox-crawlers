@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    Apifox API文档抓取工具 - 本地启动
echo ========================================
echo.

:: 检查Python是否安装
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [成功] Python版本: %PYTHON_VERSION%
echo.

:: 检查pip是否安装
echo [2/5] 检查pip环境...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到pip，请重新安装Python
    pause
    exit /b 1
)
echo [成功] pip已安装
echo.

:: 升级pip并安装依赖
echo [3/5] 安装Python依赖包...
echo 使用清华大学镜像源加速下载...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，尝试使用默认源...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)
echo [成功] 依赖安装完成
echo.

:: 创建必要目录
echo [4/5] 创建数据目录...
if not exist "data" mkdir data
if not exist "data\01" mkdir data\01
if not exist "data\01\md" mkdir data\01\md
if not exist "data\02" mkdir data\02
if not exist "data\02\md" mkdir data\02\md
if not exist "data\02\yml" mkdir data\02\yml
if not exist "data\final" mkdir data\final
if not exist "data\final\md" mkdir data\final\md
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
if not exist "templates" mkdir templates
if not exist "utils" mkdir utils
echo [成功] 目录创建完成
echo.

:: 启动Flask应用
echo [5/5] 启动Web服务...
echo.
echo ========================================
echo    服务启动中，请稍候...
echo ========================================
echo.

:: 延迟3秒后打开浏览器
start /b timeout /t 3 /nobreak >nul && start http://localhost:5000

:: 启动Python应用
python app.py

:: 如果程序退出，暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo [错误] 服务启动失败
    pause
)