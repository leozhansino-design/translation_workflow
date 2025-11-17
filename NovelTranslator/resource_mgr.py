"""
资源管理器 - 负责分配风格和人名（支持云端同步）
确保同批次翻译时：
1. 同类型小说轮流使用不同风格
2. 人名不重复
"""

import json
import os
from typing import List, Dict, Any
from path_utils import get_data_dir
from cloud_sync import CloudSync


class ResourceManager:
    def __init__(self, data_dir: str = None):
        # 使用正确的路径（开发模式和打包模式都支持）
        if data_dir is None:
            data_dir = get_data_dir()
        self.data_dir = data_dir

        # 初始化云端同步
        self.cloud_sync = CloudSync()

        # 使用云端路径（如果启用）或本地路径
        self.styles_file = self.cloud_sync.get_data_file_path(
            "styles.json",
            os.path.join(data_dir, "styles.json")
        )
        self.names_file = self.cloud_sync.get_data_file_path(
            "names.json",
            os.path.join(data_dir, "names.json")
        )

    def load_styles(self) -> Dict:
        """加载风格数据"""
        with open(self.styles_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_styles(self, styles: Dict):
        """保存风格数据"""
        with open(self.styles_file, 'w', encoding='utf-8') as f:
            json.dump(styles, f, indent=2, ensure_ascii=False)

    def load_names(self) -> Dict:
        """加载人名数据"""
        with open(self.names_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_names(self, names: Dict):
        """保存人名数据"""
        with open(self.names_file, 'w', encoding='utf-8') as f:
            json.dump(names, f, indent=2, ensure_ascii=False)

    def extract_genre(self, filename: str) -> str:
        """
        从文件名提取类型
        格式: 书名_类型.txt
        """
        basename = os.path.basename(filename)
        if '_' in basename:
            genre_part = basename.split('_')[-1]
            genre = genre_part.replace('.txt', '').strip()
            return genre
        return "Romance"  # 默认类型

    def extract_title(self, filename: str) -> str:
        """从文件名提取书名"""
        basename = os.path.basename(filename)
        if '_' in basename:
            return basename.split('_')[0]
        return basename.replace('.txt', '')

    def allocate_resources(self, files: List[str]) -> List[Dict[str, Any]]:
        """
        批量分配资源给多个文件

        核心逻辑：
        1. 同类型小说轮流使用不同风格（选使用次数最少的）
        2. 同批次人名不重复

        返回: List of {style, names, genre, author}
        """
        styles = self.load_styles()
        names = self.load_names()

        resources = []
        used_names_batch = set()  # 本批次已分配的人名

        for file in files:
            genre = self.extract_genre(file)

            # 如果类型不存在，使用默认Romance
            if genre not in styles:
                genre = "Romance"

            # 1. 选择风格：找使用次数最少的
            genre_data = styles[genre]
            used_counts = genre_data['used']
            min_count = min(used_counts)
            min_idx = used_counts.index(min_count)

            selected_style = genre_data['styles'][min_idx]
            selected_author = genre_data['authors'][min_idx] if min_idx < len(genre_data['authors']) else "Unknown"

            # 立即增加使用次数，避免下一个文件也选这个
            genre_data['used'][min_idx] += 1

            # 2. 选择人名：排除本批次已使用的（使用fullname）
            available_male = [n for n in names['male']
                             if n['fullname'] not in used_names_batch]
            available_male.sort(key=lambda x: x['used'])  # 按使用次数排序
            selected_male = available_male[:20]  # 选前20个

            available_female = [n for n in names['female']
                               if n['fullname'] not in used_names_batch]
            available_female.sort(key=lambda x: x['used'])
            selected_female = available_female[:20]

            # 标记为已使用（仅本批次）
            for n in selected_male + selected_female:
                used_names_batch.add(n['fullname'])

            resources.append({
                'style': selected_style,
                'names': selected_male + selected_female,
                'genre': genre,
                'author': selected_author
            })

        # 保存更新后的风格使用次数
        self.save_styles(styles)

        return resources

    def update_name_usage(self, used_names: List[str]):
        """
        更新人名使用次数
        在翻译完成后调用
        """
        names = self.load_names()

        # 转为集合以便快速查找
        used_set = set(used_names)

        # 更新使用次数（使用fullname）
        for name_obj in names['male']:
            if name_obj['fullname'] in used_set:
                name_obj['used'] += 1

        for name_obj in names['female']:
            if name_obj['fullname'] in used_set:
                name_obj['used'] += 1

        self.save_names(names)
