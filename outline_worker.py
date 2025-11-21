"""
大纲生成独立进程
作为独立进程运行，负责生成单个大纲
"""
import argparse
import json
import os
import sys
from datetime import datetime
from openai import OpenAI

from resource_mgr import ResourceManager
from prompt_manager import PromptManager
from utils import (
    extract_genre_from_filename,
    extract_title_from_filename,
    parse_json_from_llm_response,
    call_api_with_http_client
)


class OutlineWorker:
    """大纲生成工作进程"""

    def __init__(self, config_file, task_id):
        self.config_file = config_file
        self.task_id = task_id

        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化
        self.resource_mgr = ResourceManager()
        self.prompt_mgr = PromptManager()
        self.client = None
        self.progress_file = f'tasks/{task_id}/progress.json'

    def update_progress(self, status, message=""):
        """更新进度文件"""
        progress = {
            'task_id': self.task_id,
            'status': status,
            'message': message,
            'updated_at': datetime.now().isoformat()
        }

        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    def run(self):
        """运行大纲生成"""
        try:
            print(f"大纲生成任务 {self.task_id} 开始...")

            # 更新进度
            self.update_progress('initializing', '初始化中...')

            # 读取文件
            source_file = self.config['source_file']
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"✓ 文件读取完成: {os.path.basename(source_file)}")

            # 提取类型和书名
            genre = extract_genre_from_filename(source_file)
            original_title = extract_title_from_filename(source_file)

            print(f"✓ 类型: {genre}")
            print(f"✓ 书名: {original_title}")

            # 选择人名
            male_count = self.config.get('male_count', 10)
            female_count = self.config.get('female_count', 10)
            selected_names = self.resource_mgr.select_names(male_count, female_count)
            names_formatted = self.resource_mgr.format_names_for_prompt(selected_names)

            print(f"✓ 选择人名: {male_count}个男性, {female_count}个女性")

            # 选择风格
            genre_data = self.resource_mgr.styles[genre]
            counts = genre_data['used']
            min_idx = counts.index(min(counts))
            style = genre_data['styles'][min_idx]
            author = genre_data['authors'][min_idx]

            # 更新风格使用次数
            self.resource_mgr.styles[genre]['used'][min_idx] += 1
            self.resource_mgr.save_styles()

            print(f"✓ 选择风格: {author}")

            # 构建Prompt变量
            start_ch = self.config.get('start_chapter', 1)
            end_ch = self.config.get('end_chapter', 100)
            total_chapters = end_ch - start_ch + 1

            prompt_vars = {
                'genre': genre,
                'male_names': names_formatted['male_names'],
                'female_names': names_formatted['female_names'],
                'style': style,
                'start_chapter': start_ch,
                'end_chapter': end_ch,
                'total_chapters': total_chapters
            }

            # 渲染Prompt
            system_prompt = self.prompt_mgr.render_outline_prompt(prompt_vars)

            # 保存Prompt到文件（用于调试）
            prompt_file = f'tasks/{self.task_id}/prompt.txt'
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"{'='*70}\n")
                f.write(f"大纲生成 Prompt\n")
                f.write(f"{'='*70}\n\n")
                f.write(f"System Message:\n\n{system_prompt}\n\n")
                f.write(f"{'='*70}\n\n")
                f.write(f"User Message:\n\n原文内容：\n{content[:1000]}...\n")

            print(f"✓ Prompt准备完成（已保存到 {prompt_file}）")

            self.update_progress('generating', '正在调用AI生成大纲...')

            # 初始化客户端
            self.client = OpenAI(
                api_key=self.config['api_key'],
                base_url=self.config.get('base_url', 'https://api.openai.com/v1/')
            )

            print("✓ API客户端初始化完成")
            print("正在调用AI...")

            # 检测模型类型，决定使用哪种API调用方式
            model = self.config.get('model', 'gpt-4-turbo-preview')
            use_http_client = 'gemini' in model.lower() or 'gpt-5' in model.lower()

            if use_http_client:
                # 使用http.client方式（适合Gemini等模型）
                print(f"检测到特殊模型 '{model}'，使用http.client方式调用API...")
                result = call_api_with_http_client(
                    api_key=self.config['api_key'],
                    base_url=self.config.get('base_url', 'https://api.openai.com/v1/'),
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"原文内容：\n\n{content}"}
                    ],
                    temperature=self.config.get('temperature', 0.8),
                    max_tokens=self.config.get('max_tokens', 8000)
                )

                if not result['success']:
                    raise Exception(f"API调用失败: {result['error']}\n详情: {result.get('details', 'N/A')}")

                result_text = result['content']
            else:
                # 使用标准OpenAI客户端方式
                print(f"使用标准OpenAI客户端调用模型 '{model}'...")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"原文内容：\n\n{content}"}
                    ],
                    temperature=self.config.get('temperature', 0.8),
                    max_tokens=self.config.get('max_tokens', 8000)
                )

                result_text = response.choices[0].message.content

            print("✓ AI响应完成")

            # 解析JSON
            try:
                outline = parse_json_from_llm_response(result_text)

                # 保存大纲数据
                outline_data = {
                    'outline': outline,
                    'source_file': source_file,
                    'original_title': original_title,
                    'chapter_range': [start_ch, end_ch],
                    'genre': genre,
                    'selected_names': selected_names,
                    'style': style,
                    'author': author,
                    'created_at': datetime.now().isoformat(),
                    'tokens_used': response.usage.total_tokens,
                    'cost': (response.usage.prompt_tokens / 1000) * 0.01 + (response.usage.completion_tokens / 1000) * 0.03
                }

                # 保存JSON文件
                os.makedirs('outlines', exist_ok=True)
                safe_title = "".join(c for c in outline['title'] if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.replace(' ', '_')

                json_filename = f"outlines/{safe_title}_Outline.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(outline_data, f, indent=2, ensure_ascii=False)

                # 生成文本格式
                txt_filename = f"outlines/{safe_title}_Outline.txt"
                txt_content = self.generate_outline_text(outline_data)
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(txt_content)

                print(f"✓ 大纲已保存:")
                print(f"  - {json_filename}")
                print(f"  - {txt_filename}")

                self.update_progress('completed', f'大纲生成成功！\n文件: {json_filename}')

                print(f"\n✅ 任务完成！")
                print(f"   书名: {outline['title']}")
                print(f"   类型: {outline['genre']}")
                print(f"   章节: {len(outline.get('chapter_outlines', []))}章")
                print(f"   Token: {response.usage.total_tokens:,}")
                print(f"   费用: ${outline_data['cost']:.2f}")

            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析失败: {str(e)}")
                # 保存原始响应
                raw_file = f'tasks/{self.task_id}/raw_response.txt'
                with open(raw_file, 'w', encoding='utf-8') as f:
                    f.write(result_text)
                self.update_progress('failed', f'JSON解析失败，原始响应已保存到 {raw_file}')

        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            self.update_progress('failed', f'错误: {str(e)}')

    def generate_outline_text(self, data):
        """生成格式化的大纲文本"""
        outline = data['outline']

        text = f"""{'='*70}
BOOK METADATA
{'='*70}
Original Title: {data['original_title']}
English Title: {outline['title']}
Genre: {outline['genre']}
Age Category: {outline.get('age_category', 'N/A')}
Chapter Range: {data['chapter_range'][0]}-{data['chapter_range'][1]}
Total Chapters: {len(outline.get('chapter_outlines', []))}

Blurb:
{outline.get('blurb', '')}

Tags:
{' '.join(outline.get('tags', []))}

{'='*70}
WORLD BUILDING
{'='*70}
{outline.get('world_setting', '')}

{'='*70}
CHARACTERS
{'='*70}
"""
        for i, char in enumerate(outline.get('main_characters', []), 1):
            text += f"\n{i}. {char['name']} ({char['gender']})\n"
            text += f"   Role: {char['role']}\n"
            text += f"   Personality: {char.get('personality', '')}\n"
            text += f"   Background: {char.get('background', '')}\n"

        text += f"\n{'='*70}\n"
        text += "WRITING STYLE\n"
        text += f"{'='*70}\n"
        text += f"Style: {data['author']}\n"
        text += f"Description: {data['style']}\n"

        text += f"\n{'='*70}\n"
        text += "CHAPTER OUTLINE\n"
        text += f"{'='*70}\n"

        for ch in outline.get('chapter_outlines', []):
            text += f"\nChapter {ch['chapter_number']}: {ch['title']}\n"
            text += f"- Plot: {ch.get('summary', '')}\n"
            if ch.get('key_events'):
                text += f"- Key Events: {', '.join(ch['key_events'])}\n"
            if ch.get('characters_involved'):
                text += f"- Characters: {', '.join(ch['characters_involved'])}\n"

        return text


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='大纲生成独立进程')
    parser.add_argument('--config', required=True, help='配置文件路径')
    parser.add_argument('--task-id', required=True, help='任务ID')

    args = parser.parse_args()

    # 创建并运行worker
    worker = OutlineWorker(args.config, args.task_id)
    worker.run()


if __name__ == '__main__':
    main()
