import time
import os
from groq import Groq
from dotenv import load_dotenv
from src.core.agent_interface import BaseAgent, AgentResponse
from src.observability.log_config import get_logger

load_dotenv()

logger = get_logger(__name__)


class SimpleChatAgent(BaseAgent):
    """
    Sample agent powered by Groq (LPU inference).
    Uses the Groq Python SDK with Llama 3.3 70B.
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        system_prompt: str = None
    ):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model_name    = model
        self.system_prompt = system_prompt or (
            "You are a helpful, honest, and safe AI assistant. "
            "You refuse harmful requests politely but firmly."
        )

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": input}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            output  = response.choices[0].message.content
            latency = round((time.time() - start) * 1000, 2)

            # Track token usage for cost reporting
            try:
                from src.observability.cost_tracker import COST_TRACKER
                usage = response.usage
                COST_TRACKER.record_call(
                    component="agent",
                    model=self.model_name,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                )
            except Exception:
                pass  # Cost tracking is optional

            return AgentResponse(output=output, latency_ms=latency)

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            logger.error("AGENT ERROR: %s", str(e))
            return AgentResponse(
                output="",
                error=str(e),
                latency_ms=latency
            )