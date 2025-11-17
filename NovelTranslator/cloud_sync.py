"""
云端数据同步模块 - 支持多台电脑共享配置文件
支持：iCloud Drive, OneDrive, Dropbox, Google Drive, 或自定义路径
"""

import os
import json
import shutil
import platform
from typing import Optional, Dict, Any
from pathlib import Path


class CloudSync:
    """云端同步管理器"""

    def __init__(self):
        self.config_file = self._get_local_config_path()
        self.cloud_config = self._load_cloud_config()

    def _get_local_config_path(self) -> str:
        """获取本地配置文件路径"""
        if platform.system() == 'Darwin':  # macOS
            config_dir = os.path.expanduser("~/Library/Application Support/NovelTranslator")
        elif platform.system() == 'Windows':
            config_dir = os.path.expanduser("~/AppData/Local/NovelTranslator")
        else:  # Linux
            config_dir = os.path.expanduser("~/.config/NovelTranslator")

        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "cloud_sync_config.json")

    def _load_cloud_config(self) -> Dict[str, Any]:
        """加载云端同步配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载云端配置失败: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "enabled": False,
            "cloud_type": "custom",  # icloud, onedrive, dropbox, gdrive, custom
            "cloud_path": "",
            "sync_items": {
                "default_prompt": True,
                "names": True,
                "styles": True,
                "summary": True
            }
        }

    def save_config(self, config: Dict[str, Any]):
        """保存云端配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.cloud_config = config
            return True
        except Exception as e:
            print(f"保存云端配置失败: {e}")
            return False

    def get_suggested_paths(self) -> Dict[str, str]:
        """获取推荐的云端路径（根据操作系统）"""
        system = platform.system()
        suggestions = {}

        if system == 'Darwin':  # macOS
            suggestions['iCloud Drive'] = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/NovelTranslator")
            suggestions['OneDrive'] = os.path.expanduser("~/OneDrive/NovelTranslator")
            suggestions['Dropbox'] = os.path.expanduser("~/Dropbox/NovelTranslator")
            suggestions['Google Drive'] = os.path.expanduser("~/Google Drive/NovelTranslator")

        elif system == 'Windows':
            suggestions['OneDrive'] = os.path.expanduser("~/OneDrive/NovelTranslator")
            suggestions['Dropbox'] = os.path.expanduser("~/Dropbox/NovelTranslator")
            suggestions['Google Drive'] = os.path.expanduser("~/Google Drive/NovelTranslator")

        return suggestions

    def is_enabled(self) -> bool:
        """检查云端同步是否启用"""
        return self.cloud_config.get('enabled', False)

    def get_cloud_path(self) -> Optional[str]:
        """获取云端路径"""
        if not self.is_enabled():
            return None

        cloud_path = self.cloud_config.get('cloud_path', '')
        if cloud_path and os.path.exists(cloud_path):
            return cloud_path
        return None

    def get_data_file_path(self, filename: str, local_path: str) -> str:
        """
        获取数据文件路径（云端或本地）

        Args:
            filename: 文件名 (如 'names.json')
            local_path: 本地路径（fallback）

        Returns:
            实际使用的文件路径
        """
        # 如果云端同步未启用，返回本地路径
        if not self.is_enabled():
            return local_path

        # 检查该文件是否需要同步
        sync_key = filename.replace('.json', '').replace('_', '')
        if not self.cloud_config['sync_items'].get(sync_key, False):
            return local_path

        # 获取云端路径
        cloud_path = self.get_cloud_path()
        if not cloud_path:
            return local_path

        cloud_file = os.path.join(cloud_path, 'data', filename)

        # 如果云端文件不存在，从本地复制
        if not os.path.exists(cloud_file):
            self._sync_local_to_cloud(local_path, cloud_file)

        return cloud_file if os.path.exists(cloud_file) else local_path

    def _sync_local_to_cloud(self, local_file: str, cloud_file: str):
        """从本地同步到云端"""
        try:
            if os.path.exists(local_file):
                os.makedirs(os.path.dirname(cloud_file), exist_ok=True)
                shutil.copy2(local_file, cloud_file)
                print(f"已同步到云端: {cloud_file}")
        except Exception as e:
            print(f"同步到云端失败: {e}")

    def setup_cloud_folder(self, cloud_path: str) -> bool:
        """设置云端文件夹（创建必要的目录结构）"""
        try:
            # 创建主目录
            os.makedirs(cloud_path, exist_ok=True)

            # 创建data子目录
            data_dir = os.path.join(cloud_path, 'data')
            os.makedirs(data_dir, exist_ok=True)

            # 创建README文件说明
            readme_path = os.path.join(cloud_path, 'README.txt')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("""NovelTranslator 云端数据文件夹

此文件夹包含在多台电脑间共享的配置文件：

/data/
  - default_prompt.json  # 翻译Prompt模板
  - names.json          # 人名库
  - styles.json         # 写作风格库
  - summary.json        # 翻译记录

⚠️ 请勿手动删除或修改这些文件，除非你知道自己在做什么。

支持的云存储服务：
- iCloud Drive (macOS)
- OneDrive (Windows/Mac)
- Dropbox (Windows/Mac)
- Google Drive (Windows/Mac)
- 或任何其他支持文件同步的云服务

设置完成后，所有电脑都会自动使用云端的配置文件。
""")

            return True
        except Exception as e:
            print(f"设置云端文件夹失败: {e}")
            return False

    def test_cloud_path(self, cloud_path: str) -> tuple[bool, str]:
        """
        测试云端路径是否可用

        Returns:
            (success, message)
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(cloud_path):
                return False, "路径不存在，请先创建该文件夹"

            # 检查是否可写
            test_file = os.path.join(cloud_path, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                return False, f"无写入权限: {str(e)}"

            return True, "✅ 路径可用"

        except Exception as e:
            return False, f"测试失败: {str(e)}"

    def migrate_local_to_cloud(self, local_data_dir: str) -> bool:
        """将本地数据迁移到云端"""
        cloud_path = self.get_cloud_path()
        if not cloud_path:
            return False

        try:
            cloud_data_dir = os.path.join(cloud_path, 'data')
            os.makedirs(cloud_data_dir, exist_ok=True)

            files_to_sync = ['default_prompt.json', 'names.json', 'styles.json', 'summary.json']

            for filename in files_to_sync:
                local_file = os.path.join(local_data_dir, filename)
                cloud_file = os.path.join(cloud_data_dir, filename)

                if os.path.exists(local_file):
                    shutil.copy2(local_file, cloud_file)
                    print(f"已迁移: {filename}")

            return True
        except Exception as e:
            print(f"迁移失败: {e}")
            return False
