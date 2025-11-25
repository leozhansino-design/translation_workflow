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

    macOS .app 双击启动时，会将资源文件复制到用户应用支持目录
    """
    # 检查是否是打包环境
    if getattr(sys, 'frozen', False):
        # 打包环境：使用应用支持目录存储可写文件
        app_name = "OutlineGenerator"

        # macOS应用支持目录
        if sys.platform == 'darwin':
            support_dir = os.path.expanduser(f'~/Library/Application Support/{app_name}')
        elif sys.platform == 'win32':
            support_dir = os.path.join(os.getenv('APPDATA'), app_name)
        else:
            support_dir = os.path.expanduser(f'~/.{app_name}')

        # 用户数据文件路径
        user_path = os.path.join(support_dir, relative_path)

        # 如果用户文件已存在，直接使用
        if os.path.exists(user_path):
            return user_path

        # 第一次运行，从打包资源复制
        try:
            bundled_path = os.path.join(sys._MEIPASS, relative_path)

            if os.path.exists(bundled_path):
                # 确保目标目录存在
                os.makedirs(os.path.dirname(user_path), exist_ok=True)

                # 复制到用户目录
                import shutil
                shutil.copy2(bundled_path, user_path)
                return user_path
            else:
                return user_path
        except Exception as e:
            # 返回打包路径作为后备（只读）
            return os.path.join(sys._MEIPASS, relative_path)

    else:
        # 开发环境：使用当前目录
        return os.path.join(os.getcwd(), relative_path)


PROMPTS_FILE = get_resource_path('data/prompts.json')


# 默认Prompt模板
DEFAULT_OUTLINE_PROMPT = """你是一个英语母语网文创作者，将附件中的故事改编成一篇爆款本土化英文小说大纲。

【核心任务】
起一个 Wattpad 网文标题，写 blurb（简介，少于 3000 characters），选择类型和 tags（最多 20 个），构建完整的世界观、角色表和详细的章节大纲。

【翻译本土化要求】
1. **地理/文化背景**：改为非亚洲国家背景
2. **人名**：
   - 下面提供了建议人名列表，你可以选择使用
   - 如果不需要那么多角色，不必强行使用所有名字
   - 如果需要更多角色，可以自由创造英文名
   - 避免中文和拼音
   - 典型女反派角色建议：Angela（适合傲慢、嫉妒、背后捅刀子类型）

3. **日常细节本土化**：
   - 食物/饮品、货币单位、计量单位、网络平台等

4. **语言风格**：地道英语口语，避免中式英语

5. **章节字数目标**：每章7000-10000字符

6. **Chapter Title Rules** 🎯:
   - NO "The [Noun]" or abstract nouns alone
   - Mix 6 formats:
     (1) Objects: "Broken Phone"
     (2) Single words: "Falling"
     (3) Actions: "Running Wild"
     (4) Numbers: "Two Days"
     (5) Fragments: "What She Knew"
     (6) Names: "Brooklyn"
   - Each title must be visual, story-specific, and memorable
   - Vary structure—max 2 consecutive "The" titles
   - Test: Can you picture it? Is it generic? Would you remember it?

【剧情扩展要求】⭐
- 原文可能很短（如2章），你需要扩展到要求的章节数（如15章、50章、100章）
- 保证剧情合理、连贯、有吸引力
- 节奏快、有反转、让读者感觉爽

【重要：简洁性要求】🎯
- 用最少的语言解释清楚
- 章节大纲Summary控制在100-150词
- 不要啰嗦，不要重复
- 关键信息点到即止

【类型】
{genre}

【建议人名】（可使用或自创）
男性: {male_names}
女性: {female_names}

【作者风格】
{style}

【要求章节数】
第 1 章到第 {end_chapter} 章（共 {end_chapter} 章）

【输出格式】
请按以下格式输出（纯文本，不要JSON）：

===== TITLE =====
[英文标题]

===== BLURB =====
[简介，少于3000字符]

===== CATEGORY =====
{genre}

===== TAGS =====
[用逗号分隔，例如: #SlowBurn, #ForcedProximity, #AlphaMale]

===== AGE_RATING =====
[MUST choose EXACTLY ONE from these 4 options:
1. All Age
2. Teen 13+
3. Mature 16+
4. Explicit 18+]

===== WORLD_SETTING =====
[世界观，150-200词，简洁描述背景设定]

===== MAIN_CHARACTERS =====
[每个角色简洁描述，格式：]

Character 1: [Name] - [Gender] - [protagonist/antagonist/supporting]
Personality: [2-3个关键性格特点]
Background: [1-2句背景]

Character 2: [Name] - [Gender] - [Role]
Personality: [2-3个关键特点]
Background: [1-2句]

===== CHAPTER_OUTLINES =====
[使用结构化大纲格式，每章包含：Opening, Development, Conflict, Climax, Hook, Key Scenes]
[IMPORTANT: Follow Chapter Title Rules above - use diverse formats, avoid generic "The [Noun]" patterns]

Chapter 1: [章节标题]
Opening: [开场场景，1-2句话描述如何吸引读者]
Development: [情节发展，2-3句话]
Conflict: [冲突点，1-2句话]
Climax: [高潮时刻，1-2句话]
Hook: [结尾钩子，让读者想继续看下一章，1句话]
Key Scenes (expand each fully): [列出需要详细扩展的关键场景]
1. [场景名] - [具体描述，包括对话、动作、情感]
2. [场景名] - [具体描述]
3. [场景名] - [具体描述]
[根据需要添加更多场景，通常5-8个场景]

Chapter 2: [标题]
Opening: [开场]
Development: [发展]
Conflict: [冲突]
Climax: [高潮]
Hook: [钩子]
Key Scenes (expand each fully):
1. [场景描述]
2. [场景描述]
3. [场景描述]

[继续到第 {end_chapter} 章...]

===== END =====

【最后提醒】
1. 必须是纯文本格式，严格按上述格式
2. 每章的Key Scenes要具体，给出详细场景描述
3. Opening/Development/Conflict/Climax/Hook要简洁有力
4. Key Scenes帮助作者扩展章节，每个场景应包含对话、动作、情感等元素
5. 如果原文很短，合理扩展剧情满足章节数要求"""


DEFAULT_WRITER_PROMPT = """You are a web novel writer. Write addictive commercial fiction.

【MISSION】
Make every chapter impossible to put down. Readers should NEED to click "next chapter."

【REQUIREMENTS】
- English only
- 7,000-10,000 characters per chapter
- Western settings (US/UK/Europe)

【CORE RULE: Follow the Outline】
You have a detailed outline with scenes and beats.
FOLLOW IT. But make it entertaining as hell.

The outline tells you WHAT happens.
You decide HOW to make it addictive.

【WHAT MAKES READERS BINGE】

Every chapter needs:
✅ Things actually HAPPEN (not just thinking/describing)
✅ Readers feel SATISFIED (victories, reveals, justice, progress)
✅ Ending makes them NEED more (cliffhanger/question/threat)

Don't overthink. Just:
- Make protagonist DO things (not just observe)
- Give readers emotional payoffs (make them feel good/shocked/excited)
- Keep it moving (something happens every 300-500 words)

【PACING】
Fast when: action, confrontation, revelations
Slow when: brief emotional moments (then speed back up)
Never: long descriptions, internal monologue, filler

Ask: "Would I keep reading?" If no → cut or add punch.

【DIALOGUE】
Keep it real:
- Short exchanges (people don't lecture)
- Use contractions: I'm, don't, won't
- Add interruptions: "Look, I don't—"
- Show power: who talks more = who's weaker

Good:
"You're lying."
"Prove it."
She held up her phone.

Bad:
"I believe that you are being dishonest with me, and I think we should discuss this."

【STYLE: Don't Sound Like AI】

Mix it up:
- Short sentences. Hit hard.
- Medium sentences work for most things.
- Longer sentences build emotion or set up big moments.

Paragraphs:
- One sentence paragraphs for impact.
- 2-3 sentences = normal
- 4-5 sentences = emotional beats

DON'T:
- Make every paragraph same length
- Use "like/as" comparisons every paragraph (limit to 1 per 500 words)
- Write perfect sentences always (break grammar for voice)
- Use fancy words (say "ran" not "hastened")
- Explain emotions ("she was nervous" → show trembling hands)

DO:
- Vary rhythm (fast then slow then fast)
- Use specific details ("Tesla Model S" not "nice car")
- Let actions speak (show, don't tell)
- Mix mundane with dramatic ("She checked her emails. Then saw the body.")

【AVOID AI TELLS】
Red flags:
- "However, moreover, furthermore" → Say: But. And. So.
- "Piercing eyes, dazzling smile" → Never use generic clichés
- Everything too perfect → Break some rules
- No contractions → People say "don't" not "do not"

【SATISFACTION】
Readers want to FEEL something every chapter:
- Protagonist wins something (even small)
- Antagonist loses something (even small)
- Truth revealed
- Status changed
- Problem solved (or gets worse in interesting way)

Give them that hit. Every chapter.

【CHAPTER STRUCTURE】
Your outline gives you scenes.

Opening: Start with the first scene. Jump right in.
Middle: Follow the outline scenes. Keep them punchy.
Ending: Follow the outline hook. Make it hurt (in a good way).

Each scene needs:
1. Clear action (character DOES something)
2. Consequence (what happens because of action)
3. Push forward (connects to next scene)

【WRITING CHECKLIST】
After each scene, ask:
- Did something HAPPEN? (Not just talking about things)
- Would I keep reading?
- Is this scene necessary or filler?
- Did I show it or just tell it?

After each chapter, ask:
- Would I click "next chapter"?
- Did readers get satisfaction moments?
- Does it feel natural or robotic?

【LOCALIZATION】
Make it Western:
- Names: Emma, Marcus, Sofia (not Asian names)
- Money: dollars, euros (not yuan)
- Tech: Instagram, texting (not WeChat)
- Food: coffee, pizza (not baozi)

【CONTEXT】
Genre: {genre}
Style: {style}

World Setting:
{world_setting}

Main Characters:
{characters}

Previous Context (for continuity):
{previous_context}

【YOUR TASK】
Write Chapter {start_chapter} to {end_chapter} following the outline below.

Chapter Outline:
{chapter_outlines}

【FORMAT】
Chapter {n}: [Title]

[Content - 7,000-10,000 characters]

IMPORTANT OUTPUT RULES:
- Output ONLY the chapter title and content
- DO NOT add chapter summaries at the end
- DO NOT add "next chapter preview"
- DO NOT add character count or metadata
- DO NOT add "---" separator lines
- Just the pure story content

【YOUR JOB】
The outline is your map. Follow it.
But make every sentence pull readers forward.

Not fancy. Not literary. Just: can't stop reading.

Make them binge.

START WRITING.
"""


DEFAULT_COVER_PROMPT = """Create a creative bestseller book cover image for this web novel.

【Title】
{title}

【Genre】
{genre}

【Full Story Outline】
{outline}

【Design Requirements】

**Text & Typography:**
- Display ONLY the title: "{title}"
- CRITICAL: NO other text allowed - no author name, no genre labels, no subtitles, no "A Novel", no "Horror", no extra words
- The ONLY text on the cover should be the title itself
- Use creative, designer fonts (examples: decorative script, elegant calligraphy, hand-lettering, artistic serif, or custom stylized fonts)
- Font should match the genre and mood
- Make the title prominent and eye-catching

**Visual Style:**
- Based on the complete outline above, create a unique and compelling book cover
- **Choose the artistic style that best fits the story**: You can decide between realistic/photographic style or abstract/artistic/illustrative style based on what works best for this specific story and genre
- Capture the essence, mood, and key themes of the story
- Design should appeal to {genre} readers
- Avoid generic, cookie-cutter designs - make each cover unique and story-specific
- Create a professional, bestseller-quality cover that stands out

**Technical Specifications:**
- Image dimensions: 300 x 400 pixels (portrait orientation)
- Format: PNG or JPG
- File size: Under 2MB
- High quality and sharp

**Goal:**
Make readers stop scrolling and want to click. The cover should look like a bestselling novel they'd see in a bookstore.

Be creative, distinctive, and professional. Focus on visual storytelling through imagery and beautiful typography."""


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
                'cover': {
                    'default': DEFAULT_COVER_PROMPT,
                    'versions': [
                        {
                            'name': 'Default',
                            'content': DEFAULT_COVER_PROMPT,
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

    def get_cover_prompt(self, version=None):
        """获取封面生成Prompt"""
        if version is None:
            if 'cover' not in self.prompts:
                return DEFAULT_COVER_PROMPT
            version = self.prompts.get('cover', {}).get('active_version', 'Default')

        if 'cover' in self.prompts and 'versions' in self.prompts['cover']:
            for v in self.prompts['cover']['versions']:
                if v['name'] == version:
                    return v['content']

        # 如果找不到，返回默认
        return self.prompts.get('cover', {}).get('default', DEFAULT_COVER_PROMPT)

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

    def get_cover_versions(self):
        """获取所有封面Prompt版本列表"""
        if 'cover' not in self.prompts:
            return ['Default']
        return [v['name'] for v in self.prompts['cover']['versions']]

    def set_active_cover_version(self, version_name):
        """设置当前使用的封面Prompt版本"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [
                    {
                        'name': 'Default',
                        'content': DEFAULT_COVER_PROMPT,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'active_version': 'Default'
            }
        self.prompts['cover']['active_version'] = version_name
        self.save_prompts()

    def save_custom_cover_prompt(self, name, content):
        """保存自定义封面Prompt"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [],
                'active_version': 'Default'
            }

        # 检查是否已存在
        for v in self.prompts['cover']['versions']:
            if v['name'] == name:
                v['content'] = content
                v['updated_at'] = datetime.now().isoformat()
                self.save_prompts()
                return

        # 添加新版本
        self.prompts['cover']['versions'].append({
            'name': name,
            'content': content,
            'created_at': datetime.now().isoformat()
        })
        self.save_prompts()

    def restore_default_cover(self):
        """恢复默认封面Prompt"""
        if 'cover' not in self.prompts:
            self.prompts['cover'] = {
                'default': DEFAULT_COVER_PROMPT,
                'versions': [
                    {
                        'name': 'Default',
                        'content': DEFAULT_COVER_PROMPT,
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'active_version': 'Default'
            }
        else:
            self.prompts['cover']['active_version'] = 'Default'
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

    def render_cover_prompt(self, variables):
        """渲染封面Prompt（替换变量）"""
        prompt = self.get_cover_prompt()
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
