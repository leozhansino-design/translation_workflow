"""
翻译逻辑 - 负责实际的翻译工作
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, Any, Callable, Optional
import re
from path_utils import get_data_dir, get_output_dir


class Translator:
    def __init__(self, config_manager, resource_manager, output_dir: str = None):
        self.config_mgr = config_manager
        self.resource_mgr = resource_manager

        # 使用正确的路径（开发模式和打包模式都支持）
        if output_dir is None:
            output_dir = get_output_dir()
        self.output_dir = output_dir

        data_dir = get_data_dir()
        self.default_prompt_path = os.path.join(data_dir, "default_prompt.json")

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 确保data目录存在
        os.makedirs(data_dir, exist_ok=True)

    def load_default_prompt(self) -> str:
        """从JSON文件加载默认Prompt"""
        try:
            if os.path.exists(self.default_prompt_path):
                with open(self.default_prompt_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('base_prompt', self._get_fallback_prompt())
            else:
                # 如果文件不存在，返回默认prompt
                return self._get_fallback_prompt()
        except Exception as e:
            print(f"加载default_prompt.json失败: {str(e)}, 使用内置prompt")
            return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """备用的内置Prompt（防止JSON文件损坏）"""
        return """You are a native English webnovel author creating a viral, fully localized English novel from a Chinese source. Write for native English readers with natural pacing and style. DO NOT follow the original chapter structure—restructure freely for maximum impact. Each chapter must exceed 1000 words.

Provide a catchy Wattpad-style title, chapter titles, a blurb (under 3000 characters), and select the genre (Fantasy, Romance, Urban, Sci-Fi, Mystery, Horror, Adventure, Historical, Crime, LGBTQ+, Paranormal, System, Reborn, Revenge, Fanfiction). All character names must be creative and fully localized.

【TAGS REQUIREMENT - CRITICAL】
Based on the novel's content, generate 5-20 tags that describe the story.
- Tags must be SINGLE WORDS ONLY (no spaces allowed)
- Can use internet slang, memes, or trending terms
- Examples: #enemiestolovers #alphamale #reborn #revenge #billionaire #mafia #omegaverse #slowburn #powercouple #faceslapping #op-mc #cultivation #gamelit #isekai #transmigration #villainess #yandere #harem #obsession #toxic #greenflags #redflags
- Tags should capture: themes, tropes, character types, plot elements, vibes
- Format: Put tags at the VERY BEGINNING of output, separated by spaces

【LOCALIZATION REQUIREMENTS】

1. **Geography/Culture**: Set in non-Asian countries with appropriate place names, scenes, and customs matching the local culture.

2. **Character Names**:
   - MUST use full English names (firstname + lastname format, e.g., "Alexander Blake", "Isabella Rose")
   - Use full name on first mention, then firstname or nickname thereafter
   - NO Chinese names or pinyin
   - Ensure names don't repeat across different novels in this project
   - Maintain character relationships, personality traits, and nickname logic

3. **Daily Life Details**:
   - Food/drinks: Localize contextually (delivery → pizza/Chinese takeout, drinks → coffee/beer, etc.)
   - Social customs: Party styles, forms of address, holiday celebrations
   - Education: Adapt to local school systems (elementary/middle/high school/college)
   - Occupations: Keep original job types but use localized descriptions and industry terminology

4. **Language Style**:
   - Use authentic English colloquialisms, slang, and natural expressions
   - Avoid literal "Chinglish" translations
   - Preserve the original's narrative style, atmosphere, and emotional tension
   - Dialogue must fit character backgrounds and speech patterns
   - Use punchy, direct language for fast pacing
   - Include more ACTION and less introspection

5. **Cultural Element Adaptation** (adjust by genre):
   - Mythology/supernatural: Taoist/Buddhist elements → Christian/Norse mythology/Celtic folklore
   - Holidays: Spring Festival → Christmas/Thanksgiving, Mid-Autumn → Halloween
   - Currency: RMB → USD/GBP
   - Units: kilometers → miles, kilograms → pounds
   - Platforms: Weibo → Twitter/X, WeChat → WhatsApp/iMessage
   - Pop culture: Adapt to Western movies/music/internet memes familiar to American/European audiences

【PACING & STRUCTURE REQUIREMENTS】

6. **Fast-Paced "Satisfying Read" (爽文) Structure**:
   - EVERY chapter must have at least TWO major plot beats or reveals
   - Each chapter must END with a hook/cliffhanger to drive readers forward
   - Cut internal monologue by 50%—show through ACTION and DIALOGUE
   - Reduce flashbacks—use brief mentions or integrate into present action
   - Protagonist should be PROACTIVE, not just reactive
   - Include power reversals, unexpected twists, and "hell yeah" moments
   - Balance suffering with cathartic victories/revenge beats
   - Deliver emotional payoff FASTER—don't make readers wait too long

7. **Chapter Structure**:
   - Break long chapters (>3000 words) into multiple shorter chapters (1200-2000 words ideal for webnovel format)
   - Each chapter title should be punchy and intriguing (avoid "The [Noun]" format)
   - Chapter endings should make readers immediately want the next chapter

8. **Dialogue**:
   - Make dialogue snappier and more confrontational
   - Characters should have distinct voices
   - Use subtext and tension in conversations
   - Avoid overly polite or formal speech unless character-appropriate

9. **Atmospheric Horror/Thriller Enhancement** (if applicable):
   - Build environmental dread through specific sensory details
   - Create a sense of community complicity or conspiracy
   - Use small-town/isolated setting paranoia effectively
   - Blend mundane domesticity with creeping horror

【GOAL】
The final work must read as if originally written by a Western author, NOT translated literature. Readers should feel immersed in a story that belongs to their culture and storytelling tradition.

【FORMAT REQUIREMENTS】
- Preserve key narrative beats and plot twists
- Use webnovel paragraph spacing (blank line between each paragraph)
- Follow English punctuation conventions
- Avoid "The XXX" prepositional phrase chapter titles
- Overall: FAST pacing, TWISTS, maximum reader satisfaction (爽感)

【OUTPUT INSTRUCTIONS - CRITICAL】
DO NOT respond conversationally. DO NOT say "I will create..." or "Next I'll give you..." or ask for confirmation.

IMMEDIATELY output in this exact format:

Tags: #tag1 #tag2 #tag3 #tag4 #tag5 [continue with 5-20 total tags, single words only]

Title: [Your Wattpad-style title]
Genre: [Selected genre]

Blurb:
[Your blurb under 3000 characters]

---

Chapter 1: [Punchy chapter title]

[Full chapter text with blank lines between paragraphs, 1000+ words]

Chapter 2: [Punchy chapter title]

[Full chapter text with blank lines between paragraphs, 1000+ words]

[Continue with all chapters...]

START TRANSLATING NOW. Output the complete novel immediately."""

    def build_prompt(self, style: str, names: list) -> str:
        """构建翻译Prompt - English Version with Tags"""
        # 从JSON文件加载base prompt
        base = self.load_default_prompt()

        style_part = f"\n\n【WRITING STYLE TO EMULATE】\n{style}"

        # 使用fullname并明确标注firstname和lastname
        names_list = ", ".join([f"{n['fullname']} (first: {n['firstname']}, last: {n['lastname']})" for n in names])
        names_part = f"\n\n【AVAILABLE CHARACTER NAMES (Use Full Name Format)】\n{names_list}\n\nIMPORTANT: On first mention, use full name (e.g., Alexander Blake). Thereafter, use firstname (Alexander) or lastname (Blake) or nickname. Ensure no duplication with other novels in this project."

        return base + style_part + names_part

    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_result(self, title: str, content: str):
        """保存翻译结果到专属文件夹"""
        # 创建以原文件名命名的文件夹（去掉.txt后缀）
        folder_name = title.replace('.txt', '').replace('_translated', '')
        output_folder = os.path.join(self.output_dir, folder_name)
        os.makedirs(output_folder, exist_ok=True)

        # 在文件夹内保存翻译结果
        output_file = os.path.join(output_folder, f"{folder_name}_translated.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return output_file

    def extract_tags(self, content: str) -> list:
        """从翻译结果中提取Tags"""
        try:
            # 查找Tags行 (格式: Tags: #tag1 #tag2 #tag3...)
            match = re.search(r'^Tags:\s*(.+?)$', content, re.MULTILINE | re.IGNORECASE)
            if match:
                tags_line = match.group(1).strip()
                # 提取所有#开头的标签
                tags = re.findall(r'#(\w+)', tags_line)
                return tags if tags else []
            return []
        except Exception as e:
            print(f"提取Tags失败: {str(e)}")
            return []

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

            # 提取tags
            tags = self.extract_tags(translated)

            # 提取使用的人名并更新使用次数
            used_names = self.extract_used_names(translated, resource['names'])
            self.resource_mgr.update_name_usage(used_names)

            # 记录到summary (添加prompt和tags字段)
            record = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original": title,
                "translated": output_file,
                "genre": genre,
                "author_style": resource['author'],
                "names": used_names,
                "tags": tags,  # 添加tags字段
                "word_count": word_count,
                "time": round(duration, 2),
                "cost": round(cost, 2),
                "prompt": prompt  # 添加prompt字段
            }
            self.config_mgr.add_record(record)

            # 更新状态：完成（传递prompt）
            if status_callback:
                status_callback(title, "完成", duration, cost, prompt)

            return {
                'success': True,
                'title': title,
                'translated_file': output_file,
                'duration': duration,
                'cost': cost,
                'prompt': prompt,  # 返回prompt
                'tags': tags  # 返回tags
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
