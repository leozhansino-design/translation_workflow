"""
小说翻译工具 - 主程序
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import os
from config import config
from translator import Translator
from resource_mgr import ResourceManager


class TranslatorApp:
    """翻译应用主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说翻译工具")
        self.window.geometry("800x700")

        self.translator = Translator()
        self.resource_mgr = ResourceManager()

        # 文件列表
        self.files = []
        self.file_listbox = None

        # 翻译状态
        self.executor = None
        self.is_translating = False
        self.status_labels = {}
        self.start_times = {}
        self.timer_running = {}

        # 总体统计
        self.total_completed = 0
        self.total_start_time = None

        # 初始化界面
        self.setup_ui()

        # 加载配置
        self.load_config()

    def setup_ui(self):
        """设置界面"""
        # 标题
        title_frame = tk.Frame(self.window)
        title_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(
            title_frame,
            text="小说翻译工具",
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)

        tk.Button(
            title_frame,
            text="设置",
            command=self.show_settings
        ).pack(side=tk.RIGHT)

        # API配置区域
        api_frame = tk.LabelFrame(self.window, text="API配置", padx=10, pady=10)
        api_frame.pack(fill=tk.X, padx=10, pady=5)

        # API Key
        tk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            show="*",
            width=30
        )
        self.api_key_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        tk.Button(
            api_frame,
            text="测试",
            command=self.test_connection
        ).grid(row=0, column=2, pady=2, padx=5)

        self.connection_status = tk.Label(api_frame, text="", fg="gray")
        self.connection_status.grid(row=0, column=3, pady=2, padx=5)

        # 线程数
        tk.Label(api_frame, text="线程数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.threads_var = tk.IntVar(value=10)
        tk.Spinbox(
            api_frame,
            from_=1,
            to=20,
            textvariable=self.threads_var,
            width=10
        ).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        # 文件管理区域
        file_frame = tk.LabelFrame(self.window, text="文件管理", padx=10, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 按钮行
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Button(
            btn_frame,
            text="添加文件",
            command=self.add_files
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="添加文件夹",
            command=self.add_folder
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="清空列表",
            command=self.clear_files
        ).pack(side=tk.LEFT, padx=2)

        # 文件列表
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=8
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # 统计信息
        self.stats_label = tk.Label(file_frame, text="共0本 | 预计$0.00")
        self.stats_label.pack(pady=5)

        # 开始按钮
        start_frame = tk.Frame(self.window)
        start_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = tk.Button(
            start_frame,
            text="🚀 开始翻译",
            command=self.start_translation,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2
        )
        self.start_button.pack(fill=tk.X)

        # 翻译状态区域
        status_frame = tk.LabelFrame(self.window, text="翻译状态", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 状态文本框
        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=10,
            state=tk.DISABLED
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        # 总体进度
        self.progress_label = tk.Label(
            status_frame,
            text="总耗时: 0分0秒 | 完成: 0/0本",
            font=("Arial", 10)
        )
        self.progress_label.pack(pady=5)

    def load_config(self):
        """加载配置"""
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)

        max_workers = config.get_max_workers()
        self.threads_var.set(max_workers)

    def save_config(self):
        """保存配置"""
        config.set_api_key(self.api_key_var.get())
        config.set_max_workers(self.threads_var.get())

    def show_settings(self):
        """显示设置对话框"""
        settings_win = tk.Toplevel(self.window)
        settings_win.title("设置")
        settings_win.geometry("400x300")

        # Model选择
        tk.Label(settings_win, text="模型:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        model_var = tk.StringVar(value=config.get_model())
        models = ["gpt-4-turbo-preview", "gpt-4", "gpt-3.5-turbo"]
        tk.OptionMenu(settings_win, model_var, *models).grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        # Temperature
        tk.Label(settings_win, text="Temperature:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        temp_var = tk.DoubleVar(value=config.get_temperature())
        tk.Scale(
            settings_win,
            from_=0,
            to=1,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=temp_var
        ).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        # Max Tokens
        tk.Label(settings_win, text="Max Tokens:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        tokens_var = tk.IntVar(value=config.get_max_tokens())
        tk.Spinbox(
            settings_win,
            from_=1000,
            to=100000,
            increment=1000,
            textvariable=tokens_var,
            width=10
        ).grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

        def save_settings():
            config.set('model', model_var.get())
            config.set('temperature', temp_var.get())
            config.set('max_tokens', tokens_var.get())
            messagebox.showinfo("成功", "设置已保存")
            settings_win.destroy()

        tk.Button(
            settings_win,
            text="保存",
            command=save_settings
        ).grid(row=3, column=0, columnspan=2, pady=20)

    def test_connection(self):
        """测试API连接"""
        self.save_config()

        def test():
            self.connection_status.config(text="测试中...", fg="orange")
            success, message = self.translator.test_connection()
            if success:
                self.connection_status.config(text="✅ 连接成功", fg="green")
            else:
                self.connection_status.config(text="❌ " + message, fg="red")

        threading.Thread(target=test, daemon=True).start()

    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        for file in files:
            if file not in self.files:
                self.files.append(file)
                # 显示文件名和字数
                basename = os.path.basename(file)
                word_count = self.translator.estimate_word_count(file)
                display = f"{basename} ({word_count}字)"
                self.file_listbox.insert(tk.END, display)

        self.update_stats()

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    file_path = os.path.join(folder, filename)
                    if file_path not in self.files:
                        self.files.append(file_path)
                        word_count = self.translator.estimate_word_count(file_path)
                        display = f"{filename} ({word_count}字)"
                        self.file_listbox.insert(tk.END, display)

        self.update_stats()

    def clear_files(self):
        """清空文件列表"""
        self.files = []
        self.file_listbox.delete(0, tk.END)
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        total_files = len(self.files)
        total_cost = sum(self.translator.estimate_cost(f) for f in self.files)
        self.stats_label.config(text=f"共{total_files}本 | 预计${total_cost:.2f}")

    def start_translation(self):
        """开始翻译"""
        if not self.files:
            messagebox.showwarning("警告", "请先添加文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请先设置API Key")
            return

        if self.is_translating:
            messagebox.showinfo("提示", "翻译正在进行中")
            return

        # 保存配置
        self.save_config()

        # 确认开始
        if not messagebox.askyesno("确认", f"确定要翻译 {len(self.files)} 本小说吗？"):
            return

        # 重置状态
        self.is_translating = True
        self.total_completed = 0
        self.total_start_time = time.time()
        self.status_labels = {}
        self.start_times = {}
        self.timer_running = {}

        # 清空状态文本
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED, text="翻译中...")

        # 分配资源
        self.append_status("正在分配资源...")
        resources = self.resource_mgr.allocate_resources(self.files)
        self.append_status(f"资源分配完成，准备翻译 {len(self.files)} 本小说\n")

        # 启动多线程
        max_workers = self.threads_var.get()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        for file_path, resource in zip(self.files, resources):
            title = self.resource_mgr.extract_title(file_path)
            self.start_times[title] = None
            self.timer_running[title] = False

            # 提交任务
            self.executor.submit(
                self.translate_one,
                file_path,
                resource
            )

        # 启动总体计时器
        self.update_total_progress()

    def translate_one(self, file_path, resource):
        """翻译单本小说（在线程中运行）"""
        title = self.resource_mgr.extract_title(file_path)

        # 开始计时
        self.start_times[title] = time.time()
        self.timer_running[title] = True

        # 启动计时器
        self.window.after(0, lambda: self.start_timer(title))

        # 进度回调
        def progress_callback(t, status, elapsed, cost):
            self.update_status_safe(t, status, elapsed, cost)

        # 执行翻译
        result = self.translator.translate_novel(
            file_path,
            resource,
            progress_callback
        )

        # 停止计时
        self.timer_running[title] = False

        # 更新完成状态
        if result['success']:
            self.append_status(
                f"✅ {title}  完成  "
                f"{int(result['duration'])}秒  ${result['cost']:.2f}\n"
            )
        else:
            self.append_status(
                f"❌ {title}  失败: {result.get('error', '未知错误')}\n"
            )

        # 更新完成计数
        self.total_completed += 1

        # 检查是否全部完成
        if self.total_completed >= len(self.files):
            self.on_all_completed()

    def start_timer(self, title):
        """启动计时器（每秒更新）"""
        if not self.timer_running.get(title, False):
            return

        start_time = self.start_times.get(title)
        if start_time:
            elapsed = time.time() - start_time
            self.update_status_safe(title, "翻译中", elapsed, None)

        # 1秒后再次调用
        self.window.after(1000, lambda: self.start_timer(title))

    def update_status_safe(self, title, status, elapsed_time, cost):
        """线程安全地更新状态"""
        def _update():
            # 构建状态文本
            if cost is not None:
                status_text = f"  {status}  {int(elapsed_time)}秒  ${cost:.2f}"
            else:
                status_text = f"  {status}  {int(elapsed_time)}秒"

            # 在状态文本框中更新或添加
            self.status_text.config(state=tk.NORMAL)

            # 查找是否已存在这个标题
            content = self.status_text.get(1.0, tk.END)
            lines = content.split('\n')
            found = False

            for i, line in enumerate(lines):
                if line.startswith(title) or (status.startswith("🔄") and title in line):
                    # 更新现有行
                    line_start = f"{i+1}.0"
                    line_end = f"{i+1}.end"
                    prefix = "🔄 " if status == "翻译中" else "✅ "
                    self.status_text.delete(line_start, line_end)
                    self.status_text.insert(line_start, f"{prefix}{title}{status_text}")
                    found = True
                    break

            if not found:
                # 添加新行
                prefix = "🔄 " if status == "翻译中" else "⏸ "
                self.status_text.insert(tk.END, f"{prefix}{title}{status_text}\n")

            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)

        self.window.after(0, _update)

    def append_status(self, text):
        """添加状态信息"""
        def _append():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, text + "\n")
            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)

        self.window.after(0, _append)

    def update_total_progress(self):
        """更新总体进度"""
        if not self.is_translating:
            return

        if self.total_start_time:
            total_elapsed = time.time() - self.total_start_time
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            progress_text = (
                f"总耗时: {minutes}分{seconds}秒 | "
                f"完成: {self.total_completed}/{len(self.files)}本"
            )
            self.progress_label.config(text=progress_text)

        # 1秒后再次更新
        self.window.after(1000, self.update_total_progress)

    def on_all_completed(self):
        """所有翻译完成"""
        self.is_translating = False
        self.start_button.config(state=tk.NORMAL, text="🚀 开始翻译")

        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

        total_elapsed = time.time() - self.total_start_time
        minutes = int(total_elapsed // 60)
        seconds = int(total_elapsed % 60)

        messagebox.showinfo(
            "完成",
            f"所有翻译已完成！\n总耗时: {minutes}分{seconds}秒\n完成: {self.total_completed}/{len(self.files)}本"
        )

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    """主函数"""
    app = TranslatorApp()
    app.run()


if __name__ == '__main__':
    main()
