"""
小说翻译工具 - 简化优化版
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
from translator import Translator


class TranslatorApp:
    """翻译应用主窗口"""

    def __init__(self):
        self.window = tk.Tk()
        self.window.title("小说翻译工具 - 简化优化版")
        self.window.geometry("1000x800")

        # 默认配置
        self.api_key_var = tk.StringVar(value="sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln")
        self.base_url_var = tk.StringVar(value="https://yunwuapi.com/v1/")
        self.model_var = tk.StringVar(value="gemini-2.5-pro")
        self.custom_model_var = tk.StringVar()
        self.names_db_var = tk.IntVar(value=1)

        # 文件列表
        self.files = []  # [(file_path, genre, status), ...]
        self.file_listbox = None
        self.file_status = {}  # {file_path: status_label}
        self.translation_threads = {}  # {file_path: thread}

        # 初始化界面
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 创建Notebook（标签页）
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标签页1：主界面
        main_frame = tk.Frame(notebook)
        notebook.add(main_frame, text="主界面")

        # 标签页2：Prompt预览
        self.prompt_preview_frame = tk.Frame(notebook)
        notebook.add(self.prompt_preview_frame, text="Prompt预览")

        # ==================== 主界面布局 ====================
        self.setup_main_frame(main_frame)

        # ==================== Prompt预览界面 ====================
        self.setup_prompt_preview_frame()

    def setup_main_frame(self, parent):
        """设置主界面"""
        # API配置区
        config_frame = tk.LabelFrame(parent, text="API配置", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # API Key
        tk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Entry(
            config_frame,
            textvariable=self.api_key_var,
            width=50,
            show="*"
        ).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=2, padx=5)

        # Base URL
        tk.Label(config_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Entry(
            config_frame,
            textvariable=self.base_url_var,
            width=50
        ).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=2, padx=5)

        # 模型选择
        tk.Label(config_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=2)
        model_menu = ttk.Combobox(
            config_frame,
            textvariable=self.model_var,
            values=["gpt-5.1", "gemini-2.5-pro", "自定义"],
            state="readonly",
            width=20
        )
        model_menu.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        # 自定义模型输入框
        tk.Label(config_frame, text="自定义模型:").grid(row=2, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        tk.Entry(
            config_frame,
            textvariable=self.custom_model_var,
            width=20
        ).grid(row=2, column=3, sticky=tk.W, pady=2, padx=5)

        # 人名库选择
        tk.Label(config_frame, text="人名库:").grid(row=3, column=0, sticky=tk.W, pady=2)
        names_frame = tk.Frame(config_frame)
        names_frame.grid(row=3, column=1, columnspan=3, sticky=tk.W, pady=2, padx=5)
        for i in [1, 2, 3]:
            tk.Radiobutton(
                names_frame,
                text=f"人名库 {i}",
                variable=self.names_db_var,
                value=i
            ).pack(side=tk.LEFT, padx=5)

        # 测试连接按钮
        self.test_btn = tk.Button(
            config_frame,
            text="测试连接",
            command=self.test_connection,
            bg="#2196F3",
            fg="white"
        )
        self.test_btn.grid(row=4, column=0, columnspan=4, pady=10)

        self.connection_status = tk.Label(config_frame, text="", fg="gray")
        self.connection_status.grid(row=5, column=0, columnspan=4)

        # Prompt管理区
        prompt_frame = tk.LabelFrame(parent, text="Prompt管理", padx=10, pady=10)
        prompt_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(
            prompt_frame,
            text="编辑默认Prompt",
            command=self.edit_default_prompt,
            bg="#FF9800",
            fg="white"
        ).pack(pady=5)

        # 文件管理区
        file_frame = tk.LabelFrame(parent, text="文件管理", padx=10, pady=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 按钮行
        btn_frame = tk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Button(
            btn_frame,
            text="添加文件",
            command=self.add_files,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="添加文件夹",
            command=self.add_folder,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            btn_frame,
            text="清空列表",
            command=self.clear_files,
            bg="#F44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=2)

        # 文件列表（使用Treeview显示更多信息）
        list_frame = tk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_tree = ttk.Treeview(
            list_frame,
            columns=("filename", "genre", "status"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.file_tree.heading("filename", text="文件名")
        self.file_tree.heading("genre", text="类型")
        self.file_tree.heading("status", text="状态")
        self.file_tree.column("filename", width=400)
        self.file_tree.column("genre", width=100)
        self.file_tree.column("status", width=200)
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_tree.yview)

        # 统计信息
        self.stats_label = tk.Label(file_frame, text="共0本小说")
        self.stats_label.pack(pady=5)

        # 开始翻译按钮
        self.start_button = tk.Button(
            parent,
            text="🚀 开始翻译",
            command=self.start_translation,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2
        )
        self.start_button.pack(fill=tk.X, padx=10, pady=10)

        # 状态显示区
        status_frame = tk.LabelFrame(parent, text="翻译状态", padx=10, pady=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=8,
            state=tk.DISABLED
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

    def setup_prompt_preview_frame(self):
        """设置Prompt预览界面"""
        # 说明文字
        info_label = tk.Label(
            self.prompt_preview_frame,
            text="添加文件后，此处将显示每个文件的完整Prompt预览",
            font=("Arial", 10)
        )
        info_label.pack(pady=20)

        # 创建子Notebook用于显示每个文件的prompt
        self.prompt_notebook = ttk.Notebook(self.prompt_preview_frame)
        self.prompt_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_prompt_previews(self):
        """更新所有文件的Prompt预览"""
        # 清空现有标签页
        for tab in self.prompt_notebook.tabs():
            self.prompt_notebook.forget(tab)

        # 为每个文件创建预览标签页
        translator = self.get_translator()
        prompt_template = translator.load_prompt_template()

        for file_path, genre, _ in self.files:
            filename = os.path.basename(file_path)

            # 创建标签页
            tab_frame = tk.Frame(self.prompt_notebook)
            self.prompt_notebook.add(tab_frame, text=filename[:20] + "...")

            # 加载人名库
            names_db = translator.load_names_database(self.names_db_var.get())
            allocated_names = translator.allocate_names(names_db, count=20)

            # 构建完整prompt
            full_prompt = translator.build_translation_prompt(
                prompt_template,
                genre,
                allocated_names
            )

            # 显示prompt
            text_widget = scrolledtext.ScrolledText(tab_frame, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.insert(1.0, full_prompt)
            text_widget.config(state=tk.DISABLED)

    def edit_default_prompt(self):
        """编辑默认Prompt"""
        edit_window = tk.Toplevel(self.window)
        edit_window.title("编辑默认Prompt")
        edit_window.geometry("800x600")

        # 文本编辑框
        text_frame = tk.Frame(edit_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)

        # 加载当前prompt
        translator = self.get_translator()
        current_prompt = translator.load_prompt_template()
        text_widget.insert(1.0, current_prompt)

        # 保存按钮
        def save_prompt():
            new_prompt = text_widget.get(1.0, tk.END).strip()
            translator.save_prompt_template(new_prompt)
            messagebox.showinfo("成功", "Prompt已保存！")
            edit_window.destroy()
            # 更新预览
            self.update_prompt_previews()

        btn_frame = tk.Frame(edit_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="保存",
            command=save_prompt,
            bg="#4CAF50",
            fg="white",
            width=20
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="取消",
            command=edit_window.destroy,
            width=20
        ).pack(side=tk.LEFT, padx=5)

    def get_translator(self):
        """获取配置好的Translator实例"""
        model = self.model_var.get()
        if model == "自定义":
            model = self.custom_model_var.get()

        return Translator(
            api_key=self.api_key_var.get(),
            base_url=self.base_url_var.get(),
            model=model
        )

    def test_connection(self):
        """测试API连接"""
        def test():
            self.connection_status.config(text="测试中...", fg="orange")
            translator = self.get_translator()
            success, message = translator.test_connection()
            if success:
                self.connection_status.config(text="✅ 连接成功", fg="green")
            else:
                self.connection_status.config(text=f"❌ {message}", fg="red")

        threading.Thread(target=test, daemon=True).start()

    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        translator = self.get_translator()

        for file in files:
            if file not in [f[0] for f in self.files]:
                # 自动提取genre
                filename = os.path.basename(file)
                genre = translator.extract_genre_from_filename(filename)

                # 添加到列表
                self.files.append((file, genre, "等待中"))
                self.file_tree.insert(
                    "",
                    tk.END,
                    values=(filename, genre, "等待中")
                )

        self.update_stats()
        self.update_prompt_previews()

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            translator = self.get_translator()
            for filename in os.listdir(folder):
                if filename.endswith('.txt'):
                    file_path = os.path.join(folder, filename)
                    if file_path not in [f[0] for f in self.files]:
                        # 自动提取genre
                        genre = translator.extract_genre_from_filename(filename)

                        # 添加到列表
                        self.files.append((file_path, genre, "等待中"))
                        self.file_tree.insert(
                            "",
                            tk.END,
                            values=(filename, genre, "等待中")
                        )

        self.update_stats()
        self.update_prompt_previews()

    def clear_files(self):
        """清空文件列表"""
        self.files = []
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.update_stats()
        self.update_prompt_previews()

    def update_stats(self):
        """更新统计信息"""
        self.stats_label.config(text=f"共{len(self.files)}本小说")

    def update_file_status(self, file_path, status):
        """更新文件状态"""
        # 找到对应的tree item并更新
        for i, (fp, genre, _) in enumerate(self.files):
            if fp == file_path:
                self.files[i] = (fp, genre, status)
                # 更新tree view
                items = self.file_tree.get_children()
                if i < len(items):
                    item_id = items[i]
                    values = self.file_tree.item(item_id, "values")
                    self.file_tree.item(item_id, values=(values[0], values[1], status))
                break

    def append_status(self, text):
        """添加状态信息"""
        def _append():
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, text + "\n")
            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)

        self.window.after(0, _append)

    def start_translation(self):
        """开始翻译"""
        if not self.files:
            messagebox.showwarning("警告", "请先添加文件")
            return

        if not self.api_key_var.get():
            messagebox.showwarning("警告", "请先设置API Key")
            return

        # 确认开始
        if not messagebox.askyesno("确认", f"确定要翻译 {len(self.files)} 本小说吗？\n\n翻译将并行进行，互不阻塞。"):
            return

        # 清空状态
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

        self.append_status(f"{'='*60}")
        self.append_status(f"开始翻译 {len(self.files)} 本小说...")
        self.append_status(f"{'='*60}\n")

        # 为每个文件启动独立线程
        for file_path, genre, _ in self.files:
            self.update_file_status(file_path, "翻译中...")
            thread = threading.Thread(
                target=self.translate_one,
                args=(file_path, genre),
                daemon=True
            )
            thread.start()
            self.translation_threads[file_path] = thread

    def translate_one(self, file_path, genre):
        """翻译单个文件（在独立线程中运行）"""
        filename = os.path.basename(file_path)

        # 创建translator实例
        translator = self.get_translator()

        # 进度回调
        def progress_callback(status_msg):
            self.append_status(f"[{filename}] {status_msg}")
            self.window.after(0, lambda: self.update_file_status(file_path, status_msg))

        # 执行翻译
        result = translator.translate_novel(
            file_path,
            genre,
            self.names_db_var.get(),
            progress_callback
        )

        # 更新最终状态
        if result['success']:
            final_status = f"✅ 完成 ({result['duration']:.1f}秒)"
            self.append_status(f"\n[{filename}] {final_status}")
            self.append_status(f"[{filename}] 输出: {result['output_folder']}")
            self.append_status(f"[{filename}] Tokens: {result['tokens']}\n")
        else:
            final_status = f"❌ 失败: {result['error']}"
            self.append_status(f"\n[{filename}] {final_status}\n")

        self.window.after(0, lambda: self.update_file_status(file_path, final_status))

    def run(self):
        """运行应用"""
        self.window.mainloop()


def main():
    """主函数"""
    app = TranslatorApp()
    app.run()


if __name__ == '__main__':
    main()
