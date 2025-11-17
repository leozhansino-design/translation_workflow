#!/bin/bash
# macOS应用打包脚本 - Novel Translator

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Novel Translator - macOS 打包脚本"
echo "=========================================="
echo ""

# 检查是否在虚拟环境中
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境"
    echo "正在激活虚拟环境..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 找不到虚拟环境，请先运行: python3 -m venv venv"
        exit 1
    fi
fi

# 检查PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "⚠️  未安装PyInstaller，正在安装..."
    pip install pyinstaller
    echo "✅ PyInstaller安装完成"
fi

# 进入程序目录
cd NovelTranslator

echo ""
echo "📦 开始打包应用..."
echo ""

# 清理旧的打包文件
if [ -d "dist" ]; then
    echo "🗑️  清理旧的打包文件..."
    rm -rf dist build *.spec
fi

# 打包应用
pyinstaller \
    --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=openai \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    --hidden-import=aiohttp \
    --clean \
    main.py

echo ""
echo "✅ 打包完成！"
echo ""
echo "应用位置: $(pwd)/dist/NovelTranslator.app"
echo ""

# 询问是否复制到应用程序文件夹
read -p "是否将应用复制到 /Applications 文件夹？ (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 复制到 /Applications..."
    cp -r dist/NovelTranslator.app /Applications/
    echo "✅ 已复制到 /Applications/NovelTranslator.app"
    echo ""
    echo "您现在可以从启动台或应用程序文件夹启动 Novel Translator 了！"
else
    echo "跳过复制。您可以手动从 dist 文件夹启动应用。"
fi

echo ""
echo "=========================================="
echo "  打包完成！"
echo "=========================================="
echo ""
echo "📝 注意事项："
echo "1. 首次运行时，macOS可能会提示\"无法验证开发者\""
echo "2. 解决方法：右键点击应用 → 选择\"打开\" → 点击\"打开\"确认"
echo "3. 或者运行: sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app"
echo ""
