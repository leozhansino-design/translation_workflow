"""
配置管理模块
"""
import json
import os
import sys


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持PyInstaller打包）

    优先使用当前目录的文件，如果不存在则从打包资源复制
    """
    local_path = os.path.join(os.getcwd(), relative_path)

    if os.path.exists(local_path):
        return local_path

    try:
        base_path = sys._MEIPASS
        bundled_path = os.path.join(base_path, relative_path)

        if relative_path.startswith('data/') and os.path.exists(bundled_path):
            os.makedirs(os.path.join(os.getcwd(), 'data'), exist_ok=True)
            import shutil
            try:
                shutil.copy2(bundled_path, local_path)
            except:
                pass

        return local_path

    except AttributeError:
        return local_path


CONFIG_FILE = get_resource_path('data/config.json')


class Config:
    """配置管理类"""

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            return {
                'api_key': 'sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln',
                'model': 'gpt-4-turbo-preview',
                'max_workers': 10,
                'temperature': 0.8,
                'max_tokens': 100000
            }

    def save_config(self):
        """保存配置文件"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()

    def get_api_key(self):
        """获取API密钥"""
        return self.config.get('api_key', 'sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln')

    def set_api_key(self, api_key):
        """设置API密钥"""
        self.set('api_key', api_key)

    def get_max_workers(self):
        """获取最大线程数"""
        return self.config.get('max_workers', 10)

    def set_max_workers(self, max_workers):
        """设置最大线程数"""
        self.set('max_workers', max_workers)

    def get_model(self):
        """获取模型名称"""
        return self.config.get('model', 'gpt-4-turbo-preview')

    def get_temperature(self):
        """获取温度参数"""
        return self.config.get('temperature', 0.8)

    def get_max_tokens(self):
        """获取最大token数"""
        return self.config.get('max_tokens', 100000)


# 全局配置实例
config = Config()
