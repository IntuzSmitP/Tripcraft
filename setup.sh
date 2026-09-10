#!/bin/bash

echo "Setting up Tripcraft..."

# Setup Backend
echo "Setting up Backend..."
cd backend
if command -v uv &> /dev/null; then
    uv sync
else
    echo "uv is not installed. Please install uv (https://docs.astral.sh/uv/) and run 'uv sync' in the backend directory."
fi
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created backend/.env from example. Please update it with your API keys (e.g. OPENROUTER_API_KEY or NVIDIA_API_KEY)."
fi
cd ..

# Setup Frontend
echo "Setting up Frontend..."
cd frontend
if command -v npm &> /dev/null; then
    npm install
else
    echo "npm is not installed. Please install Node.js and run 'npm install' in the frontend directory."
fi
cd ..

echo "Setup complete! Please configure your environment variables in backend/.env before running."
