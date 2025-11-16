"""
翻译逻辑 - 负责实际的翻译工作
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import re


class Translator:
    def __init__(self, config_manager, resource_manager, output_dir: str = "output"):
        self.config_mgr = config_manager
        self.resource_mgr = resource_manager
        self.output_dir = output_dir

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def build_prompt(self, style: str, names: list) -> str:
        """构建翻译Prompt"""
        base = """你是一个英语母语网文创作者，将附件中的故事翻译成一篇爆款本土化英文小说。符合英语母语读者的阅读习惯，不用按照原来的章节,保持每个章节大于1000词，可以更改原来的章节结构。

起一个wattpad网文标题，起各个章节的标题，写它的blurb(小于3000characters)，选择它的类型（Fantasy,Romance,Urban,Sci-Fi,Mystery, Horror,Adventure,Historical,Crime,LGBTQ+,Paranormal,System,Reborn,Revenge,Fanfiction）角色名字要有新意本土化

【翻译本土化要求】
1. **地理/文化背景**：改为非亚洲国家背景，地名、场景、文化习俗要符合当地
2. **人名**：必须使用完整的英文名字（firstname + lastname格式，如 "Alexander Blake", "Isabella Rose"），不能只用firstname。避免中文和拼音，检索project不要和其他小说里的人名重复，保持角色关系、性格特征和昵称逻辑。首次出现时使用全名，之后可以用firstname或昵称。
3. **日常细节**：食物/饮品（根据场景本土化：外卖→披萨/中餐外卖，饮料→咖啡/啤酒等）- 社交习惯（聚会方式、称呼、节日庆祝等）- 教育体系（小学/初中/高中/大学对应当地学制）- 职业设定（保持原有职业类型，但用本地化描述和行业术语）
4. **语言风格**：使用地道的英语口语、俚语和习惯表达 - 避免直译式的中式英语表达 - 保持原作的叙事风格、氛围和情感张力 - 对话要符合角色背景和说话习惯
5. **文化元素适配**（根据题材调整）：神话/超自然：道教/佛教元素→基督教/北欧神话/凯尔特民间传说等 - 节日：春节→圣诞节/感恩节，中秋节→万圣节等 - 货币单位：人民币→美元/英镑 - 计量单位：公里→英里，公斤→磅等 - 网络平台：微博→Twitter/X，微信→WhatsApp/iMessage等 - 流行文化梗：改为欧美观众熟悉的电影/音乐/网络梗

【目标】翻译后的作品应该让英语母语读者感觉这是由英语国家作者创作的原创作品，而不是翻译文学。

【格式要求】保留重要的叙事节奏和情节转折; 输出的正文要每一段文字空一行的那种网文格式; 符合英文的标点符号；章节标题不要用the XXX 的宾语短语、介词短语格式；整体剧情节奏快、有反转、让读者感觉爽"""

        style_part = f"\n\n【写作风格】\n{style}"

        # 使用fullname并明确标注firstname和lastname
        names_list = ", ".join([f"{n['fullname']} (first: {n['firstname']}, last: {n['lastname']})" for n in names])
        names_part = f"\n\n【可用角色名（必须使用Full Name格式）】\n{names_list}\n\n重要：首次介绍角色时必须使用完整全名（如 Alexander Blake），之后可以用firstname（Alexander）或lastname（Blake）或昵称。确保不与其他小说重复。"

        return base + style_part + names_part

    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_result(self, title: str, content: str):
        """保存翻译结果"""
        output_file = os.path.join(self.output_dir, f"{title}_translated.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_file

    def extract_used_names(self, content: str, available_names: list) -> list:
        """从翻译结果中提取实际使用的人名（全名格式）"""
        used_names = []

        for name_obj in available_names:
            fullname = name_obj['fullname']
            firstname = name_obj['firstname']
            lastname = name_obj['lastname']

            # 检查全名、firstname或lastname是否出现
            pattern_full = r'\b' + re.escape(fullname) + r'\b'
            pattern_first = r'\b' + re.escape(firstname) + r'\b'
            pattern_last = r'\b' + re.escape(lastname) + r'\b'

            if (re.search(pattern_full, content, re.IGNORECASE) or
                re.search(pattern_first, content, re.IGNORECASE) or
                re.search(pattern_last, content, re.IGNORECASE)):
                used_names.append(fullname)

        return used_names

    def count_words(self, content: str) -> int:
        """统计字数（中文字符数）"""
        # 移除空白字符
        content = re.sub(r'\s+', '', content)
        return len(content)

    def translate_one(
        self,
        file_path: str,
        resource: Dict[str, Any],
        status_callback: Optional[Callable] = None,
        api_caller: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        翻译单个文件

        Args:
            file_path: 文件路径
            resource: 分配的资源 {style, names, genre, author}
            status_callback: 状态更新回调函数 callback(title, status, elapsed, cost)
            api_caller: API调用函数 caller(prompt, content) -> (translated, input_tokens, output_tokens)

        Returns:
            {
                'success': bool,
                'title': str,
                'translated_file': str,
                'duration': float,
                'cost': float,
                'error': str (if failed)
            }
        """
        title = self.resource_mgr.extract_title(file_path)
        genre = resource['genre']
        start_time = time.time()

        try:
            # 读取文件
            content = self.read_file(file_path)
            word_count = self.count_words(content)

            # 构建Prompt
            prompt = self.build_prompt(resource['style'], resource['names'])

            # 更新状态：运行中
            if status_callback:
                status_callback(title, "运行中", 0, 0)

            # 调用API
            if api_caller is None:
                raise Exception("API caller not provided")

            translated, input_tokens, output_tokens = api_caller(prompt, content)

            # 计算成本和耗时
            duration = time.time() - start_time
            cost = self.config_mgr.calculate_cost(input_tokens, output_tokens)

            # 保存结果
            output_file = self.save_result(title, translated)

            # 提取使用的人名并更新使用次数
            used_names = self.extract_used_names(translated, resource['names'])
            self.resource_mgr.update_name_usage(used_names)

            # 记录到summary
            record = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original": title,
                "translated": output_file,
                "genre": genre,
                "author_style": resource['author'],
                "names": used_names,
                "word_count": word_count,
                "time": round(duration, 2),
                "cost": round(cost, 2)
            }
            self.config_mgr.add_record(record)

            # 更新状态：完成
            if status_callback:
                status_callback(title, "完成", duration, cost)

            return {
                'success': True,
                'title': title,
                'translated_file': output_file,
                'duration': duration,
                'cost': cost
            }

        except Exception as e:
            duration = time.time() - start_time

            # 更新状态：失败
            if status_callback:
                status_callback(title, f"失败: {str(e)}", duration, 0)

            return {
                'success': False,
                'title': title,
                'duration': duration,
                'error': str(e)
            }

    def test_api_connection(self, api_caller: Callable) -> Dict[str, Any]:
        """
        测试API连接

        Args:
            api_caller: API调用函数

        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # 简单的测试调用
            test_prompt = "You are a helpful assistant."
            test_content = "Hello, this is a test."

            result = api_caller(test_prompt, test_content)

            if result and len(result) == 3:
                return {
                    'success': True,
                    'message': '✅ API连接成功'
                }
            else:
                return {
                    'success': False,
                    'message': '❌ API返回格式错误'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'❌ API连接失败: {str(e)}'
            }
