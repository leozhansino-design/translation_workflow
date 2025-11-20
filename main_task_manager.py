"""
任务管理器主窗口
显示所有写作任务，支持创建、监控、管理任务
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import os

from task_manager import TaskManager
from utils import format_time_elapsed, scan_chapter_files


class TaskManagerWindow:
    """任务管理器主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("任务管理器 - 小说写作工具")
        self.window.geometry("1000x700")

        self.task_mgr = TaskManager()
        self.tasks = []
        self.selected_task_id = None

        # 轮询线程
        self.polling = False

        # 初始化界面
        self.setup_ui()
        self.refresh_tasks()

        # 启动轮询
        self.start_polling()

    def setup_ui(self):
        """设置界面"""
        # === 标题栏 ===
        title_frame = tk.Frame(self.window, bg="#4CAF50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="📋 任务管理器",
            font=("Arial", 20, "bold"),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="管理所有写作任务",
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # === 工具栏 ===
        toolbar = tk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            toolbar,
            text="➕ 新建任务",
            command=self.create_new_task,
            bg="#2196F3",
            fg="white",
            width=12
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
        columns = ('状态', '书名', '进度', '费用', '更新时间')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)

        # 设置列
        self.task_tree.heading('状态', text='状态')
        self.task_tree.heading('书名', text='书名')
        self.task_tree.heading('进度', text='进度')
        self.task_tree.heading('费用', text='费用')
        self.task_tree.heading('更新时间', text='更新时间')

        self.task_tree.column('状态', width=100)
        self.task_tree.column('书名', width=300)
        self.task_tree.column('进度', width=150)
        self.task_tree.column('费用', width=100)
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
        self.tasks = self.task_mgr.list_all_tasks()

        # 填充列表
        for task_data in self.tasks:
            summary = self.task_mgr.get_task_summary(task_data['task_id'])
            if summary:
                status_icon = self.get_status_icon(summary['status'])
                status_text = f"{status_icon} {summary['status']}"

                progress_text = f"{summary['current_chapter']}/{summary['target_chapters']} ({summary['progress_percent']:.1f}%)"

                cost_text = f"${summary['total_cost']:.2f}"

                updated_time = summary.get('updated_at', '')[:19]  # 只显示日期时间

                self.task_tree.insert('', tk.END, iid=summary['task_id'], values=(
                    status_text,
                    summary['title'],
                    progress_text,
                    cost_text,
                    updated_time
                ))

    def get_status_icon(self, status):
        """获取状态图标"""
        icons = {
            'pending': '⏸️',
            'initializing': '🔄',
            'in_progress': '🔄',
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
        summary = self.task_mgr.get_task_summary(task_id)
        progress = self.task_mgr.get_task_progress(task_id)
        config = self.task_mgr.get_task_config(task_id)

        if not summary or not progress or not config:
            return

        detail = f"""
{'='*70}
任务ID: {task_id}
书名: {summary['title']}
状态: {summary['status']}
{'='*70}

进度信息:
- 当前章节: {summary['current_chapter']} / {summary['target_chapters']}
- 完成度: {summary['progress_percent']:.1f}%
- Token使用: {progress.get('total_tokens', 0):,}
- 预计费用: ${summary['total_cost']:.2f}

配置信息:
- 模型: {config.get('model', 'N/A')}
- 批次大小: {config.get('batch_size', 'N/A')} 章/批
- Temperature: {config.get('temperature', 'N/A')}

时间信息:
- 创建时间: {summary['created_at'][:19]}
- 更新时间: {summary['updated_at'][:19]}

进程状态:
- 是否运行: {'✅ 运行中' if summary['is_running'] else '❌ 未运行'}

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
            TaskDetailWindow(self.window, self.selected_task_id, self.task_mgr)

    def create_new_task(self):
        """创建新任务"""
        NewTaskWindow(self.window, self.task_mgr, callback=self.refresh_tasks)

    def delete_selected_task(self):
        """删除选中的任务"""
        if not self.selected_task_id:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        if messagebox.askyesno("确认", "确定要删除这个任务吗？\n注意：这不会删除生成的项目文件。"):
            self.task_mgr.delete_task(self.selected_task_id)
            self.selected_task_id = None
            self.refresh_tasks()

    def start_polling(self):
        """启动轮询"""
        self.polling = True

        def poll():
            while self.polling:
                time.sleep(2)  # 每2秒刷新一次
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


class NewTaskWindow:
    """新建任务窗口"""

    def __init__(self, parent, task_mgr, callback=None):
        self.task_mgr = task_mgr
        self.callback = callback

        self.window = tk.Toplevel(parent)
        self.window.title("新建任务")
        self.window.geometry("600x500")

        self.outline_file = None
        self.project_folder = None

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 大纲选择
        tk.Label(self.window, text="选择大纲文件:", font=("Arial", 11, "bold")).pack(
            anchor=tk.W, padx=10, pady=(10, 5)
        )

        file_frame = tk.Frame(self.window)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_label = tk.Label(file_frame, text="未选择文件", fg="gray")
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            file_frame,
            text="选择大纲",
            command=self.select_outline
        ).pack(side=tk.RIGHT)

        # 项目文件夹（续写用）
        tk.Label(self.window, text="项目文件夹（续写用，可选）:", font=("Arial", 10)).pack(
            anchor=tk.W, padx=10, pady=(10, 5)
        )

        folder_frame = tk.Frame(self.window)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)

        self.folder_label = tk.Label(folder_frame, text="未选择（新建项目）", fg="gray")
        self.folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(
            folder_frame,
            text="选择文件夹",
            command=self.select_project_folder
        ).pack(side=tk.RIGHT)

        # 配置参数
        config_frame = tk.LabelFrame(self.window, text="配置参数", padx=15, pady=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # API Key
        tk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
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

        # 目标章节数
        tk.Label(config_frame, text="目标章节数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.target_chapters_var = tk.IntVar(value=100)
        tk.Spinbox(
            config_frame,
            from_=1,
            to=500,
            textvariable=self.target_chapters_var,
            width=15
        ).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)

        # 批次大小
        tk.Label(config_frame, text="批次大小:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.IntVar(value=3)
        tk.Spinbox(
            config_frame,
            from_=1,
            to=10,
            textvariable=self.batch_size_var,
            width=15
        ).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)

        # Temperature
        tk.Label(config_frame, text="Temperature:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.8)
        tk.Scale(
            config_frame,
            from_=0,
            to=1,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.temperature_var,
            length=200
        ).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        # Max Tokens
        tk.Label(config_frame, text="Max Tokens:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.IntVar(value=100000)
        tk.Spinbox(
            config_frame,
            from_=1000,
            to=200000,
            increment=1000,
            textvariable=self.max_tokens_var,
            width=15
        ).grid(row=6, column=1, sticky=tk.W, pady=5, padx=5)

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

    def select_outline(self):
        """选择大纲文件"""
        file_path = filedialog.askopenfilename(
            title="选择大纲JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            initialdir="outlines"
        )

        if file_path:
            self.outline_file = file_path
            self.file_label.config(text=os.path.basename(file_path), fg="black")

    def select_project_folder(self):
        """选择项目文件夹（续写用）"""
        folder_path = filedialog.askdirectory(
            title="选择项目文件夹",
            initialdir="projects"
        )

        if folder_path:
            # 扫描已完成的章节
            scan_result = scan_chapter_files(folder_path)
            max_chapter = scan_result['max_chapter']

            self.project_folder = folder_path
            self.folder_label.config(
                text=f"{os.path.basename(folder_path)} (已完成: {max_chapter}章)",
                fg="black"
            )

    def create_and_start(self):
        """创建并启动任务"""
        if not self.outline_file:
            messagebox.showwarning("警告", "请先选择大纲文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请输入API Key")
            return

        # 构建配置
        config = {
            'api_key': self.api_key_var.get(),
            'base_url': self.base_url_var.get(),
            'model': self.model_var.get(),
            'target_chapters': self.target_chapters_var.get(),
            'batch_size': self.batch_size_var.get(),
            'temperature': self.temperature_var.get(),
            'max_tokens': self.max_tokens_var.get()
        }

        if self.project_folder:
            config['project_folder'] = self.project_folder

        try:
            # 创建任务
            task_id = self.task_mgr.create_task(self.outline_file, config)

            # 启动任务
            self.task_mgr.start_task(task_id)

            messagebox.showinfo("成功", f"任务已创建并启动！\n任务ID: {task_id}")

            # 刷新父窗口
            if self.callback:
                self.callback()

            # 关闭窗口
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("错误", f"创建任务失败: {str(e)}")


class TaskDetailWindow:
    """任务详情窗口"""

    def __init__(self, parent, task_id, task_mgr):
        self.task_id = task_id
        self.task_mgr = task_mgr

        self.window = tk.Toplevel(parent)
        self.window.title(f"任务详情 - {task_id}")
        self.window.geometry("700x600")

        self.setup_ui()
        self.load_detail()

    def setup_ui(self):
        """设置界面"""
        # 详情文本
        self.detail_text = scrolledtext.ScrolledText(
            self.window,
            height=30,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 按钮
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="刷新",
            command=self.load_detail,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="停止任务",
            command=self.stop_task,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="打开项目文件夹",
            command=self.open_project_folder,
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="关闭",
            command=self.window.destroy,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

    def load_detail(self):
        """加载详情"""
        config = self.task_mgr.get_task_config(self.task_id)
        progress = self.task_mgr.get_task_progress(self.task_id)

        if not config or not progress:
            return

        detail = f"""
{'='*70}
任务ID: {self.task_id}
{'='*70}

配置信息:
- 大纲文件: {config.get('outline_file', 'N/A')}
- 模型: {config.get('model', 'N/A')}
- Base URL: {config.get('base_url', 'N/A')}
- 批次大小: {config.get('batch_size', 'N/A')} 章/批
- 目标章节数: {config.get('target_chapters', 'N/A')}
- Temperature: {config.get('temperature', 'N/A')}
- Max Tokens: {config.get('max_tokens', 'N/A')}

进度信息:
- 状态: {progress.get('status', 'N/A')}
- 当前章节: {progress.get('current_chapter', 0)} / {progress.get('target_chapters', 0)}
- 已完成章节: {progress.get('chapters_completed', 0)}
- Token使用: {progress.get('total_tokens', 0):,}
- 预计费用: ${progress.get('total_cost', 0):.2f}

时间信息:
- 创建时间: {progress.get('created_at', 'N/A')}
- 更新时间: {progress.get('updated_at', 'N/A')}

消息:
{progress.get('message', 'N/A')}

{'='*70}
"""

        self.detail_text.delete(1.0, tk.END)
        self.detail_text.insert(1.0, detail)

    def stop_task(self):
        """停止任务"""
        if messagebox.askyesno("确认", "确定要停止这个任务吗？"):
            success = self.task_mgr.stop_task(self.task_id)
            if success:
                messagebox.showinfo("成功", "任务已停止")
            else:
                messagebox.showwarning("警告", "任务可能未运行或已停止")

    def open_project_folder(self):
        """打开项目文件夹"""
        config = self.task_mgr.get_task_config(self.task_id)
        project_folder = config.get('project_folder')

        if project_folder and os.path.exists(project_folder):
            import platform
            system = platform.system()

            if system == 'Darwin':  # Mac
                os.system(f'open "{project_folder}"')
            elif system == 'Windows':
                os.system(f'explorer "{project_folder}"')
            else:  # Linux
                os.system(f'xdg-open "{project_folder}"')
        else:
            messagebox.showwarning("警告", "项目文件夹不存在")


def main():
    """主函数"""
    app = TaskManagerWindow()
    app.run()


if __name__ == '__main__':
    main()
