#!/bin/bash
# Compile Protocol Buffer definitions

set -e

PROTO_DIR="proto"
OUT_DIR="."

echo "Compiling Protocol Buffer definitions..."
echo "  Proto file: $PROTO_DIR/sobel_service.proto"
echo "  Output directory: $OUT_DIR"
echo

# Check if protoc is installed
if ! command -v python3 -m grpc_tools.protoc &> /dev/null; then
    echo "Error: grpcio-tools not installed"
    echo "Install with: pip3 install grpcio-tools"
    exit 1
fi

# Compile proto file
python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTO_DIR/sobel_service.proto"

echo "✓ Compilation successful!"
echo
echo "Generated files:"
echo "  sobel_service_pb2.py       (Message classes)"
echo "  sobel_service_pb2_grpc.py  (Service stubs)"
echo
