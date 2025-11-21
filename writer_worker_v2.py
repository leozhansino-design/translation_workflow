"""
Writer Worker V2 - 完全基于用户成功脚本重写
"""
import argparse
import json
import os
import sys
import time
import re
import http.client
from datetime import datetime

from utils import (
    scan_chapter_files,
    save_chapter_file,
    validate_chapter_length,
    save_project_metadata
)


# 写作风格系统提示词（基于最佳实践）
WRITING_SYSTEM_PROMPT = """You are a professional web fiction writer. Write addictive, fast-paced English novels.

【CRITICAL REQUIREMENTS】
- Each chapter MUST be at least 10,000 CHARACTERS (not words, CHARACTERS)
- If a chapter is less than 10,000 characters, you MUST continue writing until it reaches 10,000 characters
- Write in ENGLISH only

【Writing Style】
- Short, punchy sentences that hit hard
- Fragmented thoughts for impact: "A crack. A shout. Hands scrambling."
- Poetic but simple imagery: "Blood hit her face. A splatter—hot."
- Sensory details: smell, touch, sound, sight
- Short paragraphs (1-3 sentences max)
- Active voice, strong verbs
- Show, don't tell

【Pacing】
- Open with immediate action or shock
- Fast cuts between scenes
- No long descriptions
- Every paragraph moves the story forward
- Build tension constantly
- End chapters with powerful hooks

【Dialogue】
- Natural, conversational
- Short exchanges
- Conflict in every conversation
- Use dialogue to reveal character and push plot
- Mix dialogue with action beats

【Character Voice】
- Each character has distinct speech patterns
- Reactions before thoughts
- Internal monologue is brief and sharp
- Emotions through physical sensations

【Scene Structure】
- Start in the middle of action
- Use sensory details (not just visual)
- Include bystander reactions
- Build to a moment of impact
- Leave readers wanting more

【Avoid】
- Long explanations
- Complex sentences with multiple clauses
- Formal or literary language
- Passive voice
- Slow buildup

【Format】
Chapter X: [Title]

[Content - minimum 10,000 characters]

IMPORTANT: Each chapter MUST have at least 10,000 characters. Count carefully. If not enough, keep writing.

Write ONLY the novel chapters in English. No explanations."""


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

        # 统计
        self.total_tokens = 0
        self.total_cost = 0.0
        self.chapters_completed = 0

        print(f"\n{'='*70}")
        print(f"📚 Writer Worker V2 初始化完成")
        print(f"{'='*70}")
        print(f"  任务ID: {task_id}")
        print(f"  模型: {self.config.get('model', 'N/A')}")
        print(f"  Base URL: {self.config.get('base_url', 'N/A')}")
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
        API调用 - 完全按照用户成功脚本的方式
        """
        print(f"\n{'='*70}")
        print(f"🌐 API调用")
        print(f"{'='*70}")
        print(f"  System Prompt: {len(system_prompt):,} 字符")
        print(f"  User Prompt: {len(user_prompt):,} 字符")

        # 合并system和user为单个user消息（完全按照用户的代码）
        combined_content = f"{system_prompt}\n\n{user_prompt}"

        model = self.config.get('model', 'gpt-5-mini')
        temperature = self.config.get('temperature', 0.85)
        max_tokens = self.config.get('max_tokens', 120000)

        payload = json.dumps({
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": combined_content
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config["api_key"]}'
        }

        # 解析URL（按照用户的代码）
        base_url = self.config.get('base_url', 'https://yunwuapi.com')
        host = base_url.replace("https://", "").replace("http://", "")

        print(f"  Host: {host}")
        print(f"  Model: {model}")
        print(f"  Temperature: {temperature}")
        print(f"  Max Tokens: {max_tokens:,}")
        print(f"\n⏳ 发送请求...")

        conn = http.client.HTTPSConnection(host)

        try:
            start_time = time.time()

            # 发送请求
            conn.request("POST", "/v1/chat/completions", payload, headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')

            elapsed = time.time() - start_time

            if response.status == 200:
                response_data = json.loads(data)
                content = response_data['choices'][0]['message']['content']
                usage = response_data.get('usage', {})

                chars = len(content)
                words = len(content.split())

                print(f"\n✅ API调用成功")
                print(f"  耗时: {elapsed:.1f}秒")
                print(f"  生成字符: {chars:,}")
                print(f"  生成单词: {words:,}")
                if usage:
                    print(f"  Tokens: {usage.get('total_tokens', 'N/A'):,}")

                return {
                    'success': True,
                    'content': content,
                    'usage': usage
                }
            else:
                error_msg = f"状态码: {response.status}"
                print(f"\n❌ API调用失败: {error_msg}")
                print(f"  响应: {data[:500]}")
                return {
                    'success': False,
                    'error': error_msg,
                    'details': data
                }

        except Exception as e:
            print(f"\n❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            conn.close()

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

    def build_user_prompt(self, outline_data, batch_start, batch_end, previous_context=""):
        """
        构建用户prompt - 基于成功脚本的结构
        关键：明确告诉AI要做什么！
        """
        outline_folder = outline_data['outline_folder']

        # 1. 读取_writing_prompt.txt（世界观+角色）
        writing_prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
        base_info = ""
        if os.path.exists(writing_prompt_file):
            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                base_info = f.read()

        # 2. 读取相关章节的prompts
        chapter_outlines = ""

        # 添加上一章（如果有）
        if batch_start > 1:
            prev_file = os.path.join(outline_folder, f'chapter_{batch_start - 1}_prompt.txt')
            if os.path.exists(prev_file):
                with open(prev_file, 'r', encoding='utf-8') as f:
                    chapter_outlines += f"===== Previous Chapter (Chapter {batch_start - 1}) =====\n"
                    chapter_outlines += f.read() + "\n\n"

        # 添加当前批次所有章节
        for ch_num in range(batch_start, batch_end + 1):
            chapter_file = os.path.join(outline_folder, f'chapter_{ch_num}_prompt.txt')
            if os.path.exists(chapter_file):
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    chapter_outlines += f.read() + "\n\n"

        # 3. 构建完整的用户prompt（类似成功脚本的STORY_OUTLINE）
        user_prompt = f"""Write Chapter {batch_start}"""
        if batch_end > batch_start:
            user_prompt += f" to {batch_end}"

        user_prompt += f""" in ENGLISH based on this information. Each chapter MUST be 10,000+ characters.

Title: {outline_data['title']}
Genre: {outline_data['genre']}

{base_info}

{chapter_outlines}"""

        # 添加前文context（如果有）
        if previous_context:
            user_prompt += f"""

===== PREVIOUS_CONTEXT (last 2000 characters from previous chapter) =====
{previous_context}
"""

        # 添加明确的写作指令（关键！）
        user_prompt += f"""

CRITICAL INSTRUCTIONS:
- Write Chapter {batch_start}"""
        if batch_end > batch_start:
            user_prompt += f" through {batch_end}"
        user_prompt += """
- Each chapter MUST be at least 10,000 CHARACTERS
- Expand every scene with:
  - Multiple dialogue exchanges (3-5 back-and-forth)
  - Crowd reactions and comments
  - Detailed physical descriptions
  - Character thoughts and feelings
  - Sensory details (smells, sounds, textures)
  - Small moments between big events

Start writing now. Remember: 10,000+ characters per chapter."""

        return user_prompt

    def get_previous_context(self, current_chapter):
        """获取前文上下文"""
        if current_chapter <= 1:
            return ""

        prev_file = os.path.join(self.project_folder, f'chapter_{current_chapter - 1}.txt')
        if not os.path.exists(prev_file):
            return ""

        try:
            with open(prev_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 去掉元数据
                if '---' in content:
                    content = content.split('---')[0]
                context = content[-2000:] if len(content) > 2000 else content
                print(f"  ✓ 加载前文: {len(context)} 字符")
                return context
        except:
            return ""

    def generate_batch(self, outline_data, batch_start, batch_end, previous_context=""):
        """生成一个批次的章节"""
        print(f"\n{'#'*70}")
        print(f"# 批次: Chapter {batch_start}-{batch_end}")
        print(f"{'#'*70}")

        # 构建prompt
        system_prompt = WRITING_SYSTEM_PROMPT
        user_prompt = self.build_user_prompt(outline_data, batch_start, batch_end, previous_context)

        # 调用API
        result = self.call_api(system_prompt, user_prompt)

        if not result['success']:
            raise Exception(f"API调用失败: {result['error']}")

        # 更新统计
        if result.get('usage'):
            self.total_tokens += result['usage'].get('total_tokens', 0)

        # 解析章节
        print(f"\n📄 解析章节...")
        chapters = self.parse_chapters(result['content'], batch_start, batch_end)
        print(f"  ✓ 解析到 {len(chapters)} 个章节")

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

            # 验证长度
            is_valid, char_count, message = validate_chapter_length(content, min_chars=9000)

            if not is_valid:
                print(f"  ⚠️  Chapter {chapter_num}: {message}")

            # 保存
            metadata = {
                'Character Count': char_count,
                'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Model': self.config.get('model', 'unknown'),
                'Valid': 'Yes' if is_valid else f'No - {message}'
            }

            save_chapter_file(self.project_folder, chapter_num, content, metadata)
            self.chapters_completed += 1

            print(f"  ✓ Chapter {chapter_num}: {char_count:,} 字符 {'✅' if is_valid else '⚠️'}")

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

            # 构建批次
            print(f"\n🔄 调用 build_chapter_batches()...")
            batches = self.build_chapter_batches(start_chapter, end_chapter)
            print(f"✅ build_chapter_batches() 完成: {len(batches)} 个批次")

            self.update_progress('in_progress', current_chapter=start_chapter, message='开始生成')

            # 逐批生成
            for i, (batch_start, batch_end) in enumerate(batches, 1):
                print(f"\n{'='*70}")
                print(f"📦 批次 {i}/{len(batches)}: Chapter {batch_start}-{batch_end}")
                print(f"{'='*70}")

                # 获取前文
                print(f"\n🔄 获取前文上下文...")
                previous_context = self.get_previous_context(batch_start)
                print(f"✅ 前文上下文: {len(previous_context)} 字符")

                # 生成
                print(f"\n🔄 调用 generate_batch()... 【这里会调用API】")
                chapters = self.generate_batch(outline_data, batch_start, batch_end, previous_context)
                print(f"✅ generate_batch() 完成: {len(chapters)} 个章节")

                # 保存
                self.save_chapters(chapters)

                # 更新进度
                self.update_progress(
                    'in_progress',
                    current_chapter=batch_end,
                    message=f'已完成 {batch_end}/{end_chapter} 章'
                )

                print(f"\n✅ 批次 {i} 完成")

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
