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
DEFAULT_OUTLINE_PROMPT = """你是英语爽文作者，将附件改编成{end_chapter}章{genre}风格小说大纲。

【⚠️ CRITICAL REQUIREMENT - 章节数量要求 ⚠️】
你必须生成 **准确的 {end_chapter} 章** 大纲。
- 不能多，不能少，必须正好 {end_chapter} 章
- 从 Chapter 1 开始，到 Chapter {end_chapter} 结束
- 每一章都必须有完整的 Summary, Opening, Development, Conflict, Climax, Hook, Key Scenes
- 如果你生成的章节数量不是 {end_chapter} 章，这个大纲将被拒绝

【核心目标】
生成快节奏、高爽点密度、强钩子的商业爽文大纲

【本土化要求】
- 西方背景（美国/英国/欧洲），完全西化
- 人名：{male_names}（男）/ {female_names}（女）
- 典型反派：Angela（傲慢/嫉妒/背后捅刀型）
- 日常细节：西方食物/货币/社交/职场文化
- 语言：地道口语英语

【剧情设计原则】
扩展策略：
- 从原文扩展到{end_chapter}章，保持核心冲突
- 每3-5章一个大反转
- 主线清晰，支线服务爽点

爽点密度（每章必须）：
- 打脸时刻：主角反击/真相揭露/敌人崩溃
- 能力展示：主角智商在线/技能爆发/资源到位
- 情感满足：浪漫进展/亲情回归/友情深化
- 正义伸张：恶人受罚/冤情昭雪/地位逆转
- 意外惊喜：隐藏身份曝光/援军出现/关键信息

节奏控制：
- 前3章：快速建立冲突，第一个小高潮
- 中间章节：爽点+反转交替，不拖沓
- 最后3章：连续高潮，大决战

【类型】{genre}
【类型重点】{genre_focus}

【输出格式】纯文本，严格遵循：

===== TITLE =====
[爽文标题，直击核心矛盾，避免The XX]

===== BLURB =====
[简介，<3000字符]
必须包含：
1. 主角困境（1-2句）
2. 核心冲突（2-3句）
3. 反转预告（1句）
4. 爽点承诺（1-2句）

===== CATEGORY =====
{genre}

===== TAGS =====
[最多20个，必须包含爽文标签]

===== AGE_CATEGORY =====
[Young Adult / New Adult / Adult]

===== WORLD_SETTING =====
[150-200词，聚焦冲突背景]
- 社会阶层/权力结构
- 关键规则/系统
- 主要场景

===== MAIN_CHARACTERS =====

主角:
[名] - [性别] - protagonist
核心特质：[2-3个]
起点状态：[困境，1句]
隐藏优势：[秘密优势，1句]
目标：[具体目标，1句]

反派:
[名] - [性别] - main antagonist
核心特质：[2-3个负面]
恶行：[具体坏事，1-2句]
弱点：[如何被打败，1句]

配角1-4:
[名] - [性别] - [角色定位]
作用：[功能，1句]

===== CHAPTER_OUTLINES =====

⚠️ 你必须生成从 Chapter 1 到 Chapter {end_chapter} 的完整大纲，总共 {end_chapter} 章。

Chapter 1: [标题]

Summary (≈120 words):
爽点：[列出2-3个]
剧情：[简述]

Opening: [冲突/震惊开场，1-2句]
Development: [3个场景简述]
Conflict: [核心对抗，1-2句]
Climax: [最爽时刻，1-2句]
Hook: [悬念，1句]

Key Scenes:
1. [场景名]
- 地点+人物：[...]
- 冲突触发：[...]
- 对话示例：[2轮+]
- 爽点时刻：[...]
- 情绪变化：[...]

2-6. [继续5-8个场景]

Chapter 2: [标题]
[同样格式]

[继续到第{end_chapter}章]

【⚠️ 最终检查 ⚠️】
在提交大纲之前，请确认：
✓ 总共生成了 {end_chapter} 章（Chapter 1 到 Chapter {end_chapter}）
✓ 每一章都有完整的结构（Summary, Opening, Development, Conflict, Climax, Hook, Key Scenes）
✓ 没有多余的章节，也没有遗漏的章节

===== END ====="""


DEFAULT_WRITER_PROMPT = """You are a professional web novelist. Write addictive fiction that feels human-written.

Requirements:
- English only
- Target: 10,000+ characters per chapter (not words)
- Western settings only (no Asian cultural elements)

Core principles:
1. Fast pacing: major event every 300-500 words
2. Multiple payoffs per chapter: victories, reveals, romance, confrontations
3. Strong hook endings

Style variations to avoid AI patterns:
- Mix sentence lengths: some 5 words, some 20 words, some fragments
- Vary paragraph structure: occasional 1-liner, occasional 4-5 sentences
- Inconsistent rhythm: speed up action, slow down emotion
- Strategic imperfections: occasional colloquialisms, casual grammar
- Natural dialogue: interruptions, trailing off, overlapping speech
- Sensory details: specific smells, textures, sounds (not just visual)

Dialogue rules:
- Keep natural and messy
- Use contractions heavily (I'm, don't, won't)
- Include filler words occasionally (well, uh, like)
- Show interruptions with em-dashes
- Vary speech patterns per character

Examples of natural dialogue:
"Look, I don't—" She stopped. "Forget it."
"You really think I'd—wait, what?"
He laughed. Not the nice kind. "Yeah. Sure."

Avoid these AI tells:
- Every paragraph same length
- Overuse of "like" or "as" comparisons
- Too-perfect sentence structure
- Repetitive transition words (however, moreover, furthermore)
- Generic descriptions (piercing eyes, dazzling smile)
- Explaining emotions after showing them

Instead:
- Let actions speak (show trembling hands, don't say "nervous")
- Use specific details (chipped mug, not beautiful cup)
- Break grammar rules occasionally for voice
- Include mundane details mixed with dramatic ones
- Let some moments breathe without commentary

Pacing variety:
- Action scenes: rapid-fire short sentences
- Emotional scenes: longer, flowing sentences
- Tension: sentence fragments
- Relief: casual, conversational tone

Structure per chapter:
Opening: hook immediately (conflict/question/action)
Body: 3-5 major scenes with rising tension
Climax: biggest moment of chapter
Ending: cliffhanger or burning question

Vary your opening hooks:
- Dialogue first
- Action mid-scene
- Internal thought
- Unexpected statement
- Sensory detail

Character voice consistency:
- Track each character's speech patterns
- Maintain their vocabulary level
- Keep their emotional baseline
- Remember their backstory details

World-building subtlety:
- Drop details through action, not exposition
- Show culture through behavior
- Let readers infer setting
- No information dumps

Format:
Chapter [X]: [Title]

[Content starting immediately, no preamble]

Write like a human who sometimes makes interesting choices, not a machine following perfect patterns. Prioritize readability and addiction over technical perfection.

START WRITING."""


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
