#!/bin/bash

# Azure Incident Resolver - Quick Start Script
# This script sets up your local development environment

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║     Azure Incident Resolver - Quick Start Setup           ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Node.js or Python
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js installed: $NODE_VERSION"
    RUNTIME="node"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python installed: $PYTHON_VERSION"
    RUNTIME="python"
else
    echo "✗ Neither Node.js nor Python found. Please install one of them."
    exit 1
fi

# Check Azure CLI
if command -v az &> /dev/null; then
    echo "✓ Azure CLI installed"
else
    echo "✗ Azure CLI not found. Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

echo ""
echo "Setting up environment..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your Azure credentials before running!"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."

if [ "$RUNTIME" = "node" ]; then
    npm install
    echo "✓ Node.js dependencies installed"
elif [ "$RUNTIME" = "python" ]; then
    pip install -r requirements.txt
    echo "✓ Python dependencies installed"
fi

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p logs
mkdir -p data/incidents
mkdir -p data/runbooks
echo "✓ Directories created"

# Check Azure login
echo ""
echo "Checking Azure authentication..."
if az account show &> /dev/null; then
    ACCOUNT=$(az account show --query name -o tsv)
    echo "✓ Logged into Azure: $ACCOUNT"
else
    echo "⚠️  Not logged into Azure. Run: az login"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Login to Azure (if not already):"
echo "   az login"
echo ""
echo "3. Run in test mode to simulate an incident:"
if [ "$RUNTIME" = "node" ]; then
    echo "   export TEST_MODE=true"
    echo "   npm start"
else
    echo "   export TEST_MODE=true"
    echo "   python src/orchestration/orchestrator.py"
fi
echo ""
echo "4. Deploy to Azure:"
echo "   ./scripts/deploy-infrastructure.sh"
echo ""
echo "For full documentation, see: docs/deployment.md"
echo ""
