#!/bin/bash
# Debug script for company-agent with evaluation and resume support

set -e

cd "$(dirname "$0")"

echo "🚀 Starting company-agent in debug mode..."
echo ""
echo "Configuration:"
echo "  - Input file: input.json"
echo "  - Evaluator: uipath-json-similarity"
echo "  - Resume data: {'Approved': true}"
echo "  - Debug port: 5678"
echo ""
echo "📝 Steps to debug:"
echo "  1. This script will start the debug server"
echo "  2. In VS Code, press F5 or go to Run -> Start Debugging"
echo "  3. Select 'UiPath: Debug Company Agent' from the dropdown"
echo "  4. Set breakpoints in main.py"
echo "  5. The agent will pause at breakpoints"
echo ""
echo "🔗 For more info: https://uipath.github.io/uipath-python/cli/#run"
echo ""
read -p "Press Enter to start the debug server..."

# Run with debug enabled
# Note: The --resume parameter syntax depends on the interrupt structure
# Use single quotes for JSON to avoid shell interpretation
uv run uipath run agent \
  --file input.json \
  --generate-evals company-agent-eval.json \
  --eval-evaluators uipath-json-similarity \
  --debug

# Alternative: Resume from a previous interrupt
# uv run uipath run agent \
#   --file input.json \
#   --resume '{"Approved": true, "Comment": ""}' \
#   --debug
