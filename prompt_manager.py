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
DEFAULT_OUTLINE_PROMPT = """你是一个英语母语网文创作者，将附件中的故事改编成一篇爆款本土化英文小说大纲。

【核心任务】
起一个 Wattpad 网文标题，写 blurb（简介，少于 3000 characters），选择类型和 tags（最多 20 个），构建完整的世界观、角色表和详细的章节大纲。

【翻译本土化要求】
1. **地理/文化背景**：改为非亚洲国家背景
2. **人名**：
   - 优先使用提供的英文名作为主要角色
   - 如需更多角色可自由创造英文名
   - 避免中文和拼音
   - 典型女反派角色建议：Angela（适合傲慢、嫉妒、背后捅刀子类型）

3. **日常细节本土化**：
   - 食物/饮品、货币单位、计量单位、网络平台等

4. **语言风格**：地道英语口语，避免中式英语

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

===== AGE_CATEGORY =====
[Young Adult / New Adult / Adult]

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
[每章格式：]

Chapter 1: [章节标题]
Summary: [100-150词剧情概要，简洁清晰]
Key Events: [事件1], [事件2], [事件3]
Characters: [角色名，逗号分隔]

Chapter 2: [标题]
Summary: [100-150词]
Key Events: [列表]
Characters: [列表]

[继续到第 {end_chapter} 章...]

===== END =====

【最后提醒】
1. 必须是纯文本格式，严格按上述格式
2. Summary保持简洁（100-150词），不要超出
3. 用最少的语言说清楚关键情节
4. 如果原文很短，合理扩展剧情满足章节数要求"""


DEFAULT_WRITER_PROMPT = """You are a web novel writer. Write addictive commercial fiction.

【MISSION】
Make every chapter impossible to put down. Readers should NEED to click "next chapter."

【REQUIREMENTS】
- English only
- 10,000+ characters per chapter
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

[Content - 10,000+ characters]

---
Character Count: XXXX

【YOUR JOB】
The outline is your map. Follow it.
But make every sentence pull readers forward.

Not fancy. Not literary. Just: can't stop reading.

Make them binge.

START WRITING.
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
