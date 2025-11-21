@echo off
chcp 65001 >nul
title 大纲生成器 - Tool 1

echo ============================================================
echo   启动大纲生成器 (Tool 1)
echo ============================================================
echo.

if exist "dist\OutlineGenerator.exe" (
    echo 使用打包版本...
    start "" "dist\OutlineGenerator.exe"
) else (
    echo 使用源代码版本...
    python outline_generator.py
)

exit
