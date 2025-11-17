"""
翻译脚本基类
"""
import json
import sys
import os
import time
from openai import OpenAI

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.preprocessor import Preprocessor


class TranslatorWorker:
    """翻译工作器"""

    def __init__(self, worker_id: int, env: str = "windows1"):
        self.worker_id = worker_id
        self.env = env

        # 加载配置
        self.load_config()

        # 初始化API客户端
        self.client = OpenAI(
            api_key=self.api_config["api_key"],
            base_url=self.api_config["base_url"]
        )

        # 初始化管理器
        self.task_manager = TaskManager()

        # 根据环境选择names.json
        env_config_path = "config/env_config.json"
        with open(env_config_path, 'r', encoding='utf-8') as f:
            env_config = json.load(f)

        names_file = env_config["environments"][self.env]["names_file"]

        self.preprocessor = Preprocessor(
            names_file=names_file,
            styles_file="data/styles.json",
            base_prompt_file="config/base_prompt.txt"
        )

    def load_config(self):
        """加载配置"""
        with open("config/api_config.json", 'r', encoding='utf-8') as f:
            self.api_config = json.load(f)

    def run(self):
        """运行翻译工作器"""
        print(f"[Worker {self.worker_id}] 启动 (环境: {self.env})")

        while True:
            # 获取下一个任务
            task = self.task_manager.get_next_task()

            if not task:
                print(f"[Worker {self.worker_id}] 没有待处理任务，等待...")
                time.sleep(5)
                continue

            task_id = task["task_id"]
            print(f"[Worker {self.worker_id}] 获取任务: {task_id}")

            # 更新任务状态为处理中
            self.task_manager.update_task_status(
                task_id,
                "processing",
                worker_id=self.worker_id,
                started_at=time.time()
            )

            try:
                # 执行翻译
                self.translate_task(task)

                # 更新任务状态为完成
                self.task_manager.update_task_status(
                    task_id,
                    "completed",
                    completed_at=time.time()
                )
                print(f"[Worker {self.worker_id}] ✅ 任务完成: {task_id}")

            except Exception as e:
                print(f"[Worker {self.worker_id}] ❌ 任务失败: {task_id}")
                print(f"错误: {str(e)}")

                # 更新任务状态为失败
                self.task_manager.update_task_status(
                    task_id,
                    "failed",
                    error=str(e),
                    failed_at=time.time()
                )

            # 完成后退出（单任务模式）
            break

    def translate_task(self, task: dict):
        """
        翻译任务
        """
        task_id = task["task_id"]
        novel_path = task["novel_path"]
        genre = task["genre"]
        style_index = task["style_index"]
        output_dir = task["output_dir"]

        print(f"[Worker {self.worker_id}] 开始预处理...")

        # 预处理（提取人名、分配英文名、组装prompt）
        final_prompt, novel_content, name_mapping = self.preprocessor.preprocess_task(
            task_id, novel_path, genre, style_index
        )

        print(f"[Worker {self.worker_id}] 预处理完成，开始翻译...")

        # 发送翻译请求（流式接收）
        start_time = time.time()

        content_path = os.path.join(output_dir, "content.txt")

        with open(content_path, 'w', encoding='utf-8') as f:
            response = self.client.chat.completions.create(
                model=self.api_config["model"],
                messages=[
                    {"role": "system", "content": final_prompt},
                    {"role": "user", "content": novel_content}
                ],
                temperature=self.api_config["temperature"],
                max_tokens=self.api_config["max_tokens"],
                stream=True,
                timeout=self.api_config["timeout"]
            )

            print(f"[Worker {self.worker_id}] 开始接收流式输出...")

            chunk_count = 0
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    f.write(content)
                    f.flush()  # 实时写入
                    chunk_count += 1

                    if chunk_count % 100 == 0:
                        print(f"[Worker {self.worker_id}] 已接收 {chunk_count} 个块...")

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"[Worker {self.worker_id}] ✅ 翻译完成！")
        print(f"[Worker {self.worker_id}] 耗时: {elapsed:.2f} 秒")
        print(f"[Worker {self.worker_id}] 输出文件: {content_path}")


def main(worker_id: int, env: str = "windows1"):
    """主函数"""
    worker = TranslatorWorker(worker_id, env)
    worker.run()


if __name__ == "__main__":
    # 从命令行参数获取worker_id和环境
    if len(sys.argv) >= 2:
        worker_id = int(sys.argv[1])
        env = sys.argv[2] if len(sys.argv) >= 3 else "windows1"
        main(worker_id, env)
    else:
        print("用法: python translator_base.py <worker_id> [environment]")
        print("例如: python translator_base.py 1 windows1")
