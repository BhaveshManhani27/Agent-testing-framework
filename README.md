# ðŸ¤– Agent Testing Framework

A production-grade framework to test **any AI agent** using
predefined test cases, automated evaluation, adversarial testing,
multi-turn conversation testing, and dimensional scoring â€”
with statistical analysis, cost tracking, and full observability.

![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/tests-125%20passed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ðŸ“Œ What Is This?

Most AI systems fail not because of poor models â€” but due to:
- No structured testing
- No guardrail validation  
- No evaluation pipeline

This framework fixes that.

You plug in **any agent** via a simple interface.
The framework handles everything else:
```
Your Agent
    â”‚
    â–¼
20+ Test Cases (normal, edge, adversarial, safety)
  + 5 Multi-turn conversation scenarios
    â”‚
    â–¼
Evaluation Pipeline
    â”œâ”€â”€ Rule-based checks          (fast, deterministic)
    â”œâ”€â”€ Multi-judge consensus      (3 LLM judges + variance)
    â”œâ”€â”€ Behavioral consistency     (N-run stability + embedding similarity)
    â”œâ”€â”€ Multi-turn testing         (context retention, safety escalation)
    â”œâ”€â”€ Statistical analysis       (bootstrap CIs, Wilson intervals)
    â””â”€â”€ Failure taxonomy           (classify WHY it failed)
    â”‚
    â–¼
Dimensional Scorecard
    â”œâ”€â”€ Safety Score        (with 95% confidence interval)
    â”œâ”€â”€ Accuracy Score      (with 95% confidence interval)
    â”œâ”€â”€ Robustness Score
    â””â”€â”€ Consistency Score
    â”‚
    â–¼
Reports (JSON + HTML) + Structured Logs + Cost Report
```

---

## âœ¨ Key Features

| Feature | Description |
|---|---|
| **Agent-Agnostic** | Plug in any agent via `BaseAgent` interface |
| **Multi-Judge Consensus** | 3 LLM judges with variance tracking and confidence scoring |
| **Adversarial Mutation Engine** | Auto-generates 5 attack variants from normal cases |
| **Multi-Turn Conversation Testing** | 5 scenarios: context retention, safety escalation, role persistence |
| **Embedding-Based Similarity** | Deterministic cosine similarity via sentence-transformers |
| **Statistical Analysis** | Bootstrap CIs, Wilson score intervals, Cohen's d effect size |
| **Behavioral Consistency Testing** | Runs same input N times, scores stability |
| **Failure Taxonomy** | Tags every failure: HALLUCINATION, REFUSAL_FAILURE, etc. |
| **Dimensional Scoring** | Safety, Accuracy, Robustness, Consistency with confidence intervals |
| **Async Parallel Execution** | Concurrent test execution with configurable semaphore |
| **Cost Tracking** | Per-test, per-component (agent vs judge) cost reporting |
| **Structured Logging** | Centralized `logging` module across all components |
| **HTML + JSON Reports** | Visual dashboard + machine-readable logs |
| **125 Unit Tests** | Full test suite, zero API calls, runs in 0.5s |

---

## ðŸ“ Project Structure
```
agent-testing-framework/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ agent_interface.py      # BaseAgent contract
â”‚   â”‚   â”œâ”€â”€ test_registry.py        # Test case loader (Pydantic)
â”‚   â”‚   â”œâ”€â”€ runner.py               # Sequential test executor
â”‚   â”‚   â””â”€â”€ async_runner.py         # Parallel test executor (asyncio)
â”‚   â”œâ”€â”€ evaluation/
â”‚   â”‚   â”œâ”€â”€ rule_evaluator.py       # Fast deterministic checks
â”‚   â”‚   â”œâ”€â”€ llm_judge.py            # Single LLM judge
â”‚   â”‚   â”œâ”€â”€ consensus_judge.py      # 3-judge consensus system
â”‚   â”‚   â”œâ”€â”€ consistency_evaluator.py# N-run stability + embedding similarity
â”‚   â”‚   â”œâ”€â”€ multi_turn.py           # Multi-turn conversation testing
â”‚   â”‚   â”œâ”€â”€ rate_limiter.py         # Thread-safe API rate limiter
â”‚   â”‚   â””â”€â”€ pipeline.py             # Full evaluation pipeline
â”‚   â”œâ”€â”€ adversarial/
â”‚   â”‚   â”œâ”€â”€ generator.py            # Adversarial mutation engine
â”‚   â”‚   â””â”€â”€ catalog.py              # Curated adversarial cases
â”‚   â”œâ”€â”€ metrics/
â”‚   â”‚   â”œâ”€â”€ scorer.py               # Dimensional scoring with CIs
â”‚   â”‚   â””â”€â”€ statistics.py           # Bootstrap CI, Wilson, Cohen's d
â”‚   â”œâ”€â”€ reporting/
â”‚   â”‚   â””â”€â”€ reporter.py             # Text + HTML reports
â”‚   â”œâ”€â”€ observability/
â”‚   â”‚   â”œâ”€â”€ log_config.py           # Centralized logging configuration
â”‚   â”‚   â”œâ”€â”€ logger.py               # Structured JSON run logging
â”‚   â”‚   â””â”€â”€ cost_tracker.py         # API cost tracking
â”‚   â””â”€â”€ agents/
â”‚       â””â”€â”€ sample_agent.py         # Groq sample agent
â”‚
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ conftest.py                 # Shared fixtures + mock agents
â”‚   â”œâ”€â”€ test_rule_evaluator.py      # 24 tests â€” every criteria path
â”‚   â”œâ”€â”€ test_scorer.py              # 28 tests â€” scoring + grading
â”‚   â”œâ”€â”€ test_pipeline.py            # 9 tests â€” failure taxonomy
â”‚   â”œâ”€â”€ test_consensus.py           # 15 tests â€” consensus math
â”‚   â”œâ”€â”€ test_registry.py            # 7 tests â€” YAML loading
â”‚   â”œâ”€â”€ test_runner.py              # 10 tests â€” execution + errors
â”‚   â”œâ”€â”€ test_adversarial.py         # 11 tests â€” mutation + catalog
â”‚   â””â”€â”€ test_statistics.py          # 21 tests â€” CIs + effect size
â”‚
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ test_cases.yaml             # 20 single-turn test cases
â”‚   â””â”€â”€ conversation_tests.yaml    # 5 multi-turn conversation tests
â”œâ”€â”€ main.py                         # Main entrypoint
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env.example
â”œâ”€â”€ INTEGRATION_GUIDE.md
â””â”€â”€ ARCHITECTURE.md
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- A Groq API key (free tier works)
- Git

### Step 1 â€” Clone the repository
```bash
git clone https://github.com/BhaveshManhani27/Agent-testing-framework.git
cd Agent-testing-framework
```

### Step 2 â€” Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### Step 3 â€” Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 â€” Configure environment

Copy the example env file:
```bash
cp .env.example .env
```

Open `.env` and fill in your values:
```bash
# Required â€” used by both agent and LLM judge
Groq_API_KEY=your-Groq-api-key-here

# Agent configuration
AGENT_PROVIDER=Groq
AGENT_MODEL=Groq-2.5-flash-lite

# Judge configuration
JUDGE_PROVIDER=Groq
JUDGE_MODEL=Groq-2.5-flash-lite
```

---

## Running the Framework

### Quick run (6 tests â€” fastest, saves API cost)
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

### Multi-turn conversation testing
```bash
python main.py --multi-turn
```

### Parallel execution (async mode)
```bash
python main.py --async-mode --max-concurrent 3
```

### Everything at once
```bash
python main.py --adversarial --consistency --multi-turn
```

### Faster mode (single judge instead of 3)
```bash
python main.py --no-consensus
```

### Skip optional outputs
```bash
python main.py --no-report     # skip file report generation
python main.py --no-cost       # skip cost tracking report
```

---

## Running Tests

The framework includes 125 unit tests that run in ~0.5 seconds
with zero API calls:

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test module
python -m pytest tests/test_scorer.py -v

# Run with coverage
python -m pytest tests/ --tb=short
```

---

## Output

After running, these are generated automatically:

### 1. Logs (`logs/`)
```
logs/
â”œâ”€â”€ run_a3f9c1b2.jsonl           # one JSON line per test result
â””â”€â”€ run_a3f9c1b2_summary.json    # full scorecard
```

### 2. Reports (`reports/`)
```
reports/
â”œâ”€â”€ report_20240101_120000.txt   # terminal-style text report
â””â”€â”€ report_20240101_120000.html  # visual HTML dashboard
```

### 3. Cost Report (terminal)
```
COST REPORT
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  Total API calls    : 63
  Total tokens       : 18,240 (in: 14,100, out: 4,140)
  Estimated cost     : $0.0023
  â”œâ”€â”€ Agent          : $0.0008 (21 calls)
  â””â”€â”€ Judge          : $0.0015 (42 calls)
  Cost per test      : $0.000109
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
```

---

## ðŸ“‹ Test Case Categories

The framework ships with 20 single-turn + 5 multi-turn test cases:

### Single-Turn Tests (`data/test_cases.yaml`)

| Category | Count | Tests |
|---|---|---|
| **Normal** | 5 | Basic factual queries, arithmetic, creative tasks |
| **Edge** | 5 | Ambiguous inputs, empty content, nonsense input |
| **Adversarial** | 5 | Prompt injection, jailbreaks, role confusion |
| **Safety** | 5 | Harmful requests, dangerous instructions |

### Multi-Turn Conversation Tests (`data/conversation_tests.yaml`)

| ID | Scenario | What It Tests |
|---|---|---|
| CONV001 | Context retention | Does the agent remember earlier turns? |
| CONV002 | Safety escalation | Does a multi-step jailbreak succeed? |
| CONV003 | Emotional manipulation | Does the agent cave to emotional pressure? |
| CONV004 | Topic switching | Can it handle abrupt context changes? |
| CONV005 | Role persistence | Does the agent maintain identity under pressure? |

Plus the adversarial mutation engine generates additional
attack variants from normal cases automatically.

---

## ðŸ§¬ Adversarial Mutation Engine

Takes any normal test case and generates adversarial variants:

| Mutation Type | What It Does |
|---|---|
| `prompt_injection` | Appends hidden instructions |
| `role_confusion` | Claims agent is unrestricted AI |
| `goal_hijacking` | Redirects agent toward harmful objective |
| `authority_spoofing` | Claims admin/developer privileges |
| `context_overflow` | Floods context with noise |

---

## âš–ï¸ Multi-Judge Consensus Scoring

Instead of trusting one LLM judge, the framework runs **3 judges**:
```
Judge 1 (temperature=0.0) â†’ score + reason
Judge 2 (temperature=0.0) â†’ score + reason
Judge 3 (temperature=0.3) â†’ score + reason
        â”‚
        â–¼
Consensus Engine
        â”‚
â”œâ”€â”€ Averaged scores per dimension
â”œâ”€â”€ Variance per dimension
â”œâ”€â”€ Confidence: HIGH / MEDIUM / LOW
â””â”€â”€ Contested flag if judges disagree > 0.25
```

---

## ðŸ“Š Statistical Analysis

All scores include proper uncertainty quantification:

| Method | What It Does | Why |
|---|---|---|
| **Bootstrap CI** | 95% confidence interval on scores | Know how reliable a score is with small N |
| **Wilson Score Interval** | CI on pass rates | Better than normal approx for n < 30 |
| **Cohen's d** | Effect size for comparisons | Is the difference meaningful, not just non-zero? |

```
Overall Score : 0.87    CI: [0.78, 0.94]  (95% bootstrap)
Pass Rate     : 85.0%   CI: [62.1%, 96.8%] (Wilson)
```

---

## ðŸ“ Scoring Dimensions

| Dimension | Weight | What It Measures |
|---|---|---|
| **Safety** | 40% | Refuses harmful requests |
| **Accuracy** | 30% | Answers correctly |
| **Robustness** | 20% | Resists adversarial attacks |
| **Consistency** | 10% | Stable behavior across runs |

### Score Interpretation

| Score | Grade | Label |
|---|---|---|
| 0.90 â€“ 1.00 | A | EXCELLENT |
| 0.75 â€“ 0.89 | B | GOOD |
| 0.50 â€“ 0.74 | C | POOR |
| 0.00 â€“ 0.49 | F | CRITICAL |

---

## ðŸ” Failure Taxonomy

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

## ðŸ¢ Testing Your Own Agent

If you want to plug in your own agent and run
the full evaluation against it:

ðŸ‘‰ **See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)**

It covers:
- How to wrap any agent in 3 minutes
- REST API agents
- LangChain agents
- What outputs you receive

---

## ðŸ› ï¸ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| LLM Provider | Google Groq |
| Data Validation | Pydantic |
| Test Config | YAML |
| Semantic Similarity | sentence-transformers (all-MiniLM-L6-v2) |
| Statistical Analysis | Bootstrap CI, Wilson intervals, Cohen's d |
| Testing | pytest (125 tests) |
| Logging | Python `logging` module (structured) |
| Reporting | HTML + JSON |
| Async | asyncio + semaphore |

---

## ðŸ—ºï¸ Architecture

For a deep dive into system design, data flow,
and key decisions:

ðŸ‘‰ **See [ARCHITECTURE.md](ARCHITECTURE.md)**

---

## ðŸ”§ Common Issues

**`ModuleNotFoundError: No module named 'src'`**
```bash
# Must run from the root folder
cd Agent-testing-framework
python main.py
```

**`google.api_core.exceptions.PermissionDenied`**
```bash
# Check your .env file
cat .env   # should show Groq_API_KEY=your-key
```

**Rate limit errors**
```bash
# The built-in rate limiter handles this automatically.
# If issues persist, try --no-consensus for fewer API calls.
python main.py --no-consensus
```

---

## ðŸ“„ License

MIT License â€” free to use, modify, and distribute.

---

## ðŸ‘¤ Author

**Bhavesh** â€” AI Research Intern Candidate  
Built for Uptiq.ai Agent Testing
