"""
翻译脚本 5
"""
from translator_base import main

if __name__ == "__main__":
    import sys
    env = sys.argv[1] if len(sys.argv) >= 2 else "windows1"
    main(5, env)
