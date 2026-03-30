import time
import os
from openai import OpenAI
from dotenv import load_dotenv

from src.core.agent_interface import BaseAgent, AgentResponse

load_dotenv()

class SimplechatAgent(BaseAgent):
    """
    A basic chatbot agent powered by GPT.
    This is the sample agent we'll use to demonstrate the framework.
    """

    def __init__(self, model: str = "gpt-4o-mini", system_prompt: str = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.system_prompt = system_prompt or (
            "You are a helpful, honest, and safe AI assistant. "
            "You refuse harmful requests politely but firmly."
        )

    def run(self, input: str) -> AgentResponse:
        start = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user",   "content": input}
                ],
                temperature=0.0   # Deterministic output for testing
            )

            output = response.choices[0].message.content
            latency = (time.time() - start) * 1000  # convert to ms

            return AgentResponse(
                output=output,
                latency_ms=round(latency, 2)
            )

        except Exception as e:
            return AgentResponse(
                output="",
                error=str(e),
                latency_ms=round((time.time() - start) * 1000, 2)
            )