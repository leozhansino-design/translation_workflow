"""
启动GUI的简单脚本
"""
import sys
import os

# 确保在项目根目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 运行主GUI
from main_gui import main

if __name__ == "__main__":
    main()
