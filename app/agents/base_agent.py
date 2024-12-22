from abc import ABC, abstractmethod
from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.assistant = None
        self.tools = []
        self._setup_assistant()

    @abstractmethod
    def _setup_assistant(self):
        """Setup the OpenAI assistant with specific tools and instructions"""
        pass

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the agent's main functionality"""
        pass

    async def _run_assistant(self, prompt: str) -> Dict[str, Any]:
        """Run the assistant with a given prompt"""
        thread = self.client.beta.threads.create()
        
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id
        )

        # Wait for completion
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                raise Exception("Assistant run failed")

        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        return messages.data[0].content[0].text.value 