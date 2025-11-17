"""
简化版翻译模块 - 快速流式翻译
"""
import os
import time
import json
import random
import threading
from openai import OpenAI


class Translator:
    """翻译器 - 简化版本"""

    # 类级别的锁,用于保护names数据库的读写
    _names_lock = threading.Lock()

    def __init__(self, api_key, base_url, model, max_tokens=100000):
        """
        初始化翻译器

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            max_tokens: 最大token数量
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.client = None

        # 获取脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.script_dir, "data")

    def initialize_client(self):
        """初始化OpenAI客户端"""
        if not self.client:
            # 设置更长的超时时间(3600秒=1小时)
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=3600.0
            )

    def test_connection(self):
        """测试API连接"""
        try:
            self.initialize_client()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello!"}],
                max_tokens=50
            )
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def load_prompt_template(self):
        """加载prompt模板"""
        template_path = os.path.join(self.data_dir, "default_prompt.txt")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "You are a professional translator. Translate the following text to English."

    def save_prompt_template(self, content):
        """保存prompt模板"""
        template_path = os.path.join(self.data_dir, "default_prompt.txt")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def load_styles(self):
        """加载作家风格库"""
        styles_path = os.path.join(self.data_dir, "styles.json")
        if os.path.exists(styles_path):
            with open(styles_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def get_random_author_style(self, genre):
        """
        随机选择作家风格

        Args:
            genre: 小说类型

        Returns:
            选中的风格描述文本
        """
        styles_data = self.load_styles()

        # 如果没有对应genre的风格，返回空字符串
        if genre not in styles_data:
            return ""

        genre_data = styles_data[genre]
        styles = genre_data.get("styles", [])

        if not styles:
            return ""

        # 随机选择一个风格
        return random.choice(styles)

    def load_names_database(self, db_number):
        """
        加载人名库

        Args:
            db_number: 1, 2, 或 3

        Returns:
            包含male和female列表的字典
        """
        db_path = os.path.join(self.data_dir, f"names_{db_number}.json")
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"male": [], "female": []}

    def save_names_database(self, db_number, names_db):
        """
        保存人名库

        Args:
            db_number: 1, 2, 或 3
            names_db: 人名库字典
        """
        db_path = os.path.join(self.data_dir, f"names_{db_number}.json")
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(names_db, f, ensure_ascii=False, indent=2)

    def allocate_names(self, names_db, db_number, count=20):
        """
        从人名库中分配人名(选择使用次数最少的名字)

        Args:
            names_db: 人名库字典
            db_number: 数据库编号(用于保存更新)
            count: 要分配的名字数量

        Returns:
            分配的名字列表（字符串列表）
        """
        # 使用类级别的锁来确保线程安全
        with Translator._names_lock:
            male_names = names_db.get("male", [])
            female_names = names_db.get("female", [])

            # 简单分配：男女各一半
            male_count = count // 2
            female_count = count - male_count

            allocated = []

            # 为男性名字按used字段排序,选择使用最少的
            if len(male_names) >= male_count:
                # 排序:按used字段升序
                sorted_male = sorted(male_names, key=lambda x: x.get("used", 0) if isinstance(x, dict) else 0)

                for i in range(male_count):
                    name_obj = sorted_male[i]
                    if isinstance(name_obj, dict):
                        allocated.append(name_obj.get("fullname", ""))
                        # 更新used计数
                        name_obj["used"] = name_obj.get("used", 0) + 1
                    else:
                        allocated.append(str(name_obj))

            # 为女性名字按used字段排序,选择使用最少的
            if len(female_names) >= female_count:
                # 排序:按used字段升序
                sorted_female = sorted(female_names, key=lambda x: x.get("used", 0) if isinstance(x, dict) else 0)

                for i in range(female_count):
                    name_obj = sorted_female[i]
                    if isinstance(name_obj, dict):
                        allocated.append(name_obj.get("fullname", ""))
                        # 更新used计数
                        name_obj["used"] = name_obj.get("used", 0) + 1
                    else:
                        allocated.append(str(name_obj))

            # 保存更新后的names数据库
            self.save_names_database(db_number, names_db)

            return allocated

    def build_translation_prompt(self, prompt_template, genre, names=None, author_style=None):
        """
        构建翻译提示词

        Args:
            prompt_template: prompt模板
            genre: 小说类型
            names: 分配的人名列表（可选）
            author_style: 作家风格描述（可选）

        Returns:
            完整的prompt
        """
        # 基础prompt
        full_prompt = prompt_template

        # 添加作家风格（在人名之前）
        if author_style:
            full_prompt += f"\n\n【AUTHOR STYLE】\n{author_style}"

        # 如果有人名，添加人名列表
        if names and len(names) > 0:
            names_text = ", ".join(names)
            full_prompt += f"\n\n【AVAILABLE CHARACTER NAMES】\nUse these names for characters: {names_text}\nThese names are pre-allocated and ensure no repetition across novels."

        # 添加genre信息
        full_prompt += f"\n\n【TARGET GENRE】\n{genre}"

        return full_prompt

    def read_novel_file(self, file_path):
        """读取小说文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def translate_novel(self, file_path, genre, names_db_num, progress_callback=None):
        """
        翻译小说

        Args:
            file_path: 文件路径
            genre: 小说类型
            names_db_num: 人名库编号（1/2/3）
            progress_callback: 进度回调函数(status_message)

        Returns:
            结果字典 {success, output_folder, duration, error}
        """
        start_time = time.time()
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]

        try:
            # 初始化客户端
            self.initialize_client()

            if progress_callback:
                progress_callback(f"📖 正在读取文件: {filename}")

            # 读取小说内容
            novel_content = self.read_novel_file(file_path)

            if progress_callback:
                progress_callback(f"📝 生成Unique prompt中...")

            # 加载人名库并分配人名(选择使用次数最少的)
            names_db = self.load_names_database(names_db_num)
            allocated_names = self.allocate_names(names_db, names_db_num, count=20)

            if progress_callback:
                progress_callback(f"✍️ 正在构建提示词...")

            # 加载prompt模板
            prompt_template = self.load_prompt_template()

            # 随机选择作家风格
            author_style = self.get_random_author_style(genre)

            # 构建完整prompt
            full_prompt = self.build_translation_prompt(
                prompt_template,
                genre,
                allocated_names,
                author_style
            )

            if progress_callback:
                progress_callback(f"🚀 正在发送翻译请求...")

            # 使用流式API进行翻译,避免长时间等待
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": novel_content}
                ],
                temperature=0.7,
                max_tokens=self.max_tokens,
                stream=True
            )

            if progress_callback:
                progress_callback(f"📥 正在接收翻译结果...")

            # 获取流式翻译结果
            translated_content = ""
            total_tokens = 0

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        translated_content += delta.content

                # 更新token统计(如果有)
                if hasattr(chunk, 'usage') and chunk.usage:
                    total_tokens = chunk.usage.total_tokens

            if progress_callback:
                progress_callback(f"💾 正在保存结果...")

            # 创建输出文件夹（使用绝对路径）
            output_base = os.path.join(self.script_dir, "output")
            output_folder = os.path.join(output_base, filename_no_ext)
            os.makedirs(output_folder, exist_ok=True)

            # 保存到content.txt
            output_file = os.path.join(output_folder, "content.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_content)

            duration = time.time() - start_time

            if progress_callback:
                progress_callback(f"✅ 翻译完成！用时 {duration:.1f}秒")

            # 如果没有获取到token统计,使用估算值
            if total_tokens == 0:
                total_tokens = len(novel_content) + len(translated_content)

            return {
                'success': True,
                'output_folder': output_folder,
                'duration': duration,
                'tokens': total_tokens,
                'filename': filename
            }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            if progress_callback:
                progress_callback(f"❌ 翻译失败: {error_msg}")

            return {
                'success': False,
                'error': error_msg,
                'duration': duration,
                'filename': filename
            }

    def extract_genre_from_filename(self, filename):
        """
        从文件名提取genre

        Args:
            filename: 文件名，例如 "76死亡运动会_Horror.txt"

        Returns:
            genre字符串，如果未找到则返回"Fantasy"
        """
        valid_genres = [
            "Fantasy", "Urban", "Romance", "Sci-Fi", "Mystery",
            "Action", "Adventure", "Horror", "Crime", "LGBTQ+",
            "Paranormal", "System", "Reborn", "Revenge", "Fanfiction"
        ]

        # 查找文件名中的genre
        for genre in valid_genres:
            if f"_{genre}" in filename:
                return genre

        # 默认返回Fantasy
        return "Fantasy"

    def estimate_cost(self, file_path):
        """
        估算翻译费用

        Args:
            file_path: 文件路径

        Returns:
            估算字符数
        """
        try:
            content = self.read_novel_file(file_path)
            return len(content)
        except:
            return 0
