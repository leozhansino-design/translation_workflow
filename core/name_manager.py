"""
人名管理模块 - 提取中文人名并分配英文名
"""
import json
import re
import fcntl
import os
from typing import Dict, List, Tuple


class NameManager:
    """人名管理器"""

    def __init__(self, names_file: str):
        self.names_file = names_file

    def extract_chinese_names(self, text: str) -> List[str]:
        """
        从文本中提取中文人名
        简单规则：2-4个连续中文字符，且在文本中出现多次的
        """
        # 匹配2-4个连续中文字符
        pattern = r'[\u4e00-\u9fff]{2,4}'
        potential_names = re.findall(pattern, text)

        # 统计出现频率
        name_counts = {}
        for name in potential_names:
            name_counts[name] = name_counts.get(name, 0) + 1

        # 过滤：出现次数 >= 3 的作为人名
        extracted_names = [name for name, count in name_counts.items() if count >= 3]

        # 按出现频率排序
        extracted_names.sort(key=lambda x: name_counts[x], reverse=True)

        return extracted_names

    def assign_english_names(self, chinese_names: List[str]) -> Dict[str, str]:
        """
        为中文人名分配英文名
        使用文件锁保护names.json
        """
        name_mapping = {}

        # 读取names.json（加文件锁）
        with open(self.names_file, 'r+', encoding='utf-8') as f:
            # 加锁
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

            try:
                names_data = json.load(f)

                # 为每个中文名分配英文名
                for cn_name in chinese_names:
                    # 简单判断性别（可以改进）
                    gender = self._guess_gender(cn_name)

                    # 从对应性别列表中找到使用次数最少的名字
                    assigned_name = self._get_least_used_name(names_data, gender)

                    if assigned_name:
                        name_mapping[cn_name] = assigned_name
                        # 增加使用次数
                        self._increment_name_usage(names_data, gender, assigned_name)

                # 写回文件
                f.seek(0)
                f.truncate()
                json.dump(names_data, f, indent=2, ensure_ascii=False)

            finally:
                # 解锁
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return name_mapping

    def _guess_gender(self, name: str) -> str:
        """
        简单的性别判断（基于常见字）
        可以根据需要改进
        """
        # 常见女性名字字
        female_chars = ['芳', '娜', '丽', '婷', '莉', '雪', '梅', '红', '玲', '秀', '英', '华', '慧', '敏', '静']

        for char in female_chars:
            if char in name:
                return 'female'

        return 'male'  # 默认male

    def _get_least_used_name(self, names_data: dict, gender: str) -> str:
        """获取使用次数最少的名字"""
        names_list = names_data.get(gender, [])

        if not names_list:
            return None

        # 找到使用次数最少的
        min_used = min(names_list, key=lambda x: x['used'])
        return min_used['name']

    def _increment_name_usage(self, names_data: dict, gender: str, name: str):
        """增加名字使用次数"""
        names_list = names_data.get(gender, [])

        for item in names_list:
            if item['name'] == name:
                item['used'] += 1
                break

    def create_name_mapping_file(self, name_mapping: Dict[str, str], output_path: str):
        """保存人名对照表"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(name_mapping, f, indent=2, ensure_ascii=False)

    def format_name_mapping_for_prompt(self, name_mapping: Dict[str, str]) -> str:
        """
        格式化人名对照表，用于插入prompt
        """
        if not name_mapping:
            return ""

        mapping_text = "\n【CHARACTER NAME MAPPING - USE THESE EXACTLY】\n"
        for cn_name, en_name in name_mapping.items():
            mapping_text += f"{cn_name} → {en_name}\n"
        mapping_text += "\n"

        return mapping_text
