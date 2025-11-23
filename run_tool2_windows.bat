@echo off
chcp 65001 >nul
title 任务管理器 - Tool 2

echo ============================================================
echo   启动任务管理器 (Tool 2)
echo ============================================================
echo.

if exist "dist\TaskManager.exe" (
    echo 使用打包版本...
    start "" "dist\TaskManager.exe"
) else (
    echo 使用源代码版本...
    python main_task_manager.py
)

exit
