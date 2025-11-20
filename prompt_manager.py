"""
Prompt管理系统
支持查看、编辑、保存Prompt模板
"""
import json
import os
import sys
from datetime import datetime


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）

    优先使用当前目录的文件，如果不存在则从打包资源复制
    """
    local_path = os.path.join(os.getcwd(), relative_path)

    if os.path.exists(local_path):
        return local_path

    try:
        base_path = sys._MEIPASS
        bundled_path = os.path.join(base_path, relative_path)

        if relative_path.startswith('data/') and os.path.exists(bundled_path):
            os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)
            import shutil
            try:
                shutil.copy2(bundled_path, local_path)
            except:
                pass

        return local_path

    except AttributeError:
        return local_path


PROMPTS_FILE = get_resource_path('data/prompts.json')


# 默认Prompt模板
DEFAULT_OUTLINE_PROMPT = """你是一个英语母语网文创作者，将附件中的故事改编成一篇爆款本土化英文小说大纲。符合英语母语读者的阅读习惯。

【核心任务】
起一个 Wattpad 网文标题，写 blurb（简介，少于 3000 characters），选择类型和 tags（最多 20 个），构建完整的世界观、角色表和详细的章节大纲。

【翻译本土化要求】
1. **地理/文化背景**：改为非亚洲国家背景，地名、场景、文化习俗要符合当地
2. **人名**：
   - 优先使用提供的英文名作为主要角色
   - **如果需要更多角色，可以自由创造新的英文名字**
   - 避免中文和拼音，确保人名一致性
3. **日常细节**：
   - 食物/饮品：根据场景本土化（外卖→披萨/中餐外卖，饮料→咖啡/啤酒等）
   - 社交习惯：聚会方式、称呼、节日庆祝等
   - 教育体系：小学/初中/高中/大学对应当地学制
   - 职业设定：保持原有职业类型，但用本地化描述和行业术语
   - 货币单位：人民币→美元/英镑
   - 计量单位：公里→英里，公斤→磅等
   - 网络平台：微博→Twitter/X，微信→WhatsApp/iMessage 等

4. **语言风格**：
   - 使用地道的英语口语、俚语和习惯表达
   - 避免直译式的中式英语表达
   - 保持原作的叙事风格、氛围和情感张力
   - 对话要符合角色背景和说话习惯

5. **文化元素适配**（根据题材调整）：
   - 神话/超自然：道教/佛教元素→基督教/北欧神话/凯尔特民间传说等
   - 节日：春节→圣诞节/感恩节，中秋节→万圣节等
   - 流行文化梗：改为欧美观众熟悉的电影/音乐/网络梗

【剧情扩展要求】⭐
- **原文内容可能很短（例如只有2章）**
- 你需要根据要求的章节数（例如15章、30章、100章）**自由扩展剧情**
- **保证剧情合理、连贯、有吸引力**
- 增加必要的情节转折、人物关系、次要情节线
- 保持整体节奏：快节奏、有反转、让读者感觉爽

【输出格式要求】
- 保留重要的叙事节奏和情节转折
- 符合英文的标点符号
- 章节标题不要用"the XXX"的宾语短语、介词短语格式
- 整体剧情节奏快、有反转、让读者感觉爽

【类型】
{genre}

【建议人名列表】（可以使用，也可以自己创造新名字）
男性名字参考: {male_names}
女性名字参考: {female_names}

【作者风格】
{style}

【要求章节范围】
第 1 章 到 第 {end_chapter} 章（共 {end_chapter} 章）
**注意：如果原文很短，你需要合理扩展剧情来满足章节数要求**

【输出格式】
请按以下格式输出（纯文本，不要JSON）：

===== TITLE =====
[英文标题]

===== BLURB =====
[简介内容，少于3000字符]

===== CATEGORY =====
{genre}

===== TAGS =====
[用逗号分隔，例如: #SlowBurn, #ForcedProximity, #AlphaMale]

===== AGE_CATEGORY =====
[Young Adult / New Adult / Adult]

===== WORLD_SETTING =====
[世界观描述，200-500词]

===== MAIN_CHARACTERS =====
[每个角色一段，格式：]
Character 1: [姓名] - [性别] - [角色定位：protagonist/antagonist/supporting]
Personality: [性格描述]
Background: [背景故事]

Character 2: [姓名] - [性别] - [角色定位]
Personality: [性格描述]
Background: [背景故事]

[继续列出所有主要角色...]

===== CHAPTER_OUTLINES =====
[每章一段，格式：]

Chapter 1: [章节标题]
Summary: [本章剧情概要，200-300词，详细描述关键情节]
Key Events: [关键事件1], [关键事件2], [关键事件3]
Characters: [涉及的角色名，用逗号分隔]

Chapter 2: [章节标题]
Summary: [本章剧情概要，200-300词]
Key Events: [关键事件列表]
Characters: [涉及的角色名]

[继续到第 {end_chapter} 章...]

===== END =====

【重要提醒】
1. 输出必须是纯文本格式，严格按照上述格式
2. 不要输出JSON或其他格式
3. 每个章节的Summary要详细，确保后续写作有足够信息
4. 如果原文内容不足以支撑要求的章节数，请合理扩展剧情"""


DEFAULT_WRITER_PROMPT = """你是一个专业的英语网文作家。根据以下信息写作章节内容。

【必须遵守的规则】
1. 每章字符数必须在 9500-30000 之间（包括空格和标点）
2. 保持故事连贯性和情感张力
3. 对话要自然、地道，符合角色性格
4. 避免重复描写和冗长段落
5. 确保章节独立但互相衔接

【字符数检查】
- 最少：9500 字符（不能少）
- 最多：30000 字符（不能超）
- 如果不符合，自动调整重写

【类型】
{genre}

【作者风格】
{style}

【世界观】
{world_setting}

【主要角色】
{characters}

【任务】
请根据以下大纲写作 Chapter {start_chapter} - {end_chapter}，
确保：
1. 突出主角的视角和情感
2. 推进情节发展
3. 保持与前文的连贯性（见下文）
4. 每章字符数 9500-30000

【前文参考】
（仅续写时提供）
{previous_context}

【章节大纲】
{chapter_outlines}

【输出格式】
每章单独输出，格式如下：

Chapter {n}: [章节标题]

[正文内容...]

---

（在每章末尾标注字符数）
Character Count: XXXX
"""


class PromptManager:
    """Prompt管理器"""

    def __init__(self):
        self.prompts = self.load_prompts()

    def load_prompts(self):
        """加载Prompt配置"""
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始化默认Prompt
            default_prompts = {
                'outline': {
                    'default': DEFAULT_OUTLINE_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_OUTLINE_PROMPT,
                            'created_at': datetime.now().isoformat()
                        }
                    ],
                    'active_version': 'Default'
                },
                'writer': {
                    'default': DEFAULT_WRITER_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_WRITER_PROMPT,
                            'created_at': datetime.now().isoformat()
                        }
                    ],
                    'active_version': 'Default'
                },
                'character_prompts': {}
            }
            self.save_prompts(default_prompts)
            return default_prompts

    def save_prompts(self, prompts=None):
        """保存Prompt配置"""
        os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
        if prompts is None:
            prompts = self.prompts
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

    def get_outline_prompt(self, version=None):
        """获取大纲生成Prompt"""
        if version is None:
            version = self.prompts['outline']['active_version']

        for v in self.prompts['outline']['versions']:
            if v['name'] == version:
                return v['content']

        # 如果找不到，返回默认
        return self.prompts['outline']['default']

    def get_writer_prompt(self, version=None):
        """获取内容写作Prompt"""
        if version is None:
            version = self.prompts['writer']['active_version']

        for v in self.prompts['writer']['versions']:
            if v['name'] == version:
                return v['content']

        return self.prompts['writer']['default']

    def save_custom_outline_prompt(self, name, content):
        """保存自定义大纲Prompt"""
        # 检查是否已存在
        for v in self.prompts['outline']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        # 添加新版本
        self.prompts['outline']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def save_custom_writer_prompt(self, name, content):
        """保存自定义写作Prompt"""
        for v in self.prompts['writer']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        self.prompts['writer']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def set_active_outline_version(self, version_name):
        """设置当前使用的大纲Prompt版本"""
        self.prompts['outline']['active_version'] = version_name
        self.save_prompts()

    def set_active_writer_version(self, version_name):
        """设置当前使用的写作Prompt版本"""
        self.prompts['writer']['active_version'] = version_name
        self.save_prompts()

    def get_outline_versions(self):
        """获取所有大纲Prompt版本列表"""
        return [v['name'] for v in self.prompts['outline']['versions']]

    def get_writer_versions(self):
        """获取所有写作Prompt版本列表"""
        return [v['name'] for v in self.prompts['writer']['versions']]

    def restore_default_outline(self):
        """恢复默认大纲Prompt"""
        self.prompts['outline']['active_version'] = 'Default'
        self.save_prompts()

    def restore_default_writer(self):
        """恢复默认写作Prompt"""
        self.prompts['writer']['active_version'] = 'Default'
        self.save_prompts()

    def render_outline_prompt(self, variables):
        """渲染大纲Prompt（替换变量）"""
        prompt = self.get_outline_prompt()
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def render_writer_prompt(self, variables):
        """渲染写作Prompt（替换变量）"""
        prompt = self.get_writer_prompt()
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        return prompt

    def save_character_prompt(self, character_name, prompt_content):
        """为角色保存独立Prompt"""
        self.prompts['character_prompts'][character_name] = {
            'content': prompt_content,
            'updated_at': datetime.now().isoformat()
        }
        self.save_prompts()

    def get_character_prompt(self, character_name):
        """获取角色独立Prompt"""
        return self.prompts['character_prompts'].get(character_name, {}).get('content', None)

    def get_all_character_prompts(self):
        """获取所有角色Prompt"""
        return self.prompts['character_prompts']

    def get_default_outline_prompt(self):
        """获取当前活跃的大纲Prompt（简化方法）"""
        return self.get_outline_prompt()

    def save_custom_prompt(self, content):
        """保存自定义Prompt（简化方法）

        保存为"Custom"版本并设置为活跃版本
        """
        version_name = "Custom"
        self.save_custom_outline_prompt(version_name, content)
        self.set_active_outline_version(version_name)

    def reset_to_default(self):
        """重置为默认Prompt（简化方法）"""
        self.restore_default_outline()
