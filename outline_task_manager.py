"""
大纲生成任务管理器
支持多个大纲生成任务并行运行
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os
import json
import subprocess
import sys
import uuid
from datetime import datetime

from config import config
from utils import extract_genre_from_filename, validate_genre
from resource_mgr import ResourceManager


class OutlineTaskManager:
    """大纲任务管理器主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("大纲生成任务管理器")
        self.window.geometry("1000x700")

        self.resource_mgr = ResourceManager()
        self.tasks = []
        self.selected_task_id = None
        self.polling = False

        # 初始化界面
        self.setup_ui()
        self.refresh_tasks()
        self.start_polling()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
        title_frame = tk.Frame(self.window, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📝 大纲生成任务管理器",
            font=("Arial", 20, "bold"),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="支持多任务并行生成",
            font=("Arial", 11),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # === 工具栏 ===
        toolbar = tk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            toolbar,
            text="➕ 新建大纲任务",
            command=self.create_new_task,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="🔄 刷新",
            command=self.refresh_tasks,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            toolbar,
            text="🗑️ 删除任务",
            command=self.delete_selected_task,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # === 任务列表 ===
        list_frame = tk.LabelFrame(self.window, text="任务列表", padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建Treeview
        columns = ('状态', '书名', '类型', '更新时间')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # 设置列
        self.task_tree.heading('状态', text='状态')
        self.task_tree.heading('书名', text='书名')
        self.task_tree.heading('类型', text='类型')
        self.task_tree.heading('更新时间', text='更新时间')

        self.task_tree.column('状态', width=120)
        self.task_tree.column('书名', width=400)
        self.task_tree.column('类型', width=120)
        self.task_tree.column('更新时间', width=200)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscroll=scrollbar.set)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_selected)
        self.task_tree.bind('<Double-1>', self.open_task_detail)

        # === 详情面板 ===
        detail_frame = tk.LabelFrame(self.window, text="任务详情", padx=10, pady=10)
        detail_frame.pack(fill=tk.X, padx=10, pady=10)

        self.detail_text = scrolledtext.ScrolledText(
            detail_frame,
            height=8,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

    def refresh_tasks(self):
        """刷新任务列表"""
        # 清空现有列表
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # 获取所有任务
        tasks_dir = 'tasks'
        if not os.path.exists(tasks_dir):
            return

        self.tasks = []

        for task_id in os.listdir(tasks_dir):
            task_dir = os.path.join(tasks_dir, task_id)
            if os.path.isdir(task_dir):
                progress_file = os.path.join(task_dir, 'progress.json')
                config_file = os.path.join(task_dir, 'config.json')

                if os.path.exists(progress_file) and os.path.exists(config_file):
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress = json.load(f)

                    with open(config_file, 'r', encoding='utf-8') as f:
                        task_config = json.load(f)

                    # 只显示大纲生成任务
                    if task_config.get('task_type') == 'outline':
                        self.tasks.append({
                            'task_id': task_id,
                            'progress': progress,
                            'config': task_config
                        })

        # 填充列表
        for task_data in self.tasks:
            progress = task_data['progress']
            task_config = task_data['config']

            status_icon = self.get_status_icon(progress.get('status', 'unknown'))
            status_text = f"{status_icon} {progress.get('status', 'unknown')}"

            book_name = os.path.basename(task_config.get('source_file', '未知'))
            genre = task_config.get('genre', 'N/A')
            updated_time = progress.get('updated_at', '')[:19]

            self.task_tree.insert('', tk.END, iid=task_data['task_id'], values=(
                status_text,
                book_name,
                genre,
                updated_time
            ))

    def get_status_icon(self, status):
        """获取状态图标"""
        icons = {
            'pending': '⏸️',
            'initializing': '🔄',
            'generating': '🔄',
            'completed': '✅',
            'failed': '❌'
        }
        return icons.get(status, '❓')

    def on_task_selected(self, event):
        """任务选择事件"""
        selection = self.task_tree.selection()
        if not selection:
            return

        task_id = selection[0]
        self.selected_task_id = task_id
        self.show_task_detail(task_id)

    def show_task_detail(self, task_id):
        """显示任务详情"""
        task_data = next((t for t in self.tasks if t['task_id'] == task_id), None)
        if not task_data:
            return

        progress = task_data['progress']
        task_config = task_data['config']

        detail = f"""
{'='*70}
任务ID: {task_id}
文件: {os.path.basename(task_config.get('source_file', '未知'))}
类型: {task_config.get('genre', 'N/A')}
状态: {progress.get('status', 'unknown')}
{'='*70}

配置信息:
- 章节范围: {task_config.get('start_chapter', 1)}-{task_config.get('end_chapter', 100)}
- 男性人名数: {task_config.get('male_count', 10)}
- 女性人名数: {task_config.get('female_count', 10)}
- 模型: {task_config.get('model', 'N/A')}
- Temperature: {task_config.get('temperature', 0.8)}

时间信息:
- 创建时间: {task_config.get('created_at', 'N/A')[:19]}
- 更新时间: {progress.get('updated_at', 'N/A')[:19]}

消息:
{progress.get('message', 'N/A')}
"""

        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, detail)
        self.detail_text.config(state=tk.DISABLED)

    def open_task_detail(self, event):
        """双击打开任务详情窗口"""
        if self.selected_task_id:
            messagebox.showinfo("任务详情", f"任务ID: {self.selected_task_id}\n\n双击查看详情功能待实现")

    def create_new_task(self):
        """创建新任务"""
        NewOutlineTaskWindow(self.window, callback=self.refresh_tasks)

    def delete_selected_task(self):
        """删除选中的任务"""
        if not self.selected_task_id:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认", "确定要删除这个任务吗？"):
            import shutil
            task_dir = os.path.join('tasks', self.selected_task_id)
            if os.path.exists(task_dir):
                shutil.rmtree(task_dir)
            self.selected_task_id = None
            self.refresh_tasks()

    def start_polling(self):
        """启动轮询"""
        self.polling = True

        def poll():
            while self.polling:
                time.sleep(2)
                self.window.after(0, self.refresh_tasks)

        threading.Thread(target=poll, daemon=True).start()

    def run(self):
        """运行应用"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.mainloop()

    def on_close(self):
        """关闭窗口"""
        self.polling = False
        self.window.destroy()


class NewOutlineTaskWindow:
    """新建大纲任务窗口"""

    def __init__(self, parent, callback=None):
        self.callback = callback
        self.resource_mgr = ResourceManager()

        self.window = tk.Toplevel(parent)
        self.window.title("新建大纲生成任务")
        self.window.geometry("600x550")

        self.source_file = None
        self.detected_genre = None

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 文件选择
        tk.Label(self.window, text="选择原文文件:", font=("Arial", 11, "bold")).pack(
            anchor=tk.W, padx=10, pady=(10, 5)
        )

        file_frame = tk.Frame(self.window)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_label = tk.Label(file_frame, text="未选择文件（格式：书名_类型.txt）", fg="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_frame,
            text="选择文件",
            command=self.select_file
        ).pack(side=tk.RIGHT)

        self.genre_label = tk.Label(file_frame, text="", fg="blue", font=("Arial", 10, "bold"))
        self.genre_label.pack(side=tk.RIGHT, padx=10)

        # 配置参数
        config_frame = tk.LabelFrame(self.window, text="配置参数", padx=15, pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API Key
        tk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=config.get_api_key())
        tk.Entry(
            config_frame,
            textvariable=self.api_key_var,
            show="*",
            width=40
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # Base URL
        tk.Label(config_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        tk.Entry(
            config_frame,
            textvariable=self.base_url_var,
            width=40
        ).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # 模型
        tk.Label(config_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-4-turbo-preview")
        ttk.Combobox(
            config_frame,
            textvariable=self.model_var,
            values=["gemini-2.5-pro", "gpt-5.1", "gpt-5", "gemini-3-pro-preview", "gpt-4-turbo-preview"],
            width=37,
            state="readonly"
        ).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        # 章节范围
        tk.Label(config_frame, text="章节范围:").grid(row=3, column=0, sticky=tk.W, pady=5)
        range_frame = tk.Frame(config_frame)
        range_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(range_frame, text="第").pack(side=tk.LEFT)
        self.start_chapter_var = tk.IntVar(value=1)
        tk.Spinbox(
            range_frame,
            from_=1,
            to=500,
            textvariable=self.start_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(range_frame, text="章 至 第").pack(side=tk.LEFT)
        self.end_chapter_var = tk.IntVar(value=100)
        tk.Spinbox(
            range_frame,
            from_=1,
            to=500,
            textvariable=self.end_chapter_var,
            width=8
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(range_frame, text="章").pack(side=tk.LEFT)

        # 人名数量
        tk.Label(config_frame, text="男性人名数:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.male_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            config_frame,
            from_=5,
            to=30,
            textvariable=self.male_count_var,
            width=15
        ).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(config_frame, text="女性人名数:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.female_count_var = tk.IntVar(value=10)
        tk.Spinbox(
            config_frame,
            from_=5,
            to=30,
            textvariable=self.female_count_var,
            width=15
        ).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        # Temperature
        tk.Label(config_frame, text="Temperature:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(
            config_frame,
            from_=0,
            to=1,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        ).grid(row=6, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=100000)
        tk.Spinbox(
            config_frame,
            from_=1000,
            to=200000,
            increment=1000,
            textvariable=self.max_tokens_var,
            width=15
        ).grid(row=7, column=1, sticky=tk.W, pady=5, padx=5)

        # 按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="创建并启动",
            command=self.create_and_start,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame,
            text="取消",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def select_file(self):
        """选择源文件"""
        file_path = filedialog.askopenfilename(
            title="选择原文文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 提取类型
                genre = extract_genre_from_filename(file_path)

                # 验证类型
                available_genres = self.resource_mgr.get_available_genres()
                validate_genre(genre, available_genres)

                # 保存数据
                self.source_file = file_path
                self.detected_genre = genre

                # 更新界面
                self.file_label.config(
                    text=os.path.basename(file_path),
                    fg="black"
                )
                self.genre_label.config(text=f"类型: {genre}")

            except ValueError as e:
                messagebox.showerror("文件名错误", str(e))
                self.source_file = None
                self.detected_genre = None

    def create_and_start(self):
        """创建并启动任务"""
        if not self.source_file:
            messagebox.showwarning("警告", "请先选择原文文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        if self.start_chapter_var.get() > self.end_chapter_var.get():
            messagebox.showwarning("警告", "起始章节不能大于结束章节")
            return

        try:
            # 生成任务ID
            task_id = f"outline_{uuid.uuid4().hex[:12]}"

            # 创建任务文件夹
            task_dir = os.path.join('tasks', task_id)
            os.makedirs(task_dir, exist_ok=True)

            # 构建配置
            task_config = {
                'task_id': task_id,
                'task_type': 'outline',
                'source_file': self.source_file,
                'genre': self.detected_genre,
                'api_key': self.api_key_var.get(),
                'base_url': self.base_url_var.get(),
                'model': self.model_var.get(),
                'start_chapter': self.start_chapter_var.get(),
                'end_chapter': self.end_chapter_var.get(),
                'male_count': self.male_count_var.get(),
                'female_count': self.female_count_var.get(),
                'temperature': self.temperature_var.get(),
                'max_tokens': self.max_tokens_var.get(),
                'created_at': datetime.now().isoformat()
            }

            # 保存配置
            config_file = os.path.join(task_dir, 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(task_config, f, indent=2, ensure_ascii=False)

            # 创建初始进度文件
            progress_file = os.path.join(task_dir, 'progress.json')
            progress = {
                'task_id': task_id,
                'status': 'pending',
                'message': '等待启动',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)

            # 启动独立进程
            python_exe = sys.executable
            process = subprocess.Popen([
                python_exe,
                'outline_worker.py',
                '--config', config_file,
                '--task-id', task_id
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # 保存进程ID
            pid_file = os.path.join(task_dir, 'pid.txt')
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            messagebox.showinfo("成功", f"大纲生成任务已创建并启动！\n任务ID: {task_id}")

            # 刷新父窗口
            if self.callback:
                self.callback()

            # 关闭窗口
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败: {str(e)}")


def main():
    """主函数"""
    app = OutlineTaskManager()
    app.run()


if __name__ == '__main__':
    main()
