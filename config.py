"""
配置管理模块
"""
import json
import os

CONFIG_FILE = 'data/config.json'


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
                'api_key': '',
                'model': 'gpt-4-turbo-preview',
                'max_workers': 10,
                'temperature': 0.8,
                'max_tokens': 50000
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
        return self.config.get('api_key', '')

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
        return self.config.get('max_tokens', 50000)


# 全局配置实例
config = Config()
