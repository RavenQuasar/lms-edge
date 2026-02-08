#!/bin/bash

cd "$(dirname "$0")"

echo "🚀 Starting LMS-Edge Backend Server..."

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📚 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔧 Initializing database..."
python init_users.py

echo "🎉 Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
