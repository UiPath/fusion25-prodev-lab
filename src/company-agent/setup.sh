#!/bin/bash
# Setup script for company-agent

set -e

echo "🚀 Setting up company-agent..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
uv venv

# Install dependencies (using local uipath packages)
echo "📥 Installing dependencies..."
uv pip install -e ../../../uipath-python \
    -e ../../../uipath-langchain-python \
    langchain-core \
    langchain-openai \
    langchain-anthropic \
    langgraph \
    python-dotenv \
    pydantic \
    httpx

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your credentials, or run: uv run uipath auth"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Authenticate: uv run uipath auth"
echo "  2. Initialize: uv run uipath init"
echo "  3. Run the agent: uv run uipath dev"
echo ""
echo "For more information, see README.md"
