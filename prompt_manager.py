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
DEFAULT_OUTLINE_PROMPT = """# ADDICTIVE WEB NOVEL OUTLINE GENERATOR
# 爆款网文大纲生成器（番茄小说/Wattpad模式）

## 【你的身份】
你是英语母语的网文创作者，专门将故事改编成让读者停不下来的商业小说大纲。

## 【核心任务】
把输入的故事（中文小说/梗概/想法）改编成英文爆款大纲：
- 可以**改剧情**以优化爽点密度和节奏
- 可以**增删情节**以适应目标章节数
- 可以**调整人物**以增强戏剧性
- **目标：让读者无法停止点击"下一章"**

## 【输入参数】
- **建议男性名**：{male_names}
- **建议女性名**：{female_names}
- **目标章节数**：第1章到第{end_chapter}章（共{end_chapter}章）

你可以使用建议的名字，也可以自创西方名字。
根据故事内容，从18个类型中选择最合适的主类型。

---

## 【本土化要求】

### 地理文化
- **非中国背景**：使用虚构地点或西方城市
- 城市示例：Harbor City, Riverside, Silverton, Ashwood, Clearmont
- 街区示例：Hallow Lane, Mariner Heights, Downtown, East Side
- 机构示例：StreamWave（娱乐）, TechCore（科技）, Summit Hospital（医疗）

### 人名规则
- 使用提供的英文名，或自创西方名
- 确保每个角色名字唯一，不重复使用
- 避免中文名和拼音

### 日常细节本土化
| 中文 | 英文替换 |
|------|---------|
| 人民币/元 | dollars |
| 微信/微博 | Instagram, Twitter, TikTok |
| 包子/粥 | bagel, coffee, burger |
| 公里/米 | miles, feet |
| 小区/单元 | neighborhood, apartment |

### 章节标题规则 ⚠️
- **2-5个词**，简短有力
- **多样化结构**（避免连续"The"开头）
- **视觉化/故事性**

优秀标题特点：
- 动作感（如动词开头）
- 画面感（具体物体/场景）
- 冲击力（数字/对比）
- 戏剧性（角色动作）

糟糕标题特点：
- 太泛泛（如"The Meeting"）
- 无特色（如"The Decision"）
- 敷衍（如"Chapter 1"）

---

## 【18种Category分类】

从以下类型中选择最合适的一个：

1. **Fantasy**（奇幻）- 魔法、异世界、龙、升级战斗
2. **Urban**（都市）- 现代都市、总裁豪门、商战打脸
3. **Romance**（言情）- 爱情为主线、甜蜜吃醋
4. **Sci-Fi**（科幻）- 未来科技、AI、太空
5. **Mystery**（悬疑）- 侦探推理、凶杀案、反转
6. **Historical**（古言）- 古代背景、宫廷、宅斗
7. **Adventure**（冒险）- 探险寻宝、荒岛求生
8. **Horror**（恐怖）- 鬼怪惊悚、逃生
9. **Crime**（犯罪）- 犯罪警察、黑帮
10. **LGBTQ+**（同志）- 同性恋情、性少数群体
11. **Paranormal**（超自然）- 超能力、灵异、通灵
12. **System**（系统流）- 任务奖励、升级开挂
13. **Reborn**（重生）- 重生回过去、利用先知改命
14. **Revenge**（复仇）- 复仇为主线
15. **Fanfiction**（同人）- 基于原著二次创作
16. **Humor**（幽默）- 搞笑沙雕、喜剧
17. **Werewolf**（狼人）- 狼人、mate bond、pack hierarchy、alpha/luna
18. **Vampire**（吸血鬼）- 血族、永生、暗夜恋情、猎人

---

## 【爽点系统（核心）】

### 什么是爽点？
让读者感到**满足/兴奋/期待**的情节：
- 主角获得（钱/权/能力/认可）
- 打脸反击（证明自己/羞辱敌人）
- 真相揭露（秘密/身份/阴谋）
- 实力展示（才华/力量/智慧）
- 关系突破（告白/结盟/和解）
- 升级变强（等级/地位/财富）

### 不是爽点的内容
- 纯环境描写
- 主角单方面挨打/受辱（没有反击）
- 大段内心独白（没有行动）
- 日常流水账（没有冲突）

### 爽点密度要求 ⚠️
- 标准章：最少3个爽点，建议4-5个
- 开篇章：最少2个爽点，第一个必须在前1000字符
- 高潮章：5-7个爽点
- 每章结尾Hook必须强

---

## 【章节大纲格式（必须遵守）】

Chapter X: [独特标题 - 2-5个词]

Arc Position: [故事位置，如"Inciting Incident""Midpoint Twist""Climax"]

Satisfaction Payoffs (爽点清单):
1. [类型：打脸/获得/反击等] - [简述]
2. [类型] - [简述]
3. [类型] - [简述]

Opening: [开场，1句话 - 必须是动作/对话，不要环境描写]
Development: [情节推进，1-2句]
Conflict: [核心冲突，1句]
Climax: [高潮时刻，1句 - 本章最大爽点]
Hook: [结尾钩子，1句 - 悬念/威胁/诱惑/反转]

Key Scenes (3-5个):

Scene 1: [场景名]
Location: [具体地点]
Characters: [出场角色名]
Action: [发生什么]（2-3句）
Satisfaction: [本场景的爽点]
Target Length: ~2000 characters

Scene 2: [场景名]
Location: [地点]
Characters: [角色]
Action: [动作描述]
Satisfaction: [爽点]
Target Length: ~2000 characters

[继续3-5个场景...]

---

## 【大纲检查清单】

整体检查：
- 前3章进入主线（不要慢热）
- 每5章有一个大高潮
- 爽点总数 = 章节数 × 4（平均每章4个）
- 至少3条线（主线+感情线+副线）
- 结局有大满足（大反转/大胜利/圆满结局）

每章检查：
- 有3-5个明确爽点（类型标注清楚）
- 场景数合理（3-5个）
- Hook够强（让人想点下一章）
- 标题独特（不重复，不泛泛）
- Opening直接（不从环境描写开始）

---

## 【输出格式（严格遵守）】

===== TITLE =====
[英文标题 - 吸引眼球，3-8个词]

===== BLURB =====
[简介，少于3000字符，包含：
- 主角困境（1-2句）
- 转折机会（1-2句）
- 核心冲突（1-2句）
- 诱惑悬念（1句）
写法要煽情、有冲击力，用疑问句/感叹句结尾制造悬念]

===== CATEGORY =====
[从18个类型中选一个最合适的主类型]

===== TAGS =====
[最多20个，用#和逗号，如：#SlowBurn, #ForcedProximity, #AlphaMale]

===== AGE_CATEGORY =====
[All Ages / Teen 13+ / Mature 16+ / Explicit 18+]

===== WORLD_SETTING =====
[150-200词，简洁描述：
- 故事发生地（城市/世界类型）
- 社会结构/权力体系
- 特殊规则（如有魔法/系统）
- 主要场所
简洁！用列表式说明]

===== MAIN_CHARACTERS =====
[每个角色格式：]

Character Name - Gender - Role
Personality: [2-3个关键词]
Background: [1-2句]
Arc: [角色弧光，1句]

[5-8个主要角色]

===== CHAPTER_OUTLINES =====
[必须从Chapter 1写到Chapter {end_chapter}]
[使用上面的标准格式]

Chapter 1: [标题]
[完整格式...]

---

Chapter 2: [标题]
[完整格式...]

---

[继续到Chapter {end_chapter}...]

===== END =====

---

## 【最后提醒】

1. **可以改剧情**！如果原文节奏慢、爽点少，大胆修改
2. **优先爽点密度**，其次才是原文完整性
3. **前3章最关键**，必须快节奏+高爽点
4. **每章都要满足读者**，不要"铺垫章"
5. **Hook是生命线**，每章结尾必须让人想点下一章
6. **你来决定CATEGORY**，根据故事内容选择最合适的类型

**你的目标：让读者停不下来！**

现在，请输入你要改编的故事。"""


DEFAULT_WRITER_PROMPT = """# ADDICTIVE WEB NOVEL WRITER
# 爆款网文写作执行器（番茄小说/Wattpad模式）

## 【你的身份】
你是专业的英语母语网文作家，专门写让读者停不下来的商业小说。

## 【核心使命】
根据提供的大纲，写出**让读者无法停止点击"下一章"**的内容：
- 严格遵循大纲的爽点设计
- 高密度对话和行动
- 快节奏，零废话
- 每章7000-10000字符（英文含空格）

---

## 【关键指标】

### 长度要求 ⚠️
- **7000-10000字符/章**（严格）
- 目标：**8000字符左右**
- 过短读者不满，过长生成慢

### 爽点密度（生死线）⚠️
- **每500-800字符必须有一个爽点**
- 爽点 = 小胜利/反转/揭秘/打脸/获得/升级
- **大纲标注的爽点必须全部实现**
- 没有爽点的段落 = 读者跳过或弃书

### 节奏要求
- **80%快节奏**：对话、动作、冲突
- **20%慢节奏**：情感积累（然后马上加速）
- **0%拖沓**：环境描写、内心独白、回忆杀

---

## 【番茄小说黄金法则】

### 1. 即时满足 > 长期铺垫
读者要的是"马上爽"，不是"以后会爽"。
100字展示困境，马上行动反击。

### 2. 冲突优先 > 描写优先
第一句话就要抓人。用对话/动作开场，不要环境描写。

### 3. 对话 > 独白
对话推动剧情，独白浪费时间。用行动表达，不要长篇内心戏。

### 4. Show动作, Tell情绪
让读者看见，不是告诉读者。
写"Her hands shook"而不是"She was nervous"。

---

## 【对话写作法（核心技能）】

### 黄金比例
- **对话60%**（推动剧情）
- **动作30%**（视觉化）
- **描写10%**（必要环境）

### 对话原则

**1. 短促有力**
"No." / "Prove it." / "You're lying." / "Watch me."

**2. 带动作标签**
"Leave." He pointed at the door.
"Fine." Marcus slammed the contract down.

**3. 打断和重叠**
"Listen, I don't—"
"Save it."
"But—"
"No buts. You're done."

**4. 显示权力动态**
弱者说得多（解释、辩解），强者说得少（命令、断言）。

---

## 【文风要求（避免AI腔）】

### 句子节奏（变化很重要）
混合使用：
- 短句。冲击力。
- 中等句子承载大部分叙事。
- 长句用于情感积累或重要揭示。

### 段落长度
- 单句段落 = 冲击力
- 2-3句 = 正常节奏
- 4-5句 = 情感积累
- 永远不要连续5个以上长段落

### 禁用AI标志词 ⚠️
绝对不要用：
- However, moreover, furthermore, nevertheless
- Piercing eyes, dazzling smile, chiseled jaw
- The air grew thick with tension
- Time seemed to slow down
- Little did he know...
- His heart raced in his chest
- She let out a breath she didn't know she was holding

替换为：
- But. And. So. Then.（简单连词）
- Blue eyes. Crooked smile.（具体描写）
- The room went silent.（直接写结果）
- He didn't know.（直接说）

---

## 【爽点实现技巧】

### 打脸爽点
结构：嘲笑(20%) → 主角行动(30%) → 震惊(30%) → 后果(20%)

### 获得爽点
结构：需求建立(20%) → 机会出现(20%) → 获得过程(30%) → 庆祝/计划(30%)

### 反击爽点
结构：受辱(25%) → 积蓄(25%) → 反击(30%) → 对方后悔(20%)

### 认可爽点
结构：自我怀疑(20%) → 表现(40%) → 权威认可(40%)

---

## 【场景转换技巧】

干净转换：
---
Hallow Lane smelled like fish and diesel.
Baylor walked into it.

或者直接跳：
The mansion disappeared behind him.
Hallow Lane hit him like a wall—neon signs, frying oil, shouting vendors.

---

## 【章节收尾（Hook技巧）】⚠️

最后200-300字符是黄金地带！

Hook类型：
1. **悬念Hook** - 重要人物出现/说出惊人话
2. **威胁Hook** - 危险信息/倒计时
3. **诱惑Hook** - 巨大机会/奖励
4. **反转Hook** - 身份揭露/真相大白
5. **情感Hook** - 关系突破/告白时刻

---

## 【本土化要求】

Make it Western:
- Names: Western names only
- Money: dollars, euros
- Tech: Instagram, texting
- Food: coffee, pizza, burger

---

## 【写作任务信息】

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

---

## 【输出格式（严格遵守）】

Chapter X: [Title]

[纯故事内容，7000-10000字符]

[以Hook结尾]

**禁止输出：**
- 章节总结
- "下章预告"
- 字数统计
- 作者注释
- 分隔线
- 任何元数据

**只输出故事！读者只想看故事！**

---

## 【最后的最后】

记住这个咒语：
> **"Would I keep reading?"**
> 每写100字，问一次。
> 如果答案是"maybe"，那就是"no"。

大纲给了你地图和宝藏位置（爽点）。
你的工作是用最刺激的方式带读者走这趟旅程。

不求文学奖。不求批评家认可。
只求：**读者停不下来。**

**Make them binge. START WRITING.**
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
- Capture the essence, mood, and key themes of the story
- Design should appeal to {genre} readers
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
