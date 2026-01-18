#!/bin/bash
# Run tests locally

set -e

echo "Installing test dependencies..."
pip install -r requirements-api.txt
pip install pytest pytest-cov

echo "Running unit tests..."
python -m pytest tests/ -v --cov=api --cov-report=term-missing

echo "✅ Tests complete!"
