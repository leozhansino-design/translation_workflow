"""
打包脚本 - 使用PyInstaller打包成单个exe文件

使用方法:
    python build_exe.py

生成文件:
    dist/NovelTranslator.exe
"""

import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'main.py',                              # 主程序
    '--onefile',                            # 打包成单个文件
    '--windowed',                           # 不显示控制台窗口
    '--name=NovelTranslator',               # 程序名称
    '--add-data=data;data',                 # 包含data目录
    '--hidden-import=openai',               # 隐式导入
    '--hidden-import=tkinter',
    '--hidden-import=concurrent.futures',
    '--clean',                              # 清理临时文件
    '--noconfirm',                          # 不询问确认
])

print("\n" + "="*50)
print("打包完成！")
print("生成文件: dist/NovelTranslator.exe")
print("="*50)
