"""
预处理模块 - 在翻译前完成所有准备工作
"""
import json
import os
from typing import Dict, Tuple
from core.name_manager import NameManager


class Preprocessor:
    """预处理器"""

    def __init__(self, names_file: str, styles_file: str, base_prompt_file: str):
        self.names_file = names_file
        self.styles_file = styles_file
        self.base_prompt_file = base_prompt_file
        self.name_manager = NameManager(names_file)

    def preprocess_task(self, task_id: str, novel_path: str, genre: str, style_index: int) -> Tuple[str, str, Dict]:
        """
        预处理任务
        返回：(final_prompt, novel_content, name_mapping)
        """
        print(f"[预处理] 任务ID: {task_id}")

        # 1. 读取小说内容
        print("[预处理] 读取小说内容...")
        with open(novel_path, 'r', encoding='utf-8') as f:
            novel_content = f.read()
        print(f"[预处理] 小说内容: {len(novel_content)} 字符")

        # 2. 提取中文人名
        print("[预处理] 提取中文人名...")
        chinese_names = self.name_manager.extract_chinese_names(novel_content)
        print(f"[预处理] 提取到 {len(chinese_names)} 个人名: {chinese_names[:10]}")

        # 3. 分配英文名（使用文件锁）
        print("[预处理] 分配英文名...")
        name_mapping = self.name_manager.assign_english_names(chinese_names)
        print(f"[预处理] 已分配 {len(name_mapping)} 个英文名")

        # 4. 保存人名对照表
        output_dir = f"outputs/{task_id}"
        name_mapping_path = os.path.join(output_dir, "name_mapping.json")
        self.name_manager.create_name_mapping_file(name_mapping, name_mapping_path)
        print(f"[预处理] 人名对照表已保存: {name_mapping_path}")

        # 5. 读取写作风格
        print("[预处理] 读取写作风格...")
        with open(self.styles_file, 'r', encoding='utf-8') as f:
            styles_data = json.load(f)

        style_text = ""
        if genre in styles_data:
            styles_list = styles_data[genre]["styles"]
            if 0 <= style_index < len(styles_list):
                style_text = styles_list[style_index]
                print(f"[预处理] 使用风格: {genre} - 风格{style_index + 1}")

        # 6. 读取基础prompt
        print("[预处理] 组装最终prompt...")
        with open(self.base_prompt_file, 'r', encoding='utf-8') as f:
            base_prompt = f.read()

        # 7. 组装最终prompt（添加人名映射和写作风格）
        name_mapping_text = self.name_manager.format_name_mapping_for_prompt(name_mapping)

        final_prompt = f"""{base_prompt}

{name_mapping_text}

【WRITING STYLE】
{style_text}
"""

        print(f"[预处理] 最终prompt长度: {len(final_prompt)} 字符")
        print("[预处理] ✅ 预处理完成！")

        return final_prompt, novel_content, name_mapping
