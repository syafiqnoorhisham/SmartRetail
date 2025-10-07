#!/bin/bash

# SmartRetail Quick Start Script

echo "🚀 Starting SmartRetail..."

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Copying from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env with your Supabase credentials"
    exit 1
fi

# Run migrations (if needed)
echo "📦 Running migrations..."
python manage.py migrate

# Start the server
echo "✅ Starting development server..."
echo "🌐 Access your app at: http://localhost:8000"
echo "🛑 Press CTRL+C to stop the server"
echo ""
python manage.py runserver
