import time
import os
from google import genai
from dotenv import load_dotenv
from src.core.agent_interface import BaseAgent, AgentResponse
from src.observability.log_config import get_logger

load_dotenv()

logger = get_logger(__name__)


class SimpleChatAgent(BaseAgent):
    """
    Sample agent powered by Google Gemini.
    Uses new google-genai package.
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash-lite",
        system_prompt: str = None
    ):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model_name    = model
        self.system_prompt = system_prompt or (
            "You are a helpful, honest, and safe AI assistant. "
            "You refuse harmful requests politely but firmly."
        )

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            # Combine system prompt + user input inline
            full_input = (
                f"{self.system_prompt}\n\nUser: {input}"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_input
            )
            output  = response.text
            latency = round((time.time() - start) * 1000, 2)

            # Estimate token count for cost tracking
            try:
                from src.observability.cost_tracker import COST_TRACKER
                input_tokens = len(full_input.split())
                output_tokens = len(output.split())
                COST_TRACKER.record_call(
                    component="agent",
                    model=self.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
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