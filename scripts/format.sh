#!/bin/bash
# Format script for Phaser MCP Server

set -e

echo "🔧 Formatting Python code..."
uv run ruff format
uv run ruff check --fix

echo "📝 Formatting Markdown files..."
uv run mdformat README.md docs/ --wrap 88

echo "✅ All formatting complete!"
