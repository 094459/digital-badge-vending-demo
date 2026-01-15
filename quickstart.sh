#!/bin/bash

echo "🚀 Digital Badge Platform - Quick Start"
echo "========================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv is installed"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration"
fi

echo "✓ .env file exists"

# Check AWS credentials
echo ""
echo "Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✓ AWS credentials configured"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    echo "  Account: $AWS_ACCOUNT"
else
    echo "⚠️  AWS credentials not found"
    echo ""
    echo "Configure AWS credentials using one of these methods:"
    echo "  1. Run: aws configure"
    echo "  2. Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    echo "  3. Use IAM role (for EC2/ECS/Lambda)"
    echo ""
    echo "Continuing without AWS credentials (AI features will not work)..."
fi
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Initialize database
echo "🗄️  Initializing database..."
uv run python init_db.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  uv run python run.py"
echo ""
echo "Then visit: http://127.0.0.1:5001"
echo ""
echo "Admin panel: http://127.0.0.1:5001/admin"
echo ""
