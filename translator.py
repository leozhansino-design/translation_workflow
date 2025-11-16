"""
翻译逻辑模块
"""
import os
import time
from openai import OpenAI
from config import config
from resource_mgr import ResourceManager


class Translator:
    """翻译器"""

    def __init__(self):
        self.config = config
        self.resource_mgr = ResourceManager()
        self.client = None

    def initialize_client(self):
        """初始化OpenAI客户端"""
        api_key = self.config.get_api_key()
        if not api_key:
            raise ValueError("API Key 未设置")
        self.client = OpenAI(api_key=api_key)

    def test_connection(self):
        """测试API连接"""
        try:
            self.initialize_client()
            # 发送一个简单的测试请求
            response = self.client.chat.completions.create(
                model=self.config.get_model(),
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10
            )
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def build_prompt(self, style, names, genre):
        """构建翻译提示词

        Args:
            style: 写作风格描述
            names: 可用人名列表
            genre: 小说类型

        Returns:
            完整的提示词
        """
        base = """你是一个英语母语网文创作者，将附件中的故事翻译成一篇爆款本土化英文小说。符合英语母语读者的阅读习惯，不用按照原来的章节，保持每个章节大于1000词，可以更改原来的章节结构。

起一个wattpad网文标题，起各个章节的标题，写它的blurb(小于3000characters)，选择它的类型（Fantasy,Romance,Urban,Sci-Fi,Mystery, Horror,Adventure,Historical,Crime,LGBTQ+,Paranormal,System,Reborn,Revenge,Fanfiction）角色名字要有新意本土化

【翻译本土化要求】
1. **地理/文化背景**：改为非亚洲国家背景，地名、场景、文化习俗要符合当地
2. **人名**：改为常见英文名也可以是欧洲/拉丁裔/南美洲名字，避免中文和拼音，检索project不要和其他小说里的人名重复，保持角色关系、性格特征和昵称逻辑
3. **日常细节**：食物/饮品（根据场景本土化：外卖→披萨/中餐外卖，饮料→咖啡/啤酒等）- 社交习惯（聚会方式、称呼、节日庆祝等）- 教育体系（小学/初中/高中/大学对应当地学制）- 职业设定（保持原有职业类型，但用本地化描述和行业术语）
4. **语言风格**：使用地道的英语口语、俚语和习惯表达 - 避免直译式的中式英语表达 - 保持原作的叙事风格、氛围和情感张力 - 对话要符合角色背景和说话习惯
5. **文化元素适配**（根据题材调整）：神话/超自然：道教/佛教元素→基督教/北欧神话/凯尔特民间传说等 - 节日：春节→圣诞节/感恩节，中秋节→万圣节等 - 货币单位：人民币→美元/英镑 - 计量单位：公里→英里，公斤→磅等 - 网络平台：微博→Twitter/X，微信→WhatsApp/iMessage等 - 流行文化梗：改为欧美观众熟悉的电影/音乐/网络梗

【目标】翻译后的作品应该让英语母语读者感觉这是由英语国家作者创作的原创作品，而不是翻译文学。

【格式要求】保留重要的叙事节奏和情节转折; 输出的正文要每一段文字空一行的那种网文格式; 符合英文的标点符号；章节标题不要用the XXX 的宾语短语、介词短语格式；整体剧情节奏快、有反转、让读者感觉爽"""

        style_part = f"\n\n【写作风格】\n{style}"

        names_list = ", ".join([n['name'] for n in names])
        names_part = f"\n\n【可用角色名】\n{names_list}\n优先使用这些名字，确保不与其他小说重复。"

        genre_part = f"\n\n【小说类型】\n{genre}"

        return base + style_part + names_part + genre_part

    def read_file(self, file_path):
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def calculate_cost(self, usage):
        """计算API调用费用

        Args:
            usage: API返回的usage对象

        Returns:
            费用（美元）
        """
        # GPT-4 Turbo 定价（示例，实际请根据OpenAI定价调整）
        # Input: $0.01 per 1K tokens
        # Output: $0.03 per 1K tokens
        input_cost = (usage.prompt_tokens / 1000) * 0.01
        output_cost = (usage.completion_tokens / 1000) * 0.03
        return input_cost + output_cost

    def estimate_word_count(self, file_path):
        """估算文件字数"""
        try:
            content = self.read_file(file_path)
            # 简单估算：统计字符数
            return len(content)
        except Exception:
            return 0

    def estimate_cost(self, file_path):
        """估算翻译费用

        Args:
            file_path: 文件路径

        Returns:
            估算费用（美元）
        """
        word_count = self.estimate_word_count(file_path)
        # 粗略估算：每1000字符约$0.02
        return (word_count / 1000) * 0.02

    def save_result(self, title, translated_content, genre):
        """保存翻译结果

        Args:
            title: 原始书名
            translated_content: 翻译后的内容
            genre: 小说类型
        """
        os.makedirs('output', exist_ok=True)

        # 生成输出文件名
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        output_file = f'output/{safe_title}_{genre}_translated.txt'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        return output_file

    def translate_novel(self, file_path, resource, progress_callback=None):
        """翻译单本小说

        Args:
            file_path: 文件路径
            resource: 分配的资源（style, names, author, genre）
            progress_callback: 进度回调函数 (title, status, elapsed_time, cost)

        Returns:
            包含结果信息的字典
        """
        title = self.resource_mgr.extract_title(file_path)
        genre = resource['genre']

        # 初始化客户端
        if not self.client:
            self.initialize_client()

        # 开始计时
        start_time = time.time()

        try:
            # 读取文件内容
            content = self.read_file(file_path)

            # 构建提示词
            prompt = self.build_prompt(
                resource['style'],
                resource['names'],
                genre
            )

            # 调用API（阻塞等待）
            if progress_callback:
                progress_callback(title, "翻译中", time.time() - start_time, None)

            response = self.client.chat.completions.create(
                model=self.config.get_model(),
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                temperature=self.config.get_temperature(),
                max_tokens=self.config.get_max_tokens()
            )

            # 计算耗时和费用
            duration = time.time() - start_time
            translated = response.choices[0].message.content
            cost = self.calculate_cost(response.usage)

            # 保存结果
            output_file = self.save_result(title, translated, genre)

            # 更新人名使用次数
            self.resource_mgr.update_name_usage(resource['names'], translated)

            # 提取使用的人名
            used_names = [n['name'] for n in resource['names'] if n['name'] in translated]

            # 记录到summary
            self.resource_mgr.add_to_summary({
                'original': title,
                'translated': output_file,
                'genre': genre,
                'author_style': resource['author'],
                'names': used_names,
                'time': int(duration),
                'cost': round(cost, 2)
            })

            # 最终状态更新
            if progress_callback:
                progress_callback(title, "完成", duration, cost)

            return {
                'success': True,
                'title': title,
                'output_file': output_file,
                'duration': duration,
                'cost': cost,
                'genre': genre
            }

        except Exception as e:
            duration = time.time() - start_time
            if progress_callback:
                progress_callback(title, f"失败: {str(e)}", duration, None)

            return {
                'success': False,
                'title': title,
                'error': str(e),
                'duration': duration,
                'genre': genre
            }
