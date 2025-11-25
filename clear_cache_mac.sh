#!/bin/bash

echo "========================================"
echo "清理Mac应用缓存"
echo "========================================"
echo ""

echo "这个脚本会删除打包应用的缓存数据"
echo "缓存位置: ~/Library/Application Support/OutlineGenerator"
echo "          ~/Library/Application Support/WriterTaskManager"
echo ""
echo "删除后，应用会使用最新的styles.json（包含Humor类型）"
echo ""
read -p "按Enter继续..."

echo ""
echo "正在清理 OutlineGenerator 缓存..."
if [ -d "$HOME/Library/Application Support/OutlineGenerator" ]; then
    rm -rf "$HOME/Library/Application Support/OutlineGenerator"
    echo "✓ 已删除 OutlineGenerator 缓存"
else
    echo "ℹ OutlineGenerator 缓存不存在"
fi

echo ""
echo "正在清理 WriterTaskManager 缓存..."
if [ -d "$HOME/Library/Application Support/WriterTaskManager" ]; then
    rm -rf "$HOME/Library/Application Support/WriterTaskManager"
    echo "✓ 已删除 WriterTaskManager 缓存"
else
    echo "ℹ WriterTaskManager 缓存不存在"
fi

echo ""
echo "========================================"
echo "清理完成！"
echo "========================================"
echo ""
echo "现在运行打包的应用，它会使用新的styles.json"
echo "新的styles.json包含Humor类型"
echo ""
