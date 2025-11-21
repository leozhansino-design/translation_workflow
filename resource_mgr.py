"""
资源管理模块 - 负责分配风格和人名
支持并发安全的资源分配
"""
import json
import os
import sys
import re
import threading
import time
from datetime import datetime


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）

    如果是打包环境且本地没有data文件夹，会自动从打包资源复制到当前目录

    Args:
        relative_path: 相对路径，如 'data/styles.json'

    Returns:
        绝对路径
    """
    # 优先使用当前目录的文件（用于读写）
    local_path = os.path.join(os.getcwd(), relative_path)

    # 如果本地文件存在，直接使用
    if os.path.exists(local_path):
        return local_path

    # 检查是否是打包环境
    try:
        # PyInstaller创建临时文件夹，路径存储在_MEIPASS中
        base_path = sys._MEIPASS
        bundled_path = os.path.join(base_path, relative_path)

        # 如果是data目录下的文件，且打包资源存在，复制到本地
        if relative_path.startswith('data/') and os.path.exists(bundled_path):
            # 确保本地data目录存在
            local_data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(local_data_dir, exist_ok=True)

            # 复制文件到本地
            import shutil
            try:
                shutil.copy2(bundled_path, local_path)
                print(f"✓ 已复制资源文件: {relative_path}")
            except Exception as e:
                print(f"⚠ 复制资源文件失败: {e}")
                # 复制失败，返回打包路径（只读）
                return bundled_path

        return local_path

    except AttributeError:
        # 开发环境，使用当前目录
        return local_path


STYLES_FILE = get_resource_path('data/styles.json')
NAMES_FILE = get_resource_path('data/names_1.json')
SUMMARY_FILE = get_resource_path('data/summary.json')
LOCK_FILE = get_resource_path('data/.resource_lock')


class ResourceManager:
    """资源管理器（并发安全）"""

    def __init__(self):
        self.styles = self.load_styles()
        self.names = self.load_names()
        self.summary = self.load_summary()
        self._lock = threading.Lock()  # 内存锁

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

    def select_names(self, male_count=10, female_count=10):
        """从names_1.json中选择使用次数最少的人名（并发安全）

        Args:
            male_count: 需要的男性名字数量
            female_count: 需要的女性名字数量

        Returns:
            包含选中人名的字典 {'male': [...], 'female': [...]}
        """
        with self._lock:
            # 重新加载最新数据（防止其他进程修改）
            self.names = self.load_names()

            # 获取男性名字（按used排序）
            male_names = sorted(self.names['male'], key=lambda x: x['used'])
            selected_male = male_names[:male_count]

            # 获取女性名字（按used排序）
            female_names = sorted(self.names['female'], key=lambda x: x['used'])
            selected_female = female_names[:female_count]

            # 更新使用次数（标记为已预留）
            for name in selected_male:
                name['used'] += 1
            for name in selected_female:
                name['used'] += 1

            # 立即保存更新（锁定这些人名）
            self.save_names()

            return {
                'male': selected_male,
                'female': selected_female
            }

    def format_names_for_prompt(self, selected_names):
        """格式化人名列表为Prompt字符串

        Args:
            selected_names: select_names()的返回值

        Returns:
            格式化的字符串，例如 "Marcus Sterling, Alexander Cross, ..."
        """
        male_str = ", ".join([n['fullname'] for n in selected_names['male']])
        female_str = ", ".join([n['fullname'] for n in selected_names['female']])

        return {
            'male_names': male_str,
            'female_names': female_str
        }

    def select_style(self, genre):
        """获取类型的focus说明（新版本不再选择作者风格）

        Args:
            genre: 类型名称，如 'Romance', 'Horror'

        Returns:
            包含 genre_focus 的字典
            例如: {'genre_focus': 'Romantic chemistry drives everything...'}
        """
        if genre not in self.styles:
            raise ValueError(f"类型 '{genre}' 不存在")

        genre_data = self.styles[genre]

        # 新版本直接返回focus字段
        return {
            'genre_focus': genre_data.get('focus', '')
        }
