"""
翻译脚本 4
"""
from translator_base import main

if __name__ == "__main__":
    import sys
    env = sys.argv[1] if len(sys.argv) >= 2 else "windows1"
    main(4, env)
