
import os
from prompting import PromptEngine
from llm import chat_completion_request
from workspace import Workspace
from agent_log import AgentLogger
LOG = AgentLogger(__name__)

class AIPlanning:
    def __init__(
        self, 
        task: str,
        task_id: str,
        abilities: str,
        workspace: Workspace,
        model: str = os.getenv("OPENAI_MODEL")):
        
        self.task = task
        self.task_id = task_id
        self.abilities = abilities
        self.workspace = workspace
        self.model = model
        self.prompt_engine = PromptEngine(self.model)

    async def create_steps(self) -> str:
        abilities_prompt = self.prompt_engine.load_prompt(
            "abilities-list",
            **{"abilities": self.abilities}
        )
        
        step_prompt = self.prompt_engine.load_prompt(
            "get-steps",
            **{
                "task": self.task
            }
        )

        chat_list = [
            {
                "role": "system",
                "content": abilities_prompt
            },
            {
                "role": "system",
                "content": "You are an professional Project Manager."
            },
            {
                "role": "system", 
                "content": step_prompt
            }
        ]

        LOG.info(f" AIPlanner\n")
        for chat in chat_list:
            LOG.info(f"role: {chat['role']}\ncontent: {chat['content']}")

        chat_completion_parms = {
            "messages": chat_list,
            "model": self.model,
            "temperature": 0
        }
        
        response = await chat_completion_request(
            **chat_completion_parms)
            
        return response
