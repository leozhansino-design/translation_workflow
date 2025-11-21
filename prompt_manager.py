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
DEFAULT_OUTLINE_PROMPT = """你是英语网文作者，将附件改编成英文小说大纲。

【⚠️ CRITICAL REQUIREMENT - 章节数量要求 ⚠️】
你必须生成 **准确的 {end_chapter} 章** 大纲。
- 不能多，不能少，必须正好 {end_chapter} 章
- 从 Chapter 1 开始，到 Chapter {end_chapter} 结束
- 每一章都必须有完整的 Summary, Opening, Development, Conflict, Climax, Hook, Key Scenes
- 如果你生成的章节数量不是 {end_chapter} 章，这个大纲将被拒绝

本土化要求：
- 西方背景（美国/英国/欧洲），禁用中文名/地名/文化
- 人名：{male_names}（男）/ {female_names}（女）
- 反派建议：Angela（傲慢/嫉妒型）
- 日常：西方食物/货币/社交
- 语言：地道英语

剧情要求：
- 从原文扩展到{end_chapter}章（必须准确）
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

⚠️ 你必须生成从 Chapter 1 到 Chapter {end_chapter} 的完整大纲，总共 {end_chapter} 章。

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

【⚠️ 最终检查 ⚠️】
在提交大纲之前，请确认：
✓ 总共生成了 {end_chapter} 章（Chapter 1 到 Chapter {end_chapter}）
✓ 每一章都有完整的结构（Summary, Opening, Development, Conflict, Climax, Hook, Key Scenes）
✓ 没有多余的章节，也没有遗漏的章节

===== END ====="""


DEFAULT_WRITER_PROMPT = """You are a professional web novel writer. Write addictive English fiction in pure narrative form.

CRITICAL FORMAT REQUIREMENTS:
- Output format: "Chapter X: [Title]" followed immediately by the story content
- DO NOT include ANY structural markers like "爽点1.", "Opening:", "Development:", etc.
- Write in continuous narrative prose ONLY
- NO meta-commentary, NO section labels, NO structural annotations

CONTENT RULES:
1. English ONLY - Absolutely no Chinese names, places, or cultural elements
2. Chapter length: 15,000-20,000 words
3. Include 3-5 satisfying moments per chapter (victories, reveals, confrontations, romance)
4. Western setting exclusively (American/British/European names, places, culture)

WRITING STYLE:
- Short, punchy sentences (10-15 words average)
- Varied paragraph lengths (1-5 sentences, mostly 1-3)
- Fast pacing: major event every 200-300 words
- Mobile-friendly formatting

CHAPTER STRUCTURE (integrate naturally, don't label):
- Start with immediate action or tension
- Build through 3-5 major scenes
- Include satisfying payoffs throughout
- End with hook/cliffhanger

DIALOGUE:
- Natural, conversational exchanges
- Use contractions (I'm, don't, can't)
- Interruptions and overlaps
- Character-specific speech patterns

EXAMPLE OUTPUT FORMAT:
Chapter 1: The Beginning

Emma pushed through the glass doors, her heels clicking against marble. The office was silent.

Too silent.

"Where is everyone?" She glanced at her phone. 8:47 AM. The place should be buzzing.

Lucas appeared from around the corner. His face was pale. "Em, we need to talk."

"Not now. I have the presentation—"

"The company's bankrupt."

[Continue the narrative without any structural markers or meta-commentary...]

WRITE PURE NARRATIVE ONLY. NO LABELS. NO MARKERS. START NOW.
"""


DEFAULT_COVER_PROMPT_TEMPLATE = """Create a professional book cover image for "{title}".

Genre: {genre}
Tags: {tags}

Visual Style Requirements:
- {genre_style}
- Photorealistic with cinematic quality
- High contrast dramatic lighting
- Professional publishing-grade composition
- Clear focal point with atmospheric background

Story Context (use this to inform the visual design):
{outline}

Technical Specifications:
- Vertical portrait orientation (1024x1792)
- Composition leaves space for title overlay
- Sharp focus on main visual elements
- Evocative of {genre} genre atmosphere
- Professional book cover quality

Design a visually striking cover that captures the essence and mood of this {genre} story."""


class PromptManager:
    """Prompt管理器"""

    def __init__(self):
        self.prompts = self.load_prompts()
        # 自动更新默认prompts（确保用户总是使用最新版本）
        self._update_default_prompts()

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
                'cover': {
                    'default': DEFAULT_COVER_PROMPT_TEMPLATE,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_COVER_PROMPT_TEMPLATE,
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

    def _update_default_prompts(self):
        """自动更新Default版本的prompts为代码中的最新版本"""
        updated = False

        # 更新outline的Default版本
        if 'outline' in self.prompts and 'versions' in self.prompts['outline']:
            for version in self.prompts['outline']['versions']:
                if version['name'] == 'Default':
                    if version['content'] != DEFAULT_OUTLINE_PROMPT:
                        print("  🔄 检测到大纲Prompt更新，自动升级到最新版本")
                        version['content'] = DEFAULT_OUTLINE_PROMPT
                        version['updated_at'] = datetime.now().isoformat()
                        updated = True
                    break

        # 更新writer的Default版本
        if 'writer' in self.prompts and 'versions' in self.prompts['writer']:
            for version in self.prompts['writer']['versions']:
                if version['name'] == 'Default':
                    if version['content'] != DEFAULT_WRITER_PROMPT:
                        print("  🔄 检测到写作Prompt更新，自动升级到最新版本")
                        version['content'] = DEFAULT_WRITER_PROMPT
                        version['updated_at'] = datetime.now().isoformat()
                        updated = True
                    break

        # 如果有更新，保存到文件
        if updated:
            self.save_prompts()
            print("  ✅ Prompt已更新并保存")

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

    # === Cover Prompt 管理方法 ===
    def get_cover_prompt(self, version=None):
        """获取封面生成Prompt模板"""
        # 确保cover字段存在（向后兼容）
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT_TEMPLATE,
                'versions': [
                    {
                        'name': 'Default',
                        'content': DEFAULT_COVER_PROMPT_TEMPLATE,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'active_version': 'Default'
            }
            self.save_prompts()

        if version is None:
            version = self.prompts['cover'].get('active_version', 'Default')

        for v in self.prompts['cover']['versions']:
            if v['name'] == version:
                return v['content']

        return self.prompts['cover']['default']

    def save_custom_cover_prompt(self, name, content):
        """保存自定义封面Prompt"""
        # 确保cover字段存在
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT_TEMPLATE,
                'versions': [],
                'active_version': 'Default'
            }

        for v in self.prompts['cover']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        self.prompts['cover']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def set_active_cover_version(self, version_name):
        """设置当前使用的封面Prompt版本"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT_TEMPLATE,
                'versions': [{'name': 'Default', 'content': DEFAULT_COVER_PROMPT_TEMPLATE, 'created_at': datetime.now().isoformat()}],
                'active_version': 'Default'
            }
        self.prompts['cover']['active_version'] = version_name
        self.save_prompts()

    def get_cover_versions(self):
        """获取所有封面Prompt版本列表"""
        if 'cover' not in self.prompts:
            return ['Default']
        return [v['name'] for v in self.prompts['cover']['versions']]

    def restore_default_cover(self):
        """恢复默认封面Prompt"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT_TEMPLATE,
                'versions': [{'name': 'Default', 'content': DEFAULT_COVER_PROMPT_TEMPLATE, 'created_at': datetime.now().isoformat()}],
                'active_version': 'Default'
            }
        else:
            self.prompts['cover']['active_version'] = 'Default'
        self.save_prompts()
