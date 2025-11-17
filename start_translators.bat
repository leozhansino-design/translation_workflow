@echo off
REM 批量启动翻译器脚本
REM 用法: start_translators.bat [环境名称] [翻译器数量]
REM 例如: start_translators.bat windows1 5

set ENV=%1
set COUNT=%2

if "%ENV%"=="" set ENV=windows1
if "%COUNT%"=="" set COUNT=1

echo 启动 %COUNT% 个翻译器（环境: %ENV%）
echo.

for /L %%i in (1,1,%COUNT%) do (
    echo 启动翻译器 %%i...
    start "Translator %%i" python translators/translator_%%i.py %ENV%
)

echo.
echo 已启动 %COUNT% 个翻译器
pause
