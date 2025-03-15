"""
项目主入口文件
"""

# 导入补丁文件，修复six.moves导入问题
import six_patch  # 这行必须放在其他导入语句之前

import asyncio

from app.agent.manus import Manus
from app.logger import logger


async def main():
    agent = Manus()
    while True:
        try:
            prompt = input("Enter your prompt (or 'exit' to quit): ")
            if prompt.lower() == "exit":
                logger.info("Goodbye!")
                break
            logger.warning("Processing your request...")
            await agent.run(prompt)
        except KeyboardInterrupt:
            logger.warning("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
