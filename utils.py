"""
工具函数模块
"""
import os
import re
import json
import http.client
from datetime import datetime


def extract_genre_from_filename(filename):
    """从文件名提取类型

    Args:
        filename: 文件名，格式为 [书名]_[类型].txt

    Returns:
        类型字符串，如 'Romance', 'Fantasy'
        自动处理大小写，将首字母大写

    Raises:
        ValueError: 如果文件名格式不正确
    """
    basename = os.path.basename(filename)
    match = re.search(r'_([A-Za-z+\-]+)\.txt$', basename, re.IGNORECASE)

    if match:
        genre = match.group(1)
        # 首字母大写处理，支持LGBTQ+这种特殊情况
        if genre.upper() == 'LGBTQ+':
            return 'LGBTQ+'
        elif genre.lower() in ['sci-fi', 'scifi']:
            return 'Sci-Fi'
        else:
            # 普通类型首字母大写
            return genre.capitalize()
    else:
        raise ValueError(
            f"无效的文件名格式: {basename}\n"
            f"正确格式: [书名]_[类型].txt\n"
            f"例如: 霸道总裁_Romance.txt 或 霸道总裁_romance.txt"
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

    # 查找所有chapter_*.txt文件（支持 chapter_1.txt 和 chapter_1_Title.txt 格式）
    # 但排除大纲文件 chapter_X_prompt.txt
    for filename in os.listdir(project_folder):
        # 排除大纲文件
        if '_prompt.txt' in filename:
            continue

        match = re.match(r'chapter_(\d+)(?:_.*)?\.txt$', filename)
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


def save_chapter_file(project_folder, chapter_num, content, metadata=None, title=None):
    """保存章节文件

    Args:
        project_folder: 项目文件夹路径
        chapter_num: 章节号
        content: 章节内容
        metadata: 可选的元数据字典
        title: 章节标题（用于文件名）
    """
    os.makedirs(project_folder, exist_ok=True)

    # 如果有title，使用 chapter_1_Title.txt 格式
    # 清理title中的特殊字符，只保留字母数字和空格
    if title:
        safe_title = "".join(c if c.isalnum() or c.isspace() else "_" for c in title)
        safe_title = safe_title.strip().replace(" ", "_")
        # 限制长度避免文件名过长
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        filename = f'chapter_{chapter_num}_{safe_title}.txt'
    else:
        filename = f'chapter_{chapter_num}.txt'

    filepath = os.path.join(project_folder, filename)

    # 只保存纯正文，不添加任何metadata
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # metadata信息只在console显示，不写入文件
    print(f"  💾 章节已保存: {filename}")
    if metadata:
        print(f"  📊 元数据: {metadata}")
    else:
        print(f"  📊 字符数: {len(content)}")


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


def call_api_with_http_client(api_key, base_url, model, messages, temperature=0.8, max_tokens=8000):
    """使用http.client调用API（支持Gemini和GPT模型）

    完全按照标准http.client方式调用，适用于所有兼容OpenAI格式的API。

    Args:
        api_key: API密钥
        base_url: API基础URL（如 "https://yunwuapi.com" 或 "https://yunwuapi.com/v1/"）
        model: 模型名称
        messages: 消息列表 [{"role": "system/user", "content": "..."}]
        temperature: 温度参数
        max_tokens: 最大token数

    Returns:
        {
            'success': True/False,
            'content': 响应内容（成功时）,
            'usage': token使用统计（成功时）,
            'error': 错误信息（失败时）,
            'details': 详细信息（失败时）
        }
    """
    # 合并system和user消息为一条user消息（Gemini等模型要求）
    combined_content = ""
    for msg in messages:
        if msg['role'] == 'system':
            combined_content += msg['content'] + "\n\n"
        elif msg['role'] == 'user':
            combined_content += msg['content']

    # 准备请求数据
    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": combined_content
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # 解析URL - 去掉协议头
    host = base_url.replace("https://", "").replace("http://", "").rstrip('/')
    # 如果URL中包含路径，分离出来
    if '/' in host:
        host = host.split('/')[0]

    conn = None
    try:
        # 设置连接（不设置timeout，和成功的Gemini测试代码一样）
        conn = http.client.HTTPSConnection(host)

        # 发送请求
        conn.request("POST", "/v1/chat/completions", payload, headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')

        # 解析并返回结果
        if response.status == 200:
            response_data = json.loads(data)
            content = response_data['choices'][0]['message']['content']
            usage = response_data.get('usage', {})

            return {
                'success': True,
                'content': content,
                'usage': usage
            }
        else:
            return {
                'success': False,
                'error': f"请求失败，状态码：{response.status}",
                'details': data
            }

    except Exception as e:
        return {
            'success': False,
            'error': f'发生错误：{e}',
            'details': str(type(e).__name__)
        }

    finally:
        if conn:
            conn.close()
