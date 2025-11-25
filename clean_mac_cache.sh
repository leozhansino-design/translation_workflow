#!/bin/bash
# macOS 应用缓存清理脚本
# 解决打包后 prompts 不更新的问题

echo "================================================"
echo "  清理 OutlineGenerator macOS 应用缓存"
echo "================================================"
echo ""

APP_SUPPORT_DIR=~/Library/Application\ Support/OutlineGenerator

# 检查目录是否存在
if [ -d "$APP_SUPPORT_DIR" ]; then
    echo "📁 找到应用支持目录："
    echo "   $APP_SUPPORT_DIR"
    echo ""

    # 显示当前缓存的文件
    echo "📋 当前缓存的文件："
    ls -lh "$APP_SUPPORT_DIR/data/" 2>/dev/null || echo "   (无 data 目录)"
    echo ""

    # 询问是否删除
    read -p "是否删除整个应用支持目录? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "$APP_SUPPORT_DIR"
        echo "✅ 已删除应用支持目录"
        echo ""
        echo "下次启动应用时会重新创建，使用最新的 prompts.json"
    else
        echo "❌ 取消删除"
    fi
else
    echo "ℹ️  应用支持目录不存在，无需清理"
    echo "   $APP_SUPPORT_DIR"
fi

echo ""
echo "================================================"
echo "  其他清理建议："
echo "================================================"
echo "1. 删除旧的 .app 文件"
echo "2. 清理 Python 缓存："
echo "   rm -rf __pycache__ build dist"
echo "3. 清理 .pyc 文件："
echo "   find . -name '*.pyc' -delete"
echo "4. 重新打包："
echo "   pyinstaller --clean your_spec_file.spec"
echo ""
echo "完成！"
