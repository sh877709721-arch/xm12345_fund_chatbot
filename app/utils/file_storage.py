import os
from typing import Optional
from pathlib import Path


class FileStorage:
    """文件存储工具类"""

    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def get_upload_dir(self, subfolder: str = "") -> Path:
        """获取上传目录路径"""
        if subfolder:
            return self.base_dir / subfolder
        return self.base_dir

    def get_file_path(self, filename: str, subfolder: str = "") -> Path:
        """获取文件完整路径"""
        upload_dir = self.get_upload_dir(subfolder)
        return upload_dir / filename

    def get_file_url(self, filename: str, subfolder: str = "") -> str:
        """获取文件访问URL"""
        if subfolder:
            return f"/{self.base_dir.name}/{subfolder}/{filename}"
        return f"/{self.base_dir.name}/{filename}"

    def ensure_dir(self, subfolder: str = "") -> Path:
        """确保目录存在"""
        upload_dir = self.get_upload_dir(subfolder)
        upload_dir.mkdir(exist_ok=True)
        return upload_dir

    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception:
            return False


# 全局文件存储实例
file_storage = FileStorage()