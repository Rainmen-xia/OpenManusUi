from typing import List

from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.prompt.swe import *
from app.tool import Bash, StrReplaceEditor, Terminate, ToolCollection


class SWEAgent(ToolCallAgent):
    """An agent that implements the SWEAgent paradigm for executing code and natural conversations."""

    name: str = "swe"
    description: str = "an autonomous AI programmer that interacts directly with the computer to solve tasks."

    system_prompt: str = ZH_SYSTEM_PROMPT
    next_step_prompt: str = ZH_NEXT_STEP_TEMPLATE

    available_tools: ToolCollection = ToolCollection(
        Bash(), StrReplaceEditor(), Terminate()
    )
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    max_steps: int = 30

    bash: Bash = Field(default_factory=Bash)
    working_dir: str = "."

    async def think(self) -> bool:
        """Process current state and decide next action"""
        # Update working directory
        self.working_dir = await self.bash.execute("pwd")
        self.next_step_prompt = self.next_step_prompt.format(
            current_dir=self.working_dir
        )

        return await super().think()
