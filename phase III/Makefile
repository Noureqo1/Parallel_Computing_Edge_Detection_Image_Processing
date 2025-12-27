.PHONY: all install compile test demo clean help

# Default target
all: install compile

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	@if [ ! -d "venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Dependencies installed in virtual environment"
	@echo "Run 'source venv/bin/activate' to activate the environment"

# Compile Protocol Buffers
compile:
	@echo "Compiling protobuf definitions..."
	@chmod +x scripts/compile_proto.sh
	@if [ -d "venv" ]; then \
		. venv/bin/activate && ./scripts/compile_proto.sh; \
	else \
		./scripts/compile_proto.sh; \
	fi
	@echo "✓ Protobuf compiled"

# Make scripts executable
setup-scripts:
	@echo "Making scripts executable..."
	@chmod +x scripts/*.sh
	@echo "✓ Scripts ready"

# Test basic functionality
test: compile
	@echo "Testing Sobel worker..."
	@python3 server/sobel_worker.py
	@echo "✓ Worker test passed"

# Run complete demo
demo: compile setup-scripts
	@echo "Running complete demonstration..."
	@./scripts/run_demo.sh

# Start servers only
start-servers: compile setup-scripts
	@./scripts/start_replicas.sh 2 50051

# Run load test (requires servers to be running)
load-test: compile
	@echo "Running load test (ensure servers are running)..."
	@mkdir -p results
	@python3 client/load_generator.py \
		--servers localhost:50051,localhost:50052 \
		--duration 60 \
		--rate 10.0 \
		--log results/load_test.json

# Analyze existing results
analyze:
	@if [ -f results/load_test.json ]; then \
		python3 monitoring/analyze_metrics.py \
			--log results/load_test.json \
			--output results/analysis; \
	else \
		echo "Error: No results found. Run 'make demo' or 'make load-test' first."; \
	fi

# Clean generated files and results
clean:
	@echo "Cleaning generated files..."
	@rm -f sobel_service_pb2.py sobel_service_pb2_grpc.py
	@rm -f *.pyc server/*.pyc client/*.pyc monitoring/*.pyc
	@rm -rf __pycache__ server/__pycache__ client/__pycache__ monitoring/__pycache__
	@rm -rf results/*.json results/*.png results/*.txt
	@rm -rf logs/*.log logs/*.pid
	@echo "✓ Cleaned"

# Deep clean (including logs and results)
distclean: clean
	@rm -rf logs results
	@echo "✓ Deep cleaned"

# Help target
help:
	@echo "Phase 3: Resilient Distributed Sobel Service"
	@echo ""
	@echo "Available targets:"
	@echo "  make install       - Install Python dependencies"
	@echo "  make compile       - Compile Protocol Buffer definitions"
	@echo "  make test          - Test basic functionality"
	@echo "  make demo          - Run complete demonstration (recommended)"
	@echo "  make start-servers - Start 2 server replicas"
	@echo "  make load-test     - Run load test (servers must be running)"
	@echo "  make analyze       - Analyze existing test results"
	@echo "  make clean         - Remove generated files"
	@echo "  make distclean     - Remove all generated files and results"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install compile"
	@echo "  2. make demo"
	@echo "  3. View results in results/ directory"
	@echo ""
