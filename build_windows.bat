@echo off
chcp 65001 >nul
echo ============================================================
echo   小说翻译工具 - Windows 打包脚本
echo ============================================================
echo.

echo [1/3] 检查 Python 环境...
python --version
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.8+ 并添加到系统路径
    pause
    exit /b 1
)

echo.
echo [2/3] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyInstaller 未安装，正在安装...
    pip install pyinstaller
)

pip show openai >nul 2>&1
if errorlevel 1 (
    echo ⚠️  OpenAI SDK 未安装，正在安装...
    pip install openai
)

echo.
echo [3/3] 开始打包...
python build_package.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   打包成功！
echo ============================================================
echo.
echo 可执行文件位于 dist\ 文件夹:
dir dist\*.exe /B
echo.
echo 使用方法：
echo   1. 双击 dist\OutlineGenerator.exe 运行大纲生成器
echo   2. 双击 dist\TaskManager.exe 运行任务管理器
echo.
pause
