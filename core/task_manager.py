"""
任务管理模块
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, Optional


class TaskManager:
    """任务管理器"""

    def __init__(self, queue_file: str = "queue/tasks.json"):
        self.queue_file = queue_file
        self._ensure_queue_file()

    def _ensure_queue_file(self):
        """确保队列文件存在"""
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump({"tasks": []}, f, indent=2)

    def create_task(self, novel_path: str, genre: str, style_index: int) -> str:
        """
        创建新任务
        返回：task_id
        """
        # 生成任务ID（时间戳）
        task_id = f"task_{int(time.time() * 1000)}"

        # 创建任务输出目录
        output_dir = f"outputs/{task_id}"
        os.makedirs(output_dir, exist_ok=True)

        # 任务信息
        task_info = {
            "task_id": task_id,
            "novel_path": novel_path,
            "genre": genre,
            "style_index": style_index,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "output_dir": output_dir
        }

        # 保存任务信息
        task_info_path = os.path.join(output_dir, "task_info.json")
        with open(task_info_path, 'w', encoding='utf-8') as f:
            json.dump(task_info, f, indent=2, ensure_ascii=False)

        # 添加到队列
        self._add_to_queue(task_info)

        return task_id

    def _add_to_queue(self, task_info: Dict):
        """添加任务到队列"""
        with open(self.queue_file, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data["tasks"].append(task_info)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_next_task(self) -> Optional[Dict]:
        """获取下一个待处理任务"""
        with open(self.queue_file, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            tasks = data.get("tasks", [])

            # 找到第一个pending任务
            for task in tasks:
                if task["status"] == "pending":
                    return task

        return None

    def update_task_status(self, task_id: str, status: str, **kwargs):
        """
        更新任务状态
        status: pending, processing, completed, failed
        """
        # 更新队列文件
        with open(self.queue_file, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            tasks = data.get("tasks", [])

            for task in tasks:
                if task["task_id"] == task_id:
                    task["status"] = status
                    task["updated_at"] = datetime.now().isoformat()
                    task.update(kwargs)
                    break

            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 更新任务信息文件
        task_info_path = f"outputs/{task_id}/task_info.json"
        if os.path.exists(task_info_path):
            with open(task_info_path, 'r+', encoding='utf-8') as f:
                task_info = json.load(f)
                task_info["status"] = status
                task_info["updated_at"] = datetime.now().isoformat()
                task_info.update(kwargs)
                f.seek(0)
                f.truncate()
                json.dump(task_info, f, indent=2, ensure_ascii=False)

    def remove_task(self, task_id: str):
        """从队列中移除任务"""
        with open(self.queue_file, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            tasks = data.get("tasks", [])
            data["tasks"] = [t for t in tasks if t["task_id"] != task_id]
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        task_info_path = f"outputs/{task_id}/task_info.json"
        if os.path.exists(task_info_path):
            with open(task_info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
