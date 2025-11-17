#!/bin/bash
# macOS应用打包脚本 - 调试增强版
# 包含详细的错误检查和调试信息

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Novel Translator - macOS 调试打包脚本"
echo "=========================================="
echo ""

# === 环境检查 ===
echo "🔍 步骤1: 检查环境..."
echo ""

# 检查Python版本
echo "检查Python版本..."
python3 --version || {
    echo "❌ Python3未安装！"
    echo "请运行: brew install python@3.11"
    exit 1
}

# 检查虚拟环境
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境"
    echo "正在激活虚拟环境..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
    else
        echo "❌ 找不到虚拟环境！"
        echo "请先运行: python3 -m venv venv"
        exit 1
    fi
else
    echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
fi

# 检查PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "⚠️  未安装PyInstaller，正在安装..."
    pip install pyinstaller
    echo "✅ PyInstaller安装完成"
else
    echo "✅ PyInstaller已安装: $(pyinstaller --version)"
fi

# 检查依赖
echo ""
echo "检查必要的依赖..."
python3 -c "import tkinter; import openai; import pandas; import openpyxl; import aiohttp" || {
    echo "❌ 缺少必要的依赖！"
    echo "正在安装依赖..."
    pip install -r NovelTranslator/requirements.txt
}
echo "✅ 所有依赖已安装"

# === 检查项目文件 ===
echo ""
echo "🔍 步骤2: 检查项目文件..."
echo ""

# 检查NovelTranslator目录
if [ ! -d "NovelTranslator" ]; then
    echo "❌ 找不到NovelTranslator目录！"
    echo "请确保在项目根目录运行此脚本"
    exit 1
fi
echo "✅ NovelTranslator目录存在"

# 检查main.py
if [ ! -f "NovelTranslator/main.py" ]; then
    echo "❌ 找不到main.py！"
    exit 1
fi
echo "✅ main.py存在"

# 检查data目录
if [ ! -d "NovelTranslator/data" ]; then
    echo "❌ 找不到data目录！"
    exit 1
fi
echo "✅ data目录存在"

# 检查关键文件
echo "检查data目录内容..."
for file in "names.json" "styles.json"; do
    if [ ! -f "NovelTranslator/data/$file" ]; then
        echo "❌ 缺少文件: data/$file"
        exit 1
    else
        echo "  ✅ $file"
    fi
done

# 检查path_utils.py
if [ ! -f "NovelTranslator/path_utils.py" ]; then
    echo "⚠️  警告: 找不到path_utils.py（路径修复模块）"
    echo "这可能导致打包后的应用无法运行！"
    read -p "是否继续？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ path_utils.py存在"
fi

# === 测试运行 ===
echo ""
echo "🔍 步骤3: 测试程序是否能运行..."
echo ""
echo "正在测试导入模块..."

cd NovelTranslator

python3 -c "
import sys
try:
    from config import ConfigManager
    from resource_mgr import ResourceManager
    from translator import Translator
    from path_utils import get_data_dir, get_output_dir
    print('✅ 所有模块导入成功')
except Exception as e:
    print(f'❌ 模块导入失败: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 程序无法运行，请修复错误后再打包！"
    exit 1
fi

cd ..

echo ""
echo "✅ 程序通过基本测试"

# === 开始打包 ===
echo ""
echo "📦 步骤4: 开始打包应用..."
echo ""

cd NovelTranslator

# 清理旧的打包文件
if [ -d "dist" ]; then
    echo "🗑️  清理旧的打包文件..."
    rm -rf dist build *.spec
fi

echo "正在打包，请稍候..."
echo ""

# 打包应用（添加更多隐藏导入）
pyinstaller \
    --name="NovelTranslator" \
    --windowed \
    --onefile \
    --add-data "data:data" \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --hidden-import=tkinter.filedialog \
    --hidden-import=tkinter.messagebox \
    --hidden-import=tkinter.scrolledtext \
    --hidden-import=openai \
    --hidden-import=pandas \
    --hidden-import=openpyxl \
    --hidden-import=aiohttp \
    --hidden-import=path_utils \
    --hidden-import=config \
    --hidden-import=resource_mgr \
    --hidden-import=translator \
    --collect-all openai \
    --collect-all aiohttp \
    --clean \
    main.py 2>&1 | tee ../build_log.txt

echo ""
echo "✅ 打包完成！"
echo ""

# === 验证打包结果 ===
echo "🔍 步骤5: 验证打包结果..."
echo ""

APP_PATH="dist/NovelTranslator.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 打包失败！找不到.app文件"
    echo "请查看 build_log.txt 了解详细错误"
    exit 1
fi

echo "✅ .app文件已创建: $(pwd)/$APP_PATH"

# 检查.app内的data目录
DATA_PATH="$APP_PATH/Contents/MacOS/data"
if [ ! -d "$DATA_PATH" ]; then
    echo "⚠️  警告: .app内缺少data目录！"
    echo "路径: $DATA_PATH"
else
    echo "✅ data目录已包含在.app中"
    echo "  文件列表:"
    ls -lh "$DATA_PATH" | awk '{print "    " $9}'
fi

# === 测试运行 ===
echo ""
echo "🔍 步骤6: 测试打包后的应用..."
echo ""

EXEC_PATH="$APP_PATH/Contents/MacOS/NovelTranslator"

echo "尝试运行应用（5秒后自动关闭）..."
echo "如果有错误会显示在下方："
echo "---"

# 运行5秒后自动关闭（使用timeout）
timeout 5s "$EXEC_PATH" 2>&1 || {
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "---"
        echo "✅ 应用启动成功（已自动关闭）"
    else
        echo "---"
        echo "❌ 应用启动失败！退出代码: $exit_code"
        echo ""
        echo "请手动运行以下命令查看详细错误："
        echo "  $EXEC_PATH"
        echo ""
        echo "或查看构建日志:"
        echo "  cat ../build_log.txt"
        exit 1
    fi
}

cd ..

# === 询问是否安装 ===
echo ""
echo "应用位置: $(pwd)/NovelTranslator/dist/NovelTranslator.app"
echo ""

read -p "是否将应用复制到 /Applications 文件夹？ (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📋 复制到 /Applications..."
    cp -r NovelTranslator/dist/NovelTranslator.app /Applications/

    echo "🔓 移除隔离属性（避免\"无法验证开发者\"警告）..."
    sudo xattr -r -d com.apple.quarantine /Applications/NovelTranslator.app 2>/dev/null || true

    echo "✅ 已安装到 /Applications/NovelTranslator.app"
    echo ""
    echo "您现在可以从启动台或应用程序文件夹启动 Novel Translator 了！"
    echo ""
    echo "如果应用无法启动，请运行以下命令查看错误："
    echo "  /Applications/NovelTranslator.app/Contents/MacOS/NovelTranslator"
else
    echo "跳过复制。您可以手动从 dist 文件夹启动应用。"
    echo ""
    echo "手动测试命令："
    echo "  NovelTranslator/dist/NovelTranslator.app/Contents/MacOS/NovelTranslator"
fi

echo ""
echo "=========================================="
echo "  打包完成！"
echo "=========================================="
echo ""
echo "📝 调试信息："
echo "1. 构建日志: build_log.txt"
echo "2. 应用路径: NovelTranslator/dist/NovelTranslator.app"
echo "3. 测试命令: NovelTranslator/dist/NovelTranslator.app/Contents/MacOS/NovelTranslator"
echo ""
