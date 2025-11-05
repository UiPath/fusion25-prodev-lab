# Company Policy Agent

An intelligent agent that handles company policy questions with supervisor-based routing to specialized sub-agents for Policy, Procurement, and HR inquiries. Built with LangGraph and UiPath SDK with support for node-level evaluation.

## Features

- **Supervisor Routing**: Automatically classifies questions and routes to specialized agents
- **Human-in-the-Loop**: Action Center integration for low-confidence classifications
- **Context Grounding**: RAG-based retrieval from company policy documents
- **Multi-Agent Architecture**:
  - **Policy Agent**: Handles general company policy questions
  - **Procurement Agent**: Requires email/code verification for sensitive procurement data
  - **HR Agent**: Permission-gated HR queries with tool selection
- **Node-Level Evaluations**: Generate and run evaluations for each workflow node

## Architecture

```
START → Supervisor → Route by Category
           ├─→ Policy → END
           ├─→ Procurement → Verify Credentials → Procurement Node → END
           └─→ HR → Permission Check → HR Node → END
```

## Setup

### 1. Install Python and UV

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.12
uv python install 3.12

# Create virtual environment
uv venv
```

### 2. Install Dependencies

```bash
# Install the project and its dependencies
uv pip install -e .

# Or using the local uipath-python SDK for development:
uv pip install -e ../../../uipath-python
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Authenticate with UiPath (this will populate .env)
uv run uipath auth

# Edit .env to configure:
# - Index names for Context Grounding
# - Action Center settings
# - Other optional configurations
```

### 4. Initialize the Agent

```bash
# Scan entrypoints and update uipath.json
uv run uipath init
```

## Usage

### Running the Agent

#### Interactive Development Mode (Recommended)

```bash
uv run uipath dev
```

This opens an interactive chat interface with live logging and trace visualization.

#### Non-Interactive Run

```bash
# Policy question
uv run uipath run agent '{"question": "What is the vacation policy?"}'

# Procurement question (requires verification)
uv run uipath run agent '{
  "question": "What are the vendor approval thresholds?",
  "email": "user@uipath.com",
  "code": "1357"
}'

# HR question
uv run uipath run agent '{"question": "How do I request time off?"}'
```

### Generating Evaluations

Generate node-level evaluations from a successful run:

```bash
uv run uipath run agent '{"question": "What is the vacation policy?"}' \
  --generate-evals policy_eval.json \
  --eval-evaluators uipath-llm-judge-output-semantic-similarity
```

This creates:
- `evals/eval-sets/policy_eval.json` - Evaluation set with node-level tests
- `evals/evaluators/*.json` - Evaluator configurations

### Running Evaluations

```bash
# Run evaluations against the agent
uv run uipath eval agent policy_eval.json \
  --workers 1 \
  --output-file results-policy.json

# View results
cat results-policy.json
```

## Agent Configuration Files

- **[main.py](main.py)** - Main agent implementation with LangGraph workflow
- **[langgraph.json](langgraph.json)** - LangGraph configuration mapping
- **[uipath.json](uipath.json)** - UiPath entrypoint definitions and schemas
- **[pyproject.toml](pyproject.toml)** - Python dependencies
- **[company_policy.txt](company_policy.txt)** - Sample policy document
- **[hr_auth.json](hr_auth.json)** - HR permission allowlist
- **[input.json](input.json)** - Sample input for testing

## Node-Level Evaluations

The agent supports automatic generation of node-level evaluations, allowing you to test each step of the workflow independently:

### Generated Evaluation Structure

```json
{
  "id": "unique-id",
  "name": "Evaluation set generated from agent",
  "version": "1.0",
  "evaluatorRefs": ["evaluator-id"],
  "evaluations": [
    {
      "id": "eval-id",
      "name": "Node: supervisor",
      "inputs": {"question": "What is the vacation policy?"},
      "evaluationCriterias": {
        "evaluator-id": {
          "expected_output": {...}
        }
      },
      "expectedAgentBehavior": "The agent should execute node 'supervisor' and produce the expected output during the workflow execution.",
      "nodeId": "supervisor"
    },
    // ... more node evaluations
    {
      "id": "final-eval-id",
      "name": "Final Output",
      "inputs": {"question": "What is the vacation policy?"},
      "evaluationCriterias": {...},
      "expectedAgentBehavior": "Agent should produce the expected output for the given input"
    }
  ]
}
```

### How Node-Level Evaluations Work

1. **Generation**: When running with `--generate-evals`, the CLI captures each node's output from the execution trace
2. **Storage**: Each node gets a separate evaluation item with the `nodeId` field
3. **Execution**: During eval runs, evaluators automatically extract the specific node's output from the trace
4. **Comparison**: The extracted output is compared against the expected output for that node

### Benefits

- **Granular Testing**: Test individual nodes without running the full workflow
- **Regression Detection**: Catch issues in specific nodes early
- **Debugging**: Identify which node is causing failures
- **Validation**: Ensure each step produces consistent outputs

## Development

### Project Structure

```
company-agent/
├── main.py                 # Agent implementation
├── pyproject.toml         # Dependencies
├── langgraph.json        # Graph configuration
├── uipath.json           # UiPath entrypoint schema
├── .env                  # Environment variables (gitignored)
├── .env.example          # Environment template
├── company_policy.txt    # Sample policy document
├── hr_auth.json          # HR permissions
└── evals/
    ├── eval-sets/        # Evaluation test sets
    └── evaluators/       # Evaluator configurations
```

### Customization

#### Adding New Nodes

1. Define node function in [main.py](main.py:138-160)
2. Add node to graph builder
3. Connect with edges or conditional routing
4. Run `uv run uipath init` to update schemas

#### Modifying Routing Logic

Update the routing functions:
- [route_by_category](main.py:196-202) - Main category routing
- [route_after_verification](main.py:368-381) - Procurement verification gate
- [decide_next_node](main.py:383-386) - Human feedback loop

#### Custom Evaluators

Create custom evaluators in `evals/evaluators/`:

```json
{
  "id": "custom-evaluator-id",
  "name": "CustomEvaluator",
  "type": "llm_judge",
  "config": {
    "model": "gpt-4o-2024-08-06",
    "prompt": "Your evaluation prompt..."
  }
}
```

## Deployment

### Package and Publish

```bash
# Package the agent
uv run uipath pack

# Publish to Orchestrator
uv run uipath publish

# Or combine both
uv run uipath deploy
```

### Environment-Specific Deployment

```bash
# Dev environment
uv run uipath deploy --folder-path "Dev/Agents"

# Production environment
uv run uipath deploy --folder-path "Production/Agents"
```

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
uv run uipath auth

# Check credentials
cat .env | grep UIPATH
```

### Missing Context Grounding Index

If you get errors about missing indices:

1. Create indices in UiPath Studio Web
2. Upload policy documents
3. Update index names in `.env`

### Node Not Found in Trace

If node-level evaluations fail to find nodes:

- Ensure nodes are properly named in the graph
- Check that LangChain instrumentation is enabled
- Verify spans are being collected during execution

### Permission Denied

- Check `hr_auth.json` for HR queries
- Verify email/code for Procurement queries
- Ensure proper RBAC permissions in UiPath

## Additional Resources

- [AGENTS.md](AGENTS.md) - Comprehensive SDK guide
- [UiPath Python SDK Docs](https://uipath.github.io/uipath-python/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Agent Mermaid Diagram](agent.mermaid) - Visual workflow representation

## License

Copyright © UiPath. All rights reserved.
