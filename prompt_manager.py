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
DEFAULT_OUTLINE_PROMPT = """你是英语网文作者，将附件改编成{end_chapter}章英文小说大纲。

本土化要求：
- 西方背景（美国/英国/欧洲），禁用中文名/地名/文化
- 人名：{male_names}（男）/ {female_names}（女）
- 反派建议：Angela（傲慢/嫉妒型）
- 日常：西方食物/货币/社交
- 语言：地道英语

剧情要求：
- 从原文扩展到{end_chapter}章
- 节奏快、有反转、够爽
- 每章3-5个爽点

简洁原则：
- Summary: 100-150词
- 人物：2-3句
- 场景：具体不啰嗦

类型：{genre}
风格：{style}

输出格式（纯文本）：

===== TITLE =====
[标题，避免The XX]

===== BLURB =====
[简介，<3000字符]

===== CATEGORY =====
{genre}

===== TAGS =====
#Tag1, #Tag2, #Tag3（最多20个）

===== AGE_CATEGORY =====
[Young Adult / New Adult / Adult]

===== WORLD_SETTING =====
[150-200词背景设定]

===== MAIN_CHARACTERS =====

Character 1: [名] - [性别] - [protagonist/antagonist/supporting]
Personality: [2-3特质]
Background: [1-2句]

Character 2: [名] - [性别] - [定位]
Personality: [特质]
Background: [背景]

===== CHAPTER_OUTLINES =====

Chapter 1: [标题]

Summary (≈120 words): [核心剧情]

Opening: [开场，1-2句]
Development: [发展，2-3句]
Conflict: [冲突，1-2句]
Climax: [高潮，1-2句]
Hook: [钩子，1句]

Key Scenes (expand each fully):
1. [场景名] - [具体描述：对话/动作/情绪]
2. [场景名] - [互动/冲突/转折]
3. [场景名] - [爽点/满足感]
4-5. [继续5-8个场景]

Chapter 2: [标题]
Summary (≈120 words): [...]
Opening: [...]
Development: [...]
Conflict: [...]
Climax: [...]
Hook: [...]
Key Scenes (expand each fully):
1-5. [...]

[继续到第{end_chapter}章]

===== END ====="""


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
