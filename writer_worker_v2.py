"""
写作Worker V2 - 基于用户成功代码重构
完全按照工作的http.client模式
"""
import argparse
import json
import os
import sys
import time
import re
import http.client
from datetime import datetime

from prompt_manager import PromptManager
from utils import (
    scan_chapter_files,
    load_chapter_content,
    save_chapter_file,
    validate_chapter_length,
    save_project_metadata
)


class WriterWorkerV2:
    """简化版写作Worker - 基于成功的API调用模式"""

    def __init__(self, config_file, task_id):
        self.config_file = config_file
        self.task_id = task_id

        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化
        self.prompt_mgr = PromptManager()
        self.project_folder = None
        self.progress_file = f'tasks/{task_id}/progress.json'

        # 统计
        self.total_tokens = 0
        self.total_cost = 0.0
        self.chapters_completed = 0

        print(f"✓ Writer Worker V2 初始化完成")
        print(f"  任务ID: {task_id}")
        print(f"  模型: {self.config.get('model', 'N/A')}")
        print(f"  Base URL: {self.config.get('base_url', 'N/A')}")

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

        print(f"📊 进度更新: {status} - {message}")

    def call_api_direct(self, system_prompt, user_prompt, model, temperature=0.8, max_tokens=20000):
        """
        直接API调用 - 完全按照用户成功的代码模式
        """
        print(f"\n{'='*60}")
        print(f"🔄 开始API调用")
        print(f"  模型: {model}")
        print(f"  Temperature: {temperature}")
        print(f"  Max Tokens: {max_tokens}")
        print(f"  System Prompt长度: {len(system_prompt)} 字符")
        print(f"  User Prompt长度: {len(user_prompt)} 字符")
        print(f"{'='*60}")

        # 合并system和user消息为单个user消息（按照用户的代码）
        combined_content = f"{system_prompt}\n\n{user_prompt}"

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

        # 解析base_url（按照用户的代码）
        base_url = self.config.get('base_url', 'https://yunwuapi.com')
        host = base_url.replace("https://", "").replace("http://", "").rstrip('/')
        if '/' in host:
            host = host.split('/')[0]

        print(f"🌐 连接到: {host}")

        conn = None
        try:
            # 设置连接（不设置timeout，按照用户的代码）
            conn = http.client.HTTPSConnection(host)

            start_time = time.time()

            # 发送请求
            conn.request("POST", "/v1/chat/completions", payload, headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')

            elapsed = time.time() - start_time

            print(f"✓ 收到响应")
            print(f"  状态码: {response.status}")
            print(f"  耗时: {elapsed:.1f}秒")

            if response.status == 200:
                response_data = json.loads(data)
                content = response_data['choices'][0]['message']['content']
                usage = response_data.get('usage', {})

                chars = len(content)
                words = len(content.split())

                print(f"✅ API调用成功")
                print(f"  生成字符数: {chars:,}")
                print(f"  生成单词数: {words:,}")
                if usage:
                    print(f"  Tokens: {usage.get('total_tokens', 'N/A'):,}")

                return {
                    'success': True,
                    'content': content,
                    'usage': usage
                }
            else:
                error_msg = f"状态码: {response.status}"
                print(f"❌ API调用失败: {error_msg}")
                print(f"  响应前500字符: {data[:500]}")
                return {
                    'success': False,
                    'error': error_msg,
                    'details': data
                }

        except Exception as e:
            print(f"❌ API调用异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            if conn:
                conn.close()

    def load_outline(self):
        """加载大纲"""
        outline_folder = self.config['outline_file']
        self.outline_file = outline_folder

        print(f"\n📖 加载大纲...")
        print(f"  文件夹: {outline_folder}")

        # 读取 _writing_prompt.txt
        prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"找不到 _writing_prompt.txt: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        print(f"✓ _writing_prompt.txt 已加载 ({len(prompt_content)} 字符)")

        # 解析精简的prompt
        parsed_data = self._parse_writing_prompt(prompt_content)

        # 读取 title 和 genre
        title_file = os.path.join(outline_folder, 'title.txt')
        category_file = os.path.join(outline_folder, 'category.txt')

        title = "Untitled"
        genre = "Romance"

        if os.path.exists(title_file):
            with open(title_file, 'r', encoding='utf-8') as f:
                title = f.read().strip()

        if os.path.exists(category_file):
            with open(category_file, 'r', encoding='utf-8') as f:
                genre = f.read().strip()

        print(f"✓ 标题: {title}")
        print(f"✓ 类型: {genre}")
        print(f"✓ 章节数: {len(parsed_data.get('chapter_outlines', []))}")

        return {
            'outline': {
                'title': title,
                'genre': genre,
                'world_setting': parsed_data.get('world_setting', ''),
                'main_characters': parsed_data.get('main_characters', ''),
                'chapter_outlines': parsed_data.get('chapter_outlines', [])
            }
        }

    def _parse_writing_prompt(self, text):
        """解析 _writing_prompt.txt"""
        data = {
            'world_setting': '',
            'main_characters': '',
            'chapter_outlines': []
        }

        # 提取 WORLD_SETTING
        world_match = re.search(r'={5,}\s*WORLD_SETTING\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if world_match:
            data['world_setting'] = world_match.group(1).strip()

        # 提取 MAIN_CHARACTERS
        chars_match = re.search(r'={5,}\s*MAIN_CHARACTERS\s*={5,}\s*\n(.+?)(?=\n={5,}|$)', text, re.DOTALL)
        if chars_match:
            data['main_characters'] = chars_match.group(1).strip()

        # 提取 CHAPTER_OUTLINES
        chapter_section = re.search(r'={5,}\s*CHAPTER_OUTLINES\s*={5,}\s*\n(.+?)(?=\n={5,}\s*END|$)', text, re.DOTALL)
        if chapter_section:
            chapter_text = chapter_section.group(1)

            # 匹配每个章节
            chapter_pattern = r'Chapter\s+(\d+):\s*(.+?)(?=\nChapter\s+\d+:|$)'
            for match in re.finditer(chapter_pattern, chapter_text, re.DOTALL):
                ch_num = int(match.group(1))
                chapter_content = match.group(2).strip()

                # 提取标题
                lines = chapter_content.split('\n', 1)
                ch_title = lines[0].strip()
                remaining_content = lines[1] if len(lines) > 1 else ""

                data['chapter_outlines'].append({
                    'chapter': ch_num,
                    'title': ch_title,
                    'summary': remaining_content.strip()
                })

        return data

    def initialize_project(self, outline_data):
        """初始化项目文件夹"""
        print(f"\n📁 初始化项目...")

        if 'project_folder' in self.config:
            self.project_folder = self.config['project_folder']
        else:
            from utils import create_project_folder
            outline = outline_data['outline']
            self.project_folder = create_project_folder(
                outline['title'],
                outline['genre']
            )

        print(f"✓ 项目文件夹: {self.project_folder}")

        # 保存元数据
        save_project_metadata(self.project_folder, outline_data['outline'])

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

        print(f"\n📦 生成批次:")
        for i, (start, end) in enumerate(batches, 1):
            print(f"  批次{i}: Chapter {start}-{end}")

        return batches

    def get_previous_context(self, current_chapter):
        """获取前文上下文"""
        if current_chapter <= 1:
            return ""

        prev_chapter_file = os.path.join(self.project_folder, f'chapter_{current_chapter - 1}.txt')

        if not os.path.exists(prev_chapter_file):
            return ""

        content = load_chapter_content(prev_chapter_file)
        context = content[-2000:] if len(content) > 2000 else content

        print(f"✓ 加载前文上下文: {len(context)} 字符")

        return context

    def generate_batch(self, outline_data, batch_start, batch_end, previous_context=""):
        """生成一个批次的章节"""
        print(f"\n{'='*70}")
        print(f"📝 生成批次: Chapter {batch_start}-{batch_end}")
        print(f"{'='*70}")

        outline = outline_data['outline']
        outline_folder = os.path.dirname(self.outline_file)

        # 1. 读取_writing_prompt.txt
        writing_prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
        base_prompt = ""
        if os.path.exists(writing_prompt_file):
            with open(writing_prompt_file, 'r', encoding='utf-8') as f:
                base_prompt = f.read()

        # 2. 读取相关章节的prompts
        chapter_prompts = ""

        # 如果不是从第1章开始，添加上一章的prompt
        if batch_start > 1:
            prev_chapter_prompt_file = os.path.join(outline_folder, f'chapter_{batch_start - 1}_prompt.txt')
            if os.path.exists(prev_chapter_prompt_file):
                with open(prev_chapter_prompt_file, 'r', encoding='utf-8') as f:
                    chapter_prompts += f.read() + "\n\n"

        # 添加当前批次所有章节的prompts
        for ch_num in range(batch_start, batch_end + 1):
            chapter_prompt_file = os.path.join(outline_folder, f'chapter_{ch_num}_prompt.txt')
            if os.path.exists(chapter_prompt_file):
                with open(chapter_prompt_file, 'r', encoding='utf-8') as f:
                    chapter_prompts += f.read() + "\n\n"

        # 3. 组合完整的prompt
        full_prompt = base_prompt + "\n\n===== CHAPTER_OUTLINES =====\n" + chapter_prompts

        # 如果有前文，添加到prompt中
        if previous_context:
            full_prompt += f"\n\n===== PREVIOUS_CONTEXT =====\n{previous_context}\n"

        user_prompt = f"请写作 Chapter {batch_start} - {batch_end}"

        print(f"✓ Prompt构建完成")
        print(f"  System Prompt: {len(full_prompt):,} 字符")
        print(f"  User Prompt: {len(user_prompt)} 字符")

        # 调用API
        model = self.config.get('model', 'gpt-5-mini')
        temperature = self.config.get('temperature', 0.8)
        max_tokens = self.config.get('max_tokens', 20000)

        result = self.call_api_direct(
            system_prompt=full_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if not result['success']:
            raise Exception(f"API调用失败: {result['error']}\n详情: {result.get('details', 'N/A')}")

        result_text = result['content']

        # 更新统计
        if result.get('usage'):
            self.total_tokens += result['usage'].get('total_tokens', 0)

        # 解析章节
        print(f"\n📄 解析章节...")
        chapters = self.parse_chapters_from_response(result_text, batch_start, batch_end)
        print(f"✓ 解析到 {len(chapters)} 个章节")

        return chapters

    def parse_chapters_from_response(self, response_text, start_chapter, end_chapter):
        """从AI响应中解析章节"""
        chapters = {}

        # 使用正则匹配 Chapter X: 格式
        pattern = r'(?:^|\n)(?:\*\*)?Chapter\s+(\d+):\s*([^\n]+)(?:\*\*)?(?:\n|$)(.*?)(?=(?:\n\*\*)?Chapter\s+\d+:|$)'

        matches = re.finditer(pattern, response_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            chapter_content = match.group(3).strip()

            if start_chapter <= chapter_num <= end_chapter:
                # 清理元数据
                if '---' in chapter_content:
                    chapter_content = chapter_content.split('---')[0].strip()

                if 'Character Count:' in chapter_content:
                    chapter_content = chapter_content.split('Character Count:')[0].strip()

                chapters[chapter_num] = {
                    'title': chapter_title,
                    'content': chapter_content
                }

                print(f"  Chapter {chapter_num}: {chapter_title} ({len(chapter_content):,} 字符)")

        return chapters

    def validate_and_save_chapters(self, chapters):
        """验证并保存章节"""
        print(f"\n💾 保存章节...")

        for chapter_num, chapter_data in chapters.items():
            content = chapter_data['content']

            # 验证字符数
            is_valid, char_count, message = validate_chapter_length(content, min_chars=9000)

            if not is_valid:
                print(f"⚠️  Chapter {chapter_num}: {message}")

            # 保存章节文件
            metadata = {
                'Character Count': char_count,
                'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Model': self.config.get('model', 'unknown'),
                'Valid': 'Yes' if is_valid else f'No - {message}'
            }

            save_chapter_file(self.project_folder, chapter_num, content, metadata)

            self.chapters_completed += 1

            print(f"✓ Chapter {chapter_num}: {char_count:,} 字符 {'✅' if is_valid else '⚠️'}")

    def run(self):
        """运行写作进程"""
        try:
            print(f"\n{'='*70}")
            print(f"🚀 任务开始: {self.task_id}")
            print(f"{'='*70}")

            # 更新进度
            self.update_progress('initializing', message='初始化中...')

            # 加载大纲
            outline_data = self.load_outline()

            # 初始化项目
            self.initialize_project(outline_data)

            # 获取章节范围
            start_chapter, end_chapter = self.get_chapter_range()

            if start_chapter > end_chapter:
                print("✅ 所有章节已完成！")
                self.update_progress('completed', current_chapter=end_chapter, message='所有章节已完成')
                return

            # 构建批次
            batches = self.build_chapter_batches(start_chapter, end_chapter)

            self.update_progress('in_progress', current_chapter=start_chapter, message=f'开始生成章节')

            # 逐批生成
            for i, (batch_start, batch_end) in enumerate(batches, 1):
                print(f"\n{'#'*70}")
                print(f"# 批次 {i}/{len(batches)}: Chapter {batch_start}-{batch_end}")
                print(f"{'#'*70}")

                # 获取前文上下文
                previous_context = self.get_previous_context(batch_start)

                # 生成批次
                chapters = self.generate_batch(
                    outline_data,
                    batch_start,
                    batch_end,
                    previous_context
                )

                # 验证并保存
                self.validate_and_save_chapters(chapters)

                # 更新进度
                self.update_progress(
                    'in_progress',
                    current_chapter=batch_end,
                    message=f'已完成 {batch_end}/{end_chapter} 章'
                )

                print(f"✅ 批次 {i} 完成\n")

            # 完成
            self.update_progress(
                'completed',
                current_chapter=end_chapter,
                message=f'所有章节生成完成！共 {self.chapters_completed} 章'
            )

            print(f"\n{'='*70}")
            print(f"✅ 任务完成！")
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
    parser = argparse.ArgumentParser(description='Writer Worker V2')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--task-id', required=True, help='任务ID')

    args = parser.parse_args()

    # 创建并运行worker
    worker = WriterWorkerV2(args.config, args.task_id)
    worker.run()


if __name__ == '__main__':
    main()
