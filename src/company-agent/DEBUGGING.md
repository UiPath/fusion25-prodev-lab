# Debugging Guide for Company Agent

This guide explains how to debug the company-agent using VS Code's remote debugger.

## Quick Start

### Option 1: Using the Debug Script (Recommended)

```bash
./run-debug.sh
```

Then in VS Code:
1. Press `F5` or go to **Run → Start Debugging**
2. Select **"UiPath: Debug Company Agent"** from the dropdown
3. The debugger will attach and you can set breakpoints

### Option 2: Manual Command

```bash
cd /Users/cosminpaunel/work/agent-platform/fusion25-prodev-lab/src/company-agent

# Basic debug run
uv run uipath run agent --file input.json --debug

# With evaluation generation
uv run uipath run agent \
  --file input.json \
  --generate-evals company-agent-eval.json \
  --eval-evaluators uipath-json-similarity \
  --debug

# Resume from interrupt with approval
uv run uipath run agent \
  --file input.json \
  --resume '{"Approved": true, "Comment": "Looks good"}' \
  --debug
```

## Command Reference

### Basic Syntax

```bash
uv run uipath run <entrypoint> [options]
```

### Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--file <path>` | Load input from JSON file | `--file input.json` |
| `--debug` | Start debug server on port 5678 | `--debug` |
| `--generate-evals <file>` | Generate evaluation set | `--generate-evals eval.json` |
| `--eval-evaluators <list>` | Comma-separated evaluator IDs | `--eval-evaluators uipath-json-similarity` |
| `--resume <json>` | Resume from interrupt with data | `--resume '{"Approved": true}'` |

### Available Evaluators

- `uipath-json-similarity` - JSON structure comparison
- `uipath-llm-judge-output-semantic-similarity` - LLM-based semantic comparison
- `uipath-llm-judge-output-strict-json-similarity` - Strict JSON comparison with LLM
- `uipath-exact-match` - Exact string matching
- `uipath-contains` - Substring matching

## Debugging Workflow

### 1. Set Breakpoints

Open [main.py](main.py) in VS Code and click on the left margin to set breakpoints:

```python
async def supervisor_node(state: GraphState) -> GraphState:
    # Set breakpoint here to debug classification
    result = await llm.with_structured_output(LlmOutput).ainvoke(messages)
    # ...
```

Common places to set breakpoints:
- **Line 179**: After LLM classification in supervisor_node
- **Line 191**: Action response handling
- **Line 145**: Context retrieval in policy_node
- **Line 209**: Email/code validation in procurement_node

### 2. Start Debug Server

```bash
uv run uipath run agent --file input.json --debug
```

You'll see:
```
🐛 Debug server started on port 5678
📌 Waiting for debugger to attach...
  - VS Code: Run -> Start Debugging -> Python: Remote Attach
```

### 3. Attach Debugger

In VS Code:
1. Press `F5`
2. Select **"UiPath: Debug Company Agent"** (or **"Python: Remote Attach"**)
3. The debugger will connect and execution will continue

### 4. Debug Controls

Once attached, use VS Code's debug controls:
- **F5** - Continue
- **F10** - Step Over
- **F11** - Step Into
- **Shift+F11** - Step Out
- **Shift+F5** - Disconnect

### 5. Inspect Variables

When paused at a breakpoint:
- Hover over variables to see values
- Use the **Variables** pane to explore state
- Use the **Debug Console** to evaluate expressions

## Advanced Debugging

### Debugging Action Center Interrupts

When the agent creates an Action Center task (confidence < 99):

```python
action_data = interrupt(CreateAction(...))
print(f"Action response: {action_data}")  # Line 191
```

To test resume functionality:

```bash
# Start the agent
uv run uipath run agent --file input.json --debug

# In another terminal, after the action is created:
uv run uipath run agent \
  --file input.json \
  --resume '{"Approved": true, "Comment": "LGTM"}' \
  --debug
```

### Debugging Node-Level Evaluations

1. Generate evaluations from a successful run:

```bash
uv run uipath run agent --file input.json \
  --generate-evals test-eval.json \
  --eval-evaluators uipath-json-similarity
```

2. Debug the evaluation execution:

```bash
uv run uipath eval agent test-eval.json \
  --workers 1 \
  --output-file results.json
```

The evaluator will extract each node's output from the trace and compare it to the expected output.

### Debugging Context Grounding

Set breakpoints in the RAG retrieval:

```python
async def policy_node(state: GraphState) -> GraphOutput:
    retriever = ContextGroundingRetriever(...)
    context_docs = await get_context_data_async(retriever, state.question)
    # Breakpoint here to inspect retrieved documents
```

Check:
- `context_docs` - Retrieved document chunks
- `context_docs[0].page_content` - First chunk content
- `context_docs[0].metadata` - Source and metadata

### Debugging LLM Calls

Monitor LLM calls by setting breakpoints before/after:

```python
# Supervisor classification
result = await llm.with_structured_output(LlmOutput).ainvoke(messages)
# Breakpoint here: inspect result["category"] and result["confidence"]

# Policy answer generation
result = await llm.ainvoke(messages)
# Breakpoint here: inspect result.content
```

## Troubleshooting

### Debugger Won't Attach

**Problem**: "Waiting for debugger to attach..." but VS Code won't connect

**Solutions**:
1. Check port 5678 is not in use: `lsof -i :5678`
2. Ensure VS Code is in the correct workspace
3. Try the generic "Python: Remote Attach" configuration
4. Restart VS Code

### Breakpoints Not Hit

**Problem**: Breakpoints are grayed out or not triggered

**Solutions**:
1. Ensure `justMyCode: false` in launch.json
2. Check that the correct Python interpreter is selected
3. Verify the path mappings in launch.json match your setup
4. Try setting a breakpoint in a different location

### State Not Persisting

**Problem**: State changes between nodes seem incorrect

**Solution**: LangGraph uses immutable state updates. Check that node functions return new state objects:

```python
# Correct
return GraphState(question=state.question, category=result["category"])

# Incorrect (mutating state)
state.category = result["category"]
return state
```

### Resume Data Format

**Problem**: "Invalid resume data" error

**Solution**: Ensure JSON format matches the Action Center app output:

```bash
# Check the actual structure by looking at the debug output
# Line 191 prints: Action response: {actual_structure}

# Then match the format:
--resume '{"Approved": true, "Comment": "feedback here"}'
```

## VS Code Launch Configurations

Three configurations are available in [.vscode/launch.json](../../.vscode/launch.json):

### 1. Python Debugger: Python File
Standard Python file debugger (not for uipath run)

### 2. Python: Remote Attach (Generic)
Generic remote debugger for any Python process on port 5678

### 3. UiPath: Debug Company Agent (Recommended)
Configured specifically for the company-agent with correct path mappings

## Performance Tips

1. **Use `--workers 1` for eval debugging**: Easier to track execution
2. **Set selective breakpoints**: Only in the code paths you're investigating
3. **Use conditional breakpoints**: Right-click breakpoint → Edit Breakpoint → Add condition
4. **Log instead of stepping**: Add strategic print statements for less critical paths

## Additional Resources

- [UiPath Python CLI Documentation](https://uipath.github.io/uipath-python/cli/#run)
- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [LangGraph Debugging Guide](https://langchain-ai.github.io/langgraph/how-tos/debug/)
- [Main Agent Code](main.py)
- [README](README.md)
