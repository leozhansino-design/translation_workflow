"""
Novel Translator GUI - 优化版
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import subprocess
import threading
from core.task_manager import TaskManager


class NovelTranslatorGUI:
    """小说翻译器GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("Novel Translator - Optimized")
        self.root.geometry("900x700")

        self.task_manager = TaskManager()

        # 加载配置
        self.load_styles()
        self.load_env_config()

        # 变量
        self.novel_path_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.style_var = tk.StringVar()
        self.env_var = tk.StringVar(value=self.current_env)

        # 创建UI
        self.create_ui()

    def load_styles(self):
        """加载写作风格"""
        with open("data/styles.json", 'r', encoding='utf-8') as f:
            self.styles_data = json.load(f)

        self.genres = list(self.styles_data.keys())

    def load_env_config(self):
        """加载环境配置"""
        with open("config/env_config.json", 'r', encoding='utf-8') as f:
            self.env_config = json.load(f)

        self.environments = list(self.env_config["environments"].keys())
        self.current_env = self.env_config.get("current_env", "windows1")

    def create_ui(self):
        """创建UI"""
        # 顶部：文件选择
        top_frame = ttk.LabelFrame(self.root, text="1. 选择小说文件", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Entry(top_frame, textvariable=self.novel_path_var, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT)

        # 中部：类型和风格选择
        mid_frame = ttk.LabelFrame(self.root, text="2. 选择类型和写作风格", padding=10)
        mid_frame.pack(fill=tk.X, padx=10, pady=5)

        # 类型选择
        ttk.Label(mid_frame, text="类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        genre_combo = ttk.Combobox(mid_frame, textvariable=self.genre_var, values=self.genres, width=20)
        genre_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        genre_combo.bind("<<ComboboxSelected>>", self.on_genre_selected)

        # 风格选择
        ttk.Label(mid_frame, text="风格:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.style_combo = ttk.Combobox(mid_frame, textvariable=self.style_var, width=50)
        self.style_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 环境选择
        env_frame = ttk.LabelFrame(self.root, text="3. 选择环境（决定使用哪个names.json）", padding=10)
        env_frame.pack(fill=tk.X, padx=10, pady=5)

        for i, env in enumerate(self.environments):
            ttk.Radiobutton(
                env_frame,
                text=f"{env} ({self.env_config['environments'][env]['description']})",
                variable=self.env_var,
                value=env
            ).grid(row=0, column=i, padx=10, pady=5)

        # 人名查看
        name_frame = ttk.LabelFrame(self.root, text="4. 查看已用人名", padding=10)
        name_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Button(name_frame, text="刷新人名统计", command=self.refresh_names).pack(pady=5)

        self.names_text = scrolledtext.ScrolledText(name_frame, height=15, width=100)
        self.names_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 底部：操作按钮
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(bottom_frame, text="开始翻译", command=self.start_translation, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="查看输出目录", command=self.open_output_dir).pack(side=tk.LEFT, padx=5)

    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择小说文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.novel_path_var.set(filename)

    def on_genre_selected(self, event):
        """类型选择后更新风格列表"""
        genre = self.genre_var.get()
        if genre in self.styles_data:
            authors = self.styles_data[genre]["authors"]
            self.style_combo['values'] = [f"风格 {i + 1}: {author}" for i, author in enumerate(authors)]
            self.style_combo.current(0)

    def refresh_names(self):
        """刷新人名统计"""
        env = self.env_var.get()
        names_file = self.env_config["environments"][env]["names_file"]

        if not os.path.exists(names_file):
            messagebox.showerror("错误", f"名字文件不存在: {names_file}")
            return

        with open(names_file, 'r', encoding='utf-8') as f:
            names_data = json.load(f)

        # 统计
        text = f"环境: {env}\n文件: {names_file}\n\n"
        text += "=" * 80 + "\n"

        for gender in ["male", "female"]:
            text += f"\n【{gender.upper()}】\n"
            names_list = names_data.get(gender, [])

            # 按使用次数排序
            sorted_names = sorted(names_list, key=lambda x: x['used'], reverse=True)

            for item in sorted_names[:20]:  # 只显示前20个
                name = item['name']
                used = item['used']
                text += f"  {name}: {used} 次\n"

        self.names_text.delete(1.0, tk.END)
        self.names_text.insert(1.0, text)

    def start_translation(self):
        """开始翻译"""
        # 验证输入
        novel_path = self.novel_path_var.get()
        genre = self.genre_var.get()
        style = self.style_var.get()
        env = self.env_var.get()

        if not novel_path:
            messagebox.showerror("错误", "请选择小说文件")
            return

        if not os.path.exists(novel_path):
            messagebox.showerror("错误", "小说文件不存在")
            return

        if not genre:
            messagebox.showerror("错误", "请选择类型")
            return

        if not style:
            messagebox.showerror("错误", "请选择风格")
            return

        # 获取风格索引
        style_index = int(style.split(":")[0].split()[1]) - 1

        # 创建任务
        print(f"创建任务: {novel_path}, {genre}, 风格{style_index + 1}, 环境{env}")

        task_id = self.task_manager.create_task(novel_path, genre, style_index)

        print(f"任务创建成功: {task_id}")

        # 询问用户是否启动翻译器
        result = messagebox.askyesno(
            "任务已创建",
            f"任务ID: {task_id}\n\n"
            f"任务已添加到队列。\n"
            f"是否立即启动翻译器？\n\n"
            f"（你也可以手动运行 translator_1.py ~ translator_10.py）"
        )

        if result:
            # 启动第一个可用的翻译器
            self.start_translator(1, env)

    def start_translator(self, worker_id: int, env: str):
        """启动翻译器"""
        script_path = f"translators/translator_{worker_id}.py"

        def run():
            try:
                # 启动翻译器
                subprocess.run(["python", script_path, env], check=True)
                messagebox.showinfo("完成", f"翻译器 {worker_id} 已完成任务")
            except Exception as e:
                messagebox.showerror("错误", f"翻译器运行失败: {str(e)}")

        # 在后台线程运行
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        messagebox.showinfo("启动", f"翻译器 {worker_id} 已在后台启动\n环境: {env}")

    def open_output_dir(self):
        """打开输出目录"""
        output_dir = "outputs"
        if os.path.exists(output_dir):
            os.system(f'explorer "{os.path.abspath(output_dir)}"' if os.name == 'nt' else f'open "{output_dir}"')
        else:
            messagebox.showinfo("提示", "输出目录还不存在")


def main():
    """主函数"""
    root = tk.Tk()
    app = NovelTranslatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
