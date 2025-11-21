"""
Writer Worker V2 - 完全基于用户成功脚本重写
"""
import argparse
import json
import os
import sys
import time
import re
from datetime import datetime
from openai import OpenAI

from utils import (
    scan_chapter_files,
    save_chapter_file,
    validate_chapter_length,
    save_project_metadata
)
from prompt_manager import PromptManager


# 写作系统提示词（固定在代码中）- 强调自然人类写作风格
WRITING_SYSTEM_PROMPT = """You are a professional web novelist. Write addictive fiction that feels human-written.

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


class WriterWorkerV2:
    """写作Worker - 完全按照成功脚本的模式"""

    def __init__(self, config_file, task_id):
        print(f"\n{'='*70}")
        print(f"🔧 WriterWorkerV2.__init__() 开始")
        print(f"{'='*70}")
        print(f"  配置文件: {config_file}")
        print(f"  任务ID: {task_id}")

        self.config_file = config_file
        self.task_id = task_id

        # 加载配置
        print(f"\n📖 读取配置文件...")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ 配置文件读取成功")
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
            raise

        # 初始化
        self.project_folder = None
        self.outline_file = None
        self.progress_file = f'tasks/{task_id}/progress.json'
        self.prompt_mgr = PromptManager()  # Prompt管理器

        # 统计
        self.total_tokens = 0
        self.total_cost = 0.0
        self.chapters_completed = 0

        # 初始化OpenAI客户端（使用Jupyter稳定版的方式）
        print(f"\n🔧 初始化OpenAI客户端...")
        api_key = self.config.get('api_key')
        base_url = self.config.get('base_url', 'https://yunwuapi.com')

        # 确保base_url以/v1/结尾（OpenAI SDK需要）
        if not base_url.endswith('/v1/'):
            if not base_url.endswith('/'):
                base_url += '/'
            if not base_url.endswith('v1/'):
                base_url += 'v1/'

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        print(f"✅ OpenAI客户端初始化完成")

        print(f"\n{'='*70}")
        print(f"📚 Writer Worker V2 初始化完成")
        print(f"{'='*70}")
        print(f"  任务ID: {task_id}")
        print(f"  模型: {self.config.get('model', 'N/A')}")
        print(f"  Base URL: {base_url}")
        print(f"  Temperature: {self.config.get('temperature', 0.8)}")
        print(f"  Max Tokens: {self.config.get('max_tokens', 20000)}")
        print(f"  outline_file: {self.config.get('outline_file', 'NOT SET')}")
        print(f"  project_folder: {self.config.get('project_folder', 'NOT SET')}")

    def update_progress(self, status, current_chapter=0, message=""):
        """更新进度文件"""
        progress = {
            'task_id': self.task_id,
            'status': status,
            'current_chapter': current_chapter,
            'target_chapters': self.config.get('target_chapters', 0),
            'chapters_completed': self.chapters_completed,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'message': message,
            'updated_at': datetime.now().isoformat()
        }

        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def call_api(self, system_prompt, user_prompt):
        """
        API调用 - 使用OpenAI SDK（Jupyter稳定版方式）
        保持system和user消息分离，不合并！
        """
        print(f"\n{'='*70}")
        print(f"🌐 API调用 (OpenAI SDK)")
        print(f"{'='*70}")
        print(f"  System Prompt: {len(system_prompt):,} 字符")
        print(f"  User Prompt: {len(user_prompt):,} 字符")

        model = self.config.get('model', 'gpt-5-mini')
        temperature = self.config.get('temperature', 0.85)
        max_tokens = self.config.get('max_tokens', 35000)

        print(f"  Model: {model}")
        print(f"  Temperature: {temperature}")
        print(f"  Max Tokens: {max_tokens:,}")
        print(f"\n⏳ 发送请求...")

        try:
            start_time = time.time()

            # 使用OpenAI SDK调用（完全按照Jupyter稳定版）
            # 关键：保持system和user分离，不合并！
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            elapsed = time.time() - start_time

            # 获取结果
            content = response.choices[0].message.content
            usage = response.usage

            chars = len(content)
            words = len(content.split())

            print(f"\n✅ API调用成功")
            print(f"  耗时: {elapsed:.1f}秒")
            print(f"  生成字符: {chars:,}")
            print(f"  生成单词: {words:,}")
            print(f"  Tokens: {usage.total_tokens:,}")
            print(f"    - Prompt: {usage.prompt_tokens:,}")
            print(f"    - Completion: {usage.completion_tokens:,}")

            return {
                'success': True,
                'content': content,
                'usage': {
                    'total_tokens': usage.total_tokens,
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens
                }
            }

        except Exception as e:
            print(f"\n❌ API调用异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def load_outline(self):
        """加载大纲信息"""
        print(f"\n{'='*70}")
        print(f"📖 load_outline() 开始")
        print(f"{'='*70}")

        try:
            outline_folder = self.config['outline_file']
            print(f"✅ 读取 outline_file 配置: {outline_folder}")
        except KeyError as e:
            print(f"❌ 配置中缺少 'outline_file' 键!")
            print(f"  可用的配置键: {list(self.config.keys())}")
            raise

        self.outline_file = outline_folder

        print(f"\n📖 加载大纲...")
        print(f"  文件夹: {outline_folder}")

        # 读取title和genre
        title_file = os.path.join(outline_folder, 'title.txt')
        category_file = os.path.join(outline_folder, 'category.txt')

        title = "Untitled"
        genre = "Novel"

        if os.path.exists(title_file):
            with open(title_file, 'r', encoding='utf-8') as f:
                title = f.read().strip()

        if os.path.exists(category_file):
            with open(category_file, 'r', encoding='utf-8') as f:
                genre = f.read().strip()

        print(f"  标题: {title}")
        print(f"  类型: {genre}")

        return {
            'title': title,
            'genre': genre,
            'outline_folder': outline_folder
        }

    def initialize_project(self, outline_data):
        """初始化项目文件夹"""
        print(f"\n📁 初始化项目...")

        if 'project_folder' in self.config:
            self.project_folder = self.config['project_folder']
        else:
            from utils import create_project_folder
            self.project_folder = create_project_folder(
                outline_data['title'],
                outline_data['genre']
            )

        print(f"  文件夹: {self.project_folder}")

        # 保存元数据
        metadata = {
            'title': outline_data['title'],
            'genre': outline_data['genre']
        }
        save_project_metadata(self.project_folder, metadata)

        return self.project_folder

    def get_chapter_range(self):
        """获取需要生成的章节范围"""
        scan_result = scan_chapter_files(self.project_folder)
        max_chapter = scan_result['max_chapter']

        config_start = self.config.get('start_chapter', 1)
        config_end = self.config.get('end_chapter', self.config.get('target_chapters', 100))

        start_chapter = max(max_chapter + 1, config_start)
        end_chapter = config_end

        print(f"\n📊 章节范围:")
        print(f"  已完成: {max_chapter} 章")
        print(f"  配置范围: {config_start}-{config_end}")
        print(f"  将生成: {start_chapter}-{end_chapter}")

        return start_chapter, end_chapter

    def build_chapter_batches(self, start_chapter, end_chapter):
        """构建批次列表"""
        batch_size = self.config.get('batch_size', 3)
        batches = []

        current = start_chapter
        while current <= end_chapter:
            batch_end = min(current + batch_size - 1, end_chapter)
            batches.append((current, batch_end))
            current = batch_end + 1

        print(f"\n📦 批次规划:")
        for i, (start, end) in enumerate(batches, 1):
            print(f"  批次 {i}: Chapter {start}-{end}")

        return batches

    def build_user_prompt(self, outline_data, chapter_num, previous_context=""):
        """
        构建用户prompt - 简化版（只包含当前单个章节）
        System Prompt: 固定的写作规则（从prompt_mgr获取）
        User Prompt: _writing_prompt.txt（世界观+角色） + 当前章节summary + 上一章最后1500字符
        """
        outline_folder = outline_data['outline_folder']

        # 1. 读取_writing_prompt.txt（世界观+角色）
        writing_prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
        base_info = ""
        if os.path.exists(writing_prompt_file):
            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                base_info = f.read()

        # 2. 读取当前章节的summary（只读取单个章节！）
        chapter_summary = ""

        # 添加上一章summary（如果有）
        if chapter_num > 1:
            prev_file = os.path.join(outline_folder, f'chapter_{chapter_num - 1}_prompt.txt')
            if os.path.exists(prev_file):
                with open(prev_file, 'r', encoding='utf-8') as f:
                    chapter_summary += f"===== Previous Chapter Summary =====\n"
                    chapter_summary += f.read() + "\n\n"

        # 添加当前章节summary
        current_file = os.path.join(outline_folder, f'chapter_{chapter_num}_prompt.txt')
        if os.path.exists(current_file):
            with open(current_file, 'r', encoding='utf-8') as f:
                chapter_summary += f"===== Current Chapter Outline =====\n"
                chapter_summary += f.read() + "\n\n"

        # 3. 构建完整的用户prompt
        user_prompt = f"""【Book Information】
Title: {outline_data['title']}
Genre: {outline_data['genre']}

【World & Characters】
{base_info}

【Chapter Outline】
{chapter_summary}"""

        # 添加前文context（上一章最后1500字符）
        if previous_context:
            user_prompt += f"""

【Previous Chapter Ending (Last 1500 characters)】
{previous_context}
"""
        else:
            if chapter_num == 1:
                user_prompt += """

【Note】
This is the first chapter - establish the world and hook readers immediately.
"""

        # 添加写作指令
        user_prompt += f"""

Now write Chapter {chapter_num} based on the outline above."""

        return user_prompt

    def get_previous_context(self, current_chapter):
        """获取前文上下文（上一章最后1500字符）"""
        if current_chapter <= 1:
            return ""

        # 查找上一章的文件（支持 chapter_X.txt 和 chapter_X_Title.txt 两种格式）
        import glob
        prev_pattern = os.path.join(self.project_folder, f'chapter_{current_chapter - 1}*.txt')
        prev_files = glob.glob(prev_pattern)

        if not prev_files:
            return ""

        prev_file = prev_files[0]  # 取第一个匹配的文件

        try:
            with open(prev_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 去掉元数据
                if '---' in content:
                    content = content.split('---')[0]
                context = content[-1500:] if len(content) > 1500 else content
                print(f"  ✓ 加载前文: {len(context)} 字符 (from {os.path.basename(prev_file)})")
                return context
        except:
            return ""

    def generate_single_chapter(self, outline_data, chapter_num, previous_context=""):
        """生成单个章节（不再批次生成）"""
        print(f"\n{'#'*70}")
        print(f"# 生成: Chapter {chapter_num}")
        print(f"{'#'*70}")

        # 构建prompt - 从prompt_mgr获取system prompt
        system_prompt = self.prompt_mgr.get_writer_prompt()
        user_prompt = self.build_user_prompt(outline_data, chapter_num, previous_context)

        print(f"\n📝 Prompt信息:")
        print(f"  System Prompt: {len(system_prompt)} 字符")
        print(f"  User Prompt: {len(user_prompt)} 字符")

        # 调用API
        result = self.call_api(system_prompt, user_prompt)

        if not result['success']:
            raise Exception(f"API调用失败: {result['error']}")

        # 更新统计
        if result.get('usage'):
            self.total_tokens += result['usage'].get('total_tokens', 0)

        # 解析章节
        print(f"\n📄 解析章节...")
        chapters = self.parse_chapters(result['content'], chapter_num, chapter_num)

        if not chapters or chapter_num not in chapters:
            print(f"⚠️  警告：未能解析到Chapter {chapter_num}，使用原始内容")
            # 如果解析失败，使用原始内容
            chapters = {chapter_num: {
                'number': chapter_num,
                'title': f'Chapter {chapter_num}',
                'content': result['content']
            }}

        print(f"  ✓ 解析到 Chapter {chapter_num}")

        return chapters

    def parse_chapters(self, content, start_chapter, end_chapter):
        """从响应中解析章节"""
        chapters = {}

        # 匹配 Chapter X: Title
        pattern = r'(?:^|\n)(?:\*\*)?Chapter\s+(\d+):\s*([^\n]+?)(?:\*\*)?(?:\n|$)(.*?)(?=(?:\n\*\*)?Chapter\s+\d+:|$)'
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            chapter_content = match.group(3).strip()

            if start_chapter <= chapter_num <= end_chapter:
                # 清理元数据
                if '---' in chapter_content:
                    chapter_content = chapter_content.split('---')[0].strip()

                chapters[chapter_num] = {
                    'title': chapter_title,
                    'content': chapter_content
                }

                print(f"    Chapter {chapter_num}: {chapter_title} ({len(chapter_content):,} 字符)")

        return chapters

    def save_chapters(self, chapters):
        """保存章节"""
        print(f"\n💾 保存章节...")

        for chapter_num, chapter_data in chapters.items():
            content = chapter_data['content']
            title = chapter_data.get('title', '')

            # 验证长度
            is_valid, char_count, message = validate_chapter_length(content, min_chars=9000)

            if not is_valid:
                print(f"  ⚠️  Chapter {chapter_num}: {message}")

            # 保存
            metadata = {
                'Title': title,
                'Character Count': char_count,
                'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Model': self.config.get('model', 'unknown'),
                'Valid': 'Yes' if is_valid else f'No - {message}'
            }

            save_chapter_file(self.project_folder, chapter_num, content, metadata, title=title)
            self.chapters_completed += 1

            print(f"  ✓ Chapter {chapter_num}: {title} - {char_count:,} 字符 {'✅' if is_valid else '⚠️'}")

    def run(self):
        """运行写作任务"""
        try:
            print(f"\n{'='*70}")
            print(f"🚀 run() 方法开始")
            print(f"{'='*70}")

            # 更新进度
            print(f"\n📝 更新进度: 初始化中...")
            self.update_progress('initializing', message='初始化中...')

            # 加载大纲
            print(f"\n🔄 调用 load_outline()...")
            outline_data = self.load_outline()
            print(f"✅ load_outline() 完成")

            # 初始化项目
            print(f"\n🔄 调用 initialize_project()...")
            self.initialize_project(outline_data)
            print(f"✅ initialize_project() 完成")

            # 获取章节范围
            print(f"\n🔄 调用 get_chapter_range()...")
            start_chapter, end_chapter = self.get_chapter_range()
            print(f"✅ get_chapter_range() 完成: {start_chapter}-{end_chapter}")

            if start_chapter > end_chapter:
                print("\n✅ 所有章节已完成！")
                self.update_progress('completed', current_chapter=end_chapter, message='所有章节已完成')
                return

            self.update_progress('in_progress', current_chapter=start_chapter, message='开始生成')

            # 逐章节生成（不再批次生成）
            for chapter_num in range(start_chapter, end_chapter + 1):
                print(f"\n{'='*70}")
                print(f"📖 生成 Chapter {chapter_num}/{end_chapter}")
                print(f"{'='*70}")

                # 获取前文（上一章最后1500字符）
                print(f"\n🔄 获取前文上下文...")
                previous_context = self.get_previous_context(chapter_num)
                print(f"✅ 前文上下文: {len(previous_context)} 字符")

                # 生成单个章节
                print(f"\n🔄 调用 generate_single_chapter()... 【这里会调用API】")
                chapters = self.generate_single_chapter(outline_data, chapter_num, previous_context)
                print(f"✅ generate_single_chapter() 完成")

                # 保存
                self.save_chapters(chapters)

                # 更新进度
                self.update_progress(
                    'in_progress',
                    current_chapter=chapter_num,
                    message=f'已完成 {chapter_num}/{end_chapter} 章'
                )

                print(f"\n✅ Chapter {chapter_num} 完成")

            # 完成
            self.update_progress(
                'completed',
                current_chapter=end_chapter,
                message=f'所有章节生成完成！共 {self.chapters_completed} 章'
            )

            print(f"\n{'='*70}")
            print(f"✅ 任务完成")
            print(f"{'='*70}")
            print(f"  章节数: {self.chapters_completed}")
            print(f"  Tokens: {self.total_tokens:,}")
            print(f"  项目文件夹: {self.project_folder}")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"\n{'='*70}")
            print(f"❌ 错误: {str(e)}")
            print(f"{'='*70}")
            import traceback
            traceback.print_exc()

            self.update_progress('failed', message=f'错误: {str(e)}')


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🎬 writer_worker_v2.py main() 函数启动")
    print("="*70)
    print(f"  Python 版本: {sys.version}")
    print(f"  当前工作目录: {os.getcwd()}")
    print(f"  命令行参数: {sys.argv}")

    parser = argparse.ArgumentParser(description='Writer Worker V2')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--task-id', required=True, help='任务ID')

    print(f"\n🔧 解析命令行参数...")
    args = parser.parse_args()
    print(f"✅ 参数解析完成:")
    print(f"  --config: {args.config}")
    print(f"  --task-id: {args.task_id}")

    # 创建并运行worker
    print(f"\n🔧 创建 WriterWorkerV2 实例...")
    worker = WriterWorkerV2(args.config, args.task_id)
    print(f"✅ WriterWorkerV2 实例创建完成")

    print(f"\n🔧 调用 worker.run()...")
    worker.run()
    print(f"✅ worker.run() 完成")


if __name__ == '__main__':
    print("\n" + "#"*70)
    print("# writer_worker_v2.py 脚本启动")
    print("#"*70)
    try:
        main()
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ 致命错误: {e}")
        print(f"{'='*70}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
