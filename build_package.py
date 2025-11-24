"""
打包脚本 - 支持Mac和Windows
使用PyInstaller将Python程序打包成独立的可执行文件
"""
import os
import sys
import platform
import subprocess
import shutil


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False


def clean_build_dirs():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}/ ...")
            shutil.rmtree(dir_name)

    # 清理.spec文件
    for spec_file in ['OutlineGenerator.spec', 'TaskManager.spec']:
        if os.path.exists(spec_file):
            os.remove(spec_file)

    print("✓ 清理完成\n")


def build():
    """构建可执行文件"""
    system = platform.system()

    print(f"{'='*60}")
    print(f"  小说翻译工具 - 打包程序")
    print(f"  目标平台: {system}")
    print(f"{'='*60}\n")

    # 检查依赖
    if not check_dependencies():
        return False

    # 清理旧文件
    clean_build_dirs()

    # PyInstaller配置
    hidden_imports = [
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.simpledialog',
        'openai',
        'openai.types',
        'openai.types.chat',
        'PIL',
        'PIL.Image',
        'PIL._tkinter_finder',
        'json',
        're',
        'threading',
        'subprocess',
        'uuid',
        'datetime',
        'glob',
        'shutil'
    ]

    # 数据文件（使用正确的分隔符）
    separator = ';' if system == 'Windows' else ':'
    data_files = [
        ('data/styles.json', 'data'),
        ('data/names_1.json', 'data'),
    ]

    # 检查并添加summary.json（如果存在）
    if os.path.exists('data/summary.json'):
        data_files.append(('data/summary.json', 'data'))

    # 主程序入口
    entry_points = [
        ('outline_generator.py', 'OutlineGenerator'),
        ('main_task_manager.py', 'WriterTaskManager'),
    ]

    for script, name in entry_points:
        print(f"\n{'='*60}")
        print(f"正在构建: {name}")
        print(f"{'='*60}")

        if not os.path.exists(script):
            print(f"❌ 找不到文件: {script}")
            continue

        # 构建命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--name', name,
            '--onefile',
            '--clean',  # 清理临时文件
        ]

        # Windows使用窗口模式，避免控制台弹出
        if system == 'Windows':
            cmd.append('--windowed')
            cmd.append('--noconsole')
        elif system == 'Darwin':  # Mac
            cmd.append('--windowed')
        else:  # Linux
            cmd.append('--console')

        # 添加hidden imports
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])

        # 添加数据文件
        for src, dest in data_files:
            if os.path.exists(src):
                cmd.extend(['--add-data', f'{src}{separator}{dest}'])

        # 添加其他必需的模块
        cmd.extend(['--collect-all', 'openai'])

        # 添加PIL/Pillow支持
        cmd.extend(['--collect-submodules', 'PIL'])

        # 修复Tkinter打包问题 - 收集Tcl/Tk数据文件
        if system == 'Windows':
            cmd.extend(['--collect-data', 'tkinter'])
            cmd.extend(['--collect-data', 'tcl'])
            cmd.extend(['--collect-data', 'tk'])

        # 添加图标（如果有）
        if os.path.exists('icon.ico') and system == 'Windows':
            cmd.extend(['--icon', 'icon.ico'])
            print("✓ 使用自定义图标: icon.ico")
        elif os.path.exists('icon.icns') and system == 'Darwin':
            cmd.extend(['--icon', 'icon.icns'])
            print("✓ 使用自定义图标: icon.icns")

        # 添加版本信息（Windows）
        if system == 'Windows' and os.path.exists('version.txt'):
            cmd.extend(['--version-file', 'version.txt'])

        cmd.append(script)

        print(f"\n执行命令:")
        print(f"  {' '.join(cmd)}\n")

        # 运行PyInstaller
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"\n❌ 构建 {name} 失败")
            return False
        else:
            print(f"\n✅ 构建 {name} 成功")

    print(f"\n{'='*60}")
    print(f"  构建完成！")
    print(f"{'='*60}")
    print(f"\n可执行文件位于 dist/ 文件夹:")

    # 列出生成的文件
    if os.path.exists('dist'):
        for filename in os.listdir('dist'):
            file_path = os.path.join('dist', filename)
            size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"  - {filename} ({size:.1f} MB)")

    print(f"\n使用方法:")
    if system == 'Windows':
        print(f"  Tool 1 (大纲生成器-带任务队列): dist\\OutlineGenerator.exe")
        print(f"  Tool 2 (章节写作任务管理器): dist\\WriterTaskManager.exe")
    else:
        print(f"  Tool 1 (大纲生成器-带任务队列): ./dist/OutlineGenerator")
        print(f"  Tool 2 (章节写作任务管理器): ./dist/WriterTaskManager")

    return True


if __name__ == '__main__':
    try:
        if not build():
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  构建已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
