import asyncio
import os
from pathlib import Path

import aiofiles

from app.tool.base import BaseTool
from app.config import WORKSPACE_ROOT


class FileSaver(BaseTool):
    name: str = "file_saver"
    description: str = """Save content to a local file at a specified path within the workspace directory.
Use this tool when you need to save text, code, or generated content to a file in the workspace.
The tool accepts content and a file path, and saves the content to that location within the workspace.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "(required) The content to save to the file.",
            },
            "file_path": {
                "type": "string",
                "description": "(required) The path where the file should be saved, including filename and extension. Path is relative to the workspace directory.",
            },
            "mode": {
                "type": "string",
                "description": "(optional) The file opening mode. Default is 'w' for write. Use 'a' for append.",
                "enum": ["w", "a"],
                "default": "w",
            },
        },
        "required": ["content", "file_path"],
    }

    async def execute(self, content: str, file_path: str, mode: str = "w") -> str:
        """
        Save content to a file at the specified path within the workspace directory.

        Args:
            content (str): The content to save to the file.
            file_path (str): The path where the file should be saved, relative to the workspace directory.
            mode (str, optional): The file opening mode. Default is 'w' for write. Use 'a' for append.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            # 确保文件路径是相对于workspace目录的
            # 移除开头的斜杠，防止路径解析问题
            if file_path.startswith('/'):
                file_path = file_path[1:]
            
            # 构建完整的文件路径
            full_path = WORKSPACE_ROOT / file_path
            
            # 确保目录存在
            directory = os.path.dirname(full_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            # 写入文件
            async with aiofiles.open(full_path, mode, encoding="utf-8") as file:
                await file.write(content)

            return f"内容已成功保存到工作区: {file_path}"
        except Exception as e:
            return f"保存文件时出错: {str(e)}"

