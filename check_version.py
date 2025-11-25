#!/usr/bin/env python3
"""检查实际运行版本和加载的数据"""

import json
import os
import sys

print("=" * 60)
print("版本和数据诊断")
print("=" * 60)

# 检查是否在打包环境中
if getattr(sys, 'frozen', False):
    print("运行环境: 打包版本 (PyInstaller)")
    print(f"可执行文件: {sys.executable}")
    print(f"_MEIPASS: {sys._MEIPASS}")

    # 检查打包的styles.json
    styles_path = os.path.join(sys._MEIPASS, 'data', 'styles.json')
    print(f"\n打包的styles.json路径: {styles_path}")
else:
    print("运行环境: Python源代码")
    print(f"Python: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")

    styles_path = 'data/styles.json'
    print(f"\nstyles.json路径: {styles_path}")

# 检查文件
if os.path.exists(styles_path):
    print(f"✓ 文件存在")

    with open(styles_path, 'r', encoding='utf-8') as f:
        styles = json.load(f)

    genres = list(styles.keys())
    print(f"✓ 类型总数: {len(genres)}")
    print(f"\n所有类型:")
    for i, genre in enumerate(genres, 1):
        marker = "👉" if genre == "Humor" else "  "
        print(f"{marker} {i}. {genre}")

    if 'Humor' in genres:
        print(f"\n✓✓✓ Humor存在于位置 #{genres.index('Humor') + 1}")
    else:
        print(f"\n❌❌❌ Humor不存在！")
        print("这说明你运行的是旧版本的打包文件")
else:
    print(f"❌ 文件不存在: {styles_path}")

# 测试ResourceManager
print("\n" + "=" * 60)
print("ResourceManager测试")
print("=" * 60)

try:
    from resource_mgr import ResourceManager
    mgr = ResourceManager()
    genres = mgr.get_available_genres()

    print(f"✓ 加载的类型数: {len(genres)}")
    print(f"\n所有类型:")
    for i, genre in enumerate(genres, 1):
        marker = "👉" if genre == "Humor" else "  "
        print(f"{marker} {i}. {genre}")

    if 'Humor' in genres:
        print(f"\n✓✓✓ Humor被ResourceManager加载")
    else:
        print(f"\n❌❌❌ ResourceManager没有加载Humor")
except Exception as e:
    print(f"❌ 加载失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("结论")
print("=" * 60)

# Git信息
if os.path.exists('.git'):
    import subprocess
    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        commit = subprocess.check_output(['git', 'log', '-1', '--oneline'], text=True).strip()
        print(f"\nGit分支: {branch}")
        print(f"最新提交: {commit}")
    except:
        pass

print("\n如果看到Humor存在，说明代码是最新的")
print("如果Humor不存在，说明:")
print("  1. 你可能下载了错误的分支")
print("  2. 或者运行的是旧的打包文件")
print("\n正确的分支应该是: claude/fix-mac-generation-tools-01G2JxXzJnNqYoiB2FCpCqr1")
print("最新提交应该包含: fix: Normalize genre capitalization")
