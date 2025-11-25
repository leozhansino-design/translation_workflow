#!/usr/bin/env python3
"""打包前验证脚本 - 确保打包的数据是最新的"""

import json
import os
import shutil

print("=" * 60)
print("打包前验证")
print("=" * 60)

# 1. 检查styles.json
print("\n1. 检查 data/styles.json...")
with open('data/styles.json', 'r', encoding='utf-8') as f:
    styles = json.load(f)

genres = list(styles.keys())
print(f"   类型总数: {len(genres)}")

if 'Humor' in genres:
    print(f"   ✓ Humor存在 (位置 #{genres.index('Humor') + 1})")
else:
    print(f"   ❌ Humor不存在！")
    print(f"   当前类型: {', '.join(genres)}")
    exit(1)

# 2. 清理旧的打包文件
print("\n2. 清理旧的打包文件...")
to_clean = ['build', 'dist', 'OutlineGenerator.spec', 'WriterTaskManager.spec']
for item in to_clean:
    if os.path.exists(item):
        if os.path.isdir(item):
            shutil.rmtree(item)
            print(f"   ✓ 删除文件夹: {item}/")
        else:
            os.remove(item)
            print(f"   ✓ 删除文件: {item}")

# 3. 检查Git状态
print("\n3. 检查Git状态...")
import subprocess
try:
    branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
    print(f"   当前分支: {branch}")

    if branch != 'claude/fix-mac-generation-tools-01G2JxXzJnNqYoiB2FCpCqr1':
        print(f"   ⚠️  警告: 你不在正确的分支上！")
        print(f"   应该在: claude/fix-mac-generation-tools-01G2JxXzJnNqYoiB2FCpCqr1")

    commit = subprocess.check_output(['git', 'log', '-1', '--oneline'], text=True).strip()
    print(f"   最新提交: {commit}")

    # 检查是否有未提交的修改
    status = subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
    if status:
        print(f"   ⚠️  有未提交的修改")
    else:
        print(f"   ✓ 工作目录干净")

except Exception as e:
    print(f"   ⚠️  无法检查Git: {e}")

# 4. 验证关键文件存在
print("\n4. 验证关键文件...")
required_files = [
    'outline_generator.py',
    'main_task_manager.py',
    'resource_mgr.py',
    'utils.py',
    'config.py',
    'build_package.py',
    'data/styles.json',
    'data/names_1.json',
]

all_exist = True
for f in required_files:
    if os.path.exists(f):
        print(f"   ✓ {f}")
    else:
        print(f"   ❌ {f} 不存在！")
        all_exist = False

if not all_exist:
    print("\n❌ 有文件缺失，无法打包")
    exit(1)

print("\n" + "=" * 60)
print("✓✓✓ 验证通过！现在可以安全打包")
print("=" * 60)
print("\n建议的打包命令:")
print("\n调试版本 (推荐，可以看到错误):")
print("  python3 build_package.py --debug")
print("\n正式版本 (单文件):")
print("  python3 build_package.py")
print("\n打包完成后，可以运行:")
print("  python3 check_packaged_version.py")
print("来验证打包的应用是否包含Humor")
print("\n" + "=" * 60)
print("重要提示：应用缓存问题")
print("=" * 60)
print("\n如果你之前运行过打包的应用，它可能缓存了旧的styles.json")
print("重新打包后，需要清理缓存才能生效：")
print("\nWindows:")
print("  clear_cache_windows.bat  (双击运行)")
print("  或手动删除: %APPDATA%\\OutlineGenerator")
print("\nMac:")
print("  bash clear_cache_mac.sh")
print("  或手动删除: ~/Library/Application Support/OutlineGenerator")
