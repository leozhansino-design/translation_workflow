@echo off
echo ========================================
echo 清理Windows应用缓存
echo ========================================
echo.

echo 这个脚本会删除打包应用的缓存数据
echo 缓存位置: %%APPDATA%%\OutlineGenerator
echo           %%APPDATA%%\WriterTaskManager
echo.
echo 删除后，应用会使用最新的styles.json（包含Humor类型）
echo.
pause

echo.
echo 正在清理 OutlineGenerator 缓存...
if exist "%APPDATA%\OutlineGenerator" (
    rmdir /s /q "%APPDATA%\OutlineGenerator"
    echo [OK] 已删除 OutlineGenerator 缓存
) else (
    echo [提示] OutlineGenerator 缓存不存在
)

echo.
echo 正在清理 WriterTaskManager 缓存...
if exist "%APPDATA%\WriterTaskManager" (
    rmdir /s /q "%APPDATA%\WriterTaskManager"
    echo [OK] 已删除 WriterTaskManager 缓存
) else (
    echo [提示] WriterTaskManager 缓存不存在
)

echo.
echo ========================================
echo 清理完成！
echo ========================================
echo.
echo 现在运行打包的应用，它会使用新的styles.json
echo 新的styles.json包含Humor类型
echo.
pause
