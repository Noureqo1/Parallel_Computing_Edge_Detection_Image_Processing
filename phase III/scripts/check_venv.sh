#!/bin/bash
# Helper script to ensure virtual environment is activated

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    # Check if venv exists in current directory
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "WARNING: Virtual environment not found and not currently activated"
        echo "Please run: python3 -m venv venv && source venv/bin/activate"
        exit 1
    fi
fi

# Verify Python packages
python3 -c "import grpc" 2>/dev/null || {
    echo "ERROR: grpcio not installed"
    echo "Please run: pip install -r requirements.txt"
    exit 1
}

echo "✓ Virtual environment ready"
