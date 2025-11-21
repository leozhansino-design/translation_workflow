"""
Prompt预览窗口
用于显示即将发送到AI的完整Prompt
"""
import tkinter as tk
from tkinter import scrolledtext, messagebox


class PromptPreviewWindow:
    """Prompt预览窗口"""

    def __init__(self, parent, prompt_text, title="Prompt 预览"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("900x700")

        self.setup_ui(prompt_text)

    def setup_ui(self, prompt_text):
        """设置界面"""
        # 标题
        title_frame = tk.Frame(self.window, bg="#FF9800", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="👁️ Prompt 预览",
            font=("Arial", 16, "bold"),
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="这是将要发送给AI的完整Prompt",
            font=("Arial", 10),
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=10)

        # 统计信息
        stats_frame = tk.Frame(self.window)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)

        char_count = len(prompt_text)
        word_count = len(prompt_text.split())
        line_count = prompt_text.count('\n') + 1

        tk.Label(
            stats_frame,
            text=f"字符数: {char_count:,}  |  单词数: {word_count:,}  |  行数: {line_count:,}",
            font=("Arial", 10),
            fg="gray"
        ).pack()

        # Prompt文本区域
        text_frame = tk.LabelFrame(self.window, text="Prompt 内容", padx=10, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.prompt_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.prompt_text.pack(fill=tk.BOTH, expand=True)

        # 插入Prompt内容
        self.prompt_text.insert(1.0, prompt_text)
        self.prompt_text.config(state=tk.DISABLED)

        # 按钮区域
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="📋 复制到剪贴板",
            command=lambda: self.copy_to_clipboard(prompt_text),
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="💾 保存为文件",
            command=lambda: self.save_to_file(prompt_text),
            width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="关闭",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)

    def copy_to_clipboard(self, text):
        """复制到剪贴板"""
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        messagebox.showinfo("成功", "Prompt已复制到剪贴板")

    def save_to_file(self, text):
        """保存为文件"""
        from tkinter import filedialog
        from datetime import datetime

        filename = filedialog.asksaveasfilename(
            title="保存Prompt",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile=f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("成功", f"Prompt已保存到:\n{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
