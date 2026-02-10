#!/bin/bash

# Setup script for Django E-commerce Backend
# This script initializes the database and creates test users

echo "===================================="
echo "Django E-commerce Backend Setup"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created (please update with your settings)"
else
    echo "✓ .env file already exists"
fi

# Make migrations
echo ""
echo "Creating database migrations..."
python manage.py makemigrations
echo "✓ Migrations created"

# Run migrations
echo "Applying migrations to database..."
python manage.py migrate
echo "✓ Database migrated"

# Create test users
echo ""
echo "Creating test users..."
python manage.py create_test_users

echo ""
echo "===================================="
echo "Setup Complete!"
echo "===================================="
echo ""
echo "To start the development server, run:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "Django Admin will be available at: http://localhost:8000/admin"
echo ""
