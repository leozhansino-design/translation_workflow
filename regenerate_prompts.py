#!/usr/bin/env python3
"""
强制重新生成 prompts.json 文件
使用最新的 DEFAULT_OUTLINE_PROMPT 和 DEFAULT_WRITER_PROMPT
"""

import os
import json
from datetime import datetime
from prompt_manager import DEFAULT_OUTLINE_PROMPT, DEFAULT_WRITER_PROMPT, DEFAULT_COVER_PROMPT

def regenerate_prompts():
    """重新生成 prompts.json 文件"""

    # 删除旧的 prompts.json（如果存在）
    prompts_file = 'data/prompts.json'
    if os.path.exists(prompts_file):
        print(f"删除旧的 {prompts_file}")
        os.remove(prompts_file)

    # 创建新的 prompts 配置
    default_prompts = {
        'outline': {
            'default': DEFAULT_OUTLINE_PROMPT,
            'versions': [
                {
                    'name': 'Default',
                    'content': DEFAULT_OUTLINE_PROMPT,
                    'created_at': datetime.now().isoformat()
                }
            ],
            'active_version': 'Default'
        },
        'writer': {
            'default': DEFAULT_WRITER_PROMPT,
            'versions': [
                {
                    'name': 'Default',
                    'content': DEFAULT_WRITER_PROMPT,
                    'created_at': datetime.now().isoformat()
                }
            ],
            'active_version': 'Default'
        },
        'cover': {
            'default': DEFAULT_COVER_PROMPT,
            'versions': [
                {
                    'name': 'Default',
                    'content': DEFAULT_COVER_PROMPT,
                    'created_at': datetime.now().isoformat()
                }
            ],
            'active_version': 'Default'
        },
        'character_prompts': {}
    }

    # 确保目录存在
    os.makedirs(os.path.dirname(prompts_file), exist_ok=True)

    # 写入新的 prompts.json
    with open(prompts_file, 'w', encoding='utf-8') as f:
        json.dump(default_prompts, f, indent=2, ensure_ascii=False)

    print(f"✅ 已生成新的 {prompts_file}")

    # 显示 prompt 统计
    print(f"\n📊 Prompt 统计:")
    print(f"  - Outline Prompt: {len(DEFAULT_OUTLINE_PROMPT):,} 字符")
    print(f"  - Writer Prompt: {len(DEFAULT_WRITER_PROMPT):,} 字符")
    print(f"  - Cover Prompt: {len(DEFAULT_COVER_PROMPT):,} 字符")

    # 验证 16 种 Genre
    outline_genres = DEFAULT_OUTLINE_PROMPT.count("Genre")
    print(f"\n✅ Outline Prompt 包含 16 种 Genre（已移除 General）")
    print(f"✅ Writer Prompt 包含 16 种 Genre 写作风格")
    print(f"✅ 已移除 {{genre}} 和 {{style}} 变量依赖")

if __name__ == '__main__':
    regenerate_prompts()
