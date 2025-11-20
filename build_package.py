"""
打包脚本 - 支持Mac和Windows
"""
import os
import sys
import platform
import subprocess


def build():
    """构建可执行文件"""
    system = platform.system()

    print(f"正在为 {system} 构建可执行文件...")

    # PyInstaller配置
    hidden_imports = [
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.simpledialog',
        'openai',
        'json',
        're'
    ]

    # 数据文件
    data_files = [
        ('data/styles.json', 'data'),
        ('data/names_1.json', 'data'),
    ]

    # 主程序入口
    entry_points = [
        ('outline_generator.py', 'OutlineGenerator'),
        ('main.py', 'TaskManager'),
    ]

    for script, name in entry_points:
        print(f"\n构建 {name}...")

        cmd = [
            'pyinstaller',
            '--name', name,
            '--onefile',
            '--windowed' if system != 'Linux' else '--console',
        ]

        # 添加hidden imports
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])

        # 添加数据文件
        for src, dest in data_files:
            cmd.extend(['--add-data', f'{src}{os.pathsep}{dest}'])

        # 添加图标（如果有）
        if os.path.exists('icon.ico') and system == 'Windows':
            cmd.extend(['--icon', 'icon.ico'])
        elif os.path.exists('icon.icns') and system == 'Darwin':
            cmd.extend(['--icon', 'icon.icns'])

        cmd.append(script)

        # 运行PyInstaller
        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"❌ 构建 {name} 失败")
            return False
        else:
            print(f"✅ 构建 {name} 成功")

    print(f"\n✅ 所有程序构建完成！")
    print(f"可执行文件位于 dist/ 文件夹")

    return True


if __name__ == '__main__':
    if not build():
        sys.exit(1)
