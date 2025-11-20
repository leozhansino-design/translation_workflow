"""
工具函数模块
"""
import os
import re
import json
from datetime import datetime


def extract_genre_from_filename(filename):
    """从文件名提取类型

    Args:
        filename: 文件名，格式为 [书名]_[类型].txt

    Returns:
        类型字符串，如 'Romance', 'Fantasy'

    Raises:
        ValueError: 如果文件名格式不正确
    """
    basename = os.path.basename(filename)
    match = re.search(r'_([A-Za-z+\-]+)\.txt$', basename)

    if match:
        genre = match.group(1)
        return genre
    else:
        raise ValueError(
            f"无效的文件名格式: {basename}\n"
            f"正确格式: [书名]_[类型].txt\n"
            f"例如: 霸道总裁_Romance.txt"
        )


def extract_title_from_filename(filename):
    """从文件名提取书名

    Args:
        filename: 文件名，格式为 [书名]_[类型].txt

    Returns:
        书名字符串
    """
    basename = os.path.basename(filename)
    match = re.match(r'(.+?)_[A-Za-z+\-]+\.txt$', basename)

    if match:
        return match.group(1)
    else:
        # 如果没有匹配，返回不带扩展名的文件名
        return os.path.splitext(basename)[0]


def validate_genre(genre, available_genres):
    """验证类型是否在可用列表中

    Args:
        genre: 要验证的类型
        available_genres: 可用类型列表

    Returns:
        布尔值，True表示有效

    Raises:
        ValueError: 如果类型无效
    """
    if genre not in available_genres:
        raise ValueError(
            f"类型 '{genre}' 不存在\n"
            f"可用类型: {', '.join(available_genres)}"
        )
    return True


def validate_chapter_length(content, min_chars=9000, max_chars=30000):
    """验证章节长度是否在指定范围内

    Args:
        content: 章节内容
        min_chars: 最小字符数（默认9000）
        max_chars: 最大字符数（默认30000）

    Returns:
        (is_valid, char_count, message)
    """
    char_count = len(content)

    if char_count < min_chars:
        return False, char_count, f"字符数太少: {char_count} < {min_chars}"
    elif char_count > max_chars:
        return False, char_count, f"字符数太多: {char_count} > {max_chars}"
    else:
        return True, char_count, f"合格: {char_count} 字符"


def scan_chapter_files(project_folder):
    """扫描项目文件夹中的章节文件

    Args:
        project_folder: 项目文件夹路径

    Returns:
        {
            'max_chapter': 最大章节号,
            'chapter_files': [文件路径列表],
            'missing_chapters': [缺失的章节号]
        }
    """
    if not os.path.exists(project_folder):
        return {'max_chapter': 0, 'chapter_files': [], 'missing_chapters': []}

    chapter_files = []
    chapter_numbers = []

    # 查找所有ch*.txt文件
    for filename in os.listdir(project_folder):
        match = re.match(r'ch(\d+)\.txt$', filename)
        if match:
            chapter_num = int(match.group(1))
            chapter_numbers.append(chapter_num)
            chapter_files.append(os.path.join(project_folder, filename))

    if not chapter_numbers:
        return {'max_chapter': 0, 'chapter_files': [], 'missing_chapters': []}

    max_chapter = max(chapter_numbers)
    chapter_numbers_set = set(chapter_numbers)

    # 查找缺失的章节
    missing_chapters = [i for i in range(1, max_chapter + 1) if i not in chapter_numbers_set]

    return {
        'max_chapter': max_chapter,
        'chapter_files': sorted(chapter_files),
        'missing_chapters': missing_chapters
    }


def load_chapter_content(chapter_file):
    """加载章节文件内容

    Args:
        chapter_file: 章节文件路径

    Returns:
        章节内容字符串
    """
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除末尾的元数据（---之后的内容）
    if '---' in content:
        content = content.split('---')[0].strip()

    return content


def save_chapter_file(project_folder, chapter_num, content, metadata=None):
    """保存章节文件

    Args:
        project_folder: 项目文件夹路径
        chapter_num: 章节号
        content: 章节内容
        metadata: 可选的元数据字典
    """
    os.makedirs(project_folder, exist_ok=True)

    filename = f'ch{chapter_num}.txt'
    filepath = os.path.join(project_folder, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        f.write('\n\n---\n')

        # 写入元数据
        if metadata:
            for key, value in metadata.items():
                f.write(f'{key}: {value}\n')
        else:
            # 默认元数据
            f.write(f'Character Count: {len(content)}\n')
            f.write(f'Generated At: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}\n')


def parse_json_from_llm_response(response_text):
    """从LLM响应中解析JSON

    处理可能包含markdown代码块的响应

    Args:
        response_text: LLM返回的文本

    Returns:
        解析后的JSON对象

    Raises:
        json.JSONDecodeError: 如果无法解析
    """
    # 移除可能的markdown代码块标记
    text = response_text.strip()

    # 检查是否有```json ... ```格式
    if text.startswith('```'):
        # 找到第一个{和最后一个}
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1:
            text = text[start_idx:end_idx + 1]

    # 解析JSON
    return json.loads(text)


def format_time_elapsed(seconds):
    """格式化时间

    Args:
        seconds: 秒数

    Returns:
        格式化的字符串，如 "2小时15分30秒"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"


def create_project_folder(title, genre):
    """创建项目文件夹

    Args:
        title: 书名
        genre: 类型

    Returns:
        项目文件夹路径
    """
    # 生成安全的文件夹名
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    safe_title = safe_title.replace(' ', '_')

    # 添加时间戳确保唯一性
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    folder_name = f"ProjectFolder_{safe_title}_{genre}_{timestamp}"
    folder_path = os.path.join('projects', folder_name)

    os.makedirs(folder_path, exist_ok=True)

    return folder_path


def save_project_metadata(project_folder, metadata):
    """保存项目元数据文件

    Args:
        project_folder: 项目文件夹路径
        metadata: 元数据字典
    """
    # 保存各个独立文件
    if 'title' in metadata:
        with open(os.path.join(project_folder, 'title.txt'), 'w', encoding='utf-8') as f:
            f.write(metadata['title'])

    if 'blurb' in metadata:
        with open(os.path.join(project_folder, 'blurb.txt'), 'w', encoding='utf-8') as f:
            f.write(metadata['blurb'])

    if 'age_category' in metadata:
        with open(os.path.join(project_folder, 'age.txt'), 'w', encoding='utf-8') as f:
            f.write(metadata['age_category'])

    if 'tags' in metadata:
        with open(os.path.join(project_folder, 'tags.txt'), 'w', encoding='utf-8') as f:
            # tags是列表，每行一个
            if isinstance(metadata['tags'], list):
                f.write('\n'.join(metadata['tags']))
            else:
                f.write(metadata['tags'])

    if 'genre' in metadata:
        with open(os.path.join(project_folder, 'category.txt'), 'w', encoding='utf-8') as f:
            f.write(metadata['genre'])


def load_project_metadata(project_folder):
    """加载项目元数据

    Args:
        project_folder: 项目文件夹路径

    Returns:
        元数据字典
    """
    metadata = {}

    title_file = os.path.join(project_folder, 'title.txt')
    if os.path.exists(title_file):
        with open(title_file, 'r', encoding='utf-8') as f:
            metadata['title'] = f.read().strip()

    blurb_file = os.path.join(project_folder, 'blurb.txt')
    if os.path.exists(blurb_file):
        with open(blurb_file, 'r', encoding='utf-8') as f:
            metadata['blurb'] = f.read().strip()

    age_file = os.path.join(project_folder, 'age.txt')
    if os.path.exists(age_file):
        with open(age_file, 'r', encoding='utf-8') as f:
            metadata['age_category'] = f.read().strip()

    tags_file = os.path.join(project_folder, 'tags.txt')
    if os.path.exists(tags_file):
        with open(tags_file, 'r', encoding='utf-8') as f:
            metadata['tags'] = f.read().strip().split('\n')

    category_file = os.path.join(project_folder, 'category.txt')
    if os.path.exists(category_file):
        with open(category_file, 'r', encoding='utf-8') as f:
            metadata['genre'] = f.read().strip()

    return metadata
