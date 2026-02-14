#!/bin/bash

# Medical & Charity OCR System - Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "=========================================="
echo "Medical & Charity OCR System Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_success "Python $python_version is installed"
else
    print_error "Python $required_version or higher is required. Current version: $python_version"
    exit 1
fi

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_info "Not running in a virtual environment"
    read -p "Do you want to create a virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
        print_info "Activate it with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
        exit 0
    fi
else
    print_success "Running in virtual environment: $VIRTUAL_ENV"
fi

# Install system dependencies
echo ""
echo "Checking system dependencies..."

# Check for Tesseract
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    print_success "Tesseract OCR is installed: $tesseract_version"
else
    print_error "Tesseract OCR is not installed"
    print_info "Install with:"
    print_info "  Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-eng"
    print_info "  macOS: brew install tesseract"
fi

print_success "Using PyMuPDF (fitz) for PDF processing - No Poppler needed!"

# Install Python dependencies
echo ""
read -p "Do you want to install Python dependencies? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
fi

# Create .env file
echo ""
if [ ! -f ".env" ]; then
    read -p "Do you want to create .env file from template? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created"
            print_info "Please edit .env file with your configuration"
        else
            print_error ".env.example not found"
        fi
    fi
else
    print_info ".env file already exists"
fi

# Create storage directories
echo ""
print_info "Creating storage directories..."
cd backend 2>/dev/null || true

python3 -c "
from app.config import settings
settings.create_storage_directories()
" 2>/dev/null || print_error "Could not create directories. Run manually: python3 backend/app/config/settings.py"

cd - > /dev/null 2>&1 || true

# Test configuration
echo ""
read -p "Do you want to test the configuration? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Testing configuration..."
    python3 backend/app/config/settings.py
    echo ""
    print_info "Testing logging..."
    python3 backend/app/config/logging_config.py
    echo ""
    print_info "Testing exceptions..."
    python3 backend/app/utils/exceptions.py
fi

echo ""
echo "=========================================="
print_success "Setup completed successfully!"
echo "=========================================="
echo ""
print_info "Next steps:"
echo "  1. Activate virtual environment (if not already active)"
echo "  2. Edit .env file with your configuration"
echo "  3. Run: python3 backend/app/config/settings.py (to verify setup)"
echo ""
print_info "Ready to continue with OCR engine implementation!"
echo ""
