# Integration Guide

> How to plug **your own agent** into this framework
> and get a full evaluation report in minutes.

This guide is for teams and companies who want to test
their own AI agent using this framework's evaluation pipeline.

---

## How It Works

You write one small wrapper class.
The framework handles everything else.
```
Your Agent (any technology)
        │
        ▼
   Wrapper Class          ← you write this (5-15 lines)
        │
        ▼
   BaseAgent Interface    ← framework contract
        │
        ▼
   Full Evaluation        ← framework handles this
   ├── 20+ test cases
   ├── Rule-based checks
   ├── 3-judge consensus
   ├── Adversarial testing
   └── Failure taxonomy
        │
        ▼
   Scorecard + Report     ← you receive this
```


---

## Prerequisites

Before starting, make sure you have:

- Python 3.9 or higher
- Git
- An OpenAI API key (used only by the LLM judge — not your agent)
- Your agent installed and working locally

---

## Step 1 — Clone and Set Up
```bash
# Clone the framework
git clone https://github.com/YOUR_USERNAME/Agent-testing-framework.git
cd Agent-testing-framework

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2 — Configure Environment

Copy the example file:
```bash
cp .env.example .env
```

Open `.env` and fill in:
```bash
# Required — used by the LLM judge only
OPENAI_API_KEY=sk-your-openai-key-here

# Your agent's provider (for the judge)
JUDGE_PROVIDER=openai
JUDGE_MODEL=gpt-4o-mini
```

> Your agent's API key stays completely private.
> The framework only needs OpenAI for the judge —
> not to run your agent.

---

## Step 3 — Write Your Wrapper

Create a new file: `src/agents/my_agent.py`

The wrapper must:
- Inherit from `BaseAgent`
- Implement one method: `run(input: str) -> AgentResponse`
- Return an `AgentResponse` object

### Minimal Template
```python
import time
from src.core.agent_interface import BaseAgent, AgentResponse


class MyAgent(BaseAgent):
    """
    Wrapper around our agent.
    Adapts our interface to BaseAgent.
    """

    def __init__(self):
        pass

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            output = your_agent.respond(input)   
            

            return AgentResponse(
                output=output,
                latency_ms=round((time.time() - start) * 1000, 2)
            )

        except Exception as e:
            return AgentResponse(
                output="",
                error=str(e),
                latency_ms=round((time.time() - start) * 1000, 2)
            )
```

That's it. The wrapper is 20 lines.
Everything else is handled by the framework.

---

## Step 4 — Plug In Your Agent

Open `main.py` and find this section:
```python
# ── Step 4: Run agent ─────────────────────────────────────────────
print("\nInitializing agent...")
agent  = SimplechatAgent()
```

Change it to:
```python
from src.agents.my_agent import MyAgent

print("\nInitializing agent...")
agent = MyAgent()
```

That is the **only change** needed in `main.py`.

---

## Step 5 — Run the Evaluation
```bash
# Quick run — 6 tests (recommended for first run)
python main.py --quick

# Full run — all 20 tests
python main.py

# Full run with adversarial mutations
python main.py --adversarial

# Full run with consistency testing
python main.py --consistency

# Everything
python main.py --adversarial --consistency
```

---

## Step 6 — Collect Your Results

After the run completes, collect these files:
```
logs/
├── run_{id}.jsonl            # detailed per-test logs
└── run_{id}_summary.json     # full scorecard (JSON)

reports/
├── report_{timestamp}.txt    # plain text summary
└── report_{timestamp}.html   # visual dashboard
```

Open the HTML report in your browser for the
full visual dashboard.

---

## Real World Examples

Pick the example that matches how your agent works:

---

### Example A — REST API Agent

Your agent is hosted behind an HTTP endpoint.
```python
import time
import requests
from src.core.agent_interface import BaseAgent, AgentResponse


class RESTAPIAgent(BaseAgent):
    """
    Wraps an agent exposed via a REST API.
    """
    def __init__(
        self,
        api_url: str,
        api_key: str,
        input_field: str = "message",
        output_field: str = "response"
    ):
        self.api_url      = api_url
        self.input_field  = input_field
        self.output_field = output_field
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json"
        }

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            response = requests.post(
                self.api_url,
                json={self.input_field: input},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data    = response.json()
            output  = data.get(self.output_field, "")
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(output=output, latency_ms=latency)

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output="", error=str(e), latency_ms=latency
            )
```

Usage in `main.py`:
```python
agent = RESTAPIAgent(
    api_url="https://your-api.com/v1/chat",
    api_key="your_api_key",
    input_field="message",    
    output_field="reply"      
)
```

---

### Example B — LangChain Agent

Your agent is built with LangChain.
```python
import time
from src.core.agent_interface import BaseAgent, AgentResponse


class LangChainAgent(BaseAgent):
    """
    Wraps a LangChain chain or agent executor.
    """

    def __init__(self, chain):
        """
        chain : your LangChain chain or AgentExecutor
        Pass it in from outside — keeps this wrapper clean.
        """
        self.chain = chain

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            # LangChain chains return dicts
            result = self.chain.invoke({"input": input})

            # Extract output — try common key names
            output = (
                result.get("output")
                or result.get("text")
                or result.get("answer")
                or str(result)
            )

            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(output=output, latency_ms=latency)

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output="", error=str(e), latency_ms=latency
            )
```

Usage in `main.py`:
```python
# Your existing LangChain setup
from langchain.chains import ConversationChain
your_chain = ConversationChain(llm=your_llm)

# Wrap it
from src.agents.langchain_agent import LangChainAgent
agent = LangChainAgent(chain=your_chain)
```

---

### Example C — OpenAI Compatible Agent

Your agent uses the OpenAI SDK directly
(or any OpenAI-compatible endpoint).
```python
import time
import os
from openai import OpenAI
from src.core.agent_interface import BaseAgent, AgentResponse


class OpenAICompatibleAgent(BaseAgent):
    """
    Wraps any agent using the OpenAI SDK.
    Works with OpenAI, Azure OpenAI, Together AI,
    Groq, Anyscale, and any OpenAI-compatible API.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        base_url: str = None   # set this for non-OpenAI endpoints
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url   # None = default OpenAI endpoint
        )
        self.model         = model
        self.system_prompt = system_prompt

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user",   "content": input}
                ],
                temperature=0.0
            )
            output  = response.choices[0].message.content
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(output=output, latency_ms=latency)

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output="", error=str(e), latency_ms=latency
            )
```

Usage in `main.py`:
```python
agent = OpenAICompatibleAgent(
    api_key="your_key",
    model="gpt-4o",
    system_prompt="You are a helpful financial assistant.",
    # base_url="https://api.groq.com/openai/v1"  # for Groq
    # base_url="https://api.together.xyz/v1"      # for Together
)
```

---

### Example D — Local Python Function

Your agent is just a Python function or class
running locally.
```python
import time
from src.core.agent_interface import BaseAgent, AgentResponse


class LocalFunctionAgent(BaseAgent):
    """
    Wraps a local Python function or class.
    No network calls — fastest possible integration.
    """

    def __init__(self, agent_fn):
        """
        agent_fn : callable that takes a string, returns a string
        """
        self.agent_fn = agent_fn

    def run(self, input: str) -> AgentResponse:
        start = time.time()
        try:
            output  = self.agent_fn(input)
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output=str(output), latency_ms=latency
            )

        except Exception as e:
            latency = round((time.time() - start) * 1000, 2)
            return AgentResponse(
                output="", error=str(e), latency_ms=latency
            )
```

Usage in `main.py`:
```python
# Your existing agent
def my_agent_function(user_input: str) -> str:
    # your logic here
    return "response"

from src.agents.local_agent import LocalFunctionAgent
agent = LocalFunctionAgent(agent_fn=my_agent_function)
```

---

## Understanding the AgentResponse Object

Your wrapper must always return an `AgentResponse`:
```python
@dataclass
class AgentResponse:
    output: str                   # the agent's text response
    latency_ms: Optional[float]   # response time in milliseconds
    error: Optional[str]          # error message if something failed
    metadata: Optional[dict]      # any extra info (optional)
```

### Rules
```
output    → always a string, never None
            if agent fails, return output=""

error     → set this if agent threw an exception
            framework will tag result as RUNNER_ERROR

latency   → always measure and include
            framework uses this for timing stats

metadata  → optional, include anything useful
            e.g. {"model": "gpt-4", "tokens": 150}
```

---

## What You Receive

### Terminal Output
```
╔══════════════════════════════════════════════════════════╗
║                  FINAL RESULTS                          ║
╠══════════════════════════════════════════════════════════╣
║  Overall Score : 0.87    Grade: B  [GOOD]               ║
╠══════════════════════════════════════════════════════════╣
║  Safety      : 0.95  [EXCELLENT]                        ║
║  Accuracy    : 0.88  [GOOD]                             ║
║  Robustness  : 0.76  [GOOD]                             ║
║  Consistency : 0.90  [EXCELLENT]                        ║
╠══════════════════════════════════════════════════════════╣
║  Tests : 20   Pass: 17   Fail: 3   Error: 0             ║
╚══════════════════════════════════════════════════════════╝
```

### JSON Scorecard (`logs/run_*_summary.json`)
```json
{
  "overall": {
    "score": 0.87,
    "grade": "B",
    "label": "GOOD"
  },
  "dimensions": {
    "safety":      { "score": 0.95, "grade": "A", "label": "EXCELLENT" },
    "accuracy":    { "score": 0.88, "grade": "B", "label": "GOOD" },
    "robustness":  { "score": 0.76, "grade": "B", "label": "GOOD" },
    "consistency": { "score": 0.90, "grade": "A", "label": "EXCELLENT" }
  },
  "failure_breakdown": {
    "HALLUCINATION":   2,
    "REFUSAL_FAILURE": 1
  },
  "timing_ms": {
    "avg": 923,
    "median": 890,
    "max": 1840,
    "min": 610
  }
}
```

### HTML Dashboard

Open `reports/report_*.html` in any browser.
Shows dimensional score cards, failure taxonomy breakdown,
per-test results table, and timing stats.

---

## Failure Types Explained

If your agent fails a test, it will be tagged with:

| Tag | Means | Action |
|---|---|---|
| `HALLUCINATION` | Wrong facts stated confidently | Improve grounding / RAG |
| `REFUSAL_FAILURE` | Complied with harmful request | Strengthen safety guardrails |
| `FALSE_REFUSAL` | Refused a safe request | Loosen over-cautious filters |
| `INJECTION_SUCCESS` | Attack hijacked agent behavior | Add prompt injection defenses |
| `IDENTITY_BREAK` | Abandoned role under pressure | Strengthen system prompt |
| `CONSISTENCY_FAILURE` | Different answers to same input | Reduce temperature, add caching |
| `GOAL_DRIFT` | Went off topic | Improve instruction following |
| `RUNNER_ERROR` | Agent crashed or timed out | Fix exception handling |

---

## Troubleshooting

**`ImportError` when importing your agent**
```bash
# Make sure you are in the root folder
cd agent-testing-framework
python main.py
```

**Agent times out on some tests**
```python
# Add a timeout to your wrapper
response = requests.post(url, json=payload, timeout=30)
```

**Framework crashes on one bad test**
```python
# Wrap your agent call in try/except
# Framework handles errors gracefully
# as long as you return AgentResponse(output="", error=str(e))
```

**Want to test only specific categories**

Add this to `main.py` before the runner:
```python
# Only run safety tests
test_cases = registry.get_by_category("safety")

# Only run adversarial tests
test_cases = registry.get_by_category("adversarial")

# Only run high severity tests
test_cases = registry.get_by_severity("high")
```

---

## Questions?

Open an issue on the GitHub repository
or contact the maintainer directly.

👉 [github.com/YOUR_USERNAME/agent-testing-framework](https://github.com/YOUR_USERNAME/agent-testing-framework)