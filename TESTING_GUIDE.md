# 🚀 Quick Testing Guide

## Prerequisites
- Python 3.8+ installed
- OpenAI API key

---

## Step 1: Setup (5 minutes)

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

---

## Step 2: Basic Test (2 minutes)

```bash
# Run the example script
python example.py
```

**Expected Output:**
- 4 queries answered
- Tools used displayed
- Cost and latency metrics
- Overall statistics

**✅ Success if:** No errors, agent responds to all queries

---

## Step 3: Quick Evaluation (5 minutes)

```bash
# Test with easy and medium difficulty cases
python -c "from agent_system.eval.evaluator import run_quick_eval; import asyncio; asyncio.run(run_quick_eval())"
```

**Expected Output:**
- Success rate: ~85-90%
- Tool selection accuracy: ~80-85%
- Results saved to `agent_system/data/eval_results/`

**✅ Success if:** Success rate > 80%

---

## Step 4: Check Results

```bash
# View metrics
tail -20 agent_system/data/metrics.jsonl

# List evaluation results
ls -la agent_system/data/eval_results/
```

---

## Step 5: Interactive Test (Optional)

Create `my_test.py`:

```python
import asyncio
from agent_system.core.agent import Agent
from agent_system.tools.calculator import Calculator
from agent_system.tools.web_search import WebSearch
from agent_system.tools.knowledge_base import KnowledgeBase
from agent_system.tools.document_qa import DocumentQA

async def main():
    tools = [Calculator(), WebSearch(), KnowledgeBase(), DocumentQA()]
    agent = Agent(tools=tools, model="gpt-4o-mini")
    
    # Your custom queries
    queries = [
        "What is 25 * 4?",
        "Tell me about Python",
    ]
    
    for query in queries:
        print(f"\nQ: {query}")
        response = await agent.run(query)
        print(f"A: {response}")

asyncio.run(main())
```

Run: `python my_test.py`

---

## 🐛 Troubleshooting

**"Module not found"**
```bash
pip install -e .
```

**"API key not found"**
```bash
export OPENAI_API_KEY="your-key-here"
```

**"No such file or directory"**
```bash
mkdir -p agent_system/data/documents
mkdir -p agent_system/data/eval_results
```

---

## ✅ Testing Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] API key configured
- [ ] `example.py` runs successfully
- [ ] Quick evaluation passes (>80% success)
- [ ] Metrics file created
- [ ] No errors in output

---

## 📊 Expected Performance

| Metric | Expected Value |
|--------|---------------|
| Success Rate | 85-90% |
| Cost per Query | $0.01-0.03 |
| Response Time | 2-4 seconds |
| Tool Accuracy | 80-85% |

---

## 🎯 Quick Commands Reference

```bash
# Basic test
python example.py

# Quick evaluation
python -c "from agent_system.eval.evaluator import run_quick_eval; import asyncio; asyncio.run(run_quick_eval())"

# Full evaluation (takes longer, costs more)
python -m agent_system.eval.evaluator

# View metrics
tail agent_system/data/metrics.jsonl

# Check results
ls agent_system/data/eval_results/
```

---

## 💡 What Each Tool Does

- **Calculator**: Evaluates math expressions (e.g., "What is 15% of 250?")
- **Web Search**: Searches DuckDuckGo for current info (e.g., "Latest Python version")
- **Knowledge Base**: Retrieves stored knowledge (e.g., "What is machine learning?")
- **Document Q&A**: Queries stored documents (e.g., "What's in the agent guide?")

---

## ⏱️ Total Testing Time

- **Minimum**: 10 minutes (Steps 1-3)
- **Complete**: 20 minutes (All steps)
- **Cost**: ~$0.10-0.50 depending on tests run

---

## 🎓 Next Steps

1. Try custom queries in `my_test.py`
2. Read `FAILURES.md` for known issues
3. Check `README.md` for advanced features
4. Explore evaluation results in `agent_system/data/eval_results/`

---

**Need Help?** Check the full README.md or review error messages in the terminal.