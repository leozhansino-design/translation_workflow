#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成独立进程（完全重写版本）
作为独立进程运行，负责生成小说章节
"""
import argparse
import json
import os
import sys
import http.client
import time
from datetime import datetime
from pathlib import Path

from prompt_manager import PromptManager


# 你提供的核心SYSTEM_PROMPT
SYSTEM_PROMPT = """You are a web novel writer. Write addictive English web fiction.

【RULES】
1. English ONLY - No Chinese names/places
2. Each chapter: 8,000-12,000 characters
3. Include 3-5 "爽点" per chapter:
   - Victories, face-slapping, power-ups
   - Romantic moments, revelations
   - Plot twists, justice served

【STYLE: 短平快】
- Short sentences (10-15 words)
- Short paragraphs (1-3 sentences)
- Fast pacing (event every 200-300 words)
- Mobile-friendly

【STRUCTURE】
Opening: Action/tension immediately
Development: 2-3 scenes with 爽点
Climax: Biggest 爽点
Hook: Cliffhanger ending

【LOCALIZATION】
Names: Emma, Lucas, Ethan (Western)
Places: Manhattan, London, Seattle
Culture: Western only

【DIALOGUE】
Short, punchy exchanges:
"You're fired." He grinned.
She smiled. "Check your email."
His face went pale.

Write addictive entertainment. START NOW."""


class WriterWorker:
    """小说生成工作进程"""

    def __init__(self, config_file, task_id):
        self.config_file = config_file
        self.task_id = task_id

        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化
        self.prompt_mgr = PromptManager()
        self.progress_file = f'tasks/{task_id}/progress.json'
        self.outline_data = None
        self.output_folder = None

    def update_progress(self, status, message="", current_chapter=None, progress=0, output_folder=None):
        """更新进度文件"""
        progress_data = {
            'task_id': self.task_id,
            'status': status,
            'message': message,
            'updated_at': datetime.now().isoformat()
        }

        if current_chapter is not None:
            progress_data['current_chapter'] = current_chapter

        if progress > 0:
            progress_data['progress'] = progress

        if output_folder:
            progress_data['output_folder'] = output_folder

        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

    def call_api(self, prompt, user_message):
        """调用API（使用http.client，参考你的代码）"""
        api_key = self.config['api_key']
        base_url = self.config['base_url']
        model = self.config['model']
        temperature = self.config.get('temperature', 0.85)
        max_tokens = self.config.get('max_tokens', 32000)

        # 解析base_url
        if base_url.startswith("https://"):
            host = base_url.replace("https://", "").rstrip("/")
            # 检查是否已包含路径
            if "/v1" in host:
                path = "/chat/completions"
                host = host.split("/v1")[0]
            else:
                path = "/v1/chat/completions"
        else:
            host = base_url.replace("http://", "").rstrip("/")
            if "/v1" in host:
                path = "/chat/completions"
                host = host.split("/v1")[0]
            else:
                path = "/v1/chat/completions"

        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        conn = http.client.HTTPSConnection(host)

        try:
            conn.request("POST", path, payload, headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')

            if response.status == 200:
                result = json.loads(data)
                content = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                return {'success': True, 'content': content, 'usage': usage}
            else:
                return {'success': False, 'error': f"HTTP {response.status}: {data}"}

        except Exception as e:
            return {'success': False, 'error': f"请求失败: {str(e)}"}
        finally:
            conn.close()

    def build_chapter_prompt(self, chapter_num, title, genre, outline, previous_context=None):
        """构建章节提示词（参考你的代码）"""
        prompt = f"""{SYSTEM_PROMPT}

Write Chapter {chapter_num} of "{title}" ({genre}).

Chapter {chapter_num} Outline:
{outline}

Requirements:
- 8,000-12,000 characters
- 3-5 爽点
- Short-sharp-fast
- Western names only
- Cliffhanger ending
"""

        if previous_context:
            prompt += f"\n【Previous Context】\n{previous_context}\n"

        prompt += f"\nWrite Chapter {chapter_num} now."

        return prompt

    def check_resume_point(self):
        """检查断点续写位置"""
        if not self.output_folder or not os.path.exists(self.output_folder):
            return self.config['start_chapter']

        # 查找已完成的章节
        max_chapter = 0
        for f in os.listdir(self.output_folder):
            if f.startswith('ch') and f.endswith('.txt'):
                try:
                    num_str = f.replace('ch', '').replace('.txt', '')
                    num = int(num_str)
                    max_chapter = max(max_chapter, num)
                except:
                    continue

        # 如果有已完成的章节，从下一章继续
        if max_chapter > 0:
            next_chapter = max_chapter + 1
            print(f"✓ 检测到已完成章节: 第1-{max_chapter}章")
            print(f"✓ 从第{next_chapter}章继续")
            return next_chapter

        return self.config['start_chapter']

    def generate_chapter(self, chapter_num, outline_chapter):
        """生成单个章节"""
        outline = self.outline_data.get('outline', {})
        title = outline.get('title', 'Untitled')
        genre = outline.get('genre', 'Fiction')

        # 构建章节大纲文本
        chapter_outline = f"""Chapter {chapter_num}: {outline_chapter.get('title', '')}

Summary: {outline_chapter.get('summary', '')}

Key Events: {', '.join(outline_chapter.get('key_events', []))}

Characters Involved: {', '.join(outline_chapter.get('characters_involved', []))}"""

        # 获取前文上下文（可选，用于连贯性）
        previous_context = self.get_previous_context(chapter_num)

        # 构建prompt
        prompt = self.build_chapter_prompt(
            chapter_num, title, genre, chapter_outline, previous_context
        )

        # 调用API
        result = self.call_api(prompt, chapter_outline)

        return result

    def get_previous_context(self, current_chapter):
        """获取前文上下文（用于连贯性）"""
        if current_chapter <= 1:
            return None

        # 读取前一章的部分内容作为上下文
        prev_file = os.path.join(self.output_folder, f"ch{current_chapter - 1}.txt")
        if os.path.exists(prev_file):
            with open(prev_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 取最后500个字符作为上下文
                return content[-500:] if len(content) > 500 else content

        return None

    def save_chapter(self, chapter_num, content):
        """保存章节"""
        filename = f"ch{chapter_num}.txt"
        filepath = os.path.join(self.output_folder, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def run(self):
        """运行小说生成"""
        try:
            print(f"\n{'='*70}")
            print(f"小说生成任务 {self.task_id} 开始...")
            print(f"{'='*70}\n")

            self.update_progress('initializing', '初始化中...')

            # 加载大纲数据
            outline_file = self.config['outline_file']
            with open(outline_file, 'r', encoding='utf-8') as f:
                self.outline_data = json.load(f)

            outline = self.outline_data.get('outline', {})
            title = outline.get('title', 'Untitled')
            genre = outline.get('genre', 'Fiction')
            chapter_outlines = outline.get('chapter_outlines', [])

            print(f"✓ 大纲已加载")
            print(f"  书名: {title}")
            print(f"  类型: {genre}")
            print(f"  总章节: {len(chapter_outlines)}章")

            # 创建输出文件夹
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
            safe_title = safe_title.replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_folder = f"projects/Project_{safe_title}_{genre}_{timestamp}"
            os.makedirs(self.output_folder, exist_ok=True)

            print(f"✓ 输出文件夹: {self.output_folder}")

            # 保存元数据文件
            self.save_metadata()

            # 检查断点续写
            start_chapter = self.check_resume_point()
            end_chapter = self.config['end_chapter']

            print(f"\n{'='*70}")
            print(f"开始生成章节...")
            print(f"范围: 第{start_chapter}章 - 第{end_chapter}章")
            print(f"{'='*70}\n")

            # 生成章节
            for current_chapter in range(start_chapter, end_chapter + 1):
                # 找到对应的章节大纲
                outline_chapter = None
                for ch in chapter_outlines:
                    if ch.get('chapter_number') == current_chapter:
                        outline_chapter = ch
                        break

                if not outline_chapter:
                    print(f"⚠️ 警告: 第{current_chapter}章的大纲不存在，跳过")
                    continue

                # 更新进度
                total_chapters = end_chapter - start_chapter + 1
                completed = current_chapter - start_chapter
                progress_pct = int((completed / total_chapters) * 100)

                self.update_progress(
                    'generating',
                    f'正在生成第{current_chapter}章...',
                    current_chapter=current_chapter,
                    progress=progress_pct,
                    output_folder=self.output_folder
                )

                print(f"📝 生成第{current_chapter}章: {outline_chapter.get('title', '')}...")
                start_time = time.time()

                # 生成章节
                result = self.generate_chapter(current_chapter, outline_chapter)

                if result['success']:
                    content = result['content']
                    char_count = len(content)
                    elapsed = time.time() - start_time

                    # 保存章节
                    filepath = self.save_chapter(current_chapter, content)

                    print(f"   ✅ 完成 | {char_count:,} 字符 | {elapsed:.1f}秒")

                    # 检查字符数是否符合要求
                    if 8000 <= char_count <= 12000:
                        print(f"   ✓ 字符数符合要求")
                    else:
                        print(f"   ⚠️ 字符数不符合要求 (8000-12000)")

                else:
                    print(f"   ❌ 失败: {result['error']}")
                    self.update_progress('failed', f"第{current_chapter}章生成失败: {result['error']}")
                    return

                # 等待一秒避免API限流
                time.sleep(1)

            # 全部完成
            self.update_progress(
                'completed',
                f'所有章节生成完成！',
                current_chapter=end_chapter,
                progress=100,
                output_folder=self.output_folder
            )

            print(f"\n{'='*70}")
            print(f"✅ 任务完成！")
            print(f"   输出目录: {self.output_folder}")
            print(f"   章节数: {end_chapter - start_chapter + 1}")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.update_progress('failed', f'错误: {str(e)}')

    def save_metadata(self):
        """保存元数据文件"""
        outline = self.outline_data.get('outline', {})

        # title.txt
        with open(os.path.join(self.output_folder, 'title.txt'), 'w', encoding='utf-8') as f:
            f.write(outline.get('title', 'Untitled'))

        # blurb.txt
        with open(os.path.join(self.output_folder, 'blurb.txt'), 'w', encoding='utf-8') as f:
            f.write(outline.get('blurb', ''))

        # category.txt
        with open(os.path.join(self.output_folder, 'category.txt'), 'w', encoding='utf-8') as f:
            f.write(outline.get('genre', 'Fiction'))

        # tags.txt
        with open(os.path.join(self.output_folder, 'tags.txt'), 'w', encoding='utf-8') as f:
            tags = outline.get('tags', [])
            f.write('\n'.join(tags))

        # age.txt
        with open(os.path.join(self.output_folder, 'age.txt'), 'w', encoding='utf-8') as f:
            f.write(outline.get('age_category', 'Adult'))

        print(f"✓ 元数据文件已保存")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='小说生成独立进程')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--task-id', required=True, help='任务ID')

    args = parser.parse_args()

    # 创建并运行worker
    worker = WriterWorker(args.config, args.task_id)
    worker.run()


if __name__ == '__main__':
    main()
