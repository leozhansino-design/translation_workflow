"""
资源管理模块 - 负责分配风格和人名
"""
import json
import os
import re
from datetime import datetime


STYLES_FILE = 'data/styles.json'
NAMES_FILE = 'data/names.json'
SUMMARY_FILE = 'data/summary.json'


class ResourceManager:
    """资源管理器"""

    def __init__(self):
        self.styles = self.load_styles()
        self.names = self.load_names()
        self.summary = self.load_summary()

    def load_styles(self):
        """加载风格库"""
        if os.path.exists(STYLES_FILE):
            with open(STYLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_styles(self):
        """保存风格库"""
        with open(STYLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.styles, f, indent=2, ensure_ascii=False)

    def load_names(self):
        """加载人名库"""
        if os.path.exists(NAMES_FILE):
            with open(NAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"male": [], "female": []}

    def save_names(self):
        """保存人名库"""
        with open(NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.names, f, indent=2, ensure_ascii=False)

    def load_summary(self):
        """加载翻译记录"""
        if os.path.exists(SUMMARY_FILE):
            with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"records": []}

    def save_summary(self):
        """保存翻译记录"""
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.summary, f, indent=2, ensure_ascii=False)

    def extract_genre(self, filename):
        """从文件名提取类型

        格式: 书名_类型.txt
        例如: 霸道总裁_Romance.txt -> Romance
        """
        basename = os.path.basename(filename)
        match = re.search(r'_([A-Za-z+\-]+)\.txt$', basename)
        if match:
            genre = match.group(1)
            # 验证类型是否存在
            if genre in self.styles:
                return genre
        # 默认返回 Romance
        return 'Romance'

    def extract_title(self, filename):
        """从文件名提取书名

        格式: 书名_类型.txt
        例如: 霸道总裁_Romance.txt -> 霸道总裁
        """
        basename = os.path.basename(filename)
        match = re.match(r'(.+?)_[A-Za-z+\-]+\.txt$', basename)
        if match:
            return match.group(1)
        # 如果没有匹配，返回不带扩展名的文件名
        return os.path.splitext(basename)[0]

    def allocate_resources(self, files):
        """批量分配资源（风格和人名）

        Args:
            files: 文件路径列表

        Returns:
            资源列表，每个元素包含 {'style': str, 'names': list, 'author': str}
        """
        resources = []
        used_names_in_batch = set()  # 这一批已分配的名字

        for file_path in files:
            genre = self.extract_genre(file_path)

            # 选择风格：找使用次数最少的
            if genre not in self.styles:
                print(f"警告: 类型 {genre} 不存在，使用 Romance")
                genre = 'Romance'

            genre_data = self.styles[genre]
            counts = genre_data['used']
            min_count = min(counts)
            min_idx = counts.index(min_count)

            style = genre_data['styles'][min_idx]
            author = genre_data['authors'][min_idx]

            # 立即更新使用次数，避免下一个也选这个
            self.styles[genre]['used'][min_idx] += 1

            # 选择人名：跳过已分配的
            available_male = [
                n for n in self.names['male']
                if n['name'] not in used_names_in_batch
            ]
            available_male.sort(key=lambda x: x['used'])

            available_female = [
                n for n in self.names['female']
                if n['name'] not in used_names_in_batch
            ]
            available_female.sort(key=lambda x: x['used'])

            # 每本书分配20个男名和20个女名
            selected_male = available_male[:20]
            selected_female = available_female[:20]

            # 标记为已使用
            for n in selected_male + selected_female:
                used_names_in_batch.add(n['name'])

            resources.append({
                'style': style,
                'author': author,
                'names': selected_male + selected_female,
                'genre': genre
            })

        # 保存更新的使用次数
        self.save_styles()

        return resources

    def update_name_usage(self, names_list, translated_content):
        """更新人名使用次数

        Args:
            names_list: 分配给这本书的名字列表
            translated_content: 翻译后的内容
        """
        for name_obj in names_list:
            name = name_obj['name']
            # 检查名字是否在翻译内容中出现
            if name in translated_content:
                # 在原始名字库中找到并更新使用次数
                for gender in ['male', 'female']:
                    for n in self.names[gender]:
                        if n['name'] == name:
                            n['used'] += 1
                            break

        # 保存更新
        self.save_names()

    def add_to_summary(self, record):
        """添加翻译记录

        Args:
            record: 包含 original, translated, genre, author_style,
                   names, time, cost 等字段的字典
        """
        record['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.summary['records'].append(record)
        self.save_summary()

    def get_available_genres(self):
        """获取所有可用的类型"""
        return list(self.styles.keys())
