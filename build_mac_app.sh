#!/bin/bash
# macOS应用打包脚本

echo "开始打包 macOS 应用..."

# 激活虚拟环境
source venv/bin/activate

# 安装PyInstaller和SSL证书
pip install pyinstaller certifi

# 清理之前的构建
rm -rf build dist *.spec

echo "打包大纲生成器..."
pyinstaller --clean \
    --name="OutlineGenerator" \
    --windowed \
    --add-data="data:data" \
    --hidden-import="PIL._tkinter_finder" \
    --collect-all="tkinter" \
    --collect-data="certifi" \
    --copy-metadata="certifi" \
    outline_generator.py

echo "打包章节写作工具..."
pyinstaller --clean \
    --name="ChapterWriter" \
    --windowed \
    --add-data="data:data" \
    --hidden-import="PIL._tkinter_finder" \
    --collect-all="tkinter" \
    --collect-data="certifi" \
    --copy-metadata="certifi" \
    main_task_manager.py

echo "打包完成！"
echo "应用位置: dist/OutlineGenerator.app 和 dist/ChapterWriter.app"
echo "请将.app文件拖到应用程序文件夹使用"
