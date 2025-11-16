"""
配置管理 - 负责读写配置文件
"""

import json
import os
from typing import Optional


class ConfigManager:
    def __init__(self, data_dir: str = "data"):
        self.config_file = os.path.join(data_dir, "config.json")
        self.summary_file = os.path.join(data_dir, "summary.json")

    def load_config(self) -> dict:
        """加载配置"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "api_key": "",
            "api_base_url": "https://api.openai.com/v1",
            "max_workers": 10,
            "model": "gpt-5.1",
            "temperature": 0.8,
            "max_tokens": 100000,
            "cost_per_1k_input": 0.01,
            "cost_per_1k_output": 0.03
        }

    def save_config(self, config: dict):
        """保存配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_api_key(self) -> str:
        """获取API Key"""
        config = self.load_config()
        return config.get("api_key", "")

    def set_api_key(self, api_key: str):
        """设置API Key"""
        config = self.load_config()
        config["api_key"] = api_key
        self.save_config(config)

    def get_api_base_url(self) -> str:
        """获取API Base URL"""
        config = self.load_config()
        return config.get("api_base_url", "https://api.openai.com/v1")

    def set_api_base_url(self, url: str):
        """设置API Base URL"""
        config = self.load_config()
        config["api_base_url"] = url
        self.save_config(config)

    def get_max_workers(self) -> int:
        """获取最大线程数"""
        config = self.load_config()
        return config.get("max_workers", 10)

    def set_max_workers(self, workers: int):
        """设置最大线程数"""
        config = self.load_config()
        config["max_workers"] = workers
        self.save_config(config)

    def get_model_config(self) -> dict:
        """获取模型配置"""
        config = self.load_config()
        return {
            "model": config.get("model", "gpt-4-turbo-preview"),
            "temperature": config.get("temperature", 0.8),
            "max_tokens": config.get("max_tokens", 50000)
        }

    def get_cost_config(self) -> dict:
        """获取成本配置"""
        config = self.load_config()
        return {
            "cost_per_1k_input": config.get("cost_per_1k_input", 0.01),
            "cost_per_1k_output": config.get("cost_per_1k_output", 0.03)
        }

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        cost_config = self.get_cost_config()
        input_cost = (input_tokens / 1000) * cost_config["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * cost_config["cost_per_1k_output"]
        return input_cost + output_cost

    def load_summary(self) -> dict:
        """加载翻译记录"""
        if os.path.exists(self.summary_file):
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"records": []}

    def save_summary(self, summary: dict):
        """保存翻译记录"""
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def add_record(self, record: dict):
        """添加翻译记录"""
        summary = self.load_summary()
        summary["records"].append(record)
        self.save_summary(summary)
