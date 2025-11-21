"""
独立写作进程
作为独立进程运行，负责章节生成
"""
import argparse
import json
import os
import sys
import time
import re
from datetime import datetime
from openai import OpenAI

from prompt_manager import PromptManager
from utils import (
    scan_chapter_files,
    load_chapter_content,
    save_chapter_file,
    validate_chapter_length,
    save_project_metadata,
    call_api_with_http_client
)


class WriterWorker:
    """写作工作进程"""

    def __init__(self, config_file, task_id):
        self.config_file = config_file
        self.task_id = task_id

        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化
        self.prompt_mgr = PromptManager()
        self.client = None
        self.project_folder = None
        self.progress_file = f'tasks/{task_id}/progress.json'

        # 统计
        self.total_tokens = 0
        self.total_cost = 0.0
        self.chapters_completed = 0

    def initialize_client(self):
        """初始化OpenAI客户端（仅在需要时调用）"""
        if self.client is None:
            base_url = self.config.get('base_url', 'https://yunwuapi.com')
            # OpenAI SDK需要带/v1/后缀的base_url
            if not base_url.endswith('/v1/') and not base_url.endswith('/v1'):
                base_url = base_url.rstrip('/') + '/v1/'
            self.client = OpenAI(
                api_key=self.config['api_key'],
                base_url=base_url
            )

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

    def load_outline(self):
        """加载大纲（从_writing_prompt.txt）"""
        outline_folder = self.config['outline_file']
        self.outline_file = outline_folder  # 保存为实例变量，供后续使用

        # 读取 _writing_prompt.txt
        prompt_file = os.path.join(outline_folder, '_writing_prompt.txt')
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"找不到 _writing_prompt.txt 文件: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        # 解析精简的prompt
        parsed_data = self._parse_writing_prompt(prompt_content)

        # 读取 title 和 genre（用于创建项目文件夹）
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

        # 返回兼容格式
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
        """解析 _writing_prompt.txt 的内容"""
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

        # 提取 CHAPTER_OUTLINES（支持新旧格式）
        chapter_section = re.search(r'={5,}\s*CHAPTER_OUTLINES\s*={5,}\s*\n(.+?)(?=\n={5,}\s*END|$)', text, re.DOTALL)
        if chapter_section:
            chapter_text = chapter_section.group(1)

            # 匹配每个章节 - 支持新格式（Opening/Development/Conflict等）和旧格式（Summary）
            chapter_pattern = r'Chapter\s+(\d+):\s*(.+?)(?=\nChapter\s+\d+:|$)'
            for match in re.finditer(chapter_pattern, chapter_text, re.DOTALL):
                ch_num = int(match.group(1))
                chapter_content = match.group(2).strip()

                # 提取标题（第一行）
                lines = chapter_content.split('\n', 1)
                ch_title = lines[0].strip()
                remaining_content = lines[1] if len(lines) > 1 else ""

                # 将整个章节内容作为 summary（包含所有新格式字段）
                data['chapter_outlines'].append({
                    'chapter': ch_num,
                    'title': ch_title,
                    'summary': remaining_content.strip()
                })

        return data

    def initialize_project(self, outline_data):
        """初始化项目文件夹"""
        # 项目文件夹路径
        if 'project_folder' in self.config:
            self.project_folder = self.config['project_folder']
        else:
            # 创建新项目文件夹
            from utils import create_project_folder
            outline = outline_data['outline']
            self.project_folder = create_project_folder(
                outline['title'],
                outline['genre']
            )

        # 保存元数据
        save_project_metadata(self.project_folder, outline_data['outline'])

        return self.project_folder

    def get_chapter_range(self):
        """获取需要生成的章节范围"""
        # 扫描已有章节
        scan_result = scan_chapter_files(self.project_folder)
        max_chapter = scan_result['max_chapter']

        # 使用配置中的章节范围，如果没有则使用默认值
        config_start = self.config.get('start_chapter', 1)
        config_end = self.config.get('end_chapter', self.config.get('target_chapters', 100))

        # 从下一章开始（跳过已完成的）
        start_chapter = max(max_chapter + 1, config_start)
        end_chapter = config_end

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

        return batches

    def get_previous_context(self, current_chapter):
        """获取前文上下文（用于续写）"""
        if current_chapter <= 1:
            return ""

        # 读取上一章的最后2000字符
        prev_chapter_file = os.path.join(self.project_folder, f'chapter_{current_chapter - 1}.txt')

        if not os.path.exists(prev_chapter_file):
            return ""

        content = load_chapter_content(prev_chapter_file)
        # 取最后2000字符
        return content[-2000:] if len(content) > 2000 else content

    def save_prompt_log(self, batch_start, batch_end, system_prompt, prompt_vars):
        """保存每个批次的Prompt日志"""
        # 创建prompts目录
        prompts_dir = f'tasks/{self.task_id}/prompts'
        os.makedirs(prompts_dir, exist_ok=True)

        # 生成文件名
        prompt_file = os.path.join(prompts_dir, f'batch_{batch_start}-{batch_end}.txt')

        # 保存完整的prompt信息
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"批次 {batch_start}-{batch_end} 的 Prompt\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            f.write("【系统消息 (System Message)】\n")
            f.write("-" * 80 + "\n")
            f.write(system_prompt)
            f.write("\n\n")

            f.write("【用户消息 (User Message)】\n")
            f.write("-" * 80 + "\n")
            f.write(f"请写作 Chapter {batch_start} - {batch_end}")
            f.write("\n\n")

            f.write("【Prompt 变量 (Variables)】\n")
            f.write("-" * 80 + "\n")
            f.write(f"Genre: {prompt_vars.get('genre', 'N/A')}\n")
            f.write(f"Style: {prompt_vars.get('style', 'N/A')}\n")
            f.write(f"Chapters: {batch_start}-{batch_end}\n")
            f.write(f"\nWorld Setting:\n{prompt_vars.get('world_setting', 'N/A')}\n")
            f.write(f"\nCharacters:\n{prompt_vars.get('characters', 'N/A')}\n")
            f.write(f"\nChapter Outlines:\n{prompt_vars.get('chapter_outlines', 'N/A')}\n")

            if prompt_vars.get('previous_context'):
                f.write(f"\nPrevious Context:\n{prompt_vars['previous_context']}\n")

        print(f"  💾 Prompt已保存: {prompt_file}")

    def parse_chapters_from_response(self, response_text, start_chapter, end_chapter):
        """从AI响应中解析章节内容"""
        chapters = {}

        # 使用正则匹配 Chapter X: 或 **Chapter X:** 格式
        pattern = r'(?:^|\n)(?:\*\*)?Chapter\s+(\d+):\s*([^\n]+)(?:\*\*)?(?:\n|$)(.*?)(?=(?:\n\*\*)?Chapter\s+\d+:|$)'

        matches = re.finditer(pattern, response_text, re.DOTALL | re.IGNORECASE)

        for match in matches:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            chapter_content = match.group(3).strip()

            if start_chapter <= chapter_num <= end_chapter:
                # 移除可能的元数据（---之后的内容）
                if '---' in chapter_content:
                    chapter_content = chapter_content.split('---')[0].strip()

                # 移除末尾的Character Count等元数据
                if 'Character Count:' in chapter_content:
                    chapter_content = chapter_content.split('Character Count:')[0].strip()

                chapters[chapter_num] = {
                    'title': chapter_title,
                    'content': chapter_content
                }

        return chapters

    def generate_batch(self, outline_data, batch_start, batch_end, previous_context=""):
        """生成一个批次的章节

        新的Prompt构建逻辑：
        1. 读取_writing_prompt.txt（世界观+角色）
        2. 如果有上一章，加载上一章的chapter_X_prompt.txt
        3. 加载当前批次所有章节的chapter_X_prompt.txt
        4. 如果有previous_context，添加前文最后2000字
        """
        outline = outline_data['outline']
        outline_folder = os.path.dirname(self.outline_file)

        # 1. 读取_writing_prompt.txt（世界观+角色）
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

        # 准备Prompt变量（用于日志记录）
        prompt_vars = {
            'genre': outline.get('genre', ''),
            'style': outline_data.get('style', ''),
            'base_prompt': base_prompt,
            'chapter_prompts': chapter_prompts,
            'start_chapter': batch_start,
            'end_chapter': batch_end,
            'previous_context': previous_context if previous_context else ""
        }

        # 保存Prompt日志（用于调试）
        self.save_prompt_log(batch_start, batch_end, full_prompt, prompt_vars)

        # 检测模型类型，决定使用哪种API调用方式
        model = self.config.get('model', 'gpt-4-turbo-preview')
        use_http_client = 'gemini' in model.lower() or 'gpt-5' in model.lower()

        if use_http_client:
            # 使用http.client方式（适合Gemini等模型）
            print(f"使用http.client方式调用模型 '{model}'...")
            result = call_api_with_http_client(
                api_key=self.config['api_key'],
                base_url=self.config.get('base_url', 'https://yunwuapi.com'),
                model=model,
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": f"请写作 Chapter {batch_start} - {batch_end}"}
                ],
                temperature=self.config.get('temperature', 0.8),
                max_tokens=self.config.get('max_tokens', 8000)
            )

            if not result['success']:
                raise Exception(f"API调用失败: {result['error']}\n详情: {result.get('details', 'N/A')}")

            result_text = result['content']

            # 更新统计（从usage中获取）
            if result.get('usage'):
                self.total_tokens += result['usage'].get('total_tokens', 0)
                # 估算费用（如果没有usage信息）
                prompt_tokens = result['usage'].get('prompt_tokens', 0)
                completion_tokens = result['usage'].get('completion_tokens', 0)
                if prompt_tokens > 0 and completion_tokens > 0:
                    self.total_cost += self.calculate_cost_from_tokens(prompt_tokens, completion_tokens)
        else:
            # 使用标准OpenAI客户端方式（只在需要时才初始化）
            print(f"使用标准OpenAI客户端调用模型 '{model}'...")

            # 初始化客户端（如果还没初始化）
            self.initialize_client()

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": f"请写作 Chapter {batch_start} - {batch_end}"}
                ],
                temperature=self.config.get('temperature', 0.8),
                max_tokens=self.config.get('max_tokens', 8000)
            )

            # 更新统计
            self.total_tokens += response.usage.total_tokens
            self.total_cost += self.calculate_cost(response.usage)

            # 获取响应内容
            result_text = response.choices[0].message.content

        # 解析章节（两种API调用方式都需要）
        chapters = self.parse_chapters_from_response(result_text, batch_start, batch_end)

        return chapters

    def calculate_cost(self, usage):
        """计算费用（示例定价）"""
        # 这里使用GPT-4 Turbo的定价作为示例
        input_cost = (usage.prompt_tokens / 1000) * 0.01
        output_cost = (usage.completion_tokens / 1000) * 0.03
        return input_cost + output_cost

    def calculate_cost_from_tokens(self, prompt_tokens, completion_tokens):
        """从token数计算费用"""
        input_cost = (prompt_tokens / 1000) * 0.01
        output_cost = (completion_tokens / 1000) * 0.03
        return input_cost + output_cost

    def validate_and_save_chapters(self, chapters):
        """验证并保存章节"""
        for chapter_num, chapter_data in chapters.items():
            content = chapter_data['content']

            # 验证字符数
            is_valid, char_count, message = validate_chapter_length(content, min_chars=9000)

            if not is_valid:
                print(f"警告: Chapter {chapter_num} {message}")
                # 如果字符数太少，可以选择重新生成或继续
                # 这里我们选择继续，但记录警告

            # 保存章节文件
            metadata = {
                'Character Count': char_count,
                'Generated At': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'Model': self.config.get('model', 'unknown'),
                'Valid': 'Yes' if is_valid else f'No - {message}'
            }

            save_chapter_file(self.project_folder, chapter_num, content, metadata)

            self.chapters_completed += 1

            print(f"✓ 保存 Chapter {chapter_num}: {char_count} 字符")

    def run(self):
        """运行写作进程"""
        try:
            print(f"任务 {self.task_id} 开始...")

            # 更新进度
            self.update_progress('initializing', message='初始化中...')

            # 加载大纲
            outline_data = self.load_outline()
            print("✓ 大纲加载完成")

            # 初始化项目
            self.initialize_project(outline_data)
            print(f"✓ 项目文件夹: {self.project_folder}")

            # 获取章节范围
            start_chapter, end_chapter = self.get_chapter_range()
            print(f"✓ 章节范围: {start_chapter}-{end_chapter}")

            if start_chapter > end_chapter:
                print("所有章节已完成！")
                self.update_progress('completed', current_chapter=end_chapter, message='所有章节已完成')
                return

            # 构建批次
            batches = self.build_chapter_batches(start_chapter, end_chapter)
            print(f"✓ 共{len(batches)}个批次")

            self.update_progress('in_progress', current_chapter=start_chapter, message=f'开始生成章节')

            # 逐批生成
            for i, (batch_start, batch_end) in enumerate(batches, 1):
                print(f"\n[批次 {i}/{len(batches)}] 生成 Chapter {batch_start}-{batch_end}...")

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

                print(f"✓ 批次 {i} 完成")

            # 完成
            self.update_progress(
                'completed',
                current_chapter=end_chapter,
                message=f'所有章节生成完成！共 {self.chapters_completed} 章'
            )

            print(f"\n✅ 任务完成！")
            print(f"   章节数: {self.chapters_completed}")
            print(f"   Token: {self.total_tokens}")
            print(f"   费用: ${self.total_cost:.2f}")
            print(f"   项目文件夹: {self.project_folder}")

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()

            self.update_progress('failed', message=f'错误: {str(e)}')


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='独立写作进程')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--task-id', required=True, help='任务ID')

    args = parser.parse_args()

    # 创建并运行worker
    worker = WriterWorker(args.config, args.task_id)
    worker.run()


if __name__ == '__main__':
    main()
