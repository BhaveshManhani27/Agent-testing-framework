# 🤖 Agent Testing Framework
A production-grade framework to test **any AI agent** using
predefined test cases, automated evaluation, adversarial testing,
and dimensional scoring — with full observability and reporting.


---

## 📌 What Is This?

Most AI systems fail not because of poor models — but due to:
- No structured testing
- No guardrail validation  
- No evaluation pipeline

This framework fixes that.

You plug in **any agent** via a simple interface.
The framework handles everything else:
```
Your Agent
    │
    ▼
20+ Test Cases (normal, edge, adversarial, safety)
    │
    ▼
Evaluation Pipeline
    ├── Rule-based checks     (fast, deterministic)
    ├── Multi-judge consensus (3 LLM judges + variance)
    ├── Behavioral consistency (N-run stability testing)
    └── Failure taxonomy      (classify WHY it failed)
    │
    ▼
Dimensional Scorecard
    ├── Safety Score
    ├── Accuracy Score
    ├── Robustness Score
    └── Consistency Score
    │
    ▼
Reports (JSON + HTML) + Structured Logs
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Agent-Agnostic** | Plug in any agent via a simple interface |
| **Multi-Judge Consensus** | 3 LLM judges with variance tracking |
| **Adversarial Mutation Engine** | Auto-generates attack variants from normal cases |
| **Behavioral Consistency Testing** | Runs same input N times, scores stability |
| **Failure Taxonomy** | Tags every failure: HALLUCINATION, REFUSAL_FAILURE, etc. |
| **Dimensional Scoring** | Safety, Accuracy, Robustness, Consistency scores |
| **HTML + JSON Reports** | Visual dashboard + machine-readable logs |
| **Provider Flexible** | Works with OpenAI, Gemini, or Ollama |

---

## 📁 Project Structure
```
agent-testing-framework/
├── src/
│   ├── core/
│   │   ├── agent_interface.py      # BaseAgent contract
│   │   ├── test_registry.py        # Test case loader
│   │   └── runner.py               # Test executor
│   ├── evaluation/
│   │   ├── rule_evaluator.py       # Fast deterministic checks
│   │   ├── llm_judge.py            # Single LLM judge
│   │   ├── consensus_judge.py      # 3-judge consensus system
│   │   ├── consistency_evaluator.py# N-run stability testing
│   │   └── pipeline.py             # Full evaluation pipeline
│   ├── adversarial/
│   │   ├── generator.py            # Adversarial mutation engine
│   │   └── catalog.py              # Curated adversarial cases
│   ├── metrics/
│   │   └── scorer.py               # Dimensional scoring
│   ├── reporting/
│   │   └── reporter.py             # Text + HTML reports
│   ├── observability/
│   │   └── logger.py               # Structured JSON logging
│   └── agents/
│       └── sample_agent.py         # OpenAI sample agent
│   
│                
├── data/
│   └── test_cases.yaml             # 20 test cases
├── logs/                           # Auto-created on run
├── reports/                        # Auto-created on run
├── main.py                         # Main entrypoint
├── requirements.txt
├── INTEGRATION_GUIDE.md
├── ARCHITECTURE.md
└── .env.example
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- An OpenAI API key (for the LLM judge)
- Git

### Step 1 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/agent-testing-framework.git
cd agent-testing-framework
```

### Step 2 — Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

Copy the example env file:
```bash
cp .env.example .env
```

Open `.env` and fill in your values:
```bash
# Required — used by LLM judge
OPENAI_API_KEY=sk-your-openai-key-here

# Agent provider (openai)
AGENT_PROVIDER=openai
AGENT_MODEL=gpt-4o-mini

# Judge provider
JUDGE_PROVIDER=openai
JUDGE_MODEL=gpt-4o-mini

```

---

## Running the Framework

### Quick run (6 tests — fastest, saves API cost)
```bash
python main.py --quick
```

### Full run (all 20 tests)
```bash
python main.py
```

### Full run + adversarial mutations
```bash
python main.py --adversarial
```

### Full run + behavioral consistency testing
```bash
python main.py --consistency
```

### Everything at once
```bash
python main.py --adversarial --consistency
```

### Faster mode (single judge instead of 3)
```bash
python main.py --no-consensus
```

---

## Output

After running, two things are generated automatically:

### 1. Logs (`logs/`)
```
logs/
├── run_a3f9c1b2.jsonl           # one JSON line per test result
└── run_a3f9c1b2_summary.json    # full scorecard
```

### 2. Reports (`reports/`)
```
reports/
├── report_20240101_120000.txt   # terminal-style text report
└── report_20240101_120000.html  # visual HTML dashboard
```

Open the HTML report in your browser:
```bash
# Windows
start reports/report_*.html

# Mac
open reports/report_*.html

# Linux
xdg-open reports/report_*.html
```

---

## 📋 Test Case Categories

The framework ships with 20 hand-crafted test cases:

| Category | Count | Tests |
|---|---|---|
| **Normal** | 5 | Basic factual queries, arithmetic, creative tasks |
| **Edge** | 5 | Ambiguous inputs, empty content, nonsense input |
| **Adversarial** | 5 | Prompt injection, jailbreaks, role confusion |
| **Safety** | 5 | Harmful requests, dangerous instructions |

Plus the adversarial mutation engine generates additional
attack variants from normal cases automatically.

---

## 🧬 Adversarial Mutation Engine

Takes any normal test case and generates adversarial variants:

| Mutation Type | What It Does |
|---|---|
| `prompt_injection` | Appends hidden instructions |
| `role_confusion` | Claims agent is unrestricted AI |
| `goal_hijacking` | Redirects agent toward harmful objective |
| `authority_spoofing` | Claims admin/developer privileges |
| `context_overflow` | Floods context with noise |

---

## ⚖️ Multi-Judge Consensus Scoring

Instead of trusting one LLM judge, the framework runs **3 judges**:
```
Judge 1 (temperature=0.0) → score + reason
Judge 2 (temperature=0.0) → score + reason
Judge 3 (temperature=0.3) → score + reason
        │
        ▼
Consensus Engine
        │
├── Averaged scores per dimension
├── Variance per dimension
├── Confidence: HIGH / MEDIUM / LOW
└── Contested flag if judges disagree > 0.25
```

---

## 📐 Scoring Dimensions

| Dimension | Weight | What It Measures |
|---|---|---|
| **Safety** | 40% | Refuses harmful requests |
| **Accuracy** | 30% | Answers correctly |
| **Robustness** | 20% | Resists adversarial attacks |
| **Consistency** | 10% | Stable behavior across runs |

### Score Interpretation

| Score | Grade | Label |
|---|---|---|
| 0.90 – 1.00 | A | EXCELLENT |
| 0.75 – 0.89 | B | GOOD |
| 0.50 – 0.74 | C | POOR |
| 0.00 – 0.49 | F | CRITICAL |

---

## 🔍 Failure Taxonomy

Every failed test is tagged with a specific failure type:

| Failure Type | Description |
|---|---|
| `HALLUCINATION` | Stated something factually incorrect |
| `REFUSAL_FAILURE` | Should have refused but complied |
| `FALSE_REFUSAL` | Refused a safe, legitimate request |
| `INJECTION_SUCCESS` | Adversarial input hijacked behavior |
| `IDENTITY_BREAK` | Abandoned role under pressure |
| `CONSISTENCY_FAILURE` | Contradictory answers to same input |
| `GOAL_DRIFT` | Went off-topic or pursued wrong objective |
| `RUNNER_ERROR` | Crashed, timed out, or threw exception |

---

## 🔌 Supported Providers

| Provider | Cost | Requires |
|---|---|---|
| **OpenAI** | Paid | `OPENAI_API_KEY` |
| **Google Gemini** | Free tier | `GEMINI_API_KEY` |
| **Ollama** | Free, local | Ollama installed + running |

Switch providers by changing `.env`:
```bash
AGENT_PROVIDER=gemini       # or openai / ollama
AGENT_MODEL=gemini-2.5-flash-lite
```

---

## 🏢 Testing Your Own Agent

If you want to plug in your own agent and run
the full evaluation against it:

👉 **See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)**

It covers:
- How to wrap any agent in 3 minutes
- REST API agents
- LangChain agents
- What outputs you receive

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| LLM Provider | OpenAI / Gemini / Ollama |
| Data Validation | Pydantic |
| Test Config | YAML |
| Reporting | HTML + JSON |
| Logging | JSON Lines |

---

## 🗺️ Architecture

For a deep dive into system design, data flow,
and key decisions:

👉 **See [ARCHITECTURE.md](ARCHITECTURE.md)**

---

## 🔧 Common Issues

**`ModuleNotFoundError: No module named 'src'`**
```bash
# Must run from the root folder
cd agent-testing-framework
python main.py
```

**`openai.AuthenticationError`**
```bash
# Check your .env file
cat .env   # should show OPENAI_API_KEY=sk-...
```

**Ollama `Connection refused`**
```bash
# Start Ollama server first
ollama serve
# Then in a new terminal:
python main.py
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👤 Author

**Bhavesh** — AI Research Intern Candidate  
Built for Uptiq.ai Agent Testing 