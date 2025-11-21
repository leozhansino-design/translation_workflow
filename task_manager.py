"""
任务管理模块
负责创建、监控、管理写作任务
"""
import os
import json
import subprocess
import sys
from datetime import datetime
import uuid


TASKS_DIR = 'tasks'


class TaskManager:
    """任务管理器"""

    def __init__(self):
        os.makedirs(TASKS_DIR, exist_ok=True)

    def create_task(self, outline_file, config):
        """创建新的写作任务

        Args:
            outline_file: 大纲JSON文件路径
            config: 任务配置字典
                {
                    'api_key': 'sk-xxx',
                    'base_url': 'https://...',
                    'model': 'gpt-4-turbo-preview',
                    'temperature': 0.8,
                    'max_tokens': 8000,
                    'batch_size': 3,
                    'target_chapters': 100,
                    'project_folder': 'path/to/project' (可选，用于续写)
                }

        Returns:
            task_id: 任务ID
        """
        # 生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        # 创建任务文件夹
        task_dir = os.path.join(TASKS_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 合并配置
        task_config = {
            'task_id': task_id,
            'outline_file': outline_file,
            'created_at': datetime.now().isoformat(),
            **config
        }

        # 保存配置文件
        config_file = os.path.join(task_dir, 'config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(task_config, f, indent=2, ensure_ascii=False)

        # 创建初始进度文件
        progress_file = os.path.join(task_dir, 'progress.json')
        progress = {
            'task_id': task_id,
            'status': 'pending',
            'current_chapter': 0,
            'target_chapters': config.get('target_chapters', 0),
            'chapters_completed': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'message': '等待启动',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

        return task_id

    def start_task(self, task_id):
        """启动任务（作为独立进程）

        Args:
            task_id: 任务ID

        Returns:
            process: subprocess.Popen对象
        """
        task_dir = os.path.join(TASKS_DIR, task_id)
        config_file = os.path.join(task_dir, 'config.json')

        if not os.path.exists(config_file):
            raise ValueError(f"任务配置文件不存在: {task_id}")

        # 启动writer_worker.py作为独立进程
        python_exe = sys.executable

        process = subprocess.Popen([
            python_exe,
            'writer_worker.py',
            '--config', config_file,
            '--task-id', task_id
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 保存进程ID
        pid_file = os.path.join(task_dir, 'pid.txt')
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))

        return process

    def get_task_progress(self, task_id):
        """获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            进度字典，如果任务不存在返回None
        """
        progress_file = os.path.join(TASKS_DIR, task_id, 'progress.json')

        if not os.path.exists(progress_file):
            return None

        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_task_config(self, task_id):
        """获取任务配置

        Args:
            task_id: 任务ID

        Returns:
            配置字典
        """
        config_file = os.path.join(TASKS_DIR, task_id, 'config.json')

        if not os.path.exists(config_file):
            return None

        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_all_tasks(self):
        """列出所有任务

        Returns:
            任务列表 [{'task_id': ..., 'progress': ..., 'config': ...}, ...]
        """
        tasks = []

        if not os.path.exists(TASKS_DIR):
            return tasks

        for task_id in os.listdir(TASKS_DIR):
            task_dir = os.path.join(TASKS_DIR, task_id)
            if os.path.isdir(task_dir):
                progress = self.get_task_progress(task_id)
                config = self.get_task_config(task_id)

                if progress and config:
                    tasks.append({
                        'task_id': task_id,
                        'progress': progress,
                        'config': config
                    })

        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda x: x['progress'].get('created_at', ''), reverse=True)

        return tasks

    def delete_task(self, task_id):
        """删除任务

        Args:
            task_id: 任务ID
        """
        import shutil

        task_dir = os.path.join(TASKS_DIR, task_id)
        if os.path.exists(task_dir):
            shutil.rmtree(task_dir)

    def get_task_pid(self, task_id):
        """获取任务进程ID

        Args:
            task_id: 任务ID

        Returns:
            进程ID，如果不存在返回None
        """
        pid_file = os.path.join(TASKS_DIR, task_id, 'pid.txt')

        if not os.path.exists(pid_file):
            return None

        with open(pid_file, 'r') as f:
            return int(f.read().strip())

    def is_task_running(self, task_id):
        """检查任务是否正在运行

        Args:
            task_id: 任务ID

        Returns:
            布尔值
        """
        pid = self.get_task_pid(task_id)
        if pid is None:
            return False

        # 检查进程是否存在
        try:
            os.kill(pid, 0)  # 发送信号0不会杀死进程，只是检查是否存在
            return True
        except OSError:
            return False

    def stop_task(self, task_id):
        """停止任务

        Args:
            task_id: 任务ID
        """
        pid = self.get_task_pid(task_id)
        if pid:
            try:
                os.kill(pid, 15)  # SIGTERM
                return True
            except OSError:
                return False
        return False

    def get_task_summary(self, task_id):
        """获取任务摘要信息（用于显示在列表中）

        Args:
            task_id: 任务ID

        Returns:
            摘要字典
        """
        progress = self.get_task_progress(task_id)
        config = self.get_task_config(task_id)

        if not progress or not config:
            return None

        # 加载大纲获取书名
        outline_file = config.get('outline_file', '')
        title = "未知"

        if os.path.exists(outline_file):
            try:
                with open(outline_file, 'r', encoding='utf-8') as f:
                    outline_data = json.load(f)
                    title = outline_data.get('outline', {}).get('title', '未知')
            except:
                pass

        return {
            'task_id': task_id,
            'title': title,
            'status': progress.get('status', 'unknown'),
            'current_chapter': progress.get('current_chapter', 0),
            'target_chapters': progress.get('target_chapters', 0),
            'progress_percent': (progress.get('current_chapter', 0) / max(progress.get('target_chapters', 1), 1)) * 100,
            'total_cost': progress.get('total_cost', 0.0),
            'created_at': progress.get('created_at', ''),
            'updated_at': progress.get('updated_at', ''),
            'started_at': progress.get('started_at', ''),
            'model': config.get('model', 'N/A'),
            'is_running': self.is_task_running(task_id)
        }
