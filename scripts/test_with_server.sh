#!/bin/bash
# Run integration tests with the proxy server

# Always use venv
source venv/bin/activate

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
fi

# Run the async server and test script
python scripts/run_server_and_test.py