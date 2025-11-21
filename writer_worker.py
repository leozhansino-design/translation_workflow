#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小说生成独立进程（参考工作代码重写）
支持批次生成、断点续写、前文context
"""
import argparse
import json
import os
import sys
import http.client
import time
from datetime import datetime
from pathlib import Path


# 固定的SYSTEM_PROMPT
SYSTEM_PROMPT = """You are a web novel writer. Write addictive English web fiction.

【RULES】
1. English ONLY - No Chinese names/places
2. Each chapter: 15,000-20,000 words
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

        self.progress_file = f'tasks/{task_id}/progress.json'
        self.prompt_data = None
        self.output_folder = None

    def update_progress(self, status, message="", current_chapter=None, current_batch=None,
                       progress=0, output_folder=None):
        """更新进度文件"""
        progress_data = {
            'task_id': self.task_id,
            'status': status,
            'message': message,
            'updated_at': datetime.now().isoformat()
        }

        if current_chapter is not None:
            progress_data['current_chapter'] = current_chapter

        if current_batch is not None:
            progress_data['current_batch'] = current_batch

        if progress > 0:
            progress_data['progress'] = progress

        if output_folder:
            progress_data['output_folder'] = output_folder

        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

    def load_prompts(self):
        """加载prompt文件夹（参考用户代码）"""
        folder = Path(self.config['prompt_folder'])

        data = {
            'writing_prompt': '',
            'title': '',
            'category': '',
            'chapters': {}
        }

        # 读取_writing_prompt.txt（必需）
        with open(folder / '_writing_prompt.txt', 'r', encoding='utf-8') as f:
            data['writing_prompt'] = f.read().strip()

        print(f"✅ 加载: _writing_prompt.txt")

        # 读取可选文件
        title_file = folder / 'title.txt'
        if title_file.exists():
            with open(title_file, 'r', encoding='utf-8') as f:
                data['title'] = f.read().strip()
            print(f"✅ 加载: title.txt")

        category_file = folder / 'category.txt'
        if category_file.exists():
            with open(category_file, 'r', encoding='utf-8') as f:
                data['category'] = f.read().strip()
            print(f"✅ 加载: category.txt")

        # 读取所有章节prompts
        chapter_files = sorted(folder.glob('chapter_*_prompt.txt'))
        for chapter_file in chapter_files:
            filename = chapter_file.name
            try:
                chapter_num = int(filename.split('_')[1])
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    data['chapters'][chapter_num] = f.read().strip()
                print(f"✅ 加载: {filename} (第{chapter_num}章)")
            except (IndexError, ValueError):
                print(f"⚠️ 跳过无效文件: {filename}")

        print(f"\n📊 加载完成:")
        print(f"   - 总章节数: {len(data['chapters'])}")
        if data['title']:
            print(f"   - 书名: {data['title']}")
        if data['category']:
            print(f"   - 类型: {data['category']}")

        return data

    def call_api(self, system_prompt, user_prompt):
        """调用API（使用http.client）"""
        api_key = self.config['api_key']
        base_url = self.config['base_url']
        model = self.config['model']
        temperature = self.config.get('temperature', 0.85)
        max_tokens = self.config.get('max_tokens', 120000)

        # 解析base_url
        if base_url.startswith("https://"):
            host = base_url.replace("https://", "").rstrip("/")
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
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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

    def generate_batch(self, batch_num, chapter_nums, chapter_prompts, previous_context=""):
        """生成一批章节（参考用户代码）"""
        writing_prompt = self.prompt_data['writing_prompt']

        # 构建User Prompt
        user_parts = []

        # 1. 加上_writing_prompt（每次都要）
        user_parts.append("【写作要求】")
        user_parts.append(writing_prompt)
        user_parts.append("\n" + "="*60 + "\n")

        # 2. 如果有前文context，加上（第2批开始）
        if previous_context:
            user_parts.append("【前文结尾（保持连贯）】")
            user_parts.append(previous_context)
            user_parts.append("\n" + "="*60 + "\n")

        # 3. 加上本批次的章节prompts
        user_parts.append("【本批次章节大纲】")
        for ch_num, prompt in zip(chapter_nums, chapter_prompts):
            user_parts.append(f"\n===== 第{ch_num}章 =====")
            user_parts.append(prompt)

        user_parts.append("\n" + "="*60)
        user_parts.append(f"\n现在写第{chapter_nums[0]}-{chapter_nums[-1]}章。")
        user_parts.append(f"要求：每章15,000-20,000英文单词，只输出小说正文。")
        user_parts.append("\n开始写作：")

        user_prompt = "\n".join(user_parts)

        # 调用API
        result = self.call_api(SYSTEM_PROMPT, user_prompt)

        return result

    def check_resume_point(self):
        """检查断点续写位置"""
        if not self.output_folder or not os.path.exists(self.output_folder):
            return 1  # 从第1批开始

        # 查找已完成的批次文件
        max_batch = 0
        for f in os.listdir(self.output_folder):
            if f.startswith('batch_') and f.endswith('.txt'):
                try:
                    # batch_1_ch1-3.txt -> 1
                    num_str = f.split('_')[1]
                    num = int(num_str)
                    max_batch = max(max_batch, num)
                except:
                    continue

        if max_batch > 0:
            next_batch = max_batch + 1
            print(f"✓ 检测到已完成批次: 1-{max_batch}")
            print(f"✓ 从批次{next_batch}继续")
            return next_batch

        return 1

    def get_previous_context(self, batch_num):
        """获取前一批次的结尾1500字符"""
        if batch_num <= 1:
            return ""

        # 读取前一批次的文件
        prev_batch = batch_num - 1

        # 查找前一批次的文件
        for f in os.listdir(self.output_folder):
            if f.startswith(f'batch_{prev_batch}_') and f.endswith('.txt'):
                filepath = os.path.join(self.output_folder, f)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # 取最后1500个字符
                    return content[-1500:] if len(content) > 1500 else content

        return ""

    def run(self):
        """运行小说生成"""
        try:
            print(f"\n{'='*80}")
            print(f"小说生成任务 {self.task_id} 开始...")
            print(f"{'='*80}\n")

            self.update_progress('initializing', '初始化中...')

            # 加载prompts
            print("📂 加载prompts...")
            self.prompt_data = self.load_prompts()

            total_chapters = len(self.prompt_data['chapters'])
            batch_size = self.config['batch_size']
            batches_needed = (total_chapters + batch_size - 1) // batch_size

            title = self.prompt_data.get('title', 'Untitled')
            category = self.prompt_data.get('category', 'Fiction')

            print(f"\n📊 生成计划:")
            if title:
                print(f"   - 书名: {title}")
            if category:
                print(f"   - 类型: {category}")
            print(f"   - 总章节: {total_chapters}章")
            print(f"   - 批次大小: {batch_size}章/批")
            print(f"   - 预计批次: {batches_needed}批")
            print(f"   - 预计耗时: {batches_needed * 3}分钟")

            # 创建输出文件夹
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
            safe_title = safe_title.replace(' ', '_') if safe_title else 'Untitled'
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_folder = f"output/{safe_title}_{category}_{timestamp}"
            os.makedirs(self.output_folder, exist_ok=True)

            print(f"✓ 输出文件夹: {self.output_folder}")

            # 检查断点续写
            start_batch = self.check_resume_point()

            # 获取排序后的章节号列表
            chapter_nums = sorted(self.prompt_data['chapters'].keys())

            # 分批生成
            all_content = []
            previous_context = ""
            total_tokens = 0
            total_cost = 0

            # 如果是续写，加载previous_context
            if start_batch > 1:
                previous_context = self.get_previous_context(start_batch)
                print(f"✓ 加载前文context: {len(previous_context)}字符")

            print(f"\n{'='*80}")
            print(f"开始生成章节...")
            print(f"从批次{start_batch}开始，共{batches_needed}批")
            print(f"{'='*80}\n")

            for i in range((start_batch - 1) * batch_size, len(chapter_nums), batch_size):
                batch_num = (i // batch_size) + 1

                # 本批次的章节号
                batch_chapter_nums = chapter_nums[i:i+batch_size]
                start_ch = batch_chapter_nums[0]
                end_ch = batch_chapter_nums[-1]

                print(f"\n{'='*80}")
                print(f"📝 批次 {batch_num}/{batches_needed}: 第{start_ch}-{end_ch}章")
                print(f"{'='*80}")

                # 获取本批次的章节prompts
                batch_prompts = [self.prompt_data['chapters'][num] for num in batch_chapter_nums]

                # 显示发送内容
                print(f"📤 发送内容:")
                print(f"   - System Prompt: ✅ (固定)")
                print(f"   - Writing Prompt: ✅ (_writing_prompt.txt)")
                if previous_context:
                    print(f"   - 前文Context: ✅ (上批结尾1500字符)")
                print(f"   - 章节Prompts: 第{start_ch}-{end_ch}章")

                # 更新进度
                completed_batches = batch_num - 1
                progress_pct = int((completed_batches / batches_needed) * 100)

                self.update_progress(
                    'generating',
                    f'正在生成批次{batch_num}/{batches_needed}...',
                    current_chapter=start_ch,
                    current_batch=batch_num,
                    progress=progress_pct,
                    output_folder=self.output_folder
                )

                print(f"\n⏳ 正在生成第{start_ch}-{end_ch}章...\n")
                start_time = time.time()

                # 生成
                result = self.generate_batch(
                    batch_num,
                    batch_chapter_nums,
                    batch_prompts,
                    previous_context
                )

                elapsed = time.time() - start_time

                if result['success']:
                    content = result['content']
                    usage = result['usage']

                    # 统计
                    words = len(content.split())
                    tokens = usage.get('total_tokens', 0)
                    avg_words = words // len(batch_chapter_nums)

                    # 计算成本
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    input_cost = (prompt_tokens / 1_000_000) * 0.15
                    output_cost = (completion_tokens / 1_000_000) * 0.60
                    cost = input_cost + output_cost

                    total_tokens += tokens
                    total_cost += cost

                    print(f"✅ 第{start_ch}-{end_ch}章 生成完成！")
                    print(f"   ⏱️  耗时: {elapsed:.1f}秒")
                    print(f"   📊 总字数: {words:,} 词")
                    print(f"   📏 平均每章: {avg_words:,} 词")
                    print(f"   💰 Tokens: {tokens:,}")
                    print(f"   💵 成本: ${cost:.4f}")

                    # 检查字数
                    if avg_words < 12000:
                        print(f"   ⚠️  警告: 平均字数偏少 ({avg_words}/15,000)")

                    # 保存本批次
                    batch_filename = f"batch_{batch_num}_ch{start_ch}-{end_ch}.txt"
                    batch_filepath = os.path.join(self.output_folder, batch_filename)
                    with open(batch_filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"   📁 已保存: {batch_filename}")

                    # 添加到总内容
                    all_content.append(content)

                    # 提取结尾1500字符作为下一批的context
                    if batch_num < batches_needed:
                        previous_context = content[-1500:]
                        print(f"   🔗 提取结尾1500字符作为下批context")

                else:
                    print(f"❌ 生成失败: {result['error']}")
                    self.update_progress('failed', f"批次{batch_num}生成失败: {result['error']}")
                    return

                # 批次间延迟
                if batch_num < batches_needed:
                    print(f"\n⏸️  等待3秒...")
                    time.sleep(3)

            # 全部完成，合并保存
            if all_content:
                print(f"\n{'='*80}")
                print("📦 合并所有批次...")

                full_content = "\n\n".join(all_content)
                full_words = len(full_content.split())

                # 生成文件名
                filename = f"{safe_title}_complete.txt"
                final_path = os.path.join(self.output_folder, filename)

                # 保存
                with open(final_path, 'w', encoding='utf-8') as f:
                    # 添加元信息
                    if title:
                        f.write(f"Title: {title}\n")
                    if category:
                        f.write(f"Category: {category}\n")
                    f.write(f"\n{'='*80}\n\n")
                    f.write(full_content)

                print(f"\n✅ 全部完成！")
                print(f"{'='*80}")
                print(f"📊 最终统计:")
                print(f"   - 总章节: {total_chapters}章")
                print(f"   - 总字数: {full_words:,} 词")
                print(f"   - 平均每章: {full_words//total_chapters:,} 词")
                print(f"   - 总Tokens: {total_tokens:,}")
                print(f"   - 总成本: ${total_cost:.4f}")
                print(f"   - 完整版: {final_path}")
                print(f"{'='*80}\n")

                self.update_progress(
                    'completed',
                    f'所有章节生成完成！',
                    current_chapter=total_chapters,
                    current_batch=batches_needed,
                    progress=100,
                    output_folder=self.output_folder
                )

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.update_progress('failed', f'错误: {str(e)}')


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
