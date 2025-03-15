# 导入补丁文件，修复six.moves导入问题
import six_patch  # 这行必须放在其他导入语句之前

import asyncio

from app.agent.manus import Manus
from app.flow.base import FlowType
from app.flow.flow_factory import FlowFactory


async def run_flow():
    agent = Manus()

    while True:
        try:
            prompt = input("Enter your prompt (or 'exit' to quit): ")
            if prompt.lower() == "exit":
                print("Goodbye!")
                break

            flow = FlowFactory.create_flow(
                flow_type=FlowType.PLANNING,
                agents=agent,
            )

            print("Processing your request...")
            result = await flow.execute(prompt)
            print(result)

        except KeyboardInterrupt:
            print("Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(run_flow())
