@echo off
REM Windows 应用缓存清理脚本
REM 解决打包后 prompts 不更新的问题

echo ================================================
echo   清理 OutlineGenerator Windows 应用缓存
echo ================================================
echo.

set APP_DIR=%APPDATA%\OutlineGenerator

REM 检查目录是否存在
if exist "%APP_DIR%" (
    echo 📁 找到应用支持目录：
    echo    %APP_DIR%
    echo.

    echo 📋 当前缓存的文件：
    if exist "%APP_DIR%\data" (
        dir "%APP_DIR%\data" /b
    ) else (
        echo    (无 data 目录)
    )
    echo.

    set /p confirm="是否删除整个应用支持目录? (y/N): "
    if /i "%confirm%"=="y" (
        rmdir /s /q "%APP_DIR%"
        echo ✅ 已删除应用支持目录
        echo.
        echo 下次启动应用时会重新创建，使用最新的 prompts.json
    ) else (
        echo ❌ 取消删除
    )
) else (
    echo ℹ️  应用支持目录不存在，无需清理
    echo    %APP_DIR%
)

echo.
echo ================================================
echo   其他清理建议：
echo ================================================
echo 1. 删除旧的 .exe 文件
echo 2. 清理 Python 缓存：
echo    rmdir /s /q __pycache__ build dist
echo 3. 清理 .pyc 文件：
echo    del /s /q *.pyc
echo 4. 重新打包：
echo    pyinstaller --clean build_package.py
echo.
echo 完成！
pause
