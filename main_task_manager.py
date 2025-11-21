"""
小说写作工具 - 主窗口
批量生成小说章节，支持断点续写
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from datetime import datetime

from writer_worker import WriterWorker
from utils import scan_chapter_files


class WritingTask:
    """写作任务对象"""
    def __init__(self, outline_folder, config):
        self.outline_folder = outline_folder
        self.config = config
        self.status = 'pending'
        self.progress = 0
        self.current_chapter = 0
        self.total_chapters = config.get('end_chapter', 50)
        self.cost = 0.0
        self.started_at = None
        self.worker_thread = None
        self.title = os.path.basename(outline_folder)

        # 扫描已有章节（断点续写）
        self.existing_chapters = self._scan_existing_chapters()
        if self.existing_chapters:
            self.current_chapter = max(self.existing_chapters)
            # 计算进度
            self.progress = (len(self.existing_chapters) / self.total_chapters) * 100

    def _scan_existing_chapters(self):
        """扫描项目文件夹中已有的章节"""
        project_folder = self.config.get('project_folder', self.outline_folder)
        if not os.path.exists(project_folder):
            return []

        chapters = []
        for file in os.listdir(project_folder):
            if file.startswith('chapter_') and file.endswith('.txt'):
                try:
                    ch_num = int(file.replace('chapter_', '').replace('.txt', ''))
                    chapters.append(ch_num)
                except:
                    pass

        return sorted(chapters)


class WritingToolWindow:
    """写作工具主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说写作工具")
        self.window.geometry("1200x800")

        self.tasks = []  # 任务列表
        self.task_containers = {}  # 任务卡片引用

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 标题栏
        title_frame = tk.Frame(self.window, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📝 小说写作工具",
            font=("Arial", 20, "bold"),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="批量生成小说章节 | 支持断点续写",
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # API配置区
        config_frame = tk.LabelFrame(self.window, text="⚙️ API配置", padx=15, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # 第一行：API Key + 测试按钮
        tk.Label(config_frame, text="API Key:", width=12, anchor='w').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        tk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=40).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Button(
            config_frame,
            text="🔧 测试API",
            command=self.test_api_connection,
            width=12,
            bg="#4CAF50",
            fg="white"
        ).grid(row=0, column=2, pady=5, padx=5)

        self.api_status_label = tk.Label(config_frame, text="", fg="gray")
        self.api_status_label.grid(row=0, column=3, pady=5, padx=5)

        # 第二行：Base URL
        tk.Label(config_frame, text="Base URL:", width=12, anchor='w').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        tk.Entry(config_frame, textvariable=self.base_url_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # 第三行：Model（支持自定义输入）
        tk.Label(config_frame, text="Model:", width=12, anchor='w').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="gpt-5.1")
        model_combo = ttk.Combobox(config_frame, textvariable=self.model_var, width=37, state='normal')
        model_combo['values'] = ["gpt-5.1", "gemini-2.5-pro", "gpt-5", "gemini-3-pro-preview", "gpt-4-turbo-preview"]
        model_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)

        tk.Label(config_frame, text="💡 可自定义输入模型名", fg="gray", font=("Arial", 8)).grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5)

        # Temperature
        tk.Label(config_frame, text="Temperature:", width=12, anchor='w').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(config_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self.temperature_var, length=300).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:", width=12, anchor='w').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=20000)
        tk.Spinbox(config_frame, from_=5000, to=200000, increment=1000,
                   textvariable=self.max_tokens_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # 添加任务区
        add_task_frame = tk.LabelFrame(self.window, text="➕ 添加任务", padx=15, pady=10)
        add_task_frame.pack(fill=tk.X, padx=10, pady=10)

        # 选择大纲文件夹
        folder_frame = tk.Frame(add_task_frame)
        folder_frame.pack(fill=tk.X, pady=5)

        tk.Label(folder_frame, text="大纲文件夹:", width=12, anchor='w').pack(side=tk.LEFT)
        self.outline_folder_var = tk.StringVar(value="未选择")
        tk.Label(folder_frame, textvariable=self.outline_folder_var, fg="gray").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(folder_frame, text="📂 选择", command=self.select_outline_folder, width=10).pack(side=tk.RIGHT, padx=5)

        # 章节范围和批次
        range_frame = tk.Frame(add_task_frame)
        range_frame.pack(fill=tk.X, pady=5)

        tk.Label(range_frame, text="章节范围:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Label(range_frame, text="从").pack(side=tk.LEFT, padx=(0, 5))
        self.start_chapter_var = tk.IntVar(value=1)
        tk.Spinbox(range_frame, from_=1, to=500, textvariable=self.start_chapter_var, width=8).pack(side=tk.LEFT)
        tk.Label(range_frame, text="到").pack(side=tk.LEFT, padx=(10, 5))
        self.end_chapter_var = tk.IntVar(value=50)
        tk.Spinbox(range_frame, from_=1, to=500, textvariable=self.end_chapter_var, width=8).pack(side=tk.LEFT)

        tk.Label(range_frame, text="每批章节数:", width=12, anchor='w').pack(side=tk.LEFT, padx=(20, 5))
        self.batch_size_var = tk.IntVar(value=3)
        tk.Spinbox(range_frame, from_=1, to=10, textvariable=self.batch_size_var, width=8).pack(side=tk.LEFT)

        tk.Button(range_frame, text="✚ 添加到队列", command=self.add_task,
                  bg="#2196F3", fg="white", width=15).pack(side=tk.RIGHT, padx=5)

        # 任务队列
        queue_frame = tk.LabelFrame(self.window, text="📋 任务队列", padx=5, pady=5)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(queue_frame, bg="white")
        scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.tasks_frame = tk.Frame(self.canvas, bg="white")

        self.canvas_window = self.canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tasks_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # 显示空状态
        self.show_empty_state()

    def show_empty_state(self):
        """显示空状态提示"""
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()

        empty_label = tk.Label(
            self.tasks_frame,
            text="📭 暂无任务，请选择大纲文件夹后添加任务",
            font=("Arial", 12),
            fg="gray",
            bg="white"
        )
        empty_label.pack(pady=50)

    def select_outline_folder(self):
        """选择大纲文件夹"""
        folder = filedialog.askdirectory(title="选择大纲文件夹", initialdir="outlines")
        if folder:
            # 验证文件夹包含_writing_prompt.txt
            if not os.path.exists(os.path.join(folder, '_writing_prompt.txt')):
                messagebox.showwarning("警告", "所选文件夹不包含 _writing_prompt.txt 文件")
                return

            self.outline_folder_var.set(os.path.basename(folder))
            self.selected_outline_folder = folder

    def add_task(self):
        """添加任务到队列"""
        if not hasattr(self, 'selected_outline_folder'):
            messagebox.showwarning("警告", "请先选择大纲文件夹")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 构建配置
        config = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get(),
            'start_chapter': self.start_chapter_var.get(),
            'end_chapter': self.end_chapter_var.get(),
            'batch_size': self.batch_size_var.get(),
            'project_folder': self.selected_outline_folder  # 写作到大纲文件夹
        }

        # 创建任务
        task = WritingTask(self.selected_outline_folder, config)
        self.tasks.append(task)

        # 刷新界面
        self.refresh_task_list()

        messagebox.showinfo("成功", f"任务已添加：{task.title}")

    def refresh_task_list(self):
        """刷新任务列表"""
        # 清空
        for widget in self.tasks_frame.winfo_children():
            widget.destroy()
        self.task_containers.clear()

        if not self.tasks:
            self.show_empty_state()
            return

        # 创建任务卡片
        for i, task in enumerate(self.tasks):
            self._create_task_card(task, i)

    def _create_task_card(self, task, index):
        """创建任务卡片"""
        # 任务容器
        container = tk.Frame(self.tasks_frame, bg="#f5f5f5", relief=tk.RAISED, borderwidth=1)
        container.pack(fill=tk.X, padx=5, pady=5)

        # 左侧信息
        info_frame = tk.Frame(container, bg="#f5f5f5")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题
        tk.Label(
            info_frame,
            text=f"📖 {task.title}",
            font=("Arial", 12, "bold"),
            bg="#f5f5f5"
        ).pack(anchor="w")

        # 详情
        status_map = {'pending': ('⏸️', 'orange'), 'in_progress': ('🔄', 'blue'),
                      'completed': ('✅', 'green'), 'failed': ('❌', 'red')}
        icon, color = status_map.get(task.status, ('❓', 'gray'))

        details_text = f"{icon} {task.status}  |  章节: {task.current_chapter}/{task.total_chapters}  |  模型: {task.config['model']}"
        if task.started_at:
            details_text += f"  |  启动: {task.started_at}"

        tk.Label(
            info_frame,
            text=details_text,
            font=("Arial", 9),
            bg="#f5f5f5",
            fg="gray"
        ).pack(anchor="w", pady=(5, 5))

        # 进度条
        progress_frame = tk.Frame(info_frame, bg="#f5f5f5")
        progress_frame.pack(fill=tk.X, pady=(5, 0))

        progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', value=task.progress)
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        progress_text = tk.Label(progress_frame, text=f"{task.progress:.1f}% | ${task.cost:.2f}",
                                font=("Arial", 9), bg="#f5f5f5", fg="gray")
        progress_text.pack(side=tk.LEFT, padx=(10, 0))

        # 右侧按钮
        button_frame = tk.Frame(container, bg="#f5f5f5")
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        tk.Button(button_frame, text="👁️ 预览", command=lambda: self.preview_prompt(task),
                  width=10, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="▶️ 开始", command=lambda: self.start_task(task),
                  width=10, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🔄 重新生成", command=lambda: self.restart_task(task),
                  width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="📂 文件夹", command=lambda: self.open_folder(task),
                  width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="🗑️ 删除", command=lambda: self.delete_task(index),
                  width=8, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)

        # 保存引用
        self.task_containers[index] = {
            'container': container,
            'progress_bar': progress_bar,
            'progress_text': progress_text
        }

    def preview_prompt(self, task):
        """预览Prompt"""
        # TODO: 根据当前进度动态生成prompt预览
        messagebox.showinfo("预览Prompt", f"功能开发中...\n任务：{task.title}\n当前章节：{task.current_chapter}")

    def start_task(self, task):
        """启动任务"""
        if task.status == 'in_progress':
            messagebox.showinfo("提示", "任务正在运行中")
            return

        task.status = 'in_progress'
        task.started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # TODO: 启动WriterWorker线程
        messagebox.showinfo("成功", f"任务已启动：{task.title}")
        self.refresh_task_list()

    def restart_task(self, task):
        """重新生成（从头开始）"""
        if messagebox.askyesno("确认", "确定要从头重新生成吗？\n已生成的章节将被覆盖"):
            task.current_chapter = 0
            task.progress = 0
            task.cost = 0.0
            task.status = 'pending'
            self.refresh_task_list()

    def open_folder(self, task):
        """打开文件夹"""
        import platform
        folder = task.config.get('project_folder', task.outline_folder)

        if not os.path.exists(folder):
            messagebox.showwarning("警告", "项目文件夹不存在")
            return

        system = platform.system()
        if system == 'Darwin':
            os.system(f'open "{folder}"')
        elif system == 'Windows':
            os.system(f'explorer "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def delete_task(self, index):
        """删除任务"""
        if messagebox.askyesno("确认", "确定要删除这个任务吗？\n注意：不会删除已生成的文件"):
            del self.tasks[index]
            self.refresh_task_list()

    def test_api_connection(self):
        """测试API连接"""
        api_key = self.api_key_var.get()
        base_url = self.base_url_var.get()
        model = self.model_var.get()

        if not api_key:
            self.api_status_label.config(text="❌ 请输入API Key", fg="red")
            return

        # 更新状态
        self.api_status_label.config(text="🔄 测试中...", fg="blue")
        self.window.update()

        # 在新线程中测试，避免阻塞UI
        def _test():
            try:
                from openai import OpenAI

                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )

                # 发送一个简单的测试请求
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Hello"}
                    ],
                    max_tokens=10
                )

                # 检查响应
                if response and response.choices:
                    self.window.after(0, lambda: self.api_status_label.config(
                        text="✅ API连接成功", fg="green"
                    ))
                else:
                    self.window.after(0, lambda: self.api_status_label.config(
                        text="❌ API响应异常", fg="red"
                    ))

            except Exception as e:
                error_msg = str(e)
                if len(error_msg) > 50:
                    error_msg = error_msg[:50] + "..."
                self.window.after(0, lambda: self.api_status_label.config(
                    text=f"❌ 失败: {error_msg}", fg="red"
                ))

        # 启动测试线程
        threading.Thread(target=_test, daemon=True).start()

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    app = WritingToolWindow()
    app.run()


if __name__ == '__main__':
    main()
