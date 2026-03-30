from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentResponse:
    """
    Every agent must return this — not just a raw string.
    This gives us structured data to work with downstream.
    """
    output: str                          
    latency_ms: Optional[float] = None  
    error: Optional[str] = None         
    metadata: Optional[dict] = None     


class BaseAgent(ABC):
    """
    Every agent you want to test must inherit from this class
    and implement the `run` method.

    This is the plug shape — any agent that fits this shape
    can be tested by the framework without changing any other code.
    """

    @abstractmethod
    def run(self, input: str) -> AgentResponse:
        """
        Takes a user input string.
        Returns an AgentResponse object.
        Must be implemented by every agent.
        """
        pass

    def __str__(self):
        return self.__class__.__name__