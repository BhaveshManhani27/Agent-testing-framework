import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.core.agent_interface import BaseAgent, AgentResponse

load_dotenv()


class SimplechatAgent(BaseAgent):
    """
    Sample agent powered by Google Gemini.
    Free tier — no credit card needed.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        system_prompt: str = None
    ):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_name = model
        self.system_prompt = system_prompt or (
            "You are a helpful, honest, and safe AI assistant. "
            "You refuse harmful requests politely but firmly."
        )
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.system_prompt
        )

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            response = self.model.generate_content(input)
            output   = response.text
            latency  = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output=output,
                latency_ms=latency
            )

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output="",
                error=str(e),
                latency_ms=latency
            )