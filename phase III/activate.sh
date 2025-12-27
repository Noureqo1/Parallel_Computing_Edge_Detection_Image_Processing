#!/bin/bash
# Activate virtual environment and set up environment for Phase 3

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

# Activate virtual environment
source venv/bin/activate

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo "Python: $(which python3)"
echo "pip: $(which pip)"
echo
echo "Available commands:"
echo "  make demo          - Run complete demonstration"
echo "  make compile       - Compile Protocol Buffers"
echo "  make test          - Test basic functionality"
echo "  make clean         - Clean generated files"
echo
echo "To start servers manually:"
echo "  python3 server/sobel_server.py --port 50051 --id server-0"
echo
echo "To deactivate virtual environment:"
echo "  deactivate"
